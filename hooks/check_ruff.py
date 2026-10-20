"""SessionStart hook: tell the agent once when the pylegible lint hook cannot run.

In a Python project with neither ruff nor uvx available, emits a one-line hint as additional
context so the agent can suggest an install to the user. Never installs anything itself.
Silent otherwise. Set PYLEGIBLE_NO_LINT_HINT=1 to disable.
"""

# Hooks run under whatever `python3` is on PATH, which may be pre-3.10; keep annotations lazy.
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from lint_python import ruff_command

OPT_OUT_VARIABLE = "PYLEGIBLE_NO_LINT_HINT"
PROJECT_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile")
HINT = (
    "pylegible's ruff lint hook is inactive because neither `ruff` nor `uvx` was found. "
    "Briefly suggest the user install it (e.g. `uv tool install ruff` or `pip install ruff`); "
    "do not install it yourself."
)


def is_python_project(directory: Path) -> bool:
    """Check whether directory looks like the root of a Python project."""
    if any((directory / marker).is_file() for marker in PROJECT_MARKERS):
        return True
    return any(directory.glob("*.py"))


def main() -> int:
    """Print the hint as SessionStart additional context when it applies."""
    if os.environ.get(OPT_OUT_VARIABLE) or ruff_command() is not None:
        return 0
    project_directory = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
    if not is_python_project(project_directory):
        return 0
    output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": HINT}}
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
