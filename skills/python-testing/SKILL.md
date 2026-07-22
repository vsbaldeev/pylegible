---
name: python-testing
description: >
  Use when writing or reviewing pytest tests, practicing TDD, building fixtures,
  parametrizing cases, mocking or patching dependencies, testing exceptions or async
  code, or checking coverage. For the production code's own style use python-idioms.
---

# Python Testing

## Overview

Tests are code the next person must read. A test should state one behavior in its name
and prove it in a few lines. Prefer many small, obvious tests over a few clever ones —
but collapse near-duplicate cases with parametrization rather than copy-paste. Depth in
`reference.md`.

## When to use

- Writing tests for new or changed code (follow TDD: red → green → refactor).
- Reviewing a test suite for readability, coverage, and isolation.
- Setting up fixtures, mocks, or pytest configuration.

## Core rules

| Rule | Do this |
|---|---|
| Names | `test_<subject>_<condition>_<expected>` — a sentence, not `test_1`. |
| One behavior | One logical assertion target per test. |
| Duplication | Same test shape, different data → `@pytest.mark.parametrize`, not copy-paste. |
| Exceptions | `with pytest.raises(SpecificError):` — never try/except in a test. |
| Isolation | No shared mutable state; mock external I/O; use `tmp_path` for files. |
| Floats | Compare with `pytest.approx`. |

## Example

```python
# Parametrize the invalid cases instead of writing one test each
@pytest.mark.parametrize(
    "price, percent",
    [(-1.0, 10), (100.0, -1), (100.0, 101)],
    ids=["negative-price", "negative-percent", "percent-over-100"],
)
def test_apply_discount_rejects_invalid_input(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)


def test_apply_discount_halves_price_at_fifty_percent():
    assert apply_discount(200.0, 50) == pytest.approx(100.0)
```

## Common mistakes

- A wall of near-identical tests that should be one parametrized case.
- Vague names (`test_discount`, `test_works`) that hide what broke.
- Asserting on exact float equality.
- Over-mocking — mocking the thing under test instead of its dependencies.
- Tests that depend on order or leftover state from a previous test.

## Boundary

This skill owns test code and pytest. The style of the code *under test* → **python-idioms**;
class design → **python-oop**; logging assertions aside, logging design → **python-logging**;
writing the concurrent code you are testing → **python-concurrency**. See `reference.md` for
fixtures/scopes, mocking, async tests, markers, and configuration.
