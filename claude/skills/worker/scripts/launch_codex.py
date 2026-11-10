#!/usr/bin/env python3
"""Start one codex exec attempt detached from its caller, with pid and exit-code sentinels.

wait_codex.py fills an attempt folder <WORK>/<n>-<kind>/ with input.txt, the exact bytes codex reads on stdin.
launch() starts a detached wrapper that runs codex on it and writes last.txt, stdout.log, stderr.log and, once
codex exits, exit_code; launch() writes pid. exit_code is the only completion signal, and the wrapper writes 127
when codex cannot be started.

The attempt is detached (start_new_session on POSIX, CREATE_NO_WINDOW on Windows) so it outlives its caller.

wait_codex.py calls launch(); the process that starts re-enters this file as
  python launch_codex.py --wrapper <ATTEMPT> <WORKROOT> <MODEL> <EFFORT> [--schema SCHEMA_PATH]
      [--resume SESSION_ID] [--service-tier TIER]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


def run_rules(windows: bool) -> str:
    """The rules ahead of every fresh prompt; `windows` adds the no-window rule."""
    no_windows = (
        "- Never open a window on this PC: the user is working on it. Use no GUI tool or plugin (browser, Chrome,",
        "  computer use), never run Start-Process, Invoke-Item, start, explorer or notepad, and never run a file by",
        "  its path alone: on Windows `& 'x.py'` opens it in the user's editor. Run scripts through their",
        "  interpreter (`python x.py`).",
    )
    return "\n".join(
        (
            "[Run rules, set by the orchestrator that launched you. Where they conflict with AGENTS.md, these win.]",
            "- You are a delegated worker, not an orchestrator: do the task below yourself, one step after another.",
            "  Never spawn sub-agents or parallel workers (spawn_agent or any other delegation tool), and never start",
            "  another codex process from the shell, even where an AGENTS.md file or the task asks for parallel work.",
            "- Never kill a process you did not start; the python and shell processes waiting for you are expected.",
            "- You cannot reach the user, but the orchestrator can answer you. If you cannot go on without a",
            "  decision or a fact only it can give, end with the question; it will resume this session with the",
            "  answer. Otherwise decide yourself and state the assumption.",
            *(no_windows if windows else ()),
            "- Search narrowly: give rg a target path and -j2, give find a -maxdepth, never search .temp_files/ or the",
            "  whole repository, and open known paths directly instead of searching for them.",
            "- Put scratch and output files under .temp_files/.",
            "",
            "[Task]",
            "",
        )
    )


# Windows only: on macOS a Computer Use worker has to drive Chrome, and
# AGENTS.md still makes every other window wait for the user's permission.
RUN_RULES = run_rules(os.name == "nt")


def codex_argv(
    codex: str,
    attempt: Path,
    model: str,
    effort: str,
    *,
    schema: Path | None,
    resume: str | None = None,
    service_tier: str | None = None,
) -> list[str]:
    argv = [codex, "exec", *(["resume", resume] if resume else []), "-", "-m", model]
    # GPT-6 models keep their multi-agent instructions even with both features off, which is why
    # RUN_RULES forbids sub-agents as well.
    argv += ["-c", f"model_reasoning_effort={effort}", "--disable", "multi_agent", "--disable", "multi_agent_v2"]
    # Pin standard speed when omitted instead of inheriting the user's config.
    argv += ["-c", f'service_tier="{service_tier or "default"}"']
    if schema is not None:
        argv += ["--output-schema", str(schema)]
    return [*argv, "-o", str(attempt / "last.txt")]


def child_env(base: Mapping[str, str]) -> dict[str, str]:
    """Environment for codex: git must fail instead of opening a credential window on the user's desktop."""
    return {**base, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}


def find_codex() -> str:
    codex = shutil.which("codex")
    if codex is None:
        raise FileNotFoundError("codex CLI not found on PATH")
    return codex


def launch(
    attempt: Path,
    workroot: Path,
    model: str,
    effort: str,
    *,
    schema: Path | None,
    resume: str | None = None,
    service_tier: str | None = None,
) -> int:
    """Start one attempt whose input.txt is in place; return the wrapper pid, or raise OSError when it cannot start."""
    find_codex()  # fail here, where the caller can report it, rather than inside the detached wrapper
    wrapper = [sys.executable, str(Path(__file__).resolve()), "--wrapper", str(attempt), str(workroot), model, effort]
    wrapper += ["--schema", str(schema)] if schema is not None else []
    wrapper += ["--resume", resume] if resume else []
    wrapper += ["--service-tier", service_tier] if service_tier else []
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
    (attempt / "pid").write_text(f"{proc.pid}\n", encoding="utf-8")
    return proc.pid


def run_wrapper(args: argparse.Namespace) -> int:
    """Blocking half: run codex on the attempt's input.txt, then write the exit-code sentinel."""
    attempt = Path(args.attempt)
    with (
        open(attempt / "input.txt", "rb") as stdin,
        open(attempt / "stdout.log", "wb") as stdout,
        open(attempt / "stderr.log", "wb") as stderr,
    ):
        try:
            argv = codex_argv(
                find_codex(),
                attempt,
                args.model,
                args.effort,
                schema=Path(args.schema) if args.schema else None,
                resume=args.resume,
                service_tier=args.service_tier,
            )
            code = subprocess.run(
                argv, stdin=stdin, stdout=stdout, stderr=stderr, cwd=args.workroot, env=child_env(os.environ)
            ).returncode
        except OSError as exc:
            stderr.write(f"launch_codex.py wrapper: {exc}\n".encode())
            code = 127
    (attempt / "exit_code").write_text(f"{code}\n", encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wrapper", action="store_true", required=True)
    parser.add_argument("attempt")
    parser.add_argument("workroot")
    parser.add_argument("model")
    parser.add_argument("effort")
    parser.add_argument("--schema", default=None)
    parser.add_argument("--resume", default=None)
    parser.add_argument("--service-tier", default=None)
    return run_wrapper(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
