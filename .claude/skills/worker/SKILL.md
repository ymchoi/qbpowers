---
name: worker
description: Choose the workers this session delegates to. Usage /worker [COLUMN [fast|ultrafast] | none], where COLUMN is claude, hybrid or codex, optionally with -lightest, -lighter, -light or -max; default codex.
disable-model-invocation: true
---

# Worker routing

Until the session ends, delegate work by the column this invocation selects. The latest `/worker` wins, and a routing table the user gives in the session replaces this one until the next `/worker`.

- `/worker <column>`: that column of the tables below. `/worker` alone selects `codex`.
- `/worker none`: start no workers, Claude or GPT, and do all the work yourself. Workers already running finish; take their results.

`fast` or `ultrafast` after a hybrid or codex column puts that column's GPT workers on service tier `priority` or `ultrafast`. Otherwise, and in every claude column, GPT workers run at standard speed.

Kinds of work:

- **Hard**: a bug of unknown cause, a design or architecture decision, a change across several modules, a change that is hard to undo (security, auth, payments, data migration).
- **Review**: deep review of an important change.
- **Writing**: writing or changing code, tests or documents.
- **General**: the scope is set and judgment stays inside it. Reproduction, simple diagnosis, routine review and checks.
- **Research**: web search; research in external documents or open source.
- **Simple**: nothing to interpret. Finding, reading, listing; running tests and reporting the result; a spelled-out edit in one or two files; mechanical repetition.
- **Computer Use**: one such worker at a time.

| Work | claude-lightest | claude-lighter | claude-light | claude | claude-max |
|---|---|---|---|---|---|
| Hard | opus high | opus xhigh | opus xhigh | opus xhigh | fable xhigh |
| Review | opus medium | opus medium | opus high | opus high | opus xhigh |
| Writing | sonnet medium | opus medium | opus high | opus high | opus xhigh |
| General | haiku xhigh | sonnet medium | opus medium | opus medium | opus xhigh |
| Research | haiku high | haiku max | sonnet high | opus medium | opus high |
| Simple | haiku high | haiku max | sonnet high | opus medium | opus high |
| Computer Use | luna high | luna xhigh | terra xhigh | sol xhigh | sol xhigh |

| Work | hybrid-lightest | hybrid-lighter | hybrid-light | hybrid | hybrid-max |
|---|---|---|---|---|---|
| Hard | opus high | opus xhigh | opus xhigh | opus xhigh | fable xhigh |
| Review | opus medium | opus medium | opus high | opus high | opus xhigh |
| Writing | terra xhigh | sol high | sol high | sol xhigh | astra xhigh |
| General | terra high | terra xhigh | terra xhigh | sol high | sol max |
| Research | luna high | luna xhigh | terra medium | terra xhigh | sol xhigh |
| Simple | luna high | luna xhigh | terra medium | terra xhigh | sol xhigh |
| Computer Use | luna high | luna xhigh | terra xhigh | sol xhigh | sol xhigh |

| Work | codex-lightest | codex-lighter | codex-light | codex | codex-max |
|---|---|---|---|---|---|
| Hard | sol high | sol xhigh | sol max | astra xhigh | astra max |
| Review | sol high | sol xhigh | sol xhigh | sol max | astra max |
| Writing | terra xhigh | sol high | sol high | sol xhigh | astra xhigh |
| General | terra high | terra xhigh | terra xhigh | sol high | sol max |
| Research | luna high | luna xhigh | terra medium | terra xhigh | sol xhigh |
| Simple | luna high | luna xhigh | terra medium | terra xhigh | sol xhigh |
| Computer Use | luna high | luna xhigh | terra xhigh | sol xhigh | astra max |

`opus`, `sonnet`, `haiku` and `fable` are Claude subagents; `astra` (`gpt-6-astra`), `sol` (`gpt-6.1-sol`), `terra` (`gpt-6.1-terra`) and `luna` (`gpt-6-luna`) run through codex. The word after the model is its effort. Computer Use always runs through codex, in the claude columns too.

Whenever you can, split work across workers and run them in parallel; parallelize only tasks that can run side by side without trouble.

If a worker fails, report it; do not quietly hand its work to a different worker or do it yourself. Trying the same worker again is fine.

## Claude workers

Spawn with the `Agent` tool: `subagent_type: worker-effort-<effort>`, `model: <opus|sonnet|haiku|fable>`.

## GPT workers

Run codex with the scripts in `.claude/skills/worker/scripts/`, using the repo `.venv` Python.

1. `new_workdir.py [COUNT]` prints COUNT new work dirs.
2. Write each task to `<WORK>/prompt.txt`. For a JSON result, add `<WORK>/schema.json`.
3. Hand the work dirs to one waiter in the background (`run_in_background: true`):
   `wait_codex.py --model <astra|sol|terra|luna> --effort <effort> [--service-tier <tier>] <WORK>...`
   Add `--workroot <DIR>` when codex must work outside the repo root, such as in a worktree. Add `--cap N` (runs at once, default 64), `--launch-gap S` (seconds between starts) or `--retries N` (fresh restarts of a run that failed for good) when the user asks for them.
   Never give one work dir to two waiters, and never stop a waiter's background task: that also kills the codex runs it started. To act on each run as it ends, give each its own waiter.
4. Act on the summary:
   - `OK <file>`: codex's final message.
   - `FAILED <WORK> <kind>`: report it; do not rerun blindly.
   - `STALLED <WORK> <minutes>`: report it; never kill codex for being slow. The same command waits another round.
   - `RUNNING` / `QUEUED`: the same command continues the batch. After a usage limit, rerun it once the reset time shown has passed.
5. To answer a worker's question or give it follow-up instructions, write them to `<WORK>/reply.txt` and run the waiter on that work dir again. The run continues in the same codex session.

The waiter makes `schema.json` strict (`additionalProperties: false`, every property required). Avoid what it cannot fix: a non-object root, `allOf`/`not`/`if`/`then`/`else`/`dependentRequired`/`dependentSchemas`, and maps (use arrays of key/value objects).
