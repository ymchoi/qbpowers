#!/usr/bin/env python3
"""Drive one codex delegation to a terminal verdict.

Usage: python run_codex.py <WORK> <MODEL> <EFFORT> [--schema] [--workroot DIR]

Prints exactly one of:
  RUNNING      codex is still working — call again with the same arguments
  OK <file>    success; <file> is the relay copy, work_dir already correct
  FAILED       followed by a report block the bridge relays verbatim

The relay copy exists because "overwrite work_dir with your own path" used to
be prose, and 16% of otherwise-compliant bridges passed codex's value through
instead — indistinguishable, downstream, from having skipped codex entirely.

Every branch the bridge procedure used to spell out in prose lives here
instead: launching, polling, classifying a failure, and the single resume
attempt. Prose made the relay model the control-flow engine, which is exactly
where bridges went off-protocol; code cannot be skipped the way a step can.

All state lives in <WORK>, so repeated invocations pick up where the previous
one stopped and codex is never launched twice for the same attempt.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from _paths import SCRIPTS_DIR, repo_root

SESSION_RE = re.compile(r"^session id:\s*(\S+)", re.MULTILINE)
MARKER = "<GATE_MARKER>"
STDERR_TAIL_LINES = 30


def _script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / name), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def launch(
    work: Path,
    workroot: Path,
    model: str,
    effort: str,
    schema: bool,
    resume: str | None,
) -> subprocess.CompletedProcess[str]:
    """Spawn one codex attempt — the only side effect that reaches the network."""
    args = [str(work), str(workroot), model, effort]
    if schema:
        args.append("--schema")
    if resume:
        args += ["--resume", resume]
    return _script("launch_codex.py", *args)


def poll(work: Path, attempt: int) -> str:
    args = [str(work), *(["2"] if attempt == 2 else [])]
    out = _script("poll_codex.py", *args).stdout.strip()
    return out.splitlines()[0] if out else "CRASHED"


def diagnose(work: Path, attempt: int, schema: bool) -> list[str]:
    args = [str(work), *(["2"] if attempt == 2 else []), *(["--schema"] if schema else [])]
    return _script("diagnose_codex.py", *args).stdout.splitlines()


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _suffix(attempt: int) -> str:
    return "2" if attempt == 2 else ""


def current_attempt(work: Path) -> int:
    """0 = not launched yet. A pid sentinel is what makes a relaunch impossible."""
    if (work / "pid2").is_file():
        return 2
    if (work / "pid").is_file():
        return 1
    return 0


def exit_code(work: Path, attempt: int) -> int | None:
    try:
        return int((work / f"exit_code{_suffix(attempt)}").read_text().strip())
    except OSError, ValueError:
        return None


def succeeded(work: Path, attempt: int) -> bool:
    if exit_code(work, attempt) != 0:
        return False
    try:
        return (work / f"last{_suffix(attempt)}.txt").stat().st_size > 0
    except OSError:
        return False


def session_id(work: Path) -> str | None:
    m = SESSION_RE.search(_text(work / "stderr.log"))
    return m.group(1) if m else None


def write_relay(work: Path, attempt: int, schema: bool) -> Path:
    """Copy codex's output with work_dir already set, so the bridge only copies.

    Raises ValueError if a schema run produced something that is not a JSON
    object; --output-schema should make that impossible, so it is a real fault.
    """
    source = (work / f"last{_suffix(attempt)}.txt").read_text(encoding="utf-8")
    if not schema:
        relay = work / "relay.txt"
        relay.write_text(f"{source.rstrip()}\n\nwork_dir={work}\n", encoding="utf-8")
        return relay
    payload = json.loads(source)
    if not isinstance(payload, dict):
        raise ValueError(f"schema run returned {type(payload).__name__}, not a JSON object")
    payload["work_dir"] = str(work)
    relay = work / "relay.json"
    relay.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return relay


def report(work: Path, attempt: int, kind: str, evidence: list[str], authorized: bool, note: str = "") -> str:
    code = exit_code(work, attempt)
    lines = [
        f"BRIDGE_FAILURE: codex delegation failed on attempt {attempt} ({kind})",
        f"work_dir: {work}",
        f"exit_code: {code if code is not None else 'missing — the wrapper crashed'}",
        f"session_id: {session_id(work) or 'none'}",
    ]
    if authorized:
        lines.append(
            "WARNING: this delegation was authorized to modify files. Inspect this work "
            "dir's logs and the delegation's target paths for changes already applied "
            "before replaying, rather than re-delegating blindly."
        )
    if note:
        lines.append(note)
    if evidence:
        lines += ["--- diagnosis ---", *evidence]
    tail = _text(work / f"stderr{_suffix(attempt)}.log").splitlines()[-STDERR_TAIL_LINES:]
    if tail:
        lines += ["--- stderr tail ---", *tail]
    return "\n".join(lines)


def fail(work: Path, attempt: int, kind: str, evidence: list[str], authorized: bool, note: str = "") -> int:
    print("FAILED")
    print(report(work, attempt, kind, evidence, authorized, note))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("work")
    parser.add_argument("model")
    parser.add_argument("effort")
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--workroot", default=None)
    # Declared, never sniffed: prompts routinely say "no <GATE_MARKER> marker is present",
    # and a substring test read those as authorization for the resume prompt.
    parser.add_argument("--authorized", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    work = Path(args.work).resolve()
    if not work.is_dir():
        print("FAILED")
        print(f"BRIDGE_FAILURE: work dir does not exist: {work}")
        return 0
    workroot = Path(args.workroot).resolve() if args.workroot else repo_root()

    attempt = current_attempt(work)
    if attempt == 0:
        if args.schema:
            norm = _script("normalize_schema.py", str(work / "schema.json"))
            if norm.returncode != 0:
                return fail(work, 1, "SCHEMA_NORMALIZE_FAILED", norm.stderr.splitlines(), args.authorized)
        started = launch(work, workroot, args.model, args.effort, args.schema, None)
        if started.returncode != 0:
            return fail(work, 1, "LAUNCH_FAILED", started.stderr.splitlines(), args.authorized)
        attempt = 1

    if poll(work, attempt) == "RUNNING":
        print("RUNNING")
        return 0
    if succeeded(work, attempt):
        try:
            print(f"OK {write_relay(work, attempt, args.schema)}")
        except (OSError, ValueError) as exc:
            return fail(work, attempt, "UNUSABLE_OUTPUT", [str(exc)], args.authorized)
        return 0

    lines = diagnose(work, attempt, args.schema)
    kind = lines[0] if lines else "NONE"
    evidence = lines[1:]

    # One recovery attempt, and only for an unclassified failure: a full session
    # or a rejected schema would fail identically on resume.
    if attempt != 1 or kind != "NONE":
        return fail(work, attempt, kind, evidence, args.authorized)

    sid = session_id(work)
    if sid is None:
        return fail(
            work,
            1,
            kind,
            evidence,
            args.authorized,
            "codex never started: stderr.log carries no session id, so no resume is possible.",
        )
    # A resume is a NEW prompt, so the modification gate must be re-passed with
    # exactly the original authorization.
    head = f"{MARKER} — " if args.authorized else ""
    (work / "prompt2.txt").write_text(f"{head}Continue and finish the task.\n", encoding="utf-8")
    resumed = launch(work, workroot, args.model, args.effort, args.schema, sid)
    if resumed.returncode != 0:
        return fail(work, 1, "RESUME_LAUNCH_FAILED", resumed.stderr.splitlines(), args.authorized)
    print("RUNNING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
