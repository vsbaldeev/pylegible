# python-dev

An opinionated, installable plugin that encodes a house style for writing Python. Its
overriding value: **code that is easy for a human to read, not merely correct.**

It works with **Claude Code** (as a plugin) and **Codex** (as Agent Skills + `AGENTS.md`),
and it doubles as a teaching artifact — see [`docs/how-it-works.md`](docs/how-it-works.md)
for a from-scratch explanation of how hooks, skills, and `CLAUDE.md`/`AGENTS.md` differ
under the hood.

## What's inside

- **Seven topic skills** — each a lean `SKILL.md` (loads when it triggers) plus a
  `reference.md` with the depth (loads only when needed). Scopes are non-overlapping: each
  `SKILL.md` ends with a **Boundary** line pointing at the right skill for adjacent topics.
- **Always-on conventions and design principles** — [`CLAUDE.md`](CLAUDE.md) (Claude Code)
  and [`AGENTS.md`](AGENTS.md) (Codex), kept in sync.
- Reference catalogs current through **Python 3.13 / 3.14** (features flagged by version).

## Skills

| Skill | Use when you are… |
|---|---|
| **python-patterns** | writing or reviewing everyday Python — idioms, typing, error handling, comprehensions, packaging |
| **python-testing** | writing pytest tests or doing TDD — fixtures, parametrization, mocking, coverage |
| **python-logging** | adding logging, choosing a level, deciding stdout vs stderr, or replacing `print` |
| **python-oop** | designing classes — dataclasses, Protocol/ABC, composition over inheritance, SOLID |
| **python-data-model** | dunder methods, operators, custom sequences/iterators, `with`, pattern matching |
| **python-metaprogramming** | decorators, descriptors, metaclasses, `__init_subclass__`, dynamic attributes |
| **python-concurrency** | choosing threads/asyncio/processes, executors, races, the GIL, free-threading |

## Layout

```
python-dev/
├── .claude-plugin/{plugin.json, marketplace.json}   Claude Code plugin manifest
├── CLAUDE.md                                          always-on rules (Claude Code)
├── AGENTS.md                                          always-on rules (Codex) — mirrors CLAUDE.md
├── docs/how-it-works.md                               hooks vs skills vs CLAUDE.md
└── skills/<name>/{SKILL.md, reference.md}             the seven skills
```

## Install — Claude Code

1. Clone the repository:

   ```bash
   git clone https://github.com/YOUR_USERNAME/python-dev.git
   ```

2. Register it as a local-directory plugin by merging these keys into
   `~/.claude/settings.json` (do not replace the file). Set `path` to wherever you cloned it:

   ```jsonc
   {
     "extraKnownMarketplaces": {
       "python-dev": {
         "source": { "source": "directory", "path": "/absolute/path/to/python-dev" }
       }
     },
     "enabledPlugins": {
       "python-dev@python-dev": true
     }
   }
   ```

3. Open `/hooks` once or restart so Claude Code reloads config; the seven skills then appear
   in the skill listing and auto-trigger by description.

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
