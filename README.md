# qbpowers

Agent skills for Claude Code and the OpenAI Codex CLI — a public snapshot of skills in daily use in a personal project.

**English** · [한국어](#한국어)

| Skill | Claude | Codex | What it does |
|---|:---:|:---:|---|
| [model-sub-codex](#model-sub-codex) | ✓ | — | Hand subagent work to the codex CLI, run by the main agent. |
| [model-sub-claude](#model-sub-claude) | ✓ | — | Pin the session's default subagent model + effort. |
| [grill-me](#grill-me) | ✓ | ✓ | Relentless questioning that aligns the agent's understanding with yours. |
| [handoff](#handoff) | ✓ | ✓ | Session handover document a context-blind agent can resume from. |
| [wait-what](#wait-what) | ✓ | — | Re-explain the previous answer in plainer language. |

All skills are manual-only: they run when you type the command.

## model-sub-codex

*Claude Code only. Requires an installed, authenticated `codex` CLI and a Python 3.14+ `.venv` at the project root.*

While the mode is on, work Claude would give a subagent goes to codex instead. Claude runs `codex exec` itself through the bundled scripts and reads each run's output file — no relay subagent sits in between. Model: `astra` | `sol` | `luna` (GPT-6, default `luna`); effort: `low` | `medium` | `high` | `xhigh` | `max` (default `max`).

**Design intent** — combine only the strengths of both models.

- **Orchestrator (Claude)**: 1M context, high reasoning quality
- **Worker (codex)**: low cost per task, fast turnaround

Each side covers the other's weak spot, so you get reasoning quality, cost savings, and throughput together.

- One background waiter drives a whole batch: at most 32 `codex exec` processes per machine, one resume after an unexplained failure, silent runs reported rather than killed, and a pause at the usage limit that the same command resumes after the reset.
- codex works alone: every prompt opens with fixed run rules against sub-agents and nested codex runs, and the waiter reports any run that spawns one anyway.

```
/model-sub-codex              # gpt-6-luna + max
/model-sub-codex sol          # gpt-6-sol + max
/model-sub-codex astra high   # gpt-6-astra + high
```

## model-sub-claude

*Claude Code only. Needs the `sub-effort-*` agent definitions (see [Installation](#installation)).*

Pins the default model and reasoning effort for every subagent Claude Code spawns for the rest of the session. Model: `fable` | `opus` | `sonnet` | `haiku` (default `opus`); effort: `low` | `medium` | `high` | `xhigh` | `max` (default `max`).

Subagents run as the `sub-effort-<effort>` agent type — the Agent tool has no effort parameter, so the definition carries it — and that type cannot spawn subagents of its own. With ultracode on, workflow agents use the same types.

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

## wait-what

*Claude Code only. Answers in Korean.*

For when an answer did not land. It re-pitches the previous response with a little context restored, rewritten under the clarity principles of ASD-STE100 Simplified Technical English — one idea per sentence, short sentences, active voice, the same word for the same thing.

```
/wait-what
```

ASD-STE100 is a controlled English written for aircraft maintenance manuals. Only its clarity principles are borrowed, not its approved word list; the reply itself is Korean. Edit the skill's one line if you want another language.

## Installation

- **Claude Code**: copy a directory under `claude/skills/` into your project's `.claude/skills/`. For `model-sub-claude`, also copy `claude/agents/sub-effort-*.md` into `.claude/agents/` (restart Claude Code if that directory is new).
- **Codex CLI**: copy a directory under `codex/skills/` into your project's `.codex/skills/`.

## Repo extras

- Root `AGENTS.md` / `CLAUDE.md` — the live agent instruction files these skills grew out of; project-specific sections removed, usable as a template.
- `utils/fetch_web/` — Patchright-based fallback page fetcher used by the research rules in `AGENTS.md`. Requires `patchright==1.59.1` and Chrome (`pip install patchright==1.59.1 && patchright install chrome`); always runs headed — Patchright loses its bot-detection evasion headless.

## Portability

The skills assume a few conventions from their home project — substitute your own:

- `.temp_files/` — a scratch-directory convention at the project root (used by handoff and model-sub-codex).
- `<GATE_MARKER>` — placeholder in `model-sub-codex` and `AGENTS.md` for your file-modification approval phrase (drop that rule if you don't use such a gate).

## License

Original skills (handoff, model-sub-claude, model-sub-codex, wait-what) and everything else authored here: [Unlicense](LICENSE) — public domain. Derived skill (grill-me): modified from [mattpocock/skills](https://github.com/mattpocock/skills), MIT licensed — see [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

---

# 한국어

Claude Code와 OpenAI Codex CLI를 위한 에이전트 스킬 모음 — 개인 프로젝트에서 매일 쓰는 스킬의 공개 스냅샷.

| 스킬 | Claude | Codex | 하는 일 |
|---|:---:|:---:|---|
| `model-sub-codex` | ✓ | — | subagent 작업을 codex CLI로 넘기고, 메인 에이전트가 직접 실행한다. |
| `model-sub-claude` | ✓ | — | 세션의 기본 subagent 모델 + effort를 고정한다. |
| `grill-me` | ✓ | ✓ | 압박 질문을 반복해 에이전트와 사용자의 이해를 일치시킨다. |
| `handoff` | ✓ | ✓ | 맥락 없는 에이전트도 이어받을 수 있는 인수인계 문서를 만든다. |
| `wait-what` | ✓ | — | 직전 답변을 더 쉬운 말로 다시 설명한다. |

모든 스킬은 수동 전용이다 — 명령을 입력했을 때만 실행된다.

## model-sub-codex

*Claude Code 전용. 설치·인증된 `codex` CLI와 프로젝트 루트의 Python 3.14+ `.venv` 필요.*

모드가 켜져 있는 동안 Claude가 subagent에게 줄 일은 codex로 간다. Claude가 번들 스크립트로 `codex exec`를 직접 실행하고 실행마다 출력 파일을 읽는다 — 중간에 릴레이 subagent가 없다. 모델: `astra` | `sol` | `luna`(GPT-6, 기본 `luna`), effort: `low` | `medium` | `high` | `xhigh` | `max`(기본 `max`).

**설계 의도** — 두 모델의 강점만 조합한다.

- **오케스트레이터(Claude)**: 1M 컨텍스트, 높은 추론 품질
- **워커(codex)**: 낮은 태스크당 비용, 빠른 처리

각자의 약점은 상대가 메우므로, 높은 추론 품질과 비용 절감, 작업 속도를 함께 달성하는 것이 목표다.

- 백그라운드 대기 스크립트 하나가 배치 전체를 몬다: 기계당 `codex exec` 최대 32개, 원인 불명 실패 뒤 한 번 재개, 조용해진 실행은 죽이지 않고 보고, 사용량 한도에서는 배치를 멈추고 리셋 뒤 같은 명령으로 이어 간다.
- codex는 혼자 일한다: 모든 프롬프트 앞에 서브에이전트와 하위 codex 실행을 금지하는 고정 규칙이 붙고, 그래도 띄운 실행은 대기 스크립트가 보고한다.

```
/model-sub-codex              # gpt-6-luna + max
/model-sub-codex sol          # gpt-6-sol + max
/model-sub-codex astra high   # gpt-6-astra + high
```

## model-sub-claude

*Claude Code 전용. `sub-effort-*` 에이전트 정의가 필요하다(설치 참조).*

이후 세션 내내 Claude Code가 생성하는 모든 subagent의 기본 모델과 추론 effort를 고정한다. 모델: `fable` | `opus` | `sonnet` | `haiku`(기본 `opus`), effort: `low` | `medium` | `high` | `xhigh` | `max`(기본 `max`).

subagent는 `sub-effort-<effort>` 에이전트 종류로 돈다 — Agent 도구에는 effort 파라미터가 없어서 정의 파일이 effort를 담는다 — 그리고 이 종류는 자기 subagent를 띄울 수 없다. ultracode가 켜져 있으면 workflow 에이전트도 같은 종류를 쓴다.

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

## wait-what

*Claude Code 전용. 한국어로 답한다.*

답변이 와닿지 않았을 때 쓴다. 맥락을 조금 되살려 직전 답변을 다시 설명하되, ASD-STE100 Simplified Technical English의 명료성 원칙 — 한 문장에 한 가지, 짧은 문장, 능동태, 같은 뜻에는 같은 낱말 — 을 적용해 다시 쓴다.

```
/wait-what
```

ASD-STE100은 항공기 정비 설명서를 위해 만든 통제 영어다. 승인 어휘 목록이 아니라 명료성 원칙만 빌려 왔고, 답변 자체는 한국어다. 다른 언어를 원하면 스킬의 한 줄을 고치면 된다.

## 설치

- **Claude Code**: `claude/skills/` 아래 디렉터리를 프로젝트의 `.claude/skills/`로 복사한다. `model-sub-claude`를 쓰려면 `claude/agents/sub-effort-*.md`도 `.claude/agents/`로 복사한다(그 디렉터리를 새로 만들었다면 Claude Code를 재시작한다).
- **Codex CLI**: `codex/skills/` 아래 디렉터리를 프로젝트의 `.codex/skills/`로 복사한다.

## 저장소 부가물

- 루트 `AGENTS.md` / `CLAUDE.md` — 이 스킬들이 자라난 실제 에이전트 지침 파일. 프로젝트 고유 섹션은 제거했으며 템플릿으로 쓸 수 있다.
- `utils/fetch_web/` — `AGENTS.md`의 리서치 규칙이 사용하는 Patchright 기반 폴백 페이지 페처. `patchright==1.59.1`과 Chrome이 필요하고(`pip install patchright==1.59.1 && patchright install chrome`), 항상 headed로 동작한다 — Patchright는 headless에서 봇 탐지 회피 효과를 잃는다.

## 이식성

스킬들은 자신이 태어난 프로젝트의 몇 가지 관례를 전제한다 — 각자의 것으로 바꿔 쓰면 된다.

- `.temp_files/` — 프로젝트 루트의 스크래치 디렉터리 관례(handoff와 model-sub-codex가 사용).
- `<GATE_MARKER>` — `model-sub-codex`와 `AGENTS.md`의 플레이스홀더로, 파일 수정 승인 문구를 뜻한다(그런 게이트를 쓰지 않는다면 해당 규칙을 빼면 된다).

## 라이선스

여기서 직접 작성한 스킬(handoff, model-sub-claude, model-sub-codex, wait-what)과 그 밖의 모든 것: [Unlicense](LICENSE) — 퍼블릭 도메인. 파생 스킬(grill-me): [mattpocock/skills](https://github.com/mattpocock/skills)를 개조한 것으로 MIT 라이선스 — [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md) 참조.
