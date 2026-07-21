# Python Patterns — reference catalog

Depth for `python-patterns`. Load when you need the details behind a rule. Every example
here obeys the house conventions in the project `CLAUDE.md` (no single-letter names, no
leading single underscore, ≤40-line bodies, Google-style docstrings).

## EAFP over LBYL

Prefer trying the operation and handling the exception over pre-checking conditions.

```python
# EAFP — one lookup, clear intent
def get_setting(settings: dict[str, str], key: str, default: str = "") -> str:
    try:
        return settings[key]
    except KeyError:
        return default

# LBYL — double lookup, races if the dict changes between check and use
def get_setting(settings: dict[str, str], key: str, default: str = "") -> str:
    if key in settings:
        return settings[key]
    return default
```

## Error handling

Catch the narrowest exception that fits, translate it to your domain, and preserve the
cause with `from`.

```python
def load_config(path: Path) -> Config:
    try:
        with path.open(encoding="utf-8") as handle:
            return Config.from_json(handle.read())
    except FileNotFoundError as error:
        raise ConfigError(f"Config file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in config: {path}") from error
```

Define a small exception hierarchy per package so callers can catch by category:

```python
class AppError(Exception):
    """Base class for this application's errors."""


class ValidationError(AppError):
    """Input failed validation."""


class NotFoundError(AppError):
    """A requested resource does not exist."""
```

## Type hints

Annotate every signature. Use built-in generics; use `X | None` over `Optional[X]`.

```python
def first_match(values: list[str], prefix: str) -> str | None:
    """Return the first value starting with prefix, or None."""
    for value in values:
        if value.startswith(prefix):
            return value
    return None
```

- Alias complex unions: `Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None`.
- Use `TypeVar` for generic helpers; `Protocol` for structural typing (see python-oop).

## Context managers

Use `with` for anything that must be released. Write your own with `contextmanager`.

```python
from contextlib import contextmanager

@contextmanager
def timed(label: str) -> Iterator[None]:
    """Log how long the wrapped block takes."""
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("%s took %.4fs", label, time.perf_counter() - start)
```

## Comprehensions and generators

Comprehensions are for a single map and/or filter. Anything more (two conditions, a
nested loop, side effects) reads better as a named loop or helper.

```python
# Fine: one map, one filter
active_names = [user.name for user in users if user.is_active]

# Too dense: extract a helper instead
def even_doubles(numbers: Iterable[int]) -> list[int]:
    result = []
    for number in numbers:
        if number > 0 and number % 2 == 0:
            result.append(number * 2)
    return result
```

Use a generator (not a list) when the caller only iterates, or the data is large:

```python
def read_lines(path: Path) -> Iterator[str]:
    """Yield each stripped line without loading the whole file."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            yield line.strip()
```

## Imports and packaging

Order: standard library, third-party, local — each group separated by a blank line, sorted
(isort/ruff enforce it). Avoid `from module import *`. Prefer a `src/` layout:

```
project/
  src/mypackage/__init__.py
  tests/
  pyproject.toml
```

Export the public surface explicitly in `__init__.py` with `__all__`.

## Concurrency (pick the right model)

- I/O-bound → threads (`concurrent.futures.ThreadPoolExecutor`) or `asyncio`.
- CPU-bound → processes (`ProcessPoolExecutor`).
- Don't reach for concurrency until a profiler says you need it.

## Anti-patterns

| Anti-pattern | Instead |
|---|---|
| Mutable default arg `def add(item, items=[])` | Default `None`, create inside |
| Bare `except:` then `return None` | Catch specific exception, let others propagate |
| `type(obj) == list` | `isinstance(obj, list)` |
| `value == None` | `value is None` |
| `from os.path import *` | `from os.path import join, exists` |
| Building strings with `+=` in a loop | `"".join(parts)` |
| Comment explaining a cryptic name | Rename so the comment is unnecessary |
