# Python Idioms — reference catalog

Depth for `python-idioms`. Load when you need the details behind a rule. Every example
here follows house convention: no single-letter names, no leading single underscore,
≤40-line bodies, Google-style docstrings.

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

Version notes:

- On 3.14+ (PEP 758) you may drop the parentheses when catching several types without `as`:
  `except (TypeError, ValueError):` can be written `except TypeError, ValueError:`.
- Never `return`, `break`, or `continue` out of a `finally` block — it silently discards any
  in-flight exception. Python 3.14+ flags this with a `SyntaxWarning` (PEP 765).
- Mark obsolete APIs with `@warnings.deprecated("use X instead")` (3.13+, PEP 702): it warns
  callers at runtime and is understood by type checkers.

## Fail fast

Surface bad state at its source, loudly — never let it travel and corrupt something far
away, where the traceback no longer points at the cause. Validate inputs at the boundary
and raise; do not paper over problems with a silent default.

```python
# Fail fast: reject the bad value where it enters
def set_retry_count(count: int) -> None:
    if count < 0:
        raise ValueError(f"retry count must be >= 0, got {count}")
    ...

# Slow failure: a bad value survives and blows up somewhere unrelated later
def set_retry_count(count: int) -> None:
    self.count = count if count >= 0 else 0   # silently rewrites the caller's intent
```

The bare-`except`-then-`return None` anti-pattern is the opposite of failing fast: it hides
the error and hands back a value that lies. Catch what you can handle; let the rest raise.

## Separation of concerns

Keep I/O, business logic, and presentation in separate functions or layers. A function
that reads a file, computes a result, and prints it is three responsibilities welded
together — hard to test and hard to reuse.

```python
def load_orders(path: Path) -> list[Order]:      # I/O
    ...
def total_due(orders: list[Order]) -> Money:     # logic — pure, trivially testable
    ...
def render_invoice(total: Money) -> str:         # presentation
    ...
```

The pure logic in the middle needs no files or mocks to test. Logs and diagnostics are a
presentation concern too — see python-logging for stdout-vs-stderr.

## Simplicity: KISS, YAGNI, least surprise

- **KISS** — reach for the simplest construct that works. A loop over a clever nested
  comprehension; a function over a class; a dict over a small framework.
- **YAGNI** — build for the requirement in front of you, not an imagined future one.
  Add the extension point when the second case actually arrives.
- **Least surprise** — code should behave the way a reader expects. No side effects hidden
  behind an innocent-looking name; no function that returns different types by mood.

Needless indirection fails KISS the same way needless cleverness does — a function that adds
no behavior is a detour, not an abstraction:

```python
# Needless: adds a name to trace through, changes nothing
def get_user(user_id: str) -> User:
    return fetch_user(user_id)

# Call fetch_user directly instead — no wrapper needed
```

A wrapper earns its place only when it changes something: adapts a signature, adds a default,
narrows a type, adds logging/caching/error translation. Delegation with zero added behavior
is a rename in disguise.

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
- Narrow with `typing.TypeIs` (3.13+) for a predicate that both tests and narrows a type —
  reads more naturally than `TypeGuard`:

  ```python
  def is_nonempty(value: str | None) -> TypeIs[str]:
      return bool(value)
  ```

**Deferred annotations (3.14+).** PEP 649/749 evaluate annotations lazily, so
`from __future__ import annotations` is no longer needed and forward references drop their
quotes (`-> Vector2D`, not `-> "Vector2D"`). Inspect them at runtime with
`annotationlib.get_annotations(...)`. On 3.13 and earlier, keep the quotes or the `__future__`
import.

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

## Definition order

Define a function or method above the code that calls it. The file then reads top-down from
building blocks to the code that composes them, and no line refers to a name the reader has
not yet seen.

```python
def parse_line(line: str) -> Record:
    """Parse one CSV line into a record."""
    ...


def parse_file(path: Path) -> list[Record]:
    """Parse every line of a file."""
    return [parse_line(line) for line in path.read_text().splitlines()]
```

The same holds inside a class: a helper method sits above the method that calls it. Python
allows either order at call time; this is a readability rule, not a language requirement.
Mutually recursive functions cannot both come first — keep them adjacent.

## Imports

Order: standard library, third-party, local — each group separated by a blank line, sorted
(isort/ruff enforce it). Avoid `from module import *` — import the module, or the specific
names you use, so a reader can trace where each name came from.

Use absolute imports only (`from mypackage.orders.pricing import calculate_total`) —
unambiguous, greppable, and stable when a file moves within the package. Do not use relative
imports (`from . import pricing`), even one level deep; if the absolute path feels verbose,
that is a hint the module is in the wrong place — see python-project-structure.
(ruff `TID252` enforces this.)

Put every import at the top of the module, before any other code. Two exceptions, each marked
with a comment saying why: breaking a circular import, and an optional or heavy dependency
imported inside the function that needs it. Imports under `if TYPE_CHECKING:` also stay at the
top level of the module. (ruff `E402` and `PLC0415` enforce this.)

```python
# Do: absolute, at the top of the module
from orders.domain.pricing import calculate_total

# Don't: relative, at any depth
from . import pricing
from ...domain.pricing import calculate_total

def export_report(rows):
    # Don't: import buried in a function without a reason
    import csv

def load_model():
    # Allowed: optional heavy dependency, deferred on purpose
    import torch  # heavy; only needed when a model is loaded
```

Where modules and packages live, what a package exports through `__init__.py`, and which way
imports may flow between them → **python-project-structure**.

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
