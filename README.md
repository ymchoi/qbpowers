# qbpowers

Agent skills for Claude Code and the OpenAI Codex CLI — a public snapshot of skills in daily use in a personal project.

**English** · [한국어](#한국어)

| Skill | Claude | Codex | What it does |
|---|:---:|:---:|---|
| [model-sub-codex](#model-sub-codex) | ✓ | — | Delegate every subagent's work to the codex CLI. |
| [model-sub-claude](#model-sub-claude) | ✓ | — | Pin the session's default subagent model + effort. |
| [grill-me](#grill-me) | ✓ | ✓ | Relentless questioning that aligns the agent's understanding with yours. |
| [handoff](#handoff) | ✓ | ✓ | Session handover document a context-blind agent can resume from. |

All skills are manual-only: they run when you type the command and never auto-trigger.

## model-sub-codex

*Claude Code only. Requires an installed, authenticated `codex` CLI.*

Works best in Claude Code's ultracode mode.

Turns every subagent this session spawns into a thin relay that runs exactly one `codex exec` and hands the result back.

**Design intent** — combine only the strengths of both models.

- **Orchestrator (Claude)**: 1M context, high reasoning quality, ultracode workflow
- **Worker (codex)**: low cost per task, fast turnaround

Each side covers the other's weak spot, so you get reasoning quality, cost savings, and throughput together.

```
/model-sub-codex                     # gpt-5.6-sol + xhigh
/model-sub-codex gpt-5.6-luna        # luna defaults to max effort
/model-sub-codex gpt-5.6-sol high    # pin model + effort for all delegations
```

If codex hits a usage limit, the session waits for the reset and re-runs the blocked work automatically.

## model-sub-claude

*Claude Code only.*

Pins the default model and reasoning effort for every subagent Claude Code spawns for the rest of the session. Model: `fable` | `opus` | `sonnet` | `haiku` (default `opus`); effort: `low` | `medium` | `high` | `xhigh` | `max` (default `max`).

```
/model-sub-claude               # opus + max (defaults)
/model-sub-claude sonnet        # sonnet + max (effort omitted = max)
/model-sub-claude sonnet high   # light, fast parallel fan-out
```

Forms a toggle group with `/model-sub-codex` — the most recent invocation wins.

## grill-me

The agent asks one pointed question per turn to **align its understanding of what you want to do with your own.** Plans, requirements, half-formed ideas — the target does not matter. Each question comes with a recommended answer, so you just confirm or push back, and anything the code can answer it looks up itself.

Simple but powerful — a few rounds of questions converge the agent's direction sharply onto your intent.

```
# describe what you want first, then invoke:
I want to record user activity logs and be able to analyse them later.
/grill-me
```

## handoff

Writes a handover document for the current session so a fresh agent with zero chat history can continue the work. The document goes to a single Markdown file under `.temp_files/` — you get back the path, not a wall of text in chat — and the skill critiques its own output as if it were the fresh agent, patching gaps before reporting.

```
/handoff
```

→ `.temp_files/20260705_142310_handoff_auth_refactor/handoff.md` + "self-check passed".

```
/handoff as a checklist of what's left, so the next session can start implementing right away
```

Free-text instructions steer length, language, format, and focus. (Codex trigger: `$handoff`.)

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

Original skills (handoff, model-sub-claude, model-sub-codex) and everything else authored here: [Unlicense](LICENSE) — public domain. Derived skill (grill-me): modified from [mattpocock/skills](https://github.com/mattpocock/skills), MIT licensed — see [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

---

# 한국어

Claude Code와 OpenAI Codex CLI를 위한 에이전트 스킬 모음 — 개인 프로젝트에서 매일 쓰는 스킬의 공개 스냅샷.

| 스킬 | Claude | Codex | 하는 일 |
|---|:---:|:---:|---|
| `model-sub-codex` | ✓ | — | 모든 subagent 작업을 codex CLI로 위임한다. |
| `model-sub-claude` | ✓ | — | 세션의 기본 subagent 모델 + effort를 고정한다. |
| `grill-me` | ✓ | ✓ | 압박 질문을 반복해 에이전트와 사용자의 이해를 일치시킨다. |
| `handoff` | ✓ | ✓ | 맥락 없는 에이전트도 이어받을 수 있는 인수인계 문서를 만든다. |

모든 스킬은 수동 전용이다 — 명령을 입력했을 때만 실행되며 자동으로 트리거되지 않는다.

## model-sub-codex

*Claude Code 전용. 설치·인증된 `codex` CLI 필요.*

Claude Code의 ultracode 모드에서 가장 잘 동작한다.

이 세션이 생성하는 모든 subagent를, `codex exec`을 정확히 한 번 실행하고 결과만 되돌려주는 얇은 릴레이로 바꾼다.

**설계 의도** — 두 모델의 강점만 조합한다.

- **오케스트레이터(Claude)**: 1M 컨텍스트, 높은 추론 품질, ultracode workflow
- **워커(codex)**: 낮은 태스크당 비용, 빠른 처리

각자의 약점은 상대가 메우므로, 높은 추론 품질과 비용 절감, 작업 속도를 함께 달성하는 것이 목표다.

```
/model-sub-codex                     # gpt-5.6-sol + xhigh
/model-sub-codex gpt-5.6-luna        # luna는 effort 기본이 max
/model-sub-codex gpt-5.6-sol high    # 모든 위임에 모델 + effort 고정
```

codex가 사용량 한도에 걸리면 세션이 리셋을 기다렸다가 막힌 작업을 자동으로 다시 실행한다.

## model-sub-claude

*Claude Code 전용.*

이후 세션 내내 Claude Code가 생성하는 모든 subagent의 기본 모델과 추론 effort를 고정한다. 모델: `fable` | `opus` | `sonnet` | `haiku`(기본 `opus`), effort: `low` | `medium` | `high` | `xhigh` | `max`(기본 `max`).

```
/model-sub-claude               # opus + max (기본값)
/model-sub-claude sonnet        # sonnet + max (effort 생략 = max)
/model-sub-claude sonnet high   # 가볍고 빠른 병렬 fan-out
```

`/model-sub-codex`와 하나의 토글 그룹을 이룬다 — 가장 최근 호출이 이긴다.

## grill-me

에이전트가 한 턴에 하나씩 압박 질문을 던져, **사용자가 하려는 바에 대한 에이전트와 사용자의 이해를 일치시킨다.** 계획이든 요구사항이든 막연한 아이디어든 대상을 가리지 않는다. 각 질문에는 추천 답이 붙어 있어 승인하거나 반박하기만 하면 되고, 코드를 보면 알 수 있는 것은 묻지 않고 직접 찾아본다.

단순하지만 강력하다 — 몇 번의 문답만으로 에이전트의 작업 방향이 사용자의 의도로 극적으로 수렴한다.

```
# 하려는 바를 먼저 말한 뒤 호출:
사용자 활동 로그를 남기고 나중에 분석할 수 있게 만들고 싶다.
/grill-me
```

## handoff

채팅 기록이 전혀 없는 새 에이전트가 작업을 이어받을 수 있도록 현재 세션의 인수인계 문서를 작성한다. 문서는 `.temp_files/` 아래 단일 Markdown 파일로 저장되어 — 채팅창에 긴 글이 쏟아지는 대신 경로만 돌려받는다 — 스킬은 자기 결과물을 새 에이전트의 눈으로 자체 비평해 빈틈을 메운 뒤 보고한다.

```
/handoff
```

→ `.temp_files/20260705_142310_handoff_auth_refactor/handoff.md` + "self-check passed".

```
/handoff 다음 세션이 바로 이어서 구현할 수 있게, 남은 작업을 체크리스트로
```

자유 서술 지시로 길이·언어·형식·초점을 조정한다. (Codex 트리거: `$handoff`.)

## 설치

- **Claude Code**: `claude/skills/` 아래 디렉터리를 프로젝트의 `.claude/skills/`로 복사한다.
- **Codex CLI**: `codex/skills/` 아래 디렉터리를 프로젝트의 `.codex/skills/`로 복사한다.

## 저장소 부가물

- 루트 `AGENTS.md` / `CLAUDE.md` — 이 스킬들이 자라난 실제 에이전트 지침 파일. 프로젝트 고유 섹션은 제거했으며 템플릿으로 쓸 수 있다.
- `utils/fetch_web/` — `AGENTS.md`의 리서치 규칙이 사용하는 Patchright 기반 폴백 페이지 페처. `patchright==1.59.1`과 Chrome이 필요하고(`pip install patchright && patchright install chrome`), 항상 headed로 동작한다 — Patchright는 headless에서 봇 탐지 회피 효과를 잃는다.

## 이식성

스킬들은 자신이 태어난 프로젝트의 몇 가지 관례를 전제한다 — 각자의 것으로 바꿔 쓰면 된다.

- `.temp_files/` — 프로젝트 루트의 스크래치 디렉터리 관례(handoff와 model-sub-codex가 사용).
- `<project-root>`와 `<GATE_MARKER>` — `model-sub-codex`와 `AGENTS.md`의 플레이스홀더로, 각각 프로젝트의 절대경로와 파일 수정 승인 문구를 뜻한다(그런 게이트를 쓰지 않는다면 해당 규칙을 빼면 된다).

## 라이선스

여기서 직접 작성한 스킬(handoff, model-sub-claude, model-sub-codex)과 그 밖의 모든 것: [Unlicense](LICENSE) — 퍼블릭 도메인. 파생 스킬(grill-me): [mattpocock/skills](https://github.com/mattpocock/skills)를 개조한 것으로 MIT 라이선스 — [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md) 참조.
