# pylegible conventions

These rules are always on for this project. The guiding value: **write Python that is
easy for a human to read, not merely code that is correct.** When clarity and
cleverness conflict, choose clarity.

## Readability first

- Optimize for the reader, not the writer. Prefer obvious code over compact code.
- Prefer explicit over implicit. No hidden side effects, no magic.
- A well-named function or variable removes the need for a comment.

## Design principles

Apply these when writing or reviewing any code. Depth and examples live in the
`python-oop`, `python-design-patterns`, and `python-idioms` skills. These are the field's
established names, not house inventions — SOLID from Robert C. Martin; DRY, YAGNI, and the
orthogonality ideas from *The Pragmatic Programmer*; KISS and least-surprise from the Unix
tradition. We adopt them; we don't claim them.

**SOLID**
- **Single Responsibility** — one reason to change per class or module.
- **Open/Closed** — extend by adding code, not editing what exists.
- **Liskov Substitution** — a subtype must be usable anywhere its base is, without surprises.
- **Interface Segregation** — many narrow interfaces over one fat one; no unused dependencies.
- **Dependency Inversion** — depend on abstractions; inject dependencies, don't hard-code them.

**General**
- **Composition over inheritance** — combine small objects rather than building deep hierarchies.
- **Law of Demeter** — talk only to immediate collaborators; `a.b.c.do()` is a smell.
- **DRY** — one authoritative home per piece of knowledge, but don't force an abstraction just to dedupe.
- **YAGNI** — build for the real requirement, not a hypothetical future one.
- **KISS** — the simplest thing that works is usually right; complexity is a liability.
- **Fail fast** — surface errors early and loudly; never silently propagate bad state.
- **Separation of concerns** — keep I/O, business logic, and presentation in separate layers.
- **Explicit over implicit** — behavior obvious from the code, not hidden in magic or globals.
- **Principle of least surprise** — code should behave the way a reader expects.

## Naming

- Never use single-letter variable names. Use names that convey meaning
  (`index` not `i`, `error` not `e`, `left`/`right` not `a`/`b`). Rare exception: `x`/`y`
  for mathematical vector or coordinate components, where the letter *is* the meaning.
  *Why:* a name is the cheapest documentation there is; a single letter makes the reader
  reconstruct what it holds (*Clean Code* — "use intention-revealing names").
- Names must not start with a single underscore. Use no prefix for regular members,
  or a double underscore (`__name`) only for truly private class members.
  *Why (a deliberate divergence from PEP 8):* PEP 8 uses a single leading underscore as a
  weak, unenforced "internal use" hint. We reject that ambiguity — reserve `__name`, whose
  mangling actually makes access bite, for when privacy must be real, and use no prefix
  otherwise. This is a minority position, stated plainly so a reader can disagree knowingly.
- Module-level names never start with an underscore. Module-level constants use
  `UPPER_CASE` with no underscore prefix.
  *Why:* a leading underscore is Python's "not part of the public API" marker (skipped by
  `import *`); we keep module surfaces intentional rather than lean on it. `UPPER_CASE`
  constants follow PEP 8.

## Functions

- Keep each function body to 40 lines or fewer (count code and blank lines; do not
  count decorators, the signature, docstring lines, or comment-only lines).
- When a body exceeds the limit, extract cohesive, well-named helper functions.
  *Why:* past roughly a screenful a function usually does more than one thing and stops
  fitting in the reader's head; the limit forces extraction into named steps (*Clean Code*,
  and *Refactoring*'s Extract Function — both argue for smaller still; 40 is a pragmatic ceiling).

## Docstrings and types

- Every top-level function and every class method gets a Google-style docstring
  (exclude nested functions, test functions, and lambdas).
  *Why:* a documented interface can be used without reading its body; Google style is
  compact and widely tooled (Sphinx/Napoleon) — see the Google Python Style Guide.
- Annotate function signatures. Prefer built-in generics (`list[str]`, `dict[str, int]`).
  *Why:* annotations are checkable documentation of the contract; built-in generics (PEP 585,
  3.9+) retired `typing.List` and read more directly.

## Errors and logging

- Catch specific exceptions, never bare `except`. Chain with `raise ... from error`.
  *Why:* a bare `except` also swallows `KeyboardInterrupt`/`SystemExit` and hides real bugs
  (PEP 8, "Programming Recommendations"); `from` preserves the causal chain (PEP 3134).
- Use the `logging` module for diagnostics, never `print`. Never log secrets or PII.
  *Why:* `logging` has levels, routing, and an off switch; `print` has none and pollutes
  stdout where it can corrupt piped output (Python Logging HOWTO). Logged secrets/PII leak.
