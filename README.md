# qbpowers

매일 쓰는 스킬 다섯 개와 스킬이 쓰는 에이전트 파일을 모아 둔 저장소다. 각 스킬에는 Claude Code용과 Codex용이 있다. 필요한 것만 골라 자기 프로젝트에 복사해 쓴다.

| 스킬 | 하는 일 |
|---|---|
| [worker](#worker) | Claude가 작업을 나누어 다른 에이전트에게 맡긴다. |
| [context-doc](#context-doc) | 대화 내용이 압축된 뒤에도 에이전트가 작업을 이어 가도록 프로젝트 문서를 관리한다. |
| [freeze](#freeze) | `.temp_files/` 밖의 파일을 만들거나 고치거나 지우지 못하게 한다. |
| [grill-me](#grill-me) | 하려는 일을 Claude가 제대로 이해할 때까지 사용자에게 한 번에 하나씩 질문한다. |
| [wait-what](#wait-what) | 직전 답변을 쉬운 한국어로 다시 설명한다. |

스킬은 명령을 직접 입력할 때만 실행된다. 아래 사용 예는 Claude Code 기준이다. Codex에서는 `$<skill>`로 호출한다.

```
.claude/skills/        Claude Code 스킬 다섯 개
.codex/skills/         Codex 스킬 다섯 개
.claude/agents/        worker-effort-*.md (Claude Code의 worker에 필요), general-purpose.md (선택)
AGENTS.md, CLAUDE.md   개인 프로젝트에서 쓰는 규칙. 참고용이다
```

설치는 [아래 안내](#설치)를 따른다.

## worker

`/worker`를 입력하면 Claude는 세션이 끝날 때까지 일을 워커에게 맡긴다. Claude는 사용자와 대화하며 일을 조율하고, 워커가 실제 작업을 한다.

Claude 워커는 Opus 서브에이전트(`opus`)다. GPT 워커는 codex CLI로 실행하는 `gpt-6-astra`(`astra`)와 `gpt-6.1-sol`(`sol`)이다. effort는 모델이 얼마나 깊이 생각할지 정하는 설정이다. 화면을 조작하는 Computer Use는 GPT 워커에게만 맡긴다.

### 워커 선택

`/worker` 뒤에 어떤 워커를 쓸지 설정한다. 생략하면 `hybrid`를 쓴다.

```
/worker              # /worker hybrid와 같다
/worker claude-light
/worker claude
/worker hybrid-light [fast|ultrafast]
/worker hybrid [fast|ultrafast]
/worker codex-light [fast|ultrafast]
/worker codex [fast|ultrafast]
/worker codex-max [fast|ultrafast]
/worker none
```

- `hybrid`는 Claude와 GPT 워커를 함께 쓴다. 어려운 일과 깊은 리뷰는 Opus가 맡는다. 코드·테스트·문서 작성은 astra가, 나머지는 sol이 맡는다.
- `claude`는 Computer Use를 제외한 모든 일에 Claude 워커를 쓴다.
- `claude-light`는 `claude`보다 Opus의 effort를 낮춘다.
- `hybrid-light`는 `hybrid`보다 Opus의 effort를 낮추고, 작성도 sol에게 맡긴다.
- `codex`는 GPT 워커만 쓴다. 어려운 일과 작성, 깊은 리뷰는 astra가 맡는다. 나머지는 sol이 맡는다.
- `codex-light`는 어려운 일만 astra에게 맡기고, 나머지는 sol에게 맡긴다.
- `codex-max`는 모든 작업에 `astra max`를 쓴다.
- `none`은 새 워커를 실행하지 않는다. Claude가 직접 일한다. 이미 실행 중인 워커는 맡은 일을 마친다.

`hybrid-light`, `hybrid`, `codex-light`, `codex`, `codex-max` 뒤에는 `fast`나 `ultrafast` 중 하나를 붙일 수 있다. `fast`는 GPT 워커의 서비스 티어를 `priority`로 정한다. `ultrafast`는 서비스 티어를 `ultrafast`로 정한다. 생략하면 표준 속도로 실행한다. `claude-light`와 `claude`의 Computer Use용 GPT 워커도 표준 속도로 실행한다.

```
/worker hybrid fast
```

설정은 세션이 끝날 때까지 유지된다. 마지막으로 입력한 `/worker`가 적용된다.

### 작업별 모델과 effort

사용자가 설정을 고르면 Claude는 작업 종류에 따라 모델과 effort를 고른다. 예를 들어 `hybrid`에서는 코드 작성에 `astra max`, 버그 재현에 `sol max`를 쓴다.

원인을 모르는 버그나 설계 결정은 어려운 일로 본다. 버그 재현이나 일상적인 점검처럼 정해진 범위 안에서 판단이 필요한 일은 일반 작업으로 본다. 정해진 내용을 그대로 수행하는 일은 단순 작업으로 본다.

모델 이름 뒤에 effort를 적는다. `opus xhigh`는 Opus 워커를 xhigh effort로 쓴다는 뜻이다.

| 일 | claude-light | claude | hybrid-light | hybrid | codex-light | codex | codex-max |
|---|---|---|---|---|---|---|---|
| 어려운 일: 원인을 모르는 버그, 설계 결정, 여러 모듈에 걸친 변경, 되돌리기 어려운 변경 | opus xhigh | opus max | opus xhigh | opus max | astra max | astra max | astra max |
| 코드·테스트·문서 작성 | opus high | opus xhigh | sol max | astra max | sol max | astra max | astra max |
| 중요한 변경의 깊은 리뷰 | opus high | opus xhigh | opus high | opus xhigh | sol max | astra max | astra max |
| 조사: 웹 검색, 외부 문서, 오픈소스 | opus medium | opus high | sol max | sol max | sol max | sol max | astra max |
| 일반 작업: 범위가 정해진 일. 버그 재현, 간단한 진단, 일상적인 점검 | opus medium | opus high | sol max | sol max | sol max | sol max | astra max |
| 단순 작업: 찾기와 읽기, 테스트 실행, 내용이 정해진 수정, 기계적인 반복 | opus medium | opus medium | sol max | sol max | sol max | sol max | astra max |
| Computer Use, 한 번에 하나만 | sol max | sol max | sol max | sol max | sol max | sol max | astra max |

Codex의 `$worker`는 `codex-light`, `codex`(기본값), `codex-max` 세 설정과 `none`만 받고, Codex 자체 서브에이전트에게 일을 맡긴다. 속도 옵션은 없다.

### 작업 배정 바꾸기

기본 배정을 바꾸려면 [worker의 SKILL.md](.claude/skills/worker/SKILL.md)에 있는 표를 고친다. 작업 종류의 자세한 기준도 이 파일에 있다. 대화창에 원하는 배정표를 붙여 넣으면 다음 `/worker`를 입력할 때까지 그 표를 쓴다. `astra`와 `sol`이 가리키는 모델 이름은 [wait_codex.py](.claude/skills/worker/scripts/wait_codex.py) 맨 위에 있다.

### 작업을 맡기는 방식

- 동시에 진행해도 문제없는 일은 Claude가 여러 워커에게 나누어 맡긴다.
- 워커가 결정 없이는 더 나아갈 수 없으면 Claude에게 묻는다. 답을 받으면 멈춘 곳에서 이어 간다.
- 워커가 실패하면 Claude가 실패를 알린다. 알리지 않고 다른 워커에게 넘기거나 직접 처리하지 않는다.
- GPT 워커는 백그라운드에서 `codex exec`로 실행된다. 실행마다 `.temp_files/subcodex/` 아래에 폴더가 생기고 프롬프트, 로그, 마지막 메시지가 남는다.
- Codex 사용량 한도에 걸리면 새 작업 실행을 멈추고 대기한다. 한도가 풀리면 같은 실행 명령으로 이어 갈 수 있다.

### 메인 에이전트의 모델

메인 에이전트는 사용자와 대화하는 Claude다. 주로 일을 조율하므로 워커보다 토큰을 훨씬 적게 쓴다. 요금제에 맞춰 Opus 5.5 max, 또는 Fable 5.2 max나 xhigh를 권한다.

## context-doc

대화 내용이 압축돼도 작업을 이어 갈 수 있도록 Claude가 프로젝트 문서를 관리한다. 한 번 켜 두면 따로 시키지 않아도 Claude가 알아서 한다. 작업 중에 바뀐 규칙과 결정을 문서에 반영한다. 끝난 일은 진행 상황에서 지운다. 문서가 정해진 크기를 넘으면 줄이거나 나눈다.

문서는 영어로 쓴다. 기존 한국어 문서를 정리할 때도 영어로 옮기고, 영어로 쓰면 뜻이 틀리거나 모호해지는 곳만 한국어로 남긴다.

```
/context-doc <project path>
/context-doc <project path> review
/context-doc
/context-doc review
```

프로젝트 경로를 주면 세션이 끝날 때까지 그 프로젝트의 문서를 관리한다. 문서가 없으면 새로 만든다. 프로젝트의 `AGENTS.md`에 이 스킬의 문서 규칙이 없으면 기존 문서 구성을 정리한다. 이미 규칙이 있으면 문서를 읽고 검사한다.

`review`를 붙이면 문서 전체를 검토한다. 중복된 내용과 틀린 설명을 고친다. 근거만으로 정할 수 없는 내용은 사용자에게 알린다.

경로를 생략하면 이 세션에서 앞서 지정한 프로젝트를 쓴다. 앞서 지정한 프로젝트가 없거나 여러 개면 어느 프로젝트인지 묻는다. 세션 중에는 이 스킬을 끌 수 없다.

## freeze

`/freeze`를 입력하면 Claude와 워커는 `.temp_files/` 밖의 파일을 만들거나 고치거나 지우지 않는다. 파일 읽기와 분석, 조사는 계속할 수 있다. `.temp_files/` 안의 파일은 바꿀 수 있다.

```
/freeze
/freeze end
```

`.temp_files/` 밖의 파일을 바꿔야 하면 Claude는 무엇을 바꿀지만 알린다. 실제 변경은 `/freeze end` 뒤에 한다. `/freeze end`를 입력하면 제한이 풀리고 프로젝트의 평소 규칙을 다시 따른다. 마지막으로 입력한 설정이 세션 끝까지 유지된다.

## grill-me

생각이 덜 정리된 일을 시작할 때 쓴다. 대화에서 하려는 일을 이미 이야기했다면 `/grill-me`만 입력하면 된다. 아직 말하지 않았다면 `/grill-me` 뒤에 적는다. Claude는 그 일을 사용자와 똑같이 이해할 때까지 사용자에게 한 번에 하나씩 질문한다.

```
/grill-me
/grill-me 사용자 활동 로그를 남기고 나중에 분석하고 싶다.
```

Claude는 질문마다 추천 답과 짧은 이유를 제시한다. 추천할 근거가 없으면 그 사실을 알린다. 코드나 웹에서 알 수 있는 것은 먼저 찾아본다. 사용자에게는 취향이나 우선순위처럼 조사로 알 수 없는 것만 묻는다.

사용자가 되물으면 Claude는 인터뷰를 멈추고 그 질문에 답한다. 필요한 조사와 분석도 먼저 한다. 답변에 인터뷰 질문을 덧붙이지 않는다. 사용자의 질문이 끝나면 새로 알게 된 내용을 반영해 보류했던 질문으로 돌아간다.

## wait-what

답변이 잘 와닿지 않을 때 `/wait-what`을 입력한다. Claude가 맥락을 조금 더 붙여서 직전 답변을 쉬운 한국어로 다시 설명한다.

```
/wait-what
```

다른 언어로 받으려면 [SKILL.md](.claude/skills/wait-what/SKILL.md)의 본문과 `description`에 있는 "Korean"을 바꾼다.

## 설치

### 스킬 복사

Claude Code나 Codex를 설치하고 로그인한 뒤 진행한다. Claude Code용은 `.claude/skills/<skill>/`을 프로젝트의 `.claude/skills/`에 복사한다. Codex용은 `.codex/skills/<skill>/`을 프로젝트의 `.codex/skills/`에 복사한다.

아래 예는 두 버전을 모두 복사한다. `/path/to/project`는 사용할 프로젝트의 실제 경로로 바꾼다. 필요한 스킬만 설치하려면 반복문의 스킬 목록을 줄인다.

```sh
git clone https://github.com/ymchoi/qbpowers.git
cd qbpowers
mkdir -p /path/to/project/.claude/skills /path/to/project/.codex/skills
for skill in worker context-doc freeze grill-me wait-what; do
    cp -R ".claude/skills/$skill" /path/to/project/.claude/skills/
    cp -R ".codex/skills/$skill" /path/to/project/.codex/skills/
done
```

freeze, grill-me, wait-what은 복사만 하면 쓸 수 있다. 이 세 스킬의 Claude Code용은 `~/.claude/skills/`에 두면 모든 프로젝트에서 쓸 수 있다.

### context-doc의 Python 환경

context-doc을 쓰려면 프로젝트의 Python 환경에 `tiktoken`을 설치한다. [문서 검사 스크립트](.claude/skills/context-doc/scripts/check_docs.py)가 이 패키지를 쓴다.

### Claude Code용 worker 설정

Python 3.14와 프로젝트 루트의 `.venv`가 필요하다. worker 스크립트는 Python 3.14 문법을 쓰며 표준 라이브러리만 사용한다.

GPT 워커를 쓰려면 codex CLI가 PATH에 있고 로그인돼 있어야 한다. 프로젝트는 git 저장소여야 한다. `codex exec`는 git 저장소 밖에서는 실행되지 않는다. `claude`와 `claude-light`는 Computer Use를 쓰지 않으면 codex 없이도 동작한다.

스킬을 복사한 뒤 qbpowers 폴더에서 Claude 워커용 에이전트 파일도 복사한다.

```sh
mkdir -p /path/to/project/.claude/agents
cp .claude/agents/worker-effort-*.md /path/to/project/.claude/agents/
```

`worker-effort-*.md`는 Claude 워커의 effort를 고정한다. 이 워커는 자기 서브에이전트를 띄우지 못한다.

프로젝트 루트에 Python 3.14 `.venv`가 없으면 만든다.

```sh
python3.14 -m venv /path/to/project/.venv
```

- codex가 파일을 쓸 수 있게 한다. `codex exec`는 기본값이 읽기 전용이므로 `~/.codex/config.toml`에 `sandbox_mode = "workspace-write"`를 넣는다.
- 프로젝트의 `.gitignore`에 `.temp_files/`를 넣는다. 스크립트가 codex 작업 폴더를 `.temp_files/subcodex/`에 만든다.
- worker는 프로젝트의 `.claude/skills/`에 실제 파일로 복사해 둔다. 스크립트가 자기 위치에서 프로젝트 루트를 찾기 때문에 `~/.claude/skills/`에 두거나 심볼릭 링크로 연결하면 동작하지 않는다.
- Computer Use를 쓰려면 codex에서 먼저 설정해 둔다. Windows에서는 쓸 수 없다.

### general-purpose.md (선택)

[general-purpose.md](.claude/agents/general-purpose.md)는 worker와 별개로 선택해서 쓰는 에이전트 파일이다. 필요하면 qbpowers 폴더에서 복사한다.

```sh
mkdir -p /path/to/project/.claude/agents
cp .claude/agents/general-purpose.md /path/to/project/.claude/agents/
```

복사하면 `general-purpose`로 지정하거나 종류를 지정하지 않고 띄운 서브에이전트에 이 파일이 쓰인다. 같은 이름의 내장 에이전트가 있으면 이 파일이 우선한다. 프롬프트도 이 파일의 내용을 쓴다. 메인 세션의 모델과 관계없이 Opus로 실행된다. 자기 서브에이전트는 띄우지 못한다.

### AGENTS.md와 CLAUDE.md (선택)

[AGENTS.md](AGENTS.md)와 [CLAUDE.md](CLAUDE.md)는 개인 프로젝트에서 에이전트에게 주는 규칙이다. 스킬 설치에는 필요하지 않다. 필요한 규칙만 자신의 프로젝트에 반영한다.

- AGENTS.md는 임시 파일을 `.temp_files/`에 두게 한다. worker가 쓰는 디렉터리와 같다.
- CLAUDE.md는 Claude가 서브에이전트에 이름을 붙이지 못하게 한다. 내 환경에서는 이름 붙인 서브에이전트가 지정한 effort를 무시했고, 결과도 4,000자에서 잘려서 돌아왔다.

프로젝트에 두 파일이 함께 있으면 Claude Code는 기본적으로 `CLAUDE.md`만 읽는다. 둘 다 읽게 하려면 `/config`에서 "Project instructions"를 `claude-md-and-agents-md`로 바꾼다. 이 값은 사용자 설정, 관리자가 정한 설정, `--settings`로 지정한 파일에서 읽는다. 프로젝트나 로컬 설정에 넣어도 적용되지 않는다.

### Claude Code 다시 시작

Claude Code 실행 중에 `.claude/skills/`나 `.claude/agents/`를 새로 만들었다면 Claude Code를 다시 시작한다. 스킬 폴더만 새로 만들었다면 `/reload-skills`로도 불러올 수 있다.

## 라이선스

`context-doc`, `freeze`, `wait-what`, `worker`의 두 버전과 나머지 파일은 [Unlicense](LICENSE)에 따라 퍼블릭 도메인으로 공개한다. `grill-me`의 Claude Code용과 Codex용은 모두 [mattpocock/skills](https://github.com/mattpocock/skills)의 스킬을 고친 것으로 원래의 MIT 라이선스를 따른다. 고지는 [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md)에 있고, grill-me를 복사해 쓸 때는 이 고지도 함께 둔다.
