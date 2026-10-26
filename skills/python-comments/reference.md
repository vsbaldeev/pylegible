# Python Comments — reference

Depth behind `SKILL.md`. Each rule below names the source it comes from, so a reader can
disagree knowingly.

## Why comments are a liability

Code is executed and tested; a comment is neither. When the two drift apart, the reader
cannot tell which is right, and PEP 8 is blunt about the outcome: "Comments that contradict
the code are worse than no comments. Always make a priority of keeping the comments
up-to-date when the code changes." Every comment you add is a promise to maintain it.

*A Philosophy of Software Design* (Ousterhout) takes the other side of the same coin: comments
are not a failure — code alone cannot capture the designer's intent, assumptions, or the
reasons behind a choice. Both agree on the target: **comments carry what code cannot.**

## A taxonomy: keep, fix, delete

*Code Complete* (McConnell, ch. 32) sorts comments by what they do. Applied here:

| Kind | Example | Verdict |
|---|---|---|
| Repeats the code | `# add one to count` | Delete |
| Explains tricky code | `# shift because the field is packed in the high bits` | Keep — or simplify the code until it needs no explanation |
| Marker | `# TODO`, `# FIXME`, `# HACK` | Keep only with a ticket; see below |
| Summary | a few lines condensing a paragraph of code | Prefer extracting a named function |
| Intent | `# Retry here, not in the caller: the caller holds a lock.` | Keep — the best kind |
| Information the code cannot express | a link to the spec, a unit, an invariant, a business rule | Keep |

## Try these before writing a comment

Clean Code (Martin, ch. 4): "Don't comment bad code — rewrite it." In order of preference:

1. **Rename.** `wait` → `wait_before_retry_seconds`.
2. **Extract a function** whose name states the intent of the block you were about to explain.
3. **Extract a named constant** for a magic number or string.
4. **Express it in types** — an `Enum` or `NewType` instead of "0 means pending".
5. **Assert the invariant** — `assert`/an explicit check documents *and* enforces it, and
   cannot go stale.

Only the remainder — the *why* — becomes a comment.

```python
# Before: a comment compensating for structure
# check whether the user may edit this document
if user.role == "admin" or document.owner == user.identifier or user.identifier in document.editors:
    ...

# After: the name replaces the comment
if user_may_edit(user, document):
    ...
```

## What a good comment contains

- **Why this, not the obvious thing.** "Sort before grouping: `itertools.groupby` only merges
  *adjacent* equal keys."
- **A constraint from outside the code.** An API quirk, a rate limit, a compliance rule, with
  a link to the source of truth.
- **A warning about consequences.** "Changing this order breaks migration replay."
- **Units and ranges** when the type cannot say them: `# milliseconds`, `# inclusive`.
- **A reference** for a non-trivial algorithm, regex, or formula: the RFC, paper, or issue URL.
- **A workaround's exit condition.** "Remove when we require urllib3 >= 2.0."

```python
# The upstream API returns 200 with an empty body while a report is still generating,
# so an empty payload means "not ready", not "no results". See SUPPORT-482.
if not response.content:
    raise ReportNotReadyError(report_identifier)
```

## Placement and wording

- **Block comment** above the code, indented to match it, each line starting with `# `
  (PEP 8). Separate paragraphs with a lone `#`.
- **Inline (trailing) comment**: PEP 8 allows it, sparingly, at least two spaces after the
  statement. Use it for a unit or a one-phrase note, never for a sentence of explanation.
- **Complete sentences**, capitalized, in the present tense. Write for a maintainer who has
  not seen the ticket.
- **Line length** follows the project limit (120) rather than PEP 8's 72 for comments; wrap a
  long comment into a block rather than letting one line run on.
- **One language.** English unless the whole codebase has agreed otherwise.

## TODO, FIXME, HACK

A marker is a deferred decision. The Google Python Style Guide asks for a `TODO` to carry a
reference to the bug or ticket, so it can be found, assigned, and closed:

```python
# TODO(PAY-1204): Drop the legacy field once all clients send `currency`.
```

- Without a reference, a TODO is unowned and never closes. Create the ticket, or do not write
  the TODO.
- `FIXME` means "known wrong"; `TODO` means "known incomplete". Prefer fixing now over
  either — a marker is for what genuinely cannot be done in this change.
- Say *what* and *what unblocks it* in the same line.
- Sweep periodically: a marker older than its ticket is stale; delete or do it.

## Tool-directive comments

`# noqa`, `# type: ignore`, `# pragma: no cover`, `# fmt: off` change what tools check. They
are the highest-risk comments because they silence a safeguard.

- **Name the exact rule.** `# noqa: E501`, `# type: ignore[arg-type]` — a bare `# noqa`
  hides every future violation on that line (ruff's `PGH003`/`PGH004` flag the bare forms).
- **Add the reason** unless it is obvious: `# type: ignore[attr-defined]  # added by plugin at import`.
- **Scope narrowly.** One line, not a file-level ignore.
- **Revisit** when the dependency or tool upgrades; the suppression may no longer be needed.

## Docstring vs comment

| | Docstring | `#` comment |
|---|---|---|
| Audience | The *caller* | The *maintainer* |
| Answers | What does this do, take, return, raise? | Why is the body shaped this way? |
| Lives | Right under the `def`/`class` | Next to the surprising line |
| Tooling | `help()`, Sphinx, IDE hover | None |
| Must not | Describe implementation details a caller cannot rely on | Restate the signature |

A docstring is part of the interface and is kept in sync with the signature; PEP 257 covers
the form. A comment is an aside about the implementation.

## Delete on sight

- **Commented-out code.** Clean Code: it "sits there and rots" because no one dares delete it.
  Version control keeps history; delete it.
- **Change logs and attributions** (`# 2021-03-04 added by Sam`). `git blame` and the commit
  message hold this, accurately and for free.
- **Journal and closing-brace markers** (`# end of for loop`) — a sign the block is too long.
- **Banner comments** (`# ======== HELPERS ========`) — split the module instead.
- **Misleading or stale comments** — fix or remove; never leave them to be "probably right".
- **Opinion and venting** (`# this is ugly`, `# why does this work`) — say what is wrong and
  what would be right, or say nothing.
- **Anything sensitive.** Never put secrets, credentials, or personal data in a comment; it
  ships to every clone of the repository.

## Worked cleanup

```python
# Before
def process(orders):
    # loop over orders
    for order in orders:
        # skip cancelled
        if order.status == 3:
            continue
        # compute total
        total = 0
        for line in order.lines:
            total += line.price * line.quantity  # price times quantity
        # apply discount
        total = total * 0.9
        # TODO fix this
        order.total = total
```

```python
# After
CANCELLED_STATUS = 3
LOYALTY_DISCOUNT_RATE = 0.9


def price_open_orders(orders: list[Order]) -> None:
    """Set the discounted total on every order that is not cancelled.

    Args:
        orders: Orders to price. Cancelled orders are left untouched.
    """
    for order in orders:
        if order.status == CANCELLED_STATUS:
            continue
        order.total = line_total(order) * LOYALTY_DISCOUNT_RATE


def line_total(order: Order) -> float:
    """Return the undiscounted sum of an order's line prices."""
    return sum(line.price * line.quantity for line in order.lines)
```

Six comments became zero: names and constants carry what they said, the docstrings state the
contract, and the vague `TODO fix this` is gone — if a real defect existed, it belongs in a
ticket. The one fact worth a comment, *why* the discount is 0.9, would go above
`LOYALTY_DISCOUNT_RATE` with a pointer to the pricing policy.

## Anti-patterns

| Anti-pattern | Instead |
|---|---|
| `# increment i` above `i += 1` | Delete |
| Comment explaining a cryptic name | Rename so the comment is unnecessary |
| Commented-out code | Delete; use version control |
| `# TODO fix` with no ticket | Open a ticket and reference it, or do not write it |
| Bare `# noqa` / `# type: ignore` | Name the rule and, if unobvious, the reason |
| Comment describing past behavior | Delete; that is the commit message |
| Banner or section-divider comments | Split the module |
| A comment excusing a 60-line function | Extract named helpers |
| Author/date/changelog in a comment | Rely on `git blame` |
| Comment contradicting the code | Fix the comment in the same edit that changed the code |

## Sources

- PEP 8 — "Comments" (block vs inline, keep up to date, "contradict the code").
- PEP 257 — docstring conventions (the boundary with comments).
- Google Python Style Guide — "Comments and Docstrings", TODO format.
- Robert C. Martin, *Clean Code*, ch. 4 "Comments" — good comments vs bad, commented-out code.
- Steve McConnell, *Code Complete*, ch. 32 "Self-Documenting Code" — kinds of comments.
- John Ousterhout, *A Philosophy of Software Design*, ch. 12–13 — comments capture what code cannot.
