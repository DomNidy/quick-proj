# quick-proj

A program to quickly setup projects for prototyping/experimenting.

**TLDR:** You should probably just use `git` and `git clone` instead.

## `config.json`

Here's the structure of `config.json` and an example of a Python template.

> **Note**: The commands in `init_steps` are executed with the current working directory set to the project directory. A new project directory is created when instantiating a template. Despite this, I would be **very** cautions with the commands you define there. Also, unless you want your computer to explode, DO NOT allow any external request or source to modify or inject input into the templates, specifically the `init_steps` commands. This is a script meant for personal use, and implements basically zero guardrails and sanization. 

```json
{
  "instantiation_directory": "C:/path/to/instantiation/dir",
  "templates": [
    {
      "name": "Python Notebook with PyTorch CUDA",
      "description": "Creates a Python project using the UV package manager. The created project contains a Python notebook that can download and install PyTorch with CUDA support.",
      "editor_override": null,
      "init_steps": [
        [
          "git",
          "clone",
          "--local",
          "C:/path/to/template-git-repos/python-torch-template-repo",
          "."
        ],
        ["uv", "add", "ipykernel"],
        ["cmd", "/c", "rd", "/s", "/q", ".git", "&&", "exit"]
      ]
    }
  ],
  "editor": {
    "command": ["code"]
  }
}
```