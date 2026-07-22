---
name: python-design-patterns
description: >
  Use when choosing or naming a design pattern, or when several objects need to collaborate
  and the shape of that collaboration is the question — "what pattern fits here?", Strategy,
  Factory, Builder, Singleton, Adapter, Decorator, Facade, Proxy, Observer, State, Command,
  Visitor, Template Method, and the rest of the Gang of Four — plus which of them Python
  dissolves into a plain function, a module, or a generator. Also use when reviewing code
  that has imported a Java or C++ pattern Python does not need. For the design of a single
  class use python-oop; for expression-level idioms and error handling use python-idioms;
  for `@decorator` syntax as a language feature use python-metaprogramming.
---

# Python Design Patterns

## Overview

Most of the Gang of Four catalog is a workaround for languages that lack first-class
functions, duck typing, and modules. Python has all three, so a majority of the 23 patterns
collapse into something smaller — usually a function, a `dict`, or a module-level object.
**The most valuable thing this skill does is stop you from building a class hierarchy where
a function argument would do.**

A pattern is a name for a shape you already needed, never a goal in itself. If you cannot
say which concrete problem the pattern solves in *this* code, you do not need it (YAGNI).

## When to use

- Several objects need to collaborate and you are deciding how they connect.
- You are about to add an interface, a factory, or a hierarchy "for flexibility".
- Reviewing code that reads like translated Java — `AbstractHandlerFactory`, `getInstance()`.
- Someone asks "what design pattern should I use here?"

## The 23 patterns in Python

**Creational**

| Pattern | In Python |
|---|---|
| Factory Method | *Collapses* — a `classmethod` alternate constructor (`Config.from_json`) or a plain function. |
| Abstract Factory | *Collapses* — a `dict` of constructors, or a module of factory functions. Keep only when a family of related objects must stay consistent. |
| Builder | **Earns its keep** — stepwise or conditional construction. But try keyword arguments and `@dataclass` first. |
| Prototype | *Collapses* — `copy.deepcopy` or `dataclasses.replace`. |
| Singleton | *Reject* — a module is already a singleton. Use a module-level instance, or `@functools.cache` on a factory function. |

**Structural**

| Pattern | In Python |
|---|---|
| Adapter | **Earns its keep** — wrap a foreign interface so it satisfies your `Protocol`. |
| Facade | **Earns its keep** — one module-level function or small class hiding a multi-step subsystem. |
| Composite | **Earns its keep** (modestly) — leaves and containers behind one `Protocol`, for real trees. |
| Bridge | *Collapses* — dependency injection: hold the implementation as a collaborator. |
| Decorator | *Collapses* — `@decorator` for behavior on callables; `__getattr__` forwarding to wrap an object. Not the same thing as GoF Decorator, but it covers the same need. |
| Proxy | *Collapses* — `__getattr__` forwarding, `functools.cached_property`, or a lazy import. |
| Flyweight | *Collapses* — `@functools.cache`, interning, `__slots__`. |

**Behavioral**

| Pattern | In Python |
|---|---|
| Strategy | *Collapses* — pass a function. The single most over-classed pattern in Python. |
| Command | *Collapses* — a callable: a function, a closure, or `functools.partial`. |
| Iterator | *Collapses* — generators and `__iter__`; it is built into the language. |
| Observer | **Earns its keep** — a list of callbacks, or a small pub/sub registry. |
| State | **Earns its keep** — when transitions are genuinely complex. Otherwise an `Enum` plus a dispatch `dict`. |
| Chain of Responsibility | **Earns its keep** — a list of handlers, tried in order until one answers. |
| Template Method | **Earns its keep** (sparingly) — an ABC holding the skeleton with abstract hooks. Prefer composition when the steps are independent. |
| Visitor | *Collapses* — `functools.singledispatch`, or `match` on the node type. |
| Mediator | *Collapses* usually — a coordinating function, or an event bus if it is real. |
| Memento | *Collapses* — snapshot with `dataclasses.replace` or `copy`. |
| Interpreter | *Reject* for most work — use a parser library or the `ast` module. |

## Example

Strategy is the clearest case. The GoF shape, ported literally:

```python
# Over-classed: three types and an inheritance tree to hold one expression each
class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, total: Decimal) -> Decimal: ...

class NoDiscount(DiscountStrategy):
    def apply(self, total: Decimal) -> Decimal:
        return total

class PercentOff(DiscountStrategy):
    def __init__(self, percent: Decimal) -> None:
        self.percent = percent

    def apply(self, total: Decimal) -> Decimal:
        return total * (1 - self.percent / 100)
```

The Python shape — the strategy is just the thing you can call:

```python
Discount = Callable[[Decimal], Decimal]

def percent_off(percent: Decimal) -> Discount:
    """Build a discount that takes a fixed percentage off the total."""
    def apply(total: Decimal) -> Decimal:
        return total * (1 - percent / 100)
    return apply

def checkout(total: Decimal, discount: Discount = lambda total: total) -> Decimal:
    """Charge the total after applying the given discount."""
    return discount(total)
```

Keep a class only when the strategy carries real state or needs more than one method.

## Common mistakes

- A `Protocol` or ABC with exactly one implementation and no second one in sight — that is
  speculative Open/Closed, and YAGNI outranks it.
- A `Singleton` implemented through `__new__`. Use a module-level instance.
- Classes named `Manager`, `Helper`, `Handler`, or `Factory` that hold no state — those are
  functions wearing a class.
- Confusing GoF Decorator (wrapping an object) with Python's `@decorator` syntax.
- Building a Visitor to walk a tree when `functools.singledispatch` or `match` would do it.
- Naming a pattern in code that does not implement it, which misleads the next reader.

## Boundary

This skill owns *collaboration between objects* and the named patterns that describe it.
The design of one class — dataclass or not, `Protocol` vs ABC, SOLID, encapsulation →
**python-oop**. Expression-level idioms, comprehensions, and error handling →
**python-idioms**. Writing decorators, descriptors, and metaclasses as language machinery →
**python-metaprogramming**. Dunder methods and custom iteration → **python-data-model**.
Concurrency structure (producer/consumer, worker pools) → **python-concurrency**.
See `reference.md` for full examples of the eight patterns that earn their keep, plus the
Java-isms to reject on sight. The project `CLAUDE.md` lists the full principle set.
