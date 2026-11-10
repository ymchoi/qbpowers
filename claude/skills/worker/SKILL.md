---
name: worker
description: Choose the workers this session delegates to. Usage /worker [claude-light | claude | hybrid [fast|ultrafast] | codex-light [fast|ultrafast] | codex [fast|ultrafast] | none], default hybrid.
disable-model-invocation: true
---

# Worker routing

Until the session ends, delegate work by the column this invocation selects. The latest `/worker` wins, and a routing table the user gives in the session replaces this one until the next `/worker`.

- `/worker` or `/worker hybrid`: the `hybrid` column.
- `/worker claude-light`: the `claude-light` column.
- `/worker claude`: the `claude` column.
- `/worker codex-light`: the `codex-light` column.
- `/worker codex`: the `codex` column.
- `/worker none`: start no workers, Claude or GPT, and do all the work yourself. Workers already running finish; take their results.

`fast` or `ultrafast` after `hybrid`, `codex-light` or `codex` puts that column's GPT workers on service tier `priority` or `ultrafast`. Otherwise, and in both claude columns, GPT workers run at standard speed.

| Work | claude-light | claude | hybrid | codex-light | codex |
|---|---|---|---|---|---|
| Hard: a bug of unknown cause, a design or architecture decision, a change across several modules, a change that is hard to undo (security, auth, payments, data migration) | opus xhigh | opus max | opus max | astra max | astra max |
| Writing or changing code, tests or documents | opus high | opus xhigh | astra max | sol max | astra max |
| Deep review of an important change | opus high | opus xhigh | opus xhigh | sol max | astra max |
| Web search; research in external documents or open source | opus medium | opus high | sol max | sol max | sol max |
| General: the scope is set and judgment stays inside it. Reproduction, simple diagnosis, routine review and checks | opus medium | opus high | sol max | sol max | sol max |
| Simple: nothing to interpret. Finding, reading, listing; running tests and reporting the result; a spelled-out edit in one or two files; mechanical repetition | opus medium | opus medium | sol max | sol max | sol max |
| Computer Use, one such worker at a time | sol max | sol max | sol max | sol max | sol max |

`opus` is a Claude subagent; `astra` (`gpt-6-astra`) and `sol` (`gpt-6.1-sol`) run through codex. Computer Use is the exception in every column: it always runs through codex.

Whenever you can, split work across workers and run them in parallel; parallelize only tasks that can run side by side without trouble.

If a worker fails, report it; do not quietly hand its work to a different worker or do it yourself. Trying the same worker again is fine.

## Claude workers

Spawn with the `Agent` tool: `subagent_type: worker-effort-<effort>`, `model: opus`.

## GPT workers

Run codex with the scripts in `.claude/skills/worker/scripts/`, using the repo `.venv` Python.

1. `new_workdir.py [COUNT]` prints COUNT new work dirs.
2. Write each task to `<WORK>/prompt.txt`. For a JSON result, add `<WORK>/schema.json`.
3. Hand the work dirs to one waiter in the background (`run_in_background: true`):
   `wait_codex.py --model <astra|sol> --effort <effort> [--service-tier <tier>] <WORK>...`
   Add `--workroot <DIR>` when codex must work outside the repo root, such as in a worktree. Add `--cap N` (runs at once, default 64), `--launch-gap S` (seconds between starts) or `--retries N` (fresh restarts of a run that failed for good) when the user asks for them.
   Never give one work dir to two waiters, and never stop a waiter's background task: that also kills the codex runs it started. To act on each run as it ends, give each its own waiter.
4. Act on the summary:
   - `OK <file>`: codex's final message.
   - `FAILED <WORK> <kind>`: report it; do not rerun blindly.
   - `STALLED <WORK> <minutes>`: report it; never kill codex for being slow. The same command waits another round.
   - `RUNNING` / `QUEUED`: the same command continues the batch. After a usage limit, rerun it once the reset time shown has passed.
5. To answer a worker's question or give it follow-up instructions, write them to `<WORK>/reply.txt` and run the waiter on that work dir again. The run continues in the same codex session.

The waiter makes `schema.json` strict (`additionalProperties: false`, every property required). Avoid what it cannot fix: a non-object root, `allOf`/`not`/`if`/`then`/`else`/`dependentRequired`/`dependentSchemas`, and maps (use arrays of key/value objects).
