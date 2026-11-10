#!/usr/bin/env python3
"""Drive a batch of codex runs to a verdict each, then print one summary.

Usage:
  python wait_codex.py --model MODEL --effort EFFORT [--workroot DIR] [--cap N] [--launch-gap S]
                       [--stall-minutes M] [--retries N] [--service-tier T] WORK [WORK ...]

The caller writes prompt.txt into each WORK (from new_workdir.py) and may add schema.json (the final message must
be a JSON object) and reply.txt (an answer or follow-up for the session after a run).

The waiter writes one folder per attempt, <n>-<kind>, numbered from 1; the highest n is the latest. Kinds: fresh
(run rules, then prompt.txt), continue (resumes the session) and reply (resumes it with reply.txt, moved into
input.txt when taken). Each folder holds input.txt (exactly what codex read on stdin), last.txt (codex's final
message), stdout.log, stderr.log, pid and exit_code. WORK/last.txt is the latest success's final message, removed
just before the next attempt launches; WORK/failed.txt holds the summary lines while the verdict is FAILED.

An attempt succeeded when exit_code is 0 and last.txt is not empty (and, with schema.json, parses as a JSON
object). Any other ending is resumed with continue when codex printed a session id (a waiting reply.txt goes out
instead, and a failed continue is not resumed again), then started fresh again up to --retries times, counted from
the fresh folders on disk. A usage limit stops new starts: the run is queued and the same command continues it after
the reset. A launch that raises fails the run for this invocation only; the next invocation starts the same folder.

--cap counts only this waiter's live runs. --launch-gap spaces starts across every waiter given it (lock file under
.temp_files/subcodex/). A run alive but silent for --stall-minutes since this invocation began ends the batch and is
left alone. Nothing is killed; all state is in the WORK dirs, so the same command picks up where it stopped. Never
hand one WORK to two waiters at once.

Summary, one entry per WORK in argument order:
  OK <WORK>/last.txt
  FAILED <WORK> <label>      then an indented report; labels MISSING_PROMPT, BAD_SCHEMA, NO_SESSION, LAUNCH_FAILED,
                             BAD_OUTPUT (exit 0, unusable output), DIED (no exit code), EXIT_<code>
  STALLED <WORK> <minutes>
  RUNNING <WORK> | QUEUED <WORK>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from launch_codex import RUN_RULES, launch
from normalize_schema import normalize_file

ROOT = Path(__file__).resolve().parents[4]
MODELS = {"astra": "gpt-6-astra", "sol": "gpt-6.1-sol", "luna": "gpt-6-luna", "terra": "gpt-6.1-terra"}
EFFORTS = ("low", "medium", "high", "xhigh", "max")
STATUSES = ("OK", "FAILED", "STALLED", "RUNNING", "QUEUED")
CONTINUE_TEXT = "Continue and finish the task.\n"
POLL_SECONDS = 15.0
STDERR_TAIL_LINES = 30
SESSION_RE = re.compile(r"^session id:\s*(\S+)", re.MULTILINE)
# Matched only against codex's own ERROR lines: stderr also echoes the task's text.
USAGE_LIMIT_RE = re.compile(r"^ERROR: .*hit your usage limit.*$", re.MULTILINE)
ATTEMPT_RE = re.compile(r"\d+-(?:fresh|continue|reply)")


@dataclass
class Verdict:
    status: str  # OK | FAILED | STALLED | RUNNING | QUEUED
    detail: str = ""
    report: list[str] = field(default_factory=list)


@dataclass
class Start:
    kind: str  # fresh | continue | reply
    attempt: Path | None = None  # an existing folder whose start never completed; None makes a new one


@dataclass
class Batch:
    works: list[Path]
    model: str
    effort: str
    workroot: Path
    cap: int
    stall_seconds: float
    started: float
    launch_gap: float = 0.0
    gap_file: Path | None = None  # holds the time of the last start by any waiter keeping the gap
    limit_hit: str = ""  # codex's usage-limit message once the account runs out
    service_tier: str | None = None  # passed to codex as service_tier, for example ultrafast
    retries: int = 0  # fresh starts allowed per run after it has failed for good
    launch_failures: dict[Path, Verdict] = field(default_factory=dict)  # failed starts, kept for this invocation


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


@contextmanager
def machine_lock(path: Path) -> Iterator[TextIO]:
    """Hold an exclusive lock on path, shared with every process on this machine; the OS drops it if we die."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        if sys.platform == "win32":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield fh
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield fh
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def read_exit_code(attempt: Path) -> int | None:
    try:
        return int((attempt / "exit_code").read_text().strip())
    except OSError, ValueError:
        return None


def read_pid(attempt: Path) -> int:
    try:
        return int((attempt / "pid").read_text().strip())
    except OSError, ValueError:
        return 0


def number_of(attempt: Path) -> int:
    return int(attempt.name.split("-", 1)[0])


def kind_of(attempt: Path) -> str:
    return attempt.name.split("-", 1)[1]


def attempts(work: Path) -> list[Path]:
    """The attempt folders of a work dir, oldest first."""
    found = [p for p in work.iterdir() if p.is_dir() and ATTEMPT_RE.fullmatch(p.name)]
    return sorted(found, key=number_of)


def activity(attempt: Path) -> float:
    """Newest modification time of anything in an attempt folder."""
    return max((p.stat().st_mtime for p in attempt.iterdir()), default=attempt.stat().st_mtime)


def session_id(work: Path) -> str | None:
    """The session id codex printed in the latest fresh attempt; every resume continues that session."""
    fresh = [a for a in attempts(work) if kind_of(a) == "fresh"]
    match = SESSION_RE.search(read_text(fresh[-1] / "stderr.log")) if fresh else None
    return match.group(1) if match else None


def output_problem(work: Path, attempt: Path) -> str | None:
    """Why the attempt's final message is unusable, or None when it is usable."""
    output = attempt / "last.txt"
    if not output.is_file() or output.stat().st_size == 0:
        return "final message missing or empty"
    if not (work / "schema.json").is_file():
        return None
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"schema run returned no valid JSON: {exc}"
    return None if isinstance(payload, dict) else f"schema run returned {type(payload).__name__}, not a JSON object"


def report(work: Path, attempt: Path, evidence: list[str]) -> list[str]:
    code = read_exit_code(attempt)
    lines = [
        f"attempt: {attempt.name}",
        f"exit_code: {code if code is not None else 'missing (the wrapper died)'}",
        f"session_id: {session_id(work) or 'none'}",
    ]
    tail = read_text(attempt / "stderr.log").splitlines()[-STDERR_TAIL_LINES:]
    return [*lines, *evidence, *(["--- stderr tail ---", *tail] if tail else [])]


def new_attempt(work: Path, kind: str) -> Path:
    attempt = work / f"{len(attempts(work)) + 1}-{kind}"
    attempt.mkdir()
    return attempt


def write_input(work: Path, attempt: Path) -> None:
    """Write what codex reads on stdin for this attempt's kind."""
    kind = kind_of(attempt)
    if kind == "fresh":
        (attempt / "input.txt").write_bytes(RUN_RULES.encode() + (work / "prompt.txt").read_bytes())
    elif kind == "continue":
        (attempt / "input.txt").write_text(CONTINUE_TEXT, encoding="utf-8")
    elif not (attempt / "input.txt").exists():
        # reply.txt is consumed by the first start; a restarted folder keeps the reply it already holds.
        (work / "reply.txt").replace(attempt / "input.txt")


def evaluate(batch: Batch, work: Path, now: float) -> Verdict | Start:
    """The verdict for a work dir as its files stand, or the attempt it needs started."""
    if not (work / "prompt.txt").is_file():
        return Verdict("FAILED", "MISSING_PROMPT", [f"no prompt.txt in {work}"])
    folders = attempts(work)
    if not folders:
        return Start("fresh")
    latest = folders[-1]
    code = read_exit_code(latest)
    # No pid and no exit code: the start never completed (the waiter died or the launch raised), so restart in place.
    if code is None and not (latest / "pid").is_file():
        return Start(kind_of(latest), latest)
    if code is None and pid_alive(read_pid(latest)):
        quiet_since = activity(latest)
        if batch.stall_seconds and now - max(quiet_since, batch.started) >= batch.stall_seconds:
            return Verdict("STALLED", str(int((now - quiet_since) // 60)))
        return Verdict("RUNNING")
    problem = output_problem(work, latest) if code == 0 else None
    if code == 0 and problem is None:
        # start() removes last.txt before every launch, so an existing copy is the latest success's: keep it.
        if not (work / "last.txt").exists():
            shutil.copyfile(latest / "last.txt", work / "last.txt.tmp")
            (work / "last.txt.tmp").replace(work / "last.txt")
        if (work / "reply.txt").is_file():
            return Start("reply")
        return Verdict("OK", str(work / "last.txt"))
    sid = session_id(work)
    limit = USAGE_LIMIT_RE.search(read_text(latest / "stderr.log"))
    if limit is not None:
        if activity(latest) >= batch.started:
            batch.limit_hit = limit.group(0)
        return Start("continue" if sid else "fresh")
    if sid and (work / "reply.txt").is_file():
        return Start("reply")
    if sid and kind_of(latest) != "continue":
        return Start("continue")
    if sum(kind_of(a) == "fresh" for a in folders) - 1 < batch.retries:
        return Start("fresh")
    label = "DIED" if code is None else "BAD_OUTPUT" if code == 0 else f"EXIT_{code}"
    return Verdict("FAILED", label, report(work, latest, [] if problem is None else [f"problem: {problem}"]))


def start(batch: Batch, work: Path, request: Start) -> Verdict:
    """Create or reuse the requested attempt folder, write its input and launch it."""
    schema = work / "schema.json"
    has_schema = schema.is_file()
    if request.kind == "fresh" and has_schema:
        try:
            normalize_file(schema)
        except (OSError, ValueError) as exc:
            return Verdict("FAILED", "BAD_SCHEMA", [str(exc)])
    resume = None
    if request.kind != "fresh":
        resume = session_id(work)
        if resume is None:
            return Verdict(
                "FAILED", "NO_SESSION", ["the latest fresh attempt's stderr.log has no session id to resume"]
            )
    attempt = new_attempt(work, request.kind) if request.attempt is None else request.attempt
    try:
        write_input(work, attempt)
    except OSError as exc:
        return Verdict("FAILED", "LAUNCH_FAILED", [str(exc)])
    # Only now, so an older success stays visible until the new attempt really starts.
    (work / "last.txt").unlink(missing_ok=True)
    (work / "failed.txt").unlink(missing_ok=True)
    try:
        launch(
            attempt,
            batch.workroot,
            batch.model,
            batch.effort,
            schema=schema if has_schema else None,
            resume=resume,
            service_tier=batch.service_tier,
        )
    except OSError as exc:
        return Verdict("FAILED", "LAUNCH_FAILED", [str(exc)])
    return Verdict("RUNNING")


def start_waiting(batch: Batch, waiting: list[tuple[Path, Start]], slots: int, verdicts: dict[Path, Verdict]) -> int:
    """Start waiting runs while slots last, queue the rest, and return how many started."""
    started = 0
    for work, request in waiting:
        if batch.limit_hit or slots <= 0:
            verdicts[work] = Verdict("QUEUED")
            continue
        verdict = start(batch, work, request)
        verdicts[work] = verdict
        if verdict.status == "FAILED":
            # Kept for this invocation, so the same start is not retried on every poll.
            batch.launch_failures[work] = verdict
        elif verdict.status == "RUNNING":
            slots -= 1
            started += 1
    return started


def entry(work: Path, verdict: Verdict) -> list[str]:
    """The summary lines of one run."""
    if verdict.status == "OK":
        return [f"OK {verdict.detail}"]
    head = " ".join(part for part in (verdict.status, str(work), verdict.detail) if part)
    return [head, *(f"    {line}" for line in verdict.report)]


def mark_failed(work: Path, verdict: Verdict) -> None:
    """Keep <WORK>/failed.txt present exactly while the run's verdict is FAILED, whatever produced it."""
    if not work.is_dir():
        return
    failed_file = work / "failed.txt"
    if verdict.status != "FAILED":
        failed_file.unlink(missing_ok=True)
        return
    text = "\n".join(entry(work, verdict)) + "\n"
    if read_text(failed_file) != text:
        failed_file.write_text(text, encoding="utf-8")


def step(batch: Batch, now: float) -> dict[Path, Verdict]:
    verdicts: dict[Path, Verdict] = {}
    waiting: list[tuple[Path, Start]] = []
    for work in batch.works:
        remembered = batch.launch_failures.get(work)
        result = remembered if remembered is not None else evaluate(batch, work, now)
        if isinstance(result, Start):
            waiting.append((work, result))
        else:
            verdicts[work] = result
    busy = sum(v.status in ("RUNNING", "STALLED") for v in verdicts.values())
    if batch.launch_gap and batch.gap_file and waiting and not batch.limit_hit:
        # Counting and starting under one machine-wide lock keeps waiters within the cap together.
        with machine_lock(batch.gap_file) as stamp:
            stamp.seek(0)
            last = float(stamp.read().strip() or 0)
            slots = min(1, batch.cap - busy) if time.time() - last >= batch.launch_gap else 0
            if start_waiting(batch, waiting, slots, verdicts):
                stamp.seek(0)
                stamp.truncate()
                stamp.write(f"{time.time()}\n")
                stamp.flush()
    else:
        start_waiting(batch, waiting, batch.cap - busy if waiting and not batch.limit_hit else 0, verdicts)
    for work, verdict in verdicts.items():
        mark_failed(work, verdict)
    return verdicts


def finished(batch: Batch, verdicts: dict[Path, Verdict]) -> bool:
    statuses = {v.status for v in verdicts.values()}
    if "STALLED" in statuses:
        return True
    if batch.limit_hit:
        return "RUNNING" not in statuses
    return statuses <= {"OK", "FAILED"}


def summary(batch: Batch, verdicts: dict[Path, Verdict]) -> str:
    counts = Counter(v.status for v in verdicts.values())
    lines = ["batch: " + ", ".join(f"{counts[s]} {s.lower()}" for s in STATUSES)]
    if batch.limit_hit:
        lines.append(f"usage limit: no new runs started; run the same command after the reset. {batch.limit_hit}")
    for work in batch.works:
        lines += entry(work, verdicts[work])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Drive codex runs to a verdict each.")
    parser.add_argument("--model", type=model_arg, required=True)
    parser.add_argument("--effort", type=effort_arg, required=True)
    parser.add_argument("--workroot", type=Path, default=None, help="codex's working directory (default: repo root)")
    parser.add_argument("--cap", type=int, default=64, help="runs of this waiter that may be live at once")
    parser.add_argument(
        "--launch-gap", type=float, default=0.0, help="minimum seconds between starts across waiters given this option"
    )
    parser.add_argument("--stall-minutes", type=float, default=22.0, help="0 waits forever")
    parser.add_argument(
        "--service-tier", default=None, help="codex service tier, such as ultrafast; a model that lacks it omits it"
    )
    parser.add_argument(
        "--retries", type=int, default=0, help="fresh starts per run after it has failed for good, counted from disk"
    )
    parser.add_argument("work", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if args.cap < 1 or args.stall_minutes < 0 or args.launch_gap < 0 or args.retries < 0:
        parser.error("--cap must be at least 1, --launch-gap, --stall-minutes and --retries at least 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    batch = Batch(
        works=list(dict.fromkeys(w.resolve() for w in args.work)),
        model=args.model,
        effort=args.effort,
        workroot=(args.workroot or ROOT).resolve(),
        cap=args.cap,
        stall_seconds=args.stall_minutes * 60,
        started=time.time(),
        launch_gap=args.launch_gap,
        gap_file=ROOT / ".temp_files" / "subcodex" / ".launch_gap",
        retries=args.retries,
        service_tier=args.service_tier,
    )
    while True:
        verdicts = step(batch, time.time())
        if finished(batch, verdicts):
            break
        time.sleep(min(POLL_SECONDS, batch.launch_gap) if batch.launch_gap else POLL_SECONDS)
    print(summary(batch, verdicts))
    return 0 if all(v.status == "OK" for v in verdicts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
