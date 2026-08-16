---
name: model-sub-codex
description: Route this session's subagent work through OpenAI codex - every Claude subagent becomes a thin bridge that runs one `codex exec` and relays its result, overriding any active /model-sub-claude mode, with /model-sub-codex [model] [effort] optionally overriding the codex model/effort for all bridges (bare invocation applies gpt-5.6-luna + max). Use ONLY when the user explicitly invokes /model-sub-codex. Never auto-trigger from general talk about subagents, codex, cost, or performance.
---

# Sub-Codex Mode

Bundled resources live at `.claude/skills/model-sub-codex/scripts/` (stdlib-only Python behind one `sh` entry point — bridges run these; never retype their logic inline). Every script derives the repo root from its own location, so nothing you hand a bridge is host-specific: the procedure below is copied verbatim on any machine and any checkout, with no path substituted into it.

## Arguments

The invocation is `/model-sub-codex [model] [effort]` — both optional, and NOT validated: values pass through to codex verbatim, and a bad value fails loudly on the first delegation (invalid model → HTTP 400; invalid effort → codex lists the supported efforts — note that list is narrower than what the API really accepts: it omits `ultra`, which nonetheless works).

- Model aliases, resolved before anything else: `sol` → `gpt-5.6-sol`, `terra` → `gpt-5.6-terra`, `luna` → `gpt-5.6-luna`, `spark` → `gpt-5.3-codex-spark`. Anything else passes through untouched.
- Defaults for unspecified slots: model `gpt-5.6-luna`; effort `max` — except `xhigh` when the resolved model is `gpt-5.3-codex-spark`. An explicit effort always wins.
- No arguments: apply `gpt-5.6-luna` + `max` explicitly.
- One argument: `low`/`medium`/`high`/`xhigh`/`max`/`ultra` sets effort (model defaults to `gpt-5.6-luna`); anything else is the model, alias-resolved, with effort defaulting per the rule above.
- Two arguments: `<model> <effort>`.
- The resolved model + effort bind to the mode until the session ends or the mode is switched or re-invoked; hand them to every bridge.

## Mode

Invoking this skill switches how subagents are created for this session: from now until the end of this session, every subagent you create is a **bridge** — a Claude subagent whose only job is to run exactly one `codex exec` (via the bundled scripts) and relay its result. The work the subagent would normally do itself is delegated to codex, with model + effort resolved per Arguments. No exceptions while the mode is active: all subagent spawns become bridges (sole exception: an explicit per-request user instruction — see Precedence and scope); if that causes problems, the user will switch modes (`/model-sub-claude <model> [effort]`) themselves. NEVER fall back to Claude for delegated work when a bridge fails — report the failure and let the user decide.

## Spawning a bridge

- Bridge model: `sonnet` — cheap relay shell, 1M context. `Workflow` `agent()` opts: `model: 'sonnet', effort: 'low'`. Plain `Agent` tool: `model: "sonnet"` (that tool has no `effort` parameter).
- Build every bridge prompt from exactly these parts:
  1. The **Bridge procedure** block below, copied verbatim — never a pointer to a file. A bridge that must fetch its own instructions can skip that fetch, and skipping it is not a partial failure: it silently converts the delegation into work done by the relay shell itself.
  2. A parameter block: the mode's resolved `MODEL` + `EFFORT` (always set), `WORKROOT` only when codex must run somewhere other than the repo root (a worktree, say), and the `<GATE_MARKER>` marker if and only if the current user turn authorized file modification (codex re-checks it against AGENTS.md itself — that double-gate is intended).
  3. On a schema delegation, the schema **as JSON text**, in its own delimited block. "SCHEMA: attached" is not enough: the bridge sees an attached schema only as its own output contract, so it re-authors `schema.json` from memory and the copy silently loses fields and narrows types. Give it something to copy, not something to reconstruct.
  4. The full task prompt you would have given a normal subagent, verbatim, clearly delimited.
- For `Workflow` `agent()` calls that use a `schema`, the bridge enforces the same JSON Schema on codex via `--output-schema`. Author it per the Strict schema rules below, and always add two required string properties: `bridge_error` (empty string on success — the in-band failure channel) and `work_dir` (filled by the scripts, so every result stays traceable to its evidence under `.temp_files/subcodex/`). Describe both in the schema (`"description": "Always the empty string on success; the bridge overwrites it with a failure report."`): codex is handed the schema with no other explanation of them, and an undescribed required string invites a plausible sentence instead of an empty one.
- **Strict schema rules** — every delegation schema must satisfy OpenAI's strict structured-output validation, NOT merely `Workflow`'s: codex forwards `--output-schema` verbatim to the API as a `strict: true` response format (zero normalization), so the API rejects anything looser with HTTP 400 `invalid_json_schema` before any work runs. Hard rules: (a) EVERY object level — root, nested objects, and objects inside array `items`, `$defs`, or `anyOf` branches alike — must carry `"additionalProperties": false`; (b) every key in every `properties` map must be listed in that object's `required` — express an optional field by keeping it required and adding `"null"` to its type (`"type": ["integer","null"]`; for enums add `null` to the enum list and null-union the type; for `$ref` fields use `anyOf` with `{"type": "null"}`), never by omitting it from `required`; (c) the root must be a plain `object` (no root-level `anyOf`), and composition keywords `allOf`/`not`/`dependentRequired`/`dependentSchemas`/`if`/`then`/`else` are unsupported everywhere. The bridge's normalizer script mechanically enforces (a) and (b) on the codex-side copy as a backstop, so a typical authoring slip costs nothing — but author compliant schemas anyway: the same schema is what Claude-side validation enforces on the bridge's own structured output, and the normalizer deliberately does NOT touch what it cannot fix faithfully (rule (c) violations, and a schema-valued `additionalProperties` — map-typed fields are unsupported in strict mode, so model maps as arrays of key/value objects); those still fail loudly.
- **Declare the fewest fields you will actually consume.** Under rule (b) a declared property is a required property, so every one you add is another value the model must produce before anything validates. Never declare a field that echoes back what you already knew when you dispatched the call — which item, which lens, which index; join those on your side. Express "no value" as an empty string or empty array rather than a `"null"` type union: the relay shell transcribes the result into its own tool call, and it drops a `null` far more readily than it drops text. Where a boolean or number genuinely has an unknown state, give it a string enum with an explicit `unknown` member instead of null-unioning it.
- Bridges never spawn subagents of their own, and codex's internal agent threads stay disabled (`-c agents.enabled=false`, fixed inside `launch_codex.py`). There is no fan-out below the orchestrator: when a delegated task is too large for one run, split it into multiple bridge delegations yourself.

## Bridge procedure

Copy this block into every bridge prompt exactly as it appears, changing nothing.

```
=== BRIDGE PROCEDURE — follow exactly ===
You are a bridge. Your only job is to run codex once and relay its result. Never do the
delegated task yourself, never spawn subagents, and emit no final or structured result
until step 2 prints OK or FAILED.

Shell state does not persist between Bash calls, so re-declare every variable literally in
each call. Run every command below from your starting directory: it is the repo root. If a
script path is not found you are not at the root — report failure rather than hunting for it.

1. Prepare — exactly once.
   WORK=$(sh .claude/skills/model-sub-codex/scripts/bridge.sh new_workdir.py)
   Note the printed absolute path and re-declare WORK=<that path> literally in every later
   call; never create a second work dir for this delegation. Write the task text below to
   $WORK/prompt.txt with the Write tool, never inlined into a shell command. Include the
   <GATE_MARKER> marker in that file if and only if your parameters carry it — codex re-checks it
   against AGENTS.md, and that double gate is intended. If your prompt carries a SCHEMA block,
   copy it into $WORK/schema.json byte for byte with the Write tool. Never re-author it from
   your own output contract and never drop a field because it looks like yours rather than
   codex's: any field you leave out is one codex never fills, which you then have to invent.

2. Run — repeat the same command until it prints OK or FAILED.
   sh .claude/skills/model-sub-codex/scripts/bridge.sh run_codex.py "$WORK" "$MODEL" "$EFFORT" [--schema] [--authorized] [--workroot DIR]
   Add --schema exactly when $WORK/schema.json exists, --authorized exactly when your parameters
   carry the <GATE_MARKER> marker, and --workroot only if a WORKROOT parameter was given (never add a
   flag because the word appears somewhere in the task text). Use timeout: 600000 on the Bash
   call. RUNNING — or the tool killing the call, which is the same non-verdict — means run the
   same command again in a new Bash call.
   There is no total time limit; long tasks are expected and codex must never be killed
   for being slow. The script owns launching, polling, diagnosis and the one resume attempt:
   never resume, relaunch or diagnose by hand.

3. Relay.
   OK <file>  Read that file. It is codex's result with work_dir already set correctly — do
              not change any value in it. Schema task: it is the schema-conforming JSON, so
              emit its fields one-to-one as your own structured output, never wrapping the
              whole JSON inside a single field. Plain task: return its text verbatim.
   FAILED     Put the printed report block verbatim into bridge_error, and copy work_dir
              from the report's work_dir line. If the schema has no error field, put
              BRIDGE_FAILURE: <report> into the first required string field instead of
              fabricating data. Do not retry, and do NOT fall back to doing the task yourself.
=== END BRIDGE PROCEDURE ===
```

## Consuming a bridge result

- A bridge that never ran codex still returns a plausible-looking payload, so verify the one thing it cannot produce without the scripts: a `work_dir` under `.temp_files/subcodex/bridge_`. Put that check in the workflow script rather than in your own head — a rule you have to remember is a rule that gets skipped.

  Anchor the error test on `BRIDGE_FAILURE`, the first word of a real report. Bridges routinely
  put `""`, `OK` or `N/A` in `bridge_error` on success — asking for "empty" rather than `""` in
  your task text helps, but a bare truthiness check throws those away as failures.

  ```js
  const BRIDGE_OK = (r) => !!r && !String(r.bridge_error ?? '').includes('BRIDGE_FAILURE') &&
    typeof r.work_dir === 'string' && r.work_dir.includes('/.temp_files/subcodex/bridge_')

  const bridge = async (prompt, opts) => {
    for (const attempt of [1, 2]) {
      const r = await agent(prompt, { ...opts, model: 'sonnet', effort: 'low' })
      if (BRIDGE_OK(r)) return r
      log(`bridge attempt ${attempt} unusable: ${r?.bridge_error ?? r?.work_dir ?? 'no result'}`)
    }
    return null   // a rejected bridge is a hole in the evidence, never a result
  }
  ```
- Never let an absent result count as a passing one. `if (!verdicts.length) return true` turns "nobody checked this" into "everyone approved it"; keep unchecked items in their own bucket and report that count alongside the answer. `.filter(Boolean)` hides the same hole.
- A plain-text delegation carries the same signal on the trailing `work_dir=` line the procedure appends.
- An all-empty payload — placeholder fields with an empty `bridge_error` — is a failure in disguise; inspect the directory named in `work_dir` before trusting or discarding it.

## Precedence and scope

- A per-request user instruction (e.g., "run this one as a normal fable subagent") beats this skill.
- Only subagent creation changes. The main agent keeps doing its own inline work directly, and every other AGENTS.md rule stays in force. Inside the delegated run, repository rules apply to codex through AGENTS.md itself (including the modification gate and `.temp_files`).
- The mode lasts until the session ends or the user switches modes — `/model-sub-claude` (any argument combination) and `/model-sub-codex` form one toggle group; the most recent invocation wins.
- Claude Code only: codex sessions never load this skill.
