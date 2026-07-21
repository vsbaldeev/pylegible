# Python Metaprogramming — reference catalog

Depth for `python-metaprogramming`, distilled from *Fluent Python* (Ramalho), Part V. Load
when you need a specific technique. The rule throughout: **use the lightest tool that works**,
and prefer a plain function or class whenever one reads as clearly.

## Closures and first-class functions

Functions are objects: pass them, store them, return them. A closure captures variables from
the enclosing scope; use `nonlocal` to rebind them. Closures are the foundation decorators
are built on.

```python
def make_counter() -> Callable[[], int]:
    """Return a function that yields 1, 2, 3, ... on successive calls."""
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

## Class decorators

A class decorator takes a class and returns it, usually augmented. Prefer it to a metaclass
whenever you only need to touch a class *after* it is built — it is a plain function and
composes with other decorators.

```python
def add_repr(cls: type) -> type:
    """Give a class a field-based __repr__ derived from its instance dict."""
    def __repr__(self: object) -> str:
        fields = ", ".join(f"{name}={value!r}" for name, value in vars(self).items())
        return f"{type(self).__name__}({fields})"
    cls.__repr__ = __repr__
    return cls

@add_repr
class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
```

## Descriptors

A descriptor is a reusable managed attribute: a class implementing `__get__`/`__set__` that
lives as a class attribute on the owner. Use it to factor validation shared by many attributes.

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
reach for a plain `@property` first, and use a custom descriptor only when the same managed
behavior repeats across several attributes.

## Subclass hooks (`__init_subclass__`)

`__init_subclass__` is an implicit classmethod called when a *subclass* is defined — the
modern hook for registering, validating, or configuring subclasses without a metaclass.
Keyword arguments in the class statement arrive as parameters. Use it to enforce a contract
at definition time (fail fast) rather than waiting for an instance:

```python
class Serializer:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "content_type"):
            raise TypeError(f"{cls.__name__} must define content_type")
```

`__set_name__` (shown above under descriptors) is the companion hook for attributes: the owner
class tells each descriptor the name it was assigned to, at class-creation time.

## Metaclasses (last resort)

A metaclass is a class whose instances are classes; it customizes class *creation* itself by
overriding `type.__new__`/`__init__`. You rarely need one — `__init_subclass__` (customize
subclasses) and class decorators (augment a built class) cover almost every real case. Reach
for a metaclass only when you must shape the class-body namespace (`__prepare__`) or intercept
creation of the base class itself, which subclass hooks cannot.

```python
class SealedMeta(type):
    """Metaclass that forbids subclassing any class it creates."""
    def __new__(mcs, name, bases, namespace):
        for base in bases:
            if isinstance(base, SealedMeta):
                raise TypeError(f"{base.__name__} is sealed and cannot be subclassed")
        return super().__new__(mcs, name, bases, namespace)

class Config(metaclass=SealedMeta):
    ...
```

## Dynamic attributes (`__getattr__` / `__setattr__`)

`__getattr__(self, name)` is called only when normal lookup *fails* — the clean hook for
computed or proxied attributes. `__setattr__` intercepts *every* assignment, so route through
`super().__setattr__` to avoid recursion. Avoid `__getattribute__` (called on every read)
unless truly unavoidable.

```python
class LazyConfig:
    """Expose config keys as attributes, reading the source dict on a miss."""
    def __init__(self, source: dict[str, str]) -> None:
        self.source = source

    def __getattr__(self, name: str) -> str:
        try:
            return self.source[name]
        except KeyError:
            raise AttributeError(name) from None
```

`self.source` inside `__getattr__` does not recurse: it is a real instance attribute, so normal
lookup finds it and `__getattr__` is never re-entered. Always raise `AttributeError` (not
`KeyError`) for a genuinely missing name, so `hasattr`/`getattr` defaults behave.

## Dynamic class creation (`type()`)

`type(name, bases, namespace)` builds a class at runtime — exactly what the `class` statement
does under the hood. Reserve it for cases where the class shape is known only at runtime; a
normal `class` statement is clearer everywhere else.

```python
def make_record(name: str, fields: tuple[str, ...]) -> type:
    """Build a record class with the given fields at runtime."""
    def __init__(self, **values: object) -> None:
        for field in fields:
            setattr(self, field, values[field])
    return type(name, (), {"__init__": __init__})

Point = make_record("Point", ("x", "y"))
point = Point(x=1, y=2)
```

In practice `@dataclass` or `collections.namedtuple` beat hand-rolled `type()` for records —
use dynamic creation only when the fields truly are not known until runtime.

## Further reading

- **Fluent Python**, 2nd ed. (Ramalho) — Part V *Metaprogramming*: ch. 22 Dynamic Attributes
  and Properties, ch. 23 Attribute Descriptors, ch. 24 Class Metaprogramming. The source these
  recipes distill.
- **Descriptor Guide** — the authoritative official walkthrough of how `property`, methods, and
  `classmethod` are built on descriptors: `docs.python.org/3/howto/descriptor.html`
- **Data model reference** — the full dunder catalog, including `__set_name__`,
  `__init_subclass__`, and `__mro_entries__`: `docs.python.org/3/reference/datamodel.html`
