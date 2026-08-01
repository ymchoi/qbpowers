#!/usr/bin/env python3
"""Launch one codex exec run detached, with a pid + exit-code sentinel.

Usage:
  python launch_codex.py <WORK> <WORKROOT> <MODEL> <EFFORT> [--schema] [--resume SESSION_ID]

Fresh runs read <WORK>/prompt.txt and write last.txt / stdout.log /
stderr.log / exit_code / pid. --resume marks the single recovery attempt and
rejects an empty session id rather than silently downgrading to a fresh run:
it reads prompt2.txt and writes the same set with a "2" suffix, leaving the
first attempt's files untouched as evidence.

The parent re-invokes this file with --wrapper as a detached process
(start_new_session on POSIX, DETACHED_PROCESS on Windows), records the
wrapper pid, and returns immediately. The wrapper blocks on codex and writes
the exit code when it finishes — that file appearing is the only completion
signal poll_codex.py trusts.

codex always receives -m/-c model_reasoning_effort explicitly (the mode
resolves them; codex never falls back to its local defaults here) and
-c agents.enabled=false is fixed: bridges have no fan-out below the
orchestrator. cwd is set to WORKROOT for both fresh and resume runs, which
replaces -C and sidesteps `codex exec resume` not accepting it.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_codex_argv(args: argparse.Namespace, suffix: str, work: Path) -> list[str]:
    codex = shutil.which("codex")
    if codex is None:
        raise FileNotFoundError("codex CLI not found on PATH")
    argv = [codex, "exec"]
    if args.resume:
        argv += ["resume", args.resume]
    argv += [
        "-",
        "-m",
        args.model,
        "-c",
        f"model_reasoning_effort={args.effort}",
        "-c",
        "agents.enabled=false",
    ]
    if args.schema:
        argv += ["--output-schema", str(work / "schema.json")]
    argv += ["-o", str(work / f"last{suffix}.txt")]
    return argv


def run_wrapper(args: argparse.Namespace) -> int:
    """Blocking half: run codex with redirections, then write the sentinel."""
    work = Path(args.work)
    suffix = "2" if args.resume else ""
    argv = build_codex_argv(args, suffix, work)
    prompt = work / f"prompt{suffix}.txt"
    with (
        open(prompt, "rb") as stdin,
        open(work / f"stdout{suffix}.log", "wb") as stdout,
        open(work / f"stderr{suffix}.log", "wb") as stderr,
    ):
        try:
            rc = subprocess.run(
                argv,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                cwd=args.workroot,
                check=False,
            ).returncode
        except OSError as exc:
            stderr.write(f"launch_codex.py wrapper: {exc}\n".encode())
            rc = 127
    (work / f"exit_code{suffix}").write_text(f"{rc}\n", encoding="utf-8")
    return 0


def spawn_detached(args: argparse.Namespace, raw_argv: list[str]) -> int:
    work = Path(args.work)
    suffix = "2" if args.resume else ""
    prompt = work / f"prompt{suffix}.txt"
    if not prompt.is_file():
        print(f"launch_codex.py: missing {prompt}", file=sys.stderr)
        return 2
    if args.schema and not (work / "schema.json").is_file():
        print(f"launch_codex.py: missing {work / 'schema.json'}", file=sys.stderr)
        return 2
    build_codex_argv(args, suffix, work)  # fail loud now if codex is absent

    wrapper_argv = [sys.executable, str(Path(__file__).resolve()), "--wrapper", *raw_argv]
    kwargs: dict[str, object] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        detached = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        new_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        kwargs["creationflags"] = detached | new_group
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(wrapper_argv, **kwargs)  # type: ignore[call-overload]
    (work / f"pid{suffix}").write_text(f"{proc.pid}\n", encoding="utf-8")
    print(f"LAUNCHED attempt={'2' if args.resume else '1'} pid={proc.pid}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wrapper", action="store_true", help="internal: blocking child mode")
    parser.add_argument("work")
    parser.add_argument("workroot")
    parser.add_argument("model")
    parser.add_argument("effort")
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--resume", metavar="SESSION_ID", default=None)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.resume is not None and not args.resume.strip():
        print("launch_codex.py: --resume requires a non-empty session id", file=sys.stderr)
        return 2
    if args.wrapper:
        return run_wrapper(args)
    raw = [a for a in argv if a != "--wrapper"]
    return spawn_detached(args, raw)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
