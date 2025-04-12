import sys
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List


class InvalidConfigException(Exception):
    pass


@dataclass_json
@dataclass
class EditorCommand:
    command: str = "code"
    args: List[str] = field(default_factory=lambda: [])


# Store path to config file in the QUICK_PROJ_CONFIG_PATH environment variable
@dataclass_json
@dataclass
class Config:
    base_project_instantiation_directory: str = field(
        default_factory=lambda: str(Path.home() / "quick-projects")
    )
    templates: List[str] = field(default_factory=lambda: ["Python", "C++", "C", "Rust"])
    editor: EditorCommand = field(default_factory=EditorCommand)

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
                    existing_config = json.load(f)
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

    def _validate_config(self):
        base_project_instantiation_directory = Path(
            self.base_project_instantiation_directory
        )
        if not base_project_instantiation_directory.exists():
            print(
                f'base_project_instantiation_directory "{base_project_instantiation_directory}" does not exist, creating it'
            )
            base_project_instantiation_directory.mkdir()


c = Config()


# When we instantiate a template project, we need to:
# 1. Create directory somewhere
# 2. Run some commands afterwards
# So basically, a template is just a sequence of commands that we need to execute
# but we need some kind of config file to store defaults used to instantiate all projects.
# For example, where on disk should the project folders be created?
def main():
    print(sys.argv)
    print("Hello from quick-proj!")


if __name__ == "__main__":
    main()
