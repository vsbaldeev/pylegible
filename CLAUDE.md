# python-dev conventions

These rules are always on for this project. The guiding value: **write Python that is
easy for a human to read, not merely code that is correct.** When clarity and
cleverness conflict, choose clarity.

## Readability first

- Optimize for the reader, not the writer. Prefer obvious code over compact code.
- Prefer explicit over implicit. No hidden side effects, no magic.
- A well-named function or variable removes the need for a comment.

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
