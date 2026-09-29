#!/usr/bin/env python3
"""Drive a batch of codex runs to a verdict each, then print one summary.

Usage:
  python wait_codex.py --model MODEL --effort EFFORT [--authorized] [--workroot DIR]
                       [--cap N] [--stall-minutes M] WORK [WORK ...]

Each WORK (from new_workdir.py) holds prompt.txt and, for a JSON result,
schema.json. Runs start while fewer than --cap `codex exec` processes are alive
on this machine, counting every session's, and the rest wait their turn. A run
that fails for an unclassified reason is resumed once. The batch ends when every
run has a verdict, when a run has been silent for --stall-minutes since this
invocation began, or, once the account hits its usage limit, when nothing is
left running; a run the limit stopped is set aside and queued again. Nothing is
ever killed and all state lives in the WORK dirs, so the same command picks up
where the last one stopped and never starts a run twice. Never hand one WORK to
two waiters at once.

Summary, one entry per WORK in argument order:
  OK <file>                        codex's final message (a JSON object when schema.json exists)
  FAILED <WORK> <kind>             followed by an indented report
  STALLED <WORK> <minutes>         alive but silent; left running
  RUNNING <WORK> | QUEUED <WORK>   not finished when the batch stopped early
  SPAWNED <WORK> <n>               codex spawned sub-agents despite the run rules
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from _paths import repo_root
from diagnose_codex import diagnose, read_exit_code
from launch_codex import launch
from normalize_schema import normalize_file

MODELS = {"astra": "gpt-6-astra", "sol": "gpt-6-sol", "luna": "gpt-6-luna"}
EFFORTS = ("low", "medium", "high", "xhigh", "max")
MARKER = "<GATE_MARKER>"
POLL_SECONDS = 15.0
STDERR_TAIL_LINES = 30
SESSION_RE = re.compile(r"^session id:\s*(\S+)", re.MULTILINE)
# A command line whose program is codex or codex.exe (bare, pathed or quoted) running `exec`.
CODEX_EXEC_RE = re.compile(r'^\s*(?:"[^"]*[/\\])?(?:[^"\s]*[/\\])?codex(?:\.exe)?"?\s+exec(?:\s|$)')
# No double quotes inside: they would need escaping on the way through the Windows command line.
WINDOWS_LISTING = "Get-CimInstance Win32_Process -Filter 'Name like ''codex%''' | ForEach-Object { $_.CommandLine }"


@dataclass
class Verdict:
    status: str  # OK | FAILED | STALLED | RUNNING | QUEUED
    detail: str = ""
    report: list[str] = field(default_factory=list)


@dataclass
class Start:
    resume: str | None = None  # the session id when this is the one resume attempt


@dataclass
class Batch:
    works: list[Path]
    model: str
    effort: str
    authorized: bool
    workroot: Path
    cap: int
    stall_seconds: float
    started: float
    limit_hit: str = ""  # codex's usage-limit message once the account runs out
    launch_failures: dict[Path, Verdict] = field(default_factory=dict)


def model_arg(value: str) -> str:
    name = value.strip().lower()
    if name in MODELS.values():
        return name
    if name in MODELS:
        return MODELS[name]
    raise argparse.ArgumentTypeError(f"choose from {', '.join(MODELS)} (or {', '.join(MODELS.values())})")


def effort_arg(value: str) -> str:
    effort = value.strip().lower()
    if effort not in EFFORTS:
        raise argparse.ArgumentTypeError(f"choose from {', '.join(EFFORTS)}")
    return effort


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        # attr-defined fires on POSIX, where windll is absent; unused-ignore keeps the
        # same line clean on Windows, where it is defined.
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined,unused-ignore]
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    # Signal 0 only probes on POSIX; on Windows it would terminate the target.
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def live_codex_runs() -> int | None:
    """`codex exec` processes alive on this machine from any session; None when they cannot be listed."""
    if os.name == "nt":
        command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_LISTING]
    else:
        command = ["ps", "-A", "-o", "command="]
    try:
        listing = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60).stdout
    except OSError, subprocess.SubprocessError:
        return None
    return sum(1 for line in listing.splitlines() if CODEX_EXEC_RE.match(line))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def session_id(work: Path) -> str | None:
    match = SESSION_RE.search(read_text(work / "stderr.log"))
    return match.group(1) if match else None


def read_pid(work: Path, suffix: str) -> int:
    try:
        return int((work / f"pid{suffix}").read_text().strip())
    except OSError, ValueError:
        return 0


def attempt_files(suffix: str) -> tuple[str, ...]:
    return (f"pid{suffix}", f"exit_code{suffix}", f"input{suffix}.txt", f"last{suffix}.txt")


def set_aside(work: Path, suffix: str) -> None:
    """Move an attempt the usage limit stopped out of the way, so the next invocation starts it again."""
    aside = work / f"usage_limit_{time.strftime('%Y%m%d_%H%M%S')}_attempt{suffix or '1'}"
    aside.mkdir(exist_ok=True)
    for name in (*attempt_files(suffix), f"stdout{suffix}.log", f"stderr{suffix}.log"):
        if (work / name).exists():
            (work / name).replace(aside / name)


def output_problem(output: Path, schema: bool) -> str | None:
    """Why codex's final message is unusable, or None when it is fine."""
    if not schema:
        return None
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"schema run returned no valid JSON: {exc}"
    return None if isinstance(payload, dict) else f"schema run returned {type(payload).__name__}, not a JSON object"


def report(batch: Batch, work: Path, attempt: int, evidence: list[str], note: str = "") -> list[str]:
    suffix = "2" if attempt == 2 else ""
    code = read_exit_code(work, suffix)
    lines = [
        f"attempt: {attempt}",
        f"exit_code: {code if code is not None else 'missing (the wrapper died)'}",
        f"session_id: {session_id(work) or 'none'}",
    ]
    if batch.authorized:
        lines.append(
            "WARNING: this run was authorized to modify files; check its targets for changes "
            "already applied before rerunning it."
        )
    if note:
        lines.append(note)
    if evidence:
        lines += ["--- diagnosis ---", *evidence]
    tail = read_text(work / f"stderr{suffix}.log").splitlines()[-STDERR_TAIL_LINES:]
    if tail:
        lines += ["--- stderr tail ---", *tail]
    return lines


def evaluate(batch: Batch, work: Path, now: float) -> Verdict | Start:
    if not (work / "prompt.txt").is_file():
        return Verdict("FAILED", "MISSING_PROMPT", [f"no prompt.txt in {work}"])
    attempt = 2 if (work / "pid2").is_file() else 1 if (work / "pid").is_file() else 0
    if attempt == 0:
        return Start()
    suffix = "2" if attempt == 2 else ""
    code = read_exit_code(work, suffix)
    if code is None and pid_alive(read_pid(work, suffix)):
        last_activity = max((p.stat().st_mtime for p in work.iterdir()), default=work.stat().st_mtime)
        if batch.stall_seconds and now - max(last_activity, batch.started) >= batch.stall_seconds:
            return Verdict("STALLED", str(int((now - last_activity) // 60)))
        return Verdict("RUNNING")

    schema = (work / "schema.json").is_file()
    output = work / f"last{suffix}.txt"
    if code == 0 and output.is_file() and output.stat().st_size > 0:
        problem = output_problem(output, schema)
        if problem is None:
            return Verdict("OK", str(output))
        return Verdict("FAILED", "UNUSABLE_OUTPUT", report(batch, work, attempt, [problem]))

    kind, evidence = diagnose(work, suffix, schema)
    if kind == "USAGE_LIMIT":
        batch.limit_hit = evidence[0]
        set_aside(work, suffix)
        return evaluate(batch, work, now)
    if attempt == 2 or kind != "NONE":
        return Verdict("FAILED", kind, report(batch, work, attempt, evidence))
    sid = session_id(work)
    if sid is None:
        note = "codex never started: stderr.log carries no session id, so it cannot be resumed."
        return Verdict("FAILED", kind, report(batch, work, attempt, evidence, note))
    return Start(resume=sid)


def start(batch: Batch, work: Path, pending: Start) -> Verdict:
    schema = (work / "schema.json").is_file()
    if pending.resume:
        head = f"{MARKER} — " if batch.authorized else ""
        (work / "prompt2.txt").write_text(f"{head}Continue and finish the task.\n", encoding="utf-8")
    elif schema:
        try:
            normalize_file(work / "schema.json")
        except (OSError, ValueError) as exc:
            return Verdict("FAILED", "SCHEMA_NORMALIZE_FAILED", [str(exc)])
    try:
        launch(work, batch.workroot, batch.model, batch.effort, schema=schema, resume=pending.resume)
    except OSError as exc:
        return Verdict("FAILED", "RESUME_LAUNCH_FAILED" if pending.resume else "LAUNCH_FAILED", [str(exc)])
    return Verdict("RUNNING")


def step(batch: Batch, now: float) -> dict[Path, Verdict]:
    verdicts: dict[Path, Verdict] = {}
    waiting: list[tuple[Path, Start]] = []
    for work in batch.works:
        result = batch.launch_failures.get(work) or evaluate(batch, work, now)
        if isinstance(result, Start):
            waiting.append((work, result))
        else:
            verdicts[work] = result
    busy = sum(v.status in ("RUNNING", "STALLED") for v in verdicts.values())
    live = live_codex_runs() if waiting and not batch.limit_hit else None
    slots = batch.cap - max(busy, live or 0)
    for work, pending in waiting:
        if batch.limit_hit or slots <= 0:
            verdicts[work] = Verdict("QUEUED")
            continue
        verdict = start(batch, work, pending)
        if verdict.status == "FAILED":
            batch.launch_failures[work] = verdict
        else:
            slots -= 1
        verdicts[work] = verdict
    return verdicts


def finished(batch: Batch, verdicts: dict[Path, Verdict]) -> bool:
    statuses = {v.status for v in verdicts.values()}
    if "STALLED" in statuses:
        return True
    if batch.limit_hit:
        return "RUNNING" not in statuses
    return statuses <= {"OK", "FAILED"}


def spawned_agents(work: Path) -> int:
    """spawn_agent calls in the codex session log of this run."""
    sid = session_id(work)
    if sid is None:
        return 0
    sessions = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    count = 0
    for rollout in sessions.glob(f"*/*/*/rollout-*{sid}.jsonl"):
        with rollout.open(encoding="utf-8", errors="replace") as fh:
            count += sum('"type":"function_call"' in line and '"name":"spawn_agent"' in line for line in fh)
    return count


def summary(batch: Batch, verdicts: dict[Path, Verdict]) -> str:
    counts = Counter(v.status for v in verdicts.values())
    statuses = ("OK", "FAILED", "STALLED", "RUNNING", "QUEUED")
    lines = ["batch: " + ", ".join(f"{counts[s]} {s.lower()}" for s in statuses)]
    if batch.limit_hit:
        lines.append(f"usage limit: no new runs started; run the same command after the reset. {batch.limit_hit}")
    for work in batch.works:
        verdict = verdicts[work]
        if verdict.status == "OK":
            lines.append(f"OK {verdict.detail}")
        else:
            lines.append(" ".join(part for part in (verdict.status, str(work), verdict.detail) if part))
        lines += [f"    {line}" for line in verdict.report]
        if verdict.status in ("OK", "FAILED"):
            spawned = spawned_agents(work)
            if spawned:
                lines.append(f"SPAWNED {work} {spawned}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Drive codex runs to a verdict each.")
    parser.add_argument("--model", type=model_arg, required=True)
    parser.add_argument("--effort", type=effort_arg, required=True)
    parser.add_argument("--authorized", action="store_true", help="the prompts carry the modification-gate marker")
    parser.add_argument("--workroot", type=Path, default=None, help="codex's working directory (default: repo root)")
    parser.add_argument("--cap", type=int, default=32, help="live codex exec processes allowed on this machine")
    parser.add_argument("--stall-minutes", type=float, default=22.0, help="0 waits forever")
    parser.add_argument("work", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if args.cap < 1 or args.stall_minutes < 0:
        parser.error("--cap must be at least 1 and --stall-minutes at least 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    batch = Batch(
        works=list(dict.fromkeys(w.resolve() for w in args.work)),
        model=args.model,
        effort=args.effort,
        authorized=args.authorized,
        workroot=(args.workroot or repo_root()).resolve(),
        cap=args.cap,
        stall_seconds=args.stall_minutes * 60,
        started=time.time(),
    )
    while True:
        verdicts = step(batch, time.time())
        if finished(batch, verdicts):
            break
        time.sleep(POLL_SECONDS)
    print(summary(batch, verdicts))
    return 0 if all(v.status == "OK" for v in verdicts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
