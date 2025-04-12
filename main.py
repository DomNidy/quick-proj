import sys
import json
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, DataClassJsonMixin, Undefined
from typing import List, Any


class InvalidConfigException(Exception):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class EditorOptions:
    command: str = "code"
    args: List[str] = field(default_factory=lambda: [])


@dataclass
class Config(DataClassJsonMixin):
    base_project_instantiation_directory: str = field(
        default_factory=lambda: str(Path.home() / "quick-projects")
    )
    templates: List[str] = field(default_factory=lambda: ["Python", "C++", "C", "Rust"])
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

                    # ISSUE: Need to decode to the appropriate classes when loading from json
                    # For example, the EditorOptions object needs to be deserialized into the class,
                    # right now its just loaded as a plain old dict.
                    existing_config = json.load(
                        f, object_hook=Config._decode_json_object_to_class_object
                    )
                except json.JSONDecodeError as e:
                    raise InvalidConfigException(
                        f"Tried to load config file, but it was not valid JSON: {e}"
                    )
            for k, v in existing_config.items():
                # Make sure all fields that we load from the config file exist on the class
                if not hasattr(self, k):
                    raise InvalidConfigException(
                        f'Config file contained unexpected field: "{k}"'
                    )
                self.__setattr__(k, v)

        self._validate_config()

    @staticmethod
    def _decode_json_object_to_class_object(obj: dict[Any, Any]) -> Any:
        match obj:
            case {"command": _, "args": _}:
                return EditorOptions(**obj)
            case {
                "base_project_instantiation_directory": _,
                "templates": _,
                "editor": _,
            }:
                return obj
            case _:
                pass

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

    def open_editor(self):
        """Opens the editor. The editor is specified in the config file."""
        editor_executable_path = shutil.which(self.editor.command)
        subprocess.run(editor_executable_path)


c = Config()
app = QuickProject(c)
print(app.open_editor())


def main():
    print(sys.argv)
    print("Hello from quick-proj!")


if __name__ == "__main__":
    main()
