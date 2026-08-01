#!/usr/bin/env python3
"""Poll a launch_codex.py sentinel. Prints DONE, RUNNING, or CRASHED.

Usage: python poll_codex.py <WORK> [2]     (pass 2 for the recovery attempt)

Waits up to 570s (114 x 5s) so callers can use a 600000 ms Bash timeout
safely; POLL_TRIES overrides the loop count for tests only. DONE means the
exit-code file exists. RUNNING means the wrapper pid is still alive — call
again; there is no total time limit. CRASHED means the wrapper died without
writing the sentinel, so the file will never appear.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
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
    # POSIX: os.kill(pid, 0) probes existence. Never use this on Windows,
    # where signal 0 would TerminateProcess the target.
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "2"):
        print("usage: poll_codex.py <WORK> [2]", file=sys.stderr)
        return 2
    work = Path(argv[1])
    suffix = "2" if len(argv) == 3 else ""
    exit_code = work / f"exit_code{suffix}"
    tries = int(os.environ.get("POLL_TRIES", "114"))
    for _ in range(tries):
        if exit_code.is_file():
            break
        time.sleep(5)
    if exit_code.is_file():
        print("DONE")
        return 0
    try:
        pid = int((work / f"pid{suffix}").read_text().strip())
    except (OSError, ValueError):
        print("CRASHED")
        return 0
    print("RUNNING" if pid_alive(pid) else "CRASHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
