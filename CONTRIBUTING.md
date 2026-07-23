# Contributing

Thanks for improving **pylegible**. This plugin encodes an opinionated Python house style —
contributions should match both its conventions and its structure.

## Repo layout

- Each skill is `skills/<name>/SKILL.md` (lean house rules, loaded whenever the skill triggers)
  plus a `reference.md` (depth, loaded only when needed). The folder name must equal the
  frontmatter `name`.
- Every `SKILL.md` ends with a **Boundary** section pointing at the right skill for adjacent
  topics. Keep these cross-references reciprocal — if skill A points to B, B should point back.
- The frontmatter `description` is the only part loaded on every turn, so cross-references
  there are rationed: name a sibling only where the two scopes genuinely touch, not every
  skill in the plugin. Boundary sections are where the full map lives.
- `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) hold the always-on rules and stay in sync.

## Conventions (every code example must obey these)

- No single-letter names (the one exception the examples take, as `AGENTS.md` records: `x`/`y`
  for vector/coordinate components); no leading single underscore (`__name` only for truly
  private members).
- Function bodies ≤ 40 lines; Google-style docstrings on top-level functions and methods;
  annotate signatures with built-in generics (`list[str]`).
- Catch specific exceptions and chain with `raise ... from error`; use `logging`, never `print`.

Full rules live in `CLAUDE.md` / `AGENTS.md`.

## Evidence for structural claims

A numeric threshold or a "never do X" is a claim about real code, so check it against real
code before shipping it. `python-project-structure` cites Sentry's documented
`src/… → tests/…` mirroring rule, and pydantic (76 test files in one directory) and scrapy
(146) for where a flat `tests/` breaks down. Prefer a rule with a named repo behind it over
one that merely sounds like good architecture — and say plainly when the evidence is mixed
rather than picking the convenient half.

## Adding or changing a skill

1. Follow the existing `SKILL.md` section shape: Overview, When to use, Core rules (table),
   Example, Common mistakes, Boundary.
2. Put depth in `reference.md`; keep `SKILL.md` short enough to load on every trigger.
3. Add reciprocal Boundary cross-references in any sibling skills you touch, and a
   `description` cross-reference only in the skills whose scope genuinely abuts the new one.
4. Update the skill tables in `README.md` and `AGENTS.md`, and the keyword list in
   `.claude-plugin/plugin.json`. The skill **count** is written out in four places — three in
   `README.md` ("Nine topic skills", the Layout tree, the install section) and one in
   `AGENTS.md` — so grep for the current number rather than trusting this list.
5. Bump `version` in **both** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
   — CI fails if the two disagree. A new skill is a minor bump (0.3.0, 0.4.0); revising the
   guidance inside an existing skill is a patch bump (0.4.1).
6. If you move knowledge between skills, delete it from the old home in the same change. One
   authoritative home per rule — `python-idioms` lost its packaging snippet when
   `python-project-structure` took over layout.

## Before opening a PR

`claude plugin validate .` checks the marketplace manifest only — it will pass on a skill
whose folder name and frontmatter disagree. Reproduce all three CI jobs
(`.github/workflows/validate.yml`) locally instead:

```bash
# 1. manifests parse
for manifest in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  jq -e . "$manifest" > /dev/null || echo "FAIL $manifest"
done

# 2. plugin and marketplace agree on name and version
[ "$(jq -r .name .claude-plugin/plugin.json)" = "$(jq -r '.plugins[0].name' .claude-plugin/marketplace.json)" ] &&
[ "$(jq -r .version .claude-plugin/plugin.json)" = "$(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)" ] &&
  echo "ok manifests agree" || echo "FAIL manifests disagree"

# 3. every SKILL.md's folder matches its name and carries a description
for skill in skills/*/SKILL.md; do
  folder=$(basename "$(dirname "$skill")")
  name=$(awk '/^name:/{print $2; exit}' "$skill")
  [ "$folder" = "$name" ] || echo "FAIL $skill: name '$name' != folder '$folder'"
  grep -q '^description:' "$skill" || echo "FAIL $skill: missing description"
done

claude plugin validate .
```
