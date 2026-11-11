# qbpowers

Three Claude Code skills I use every day, with the agent files they need. Copy the ones you want into your own project.

English · [한국어](#한국어)

| Skill | What it does |
|---|---|
| [grill-me](#grill-me) | Claude interviews you, one question at a time, until it understands what you want. |
| [wait-what](#wait-what) | Claude explains its previous answer again in plainer words, in Korean. |
| [worker](#worker) | Claude hands its work to workers: Opus subagents, GPT models run through the codex CLI, or both. A table sets the model and effort for each kind of task. |

A skill runs only when you type its command.

```
claude/skills/         the three skills
claude/agents/         worker-effort-*.md (worker needs them), general-purpose.md (optional)
AGENTS.md, CLAUDE.md   my own project rules, here as a reference
```

## Install

```sh
git clone https://github.com/ymchoi/qbpowers.git
cd qbpowers
mkdir -p /path/to/project/.claude/skills
cp -R claude/skills/grill-me claude/skills/wait-what /path/to/project/.claude/skills/
```

That is all grill-me and wait-what need. They also work from `~/.claude/skills/`, where every project can use them. worker takes a few more steps, listed under its [Setup](#setup).

If Claude Code was running when you created `.claude/skills/`, restart it.

## grill-me

Type `/grill-me` and what you want to do. Claude asks one question at a time until it understands the task the way you do. Each question comes with a recommended answer and a short reason. Claude looks things up in the code and on the web first, and asks you only what it cannot find out: your preferences, priorities and constraints.

```
/grill-me I want to log what users do in the app so I can analyze it later.
```

It helps most before a task you have only half thought through.

## wait-what

Type `/wait-what` when an answer did not land. Claude explains its previous answer again, with a little more context and in plainer words.

```
/wait-what
```

The explanation comes in Korean. For another language, change "Korean" in the body and the `description` of its `SKILL.md`.

## worker

After `/worker`, Claude delegates its work for the rest of the session. It keeps talking with you and coordinating, and the tasks themselves go to workers:

- **Claude workers** are Opus subagents.
- **GPT workers** are `gpt-6-astra` and `gpt-6.1-sol`, run through the codex CLI. This puts your Codex usage to work from inside Claude Code.

`/worker` picks one column of the table below. From then on, each time Claude delegates a task, it judges what kind of task it is and uses the row that fits.

```
/worker              # same as /worker hybrid
/worker claude-light
/worker claude
/worker hybrid-light
/worker hybrid
/worker codex-light
/worker codex
/worker none
```

| Task | claude-light | claude | hybrid-light | hybrid | codex-light | codex |
|---|---|---|---|---|---|---|
| **Hard**: a bug of unknown cause, a design decision, a change across several modules or one that is hard to undo | opus xhigh | opus max | opus xhigh | opus max | astra max | astra max |
| **Writing** code, tests or documents | opus high | opus xhigh | sol max | astra max | sol max | astra max |
| **Deep review** of an important change | opus high | opus xhigh | opus high | opus xhigh | sol max | astra max |
| **Research**: web search, external documents, open source | opus medium | opus high | sol max | sol max | sol max | sol max |
| **General**: work with a set scope, such as reproducing a bug, simple diagnosis or routine checks | opus medium | opus high | sol max | sol max | sol max | sol max |
| **Simple**: finding and reading, running tests, a spelled-out edit, mechanical repetition | opus medium | opus medium | sol max | sol max | sol max | sol max |
| **Computer Use**, one at a time | sol max | sol max | sol max | sol max | sol max | sol max |

Each cell is a model and an effort. `opus` is an Opus subagent. `astra` is `gpt-6-astra` and `sol` is `gpt-6.1-sol`, both run through codex.

### Choosing a column

- `hybrid`, the default, uses both: Opus for hard problems and deep reviews, astra for writing, sol for the rest.
- `claude` uses only Claude workers, and `codex` only GPT workers.
- `claude-light`, `hybrid-light` and `codex-light` are the cheaper versions. `claude-light` lowers the efforts. `hybrid-light` lowers the Opus efforts and uses sol in place of astra for writing. `codex-light` uses sol in place of astra for writing and review.
- `none` starts no workers, so Claude does everything itself. Workers already running still finish.
- Computer Use goes through codex in every column.

Add `fast` or `ultrafast` after `hybrid-light`, `hybrid`, `codex-light` or `codex`, as in `/worker hybrid fast`, to run the GPT workers on codex's `priority` or `ultrafast` service tier. Without it they run at standard speed.

The choice lasts until the session ends, and the latest `/worker` wins.

### What to expect

- Claude runs workers in parallel when the tasks can safely run side by side.
- A worker that cannot go on without a decision asks Claude, gets the answer and continues where it stopped.
- If a worker fails, Claude tells you. It does not quietly give the work to another worker or do it itself.
- GPT workers run as background `codex exec` processes. Each run keeps its prompt, logs and final message in a folder under `.temp_files/subcodex/`, so you can see exactly what it was asked and what it answered.
- If you reach your codex usage limit, the remaining runs stay queued and can be continued after the limit resets.

### The main agent's model

The main agent, the Claude you talk to, mostly orchestrates, so it uses far fewer tokens than the workers. That makes a strong setting affordable: I recommend Opus 5.5 at max, or Fable 5.2 at max or xhigh, depending on your plan.

### Setup

You need:

- Python 3.14. The scripts use 3.14 syntax and nothing outside the standard library.
- For GPT workers, the codex CLI on your PATH and logged in. `claude` and `claude-light` work without it, apart from Computer Use.
- A git repository. `codex exec` refuses to run outside one.

From your qbpowers clone, copy worker and its agent files into the project, then create the venv:

```sh
mkdir -p /path/to/project/.claude/skills /path/to/project/.claude/agents
cp -R claude/skills/worker /path/to/project/.claude/skills/
cp claude/agents/worker-effort-*.md /path/to/project/.claude/agents/
cd /path/to/project && python3.14 -m venv .venv  # skip if the project already has a Python 3.14 .venv
```

The `worker-effort-*.md` files pin each Claude worker's effort and keep workers from starting subagents of their own.

Then:

- Let codex write files. `codex exec` is read-only by default, so put `sandbox_mode = "workspace-write"` in `~/.codex/config.toml`.
- Add `.temp_files/` to the project's `.gitignore`. The scripts keep the codex work folders in `.temp_files/subcodex/`.
- Keep worker in the project's `.claude/skills/`, as a real copy. The scripts find the project root from their own location, so `~/.claude/skills/` or a symlink does not work.
- For Computer Use, set it up in codex first. It is not available on Windows.
- Restart Claude Code if it was running when you created `.claude/skills/` or `.claude/agents/`.

### Changing the table

The table is in [SKILL.md](claude/skills/worker/SKILL.md), which also spells out what each row covers. Edit its cells to route differently. You can also paste a table of your own into the chat: it replaces this one until the next `/worker`. The model names behind `astra` and `sol` are at the top of `scripts/wait_codex.py` in the skill folder.

## Other files

### general-purpose.md (optional)

worker does not need `claude/agents/general-purpose.md`. Copy it into a project's `.claude/agents/` and it replaces Claude Code's built-in general-purpose agent in that project. Subagents started as general-purpose, or with no type, then run on Opus whatever model the main session uses. They cannot start subagents of their own, and they get this file's short prompt instead of the built-in one.

### AGENTS.md and CLAUDE.md

These are the rules I give agents in my own projects. Nothing in this repo needs them. Two of them touch worker:

- AGENTS.md puts scratch files in `.temp_files/`, the directory worker uses.
- CLAUDE.md tells Claude not to name its subagents. In my setup a named subagent ignored the effort it was given and returned its result cut at 4,000 characters.

When a project has both files, Claude Code reads only CLAUDE.md by default. To have it read both, run `/config` and set "Project instructions" to `claude-md-and-agents-md`.

## License

Everything here except grill-me is in the public domain under the [Unlicense](LICENSE). grill-me is adapted from [mattpocock/skills](https://github.com/mattpocock/skills) and stays under that project's MIT license, as noted in [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

---

# 한국어

매일 쓰는 Claude Code 스킬 세 개와, 스킬이 쓰는 에이전트 파일을 모아 둔 저장소다. 필요한 것만 골라 자기 프로젝트에 복사해 쓰면 된다.

| 스킬 | 하는 일 |
|---|---|
| `grill-me` | 하려는 일을 Claude가 제대로 이해할 때까지 한 번에 하나씩 질문한다. |
| `wait-what` | 직전 답변을 더 쉬운 말로 다시 설명한다. 답은 한국어로 온다. |
| `worker` | Claude가 일을 워커에게 넘긴다. 워커는 Opus 서브에이전트이거나 codex CLI로 돌리는 GPT 모델이고, 둘을 섞어 쓸 수도 있다. 어떤 일에 어떤 모델과 effort를 쓸지는 표로 정해져 있다. |

스킬은 명령을 직접 입력할 때만 실행된다.

```
claude/skills/         스킬 세 개
claude/agents/         worker-effort-*.md (worker에 필요), general-purpose.md (선택)
AGENTS.md, CLAUDE.md   개인 프로젝트에서 쓰는 규칙. 참고용이다
```

## 설치

```sh
git clone https://github.com/ymchoi/qbpowers.git
cd qbpowers
mkdir -p /path/to/project/.claude/skills
cp -R claude/skills/grill-me claude/skills/wait-what /path/to/project/.claude/skills/
```

grill-me와 wait-what은 이것으로 끝이다. `~/.claude/skills/`에 두면 모든 프로젝트에서 쓸 수 있다. worker는 몇 가지가 더 필요하고, worker 설명의 [준비](#준비)에 적어 두었다.

`.claude/skills/`를 Claude Code가 떠 있는 동안 새로 만들었다면 Claude Code를 다시 시작한다.

## grill-me

`/grill-me` 뒤에 하려는 일을 적는다. Claude가 그 일을 사용자와 똑같이 이해할 때까지 한 번에 하나씩 질문한다. 질문마다 추천 답과 짧은 이유가 붙는다. 코드나 웹에서 알 수 있는 것은 Claude가 먼저 찾아보고, 찾아서는 알 수 없는 것만 묻는다. 사용자의 취향, 우선순위, 제약 같은 것이다.

```
/grill-me 사용자 활동 로그를 남기고 나중에 분석하고 싶다.
```

아직 생각이 덜 정리된 일을 시작하기 전에 쓰면 좋다.

## wait-what

답변이 잘 와닿지 않을 때 `/wait-what`을 입력한다. Claude가 맥락을 조금 더 붙여서 직전 답변을 더 쉬운 말로 다시 설명한다.

```
/wait-what
```

설명은 한국어로 온다. 다른 언어로 받으려면 `SKILL.md`의 본문과 `description`에 있는 "Korean"을 바꾼다.

## worker

`/worker`를 입력하면 Claude는 세션이 끝날 때까지 일을 워커에게 넘긴다. Claude는 사용자와 대화하면서 일을 조율하고, 실제 작업은 워커가 한다.

- **Claude 워커**는 Opus 서브에이전트다.
- **GPT 워커**는 codex CLI로 돌리는 `gpt-6-astra`와 `gpt-6.1-sol`이다. Claude Code 안에서 Codex 사용량까지 일에 쓸 수 있게 된다.

`/worker`로 아래 표의 열 하나를 정한다. 그 뒤로 Claude는 일을 넘길 때마다 그 일의 성격을 보고 그 열에서 맞는 행을 알아서 고른다.

```
/worker              # /worker hybrid와 같다
/worker claude-light
/worker claude
/worker hybrid-light
/worker hybrid
/worker codex-light
/worker codex
/worker none
```

| 일 | claude-light | claude | hybrid-light | hybrid | codex-light | codex |
|---|---|---|---|---|---|---|
| **어려운 일**: 원인을 모르는 버그, 설계 결정, 여러 모듈에 걸친 변경, 되돌리기 어려운 변경 | opus xhigh | opus max | opus xhigh | opus max | astra max | astra max |
| 코드·테스트·문서 **작성** | opus high | opus xhigh | sol max | astra max | sol max | astra max |
| 중요한 변경의 **깊은 리뷰** | opus high | opus xhigh | opus high | opus xhigh | sol max | astra max |
| **조사**: 웹 검색, 외부 문서, 오픈소스 | opus medium | opus high | sol max | sol max | sol max | sol max |
| **일반 작업**: 범위가 정해진 일. 버그 재현, 간단한 진단, 일상적인 점검 | opus medium | opus high | sol max | sol max | sol max | sol max |
| **단순 작업**: 찾기와 읽기, 테스트 실행, 내용이 정해진 수정, 기계적인 반복 | opus medium | opus medium | sol max | sol max | sol max | sol max |
| **Computer Use**, 한 번에 하나만 | sol max | sol max | sol max | sol max | sol max | sol max |

칸마다 앞은 모델, 뒤는 effort다. `opus`는 Opus 서브에이전트다. `astra`는 `gpt-6-astra`, `sol`은 `gpt-6.1-sol`이고 둘 다 codex로 돈다.

### 열 고르기

- `hybrid`는 기본값이고 둘을 섞는다. 어려운 일과 깊은 리뷰는 Opus가, 작성은 astra가, 나머지는 sol이 맡는다.
- `claude`는 Claude 워커만, `codex`는 GPT 워커만 쓴다.
- `claude-light`, `hybrid-light`, `codex-light`는 더 싸게 도는 쪽이다. `claude-light`는 effort를 낮춘다. `hybrid-light`는 Opus의 effort를 낮추고 작성을 astra 대신 sol에게 맡긴다. `codex-light`는 작성과 리뷰를 astra 대신 sol에게 맡긴다.
- `none`은 워커를 띄우지 않는다. Claude가 모든 일을 직접 한다. 이미 돌고 있던 워커는 끝까지 돈다.
- Computer Use는 어느 열에서든 codex로 돈다.

`hybrid-light`, `hybrid`, `codex-light`, `codex` 뒤에 `fast`나 `ultrafast`를 붙이면 GPT 워커가 codex의 서비스 티어 `priority`나 `ultrafast`로 돈다. 예를 들면 `/worker hybrid fast`다. 붙이지 않으면 표준 속도로 돈다.

정한 것은 세션이 끝날 때까지 이어지고, 마지막으로 입력한 `/worker`가 적용된다.

### 어떻게 동작하나

- 나란히 돌려도 문제없는 일은 Claude가 워커 여러 개로 동시에 돌린다.
- 워커가 결정 없이는 더 나아갈 수 없으면 Claude에게 묻고, 답을 받아 멈춘 곳에서 이어 간다.
- 워커가 실패하면 Claude가 실패했다고 알린다. 슬쩍 다른 워커에게 넘기거나 직접 해 버리지 않는다.
- GPT 워커는 백그라운드의 `codex exec` 프로세스로 돈다. 실행마다 `.temp_files/subcodex/` 아래에 폴더가 생기고 프롬프트, 로그, 마지막 메시지가 남는다. 무엇을 시켰고 무엇을 답했는지 그대로 볼 수 있다.
- codex 사용량 한도에 걸리면 남은 실행은 대기 상태로 남고, 한도가 풀린 뒤에 이어서 돌릴 수 있다.

### 메인 에이전트의 모델

메인 에이전트(사용자와 대화하는 Claude)는 주로 오케스트레이션을 하므로 워커보다 토큰을 훨씬 적게 쓴다. 그래서 모델과 effort를 높게 두어도 부담이 작다. 요금제에 맞춰 Opus 5.5 max, 또는 Fable 5.2 max나 xhigh로 두기를 권한다.

### 준비

필요한 것:

- Python 3.14. 스크립트가 3.14 문법을 쓴다. 표준 라이브러리 말고는 쓰지 않는다.
- GPT 워커를 쓰려면 codex CLI가 PATH에 있고 로그인돼 있어야 한다. `claude`와 `claude-light`는 Computer Use만 빼면 codex 없이도 된다.
- git 저장소. `codex exec`는 git 저장소 밖에서는 실행되지 않는다.

qbpowers 클론에서 worker와 에이전트 파일을 프로젝트에 복사하고 venv를 만든다.

```sh
mkdir -p /path/to/project/.claude/skills /path/to/project/.claude/agents
cp -R claude/skills/worker /path/to/project/.claude/skills/
cp claude/agents/worker-effort-*.md /path/to/project/.claude/agents/
cd /path/to/project && python3.14 -m venv .venv  # 프로젝트에 Python 3.14 .venv가 이미 있으면 건너뛴다
```

`worker-effort-*.md`는 Claude 워커의 effort를 고정하고, 워커가 자기 서브에이전트를 또 띄우지 못하게 한다.

그다음 할 일:

- codex가 파일을 쓸 수 있게 한다. `codex exec`는 기본값이 읽기 전용이므로 `~/.codex/config.toml`에 `sandbox_mode = "workspace-write"`를 넣는다.
- 프로젝트의 `.gitignore`에 `.temp_files/`를 넣는다. 스크립트가 codex 작업 폴더를 `.temp_files/subcodex/`에 만든다.
- worker는 프로젝트의 `.claude/skills/`에 실제 파일로 복사해 둔다. 스크립트가 자기 위치에서 프로젝트 루트를 찾기 때문에 `~/.claude/skills/`에 두거나 심볼릭 링크로 연결하면 동작하지 않는다.
- Computer Use를 쓰려면 codex에서 먼저 설정해 둔다. Windows에서는 쓸 수 없다.
- `.claude/skills/`나 `.claude/agents/`를 Claude Code가 떠 있는 동안 새로 만들었다면 다시 시작한다.

### 표 바꾸기

표는 [SKILL.md](claude/skills/worker/SKILL.md)에 있고, 행마다 어떤 일이 들어가는지도 거기에 자세히 적혀 있다. 배정을 바꾸려면 그 표의 칸을 고친다. 대화창에 자기 표를 붙여 넣어도 된다. 그러면 다음 `/worker`를 입력할 때까지 그 표가 대신 쓰인다. `astra`와 `sol`이 가리키는 모델 이름은 스킬 폴더의 `scripts/wait_codex.py` 맨 위에 있다.

## 그 밖의 파일

### general-purpose.md (선택)

`claude/agents/general-purpose.md`는 worker에 필요한 파일이 아니다. 프로젝트의 `.claude/agents/`에 복사하면 그 프로젝트에서는 Claude Code에 내장된 general-purpose 에이전트 대신 이 파일이 쓰인다. 그러면 general-purpose로 띄우거나 종류 없이 띄운 서브에이전트는 메인 세션이 어떤 모델이든 Opus로 돈다. 자기 서브에이전트는 띄우지 못하고, 내장 프롬프트 대신 이 파일의 짧은 프롬프트를 받는다.

### AGENTS.md와 CLAUDE.md

개인 프로젝트에서 에이전트에게 주는 규칙이다. 이 저장소의 어느 것도 이 두 파일을 필요로 하지 않는다. 다만 worker와 닿는 규칙이 둘 있다.

- AGENTS.md는 임시 파일을 `.temp_files/`에 두게 한다. worker가 쓰는 디렉터리와 같다.
- CLAUDE.md는 Claude가 서브에이전트에 이름을 붙이지 못하게 한다. 내 환경에서는 이름 붙인 서브에이전트가 지정한 effort를 무시했고, 결과도 4,000자에서 잘려서 돌아왔다.

프로젝트에 두 파일이 함께 있으면 Claude Code는 기본적으로 CLAUDE.md만 읽는다. 둘 다 읽게 하려면 `/config`에서 "Project instructions"를 `claude-md-and-agents-md`로 바꾼다.

## 라이선스

`grill-me`를 뺀 나머지는 모두 [Unlicense](LICENSE)에 따라 퍼블릭 도메인으로 공개한다. `grill-me`는 [mattpocock/skills](https://github.com/mattpocock/skills)의 스킬을 고친 것이라 원래의 MIT 라이선스를 따르고, 고지는 [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md)에 있다.
