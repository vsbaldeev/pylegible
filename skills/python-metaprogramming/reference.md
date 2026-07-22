# Python Metaprogramming — reference catalog

Depth for `python-metaprogramming`, distilled from *Fluent Python* (Ramalho) — ch. 9 for
closures and decorators, Part V (ch. 22–24) for the class-level machinery. Load
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
    """Retry the wrapped call up to `times` times.

    Raises:
        ValueError: If `times` is less than 1.
    """
    if times < 1:
        raise ValueError(f"times must be at least 1, got {times}")

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
    """Decorator object that counts how many times the wrapped callable ran."""

    def __init__(self, function: Callable) -> None:
        """Wrap `function` and start the counter at zero."""
        functools.update_wrapper(self, function)
        self.function = function
        self.count = 0

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Count this call and delegate to the wrapped function."""
        self.count += 1
        return self.function(*args, **kwargs)

    def __get__(self, instance: object, owner: type) -> Callable:
        """Bind to `instance` so the decorator also works on methods."""
        if instance is None:
            return self
        return functools.partial(self, instance)
```

The `__get__` is what makes a class-based decorator usable on a *method*: a plain function is
a descriptor and binds itself to the instance, but an instance of `CountCalls` is not, so
without it `self` is never passed and the decorated method loses its receiver.

## Class decorators

A class decorator takes a class and returns it, usually augmented. Prefer it to a metaclass
whenever you only need to touch a class *after* it is built — it is a plain function and
composes with other decorators.

```python
def add_repr(cls: type) -> type:
    """Give a class a field-based __repr__ derived from its instance dict.

    Raises:
        TypeError: If the class already defines its own __repr__.
    """
    if "__repr__" in vars(cls):
        raise TypeError(f"{cls.__name__} already defines __repr__")

    @reprlib.recursive_repr()
    def __repr__(self: object) -> str:
        fields = ", ".join(f"{name}={value!r}" for name, value in vars(self).items())
        return f"{type(self).__name__}({fields})"

    cls.__repr__ = __repr__
    return cls

@add_repr
class Point:
    """A point in the plane."""
    def __init__(self, x: float, y: float) -> None:
        """Store the coordinates."""
        self.x = x
        self.y = y
```

Two details that bite in real code, and are why the guard and `reprlib` are there: overwriting
`__repr__` silently would discard a hand-written one, and a container that (directly or
indirectly) holds itself would recurse forever without `reprlib.recursive_repr`. Note also that
`vars(self)` needs an instance `__dict__` — on a `__slots__` class it raises `TypeError`, so
build the field list from `__slots__` there (or just use `@dataclass`, which solves all three).

## Descriptors

A descriptor is a reusable managed attribute: a class implementing `__get__`/`__set__` that
lives as a class attribute on the owner. Use it to factor validation shared by many attributes.

```python
class Positive:
    """A data descriptor enforcing a positive number."""

    def __set_name__(self, owner: type, name: str) -> None:
        """Record the per-instance slot this descriptor stores its value in."""
        self.storage_name = f"__{name}"

    def __get__(self, instance: object, owner: type) -> "float | Positive":
        """Return the stored value, or the descriptor itself on class access."""
        if instance is None:
            return self
        return getattr(instance, self.storage_name)

    def __set__(self, instance: object, value: float) -> None:
        """Store `value`, rejecting anything not strictly positive."""
        if value <= 0:
            raise ValueError(f"{self.storage_name} must be positive, got {value}")
        setattr(instance, self.storage_name, value)

class Order:
    """An order with validated numeric fields."""
    quantity = Positive()
    price = Positive()
```

The `instance is None` guard is not optional: without it, class-level access
(`Order.quantity` — which is what `help()`, `inspect`, and most doc tooling does) calls
`getattr(None, ...)` and blows up with an `AttributeError` naming the wrong object.

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

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Create the class, rejecting any base that is itself sealed.

        Raises:
            TypeError: If any base class was created by this metaclass.
        """
        for base in bases:
            if isinstance(base, SealedMeta):
                raise TypeError(f"{base.__name__} is sealed and cannot be subclassed")
        return super().__new__(mcs, name, bases, namespace, **kwargs)

class Config(metaclass=SealedMeta):
    """Application configuration — sealed, so nothing may subclass it."""
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
        """Store the mapping that unknown attributes are resolved against."""
        self.source = source

    def __getattr__(self, name: str) -> str:
        """Resolve a missing attribute from the source mapping.

        Raises:
            AttributeError: If the name is a dunder or absent from the mapping.
        """
        if name.startswith("__"):
            raise AttributeError(name)
        source = self.__dict__.get("source")      # not self.source — see below
        if source is None:
            raise AttributeError(name)
        try:
            return source[name]
        except KeyError:
            raise AttributeError(name) from None
```

Two traps here, both about re-entry. **First:** writing `self.source` inside `__getattr__`
looks safe — it is a real instance attribute, so normal lookup usually finds it and
`__getattr__` is never re-entered. But *usually* is doing the work. Whenever an instance
exists without `__init__` having run — `copy.copy`, `pickle.loads`, `object.__new__` — the
attribute is missing, so `self.source` misses, calls `__getattr__("source")`, which evaluates
`self.source` again: `RecursionError`. Reading `self.__dict__` instead cannot re-enter, because
`__dict__` is found on the type. **Second:** raise `AttributeError` for dunders rather than
looking them up, so `copy`/`pickle` see a clean "not implemented" and fall back to their
defaults. And always raise `AttributeError` (never `KeyError`) for a genuinely missing name, so
`hasattr` and `getattr(obj, name, default)` behave.

## Dynamic class creation (`type()`)

`type(name, bases, namespace)` builds a class at runtime — exactly what the `class` statement
does under the hood. Reserve it for cases where the class shape is known only at runtime; a
normal `class` statement is clearer everywhere else.

```python
def make_record(name: str, fields: tuple[str, ...]) -> type:
    """Build a record class with the given fields at runtime."""
    def __init__(self, **values: object) -> None:
        missing = sorted(set(fields) - values.keys())
        unexpected = sorted(values.keys() - set(fields))
        if missing or unexpected:
            raise TypeError(f"{name}: missing fields {missing}, unexpected {unexpected}")
        for field in fields:
            setattr(self, field, values[field])
    return type(name, (), {"__init__": __init__})

Point = make_record("Point", ("x", "y"))
point = Point(x=1, y=2)
```

In practice `@dataclass` or `collections.namedtuple` beat hand-rolled `type()` for records —
use dynamic creation only when the fields truly are not known until runtime.

## Further reading

- **Fluent Python**, 2nd ed. (Ramalho) — ch. 9 *Decorators and Closures* (and ch. 7 on
  first-class functions), then Part V *Metaprogramming*: ch. 22 Dynamic Attributes and
  Properties, ch. 23 Attribute Descriptors, ch. 24 Class Metaprogramming. The source these
  recipes distill.
- **Descriptor Guide** — the authoritative official walkthrough of how `property`, methods, and
  `classmethod` are built on descriptors: `docs.python.org/3/howto/descriptor.html`
- **Data model reference** — the full dunder catalog, including `__set_name__`,
  `__init_subclass__`, and `__mro_entries__`: `docs.python.org/3/reference/datamodel.html`
