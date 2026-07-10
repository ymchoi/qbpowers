---
name: model-sub-claude
description: Set this session's default subagent model/effort explicitly via /model-sub-claude <model> [effort] (e.g. /model-sub-claude opus max), overriding the AGENTS.md subagent defaults and canceling any active /model-sub-codex mode. Effort defaults to max when omitted; a bare /model-sub-claude with no arguments must be refused with a usage reminder, changing nothing. Use ONLY when the user explicitly invokes /model-sub-claude. Never auto-trigger from general talk about subagents, models, cost, or performance.
---

# Sub-Claude Mode

## Arguments

The invocation is `/model-sub-claude <model> [effort]`.

- `<model>` — required, one of: `fable`, `opus`, `sonnet`, `haiku`.
- `[effort]` — optional, one of: `low`, `medium`, `high`, `xhigh`, `max`. Defaults to `max` when omitted.
- Bare `/model-sub-claude`, an unknown value, or extra arguments: change NOTHING — do not touch the active mode. Reply with one usage line — `usage: /model-sub-claude <model> [effort] — model: fable|opus|sonnet|haiku, effort: low|medium|high|xhigh|max (default max)` — plus the currently active subagent mode, and stop.

## Mode

The AGENTS.md subagent rule begins "Unless the user explicitly specifies a subagent's `model`/`effort`". Invoking this skill with valid arguments IS that explicit specification: from now until the end of this session, default every subagent you create to the chosen model + effort. Because this is an explicit pin — not just the AGENTS.md prose default — soft phrasing in later prompts ("keep it lightweight", "cheaply") must not drift the default; only an explicit per-request instruction ("run this one with haiku") overrides it, and only for that request.

## How to apply on each spawn path

- `Workflow` `agent()` opts: pass `model: '<model>', effort: '<effort>'`.
- Plain `Agent` tool: pass `model: "<model>"` only — the tool has no `effort` parameter, so effort inherits the session value (under this repo's usual setup that is xhigh; the plain tool cannot reach other efforts, so pass the chosen effort explicitly on every path that does expose an effort knob).
- Any other path with a model knob (e.g., ad-hoc agent definitions you author): pick the chosen model, and the chosen effort wherever an effort knob exists.
- Nesting: plain-`Agent` subagents can spawn subagents of their own, and project instructions re-injected into them would pull nested spawns back to the AGENTS.md default. If the chosen model is not `opus`, append one line to every plain-`Agent` subagent prompt: "Default any subagents you spawn to model <model> as well." If it is `opus`, no line is needed — and stop adding one to new spawns if a previous mode required it (agents already running keep the instructions they were given). Workflow-spawned agents have no agent-spawning tools, so they never need the line.
- Leave agents whose definitions already pin a `model:` in frontmatter (e.g., specialized `.claude/agents` types) alone: this skill sets the default; it does not fight explicit pins.

## Precedence and scope

- A per-request user instruction ("run this one with haiku") beats this skill, exactly as it would beat the AGENTS.md default. Soft phrasing ("keep it lightweight") is not such an instruction — hold the pinned default unless the user explicitly names a model.
- Only the model/effort defaults of the AGENTS.md Subagents section are affected. Every other bullet of that section — and the rest of AGENTS.md — stays in force unchanged.
- The mode lasts until the session ends or the user switches modes — `/model-sub-claude` (any argument combination) and `/model-sub-codex` form one toggle group; the most recent invocation wins. `/model-sub-claude opus max` (or bare-effort `/model-sub-claude opus`) restores the AGENTS.md defaults.
- Claude Code only: codex never loads this skill and keeps its AGENTS.md default (`gpt-5.6-sol`+`ultra`).
