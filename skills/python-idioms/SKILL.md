---
name: python-idioms
description: >
  Use when writing or reviewing everyday Python — choosing between a loop and a
  comprehension, adding type hints, handling errors and exceptions, using `with` blocks and
  contextlib, organizing imports, or deciding the idiomatic ("Pythonic") way to express
  something. For where code should live — splitting modules, naming subpackages, layering,
  and import direction — use python-project-structure; for Gang-of-Four design patterns
  (Strategy, Adapter, Observer, Builder) and how
  objects should collaborate use python-design-patterns; for class design use python-oop; for
  dunder methods, including implementing `__enter__`/`__exit__`, use python-data-model; for
  decorators, descriptors, and metaclasses use python-metaprogramming; for threads, asyncio,
  and processes use python-concurrency; for tests use python-testing; for logging use
  python-logging.
---

# Python Idioms

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
| Comparisons | `is None`, `isinstance(value, SomeType)` — never `== None` or `type(value) == SomeType`. |

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

This skill owns expression-level idioms — how to write *this statement*. Where modules and
packages live, what a package exports, and which way imports flow →
**python-project-structure**. Named design
patterns and how several objects collaborate → **python-design-patterns**. Class/dataclass/
protocol design → **python-oop**. Dunder methods and custom iterators → **python-data-model**.
Decorators, descriptors, and metaclasses → **python-metaprogramming**. Tests →
**python-testing**. Logging → **python-logging**. Threads/asyncio/processes → **python-concurrency**.
See `reference.md` for the full catalog (typing, context managers, generators, imports,
anti-patterns) and the
design principles that live here: fail fast, separation of concerns, KISS/YAGNI/least
surprise. The project `CLAUDE.md` lists the full principle set (SOLID and general).
