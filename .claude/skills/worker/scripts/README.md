# Worker script maintenance

Caller workflow and rules: [worker guide](../SKILL.md).

## Work-directory protocol

`new_workdir.py` creates `WORK` under `<repo>/.temp_files/subcodex/`.
Attempts are `<n>-<kind>`, numbered from 1; the highest number is latest:

- `fresh`: run rules followed by `prompt.txt` become `input.txt`; new session.
- `continue`: `Continue and finish the task.\n` becomes `input.txt`; resumes.
- `reply`: moves `reply.txt` to `input.txt`; resumes, retaining that input on restart.

As an attempt progresses, the waiter writes `input.txt`; Codex writes `last.txt`.
The wrapper redirects stdout/stderr to `stdout.log`/`stderr.log` and writes
`exit_code`; the launcher writes the wrapper's `pid`. Caught Codex-start `OSError`s
become code 127.

`WORK/last.txt` holds the latest success, removed after preparing new input and
before launching. `WORK/failed.txt` holds the summary entry while verdict is `FAILED`.
Success requires exit code 0 and nonempty attempt `last.txt`; with `schema.json`,
the message must parse as a JSON object; schema conformance is not checked.

Resume IDs come from the latest fresh attempt's `stderr.log`. With neither a
readable exit code nor a PID file, restart in place. Outside usage limits, recovery
is: pending reply with a session ID; otherwise continue with a session ID unless
already a continue; otherwise a budgeted fresh start; otherwise failure. Fresh
retries count fresh folders on disk, minus the first.
A pending reply also resumes after success; without a session ID this is `NO_SESSION`.
A usage limit detected in this invocation queues new starts; recovery resumes the
session, or starts fresh without one. Start failures are held for this invocation.

## Process and policy reasons

The wrapper is detached so an attempt can run independently of the calling
terminal: POSIX uses `start_new_session=True`; Windows uses
`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`. Observed Windows console behavior
rules out `DETACHED_PROCESS`: Codex can allocate a new console that Windows Terminal
displays as a window. Background-task ownership follows the [worker guide](../SKILL.md).

The blanket no-window run rule is Windows-only so macOS Computer Use workers can
operate a browser. Window permissions follow the [repository rules](../../../../AGENTS.md).
CLI flags (`--disable multi_agent`, `--disable multi_agent_v2`) are paired with
fresh-input rules forbidding delegation: observed model behavior can retain
delegation instructions even with both features disabled.

## Schema compatibility

The waiter normalizes `schema.json` before fresh starts because, in observed
Codex/API behavior, `--output-schema` is sent as a `strict: true` response format;
incompatible schemas can fail with HTTP 400 `invalid_json_schema` before work runs.

## Summary

```text
batch: <n> ok, <n> failed, <n> stalled, <n> running, <n> queued
OK <WORK>/last.txt
FAILED <WORK> <label>
    <report>
STALLED <WORK> <minutes since activity>
RUNNING <WORK>
QUEUED <WORK>
```

Labels: `MISSING_PROMPT`, `BAD_SCHEMA`, `NO_SESSION`, `LAUNCH_FAILED`,
`BAD_OUTPUT` (exit 0, unusable message), `DIED` (no readable code, no live wrapper),
and `EXIT_<code>` (nonzero recorded code), after applicable recovery is exhausted.
