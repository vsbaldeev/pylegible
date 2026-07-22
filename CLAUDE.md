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
`python-oop`, `python-design-patterns`, and `python-idioms` skills.

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
  (`index` not `i`, `error` not `e`, `left`/`right` not `a`/`b`).
- Names must not start with a single underscore. Use no prefix for regular members,
  or a double underscore (`__name`) only for truly private class members.
- Module-level names never start with an underscore. Module-level constants use
  `UPPER_CASE` with no underscore prefix.

## Functions

- Keep each function body to 40 lines or fewer (count code and blank lines; do not
  count decorators, the signature, docstring lines, or comment-only lines).
- When a body exceeds the limit, extract cohesive, well-named helper functions.

## Docstrings and types

- Every top-level function and every class method gets a Google-style docstring
  (exclude nested functions, test functions, and lambdas).
- Annotate function signatures. Prefer built-in generics (`list[str]`, `dict[str, int]`).

## Errors and logging

- Catch specific exceptions, never bare `except`. Chain with `raise ... from error`.
- Use the `logging` module for diagnostics, never `print`. Never log secrets or PII.
