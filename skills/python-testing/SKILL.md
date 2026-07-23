---
name: python-testing
description: >
  Use when writing or reviewing pytest tests, practicing TDD, building fixtures,
  parametrizing cases, mocking or patching dependencies, testing exceptions or async
  code, deciding whether a test earns its place, choosing pytest plugins, reading a
  coverage report, or reproducing a failure that only happens in production — disk full,
  dropped connection, clock skew, an unlucky interleaving. For the production code's own style
  use python-idioms; for how the tests/ tree is laid out relative to the source tree
  use python-project-structure.
---

# Python Testing

## Overview

Tests are code the next person must read. A test should state one behavior in its name
and prove it in a few lines. Prefer many small, obvious tests over a few clever ones —
but collapse near-duplicate cases with parametrization rather than copy-paste. Depth in
`reference.md`.

## Why this test exists

Every test traces to one of two sources. There is no third.

| Source | Written | Bounded by |
|---|---|---|
| **Spec** — a stated requirement | before the code, outside-in | the e2e test going green. Then stop. |
| **Evidence** — an observed failure | after an incident, or after reading a dependency's documented error contract | a real traceback. No traceback, no test. |

A test written because a line was uncovered belongs to neither source. Delete it.

## When to use

- Writing tests for new or changed code — outside-in, the failing e2e test first.
- Reviewing a suite for readability, isolation, and tests that no longer earn their place.
- Reproducing a failure you cannot trigger on demand: disk full, network partition,
  clock skew, process killed mid-transaction, an unlucky thread interleaving.
- Setting up fixtures, mocks, or pytest configuration.

## Core rules

| Rule | Do this |
|---|---|
| Ordering | Start from the failing e2e test. Write unit tests only for the pieces you design to make it pass. |
| Existence | Keep a test if its failure tells you something no other test would. Otherwise delete it. |
| Shape | Few e2e tests, many supporting units. E2E says *something* broke; units say *what*. |
| Names | `test_<subject>_<condition>_<expected>` — a sentence, not `test_1`. |
| One behavior | One logical assertion target per test. |
| Duplication | Same test shape, different data → `@pytest.mark.parametrize`, not copy-paste. |
| Exceptions | `with pytest.raises(SpecificError):` — never try/except in a test. |
| Fault signatures | Inject the exception the real dependency raises, copied from a real traceback — never one you assumed. |
| Isolation | No shared mutable state; mock external I/O; use `tmp_path` for files. |
| Floats | Compare with `pytest.approx`. |
| Coverage | A diagnostic, never a target. An uncovered line is a question, not a ticket to write a test. |

## Example

```python
# Spec-driven: parametrize the invalid cases instead of writing one test each
@pytest.mark.parametrize(
    "price, percent",
    [(-1.0, 10), (100.0, -1), (100.0, 101)],
    ids=["negative-price", "negative-percent", "percent-over-100"],
)
def test_apply_discount_rejects_invalid_input(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)


# Evidence-driven: ENOSPC is what the traceback in incident 412 actually showed.
# The disk is never filled — only the signature the code observes is reproduced.
def test_save_reports_disk_full_and_leaves_index_empty(tmp_path):
    writer = Mock(spec=Writer)
    writer.write.side_effect = OSError(errno.ENOSPC, "No space left on device")
    storage = Storage(writer, index_path=tmp_path / "index.json")

    with pytest.raises(StorageFull):
        storage.save(document)

    assert json.loads((tmp_path / "index.json").read_text()) == {}
```

## Common mistakes

- A wall of near-identical tests that should be one parametrized case.
- Vague names (`test_discount`, `test_works`) that hide what broke.
- Asserting on exact float equality.
- Over-mocking — mocking the thing under test instead of its dependencies.
- Tests that depend on order or leftover state from a previous test.
- An e2e-heavy suite: every failure says "checkout is broken" and nothing says why.
- Writing a test to move a coverage number. If the branch has no evidence behind it and
  its failure would not matter, delete the branch instead.
- Injecting an invented exception. A retry test built on `ConnectionError` proves nothing
  when the driver raises `psycopg.OperationalError` — it passes, and ships the bug.

## Boundary

This skill owns test code and pytest — how a test is written. Where test files *live*, and
how `tests/` mirrors the source tree → **python-project-structure**. The style of the code
*under test* → **python-idioms**;
class design → **python-oop**; logging assertions aside, logging design → **python-logging**.
Writing concurrent code → **python-concurrency**; forcing a specific interleaving in a test
is this skill's, in `reference.md`. See `reference.md` for fixtures/scopes, mocking, async
tests, markers, configuration, which pytest plugins earn their place, and reproducing
unreproducible conditions.
