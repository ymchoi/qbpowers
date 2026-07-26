---
name: model-sub-claude
description: Set this session's default subagent model/effort explicitly via /model-sub-claude [model] [effort] (e.g. /model-sub-claude sonnet high), canceling any active /model-sub-codex mode. Omitted slots default to opus + max; an unknown value or extra arguments must be refused with a usage reminder, changing nothing. Use ONLY when the user explicitly invokes /model-sub-claude. Never auto-trigger from general talk about subagents, models, cost, or performance.
---

# Sub-Claude Mode

## Arguments

The invocation is `/model-sub-claude [model] [effort]` — both optional.

- Defaults, applied to whichever slot the user leaves unspecified: model `opus`; effort `max`.
- No arguments: apply `opus` + `max` explicitly — still a real action, since it also cancels any active `/model-sub-codex` mode and pins the default against later drift.
- One argument: `low`/`medium`/`high`/`xhigh`/`max` sets effort (model defaults to `opus`); `fable`/`opus`/`sonnet`/`haiku` sets the model (effort defaults to `max`).
- Two arguments: `<model> <effort>`.
- An unknown value or extra arguments: change NOTHING — do not touch the active mode. Reply with one usage line — `usage: /model-sub-claude [model] [effort] — model: fable|opus|sonnet|haiku (default opus), effort: low|medium|high|xhigh|max (default max)` — plus the currently active subagent mode, and stop.

## Mode

Invoking this skill with valid arguments pins the subagent defaults for this session: from now until the end of the session, default every subagent you create to the chosen model + effort. Because this is an explicit pin, soft phrasing in later prompts ("keep it lightweight", "cheaply") must not drift the default; only an explicit per-request instruction ("run this one with haiku") overrides it, and only for that request.

## How to apply on each spawn path

- `Workflow` `agent()` opts: pass `model: '<model>', effort: '<effort>'`.
- Plain `Agent` tool: pass `model: "<model>"` only — the tool has no `effort` parameter, so effort inherits the session value (the plain tool cannot reach other efforts, so pass the chosen effort explicitly on every path that does expose an effort knob).
- Any other path with a model knob (e.g., ad-hoc agent definitions you author): pick the chosen model, and the chosen effort wherever an effort knob exists.
- Nesting: plain-`Agent` subagents can spawn subagents of their own, and those nested spawns do not know about this pin. Append one line to every plain-`Agent` subagent prompt: "Default any subagents you spawn to model <model> as well." Workflow-spawned agents have no agent-spawning tools, so they never need the line.
- Leave agents whose definitions already pin a `model:` in frontmatter (e.g., specialized `.claude/agents` types) alone: this skill sets the default; it does not fight explicit pins.

## Precedence and scope

- A per-request user instruction ("run this one with haiku") beats this skill. Soft phrasing ("keep it lightweight") is not such an instruction — hold the pinned default unless the user explicitly names a model.
- Only the model/effort defaults for subagents are affected. Every other project rule stays in force unchanged.
- The mode lasts until the session ends or the user switches modes — `/model-sub-claude` (any argument combination) and `/model-sub-codex` form one toggle group; the most recent invocation wins.
- Claude Code only: codex never loads this skill.
