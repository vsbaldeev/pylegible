# python-dev

An opinionated, installable Claude Code plugin that encodes a house style for writing
Python. Its overriding value: **code that is easy for a human to read, not merely
correct.**

It is also a teaching artifact — see [`docs/how-it-works.md`](docs/how-it-works.md) for
a from-scratch explanation of how hooks, skills, and `CLAUDE.md` differ under the hood.

## Skills

| Skill | Use when you are… |
|---|---|
| **python-patterns** | writing or reviewing everyday Python — idioms, typing, error handling, comprehensions, packaging |
| **python-testing** | writing pytest tests or doing TDD — fixtures, parametrization, mocking, coverage |
| **python-logging** | adding logging, choosing a level, deciding stdout vs stderr, or replacing `print` |
| **python-oop** | designing classes — dataclasses, protocols, composition over inheritance, SOLID |
| **python-data-model** | implementing dunder methods, custom sequences/iterators, descriptors, or deep decorators |

Each skill keeps a lean `SKILL.md` (loads when it triggers) and a `reference.md` with the
depth (loads only when needed). Scopes are non-overlapping: each `SKILL.md` ends with a
**Boundary** line pointing at the right skill for adjacent topics.

## Install

This is a local-directory plugin. Enable it in `~/.claude/settings.json`:

```jsonc
{
  "extraKnownMarketplaces": {
    "python-dev": {
      "source": { "source": "directory", "path": "/Users/vsbaldeev/Projects/python-dev" }
    }
  },
  "enabledPlugins": {
    "python-dev@python-dev": true
  }
}
```

Merge those keys into your existing settings (do not replace the file). After editing,
open `/hooks` once or restart so Claude Code reloads config, then the five skills appear
in the skill listing.

## Conventions

All examples obey the rules in [`CLAUDE.md`](CLAUDE.md): no single-letter names, no
single-underscore names, functions ≤40 body lines, Google-style docstrings, specific
exceptions, and `logging` instead of `print`.
