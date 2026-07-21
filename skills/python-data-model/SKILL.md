---
name: python-data-model
description: >
  Use when implementing special ("dunder") methods, making a class support operators,
  len(), iteration, unpacking, or use as a dict key, building custom sequences or
  iterators, writing descriptors, or writing parameterized or class-based decorators.
  For ordinary class design use python-oop; for general idioms use python-patterns.
---

# Python Data Model

## Overview

Python's power comes from the data model: implement the right dunder methods and your
objects work with the language's own syntax — `+`, `==`, `len()`, `for`, `with`,
unpacking. Recipes here are distilled from *Fluent Python* (Luciano Ramalho). Implement
only the protocol you actually need, and honor its contracts. Depth in `reference.md`.

## When to use

- Making a class behave like a number, sequence, or container.
- Supporting operators, iteration, unpacking, or dict-key use.
- Writing a descriptor (reusable managed attribute) or a non-trivial decorator.

## Contracts you must not break

| If you implement… | You must also… |
|---|---|
| `__eq__` | implement `__hash__` (or set `__hash__ = None`); equal objects hash equal. |
| a hashable value object | make it immutable (`frozen=True` or block `__setattr__`). |
| `__eq__` / arithmetic dunders | return `NotImplemented` for unsupported types, not raise. |
| `__repr__` | make it unambiguous (ideally reconstructable), using `!r` on parts. |
| an iterator (`__next__`) | also return `self` from `__iter__`. |

## Example

```python
class Vector2D:
    """An immutable 2D vector. (x, y are the conventional component names.)"""
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vector2D({self.x!r}, {self.y!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __add__(self, other: "Vector2D") -> "Vector2D":
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(self.x + other.x, self.y + other.y)

    def __iter__(self) -> Iterator[float]:   # enables: x, y = vector
        yield self.x
        yield self.y
```

## Common mistakes

- `__eq__` without `__hash__` — the class silently becomes unhashable.
- Mutable objects used as dict keys — the hash changes and lookups break.
- Raising `TypeError` from `__add__`/`__eq__` instead of returning `NotImplemented`.
- A `__repr__` that reads like `__str__` (pretty, ambiguous) — repr is for developers.
- Reaching for dunders when a plain method with a clear name would read better.

## Boundary

This skill owns the data model and metaprogramming, including decorator authoring
(`functools.wraps`, parameterized, and class-based). Ordinary class design (dataclasses,
Protocol vs ABC, composition) → **python-oop**. General idioms and error handling →
**python-patterns**. See `reference.md` for the sequence protocol,
slicing, closures, descriptors, advanced decorators, `__bool__`/`__format__`/`__call__`,
alternative constructors, `collections.abc`, structural pattern matching, and async protocols.
