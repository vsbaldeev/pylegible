"""PostToolUse hook: lint the Python files the agent just edited (ruff plus pylegible's own checks).

Works under Claude Code (Edit/Write: `tool_input.file_path`) and Codex (apply_patch: paths parsed
from `tool_input.command`).

Report-only. Exits 2 with the findings on stderr, which both tools feed back to the agent;
exits 0 silently when the file is clean or not Python. Without ruff, only the own checks run.
"""

# Hooks run under whatever `python3` is on PATH, which may be pre-3.10; keep annotations lazy.
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from check_conventions import find_violations

PROJECT_CONFIG_NAMES = ("ruff.toml", ".ruff.toml")
BUNDLED_CONFIG = Path(__file__).with_name("ruff.toml")
BLOCKING_EXIT_CODE = 2
PATCH_PATH_PATTERN = re.compile(r"^\*\*\* (?:(?:Add|Update) File: (.+)|Move to: (.+))$", re.MULTILINE)


def read_payload() -> dict:
    """Return the hook's JSON payload from stdin, or an empty dict if it is not valid JSON."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def paths_from_patch(patch_text: str) -> list[str]:
    """Return the file paths a Codex apply_patch body adds, updates or moves to."""
    matches = PATCH_PATH_PATTERN.findall(patch_text)
    return [added_or_updated or moved_to for added_or_updated, moved_to in matches]


def edited_paths(payload: dict) -> list[Path]:
    """Return the files the tool call edited: Claude's `file_path`, or paths inside a Codex patch."""
    tool_input = payload.get("tool_input") or {}
    raw_paths = [tool_input["file_path"]] if tool_input.get("file_path") else []
    raw_paths += paths_from_patch(tool_input.get("command") or "")
    working_directory = Path(payload.get("cwd") or Path.cwd())
    return [working_directory / raw_path for raw_path in raw_paths]


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


def report_for(target: Path) -> str:
    """Return the combined lint findings for one file, or an empty string if it is clean."""
    if target.suffix != ".py" or not target.is_file():
        return ""
    findings = [ruff_findings(target), *find_violations(target)]
    return "\n".join(finding for finding in findings if finding)


def main() -> int:
    """Lint the edited files and return the hook's exit code."""
    reports = [report_for(target) for target in edited_paths(read_payload())]
    report = "\n".join(text for text in reports if text)
    if not report:
        return 0
    sys.stderr.write(f"pylegible lint found issues; please fix:\n{report}\n")
    return BLOCKING_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
