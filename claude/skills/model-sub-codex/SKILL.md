---
name: model-sub-codex
description: Route this session's subagent work through OpenAI codex - every Claude subagent becomes a thin bridge that runs one `codex exec` and relays its result, overriding the AGENTS.md subagent defaults and any active /model-sub-claude mode, with /model-sub-codex [model] [effort] optionally overriding the codex model/effort for all bridges (bare invocation applies gpt-5.6-sol + ultra). Use ONLY when the user explicitly invokes /model-sub-codex. Never auto-trigger from general talk about subagents, codex, cost, or performance.
---

# Sub-Codex Mode

## Arguments

The invocation is `/model-sub-codex [model] [effort]` — both optional, and NOT validated: values pass through to codex verbatim, and a bad value fails loudly on the first delegation (invalid model → HTTP 400; invalid effort → codex lists the supported efforts).

- No arguments: apply `gpt-5.6-sol` + `ultra` explicitly.
- One argument: `low`/`medium`/`high`/`xhigh`/`max`/`ultra` sets effort (model defaults to `gpt-5.6-sol`); anything else is the model (effort defaults to `ultra`).
- Two arguments: `<model> <effort>`.
- The resolved model + effort bind to the mode until the session ends or the mode is switched or re-invoked; hand them to every bridge (see Spawning a bridge).

## Mode

The AGENTS.md subagent rule begins "Unless the user explicitly specifies a subagent's `model`/`effort`". Invoking this skill IS that explicit specification: from now until the end of this session, every subagent you create is a **bridge** — a Claude subagent whose only job is to run exactly one `codex exec` and relay its result. The work the subagent would normally do itself is delegated to codex (model + effort resolved per the Arguments section, defaulting to gpt-5.6-sol + ultra for any slot left unspecified). No exceptions while the mode is active: all subagent spawns become bridges (sole exception: an explicit per-request user instruction — see Precedence and scope); if that causes problems, the user will switch modes (`/model-sub-claude <model> [effort]`) themselves.

## Spawning a bridge

- Bridge model: `sonnet` — cheap relay shell, 1M context. `Workflow` `agent()` opts: `model: 'sonnet', effort: 'low'`. Plain `Agent` tool: `model: "sonnet"` (that tool has no `effort` parameter).
- Hand the bridge: (1) the full task prompt you would have given a normal subagent, verbatim; (2) the working root for `-C` (normally this project's root); (3) the `<GATE_MARKER>` marker — include that exact phrase in the codex prompt if and only if the current user turn authorized file modification (codex reads AGENTS.md itself, so without the phrase it will refuse modification work — that double-gate is intended); (4) for `Workflow` `agent()` calls that use a `schema`, the same JSON Schema so the bridge can enforce it via `--output-schema` (as normalized in bridge step 1) — authored per the Strict schema rules below, and when you author a delegation schema in this mode, always add a required `bridge_error` string property (empty string on success) so failures have an in-band channel, and a required `work_dir` string property the bridge fills with its `$WORK` absolute path so every result stays traceable to its evidence dir; (5) the mode's resolved model + effort — always set (defaults gpt-5.6-sol / ultra) (steps 2 and 5 show the exact flags).
- **Strict schema rules** — every delegation schema must satisfy OpenAI's strict structured-output validation, NOT merely `Workflow`'s: codex forwards `--output-schema` verbatim to the API as a `strict: true` response format (zero normalization), so the API rejects anything looser with HTTP 400 `invalid_json_schema` before any work runs. Hard rules: (a) EVERY object level — root, nested objects, and objects inside array `items`, `$defs`, or `anyOf` branches alike — must carry `"additionalProperties": false`; (b) every key in every `properties` map must be listed in that object's `required` — express an optional field by keeping it required and adding `"null"` to its type (`"type": ["integer","null"]`; for enums keep `null` out of the enum list and null-union the type; for `$ref` fields use `anyOf` with `{"type": "null"}`), never by omitting it from `required`; (c) the root must be a plain `object` (no root-level `anyOf`), and composition keywords `allOf`/`not`/`dependentRequired`/`dependentSchemas`/`if`/`then`/`else` are unsupported everywhere. The bridge's step-1 normalizer mechanically enforces (a) and (b) on the codex-side copy as a backstop, so a typical authoring slip costs nothing — but author compliant schemas anyway: the same schema is what Claude-side validation enforces on the bridge's own structured output, and the normalizer deliberately does NOT touch what it cannot fix faithfully (rule (c) violations, and a schema-valued `additionalProperties` — map-typed fields are unsupported in strict mode, so model maps as arrays of key/value objects); those still fail loudly per step 5.
- Bridges never spawn subagents of their own. If the delegated task needs internal fan-out, codex fans out with its own agent threads.
- Sanity-check every bridge result you consume: an all-empty payload (empty or placeholder fields with an empty `bridge_error`) is a bridge failure in disguise — treat it as a failure and inspect the directory named in its `work_dir` field before trusting or discarding the work.

## Bridge procedure (instruct every bridge to follow this)

1. `WORK=$(mktemp -d <project-root>/.temp_files/subcodex_bridge_XXXXXX)` — a private dir keeps parallel bridges collision-free, and `.temp_files/` writes need no modification gate. Run `mktemp` exactly ONCE: shell state does not persist between Bash calls, so note the absolute path it printed and START every later Bash call by re-declaring it literally (`WORK=<that absolute path>; ...`) — never re-run mktemp for the same delegation. Write the codex prompt to `$WORK/prompt.txt` (never inline it into the command — no shell-quoting hazards). If a schema was provided, write it to `$WORK/schema.json`, then run this exact normalizer verbatim in one Bash call (idempotent — it mechanically enforces Strict schema rules (a)+(b) on the codex-side copy, preserving semantics by turning optional fields into required-but-nullable; it cannot fix rule (c) violations, which still fail loudly per step 5):

```
: "${WORK:?WORK unset}"; python3 - "$WORK/schema.json" <<'EOF'
import json, sys
path = sys.argv[1]
def nullable(v):
    if not isinstance(v, dict): return v
    t = v.get("type")
    if isinstance(t, str): v["type"] = [t, "null"]; return v
    if isinstance(t, list):
        if "null" not in t: t.append("null")
        return v
    if "anyOf" in v:
        if not any(isinstance(b, dict) and b.get("type") == "null" for b in v["anyOf"]):
            v["anyOf"].append({"type": "null"})
        return v
    return {"anyOf": [v, {"type": "null"}]}
def walk(s):
    if not isinstance(s, dict): return
    props = s.get("properties")
    t = s.get("type")
    is_obj = t == "object" or (isinstance(t, list) and "object" in t)
    if isinstance(props, dict) and (is_obj or t is None):
        if t is None: s["type"] = "object"
        s.setdefault("additionalProperties", False)
        req = s.get("required") or []
        for k in props:
            if k not in req: props[k] = nullable(props[k])
        s["required"] = list(props)
        for v in props.values(): walk(v)
    elif is_obj:
        s.setdefault("additionalProperties", False)
    walk(s.get("items"))
    for key in ("$defs", "definitions"):
        d2 = s.get(key)
        if isinstance(d2, dict):
            for v in d2.values(): walk(v)
    for key in ("anyOf", "oneOf"):
        for v in (s.get(key) or []): walk(v)
d = json.load(open(path, encoding="utf-8"))
walk(d)
json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
print("strict-normalized:", path)
EOF
```
2. Launch codex detached with an exit-code sentinel, in one Bash call:
   `: "${WORK:?WORK unset}"; nohup sh -c "codex exec - -C <workroot> -m <model> -c model_reasoning_effort=\"<effort>\" --output-schema $WORK/schema.json -o $WORK/last.txt < $WORK/prompt.txt > $WORK/stdout.log 2> $WORK/stderr.log; echo \$? > $WORK/exit_code" > /dev/null 2>&1 & echo $! > $WORK/pid`
   Include `--output-schema $WORK/schema.json` only if a schema was provided; if not, omit those two tokens entirely. The `-m <model>` and `-c model_reasoning_effort="<effort>"` flags are NOT conditional: the mode always resolves both (defaults gpt-5.6-sol / ultra), so they are present on every run and codex never relies on its own local defaults. (`-` reads the prompt from stdin; stdout carries only the final message, logs and the session id line go to stderr. `$WORK/pid` records the wrapper's PID for step 3's liveness check.)
3. Wait by polling the sentinel — there is NO total time limit; long tasks are expected and codex must never be killed for being slow. Repeat this bounded call until it prints DONE, always passing `timeout: 600000` on the Bash call (the loop runs up to 570s; the tool's default 120s timeout would kill it mid-poll with no verdict):
   `: "${WORK:?WORK unset}"; for i in $(seq 1 114); do [ -f $WORK/exit_code ] && break; sleep 5; done; if [ -f $WORK/exit_code ]; then echo DONE; elif kill -0 "$(cat $WORK/pid)" 2>/dev/null; then echo RUNNING; else echo CRASHED; fi`
   If it prints RUNNING — or the tool kills the call on timeout, which is the same non-verdict — run the same call again in a new Bash invocation. CRASHED means the detached wrapper died without writing `exit_code` (it will never appear): stop polling and go to step 5. Never emit your final/structured result before a DONE or CRASHED verdict — a premature "partial/still running" report is a protocol violation that forces the orchestrator to re-harvest your `$WORK` dir by hand.
4. Success = `exit_code` contains `0` AND `$WORK/last.txt` is non-empty → relay the content of `last.txt` as your result. Plain task: return the text verbatim. Schema task: `last.txt` IS the schema-conforming JSON — parse it and emit its fields one-to-one as your own structured output (never wrap the raw JSON text inside a single field; if codex emitted `null` for a field that only the step-1 normalizer made nullable — i.e. the schema as handed to you left it optional and non-nullable — omit that field instead of relaying the `null`) — with one field-value exception: always overwrite `work_dir` with your own `$WORK` absolute path, whatever codex put there; the same applies to failure reports.
5. Failure = a nonzero exit code, an empty result, a CRASHED verdict from step 3, or (schema task) a `last.txt` that fails to parse or validate against the schema. Recover and report like this:
   - First grep `$WORK/stderr.log` for context-window exhaustion (codex prints `ERROR: Codex ran out of room in the model's context window`). If present, do NOT resume — the session is already full and will fail again identically; report failure immediately and say the delegated input/task was too large, so the orchestrator can shrink the delegation and retry fresh.
   - Next — only for a schema task and only if the exit code is nonzero (both gates matter: stderr echoes the task's own content, so an ungated match could be the prompt itself quoting such an error) — check for a strict-schema rejection: `grep -A4 '^ERROR: {' $WORK/stderr.log | grep -F '"code": "invalid_json_schema"'`. A match means the API rejected `$WORK/schema.json` itself (HTTP 400 before any work started; codex does not retry it — two identical ERROR blocks in stderr are the same single failure printed twice). Do NOT resume — a resume re-sends the same schema and fails identically. Report failure immediately: put the full ERROR block from `$WORK/stderr.log` VERBATIM (its `message` names the offending schema context) plus the `$WORK` path into `bridge_error`, so the orchestrator re-authors the schema per Strict schema rules and re-delegates fresh.
   - Next, only if the exit code is nonzero, grep `$WORK/stderr.log` for codex's usage-limit error line: `grep -E "^ERROR: You've hit your usage limit" $WORK/stderr.log` (codex prints it as a whole line at column 1; a genuinely rate-limited run never exits 0, and keyword patterns like `rate limit|quota` must NOT be used — stderr echoes the task's own content, which matches them). If it matches, do NOT resume and do NOT retry yourself: report `RATE_LIMIT: ` followed by the matching stderr lines VERBATIM plus the `$WORK` path — in `bridge_error` for a schema task, as the leading text of your result for a plain task — codex states the reset time there (`... try again at H:MM AM/PM`, with a date when the reset falls on another calendar day, as is typical for the weekly limit) and the orchestrator schedules the retry from that text (see Rate-limit handling).
   - Otherwise make exactly one recovery attempt: write the recovery prompt to `$WORK/prompt2.txt` — `<GATE_MARKER> — Continue and finish the task.` if the original delegation prompt contained the `<GATE_MARKER>` marker, plain `Continue and finish the task.` if it did not (the resume is a NEW prompt, so the modification gate must be re-passed with exactly the original authorization) — extract the session id from the `$WORK/stderr.log` header, and relaunch detached with the same sentinel pattern but this command (note: `codex exec resume` does NOT accept `-C`; it resumes from the invoking shell's current directory, hence the leading `cd`): `: "${WORK:?WORK unset}"; nohup sh -c "cd <workroot> && codex exec resume <session-id> - -m <model> -c model_reasoning_effort=\"<effort>\" --output-schema $WORK/schema.json -o $WORK/last2.txt < $WORK/prompt2.txt > $WORK/stdout2.log 2> $WORK/stderr2.log; echo \$? > $WORK/exit_code2" > /dev/null 2>&1 & echo $! > $WORK/pid2` (omit `--output-schema` if the task had no schema; the first attempt's `stderr.log` / `exit_code` remain untouched as evidence). Poll with the step 3 command but watching `$WORK/exit_code2` and `$WORK/pid2` — the first attempt's `exit_code` already exists, so reusing step 3 verbatim would print DONE instantly. On success apply step 4 to `$WORK/last2.txt` unchanged.
   - If recovery fails too (or was skipped), report the failure LOUDLY — exit code, tail of stderr, session id, `$WORK` path — and never emit a success-shaped result: with a schema, put the full failure detail into `bridge_error` (leaving an error field empty on failure is itself a protocol violation); if the schema has no error field, put `BRIDGE_FAILURE: <detail>` into the first required string field instead of fabricating data. Do NOT fall back to doing the task yourself.

## Rate-limit handling (orchestrator policy)

codex enforces a 5-hour and a weekly usage limit; a weekly-limit wait can last days. Blocked bridges surface the limit in-band — `RATE_LIMIT: ` at the start of `bridge_error` (schema tasks) or of the plain text result (schema-less tasks) — with the codex stderr text, which states the reset time. While this mode is active, the orchestrator MUST:

- NEVER fall back to Claude for the delegated work, no matter how long the wait. Once the limit lifts, re-run the blocked delegations FRESH (new `codex exec`, not resume). But NEVER blindly replay a modification (`<GATE_MARKER>`) delegation: the limit can hit MID-RUN, after files were already partially modified. Before replaying one you MUST (1) read `$WORK/stderr.log`/`stdout.log` to see how far the run got, (2) inspect the delegation's target paths for changes already applied, and (3) either revert the partial work and re-run the original prompt, or re-run with an amended prompt stating what is already applied. Replaying a modification delegation without this check is a protocol violation. (Read-only delegations replay fresh immediately.)
- Resume at the codex-stated time (`... try again at H:MM AM/PM`, plus a date when the reset falls on another calendar day — typical for the weekly limit) + 5 min buffer. If several bridges report different times, use the LATEST. Only if no time can be parsed, arm the same Monitor below with a far TARGET (e.g. now + 24h) and let its ~3h probes detect the reset.
- Immediately record the pending resume (datetime + blocked delegation list + the mode's active model/effort) in a durable file under `.temp_files/` (e.g. the job's ledger). Context compaction survives this automatically; a session restart does NOT — the Monitor dies with the session — so restart recovery happens at the next /model-sub-codex invocation (last bullet below).
- Waits under ~1h: chained bounded background sleeps are fine. Waits over ~1h: arm ONE persistent `Monitor` that (a) probes for an early reset every ~3h with a minimal `codex exec` pinned to `gpt-5.6-luna` + `low` (probe-only exception: a one-line probe needs no reasoning, and the 5-hour/weekly limits are account-wide pools, so any model exercises the same limit) — OpenAI sometimes lifts the weekly limit earlier than stated — and (b) otherwise fires a few minutes past the stated time (clock-skew margin), giving exactly one wake-up either way (the detached process waits, not the agent — no periodic context reloads):

  ```
  Monitor({persistent: true, description: "codex reset wait until <datetime> (+3h probes)", command: `
    TARGET=<epoch of stated reset + 5min>
    mkdir -p <project-root>/.temp_files
    PD=$(mktemp -d <project-root>/.temp_files/codex_probe_XXXXXX) || { echo CODEX_PROBE_SETUP_FAILED; exit 1; }
    while [ $(date +%s) -lt $TARGET ]; do
      R=$(( TARGET - $(date +%s) + 180 )); [ "$R" -gt 10800 ] && R=10800; sleep "$R"
      printf 'Reply with exactly: OK' > $PD/p.txt
      if codex exec - -C <workroot> -m gpt-5.6-luna -c model_reasoning_effort="low" -o $PD/out.txt < $PD/p.txt >/dev/null 2>$PD/err.log && [ -s $PD/out.txt ]; then
        echo "CODEX_LIMIT_LIFTED_EARLY $(date '+%F %T')"; exit 0
      fi
    done
    echo "CODEX_RESET_TIME_REACHED $(date '+%F %T')"`})
  ```

- On wake (either event), re-run the blocked delegations fresh with the recorded model/effort and clear the pending-resume record.
- On every /model-sub-codex invocation, first check `.temp_files/` for pending-resume records left by earlier sessions: if the recorded reset time has passed, re-run those blocked delegations fresh immediately (with the recorded model/effort); if not, re-arm the Monitor above for the remaining wait.

## Precedence and scope

- A per-request user instruction (e.g., "run this one as a normal fable subagent") beats this skill.
- Only subagent creation changes. The main agent keeps doing its own inline work directly, and every other AGENTS.md rule stays in force. Inside the delegated run, repository rules apply to codex through AGENTS.md itself (including the modification gate and `.temp_files`).
- The mode lasts until the session ends or the user switches modes — `/model-sub-claude` (any argument combination) and `/model-sub-codex` form one toggle group; the most recent invocation wins.
- Claude Code only: codex sessions never load this skill.
