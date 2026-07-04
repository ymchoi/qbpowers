# qbpowers

A collection of agent skills for Claude Code and the OpenAI Codex CLI — a public snapshot of skills in daily use in a personal project.

## Skills

| Skill | Claude | Codex | Description |
|---|:---:|:---:|---|
| diagnose-bug | ✓ | ✓ | Disciplined diagnosis loop for hard bugs: reproduce → minimise → hypothesise → instrument → fix → regression-test. |
| grill-me | ✓ | ✓ | Relentless one-question-at-a-time interview about a plan until shared understanding is reached. |
| handoff | ✓ | ✓ | Generates a handover document a new, context-blind agent can continue the session from. |
| tdd | ✓ | ✓ | Red-green-refactor TDD workflow plus guides on test quality, mocking, and interface design. |
| model-sub-claude | ✓ | — | `/model-sub-claude <model> [effort]` — pin the session's default subagent model+effort explicitly. |
| model-sub-codex | ✓ | — | `/model-sub-codex [model] [effort]` — route every subagent through a `codex exec` bridge, with a rate-limit wait policy. |

## model-sub-claude

Pins the session's default subagent model and effort. Project instructions (`AGENTS.md`) set a default and defer to "explicit user specification" — invoking this skill *is* that specification: from invocation until the session ends, every subagent you spawn defaults to the chosen model + effort.

```
/model-sub-claude <model> [effort]
```

- `<model>` (required): `fable`, `opus`, `sonnet`, or `haiku`.
- `[effort]` (optional): `low`, `medium`, `high`, `xhigh`, or `max` — defaults to `max` when omitted.
- Bare `/model-sub-claude` changes nothing and replies with a one-line usage reminder plus the currently active mode.

Details:

- Applies on every spawn path: `Workflow` `agent()` calls get both `model` and `effort`; the plain `Agent` tool has no effort parameter, so effort inherits the session value there.
- For non-default models, a one-line propagation note is appended to plain-`Agent` subagent prompts so nested spawns stay on the chosen model.
- Agents whose definitions already pin a `model:` in frontmatter are left alone, and an explicit per-request instruction ("run this one with haiku") always wins; soft phrasing ("keep it lightweight") does not.
- `/model-sub-claude` and `/model-sub-codex` form a toggle group — the most recent invocation wins.

## model-sub-codex

Routes this session's subagent work through the OpenAI codex CLI. Every subagent becomes a **bridge**: a minimal Claude subagent whose only job is to run exactly one `codex exec` and relay its result. Claude Code stays the orchestrator; codex does the delegated work.

```
/model-sub-codex [model] [effort]
```

- No arguments: no overrides — codex uses its `~/.codex/config.toml` defaults.
- One argument: `minimal`/`low`/`medium`/`high`/`xhigh` is treated as effort-only; anything else is the model.
- Two arguments: `<model> <effort>`.
- Values pass through unvalidated — a bad model or effort fails loudly on the first delegation with codex's own error (invalid model → HTTP 400; invalid effort → codex lists the supported efforts).

**The bridge protocol.** Each bridge runs on a cheap relay model, creates a private work directory under `.temp_files/`, writes the delegated prompt to a file (no shell-quoting hazards), and launches codex detached via `nohup` with an exit-code sentinel file and a recorded PID. It then waits by polling in bounded calls — deliberately with **no total time limit**, since long codex runs are expected — distinguishing three verdicts: DONE (sentinel written), RUNNING (wrapper still alive), and CRASHED (wrapper died, so the sentinel will never appear). On success the bridge relays codex's final message verbatim — or, for schema tasks enforced via `--output-schema`, parses the JSON and emits its fields one-to-one, with required `bridge_error`/`work_dir` properties keeping failures and evidence traceable in-band. On failure it checks for context-window exhaustion (reported immediately — resuming a full session cannot help), then for codex's usage-limit error line, then makes exactly one `codex exec resume` recovery attempt before reporting a loud, machine-detectable `BRIDGE_FAILURE`. A bridge never silently falls back to doing the task itself.

**Rate-limit policy.** codex enforces a 5-hour and a weekly usage limit; a weekly wait can last days. A rate-limited bridge reports `RATE_LIMIT:` in-band together with codex's stderr text, which states the reset time. The orchestrator then never falls back to Claude for the delegated work: it records the blocked delegations in a durable ledger under `.temp_files/`, arms one persistent monitor that probes roughly every 3 hours for an early reset and otherwise wakes a few minutes past the stated time, and re-runs the blocked delegations fresh once the limit lifts. Re-entering the mode after a session restart re-checks the ledger and re-arms the wait.

**Modification gate.** The bridge includes the project's file-modification marker (`<GATE_MARKER>`) in the codex prompt if and only if the current user turn authorized modification — codex reads `AGENTS.md` itself, so unauthorized delegations are double-gated.

Requires an installed, authenticated codex CLI. `<project-root>` and `<GATE_MARKER>` are placeholders — see Portability notes.

## Installation

- **Claude Code**: copy a directory under `claude/skills/` into your project's `.claude/skills/`.
- **Codex CLI**: copy a directory under `codex/skills/` into your project's `.codex/skills/`.

## Instructions & utilities

- The root `AGENTS.md` / `CLAUDE.md` are the agent instruction files these skills grew out of — live instructions for this repository and a template you can adapt (project-specific sections removed).
- `utils/fetch_web/` — a Patchright-based fallback page fetcher referenced by the research rules in `AGENTS.md`. Requires `patchright==1.59.1` and Chrome (`pip install patchright && patchright install chrome`); always runs headed, since Patchright loses its bot-detection evasion in headless mode.

## Portability notes

These skills assume a few conventions from their home project:

- `.temp_files/` (handoff, model-sub-codex): a gitignored scratch-directory convention at the project root; substitute your own.
- `AGENTS.md` (model-sub-*): assumes a project instruction file defining subagent defaults and a file-modification gate — included at the repo root.
- `<project-root>` and `<GATE_MARKER>` in `model-sub-codex` and `AGENTS.md` are placeholders: replace them with your project's absolute path and your own modification-approval marker (or drop that rule if you don't use such a gate).

## License

- Original skills (handoff, model-sub-claude, model-sub-codex) and everything else authored here: [Unlicense](LICENSE) — public domain.
- Derived skills (diagnose-bug, grill-me, tdd): modified from [mattpocock/skills](https://github.com/mattpocock/skills), MIT licensed — see [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).
