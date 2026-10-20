# pylegible

[![CI](https://github.com/vsbaldeev/pylegible/actions/workflows/validate.yml/badge.svg)](https://github.com/vsbaldeev/pylegible/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%20%7C%203.14-blue.svg)](https://www.python.org/)

An opinionated, installable plugin for AI coding agents — **Claude Code** (as a plugin) and
**Codex** (as Agent Skills + `AGENTS.md`) — that encodes a house style for writing Python.
Its overriding value: **code that is easy for a human to read, not merely correct.**

## What's inside

- **Ten topic skills** — each a lean `SKILL.md` (loads when it triggers) plus a
  `reference.md` with the depth (loads only when needed). Scopes are non-overlapping: each
  `SKILL.md` ends with a **Boundary** line pointing at the right skill for adjacent topics.
- **Always-on conventions and design principles** — [`CLAUDE.md`](CLAUDE.md) (Claude Code)
  and [`AGENTS.md`](AGENTS.md) (Codex), kept in sync.
- Reference catalogs current through **Python 3.13 / 3.14** (features flagged by version).

## Skills

| Skill | Use when you are… |
|---|---|
| **python-idioms** | writing or reviewing everyday Python — idioms, typing, error handling, comprehensions, packaging |
| **python-design-patterns** | naming or choosing a design pattern — Strategy, Adapter, Observer, Builder, and which GoF patterns Python dissolves |
| **python-project-structure** | deciding where code lives — splitting modules, naming subpackages, layering, import direction, mirroring `tests/` |
| **python-testing** | writing pytest tests or doing outside-in TDD — fixtures, parametrization, mocking, fault injection, reading coverage |
| **python-editing-existing-code** | changing code you didn't write — minimal-footprint edits and characterization tests before touching untested behavior |
| **python-logging** | adding logging, choosing a level, deciding stdout vs stderr, or replacing `print` |
| **python-oop** | designing classes — dataclasses, Protocol/ABC, composition over inheritance, SOLID |
| **python-data-model** | dunder methods, operators, custom sequences/iterators, `with`, pattern matching |
| **python-metaprogramming** | decorators, descriptors, metaclasses, `__init_subclass__`, dynamic attributes |
| **python-concurrency** | choosing threads/asyncio/processes, executors, races, the GIL, free-threading |

## Layout

```
pylegible/
├── .claude-plugin/{plugin.json, marketplace.json}   Claude Code plugin manifest
├── CLAUDE.md                                          always-on rules (Claude Code)
├── AGENTS.md                                          always-on rules (Codex) — mirrors CLAUDE.md
├── hooks/{hooks.json, lint_python.py, check_conventions.py, check_ruff.py, ruff.toml}   lint after Python edits
└── skills/<name>/{SKILL.md, reference.md}             the ten skills
```

## Lint hook (Claude Code)

After every `Edit`/`Write`/`MultiEdit` of a `.py` file, a `PostToolUse` hook runs `ruff check`
and feeds any findings back to the agent. It is report-only (never auto-fixes) and silent when
the file is clean or ruff is unavailable (it uses `ruff` if installed, else `uvx ruff`). If the
project has its own ruff config (`ruff.toml`, `.ruff.toml`, or `[tool.ruff]` in
`pyproject.toml`) that is used; otherwise the bundled `hooks/ruff.toml` applies. It covers the
mechanical rules: absolute imports, imports at top, 120-char lines, no bare `except`, no `print`,
docstrings, annotations, naming. Two rules ruff has no equivalent for are checked by
`check_conventions.py` (stdlib `ast`, runs even without ruff): `PYL001` function body over 40
lines, and `PYL002` a name *defined* with a single leading underscore (`__name`, dunders and a
bare `_` are allowed; reading someone else's `obj._private` is not flagged).

If a Python project has neither `ruff` nor `uvx`, a `SessionStart` hook (`check_ruff.py`) tells the
agent once so it can suggest installing ruff; it never installs anything itself. Silence it with
`PYLEGIBLE_NO_LINT_HINT=1`.

## Install — Claude Code

From inside Claude Code, add the marketplace and install the plugin:

```text
/plugin marketplace add vsbaldeev/pylegible
/plugin install pylegible@pylegible
```

The ten skills then appear in the skill listing and auto-trigger by description. Manage or
update the plugin later with `/plugin`.

<details>
<summary>Install from source (local development)</summary>

Clone and point Claude Code at the directory:

```bash
git clone https://github.com/vsbaldeev/pylegible.git
claude --plugin-dir ./pylegible
```

Or register the clone as a local-directory marketplace by merging into `~/.claude/settings.json`
(set `path` to where you cloned it):

```jsonc
{
  "extraKnownMarketplaces": {
    "pylegible": {
      "source": { "source": "directory", "path": "/absolute/path/to/pylegible" }
    }
  },
  "enabledPlugins": {
    "pylegible@pylegible": true
  }
}
```

Settings are read at startup, so restart Claude Code (or run `/plugin`) after editing the file
for the skills to show up.

</details>

## Install — Codex

The skills follow the same Agent Skills standard Codex uses, so no content changes are
needed — only placement. Codex reads `AGENTS.md` automatically; to expose the skills:

Clone pylegible somewhere first:

```bash
git clone https://github.com/vsbaldeev/pylegible.git
```

- **Per-repo:** from the target project's root, symlink to the clone's `skills/` directory —
  Codex discovers skills in `.agents/skills/` and implicitly invokes them by description:

  ```bash
  ln -s /absolute/path/to/pylegible/skills .agents/skills
  ```

  If the target repo already has an `.agents/skills` directory or its own `AGENTS.md`, don't
  overwrite them — symlink the individual skill folders you want instead, and merge the
  relevant rules from pylegible's `AGENTS.md` into the target's by hand.
- **Global:** copy or symlink each skill directory into `~/.codex/skills/`.

Explicit invocation in Codex is `$python-logging` (etc.). The `.claude-plugin/` manifest and
any Claude Code hooks do not apply to Codex.

## Conventions and principles

All examples obey [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md): no single-letter names
(except `x`/`y` vector components), no leading single underscore, functions ≤40 body lines,
Google-style docstrings, specific exceptions, and `logging` instead of `print`. Both files
also carry the full design-principle set — **SOLID** plus composition over inheritance, Law
of Demeter, DRY, YAGNI, KISS, fail fast, separation of concerns, explicit over implicit, and
least surprise.
