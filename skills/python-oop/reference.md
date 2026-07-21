# Python OOP — reference catalog

Depth for `python-oop`. Load when designing classes beyond the defaults.

## Dataclasses

Use `@dataclass` for objects that are mostly data. It generates `__init__`, `__repr__`,
and `__eq__` for you.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    """A registered user."""
    user_id: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
```

- `frozen=True` makes instances immutable (and hashable) — good for value objects and
  dict keys.
- Validate in `__post_init__`:

```python
@dataclass
class Account:
    balance_cents: int

    def __post_init__(self) -> None:
        if self.balance_cents < 0:
            raise ValueError(f"balance cannot be negative: {self.balance_cents}")
```

Reach past dataclasses to a full class only when behavior dominates the type.

## Protocol vs ABC

Both define an interface; they differ in how implementers opt in.

- **Protocol** (structural / "duck typing with types"): any class with the right methods
  satisfies it — no inheritance, no import coupling. Prefer this for interfaces your code
  *consumes*, especially third-party or test doubles.
- **ABC** (nominal): implementers must subclass it. Choose it when the base also provides
  shared, concrete behavior the subclasses reuse (a template method).

```python
from typing import Protocol

class Repository(Protocol):
    def get(self, entity_id: str) -> Entity | None: ...
    def save(self, entity: Entity) -> None: ...
```

```python
import abc

class Report(abc.ABC):
    def render(self) -> str:            # shared behavior
        return f"{self.title()}\n{self.body()}"

    @abc.abstractmethod
    def title(self) -> str: ...
    @abc.abstractmethod
    def body(self) -> str: ...
```

## Composition over inheritance

Inheritance couples a subclass to its parent's implementation. Composition — holding a
collaborator and delegating — keeps parts swappable and testable.

```python
# Compose: the service holds a store; swap the store in tests without subclassing
class OrderService:
    def __init__(self, store: Repository) -> None:
        self.store = store

    def place(self, order: Order) -> None:
        self.store.save(order)
```

Inherit only for a genuine "is-a" relationship where the subclass is substitutable for
the base (Liskov). If you inherit to reuse a method, compose instead.

## Law of Demeter ("don't talk to strangers")

A method should call only its own methods, its parameters, objects it creates, and its
direct attributes — not reach through them. `order.customer.address.city` couples the
caller to the whole chain; every intermediate type is now something that can break it.

```python
# Reaches through internals — knows about customer AND address structure
def label(order: Order) -> str:
    return f"{order.customer.address.city}"

# Ask the immediate collaborator; let it decide how to answer
def label(order: Order) -> str:
    return order.shipping_city()          # Order delegates to customer/address internally
```

Tell an object what you want done; don't fetch its parts and do the work yourself
("Tell, Don't Ask"). A long dotted chain is the smell that flags a missing method.

## SOLID, applied pragmatically

- **S**ingle responsibility — one reason to change per class. Split god classes.
- **O**pen/closed — add behavior by adding a class/implementation, not by editing a
  switch statement. Protocols make this natural.
- **L**iskov — a subclass must honor the base's contract; no surprising overrides.
- **I**nterface segregation — many small Protocols beat one fat one; consumers depend
  only on the methods they use.
- **D**ependency inversion — depend on a Protocol, receive the concrete implementation by
  constructor injection (as `OrderService` above).

Apply these to remove real pain, not as a ceremony on every class.

## Encapsulation

- Public attribute by default — Python has no true "private", and readable code does not
  hide gratuitously.
- `__name` (name-mangled) for state that truly must not be touched from outside.
- Expose computed values with `@property` rather than getter methods:

```python
class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius

    @property
    def area(self) -> float:
        """Area of the circle."""
        return math.pi * self.radius ** 2
```

## `__slots__`

For classes created in large numbers, declare `__slots__` to drop the per-instance
`__dict__` and save memory (it also blocks accidental new attributes):

```python
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
```

Skip it for ordinary classes — it adds friction (no dynamic attributes, care with
inheritance) for no benefit when instances are few.
