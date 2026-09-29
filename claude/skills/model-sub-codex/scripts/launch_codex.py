#!/usr/bin/env python3
"""Start one codex exec attempt detached from its caller, with pid and exit-code sentinels.

A fresh attempt feeds codex RUN_RULES + <WORK>/prompt.txt and writes input.txt,
last.txt, stdout.log, stderr.log, pid and exit_code in <WORK>. The one resume
attempt feeds prompt2.txt to `codex exec resume <SESSION_ID>` and writes the
same files with a "2" suffix, leaving the first attempt's files as evidence.

The attempt is detached (start_new_session on POSIX, CREATE_NO_WINDOW on
Windows) so it outlives whatever launched it, and exit_code, written by the
wrapper once codex exits, is the only completion signal.

wait_codex.py calls launch(); the process that starts re-enters this file as
  python launch_codex.py --wrapper <WORK> <WORKROOT> <MODEL> <EFFORT> [--schema] [--resume SESSION_ID]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Never put the modification-gate marker in here: codex reads its mere presence
# as authorization.
RUN_RULES = "\n".join(
    (
        "[Run rules, set by the orchestrator that launched you. Where they conflict with AGENTS.md, these win.]",
        "- You are a delegated worker, not an orchestrator: do the task below yourself, one step after another.",
        "  Never spawn sub-agents or parallel workers (spawn_agent or any other delegation tool), and never start",
        "  another codex process from the shell, even where an AGENTS.md file or the task asks for parallel work.",
        "- Never kill a process you did not start; the python and shell processes waiting for you are expected.",
        "- Search narrowly: give rg a target path and -j2, give find a -maxdepth, never search .temp_files/ or the",
        "  whole repository, and open known paths directly instead of searching for them.",
        "- Put scratch and output files under .temp_files/; AGENTS.md's modification gate does not apply there.",
        "",
        "[Task]",
        "",
    )
)


def codex_argv(codex: str, work: Path, model: str, effort: str, schema: bool, resume: str | None) -> list[str]:
    argv = [codex, "exec", *(["resume", resume] if resume else []), "-", "-m", model]
    # GPT-6 models keep their multi-agent instructions even with both features off,
    # which is why RUN_RULES forbids sub-agents as well and wait_codex.py counts them.
    argv += ["-c", f"model_reasoning_effort={effort}", "--disable", "multi_agent", "--disable", "multi_agent_v2"]
    if schema:
        argv += ["--output-schema", str(work / "schema.json")]
    return [*argv, "-o", str(work / f"last{'2' if resume else ''}.txt")]


def find_codex() -> str:
    codex = shutil.which("codex")
    if codex is None:
        raise FileNotFoundError("codex CLI not found on PATH")
    return codex


def launch(work: Path, workroot: Path, model: str, effort: str, *, schema: bool, resume: str | None = None) -> int:
    """Start one attempt and return the wrapper pid; raises OSError when it cannot start."""
    suffix = "2" if resume else ""
    find_codex()  # fail here, where the caller can report it, rather than inside the detached wrapper
    prompt = (work / f"prompt{suffix}.txt").read_bytes()
    (work / f"input{suffix}.txt").write_bytes(prompt if resume else RUN_RULES.encode() + prompt)

    wrapper = [sys.executable, str(Path(__file__).resolve()), "--wrapper", str(work), str(workroot), model, effort]
    wrapper += [*(["--schema"] if schema else []), *(["--resume", resume] if resume else [])]
    if os.name == "nt":
        # Not DETACHED_PROCESS: without a console of its own to inherit, codex would
        # allocate a fresh one, which Windows Terminal draws as a real window.
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
        )
        proc = subprocess.Popen(
            wrapper,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    else:
        proc = subprocess.Popen(
            wrapper,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    (work / f"pid{suffix}").write_text(f"{proc.pid}\n", encoding="utf-8")
    return proc.pid


def run_wrapper(args: argparse.Namespace) -> int:
    """Blocking half: run codex with redirections, then write the exit-code sentinel."""
    work = Path(args.work)
    suffix = "2" if args.resume else ""
    with (
        open(work / f"input{suffix}.txt", "rb") as stdin,
        open(work / f"stdout{suffix}.log", "wb") as stdout,
        open(work / f"stderr{suffix}.log", "wb") as stderr,
    ):
        try:
            argv = codex_argv(find_codex(), work, args.model, args.effort, args.schema, args.resume)
            code = subprocess.run(argv, stdin=stdin, stdout=stdout, stderr=stderr, cwd=args.workroot).returncode
        except OSError as exc:
            stderr.write(f"launch_codex.py wrapper: {exc}\n".encode())
            code = 127
    (work / f"exit_code{suffix}").write_text(f"{code}\n", encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wrapper", action="store_true", required=True)
    parser.add_argument("work")
    parser.add_argument("workroot")
    parser.add_argument("model")
    parser.add_argument("effort")
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--resume", default=None)
    return run_wrapper(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
