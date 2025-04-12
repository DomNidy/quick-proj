import sys
import json
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, DataClassJsonMixin, Undefined
from typing import List, Any, Tuple, Union
import os


def is_windows() -> bool:
    if os.name == "nt":
        return True
    return False


class InvalidConfig(Exception):
    pass


class ProjectTemplateNotExists(Exception):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class EditorOptions:
    """Specifies the command that should be used to open a text editor and any arguments that should be passed along"""

    command: List[str] = field(default_factory=lambda: ["code"])


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class ProjectTemplate:
    """A project template defines the sequence of commands that are used to instantiate a project"""

    template_name: str
    editor_override: EditorOptions = field(default_factory=lambda: None)
    init_steps: List[List[str]] = field(default_factory=lambda: [])


@dataclass
class Config(DataClassJsonMixin):
    base_project_instantiation_directory: str = field(
        default_factory=lambda: str(Path.home() / "quick-projects")
    )
    templates: List[ProjectTemplate] = field(
        default_factory=lambda: [
            ProjectTemplate(
                "Python",
                init_steps=[
                    (["cmd", "/c"] if is_windows() else []) + ["echo", "Hello!"]
                ],
            )
        ]
    )
    editor: EditorOptions = field(default_factory=EditorOptions)

    def __post_init__(self):
        # Create .quick-proj if it doesn't exist
        quick_proj_dir = Path.home() / ".quick-proj"
        if not quick_proj_dir.exists():
            quick_proj_dir.mkdir()
            print(f"Created quick-proj directory at: {quick_proj_dir}")

        # Check if config file is inside quick-proj dir
        config_path = quick_proj_dir / "config.json"
        if not config_path.exists():
            print(
                'Config file "config.json" does not exist in quick-proj directory, creating one'
            )
            config_path.touch()
            # Serialize the Config object's fields to the config file
            with open(config_path, "w+") as f:
                f.write(self.to_json(indent=4))
        else:
            with open(config_path, "r") as f:
                try:
                    existing_config = json.load(
                        f, object_hook=Config._decode_dict_to_class_object
                    )
                except json.JSONDecodeError as e:
                    raise InvalidConfig(
                        f"Tried to load config file, but it was not valid JSON: {e}"
                    )
            for k, v in existing_config.items():
                # Make sure all fields that we load from the config file exist on the class
                if not hasattr(self, k):
                    raise InvalidConfig(
                        f'Config file contained unexpected field: "{k}"'
                    )
                self.__setattr__(k, v)

        self._validate_config()

    @staticmethod
    def _decode_dict_to_class_object(obj: dict[Any, Any]) -> Any:
        """Performs pattern matching on an object and tries to match it to one of the
        classes that the Config object needs.

        Args:
            obj (dict[Any, Any]): Object to attempt decoding

        Raises:
            InvalidConfigException: If the object does not match any of the config-related dataclasses

        Returns:
            Any: A class instance. The type of this object can be any of the config-related dataclasses (e.g., `EditorOptions`)
        """
        match obj:
            case {"command": c} if isinstance(c, list):
                return EditorOptions(**obj)
            case {
                "base_project_instantiation_directory": _,
                "templates": _,
                "editor": _,
            }:
                return obj
            case {
                "template_name": tn,
                "editor_override": eo,
                "init_steps": ins,
            } if (
                isinstance(tn, str)
                and isinstance(ins, list)
                and (isinstance(eo, type(None)) or isinstance(eo, EditorOptions))
            ):
                return ProjectTemplate(**obj)
            case _:
                raise InvalidConfig(
                    f"Failed to decode a nested object that was in the config file: \n{json.dumps(obj, indent=4)}\n"
                    "Ensure that you defined all fields in the config object, and that their\n"
                    "types match the types defined in the corresponding Python dataclass. This\n"
                    "usually happens when you only defined a subset of properties, or one\n"
                    "property's type does not match the intended Python type."
                )

    def _validate_config(self):
        base_project_instantiation_directory = Path(
            self.base_project_instantiation_directory
        )
        if not base_project_instantiation_directory.exists():
            print(
                f'base_project_instantiation_directory "{base_project_instantiation_directory}" does not exist, creating it'
            )
            base_project_instantiation_directory.mkdir()


class QuickProject:
    def __init__(self, config: Config) -> None:
        self.base_project_instantiation_directory = (
            config.base_project_instantiation_directory
        )
        self.templates = config.templates
        self.editor = config.editor

    def instantiate_project(self, template_name: str):
        """Instantiates the template defined by template_name

        Args:
            template_name (str): Name of the template to instantiate
        """
        pt = None
        for template in self.templates:
            if template_name == template.template_name:
                pt = template
                break

        if pt is None:
            raise ProjectTemplateNotExists(
                f'Project template "{template_name}" does not exist, check your config.\n'
                "Valid template names are: "
                + ",".join(f'"{pt.template_name}"' for pt in self.templates)
            )

        print(f"Got template: {pt}")
        for i, step in enumerate(pt.init_steps):
            print(f"Step {i+1}: {step}")

            executable = shutil.which(step[0])
            if executable is None:
                executable = step[0]

            command = [executable]

            # If this step has additional arguments, make sure we add them to the command
            if len(step) > 1:
                command.extend(step[1:])

            print(command)
            print(shutil.which("echo"))
            subprocess.run(command)

    def open_editor(self):
        """Opens the editor. The editor is specified in the config file."""
        editor_executable_path = shutil.which(self.editor.command)

        subprocess.run(editor_executable_path, shell=True)


c = Config()
app = QuickProject(c)
app.instantiate_project("Python")
app.instantiate_project("C")


def main():
    pass


if __name__ == "__main__":
    main()
