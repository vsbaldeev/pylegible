---
name: python-oop
description: >
  Use when designing Python classes and object structure — deciding whether something
  should be a class at all, using dataclasses, defining interfaces with Protocol or ABC,
  choosing composition over inheritance, applying SOLID pragmatically, or encapsulating
  state. For dunder methods, descriptors, and custom iteration use python-data-model.
---

# Python OOP

## Overview

A class earns its place when data and the behavior over it belong together, or when you
need several interchangeable implementations behind one interface. If a plain function
would read as clearly, write the function. Favor composition and small interfaces over
deep inheritance. Depth in `reference.md`.

## When to use

- Modeling a domain concept that bundles state with behavior.
- Designing interchangeable implementations behind a shared interface.
- Refactoring a "god class" or a tangled inheritance hierarchy.

## Core decisions

| Question | Default answer |
|---|---|
| Class or function? | Function, unless state + behavior clearly belong together. |
| Just holding data? | `@dataclass` (add `frozen=True` if it should be immutable). |
| Defining an interface? | `Protocol` (structural, no inheritance needed by implementers). |
| Sharing real behavior across subclasses? | `ABC` with concrete methods + `@abstractmethod`. |
| Reuse: inherit or compose? | Compose — hold a collaborator, don't subclass for reuse. |
| Hiding internals? | `__name` for truly private; no leading single underscore. |

## Example

```python
from typing import Protocol

class Notifier(Protocol):
    """Anything that can deliver a message."""
    def send(self, user: User, message: str) -> None: ...

class EmailNotifier:                      # no inheritance needed to satisfy the Protocol
    def __init__(self, smtp: SmtpClient) -> None:
        self.smtp = smtp
    def send(self, user: User, message: str) -> None:
        self.smtp.send_mail(user.email, message)

class NotificationService:                # composes notifiers; open to new channels
    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = notifiers
    def broadcast(self, user: User, message: str) -> None:
        for notifier in self.notifiers:
            notifier.send(user, message)
```

Adding a channel means writing one class that has `send` — no base class to extend, no
change to `NotificationService`.

## Common mistakes

- A class with only a constructor and one method — that is a function.
- Inheriting to reuse code (grab a `Mixin`, subclass a helper) instead of composing.
- Hand-writing `__init__`/`__repr__`/`__eq__` for a data holder — use `@dataclass`.
- Choosing `ABC` when nothing shared needs implementing — a `Protocol` is lighter.
- Leading single underscore for "private" — house style is `__name` or no prefix.

## Boundary

This skill owns class/type design. Special methods (`__eq__`, `__iter__`, `__hash__`),
descriptors, and custom sequences → **python-data-model**. General idioms and error
handling → **python-patterns**. See `reference.md` for dataclasses, Protocol vs ABC,
SOLID applied to Python, and `__slots__`.
