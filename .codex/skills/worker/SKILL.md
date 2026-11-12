---
name: worker
description: Choose native Codex subagents for this session. Usage $worker [codex-light | codex | codex-max | none], default codex.
---

# Worker routing

Until the session ends, delegate work by the column this invocation selects. The latest `$worker` wins, and a routing table the user gives in the session replaces this one until the next `$worker`.

- `$worker` or `$worker codex`: the `codex` column.
- `$worker codex-light`: the `codex-light` column.
- `$worker codex-max`: the `codex-max` column.
- `$worker none`: start no workers or new worker tasks; do the work yourself. Let already-running tasks finish and collect their results.

| Work | codex-light | codex | codex-max |
|---|---|---|---|
| Hard: a bug of unknown cause, a design or architecture decision, a change across several modules, a change that is hard to undo (security, auth, payments, data migration) | astra max | astra max | astra max |
| Writing or changing code, tests or documents | sol max | astra max | astra max |
| Deep review of an important change | sol max | astra max | astra max |
| Web search; research in external documents or open source | sol max | sol max | astra max |
| General: the scope is set and judgment stays inside it. Reproduction, simple diagnosis, routine review and checks | sol max | sol max | astra max |
| Simple: nothing to interpret. Finding, reading, listing; running tests and reporting the result; a spelled-out edit in one or two files; mechanical repetition | sol max | sol max | astra max |
| Computer Use, one such worker at a time | sol max | sol max | astra max |

`astra` is `gpt-6-astra` and `sol` is `gpt-6.1-sol`; the word after the model is its `reasoning_effort`. Service tier follows the parent session; this skill has no speed option.

Whenever you can, split work across workers and run them in parallel; parallelize only tasks that can run side by side without trouble.

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
