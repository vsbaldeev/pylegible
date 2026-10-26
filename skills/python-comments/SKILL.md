---
name: python-comments
description: >
  Use when writing, reviewing, or deleting `#` comments in Python — deciding whether a
  comment is needed, what it should say, how to word a TODO or a `noqa`/`type: ignore`
  suppression, what to do with commented-out code, or when a comment has gone stale. For
  logging use python-logging; for naming and statement-level idiom use python-idioms.
---

# Python Comments

## Overview

Code says *what* it does; a comment earns its place only by saying what the code cannot —
*why* it is this way, what constraint forced it, what will break if it changes. A comment
is also a second copy of the truth that nothing checks, so every one is a liability that
must be kept in sync. Write fewer comments, and make each one carry information the reader
cannot get from the code. Depth in `reference.md`.

The test: **delete the comment — does the reader lose something the code cannot tell
them?** If not, delete it.

## When to use

- About to write a comment: is it needed, and what should it say?
- Reviewing a diff with comments in it — redundant, stale, or misleading ones.
- Writing a `TODO`, `FIXME`, `# noqa`, `# type: ignore`, or `# pragma`.
- Finding commented-out code, a changelog or author note in a comment, or a banner comment.

## Core rules

| Rule | Do this |
|---|---|
| Why, not what | Explain intent, constraints, and trade-offs. Never restate what the next line plainly does. |
| Fix the code first | Before commenting, try a better name, an extracted function, a named constant, or a type. Comment only what is left. |
| Placement | Own line, directly above the code it explains. Trailing `#` comments only for short notes, two spaces after the code. |
| Wording | Complete sentence, `# ` with one space, present tense, ≤120 characters a line. Say it once, in English. |
| TODO | `# TODO(TICKET-123): what and why.` A TODO without a tracker reference or owner is a wish; do not add one. |
| Suppressions | `# noqa: E501` and `# type: ignore[arg-type]` name the exact code, plus a reason when it is not obvious. Never blanket. |
| Commented-out code | Delete it. Version control remembers. |
| No metadata | No author, date, or change history in comments — that is `git blame` and the commit message. |
| Keep in sync | When you change code, change its comment in the same edit. A comment that contradicts the code is worse than none. |
| Docstring vs comment | A docstring tells a *caller* the contract. A `#` comment tells a *maintainer* why the body is shaped this way. |

## Example

```python
# Noise: restates the code
# increment the retry counter
retry_count += 1

# Compensating for bad naming: rename instead
# seconds to wait
wait = 30

# Earns its place: a constraint the code cannot show
# The payment gateway rejects a second charge with the same key for 24 hours,
# so the key must be derived from the order, never generated per attempt.
idempotency_key = f"order-{order.identifier}"

# Better than a comment: the name carries it
WAIT_BEFORE_RETRY_SECONDS = 30
```

A good comment answers a question the reader would otherwise have to ask the author:
*why not the obvious approach? why this magic value? what breaks if I remove this?*

## Common mistakes

- Narrating the code line by line — a sign the code needs better names or smaller functions.
- Using a comment to excuse a function longer than 40 lines; extract named helpers instead.
- Commented-out code "in case we need it again".
- A `TODO` with no ticket and no date that outlives its author.
- `# type: ignore` or `# noqa` with no code and no reason.
- A comment describing what the code *used to* do, left behind after the edit.
- Section banners (`# ===== helpers =====`) in place of splitting the module.
- A comment that apologises ("hack", "ugly") but does not say what would be right.

## Boundary

This skill owns inline `#` comments — whether, what, and how. The docstring *requirement*
(Google style, every top-level function and method) is an always-on rule in `CLAUDE.md` /
`AGENTS.md`. Names that make a comment unnecessary, and statement-level idiom →
**python-idioms**. Log messages for a future operator → **python-logging**. Comments inside
tests and what a test should prove → **python-testing**. Whether to rewrite a misleading
comment while changing code you did not write, or leave it and note it →
**python-editing-existing-code**. See `reference.md` for the taxonomy of good and bad
comments, TODO and suppression conventions, a worked cleanup, and the sources behind each rule.
