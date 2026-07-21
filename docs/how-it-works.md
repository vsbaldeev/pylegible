# How hooks, skills, and CLAUDE.md actually work

This plugin is also a teaching artifact. If you only remember one thing, remember the
table below: the three mechanisms differ in **when they load** and **who decides**.

## What loads when

| Mechanism | When it enters the model's context | Ongoing cost | Who triggers it |
|---|---|---|---|
| **CLAUDE.md** | Always — injected into the system prompt at session start | Pays context on **every** turn | Nobody; it is unconditional |
| **Skill** | On demand — only its one-line `description` is always visible; the full `SKILL.md` body loads when the model chooses to open it | Cheap until used; the body costs context only after it triggers | **The model**, by reading descriptions and deciding the task matches |
| **Hook** | Never enters the model's context. It runs a shell command when a lifecycle event fires | A subprocess, not tokens | **A deterministic event match** — no model judgment |

The practical rule:

- Something you **always** want true → `CLAUDE.md` (like this project's readability rules).
- Deep reference knowledge you want **pulled in when relevant** → a skill.
- An automatic side effect **on an event** → a hook.

## How a skill auto-triggers

A skill does not run because it exists. Each session, the model sees a listing of every
available skill — but only the `description` field, not the body. When your task matches
a description, the model calls the `Skill` tool, and only then does the `SKILL.md` body
load.

That makes the `description` the single most important line in a skill. It must state
**when to use** the skill (concrete triggers, symptoms, keywords) — not what the skill
does. A description that summarizes the workflow tempts the model to act on the summary
instead of reading the real instructions.

```yaml
# Weak — vague, no triggers
description: Helpers for Python logging

# Strong — concrete triggers the model can match against a task
description: >
  Use when adding logging to Python code, choosing a log level, deciding what to
  send to stdout vs stderr, or replacing print statements with the logging module.
```

Progressive disclosure goes one level deeper: this plugin's skills keep `SKILL.md`
lean and push depth into a sibling `reference.md`, which the model opens only when it
needs the details. Three tiers — description (always), SKILL.md (on trigger),
reference.md (on demand) — each paid for only when reached.

## Hooks, dissected — your own skill-usage logger

Earlier we built a logger that records every skill invocation. It is two hooks wired
into `~/.claude/settings.json`, both pointing at scripts in `~/.claude/skill-usage/`:

```jsonc
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [{ "type": "command", "command": "bash ~/.claude/skill-usage/log-prompt.sh" }] }
  ],
  "PreToolUse": [
    { "matcher": "Skill",
      "hooks": [{ "type": "command", "command": "bash ~/.claude/skill-usage/log-skill.sh" }] }
  ]
}
```

- **`UserPromptSubmit`** fires when you send a message. `log-prompt.sh` receives the
  prompt as JSON on stdin and records any `/slash-commands` you typed, so a later skill
  call can be labeled manual rather than automatic.
- **`PreToolUse` with `matcher: "Skill"`** fires right before the `Skill` tool runs.
  `log-skill.sh` reads `tool_input.skill` from stdin and appends a line to
  `usage.log`, tagged `auto` or `/cmd`.

Key properties of hooks visible here:

1. They get structured JSON on **stdin** (`session_id`, `tool_name`, `tool_input`, …)
   and communicate back through **exit code** and optional JSON on stdout.
2. A `matcher` scopes a `PreToolUse`/`PostToolUse` hook to specific tools.
3. The model never sees any of this. It is deterministic plumbing — which is exactly
   why "log every skill call" is a hook and not an instruction in CLAUDE.md.

Read the report any time with:

```bash
bash ~/.claude/skill-usage/skill-usage-report.sh python
```

## CLAUDE.md precedence and cost

Multiple CLAUDE.md files can apply at once, and they are all injected together:

1. **Managed / policy** (enterprise-controlled) — authoritative; cannot be overridden.
2. **Project** — `./CLAUDE.md` at the repo root (this file's sibling).
3. **User** — `~/.claude/CLAUDE.md` (your personal global rules).

They stack rather than replace, so the model sees every applicable file at once. When
two give conflicting guidance, the more specific / project-level instruction is the one
to follow (policy always wins outright). Keep each file tight: all of them load on every
turn. Anything only *sometimes* relevant is cheaper as a skill, which stays out of
context until the moment it applies.
