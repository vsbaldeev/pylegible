# Python Project Structure — reference

Depth behind `SKILL.md`. Read when you are actually moving files.

## Why topology is a readability concern

A reader meets your directory tree before they meet a single line of code. The tree either
tells them where things are or forces them to grep. Correct code in one flat directory of
twenty modules is code nobody can navigate — which is the failure this skill exists to
prevent.

## Stage 1 — a single module

Start here. One file, `src/orders.py`, is the right answer far longer than most people
believe. A 300-line module with one concern is more readable than a package of six 50-line
files, because the reader scrolls instead of navigating.

Promote to stage 2 when any of these is true:

- The module passes **400 lines** (code and blank lines; not imports, docstrings, or
  comment-only lines — the same counting rule as the ≤40-line function limit).
- It holds **two concerns that change for different reasons** — pricing rules and HTTP
  routing move on different schedules and for different people.
- It acquires a **second external system**. One database is fine; a database *and* a
  payment API means I/O now deserves its own home.

## Stage 2 — a flat package

Modules named by topic, one directory, no layers:

```
src/orders/
  __init__.py     pricing.py     storage.py     api.py
```

This is the correct terminal state for most libraries and small services. Do not layer it
just because you can.

Promote to stage 3 when either is true:

- The directory passes **7 entries** — modules and subpackages together, `__init__.py`
  excluded. Seven is where a directory stops being a list you read and starts being one you
  search.
- **I/O modules and rule modules import each other.** When `pricing.py` imports
  `storage.py` to load a discount table, the rules are no longer testable without a
  database, and the direction of dependency has already inverted.

## Stage 3 — a layered package

```
src/orders/
  __init__.py
  domain/
    order.py            entities and value objects
    pricing.py          the rules — pure functions over domain types
  application/
    ports.py            Protocols the use cases require
    place_order.py      one use case per module
  adapters/
    postgres_repo.py    implements OrderRepository
    stripe_gateway.py   implements PaymentGateway
    http_api.py         the web surface
  bootstrap.py          composition root
```

### The dependency rule

**Imports point inward only:** `adapters → application → domain`.

- `domain` imports the standard library and other `domain` modules. Nothing else. No SQL, no
  HTTP client, no `os.environ`, no framework import. This is what makes the rules testable
  in microseconds without a fixture.
- `application` imports `domain` and declares the interfaces it needs. It never imports a
  concrete adapter.
- `adapters` imports `application` and `domain` freely. It is the only place I/O appears.

Everything else follows from this one rule, which is why it is worth enforcing mechanically
(see below) rather than by review alone.

### Ports live with their consumer

The Protocol goes in `application`, not `adapters`. The consumer declares the interface it
needs; the implementer conforms to it. This is Dependency Inversion made physical, and it is
also Interface Segregation — a use case that only saves declares only `save`.

```python
# src/orders/application/ports.py
"""Interfaces the use cases require. Implemented in adapters, never imported from there."""

from decimal import Decimal
from typing import Protocol

from orders.domain.order import Order


class OrderRepository(Protocol):
    """Persistence required by the order use cases."""

    def save(self, order: Order) -> None:
        """Persist an order, overwriting any existing one with the same id.

        Args:
            order: The order to store.
        """

    def get(self, order_id: str) -> Order:
        """Load an order by id.

        Args:
            order_id: Identifier of the order to load.

        Returns:
            The stored order.

        Raises:
            OrderNotFound: If no order has that id.
        """


class PaymentGateway(Protocol):
    """Payment capture required by the order use cases."""

    def charge(self, customer_id: str, amount: Decimal) -> None:
        """Capture a payment from a customer.

        Args:
            customer_id: Who to charge.
            amount: How much to capture.

        Raises:
            PaymentDeclined: If the gateway refuses the charge.
        """
```

Both Protocols live here because `PlaceOrder` is what needs them. An adapter that implements
only `PaymentGateway` never sees `OrderRepository` — narrow interfaces, no unused
dependencies.

The use case depends on the Protocol and receives it by injection:

```python
# src/orders/application/place_order.py
"""The place-order use case."""

import logging

from orders.application.ports import OrderRepository, PaymentGateway
from orders.domain.order import Order
from orders.domain.pricing import price_order

logger = logging.getLogger(__name__)


class PlaceOrder:
    """Place an order and capture payment for it."""

    def __init__(self, orders: OrderRepository, payments: PaymentGateway) -> None:
        """Store the collaborators this use case needs.

        Args:
            orders: Where orders are persisted.
            payments: How payment is captured.
        """
        self.orders = orders
        self.payments = payments

    def execute(self, order: Order) -> None:
        """Price the order, capture payment, then persist it.

        Args:
            order: The order to place.

        Raises:
            PaymentDeclined: If the gateway refuses the charge.
        """
        total = price_order(order)
        logger.info("placing order %s for %s", order.order_id, total)
        self.payments.charge(order.customer_id, total)
        self.orders.save(order)
```

Note what is absent: no connection string, no HTTP session, no `import psycopg`. The use
case is testable with two small fakes.

### The composition root

One module knows both sides. Without it, an adapter eventually gets imported from inside the
domain "just this once" and the dependency rule dies with no visible event.

```python
# src/orders/bootstrap.py
"""Wire concrete adapters into use cases. The only module that knows both sides."""

import logging

from orders.adapters.postgres_repo import PostgresOrderRepository
from orders.adapters.stripe_gateway import StripePaymentGateway
from orders.application.place_order import PlaceOrder

logger = logging.getLogger(__name__)


def build_place_order(database_url: str, stripe_key: str) -> PlaceOrder:
    """Construct the PlaceOrder use case with production adapters.

    Args:
        database_url: PostgreSQL connection string.
        stripe_key: Stripe secret API key.

    Returns:
        A PlaceOrder use case ready to execute.
    """
    logger.info("building place_order use case")
    return PlaceOrder(
        orders=PostgresOrderRepository(database_url),
        payments=StripePaymentGateway(stripe_key),
    )
```

`bootstrap.py` sits at the package root, not inside a layer — it belongs to none of them.

## `__init__.py`

**Package root** — declares the public surface, ≤10 names:

```python
# src/orders/__init__.py
"""Order placement and pricing."""

from orders.application.place_order import PlaceOrder
from orders.domain.order import Order

__all__ = ["Order", "PlaceOrder"]
```

**Every interior `__init__.py`** — empty. No re-export chains.

Re-exporting at every level looks tidy and costs you three things: import cycles become easy
to create and hard to read; a name's real home is hidden, so grep stops working; and
importing anything drags in everything. Import from where the thing lives —
`from orders.domain.pricing import price_order`.

The ≤10 limit on `__all__` is a cohesion check, not a style rule. A package exporting
thirty names is either two packages or a namespace pretending to be a module.

## Naming modules and packages

Name a module for **what it holds**, as a noun. `pricing.py`, `order.py`, `postgres_repo.py`.

Banned outright: `utils`, `helpers`, `common`, `misc`, `shared`, `manager`. Each is a name
that means "assorted", so each becomes the place anything unclassifiable lands — and once
one exists, sprawl is a matter of time. When you feel the urge to write `utils.py`, the
contents will tell you the real name: three date functions are `dates.py`.

`base.py` and `core.py` are near-misses. They are acceptable only when the module genuinely
holds one base class or one core type, not as a grab-bag.

The directory naming test: **can you name it without "and" or a filler word?** A directory
you want to call `parsing_and_validation` is two directories.

## Mirroring tests

`python-testing` owns the `unit/` + `integration/` split. This skill adds one rule: the
source tree mirrors inside each.

```
src/orders/
  domain/pricing.py
  domain/order.py
  application/place_order.py
  adapters/postgres_repo.py

tests/
  conftest.py
  unit/orders/domain/test_pricing.py
  unit/orders/domain/test_order.py
  unit/orders/application/test_place_order.py
  integration/orders/adapters/test_postgres_repo.py
```

Two properties fall out for free:

1. Finding a file's test is a path transformation, not a search.
2. **A `domain/` directory under `tests/integration/` proves your domain does I/O.** The
   test tree audits the source tree.

## Enforcing the dependency rule

Review catches the rule maybe half the time. `import-linter` catches it every time:

```toml
# pyproject.toml
[tool.importlinter]
root_package = "orders"

[[tool.importlinter.contracts]]
name = "Imports point inward"
type = "layers"
layers = ["orders.adapters", "orders.application", "orders.domain"]
```

Run it in CI:

```bash
lint-imports
```

Higher layers may import lower ones; the reverse fails the build. Modules outside the listed
layers are unconstrained, which is exactly why `bootstrap.py` lives at the package root — it
must import adapters, and sitting outside the contract keeps it legal without weakening the
rule for anything else.

## Migrating stage 2 → stage 3

A worked example. Before — nine modules, past the 7-entry limit, with rules and I/O tangled:

```
src/orders/
  __init__.py  api.py  billing.py  discounts.py  emails.py
  models.py  pricing.py  storage.py  taxes.py  utils.py
```

1. **Sort every module into one of three buckets** by asking what it touches. Touches
   nothing external → `domain`. Orchestrates a user-visible operation → `application`.
   Speaks SQL, HTTP, SMTP, or the filesystem → `adapters`.

   `models.py`, `pricing.py`, `discounts.py`, `taxes.py` → domain.
   `billing.py` → application. `api.py`, `storage.py`, `emails.py` → adapters.

2. **Empty `utils.py` first.** Move each function to the module that actually uses it; if
   two modules use it and it touches nothing, it is a domain function. Delete the file. Do
   this before anything else — it is the module most likely to create a cycle.

3. **Create the directories and move files**, preserving history:

   ```bash
   mkdir -p src/orders/domain src/orders/application src/orders/adapters
   git mv src/orders/pricing.py src/orders/domain/pricing.py
   git mv src/orders/storage.py src/orders/adapters/postgres_repo.py
   ```

4. **Fix the direction, not the symptom.** Every remaining `domain → adapters` import is a
   missing port: declare a Protocol in `application/ports.py`, inject it, and wire the
   concrete class in `bootstrap.py`. A circular import "fixed" by moving the import inside a
   function is the rule failing quietly — fix the direction.

5. **Add the `import-linter` contract** and let CI hold the line from here.

6. **Mirror the move in `tests/`** with the same `git mv` operations, then run the suite.
   Tests that now need a database fixture and sit under `tests/unit/` are telling you a
   file landed in the wrong layer.

## Anti-patterns

| Anti-pattern | Instead |
|---|---|
| `utils.py`, `helpers.py`, `common.py`, `misc.py` | Name the module for what it holds; `dates.py`, `retries.py` |
| Twenty modules in one directory | Group by concern into subpackages; ≤7 entries each |
| Re-export chains in every `__init__.py` | Empty interior `__init__.py`; import from where the name lives |
| `domain/` importing `adapters/` | Declare a Protocol in `application`, inject it, wire in `bootstrap.py` |
| Circular import fixed by importing inside a function | Fix the direction — the cycle is the message |
| Layering a 200-line tool | Stay at stage 1 or 2 until a promotion trigger actually fires |
| Flat `tests/` beside a nested `src/` | Mirror the source tree inside `unit/` and `integration/` |
| A package exporting 30 names | It is two packages, or a namespace pretending to be a module |
| Splitting files that always change together | Files that change together live together |
