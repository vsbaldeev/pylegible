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

## First-class functions and closures

Functions are objects: pass them, store them, return them. A closure captures variables
from the enclosing scope; use `nonlocal` to rebind them.

```python
def make_counter() -> Callable[[], int]:
    count = 0
    def next_value() -> int:
        nonlocal count
        count += 1
        return count
    return next_value
```

## Decorators

A decorator is a callable that takes a function and returns a replacement. Always
`functools.wraps` to preserve the wrapped function's identity.

Parameterized decorator (three nested layers):

```python
def retry(times: int) -> Callable[[Callable], Callable]:
    """Retry the wrapped call up to `times` times."""
    def decorator(function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return function(*args, **kwargs)
                except TransientError:
                    if attempt == times:
                        raise
        return wrapper
    return decorator
```

Class-based decorator (state across calls via an instance):

```python
class CountCalls:
    def __init__(self, function: Callable) -> None:
        functools.update_wrapper(self, function)
        self.function = function
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.function(*args, **kwargs)
```

## Descriptors

A descriptor is a reusable managed attribute: a class implementing `__get__`/`__set__`
that lives as a class attribute on the owner. Use it to factor validation shared by many
attributes.

```python
class Positive:
    """A data descriptor enforcing a positive number."""
    def __set_name__(self, owner: type, name: str) -> None:
        self.storage_name = f"__{name}"

    def __get__(self, instance: object, owner: type) -> float:
        return getattr(instance, self.storage_name)

    def __set__(self, instance: object, value: float) -> None:
        if value <= 0:
            raise ValueError(f"{self.storage_name} must be positive, got {value}")
        setattr(instance, self.storage_name, value)

class Order:
    quantity = Positive()
    price = Positive()
```

Descriptors power `property`, methods, `classmethod`, and `staticmethod` under the hood —
reach for a plain `@property` first, and use a custom descriptor only when the same
managed behavior repeats across several attributes.

## Context managers

`__enter__`/`__exit__` make an object usable with `with`. Return `False` from `__exit__`
to let exceptions propagate. For simple cases prefer `@contextmanager` (see
python-patterns) over writing the class.
