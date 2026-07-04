# qbpowers

Claude Code와 OpenAI Codex CLI에서 쓰는 에이전트 스킬 모음입니다. 개인 프로젝트에서 실사용 중인 스킬들의 공개 스냅샷입니다.

A collection of agent skills for Claude Code and the OpenAI Codex CLI — a public snapshot of skills in daily use in a personal project.

## Skills

| Skill | Claude | Codex | 설명 / Description |
|---|:---:|:---:|---|
| diagnose-bug | ✓ | ✓ | 어려운 버그를 위한 규율 잡힌 진단 루프: 재현→최소화→가설→계측→수정→회귀테스트. / Disciplined diagnosis loop for hard bugs: reproduce → minimise → hypothesise → instrument → fix → regression-test. |
| grill-me | ✓ | ✓ | 계획의 모든 분기를 공유 이해에 도달할 때까지 한 번에 하나씩 인터뷰. / Relentless one-question-at-a-time interview about a plan until shared understanding. |
| handoff | ✓ | ✓ | 컨텍스트가 없는 새 에이전트가 이어받을 수 있는 세션 인수인계 문서 생성. / Generates a handover document a context-blind agent can continue from. |
| tdd | ✓ | ✓ | red-green-refactor TDD 워크플로 + 테스트 품질/모킹/인터페이스 설계 가이드. / TDD workflow plus guides on test quality, mocking, and interface design. |
| model-sub-claude | ✓ | — | `/model-sub-claude <model> [effort]` — 세션의 서브에이전트 기본 model/effort를 명시적으로 고정. / Pin the session's default subagent model+effort explicitly. |
| model-sub-codex | ✓ | — | `/model-sub-codex [model] [effort]` — 모든 서브에이전트를 `codex exec` 브리지로 라우팅. 레이트리밋 대기 정책 포함. / Route every subagent through a `codex exec` bridge, with a rate-limit wait policy. |

## Installation / 설치

- **Claude Code**: `claude/skills/<skill>` 디렉터리를 프로젝트의 `.claude/skills/`로 복사. / Copy a directory under `claude/skills/` into your project's `.claude/skills/`.
- **Codex CLI**: `codex/skills/<skill>` 디렉터리를 프로젝트의 `.codex/skills/`로 복사. / Copy a directory under `codex/skills/` into your project's `.codex/skills/`.

## Portability notes / 이식 안내

이 스킬들은 원 프로젝트의 규약을 일부 전제합니다. / These skills assume a few conventions from their home project:

- `.temp_files/` (handoff, model-sub-codex): 프로젝트 루트의 gitignore된 임시 파일 디렉터리 규약. 본인 프로젝트의 스크래치 디렉터리로 바꿔도 됩니다. / A gitignored scratch-directory convention at the project root; substitute your own.
- `AGENTS.md` (model-sub-*): 서브에이전트 기본값과 파일 수정 게이트 규칙이 담긴 프로젝트 지침 파일을 전제합니다. / Assumes a project instruction file defining subagent defaults and a file-modification gate.
- `model-sub-codex`의 `<project-root>`와 `<GATE_MARKER>`는 플레이스홀더입니다. `<project-root>`는 본인 프로젝트의 절대 경로로, `<GATE_MARKER>`는 본인이 쓰는 파일 수정 승인 마커로 바꾸세요(그런 게이트를 쓰지 않으면 해당 규칙을 삭제). / `<project-root>` and `<GATE_MARKER>` in `model-sub-codex` are placeholders: replace them with your project's absolute path and your own modification-approval marker (or drop that rule if you don't use such a gate).

## License / 라이선스

- 직접 작성 스킬 (handoff, model-sub-claude, model-sub-codex): [Unlicense](LICENSE) — public domain.
- 파생 스킬 (diagnose-bug, grill-me, tdd): [mattpocock/skills](https://github.com/mattpocock/skills)를 개조한 것으로 MIT 라이선스가 적용됩니다. / Modified from mattpocock/skills, MIT licensed — see [THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).
