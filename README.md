# qbpowers

매일 쓰는 스킬을 모아 둔 저장소다. 각 스킬에는 Claude Code용과 Codex용이 있다. 필요한 것만 골라 자기 프로젝트에 복사해 써라.

| 스킬 | 하는 일 |
|---|---|
| [worker](#worker) | 메인 에이전트가 작업을 나누어 다른 에이전트에게 맡긴다. |
| [context-doc](#context-doc) | 대화 내용이 압축된 뒤에도 에이전트가 작업을 이어 가도록 자동으로 프로젝트 문서를 관리한다. |
| [freeze](#freeze) | `.temp_files/` 밖의 파일을 만들거나 고치거나 지우지 못하게 한다. |
| [grill-me](#grill-me) | 사용자가 하려는 일을 에이전트가 제대로 이해할 때까지 사용자에게 한 번에 하나씩 질문한다. |
| [wait-what](#wait-what) | 직전 답변을 쉬운 한국어로 다시 설명하도록 한다. |

스킬은 명령을 직접 입력할 때만 실행된다. 아래 사용 예는 Claude Code 기준이다. Codex에서는 `$<skill>`로 호출한다.

```
AGENTS.md, CLAUDE.md   개인 프로젝트에서 쓰는 규칙. 참고용이다. 위의 스킬들과 함께 쓰면 좋다.
```

설치는 [아래 안내](#설치)를 따른다.

## worker

`/worker`를 입력하면 Claude 메인 에이전트는 세션이 끝날 때까지 일을 적절하게 워커에게 맡긴다. Claude는 사용자와 대화하며 일을 조율하고, 워커가 실제 작업을 한다.

Claude 워커는 `opus`, `sonnet`, `haiku`, `fable` 서브에이전트다. GPT 워커는 codex CLI로 비대화형으로 실행하는 `astra`(`gpt-6.2-astra`), `sol`(`gpt-6.2-sol`), `terra`(`gpt-6.1-terra`)다. 화면을 조작하는 Computer Use는 GPT 워커에게만 맡긴다.

### 워커 선택

`/worker` 뒤에는 `claude`나 `codex` 중 한 계열을 적는다. 계열 이름에 `-lighter`, `-light`, `-max`를 붙이면 단계를 바꾼다. 붙이지 않으면 그 계열의 기본 단계를 쓴다. `/worker`만 입력하면 `codex`를 쓴다. 권장하는 설정도 `codex`다.

```
/worker # /worker codex와 같다
/worker claude-lighter
/worker claude-light
/worker claude
/worker claude-max
/worker codex-lighter [fast|ultrafast]
/worker codex-light [fast|ultrafast]
/worker codex [fast|ultrafast] # 이것을 사용하는 것을 추천한다.
/worker codex-max [fast|ultrafast]
/worker none # 워커를 사용하지 않는다. Claude가 워커를 쓰지 않고 메인 에이전트에서 직접 일한다.
```

각 계열에는 `lighter`, `light`, 기본, `max`의 네 단계가 있다. 가벼운 단계에서는 작은 모델을 더 많이 쓰거나 effort를 낮춘다. 높은 단계로 갈수록 큰 모델이나 높은 effort를 더 많이 쓴다. 

`codex` 계열의 모든 설정 뒤에는 `fast`나 `ultrafast` 중 하나를 붙일 수 있다. 생략하면 표준 속도로 실행한다. `claude` 계열은 속도 옵션을 받지 않는다.

설정은 세션이 끝날 때까지 유지된다. 마지막으로 입력한 `/worker`가 적용된다.

### 작업별 모델과 effort

사용자가 worker 스킬을 실행하면 그 후로는 Claude는 워커에게 시킬 작업 종류에 맞는 모델과 effort를 고른다.

무엇을 해야 할지 아직 모르는 일은 어려운 일로 본다. 원인을 모르는 버그나 설계·구조 결정이 여기에 속한다. 실행한 뒤 되돌리는 데 큰 비용이 드는 일도 여기에 속한다.

깊은 리뷰는 변경된 코드를 호출하는 곳과 테스트까지 읽으며 결함을 찾는 일이다. 어려운 일의 결과와 잘못되면 되돌리는 데 큰 비용이 드는 변경에 쓴다. 파일이나 데이터를 지우거나 덮어쓰는 변경, 비밀정보나 권한을 다루는 변경, 돈을 쓰는 변경 등이 해당한다.

코드·테스트·문서를 쓰거나 고치는 일은 작성으로 본다. 이미 정한 설계를 구현하는 일은 여러 모듈을 고쳐도 작성에 속한다. 일반 작업은 범위가 정해져 있고 그 안에서 판단하는 일이다. 버그 재현, 간단한 진단, 측정, 일상적인 점검, 코드 변경의 가벼운 리뷰와 필요 없는 코드를 찾는 리뷰가 여기에 속한다.

해석할 여지가 없는 일은 단순 작업으로 본다. 찾기와 읽기, 목록 만들기, 테스트 실행과 결과 보고, 한두 파일의 내용이 정해진 수정, 기계적인 반복이 여기에 속한다. 조사는 웹 검색과 외부 문서·오픈소스 조사를 말한다. Computer Use는 한 번에 하나만 실행한다.

#### Claude 워커 중심

| 일 | claude-lighter | claude-light | claude | claude-max |
|---|---|---|---|---|
| 어려운 일 | opus xhigh | opus xhigh | opus xhigh | fable xhigh |
| 깊은 리뷰 | opus medium | opus high | opus high | opus xhigh |
| 코드·테스트·문서 작성 | opus medium | opus high | opus high | opus xhigh |
| 일반 작업 | sonnet medium | opus medium | opus medium | opus xhigh |
| 조사 | haiku max | sonnet high | opus medium | opus high |
| 단순 작업 | haiku max | sonnet high | opus medium | opus high |
| Computer Use | terra medium | terra high | sol xhigh | sol xhigh |
| 메인 세션 Claude 권장 모델·effort | opus xhigh | opus xhigh | fable xhigh | fable max |

#### GPT 워커만 사용

| 일 | codex-lighter | codex-light | codex (추천) | codex-max |
|---|---|---|---|---|
| 어려운 일 | sol xhigh | sol max | astra xhigh | astra max |
| 깊은 리뷰 | sol high | sol xhigh | sol max | astra xhigh |
| 코드·테스트·문서 작성 | terra high | sol medium | sol xhigh | astra xhigh |
| 일반 작업 | terra high | sol medium | sol xhigh | astra xhigh |
| 조사 | terra medium | terra high | sol medium | astra high |
| 단순 작업 | terra medium | terra high | sol medium | astra high |
| Computer Use | terra medium | terra high | sol xhigh | astra xhigh |
| 메인 세션 Claude 권장 모델·effort | opus xhigh | opus xhigh | fable xhigh | fable max |

### 메인 에이전트의 모델

메인 에이전트는 사용자와 대화하는 Claude다. 각 표 마지막의 '메인 세션 Claude 권장 모델·effort'는 이 메인 에이전트를 위한 추천이다. 워커에 배정되는 모델이 아니며 꼭 따라야 하는 조건도 아니다. 메인 에이전트는 주로 일을 조율하므로 워커보다 토큰을 훨씬 적게 쓴다.

## context-doc

대화 내용이 압축돼도 작업을 이어 갈 수 있도록 Claude가 프로젝트 문서를 관리한다. 한 번 켜 두면 따로 시키지 않아도 Claude가 알아서 한다. 작업 중에 바뀐 규칙과 결정을 문서에 반영한다. 끝난 일은 진행 상황에서 지운다. 문서가 정해진 크기를 넘으면 줄이거나 나눈다.

문서는 영어로 관리된다. 기존 한국어 문서를 정리할 때도 영어로 옮기고, 영어로 쓰면 뜻이 틀리거나 모호해지는 곳만 한국어로 남긴다.

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

본인이 쓰는 에이전트에게 이 저장소를 알려주고, 본인의 환경에 맞게 설치해달라고 부탁하자. 요새는 다 이렇게 한다.

### context-doc의 Python 환경

context-doc을 쓰려면 프로젝트의 Python 환경에 `tiktoken`을 설치한다. [문서 검사 스크립트](.claude/skills/context-doc/scripts/check_docs.py)가 이 패키지를 쓴다.

### Claude Code용 worker 설정

Python 3.14와 프로젝트 루트의 `.venv`가 필요하다. worker 스크립트는 Python 3.14 문법을 쓰며 표준 라이브러리만 사용한다.

GPT 워커를 쓰려면 codex CLI가 PATH에 있고 로그인돼 있어야 한다. 프로젝트는 git 저장소여야 한다. `codex exec`는 git 저장소 밖에서는 실행되지 않는다. `claude` 계열의 모든 설정은 Computer Use를 쓰지 않으면 codex 없이도 동작한다.

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
- worker의 리뷰 워커는 AGENTS.md의 `## Comments` 절과 `## Code Changes` 절을 기준으로 변경을 검토한다. 프로젝트의 `AGENTS.md`에 이 두 절이 없으면 이 저장소의 같은 절을 복사해 넣는다.
- CLAUDE.md는 Claude가 서브에이전트에 이름을 붙이지 못하게 한다. 내 환경에서는 이름 붙인 서브에이전트가 지정한 effort를 무시했고, 결과도 4,000자에서 잘려서 돌아왔다.

프로젝트에 두 파일이 함께 있으면 Claude Code는 기본적으로 `CLAUDE.md`만 읽는다. 둘 다 읽게 하려면 `/config`에서 "Project instructions"를 `claude-md-and-agents-md`로 바꾼다. 이 값은 사용자 설정, 관리자가 정한 설정, `--settings`로 지정한 파일에서 읽는다. 프로젝트나 로컬 설정에 넣어도 적용되지 않는다.

### Claude Code 다시 시작

Claude Code 실행 중에 `.claude/skills/`나 `.claude/agents/`를 새로 만들었다면 Claude Code를 다시 시작한다. 스킬 폴더만 새로 만들었다면 `/reload-skills`로도 불러올 수 있다.

## 라이선스

`context-doc`, `freeze`, `wait-what`, `worker`의 두 버전과 나머지 파일은 [Unlicense](LICENSE)에 따라 퍼블릭 도메인으로 공개한다. `grill-me`의 Claude Code용과 Codex용은 모두 [mattpocock/skills](https://github.com/mattpocock/skills)의 스킬을 고친 것으로 원래의 MIT 라이선스를 따른다. 고지는 [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md)에 있고, grill-me를 복사해 쓸 때는 이 고지도 함께 둔다.
