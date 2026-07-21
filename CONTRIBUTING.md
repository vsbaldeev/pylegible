# Contributing

Thanks for improving **python-dev**. This plugin encodes an opinionated Python house style —
contributions should match both its conventions and its structure.

## Repo layout

- Each skill is `skills/<name>/SKILL.md` (lean, always-loaded house rules) plus a
  `reference.md` (on-demand depth). The folder name must equal the frontmatter `name`.
- Every `SKILL.md` ends with a **Boundary** section pointing at the right skill for adjacent
  topics. Keep these cross-references reciprocal — if skill A points to B, B should point back.
- `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) hold the always-on rules and stay in sync.

## Conventions (every code example must obey these)

- No single-letter names (rare exception: `x`/`y` for vector/coordinate components); no leading
  single underscore (`__name` only for truly private members).
- Function bodies ≤ 40 lines; Google-style docstrings on top-level functions and methods;
  annotate signatures with built-in generics (`list[str]`).
- Catch specific exceptions and chain with `raise ... from error`; use `logging`, never `print`.

Full rules live in `CLAUDE.md` / `AGENTS.md`.

## Adding or changing a skill

1. Follow the existing `SKILL.md` section shape: Overview, When to use, Core rules (table),
   Example, Common mistakes, Boundary.
2. Put depth in `reference.md`; keep `SKILL.md` short enough to load on every trigger.
3. Add reciprocal Boundary cross-references in any sibling skills you touch.
4. Update the skill count and tables in `README.md`, `AGENTS.md`, and the keyword list in
   `.claude-plugin/plugin.json`.

## Before opening a PR

Validate locally:

```bash
claude plugin validate .
```

CI (`.github/workflows/validate.yml`) also checks that the JSON manifests parse and that each
`SKILL.md`'s folder name matches its `name` and carries a `description`.
