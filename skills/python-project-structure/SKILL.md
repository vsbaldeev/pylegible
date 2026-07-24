---
name: python-project-structure
description: >
  Use when deciding where Python code should live — splitting a module that has grown too
  large, creating or naming a subpackage, organizing a package into layers, deciding what
  belongs in `__init__.py`, fixing a directory that has accumulated too many modules,
  untangling circular imports between siblings, or laying out `tests/` relative to the
  source tree. For class design use python-oop; for named design patterns and how objects
  collaborate use python-design-patterns; for statement-level idiom, typing, and import
  ordering use python-idioms; for test style, fixtures, and pytest configuration use
  python-testing.
---

# Python Project Structure

## Overview

Structure is the first thing a reader navigates and the last thing anyone refactors. A
package that grows by appending one more module to one flat directory stays correct and
becomes unreadable. This skill owns *topology* — which directories exist, what they are
called, which way imports flow, and where a file's test lives. Depth in `reference.md`.

The membership test: **could you follow the rule with every file's contents blanked out?**
If yes, it belongs here. If it depends on what the code says, it belongs to a sibling skill.

## When to use

- A module has outgrown a screenful and you are deciding how to split it.
- A directory holds more modules than you can keep in your head.
- Naming a new subpackage, or deciding which existing one a new file joins.
- Deciding what a package exports — what belongs in `__init__.py`.
- Untangling a circular import, or deciding whether module A may import module B.
- Laying out `tests/` so a reader can find the test for a given source file.

## Core rules

| Rule | Do this |
|---|---|
| Stages | Grow single module → flat package → layered package. Never start at stage 3. |
| Module length | ≤400 lines — code and blank lines; not imports, docstrings, or comment-only lines. |
| Directory width | ≤7 entries — modules and subpackages together, `__init__.py` excluded. |
| Nesting | ≤3 levels below the package root. |
| Public surface | Root `__init__.py` declares `__all__`, ≤10 names. Interior `__init__.py` stays empty. |
| Dependency rule | Imports point inward: `adapters → application → domain`. Never the reverse. |
| Composition root | One `bootstrap.py` wires concrete adapters into use cases. Nowhere else does. |
| Naming | Name a module for what it holds. Never `utils`, `helpers`, `common`, `misc`, `shared`, `manager`. |
| Tests | Mirror the source tree when a test covers one module (`unit/`, and adapter tests). Name for behavior when it spans modules (`e2e/`). Flat `tests/` is fine until stage 3. |

Borderline against a threshold? The naming test decides: **can you name the directory
without using "and" or a filler word?** If not, it holds more than one concern.

## The three stages

**Stage 1 — one module.** `src/orders.py`. Promote when it passes 400 lines, holds two
unrelated concerns, or starts talking to a second external system.

**Stage 2 — flat package, modules named by topic.** Promote when the directory passes 7
entries, or when I/O modules and rule modules start importing each other.

```
src/orders/
  __init__.py    pricing.py    storage.py    api.py
```

**Stage 3 — layered package.** Terminal.

```
src/orders/
  __init__.py       the public surface: __all__, ≤10 names
  domain/           pure logic — stdlib only. No SQL, HTTP, env, or framework imports.
  application/      use cases; imports domain; declares the Protocols (ports) it needs
  adapters/         postgres_repo.py, stripe_gateway.py — your code calling out
  entrypoints/      http_api.py, cli.py — the world calling in; the only place a framework appears
  bootstrap.py      composition root: wires concrete adapters into use cases
```

Split `entrypoints/` from `adapters/` once you have both. Every module in `adapters/`
implements a Protocol from `application/ports.py`; nothing in `entrypoints/` does. One
directory of each is fine while a service has only a CLI and one datastore.

## Example

Layers make the dependency rule physical — the consumer declares the interface, the adapter
implements it, and only `bootstrap.py` knows both sides:

```python
# src/orders/application/ports.py — the use case declares what it needs
class OrderRepository(Protocol):
    """Persistence required by the order use cases."""

    def save(self, order: Order) -> None:
        """Persist an order."""

# src/orders/adapters/postgres_repo.py — the adapter implements it, and imports inward
class PostgresOrderRepository:
    """Store orders in PostgreSQL."""

    def save(self, order: Order) -> None:
        """Persist an order. See OrderRepository."""
```

A test mirrors the source tree when it covers exactly one module, and is named for the
behavior when it spans several:

```
tests/
  unit/                                  mirrors src/ — one module each, collaborators faked
    orders/domain/test_pricing.py
    orders/application/test_place_order.py
  integration/                           one adapter against its real system
    orders/adapters/test_postgres_repo.py
  e2e/                                   spans modules — named for behavior, mirrors nothing
    test_place_order.py
    test_refund_order.py
```

`tests/unit/` should contain nothing but `domain/` and `application/`. A domain module whose
test needs a real system is a domain module doing I/O.

## Common mistakes

- Starting at stage 3 for a 200-line tool — four near-empty directories are their own
  readability problem. Earn each stage.
- A `utils.py` that becomes wherever anything unclassifiable lands.
- Re-exporting through every interior `__init__.py`: it invites import cycles and hides
  where a name actually lives.
- `domain/` importing from `adapters/` "just this once" — without a single composition root
  the dependency rule dies silently.
- An entrypoint reaching past the use case to call an adapter directly. Forbid it
  mechanically; it is the shortcut everyone takes under deadline.
- Splitting by technical layer parts that always change together.
- Forcing a mirror onto a test that spans modules. If there is no single source file, there
  is nothing to mirror — name it for the behavior and put it in `e2e/`.
- Keeping `tests/` flat past stage 3, until hierarchy has to be smuggled into filenames
  (`test_downloader_handler_twisted_http11.py`).

## Boundary

This skill owns where code lives — directories, module boundaries, import direction, and
the shape of `tests/`. What goes *inside* a file belongs elsewhere: class, dataclass, and
Protocol design → **python-oop**; named patterns and object collaboration →
**python-design-patterns**; statement-level idiom, typing, error handling, and import
*ordering* → **python-idioms**; test style, fixtures, and pytest configuration →
**python-testing**. *When* a split is worth doing while editing existing code, versus
noting it and leaving it — restraint against the drive-by refactor → **python-editing-existing-code**.
See `reference.md` for the stages in full, ports and composition roots,
`__init__.py` policy, a worked stage-2 → stage-3 migration, and an `import-linter` config
that makes the dependency rule CI-checkable. The project `CLAUDE.md` lists the full
design-principle set.
