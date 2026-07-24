---
name: python-editing-existing-code
description: >
  Use when changing Python you did not just write — fixing a bug in an unfamiliar module,
  adding a feature to existing code, refactoring legacy code, or touching a function that
  has no tests or does not follow the house conventions. Governs how much to change and how
  to change it safely. For how to write the pinning test use python-testing; for whether a
  file should be split or a module moved use python-project-structure; for statement-level
  rewrites of the code under edit use python-idioms.
---

# Editing Existing Code

## Overview

Writing new code and changing old code are different disciplines. New code answers to a
spec; existing code answers to the readers of your diff and to behavior that already works
in production. Two failures dominate: doing *too much* — a bugfix that renames, reflows, and
resplits half a file — and doing it *too recklessly* — changing untested behavior with no
proof you preserved it. This skill is the leash for the first and the seatbelt for the
second. Depth in `reference.md`.

## Two ways to break a working system

| Failure | Looks like | Guardrail |
|---|---|---|
| **Too much** | A one-line fix, a fifty-line diff — renames, reflows, file splits nobody asked for. | Change only the task's footprint. Note other violations; don't fix them here. |
| **Too reckless** | Editing behavior no test covers, hoping you kept it. | Pin the current behavior in a test first — even bug-for-bug — then change. |

## When to use

- Fixing a bug in code you did not write.
- Adding a feature to an existing module.
- Refactoring or cleaning up legacy code.
- Touching a function or module that has no tests.
- Editing code that violates the house conventions, and deciding how far to go.

## Core rules

| Rule | Do this |
|---|---|
| Footprint | Make the change the task needs, then stop. A bugfix is not a refactor. |
| Boy-scout, leashed | Tidy the lines you already touch. Do not rename, resplit, or restructure lines you don't. |
| Spotted violations | See a 900-line `utils.py`? Note it — a TODO, an issue — and move on. Don't drive-by fix it. |
| Pin before you touch | Before changing untested behavior, write a characterization test capturing what it does today. |
| Characterization ≠ spec | A characterization test pins current behavior, bugs and all. A spec test asserts required behavior. Know which you're writing. |
| No seam, no blind edit | Can't get the code under test? Introduce the smallest seam (sprout/wrap), or stop and surface it. |
| Bug-for-bug first | Reproduce the current output exactly, then flip the one assertion the fix moves. The rest staying green is your proof. |
| Separate the cleanup | Unrelated cleanup is its own named change, never a rider on a fix. |

## Example

A rounding bug lives in `invoice_total`, a function no test covers. Pin it, then fix it —
footprint of one:

```python
# The bug: invoice_total truncates instead of rounding. No test covers it.
# Step 1 — characterize. This PASSES today and documents the wrong answer.
def test_invoice_total_matches_current_behavior():
    line_items = [Item("widget", 3, 0.333), Item("gadget", 1, 1.005)]
    assert invoice_total(line_items) == 1.99  # 0.999 truncated to 0.99, plus 1.00

# Step 2 — fix the one line in invoice_total, then flip the one assertion the fix moves:
#     assert invoice_total(line_items) == pytest.approx(2.00)
# The rest of the suite staying green is your proof you changed only this behavior.
```

The surrounding module still has a filler name and a 600-line body. That is not this diff's
job — record it and ship the fix.

## Common mistakes

- The drive-by refactor: renaming variables and reflowing a function while fixing an
  unrelated bug, so the reviewer cannot separate the fix from the noise.
- Changing untested behavior and calling the suite passing — it never covered the line you
  touched.
- Writing a spec test where a characterization test was needed: asserting what the code
  *should* do, so it fails on the very behavior you were trying to preserve.
- "While I'm here" splitting a file — a topology change smuggled into a bugfix. It belongs
  to python-project-structure and to its own change.
- Deleting a branch you didn't understand because it looked dead. Characterize it first;
  behavior with no test is load-bearing until proven otherwise.
- Reformatting the whole file with a new tool, burying one real change in a thousand-line diff.

## Boundary

This skill owns *how to change code that already exists* — restraint in scope, safety before
the edit. How to write the pinning test itself — fixtures, mocks, `pytest.raises`, `approx`
→ **python-testing**. Whether a file should be split or a module moved, and where tests live
→ **python-project-structure** (but never as a drive-by). Statement-level style of the code
you rewrite → **python-idioms**; redesigning a class you're extending → **python-oop**. See
`reference.md` for the seam catalogue, characterization- and approval-test recipes,
sprout/wrap for untestable code, strangler-fig for larger replacements, and how to record a
violation you're leaving alone. The project `CLAUDE.md` lists the full design-principle set.
