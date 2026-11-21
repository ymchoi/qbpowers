---
name: worker
description: Choose native Codex subagents for this session. Usage $worker [codex-lighter | codex-light | codex | codex-max | none], default codex.
---

# Worker routing

Until the session ends, delegate work by the column this invocation selects. The latest `$worker` wins, and a routing table the user gives in the session replaces this one until the next `$worker`.

- `$worker <column>`: that column of the table below. `$worker` alone selects `codex`.
- `$worker none`: start no workers or new worker tasks; do the work yourself. Let already-running tasks finish and collect their results.

Kinds of work:

- **Hard**: what to do is not yet known, as with a bug of unknown cause or a design or architecture decision; or the effect, once it runs, is costly to undo; and work of that kind.
- **Deep Review**: review that looks for defects, reading callers and tests. For the result of a Hard task, and for a change where a mistake is costly to undo, such as deleting or overwriting files or data, handling secrets or permissions, spending money, and changes of that kind.
- **Writing**: writing or changing code, tests or documents, including carrying out a decided design, however many modules it touches.
- **General**: the scope is set and judgment stays inside it, as with reproduction, simple diagnosis, measurement, routine checks, and light review (comments, tests, documents) or slop review of a code change, and work of that kind.
- **Research**: web search; research in external documents or open source.
- **Simple**: nothing to interpret, as with finding, reading and listing, running tests and reporting the result, a spelled-out edit in one or two files, mechanical repetition, and work of that kind.
- **Computer Use**: one such worker at a time.

| Work | codex-lighter | codex-light | codex | codex-max |
|---|---|---|---|---|
| Hard | sol xhigh | sol max | astra xhigh | astra max |
| Deep Review | sol high | sol xhigh | sol max | astra xhigh |
| Writing | terra high | sol medium | sol xhigh | astra xhigh |
| General | terra high | sol medium | sol xhigh | astra xhigh |
| Research | terra medium | terra high | sol medium | astra high |
| Simple | terra medium | terra high | sol medium | astra high |
| Computer Use | terra medium | terra high | sol xhigh | astra xhigh |

`astra` is `gpt-6.2-astra`, `sol` is `gpt-6.2-sol` and `terra` is `gpt-6.1-terra`; the word after the model is its `reasoning_effort`. Service tier follows the parent session; this skill has no speed option.

Whenever you can, split work across workers and run them in parallel; parallelize only tasks that can run side by side without trouble.

Have a change to code that git does not ignore reviewed before you report it done, by workers that did not write it, side by side: a light review by a General worker, or a Deep Review where its definition applies; and a slop review by another General worker. A Simple edit or a change to documents alone needs none. Give each reviewer the requirements and the diff of this task's files only, new files included, not your suspicions, and the path of its guide: `.claude/skills/worker/review-light.md` for a light review, `.claude/skills/worker/review-deep.md` for a Deep Review, `.claude/skills/worker/review-slop.md` for a slop review. Do not restate the guide. Fix each finding or reject it with a reason. Before deleting code a slop finding names, check yourself what produces its case here: you know the project and the reviewer may not. If a fix adds logic beyond what its finding asked for, or deletes the handling of a case, have only the changed lines reviewed once more; no further rounds. Report the counts, what you rejected and why, and what is left.

## Native subagents

Use `spawn_agent` with the route's `model` and `reasoning_effort`, a descriptive `task_name`, and `fork_turns: "none"`. A full-history fork inherits the parent's model and effort, so it cannot implement this routing table's explicit model choices.

Give each worker a self-contained task prompt with:

- The goal, repository or worktree path, relevant facts and decisions, and the files it owns or a read-only scope.
- The checks to run and what counts as done.
- Current permissions and restrictions. Give scratch files a task-specific path under `.temp_files/YYYYMMDD_HHMMSS_<purpose>/`.
- A reminder that other work shares the filesystem: preserve others' changes. Do the assigned task directly, without starting more workers or another coding-agent process. Send questions and blockers to the parent.

Use `send_message` for updates or answers while a worker runs; use `followup_task` to give an existing worker more work or resume it with an answer after it finishes. Pass the current restrictions with follow-ups. Reuse a worker only when its model and effort match the route for the new task.

Use `wait_agent` for completion notifications and `list_agents` when status is needed. A slow worker or an expired wait is not a failed worker; do not stop it merely for taking time.

If a worker fails, report it; do not quietly hand its work to a different worker or do it yourself. Retrying the same worker is allowed. If native subagents or the selected model are unavailable, report that limitation instead of starting a CLI subprocess.
