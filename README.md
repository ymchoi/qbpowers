# qbpowers

These are Claude Code skills and agent files I use every day in a private project. If you use Claude Code, you can copy any of them into your own project.

English · [한국어](#한국어)

## What's here

| Skill | What it does |
|---|---|
| [grill-me](#grill-me) | Asks you one question at a time until it understands what you want to do. |
| [wait-what](#wait-what) | Explains the previous answer again, more plainly, in Korean. |
| [worker](#worker) | Chooses who does the work Claude delegates: Claude subagents, GPT models through codex, a mix of the two, or no one. |

The skills are in `claude/skills/`. The repo also has these files:

- `claude/agents/worker-effort-*.md`: the agent files worker needs for its Claude workers.
- `claude/agents/general-purpose.md`: an optional replacement for Claude Code's built-in general-purpose agent.
- `AGENTS.md` and `CLAUDE.md`: my own project rules, shared as a reference.

## Quick start

Both grill-me and wait-what need only a copy. Clone the repo and copy the skill into your project's `.claude/skills/`:

```sh
git clone https://github.com/ymchoi/qbpowers.git
cd qbpowers
mkdir -p /path/to/project/.claude/skills
cp -R claude/skills/grill-me /path/to/project/.claude/skills/
```

If Claude Code was running when you created `.claude/skills/`, restart it. Then type `/grill-me` followed by what you want to do. Each skill runs only when you type its command.

The worker skill needs more. Its [Setup](#setup) is at the end of the worker section.

## grill-me

Type `/grill-me` followed by what you want to do. Claude then interviews you, one question at a time, until it understands the task the way you do. Each question comes with a recommended answer and a short reason. Claude looks things up in the code and on the web itself and asks you only what it can't find out.

```
/grill-me I want to log what users do in the app so I can analyze it later.
```

## wait-what

Use `/wait-what` when an answer didn't land. Claude explains its previous answer again in Korean, in plainer words and with a little more context. For another language, edit the one-line body and the `description` in its `SKILL.md`.

```
/wait-what
```

## worker

Until the session ends, `/worker` sets who does the work Claude delegates. Depending on your subscription plan, I recommend running the main agent, which does the delegating, on Opus 5.5 max, or on Fable 5.2 max or xhigh. It mostly orchestrates, so it does not use many tokens. The latest `/worker` wins. Claude workers are Opus subagents. GPT workers are `gpt-6-astra` and `gpt-6.1-sol`, run through the codex CLI.

```
/worker              # same as /worker hybrid
/worker claude-light
/worker claude
/worker hybrid
/worker codex-light
/worker codex
/worker none
```

Add `fast` or `ultrafast` after `hybrid`, `codex-light` or `codex`, as in `/worker hybrid fast`, to put the GPT workers on service tier `priority` or `ultrafast`. Without it, and always under `claude-light` and `claude`, they run at standard speed.

Each form picks a column of the table below. `claude-light` and `claude` use Claude workers, `codex-light` and `codex` use GPT workers, and `hybrid` mixes the two. The `-light` columns use lower efforts or models. Computer Use runs through codex in every column. `none` starts no workers, so Claude does all the work itself.

| Work | claude-light | claude | hybrid | codex-light | codex |
|---|---|---|---|---|---|
| Hard problems | opus xhigh | opus max | opus max | astra max | astra max |
| Writing code, tests or documents | opus high | opus xhigh | astra max | sol max | astra max |
| Deep review | opus high | opus xhigh | opus xhigh | sol max | astra max |
| Web search and research | opus medium | opus high | sol max | sol max | sol max |
| General work | opus medium | opus high | sol max | sol max | sol max |
| Simple work | opus medium | opus medium | sol max | sol max | sol max |
| Computer Use | sol max | sol max | sol max | sol max | sol max |

Each cell gives the model, then the effort. `opus` is a Claude subagent; `astra` (`gpt-6-astra`) and `sol` (`gpt-6.1-sol`) run through codex. [SKILL.md](claude/skills/worker/SKILL.md) spells out what each row covers.

Claude runs workers in parallel when it can. If a worker fails, Claude reports it instead of quietly doing the work some other way.

### Setup

From your qbpowers clone, copy worker and its agents into the project, then create the venv:

```sh
mkdir -p /path/to/project/.claude/skills /path/to/project/.claude/agents
cp -R claude/skills/worker /path/to/project/.claude/skills/
cp claude/agents/worker-effort-*.md /path/to/project/.claude/agents/
cd /path/to/project && python3.14 -m venv .venv  # skip if the project already has a Python 3.14 .venv
```

- The codex CLI must be on your PATH, logged in and allowed to write files. `codex exec` is read-only by default, so put `sandbox_mode = "workspace-write"` in `~/.codex/config.toml`. It also refuses to run outside a git repository.
- For Computer Use, set up Computer Use in codex. It doesn't work on Windows.
- Keep worker in the project's `.claude/skills/`, not in `~/.claude/skills/`, and don't symlink it.
- The scripts put codex work dirs in `.temp_files/subcodex/` at the project root. Add `.temp_files/` to your `.gitignore`.

If Claude Code was running when you created `.claude/skills/` or `.claude/agents/`, restart it.

## Other files

### general-purpose.md (optional)

`claude/agents/general-purpose.md` has nothing to do with worker. Copy it into a project's `.claude/agents/` and it replaces Claude Code's built-in general-purpose agent in that project. Subagents started as general-purpose or without a type then run on Opus, whatever model the main session uses. They can't start subagents of their own, and they get this file's short prompt instead of the built-in one. Copy it only if you want that.

### AGENTS.md and CLAUDE.md

These are my own project rules. AGENTS.md tells agents to put scratch files in `.temp_files/`, the same directory worker uses. When a project has both files, Claude Code reads only CLAUDE.md by default. To have it read both, run `/config` and set "Project instructions" to `claude-md-and-agents-md`.

## License

Everything here except grill-me is in the public domain under the [Unlicense](LICENSE). The exception, grill-me, is adapted from [mattpocock/skills](https://github.com/mattpocock/skills) and stays under that project's MIT license, as noted in [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

---

# 한국어

개인 프로젝트에서 매일 쓰는 Claude Code 스킬과 에이전트 파일을 공개한 저장소다. Claude Code를 쓴다면 필요한 것만 골라 자기 프로젝트에 복사해 쓸 수 있다.

## 저장소 구성

| 스킬 | 하는 일 |
|---|---|
| `grill-me` | 하려는 일을 Claude가 제대로 이해할 때까지 사용자에게 한 번에 하나씩 질문한다. |
| `wait-what` | 직전 답변을 더 쉬운 한국어로 다시 설명한다. |
| `worker` | Claude가 넘기는 일을 누가 맡을지 정한다. Claude subagent나 codex로 돌리는 GPT 모델에게 맡기거나, 둘을 섞거나, 아무에게도 맡기지 않는다. |

스킬은 `claude/skills/`에 있다. 그 밖에 이런 파일이 있다.

- `claude/agents/worker-effort-*.md`: worker가 Claude 워커를 띄울 때 쓰는 에이전트.
- `claude/agents/general-purpose.md`: Claude Code에 내장된 general-purpose 에이전트를 대신하는 파일. 쓸지 말지는 선택이다.
- `AGENTS.md`, `CLAUDE.md`: 개인 프로젝트에서 쓰는 규칙. 참고용으로 올려 두었다.

## 빠른 시작

grill-me와 wait-what은 복사만 하면 된다. 저장소를 클론하고 스킬을 프로젝트의 `.claude/skills/`로 복사한다.

```sh
git clone https://github.com/ymchoi/qbpowers.git
cd qbpowers
mkdir -p /path/to/project/.claude/skills
cp -R claude/skills/grill-me /path/to/project/.claude/skills/
```

`.claude/skills/`를 Claude Code 실행 중에 새로 만들었다면 Claude Code를 다시 시작한다. 그다음 `/grill-me` 뒤에 하려는 일을 적어 입력한다. 스킬은 모두 명령을 직접 입력할 때만 실행된다.

worker는 준비할 것이 더 있다. 아래 worker 설명 끝의 [준비](#준비)에 정리해 두었다.

## grill-me

`/grill-me` 뒤에 하려는 일을 적는다. 그러면 Claude가 그 일을 사용자와 똑같이 이해할 때까지 사용자에게 한 번에 하나씩 질문한다. 질문마다 추천 답과 짧은 이유를 붙인다. 코드나 웹에서 알 수 있는 것은 Claude가 직접 찾아보고, 찾을 수 없는 것만 사용자에게 묻는다.

```
/grill-me 사용자 활동 로그를 남기고 나중에 분석하고 싶다.
```

## wait-what

답변이 잘 와닿지 않을 때 `/wait-what`을 입력한다. Claude가 맥락을 조금 더 붙여 직전 답변을 더 쉬운 한국어로 다시 설명한다. 다른 언어로 받으려면 `SKILL.md`의 한 줄짜리 본문과 `description`을 고친다.

```
/wait-what
```

## worker

`/worker`는 세션이 끝날 때까지 Claude가 넘기는 일을 누가 맡을지 정한다. 일을 넘기는 메인 에이전트는 구독 요금제에 맞춰 Opus 5.5 max, 또는 Fable 5.2 max나 xhigh로 두기를 권한다. 메인 에이전트는 주로 오케스트레이션을 맡아 토큰을 많이 쓰지 않는다. 마지막으로 입력한 `/worker`가 적용된다. Claude 워커는 Opus subagent이고, GPT 워커는 codex CLI로 돌리는 `gpt-6-astra`와 `gpt-6.1-sol`이다.

```
/worker              # /worker hybrid와 같다
/worker claude-light
/worker claude
/worker hybrid
/worker codex-light
/worker codex
/worker none
```

`hybrid`, `codex-light`, `codex` 뒤에 `fast`나 `ultrafast`를 붙이면 GPT 워커가 서비스 티어 `priority`나 `ultrafast`로 돈다. 예를 들면 `/worker hybrid fast`다. 붙이지 않았을 때와 `claude-light`, `claude`에서는 표준 속도로 돈다.

명령마다 아래 표의 열 하나를 고른다. `claude-light`와 `claude`는 Claude 워커를, `codex-light`와 `codex`는 GPT 워커를 쓰고, `hybrid`는 둘을 섞는다. `-light` 쪽은 effort나 모델을 낮춰 쓴다. Computer Use는 어느 열에서든 codex로 돈다. `none`은 워커를 띄우지 않으므로 Claude가 모든 일을 직접 한다.

| 일 | claude-light | claude | hybrid | codex-light | codex |
|---|---|---|---|---|---|
| 어려운 문제 | opus xhigh | opus max | opus max | astra max | astra max |
| 코드, 테스트, 문서 작성 | opus high | opus xhigh | astra max | sol max | astra max |
| 깊은 리뷰 | opus high | opus xhigh | opus xhigh | sol max | astra max |
| 웹 검색과 조사 | opus medium | opus high | sol max | sol max | sol max |
| 일반 작업 | opus medium | opus high | sol max | sol max | sol max |
| 단순 작업 | opus medium | opus medium | sol max | sol max | sol max |
| Computer Use | sol max | sol max | sol max | sol max | sol max |

칸마다 앞은 모델, 뒤는 effort다. `opus`는 Claude subagent이고, `astra`(`gpt-6-astra`)와 `sol`(`gpt-6.1-sol`)은 codex로 돈다. 행마다 어떤 일이 들어가는지는 [SKILL.md](claude/skills/worker/SKILL.md)에 자세히 있다.

Claude는 할 수 있으면 워커 여러 개를 동시에 돌린다. 워커가 실패하면 슬쩍 다른 방법으로 대신하지 않고 실패했다고 알린다.

### 준비

qbpowers 클론에서 아래 명령으로 worker와 에이전트 파일을 프로젝트에 복사하고 venv를 만든다.

```sh
mkdir -p /path/to/project/.claude/skills /path/to/project/.claude/agents
cp -R claude/skills/worker /path/to/project/.claude/skills/
cp claude/agents/worker-effort-*.md /path/to/project/.claude/agents/
cd /path/to/project && python3.14 -m venv .venv  # 프로젝트에 Python 3.14 .venv가 이미 있으면 건너뛴다
```

- codex CLI는 PATH에 잡혀 있고 로그인한 상태여야 하며, 파일을 쓸 수 있어야 한다. `codex exec`는 기본값이 읽기 전용이므로 `~/.codex/config.toml`에 `sandbox_mode = "workspace-write"`를 넣는다. git 저장소 밖에서는 실행되지 않는다.
- Computer Use를 쓰려면 codex에 Computer Use를 설정해 둔다. Windows에서는 쓸 수 없다.
- worker는 `~/.claude/skills/`가 아니라 프로젝트의 `.claude/skills/`에 두고, 심볼릭 링크로 연결하지 않는다.
- 스크립트는 codex 작업 디렉터리를 프로젝트 루트의 `.temp_files/subcodex/`에 만든다. `.temp_files/`는 `.gitignore`에 넣는다.

`.claude/skills/`나 `.claude/agents/`를 Claude Code 실행 중에 새로 만들었다면 다시 시작한다.

## 그 밖의 파일

### general-purpose.md (선택)

`claude/agents/general-purpose.md`는 worker와 관계없다. 프로젝트의 `.claude/agents/`에 복사하면 그 프로젝트에서는 Claude Code에 내장된 general-purpose 에이전트 대신 이 파일이 쓰인다. 그러면 general-purpose로 띄우거나 종류 없이 띄운 subagent는 메인 세션이 어떤 모델이든 Opus로 돈다. 자기 subagent는 띄우지 못하고, 내장 프롬프트 대신 이 파일의 짧은 프롬프트를 받는다. 이렇게 되기를 원할 때만 복사한다.

### AGENTS.md와 CLAUDE.md

개인 프로젝트에서 쓰는 규칙이다. AGENTS.md는 임시 파일을 worker와 같은 `.temp_files/`에 두게 한다. 프로젝트에 두 파일이 함께 있으면 Claude Code는 기본적으로 CLAUDE.md만 읽는다. 둘 다 읽게 하려면 `/config`에서 "Project instructions"를 `claude-md-and-agents-md`로 바꾼다.

## 라이선스

`grill-me`를 뺀 나머지는 모두 [Unlicense](LICENSE)에 따라 퍼블릭 도메인으로 공개한다. `grill-me`는 [mattpocock/skills](https://github.com/mattpocock/skills)의 스킬을 고친 것이라 원래의 MIT 라이선스를 따르며, 고지는 [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md)에 있다.
