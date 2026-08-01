---
name: model-sub-codex
description: Route this session's subagent work through OpenAI codex - every Claude subagent becomes a thin bridge that runs one `codex exec` and relays its result, overriding any active /model-sub-claude mode, with /model-sub-codex [model] [effort] optionally overriding the codex model/effort for all bridges (bare invocation applies gpt-5.6-luna + max). Use ONLY when the user explicitly invokes /model-sub-codex. Never auto-trigger from general talk about subagents, codex, cost, or performance.
---

# Sub-Codex Mode

All paths below use `$ROOT` = this session's absolute project root; substitute the real per-host value whenever you hand a path to a bridge. Bundled resources: `$ROOT/.claude/skills/model-sub-codex/scripts/` (Python, stdlib-only — bridges run these; never retype their logic inline) and `references/` (`bridge-procedure.md` — every bridge reads it as its first action).

## Arguments

The invocation is `/model-sub-codex [model] [effort]` — both optional, and NOT validated: values pass through to codex verbatim, and a bad value fails loudly on the first delegation (invalid model → HTTP 400; invalid effort → codex lists the supported efforts — note that list is narrower than what the API really accepts: it omits `ultra`, which nonetheless works).

- Model aliases, resolved before anything else: `sol` → `gpt-5.6-sol`, `terra` → `gpt-5.6-terra`, `luna` → `gpt-5.6-luna`, `spark` → `gpt-5.3-codex-spark`. Anything else passes through untouched.
- Defaults for unspecified slots: model `gpt-5.6-luna`; effort `max` — except `xhigh` when the resolved model is `gpt-5.3-codex-spark`. An explicit effort always wins.
- No arguments: apply `gpt-5.6-luna` + `max` explicitly.
- One argument: `low`/`medium`/`high`/`xhigh`/`max`/`ultra` sets effort (model defaults to `gpt-5.6-luna`); anything else is the model, alias-resolved, with effort defaulting per the rule above.
- Two arguments: `<model> <effort>`.
- The resolved model + effort bind to the mode until the session ends or the mode is switched or re-invoked; hand them to every bridge.

## Mode

Invoking this skill switches how subagents are created for this session: from now until the end of this session, every subagent you create is a **bridge** — a Claude subagent whose only job is to run exactly one `codex exec` (via the bundled scripts) and relay its result. The work the subagent would normally do itself is delegated to codex, with model + effort resolved per Arguments. No exceptions while the mode is active: all subagent spawns become bridges (sole exception: an explicit per-request user instruction — see Precedence and scope); if that causes problems, the user will switch modes (`/model-sub-claude <model> [effort]`) themselves.

## Spawning a bridge

- Bridge model: `sonnet` — cheap relay shell, 1M context. `Workflow` `agent()` opts: `model: 'sonnet', effort: 'low'`. Plain `Agent` tool: `model: "sonnet"` (that tool has no `effort` parameter).
- Build every bridge prompt from exactly these parts:
  1. First action: `Read $ROOT/.claude/skills/model-sub-codex/references/bridge-procedure.md and follow it exactly.`
  2. A parameter block: `ROOT`, `WORKROOT` (codex working root — normally `$ROOT`), the mode's resolved `MODEL` + `EFFORT` (always set), whether a schema is attached, and the `<GATE_MARKER>` marker if and only if the current user turn authorized file modification (codex re-checks it against AGENTS.md itself — that double-gate is intended).
  3. The full task prompt you would have given a normal subagent, verbatim, clearly delimited.
- For `Workflow` `agent()` calls that use a `schema`, the bridge enforces the same JSON Schema on codex via `--output-schema`. Author it per the Strict schema rules below, and always add two required string properties: `bridge_error` (empty string on success — the in-band failure channel) and `work_dir` (the bridge fills it with its work-dir absolute path, so every result stays traceable to its evidence under `$ROOT/.temp_files/subcodex/`).
- **Strict schema rules** — every delegation schema must satisfy OpenAI's strict structured-output validation, NOT merely `Workflow`'s: codex forwards `--output-schema` verbatim to the API as a `strict: true` response format (zero normalization), so the API rejects anything looser with HTTP 400 `invalid_json_schema` before any work runs. Hard rules: (a) EVERY object level — root, nested objects, and objects inside array `items`, `$defs`, or `anyOf` branches alike — must carry `"additionalProperties": false`; (b) every key in every `properties` map must be listed in that object's `required` — express an optional field by keeping it required and adding `"null"` to its type (`"type": ["integer","null"]`; for enums add `null` to the enum list and null-union the type; for `$ref` fields use `anyOf` with `{"type": "null"}`), never by omitting it from `required`; (c) the root must be a plain `object` (no root-level `anyOf`), and composition keywords `allOf`/`not`/`dependentRequired`/`dependentSchemas`/`if`/`then`/`else` are unsupported everywhere. The bridge's normalizer script mechanically enforces (a) and (b) on the codex-side copy as a backstop, so a typical authoring slip costs nothing — but author compliant schemas anyway: the same schema is what Claude-side validation enforces on the bridge's own structured output, and the normalizer deliberately does NOT touch what it cannot fix faithfully (rule (c) violations, and a schema-valued `additionalProperties` — map-typed fields are unsupported in strict mode, so model maps as arrays of key/value objects); those still fail loudly.
- Bridges never spawn subagents of their own, and codex's internal agent threads stay disabled (`-c agents.enabled=false`, fixed inside `launch_codex.py`). There is no fan-out below the orchestrator: when a delegated task is too large for one run, split it into multiple bridge delegations yourself.
- Sanity-check every bridge result you consume: an all-empty payload (empty or placeholder fields with an empty `bridge_error`) is a bridge failure in disguise — treat it as a failure and inspect the directory named in its `work_dir` field before trusting or discarding the work.

## Precedence and scope

- A per-request user instruction (e.g., "run this one as a normal fable subagent") beats this skill.
- If codex hits a usage limit, the bridge reports it as `RATE_LIMIT:`. Do NOT fall back to doing that work in Claude — report it to the user and stop.
- Only subagent creation changes. The main agent keeps doing its own inline work directly, and every other AGENTS.md rule stays in force. Inside the delegated run, repository rules apply to codex through AGENTS.md itself (including the modification gate and `.temp_files`).
- The mode lasts until the session ends or the user switches modes — `/model-sub-claude` (any argument combination) and `/model-sub-codex` form one toggle group; the most recent invocation wins.
- Claude Code only: codex sessions never load this skill.
