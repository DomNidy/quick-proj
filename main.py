import subprocess
import shutil
from pathlib import Path
from typing import List, Union, Optional, Annotated
from utils import generate_project_title
from pydantic import BaseModel, Field, field_validator
import os
import argparse


def is_windows() -> bool:
    if os.name == "nt":
        return True
    return False


class InvalidConfig(Exception):
    pass


class ProjectTemplateNotExists(Exception):
    pass


class EditorOptions(BaseModel):
    """Specifies the command that should be used to open a text editor and any arguments that should be passed along"""

    command: List[str] = Field(
        description="Command to open the text editor of your choice", examples=["code"]
    )


class ProjectTemplate(BaseModel):
    """A project template defines the sequence of commands that are used to instantiate a project."""

    name: Annotated[
        str,
        Field(
            description="Name of the template. Should be concise, but provide enough detail.",
            examples=["Python (Torch CUDA and UV)", "C++ (spdlog, GTest, CMake)"],
        ),
    ]
    description: Annotated[
        Optional[str],
        Field(
            description="A description for the project template. Optional.",
            examples=[
                "This template creates a Python project using the UV package manager. It also installs torch (with CUDA support), then creates a Python notebook file that imports it."
            ],
        ),
    ]
    editor_override: Annotated[
        Optional[EditorOptions],
        Field(
            description="Editor to use when instantiating this project template. Optional.",
            default=None,
        ),
    ]
    init_steps: Annotated[
        List[List[str]],
        Field(
            description="The sequence of commands to execute while instantiating the template. These commands will be executed with the current working directory being set to newly created project's folder. These commands effectively define what content will be inside of the project and should be used to create files or perform any necessary setup. For example, you can clone a git repo here, manually create a file, etc."
        ),
    ]


class Config(BaseModel):
    instantiation_directory: str = Field(
        description="Directory that projects will be created at",
    )
    templates: List[ProjectTemplate] = Field(
        description="List of ProjectTemplates",
    )
    editor: EditorOptions = Field(description="The default text editor to use")

    @staticmethod
    def _get_default_config() -> "Config":
        """Returns a Config object with reasonable defaults

        Returns:
            Config: _description_
        """
        return Config(
            instantiation_directory=str(Path.home() / "quick-projects"),
            editor=EditorOptions(command=["code"]),
            templates=[
                ProjectTemplate(
                    name="Python Application (UV)",
                    description="Creates a Python project using the UV package manager. The created project is configured to be built as an application, rather than a library.",
                    init_steps=[
                        [
                            "uv",
                            "init",
                            "--app",
                            "--name",
                            "my-project",
                            "--author-from",
                            "auto",
                            "--vcs",
                            "git",
                        ]
                    ],
                )
            ],
        )

    @field_validator("instantiation_directory", mode="after")
    @classmethod
    def _check_instantiation_directory_exists(cls, instantiation_directory: str) -> str:
        if not Path(instantiation_directory).exists():
            raise ValueError(
                f"Instantiation directory '{instantiation_directory}' does not exist"
            )
        return instantiation_directory


class QuickProject:
    def __init__(self, config: Config) -> None:
        self.instantiation_directory_path = Path(config.instantiation_directory)
        self.templates = config.templates
        self.editor = config.editor

    def instantiate_project(self, template_name: str, project_name: None | str = None):
        """Instantiates the template defined by template_name

        Args:
            template_name (str): Name of the template to instantiate
        """
        pt = None
        for template in self.templates:
            if template_name == template.name:
                pt = template
                break

        if pt is None:
            raise ProjectTemplateNotExists(
                f'Project template "{template_name}" does not exist, check your config.\n'
                "Valid template names are: "
                + ",".join(f'"{pt.name}"' for pt in self.templates)
            )

        # If no project_name was provided, construct one
        if project_name is None:
            project_name = generate_project_title()
            attempts, max_attempts = 0, 1000
            while (
                self.instantiation_directory_path / project_name
            ).exists() and attempts < max_attempts:
                attempts += 1
            else:
                project_root_path = self.instantiation_directory_path / project_name
        else:
            project_root_path = self.instantiation_directory_path / project_name

        # Create folder to store project
        try:
            project_root_path.mkdir()
        except FileExistsError as e:
            e.add_note(
                f'This occured during instantiation of project template: "{pt.name}"'
            )
            raise e

        print(f"Created project folder at: {project_root_path}")

        # Now, execute all commands in the template
        for i, step in enumerate(pt.init_steps):
            print(f"Step {i+1}: {step}")
            executable = shutil.which(step[0])
            if executable is None:
                executable = step[0]
            command = [executable]
            # If this step has additional arguments, make sure we add them to the command
            if len(step) > 1:
                command.extend(step[1:])

            print(f"\t > {command}")
            try:
                subprocess.run(command, cwd=project_root_path, capture_output=True)
            except Exception as e:
                print(f"Error occured while instantiating the project: {e}")
                print(f"Last command that was ran: {command}")
                print(
                    f'Removing the project dir "{project_root_path}" as its useless now...'
                )

                try:
                    project_root_path.rmdir()
                except OSError as e:
                    e.add_note(
                        f"You may need to remove the directory manually, path: {str(project_root_path)}"
                    )
                    raise

    def open_editor(self, path: str):
        """Open the directory using the configured editor.

        The command that will be executed is of the form:
        `editor_executable_path <path>`

        TODO: Add better support for different text editors.

        Args:
            path (str): Path to the directory to open
        """
        editor_executable_path = shutil.which(self.editor.command)
        print(editor_executable_path)
        subprocess.run(
            [editor_executable_path, path],
            shell=True,
        )


def load_config(config_path: Optional[Union[Path, str]] = None) -> "Config":
    """Load a config file from disk.

    If `config_path` is not provided, then we will attempt to
    load it from the default location in the user's home directory.
    If the config does not exist within the user's home directory,
    it will be created.

    Args:
        config_path (Optional[Union[Path, str]]): Path to the config file

    Raises:
        InvalidConfig: If any validation errors occur

    Returns:
        Config: The deserialized config object
    """
    if isinstance(config_path, str):
        config_path = Path(config_path)
    elif config_path is None:
        config_directory_path = Path.home() / ".quick-proj"
        if not config_directory_path.exists():
            config_directory_path.mkdir()
            print(
                f"Default quick-proj directory did not exist, created it at: {config_directory_path}"
            )
        config_path = config_directory_path / "config.json"

        if not config_path.exists():
            # Create new config.json file with default configuration
            with open(config_path, "w+") as f:
                f.write(Config._get_default_config().model_dump_json(indent=4))
            print(f"Created default config.json file at: {config_path}")

    if not config_path.exists():
        raise FileNotFoundError(f"Config file {config_path} does not exist")

    return Config.model_validate_json(config_path.read_text(), strict=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-path", type=Path, default=None, help="Path to the config file"
    )
    parser.add_argument(
        "--template-name",
        type=str,
        default=None,
        help="Name of the template to instantiate",
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default=None,
        help="Name of the project to instantiate",
    )
    args = parser.parse_args()

    c = load_config(args.config_path)

    app = QuickProject(c)
    app.instantiate_project(args.template_name, args.project_name)


if __name__ == "__main__":
    main()
