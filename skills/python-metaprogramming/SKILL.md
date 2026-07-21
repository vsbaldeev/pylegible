---
name: python-metaprogramming
description: >
  Use when writing decorators (function or class, parameterized), descriptors, metaclasses,
  __init_subclass__, dynamic attribute access (__getattr__/__setattr__), class decorators, or
  creating classes dynamically with type(). For operator and protocol dunders (__eq__,
  __iter__, __len__, __call__) use python-data-model; for ordinary class design use python-oop.
---

# Python Metaprogramming

## Overview

Metaprogramming is code that manipulates code — functions that wrap functions, attributes
that intercept access, classes that shape other classes. It is powerful and easy to overuse:
every layer of indirection is a layer the next reader must unwind. Reach for the lightest
tool that does the job, and metaprogram only when a plain function or class genuinely cannot.
Recipes distilled from *Fluent Python* (Ramalho). Depth in `reference.md`.

## When to use

- Factoring cross-cutting behavior around functions (retry, caching, timing) → decorators.
- Reusing the same managed-attribute logic across many attributes → descriptors.
- Registering, validating, or configuring every subclass at class-creation time.
- Intercepting attribute access for a genuinely dynamic object.

## Reach for the lightest tool

| Need | Reach for | Not |
|---|---|---|
| Run code around a function | decorator | metaclass |
| Reuse managed-attribute logic across attributes | descriptor | copy-pasted `property` |
| Register/validate each subclass at creation | `__init_subclass__` | metaclass |
| Augment a class after it is defined | class decorator | metaclass |
| Control class *creation* itself (very rare) | metaclass | — |

A metaclass is the heaviest tool and the last resort — `__init_subclass__` and class
decorators cover almost everything people once wrote metaclasses for.

## Core rules

- Every function decorator uses `functools.wraps` (or `update_wrapper`) so the wrapper keeps
  the original's name, docstring, and signature — otherwise `help()` and introspection break.
- Descriptors live as class attributes and store per-instance state under a name derived in
  `__set_name__` — never in one slot on the descriptor, which would share state across instances.
- Prefer `__init_subclass__` (a subclass hook) and class decorators over metaclasses.
- Override `__getattr__` (called only on *missing* attributes) for dynamic access; leave
  `__getattribute__` (called on *every* access) alone unless you must, and delegate to
  `super()` to avoid infinite recursion.
- Fail loud: a descriptor or hook that receives a bad value raises, never silently coerces.

## Example

```python
class Handler:
    """Base class that auto-registers every concrete subclass by key."""
    registry: dict[str, type["Handler"]] = {}

    def __init_subclass__(cls, /, key: str, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.registry[key] = cls

class JsonHandler(Handler, key="json"):
    ...

class CsvHandler(Handler, key="csv"):
    ...

# Handler.registry == {"json": JsonHandler, "csv": CsvHandler} — no metaclass required
```

## Common mistakes

- Writing a metaclass for something `__init_subclass__` or a class decorator does — needless
  indirection most readers cannot follow.
- Forgetting `functools.wraps`, so the wrapped function loses its name/docstring and tooling
  can no longer see through the wrapper.
- A descriptor storing state on itself (`self.value = ...`) instead of per-instance — every
  instance then shares one value.
- Overriding `__getattribute__` and recursing forever by touching `self.x` inside it instead
  of `super().__getattribute__(...)`.
- Metaprogramming where a plain function, class, or `@property` would read clearly.

## Boundary

This skill owns code that manipulates code: decorators, descriptors, metaclasses,
`__init_subclass__`, dynamic attribute access, class decorators, and dynamic class creation
with `type()`. Operator and protocol dunders that make an object work with syntax (`__eq__`,
`__iter__`, `__len__`, `__call__`, `__enter__`) → **python-data-model**. Ordinary class and
interface design (dataclasses, Protocol/ABC, composition) → **python-oop**. General idioms and
error handling → **python-patterns**. See `reference.md` for closures, parameterized and
class-based decorators, descriptors, metaclasses vs `__init_subclass__`, dynamic attributes,
and the *Fluent Python* chapters behind them.
