"""PostToolUse hook: lint a Python file the agent just edited (ruff plus pylegible's own checks).

Report-only. Exits 2 with the findings on stderr so Claude Code feeds them back to the agent;
exits 0 silently when the file is clean or not Python. Without ruff, only the own checks run.
"""

# Hooks run under whatever `python3` is on PATH, which may be pre-3.10; keep annotations lazy.
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from check_conventions import find_violations

PROJECT_CONFIG_NAMES = ("ruff.toml", ".ruff.toml")
BUNDLED_CONFIG = Path(__file__).with_name("ruff.toml")
BLOCKING_EXIT_CODE = 2


def read_edited_path() -> Path | None:
    """Return the file path from the hook's JSON payload on stdin, or None if absent."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return None
    file_path = payload.get("tool_input", {}).get("file_path")
    return Path(file_path) if file_path else None


def project_defines_ruff_config(start: Path) -> bool:
    """Check whether any parent directory of start holds its own ruff configuration."""
    for directory in (start, *start.parents):
        if any((directory / name).is_file() for name in PROJECT_CONFIG_NAMES):
            return True
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and "[tool.ruff" in pyproject.read_text(encoding="utf-8", errors="ignore"):
            return True
    return False


def ruff_command() -> list[str] | None:
    """Locate a way to run ruff: an installed binary, else uvx, else None."""
    if shutil.which("ruff"):
        return ["ruff"]
    if shutil.which("uvx"):
        return ["uvx", "ruff"]
    return None


def lint(command: list[str], target: Path) -> subprocess.CompletedProcess[str]:
    """Run ruff check on target, using the bundled config when the project has none."""
    arguments = [*command, "check", "--no-fix", "--output-format", "concise"]
    if not project_defines_ruff_config(target.resolve().parent):
        arguments += ["--config", str(BUNDLED_CONFIG)]
    return subprocess.run([*arguments, str(target)], capture_output=True, text=True, check=False)


def ruff_findings(target: Path) -> str:
    """Return ruff's findings for target, or an empty string if clean or ruff is unavailable."""
    command = ruff_command()
    if command is None:
        return ""
    result = lint(command, target)
    if result.returncode == 0:
        return ""
    return result.stdout.strip() or result.stderr.strip()


def main() -> int:
    """Lint the edited file and return the hook's exit code."""
    target = read_edited_path()
    if target is None or target.suffix != ".py" or not target.is_file():
        return 0
    findings = [ruff_findings(target), *find_violations(target)]
    report = "\n".join(finding for finding in findings if finding)
    if not report:
        return 0
    sys.stderr.write(f"pylegible lint found issues in {target.name}; please fix:\n{report}\n")
    return BLOCKING_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
