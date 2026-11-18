---
name: worker
description: Choose the workers this session delegates to. Usage /worker [COLUMN [fast|ultrafast] | none], where COLUMN is claude or codex, optionally with -lighter, -light or -max; default codex.
disable-model-invocation: true
---

# Worker routing

Until the session ends, delegate work by the column this invocation selects. The latest `/worker` wins, and a routing table the user gives in the session replaces this one until the next `/worker`.

- `/worker <column>`: that column of the tables below. `/worker` alone selects `codex`.
- `/worker none`: start no workers, Claude or GPT, and do all the work yourself. Workers already running finish; take their results.

`fast` or `ultrafast` after a codex column puts that column's GPT workers on service tier `priority` or `ultrafast`. Otherwise, and in every claude column, GPT workers run at standard speed.

Kinds of work:

- **Hard**: what to do is not yet known, as with a bug of unknown cause or a design or architecture decision; or the effect, once it runs, is costly to undo; and work of that kind.
- **Deep Review**: review that looks for defects, reading callers and tests. For the result of a Hard task, and for a change where a mistake is costly to undo, such as deleting or overwriting files or data, handling secrets or permissions, spending money, and changes of that kind.
- **Writing**: writing or changing code, tests or documents, including carrying out a decided design, however many modules it touches.
- **General**: the scope is set and judgment stays inside it, as with reproduction, simple diagnosis, measurement, routine checks and light review of a code change (comments, simplicity, documents), and work of that kind.
- **Research**: web search; research in external documents or open source.
- **Simple**: nothing to interpret, as with finding, reading and listing, running tests and reporting the result, a spelled-out edit in one or two files, mechanical repetition, and work of that kind.
- **Computer Use**: one such worker at a time.

| Work | claude-lighter | claude-light | claude | claude-max |
|---|---|---|---|---|
| Hard | opus xhigh | opus xhigh | opus xhigh | fable xhigh |
| Deep Review | opus medium | opus high | opus high | opus xhigh |
| Writing | opus medium | opus high | opus high | opus xhigh |
| General | sonnet medium | opus medium | opus medium | opus xhigh |
| Research | haiku max | sonnet high | opus medium | opus high |
| Simple | haiku max | sonnet high | opus medium | opus high |
| Computer Use | terra medium | terra high | sol xhigh | sol xhigh |

| Work | codex-lighter | codex-light | codex | codex-max |
|---|---|---|---|---|
| Hard | sol xhigh | sol max | astra xhigh | astra max |
| Deep Review | sol high | sol xhigh | sol max | astra xhigh |
| Writing | terra high | sol medium | sol xhigh | astra xhigh |
| General | terra high | sol medium | sol xhigh | astra xhigh |
| Research | terra medium | terra high | sol medium | astra high |
| Simple | terra medium | terra high | sol medium | astra high |
| Computer Use | terra medium | terra high | sol xhigh | astra xhigh |

`opus`, `sonnet`, `haiku` and `fable` are Claude subagents; `astra` (`gpt-6.2-astra`), `sol` (`gpt-6.2-sol`) and `terra` (`gpt-6.1-terra`) run through codex. The word after the model is its effort. Computer Use always runs through codex, in the claude columns too.

Whenever you can, split work across workers and run them in parallel; parallelize only tasks that can run side by side without trouble.

Have a change to code that git does not ignore reviewed before you report it done, by a worker that did not write it: a light review by a General worker, or a Deep Review where its definition applies. A Simple edit or a change to documents alone needs none. Give the reviewer the requirements and the diff of this task's files only, new files included, not your suspicions, and the full path of its guide in this folder: `review-light.md` for a light review, `review-deep.md` for a Deep Review. Do not restate the guide. Fix each finding or reject it with a reason. If a fix adds logic beyond what its finding asked for, have only the fixed lines reviewed once more; no further rounds. Report the counts, what you rejected and why, and what is left.

If a worker fails, report it; do not quietly hand its work to a different worker or do it yourself. Trying the same worker again is fine.

## Claude workers

Spawn with the `Agent` tool: `subagent_type: worker-effort-<effort>`, `model: <opus|sonnet|haiku|fable>`.

## GPT workers

Run codex with the scripts in `.claude/skills/worker/scripts/`, using the repo `.venv` Python.

1. `new_workdir.py [COUNT]` prints COUNT new work dirs.
2. Write each task to `<WORK>/prompt.txt`. For a JSON result, add `<WORK>/schema.json`.
3. Hand the work dirs to one waiter in the background (`run_in_background: true`):
   `wait_codex.py --model <astra|sol|terra> --effort <effort> [--service-tier <tier>] <WORK>...`
   Add `--workroot <DIR>` when codex must work outside the repo root, such as in a worktree. Add `--cap N` (runs at once, default 64), `--launch-gap S` (seconds between starts) or `--retries N` (fresh restarts of a run that failed for good) when the user asks for them.
   Never give one work dir to two waiters, and never stop a waiter's background task: that also kills the codex runs it started. To act on each run as it ends, give each its own waiter.
4. Act on the summary:
   - `OK <file>`: codex's final message.
   - `FAILED <WORK> <kind>`: report it; do not rerun blindly.
   - `STALLED <WORK> <minutes>`: report it; never kill codex for being slow. The same command waits another round.
   - `RUNNING` / `QUEUED`: the same command continues the batch. After a usage limit, rerun it once the reset time shown has passed.
5. To answer a worker's question or give it follow-up instructions, write them to `<WORK>/reply.txt` and run the waiter on that work dir again. The run continues in the same codex session.

The waiter makes `schema.json` strict (`additionalProperties: false`, every property required). Avoid what it cannot fix: a non-object root, `allOf`/`not`/`if`/`then`/`else`/`dependentRequired`/`dependentSchemas`, and maps (use arrays of key/value objects).
