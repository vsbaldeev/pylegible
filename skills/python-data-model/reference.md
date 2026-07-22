# Python Data Model — reference catalog

Depth for `python-data-model`, distilled from *Fluent Python* (Ramalho). Load when you
need a specific protocol.

## The data model in one idea

Built-in syntax and functions are dispatched to dunder methods: `len(obj)` calls
`obj.__len__()`, `obj[key]` calls `obj.__getitem__(key)`, `a + b` calls `a.__add__(b)`,
`for x in obj` calls `obj.__iter__()`. You do not call dunders directly — you implement
them so the language's own syntax works on your object.

## String representations

- `__repr__` — unambiguous, for developers; ideally `eval(repr(obj)) == obj`. Use `!r`.
- `__str__` — readable, for end users. Defaults to `__repr__` if omitted.

```python
def __repr__(self) -> str:
    return f"Card({self.rank!r}, {self.suit!r})"
```

## Truthiness (`__bool__`)

Every instance is truthy by default. Define `__bool__` to control what `if obj:` means; if
it is absent, Python falls back to `__len__` (length zero is false). Keep it cheap.

```python
class Vector2D:
    def __bool__(self) -> bool:
        return bool(self.x or self.y)   # the zero vector is falsy
```

## Formatting (`__format__`)

`format(obj, spec)` and an f-string's `f"{obj:spec}"` both dispatch to `obj.__format__(spec)`.
An empty spec should match `str(obj)`; otherwise interpret the spec however suits the type.

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self.celsius = celsius

    def __str__(self) -> str:
        return f"{self.celsius}C"

    def __format__(self, spec: str) -> str:
        if not spec:
            return str(self)
        return f"{format(self.celsius, spec)}C"   # f"{temp:.1f}" -> "20.5C"
```

## Rich comparison and hashing

Implement `__eq__` and pair it with `__hash__`. Equal objects must have equal hashes; base
both on the same tuple of fields. A class that defines `__eq__` but not `__hash__` becomes
unhashable unless you restore it.

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Money):
        return NotImplemented
    return (self.amount, self.currency) == (other.amount, other.currency)

def __hash__(self) -> int:
    return hash((self.amount, self.currency))
```

Only hashable-and-immutable objects are safe as dict keys or set members.

## Operator overloading

Return `NotImplemented` (not raise) when the other operand is unsupported, so Python can
try the reflected operation. Provide `__radd__`/`__rmul__` for `scalar * vector`.

```python
def __mul__(self, scalar: float) -> "Vector2D":
    if not isinstance(scalar, (int, float)):
        return NotImplemented
    return Vector2D(self.x * scalar, self.y * scalar)

def __rmul__(self, scalar: float) -> "Vector2D":
    return self * scalar
```

On Python 3.14+, using `NotImplemented` in a boolean context raises `TypeError`. That turns a
subtle bug loud: if you ever branch on a special method's raw result (`if left.__eq__(right):`),
a returned `NotImplemented` now fails immediately instead of reading as truthy. Return the
sentinel; never test it.

## Modified copies (`__replace__`, Python 3.13+)

`copy.replace(obj, field=value)` returns a copy of an immutable object with some fields
changed — the readable way to "edit" a frozen value object without mutating it. Dataclasses,
named tuples, and `datetime` already support it; a plain class opts in with `__replace__`.

```python
import copy

class Vector2D:
    def __replace__(self, /, **changes: float) -> "Vector2D":
        return Vector2D(changes.get("x", self.x), changes.get("y", self.y))

shifted = copy.replace(origin, x=10)   # origin untouched; shifted is a new vector
```

## The sequence protocol and slicing

`__len__` + `__getitem__` make an object indexable, iterable, and sliceable. Handle
`slice` objects by delegating to the underlying sequence, and return your own type:

```python
class Deck:
    def __init__(self, cards: list[Card]) -> None:
        self.__cards = cards

    def __len__(self) -> int:
        return len(self.__cards)

    def __getitem__(self, position: int | slice) -> "Card | Deck":
        result = self.__cards[position]
        return Deck(result) if isinstance(position, slice) else result
```

Implementing `__getitem__` alone already makes the object iterable (Python falls back to
integer indexing from 0).

## Iterators vs iterables

An **iterable** returns a fresh **iterator** from `__iter__`. Keep them separate so the
object can be iterated many times. The iterator implements `__next__` and returns `self`
from `__iter__`.

```python
class Sentence:
    def __init__(self, text: str) -> None:
        self.words = text.split()

    def __iter__(self) -> Iterator[str]:
        return iter(self.words)          # simplest: delegate to a generator/iterator
```

Prefer a generator function/expression over a hand-written `__next__` class — it is
shorter and correct by construction.

## Callable instances (`__call__`)

Define `__call__` to make an instance behave like a function while keeping state. Prefer it
over a closure when the object also needs other methods or a meaningful `repr`.

```python
class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.calls = 0

    def __call__(self, request: Request) -> bool:
        """Return True if this request stays within the limit."""
        self.calls += 1
        return self.calls <= self.per_minute
```

## Alternative constructors (`@classmethod`)

Offer a named, secondary way to build an instance with a `@classmethod`. Return `cls(...)`
so subclasses build their own type.

```python
class Vector2D:
    @classmethod
    def from_polar(cls, radius: float, angle: float) -> "Vector2D":
        """Build a vector from polar coordinates."""
        return cls(radius * math.cos(angle), radius * math.sin(angle))
```

Use `@staticmethod` only for a helper that needs neither `self` nor `cls` — often a plain
module-level function reads better.

## Reusing the ABCs in `collections.abc`

Inherit from an ABC like `Sequence` or `Mapping` and you get mixin methods for free: define a
couple of required methods and the ABC supplies the rest, correctly.

```python
from collections.abc import Sequence

class Deck(Sequence):
    def __init__(self, cards: list[Card]) -> None:
        self.cards = cards

    def __len__(self) -> int:
        return len(self.cards)

    def __getitem__(self, position: int | slice) -> "Card | list[Card]":
        return self.cards[position]
    # Sequence now supplies __contains__, __iter__, __reversed__, index, count
```

In annotations, prefer the abstract type you actually need (`Iterable`, `Mapping`,
`Sequence`) over a concrete `list`/`dict` when you only depend on the protocol.

## Structural pattern matching (`__match_args__`)

`match`/`case` can destructure your objects positionally when you declare `__match_args__`
(dataclasses set it from field order automatically).

```python
class Point:
    __match_args__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

def quadrant(point: Point) -> str:
    """Name the quadrant a point sits in."""
    match point:
        case Point(0, 0):
            return "origin"
        case Point(x, y) if x > 0 and y > 0:
            return "first"
        case _:
            return "other"
```

## Async protocols

Async iteration and async context managers mirror their sync forms with `a`-prefixed
dunders, driven by `async for` and `async with`.

```python
class Ticker:
    def __init__(self, interval: float, count: int) -> None:
        self.interval = interval
        self.count = count

    def __aiter__(self) -> "Ticker":
        self.remaining = self.count
        return self

    async def __anext__(self) -> int:
        if self.remaining == 0:
            raise StopAsyncIteration
        await asyncio.sleep(self.interval)
        self.remaining -= 1
        return self.remaining


class Connection:
    async def __aenter__(self) -> "Connection":
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        await self.close()
        return False           # do not suppress exceptions
```

Prefer an `async def` generator (with `yield`) over a hand-written `__anext__` class, just as
with sync iterators. This skill covers the *protocol* dunders; for choosing and running a
concurrency model (asyncio event loop, `TaskGroup`, threads vs processes) see
**python-concurrency**.

## Context managers

`__enter__`/`__exit__` make an object usable with `with`. Return `False` from `__exit__`
to let exceptions propagate. For simple cases prefer `@contextmanager` (see
python-idioms) over writing the class.
