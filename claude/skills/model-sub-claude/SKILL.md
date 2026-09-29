---
name: model-sub-claude
description: Pin this session's subagent model and effort, canceling /model-sub-codex. Usage /model-sub-claude [fable|opus|sonnet|haiku] [low|medium|high|xhigh|max], defaults opus max.
disable-model-invocation: true
---

# Sub-Claude Mode

## Arguments

- Model: `fable`, `opus`, `sonnet`, `haiku` (default `opus`). Effort: `low`, `medium`, `high`, `xhigh`, `max` (default `max`).
- Any other value or extra arguments: change nothing; reply with `usage: /model-sub-claude [fable|opus|sonnet|haiku] [low|medium|high|xhigh|max]` and the active subagent mode.

## Mode

Until the session ends, every subagent you create runs on the pinned model and effort. Soft phrasing ("keep it light", "cheaply") does not change the pin; only an explicit per-request model or effort does, for that request only.

`/model-sub-claude` and `/model-sub-codex` are one toggle group: the latest invocation wins.

## Spawning

Subagents run as type `sub-effort-<effort>`, which cannot spawn subagents of its own.

- Ultracode on: use `Workflow`, with `agentType: 'sub-effort-<effort>', model: '<model>', effort: '<effort>'` in every `agent()` call.
- Ultracode off: no `Workflow` unless the user asks for one in that request. Use the `Agent` tool with `subagent_type: "sub-effort-<effort>"` and `model: "<model>"`, also for work you would give `Explore` or `Plan`. Purpose-built types such as `claude-code-guide` keep their type and get only `model`.
