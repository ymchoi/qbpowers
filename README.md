# qbpowers

Agent skills for Claude Code and the OpenAI Codex CLI — a public snapshot of skills in daily use in a personal project.

| Skill | Claude | Codex | What it does |
|---|:---:|:---:|---|
| [model-sub-codex](#model-sub-codex) | ✓ | — | Delegate every subagent's work to the codex CLI. |
| [model-sub-claude](#model-sub-claude) | ✓ | — | Pin the session's default subagent model + effort. |
| [grill-me](#grill-me) | ✓ | ✓ | One-question-at-a-time interview that pressure-tests your plan. |
| [handoff](#handoff) | ✓ | ✓ | Session handover document a context-blind agent can resume from. |
| [tdd](#tdd) | ✓ | ✓ | Strict red–green–refactor workflow, one test at a time. |
| [diagnose-bug](#diagnose-bug) | ✓ | ✓ | Repro-first debugging loop for hard bugs. |

All skills are manual-only: they run when you type the command and never auto-trigger.

## model-sub-codex

*Claude Code only. Requires an installed, authenticated `codex` CLI.*

Turns every subagent this session spawns into a thin relay that runs exactly one `codex exec` and hands the result back: Claude Code stays the orchestrator, codex does the delegated work. Optional arguments override codex's `config.toml` model/effort defaults. If codex hits a usage limit, the session waits for the reset and re-runs the blocked work; if a delegation fails, it fails loudly instead of quietly doing the task in Claude.

```
/model-sub-codex                # codex config defaults
/model-sub-codex gpt-5.5 high   # pin codex model + effort for all delegations
```

Works best in Claude Code's ultracode mode, where subagents run through `Workflow` scripts — the setup this skill is designed around. Delegated codex runs can only modify files when your current message authorized modification (see Portability).

## model-sub-claude

*Claude Code only.*

Pins the default model and reasoning effort for every helper subagent Claude Code spawns in the rest of the session. Model: `fable` | `opus` | `sonnet` | `haiku` (required); effort: `low` | `medium` | `high` | `xhigh` | `max` (optional, default `max`). An explicit per-request model ("run this one with haiku") still wins for that one request; vague phrasing ("keep it cheap") doesn't move the pin.

```
/model-sub-claude haiku high    # cheap parallel fan-out from here on
/model-sub-claude opus          # opus + max (effort omitted = max)
/model-sub-claude fable max     # back to the project default
```

Forms a toggle group with `/model-sub-codex` — the most recent invocation wins.

## grill-me

Pressure-tests a plan you've already sketched. Asks exactly one question per turn, each with its own recommended answer so you can just confirm or push back, and works through the plan branch by branch. Anything the code can answer, it looks up itself instead of asking you.

```
# describe your plan first, then invoke:
I want to add rate limiting to the API. Sketch: token bucket, Redis, per API key.
/grill-me
```

The first focused question arrives (e.g. "per-key or per-IP? I'd recommend per-key because…") and the interview continues, one decision per turn, until nothing important is left undecided.

## handoff

Writes a handover document for the current session so a fresh agent with zero chat history can continue the work. The document goes to a single Markdown file under `.temp_files/` — you get back the path, not a wall of text in chat — and the skill critiques its own output as if it were the fresh agent, patching gaps before reporting.

```
/handoff
```

→ `.temp_files/20260705_142310_handoff_auth_refactor/handoff.md` + "self-check passed".

```
/handoff in Korean, focus on the failing auth test and what to try next
```

Free-text instructions steer length, language, format, and focus. (Codex trigger: `$handoff`.)

## tdd

Red–green–refactor (failing test → make it pass → clean up) with the discipline actually enforced: one failing test, the minimal code to pass it, repeat — never all-tests-then-all-code. It starts by agreeing on the public interface and which behaviors are worth testing; tests target observable behavior through public APIs so they survive refactors, and refactoring happens only once tests pass. Ships with companion guides on test quality, mocking, interface design, and refactoring.

```
/tdd
add a discount-code field to the checkout flow
```

It proposes the interface and the behaviors worth testing first, then writes one failing test and the minimal code to pass it, looping until done.

Needs a working test setup in your project — the skill brings the discipline, not a test runner.

## diagnose-bug

For bugs where you're stuck. It first builds a fast, repeatable way to trigger the bug (failing test, curl loop, request replay…) — a reliable repro is treated as 90% of the fix — then works through ranked hypotheses one at a time until the fix lands with a regression test. Flaky bugs are handled by making them reproduce more often (loop it 100×, add stress), not by demanding a clean one-shot repro.

```
/diagnose-bug the checkout API returns 500 intermittently under load
```

It first builds a stress loop that reliably triggers the 500, then shows you ranked hypotheses before changing any code.

Deliberately heavyweight — overkill for typo-level fixes.

## Installation

- **Claude Code**: copy a directory under `claude/skills/` into your project's `.claude/skills/`.
- **Codex CLI**: copy a directory under `codex/skills/` into your project's `.codex/skills/`.

## Repo extras

- Root `AGENTS.md` / `CLAUDE.md` — the live agent instruction files these skills grew out of; project-specific sections removed, usable as a template.
- `utils/fetch_web/` — Patchright-based fallback page fetcher used by the research rules in `AGENTS.md`. Requires `patchright==1.59.1` and Chrome (`pip install patchright && patchright install chrome`); always runs headed — Patchright loses its bot-detection evasion headless.

## Portability

The skills assume a few conventions from their home project — substitute your own:

- `.temp_files/` — a scratch-directory convention at the project root (used by handoff and model-sub-codex).
- `<project-root>` and `<GATE_MARKER>` — placeholders in `model-sub-codex` and `AGENTS.md` for your project's absolute path and your file-modification approval phrase (drop that rule if you don't use such a gate).

## License

Original skills (handoff, model-sub-claude, model-sub-codex) and everything else authored here: [Unlicense](LICENSE) — public domain. Derived skills (diagnose-bug, grill-me, tdd): modified from [mattpocock/skills](https://github.com/mattpocock/skills), MIT licensed — see [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).
