"""Checks for pylegible rules that ruff has no rule for.

PYL001: a function body longer than 40 lines (blank lines count; the signature, decorators,
the function's own docstring and comment-only lines do not).
PYL002: a name defined with a single leading underscore (`__name` and bare `_` are allowed).
Only definitions are flagged, so reading a third-party `obj._private` is fine.
"""

# Hooks run under whatever `python3` is on PATH, which may be pre-3.10; keep annotations lazy.
from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

MAX_FUNCTION_BODY_LINES = 40


def comment_only_lines(source: str) -> set[int]:
    """Return the line numbers that hold nothing but a comment."""
    lines = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT and token.line.strip().startswith("#"):
                lines.add(token.start[0])
    except (tokenize.TokenError, IndentationError):
        pass
    return lines


def body_line_count(function: ast.FunctionDef | ast.AsyncFunctionDef, comment_lines: set[int]) -> int:
    """Count a function's body lines, skipping its docstring and comment-only lines."""
    statements = function.body
    if ast.get_docstring(function, clean=False) is not None:
        statements = statements[1:]
    if not statements:
        return 0
    first_line = statements[0].lineno
    return sum(1 for line in range(first_line, function.end_lineno + 1) if line not in comment_lines)


def is_single_underscore(name: str | None) -> bool:
    """Check for a leading single underscore, allowing `__name`, dunders and a bare `_`."""
    return bool(name) and name.startswith("_") and not name.startswith("__") and name != "_"


def defined_names(node: ast.AST) -> list[str | None]:
    """Return the names that node itself defines or binds (not names it merely reads)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return [node.id]
    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
        return [node.attr]
    if isinstance(node, ast.ExceptHandler):
        return [node.name]
    if isinstance(node, ast.alias):
        return [node.asname]
    return []


def find_violations(path: Path) -> list[str]:
    """Return `path:line: CODE message` findings for the pylegible rules ruff cannot check."""
    source = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    comment_lines = comment_only_lines(source)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = body_line_count(node, comment_lines)
            if length > MAX_FUNCTION_BODY_LINES:
                findings.append(
                    f"{path}:{node.lineno}: PYL001 `{node.name}` body is {length} lines "
                    f"(max {MAX_FUNCTION_BODY_LINES}); extract helpers"
                )
        for name in defined_names(node):
            if is_single_underscore(name):
                findings.append(
                    f"{path}:{getattr(node, 'lineno', 1)}: PYL002 `{name}` starts with a single underscore; "
                    "drop the prefix or use `__name` for truly private members"
                )
    return sorted(findings)
