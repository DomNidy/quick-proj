# quick-proj

A program to quickly setup projects for prototyping/experimenting.

## `config.json`

Here's the structure of `config.json` and an example of a Python template.

```json
{
  "base_project_instantiation_directory": "C:\\Users\\Me\\quick-projects",
  "templates": [
    {
      "template_name": "Python",
      "editor_override": null,
      "init_steps": [
        ["cmd", "/c", "uv init"],
        ["cmd", "/c", "uv add torch"],
        ["cmd", "/c", "echo import torch as t", ">main.py"],
        ["cmd", "/c", "echo \n", ">>main.py"],
        ["cmd", "/c", "echo print(t.cuda.is_available())", ">>main.py"]
      ]
    }
  ],
  "editor": {
    "command": ["code"]
  }
}
```