# pylegible

[![CI](https://github.com/vsbaldeev/pylegible/actions/workflows/validate.yml/badge.svg)](https://github.com/vsbaldeev/pylegible/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%20%7C%203.14-blue.svg)](https://www.python.org/)

An opinionated, installable plugin for AI coding agents — **Claude Code** (as a plugin) and
**Codex** (as Agent Skills + `AGENTS.md`) — that encodes a house style for writing Python.
Its overriding value: **code that is easy for a human to read, not merely correct.**

It also doubles as a teaching artifact — see [`docs/how-it-works.md`](docs/how-it-works.md)
for a from-scratch explanation of how hooks, skills, and `CLAUDE.md`/`AGENTS.md` differ
under the hood.

## What's inside

- **Nine topic skills** — each a lean `SKILL.md` (loads when it triggers) plus a
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
├── docs/how-it-works.md                               hooks vs skills vs CLAUDE.md
└── skills/<name>/{SKILL.md, reference.md}             the nine skills
```

## Install — Claude Code

From inside Claude Code, add the marketplace and install the plugin:

```text
/plugin marketplace add vsbaldeev/pylegible
/plugin install pylegible@pylegible
```

The nine skills then appear in the skill listing and auto-trigger by description. Manage or
update the plugin later with `/plugin`.

<details>
<summary>Upgrading from <code>python-dev</code> or 0.2.x?</summary>

**Coming from `python-dev`?** The plugin was renamed in 0.2.0, and the old identifier
`python-dev@python-dev` no longer resolves. Remove the old entry (via `/plugin`, or by
deleting it from `extraKnownMarketplaces`/`enabledPlugins` in `~/.claude/settings.json`),
then install `pylegible@pylegible` as above — only the plugin and marketplace slug moved.

**Coming from 0.2.x?** `python-patterns` is now `python-idioms`. It always covered
everyday idioms rather than Gang-of-Four patterns, and the old name invited exactly that
confusion — which matters now that 0.3.0 adds a real `python-design-patterns` skill.
Nothing to do beyond updating the plugin, but if you referenced `python-patterns` by name
in your own `CLAUDE.md`, point it at `python-idioms`.

</details>

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

- **Per-repo:** `ln -s ../skills .agents/skills` from the repo root — Codex discovers skills
  in `.agents/skills/` and implicitly invokes them by description.
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
