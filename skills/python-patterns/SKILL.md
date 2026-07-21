---
name: python-patterns
description: >
  Use when writing or reviewing everyday Python — choosing between a loop and a
  comprehension, adding type hints, handling errors and exceptions, using context
  managers, organizing imports, or deciding the idiomatic ("Pythonic") way to express
  something. For class design use python-oop, for dunder methods use python-data-model,
  for tests use python-testing, for logging use python-logging.
---

# Python Patterns

## Overview

Write Python for the reader. When clarity and cleverness conflict, choose clarity — a
clever one-liner that takes a minute to decode is worse than three obvious lines. This
skill is the house style for everyday Python; the deep catalog is in `reference.md`.

## When to use

- Writing new functions or modules.
- Reviewing or refactoring existing Python for readability and idiom.
- Deciding "what is the Pythonic way to do this?"

## Core rules

| Rule | Do this |
|---|---|
| Names | Descriptive; never single-letter, never leading single underscore. `__name` only for truly private members. |
| Functions | ≤40 body lines; extract well-named helpers past that. |
| Errors | Catch specific exceptions; chain with `raise ... from error`; never bare `except`. |
| Style | EAFP (try/except) over LBYL (pre-checks). Explicit over implicit. |
| Comprehensions | Only for simple map/filter. If it needs two conditions or a nested loop, write the loop. |
| Types | Annotate signatures; prefer built-in generics (`list[str]`). |
| Comparisons | `is None`, `isinstance(x, T)` — never `== None` or `type(x) == T`. |

## Example

```python
# Clear: one obvious responsibility, specific error, chained cause
def load_settings(path: Path) -> Settings:
    """Load settings from a JSON file."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise SettingsError(f"No settings file at {path}") from error
    return Settings.from_json(raw_text)

# Too clever: nested comprehension with two conditions — expand into a loop
active_admin_emails = [u.email for g in groups for u in g.users if u.active if u.is_admin]
```

## Common mistakes

- Mutable default arguments (`def add(item, items=[])`) — use `None` and create inside.
- Bare `except:` swallowing errors and returning `None`.
- Reaching for a comprehension when a named loop or helper reads better.
- `from module import *`.

## Boundary

This skill owns general idioms. Class/dataclass/protocol design → **python-oop**. Dunder
methods, descriptors, custom iterators, deep decorators → **python-data-model**. Tests →
**python-testing**. Logging → **python-logging**. See `reference.md` for the full catalog
(typing, context managers, generators, packaging, concurrency, anti-patterns).
