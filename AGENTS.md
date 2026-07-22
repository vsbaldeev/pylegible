# AGENTS.md — pylegible

Always-on guidance for coding agents (Codex, and any tool that reads `AGENTS.md`). This
mirrors `CLAUDE.md`; the two stay in sync deliberately. Guiding value: **write Python that
is easy for a human to read, not merely code that is correct.** When clarity and cleverness
conflict, choose clarity.

## Readability first

- Optimize for the reader, not the writer. Prefer obvious code over compact code.
- Prefer explicit over implicit. No hidden side effects, no magic.
- A well-named function or variable removes the need for a comment.

## Naming

- Never use single-letter variable names. Use names that convey meaning (`index` not `i`,
  `error` not `e`, `left`/`right` not `a`/`b`). Rare exception: `x`/`y` for mathematical
  vector or coordinate components.
- Names must not start with a single underscore. Use no prefix for regular members, or a
  double underscore (`__name`) only for truly private class members.
- Module-level names never start with an underscore. Module-level constants use `UPPER_CASE`.

## Functions

- Keep each function body to 40 lines or fewer (count code and blank lines; not decorators,
  the signature, docstring lines, or comment-only lines). Extract well-named helpers past that.

## Docstrings and types

- Every top-level function and every class method gets a Google-style docstring (exclude
  nested functions, test functions, and lambdas).
- Annotate signatures. Prefer built-in generics (`list[str]`, `dict[str, int]`).

## Errors and logging

- Catch specific exceptions, never bare `except`. Chain with `raise ... from error`.
- Use the `logging` module for diagnostics, never `print`. Never log secrets or PII.

## Design principles

Apply when writing or reviewing any code. Depth and examples live in the skills below.

**SOLID** — Single Responsibility (one reason to change); Open/Closed (extend by adding
code); Liskov Substitution (subtypes usable in place of their base); Interface Segregation
(narrow interfaces, no unused dependencies); Dependency Inversion (depend on abstractions,
inject them).

**General** — Composition over inheritance; Law of Demeter (`a.b.c.do()` is a smell); DRY
(one authoritative home, but don't force an abstraction); YAGNI (build for the real
requirement); KISS (simplest thing that works); Fail fast (surface errors early and loudly);
Separation of concerns (I/O, logic, presentation in separate layers); Explicit over implicit;
Principle of least surprise.

## Skills

This project ships eight topic skills, each a `SKILL.md` (lean, loaded on demand) plus a
`reference.md` (depth). Scopes are non-overlapping — each `SKILL.md` ends with a **Boundary**
line pointing at the right skill for adjacent topics.

| Skill | Use when… |
|---|---|
| `python-idioms` | writing everyday Python — idioms, typing, errors, comprehensions, packaging |
| `python-design-patterns` | naming or choosing a design pattern — Strategy, Adapter, Observer, Builder, which GoF patterns Python dissolves |
| `python-testing` | writing pytest tests or doing TDD — fixtures, parametrization, mocking, coverage |
| `python-logging` | adding logging, choosing a level, stdout vs stderr, replacing `print` |
| `python-oop` | designing classes — dataclasses, Protocol/ABC, composition over inheritance, SOLID |
| `python-data-model` | dunder methods, operators, custom sequences/iterators, `with`, pattern matching |
| `python-metaprogramming` | decorators, descriptors, metaclasses, `__init_subclass__`, dynamic attributes |
| `python-concurrency` | choosing threads/asyncio/processes, executors, races, the GIL, free-threading |

**Making Codex pick them up.** The skills live under `skills/` (Claude Code plugin layout).
Codex discovers skills in `~/.codex/skills/` (global) or `.agents/skills/` (per-repo). To use
them in Codex, do one of:

- **Per-repo:** expose them at `.agents/skills/` — e.g. `ln -s ../skills .agents/skills` from
  the repo root (one source, both tools). Codex then implicitly invokes them by description.
- **Global:** copy or symlink each skill directory into `~/.codex/skills/`.

The frontmatter (`name` + `description`) already matches the Agent Skills standard Codex uses,
so no content changes are needed. Explicit invocation in Codex is `$python-logging` (etc.).

## Not portable to Codex

The skill-usage logger — Claude Code hooks in `~/.claude/settings.json` (`UserPromptSubmit`
and `PreToolUse` on the `Skill` tool) — is Anthropic-specific and does not run under Codex.
The `.claude-plugin/` manifest and `marketplace.json` are Claude-Code-only too; Codex reads
the skills directory directly and needs neither.
