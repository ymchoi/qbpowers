---
name: model-sub-codex
description: Route this session's subagent work to codex, run directly by the main agent. Usage /model-sub-codex [astra|sol|luna] [low|medium|high|xhigh|max], defaults luna max.
disable-model-invocation: true
---

# Sub-Codex Mode

## Arguments

- Model: `astra` → `gpt-6-astra`, `sol` → `gpt-6-sol`, `luna` → `gpt-6-luna` (default `luna`).
- Effort: `low`, `medium`, `high`, `xhigh`, `max` (default `max`).
- Any other value or extra arguments: change nothing; reply with `usage: /model-sub-codex [astra|sol|luna] [low|medium|high|xhigh|max]` and the active subagent mode.

## Mode

Until the session ends, work you would give a subagent goes to codex, which you run with the scripts below. Spawn no Claude subagents — no `Agent`, no `Workflow`, even with ultracode on. If a run fails, report it; never redo the work with Claude.

`/model-sub-codex` and `/model-sub-claude` are one toggle group: the latest invocation wins.

## Running codex

Scripts live in `.claude/skills/model-sub-codex/scripts/`; run them with the repo `.venv` Python.

1. `new_workdir.py [COUNT]` prints COUNT new work dirs.
2. Write each task to `<WORK>/prompt.txt`, with the `<GATE_MARKER>` marker only if the current user turn has it. For a JSON result, add `<WORK>/schema.json`.
3. Hand every work dir to one waiter in the background (`run_in_background: true`); it enforces the 32-process cap itself:
   `wait_codex.py --model <model> --effort <effort> [--authorized] <WORK>...`
   Pass `--authorized` exactly when the prompts carry the marker. Never give one work dir to two waiters.
4. Act on its summary:
   - `OK <file>`: codex's final message.
   - `FAILED <WORK> <kind>`: report it; don't rerun blindly.
   - `STALLED <WORK> <minutes>`: report it; never kill codex for being slow. The same command waits another round.
   - `RUNNING` / `QUEUED`: the same command continues the batch. After a usage limit, rerun it once the reset time shown has passed.
   - `SPAWNED <WORK> <n>`: codex spawned sub-agents despite the ban; report it.

## Schema

The waiter makes `schema.json` strict (`additionalProperties: false`, every property required). Avoid what it cannot fix: a non-object root, `allOf`/`not`/`if`/`then`/`else`/`dependentRequired`/`dependentSchemas`, and maps (use arrays of key/value objects).
