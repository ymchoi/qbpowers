#!/usr/bin/env python3
"""Classify a failed codex run. Prints one verdict line, then evidence lines.

Usage: python diagnose_codex.py <WORK> [2] [--schema]

Verdicts, checked in this order:
  CONTEXT_EXHAUSTED  session is full; a resume would fail identically
  SCHEMA_REJECTED    the API refused schema.json itself (HTTP 400, pre-work)
  NONE               unknown failure; the caller may make one resume attempt

Gating encodes hard-won rules — do not substitute ad-hoc greps:
- stderr echoes the task's own content, so every string match is anchored to
  lines codex itself prints (leading "ERROR: ").
- the schema check counts only when the run did not succeed: a nonzero exit
  code or a missing sentinel from a crashed wrapper, because echoed error text
  in a successful run must not trigger it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CONTEXT_RE = re.compile(r"^ERROR: .*Codex ran out of room in the model", re.MULTILINE)
SCHEMA_CODE = '"code": "invalid_json_schema"'


def read_exit_code(work: Path, suffix: str) -> int | None:
    try:
        return int((work / f"exit_code{suffix}").read_text().strip())
    except (OSError, ValueError):
        return None


def schema_error_block(stderr_text: str) -> list[str] | None:
    lines = stderr_text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("ERROR: {") and SCHEMA_CODE in "\n".join(lines[i : i + 5]):
            return lines[i : i + 40]
    return None


def main(argv: list[str]) -> int:
    schema_task = "--schema" in argv[1:]
    args = [a for a in argv[1:] if a != "--schema"]
    if len(args) not in (1, 2) or (len(args) == 2 and args[1] != "2"):
        print("usage: diagnose_codex.py <WORK> [2] [--schema]", file=sys.stderr)
        return 2
    work = Path(args[0])
    suffix = "2" if len(args) == 2 else ""
    exit_code = read_exit_code(work, suffix)
    try:
        stderr_text = (work / f"stderr{suffix}.log").read_text(encoding="utf-8", errors="replace")
    except OSError:
        stderr_text = ""

    context_hits = CONTEXT_RE.findall(stderr_text)
    if context_hits:
        print("CONTEXT_EXHAUSTED")
        for line in context_hits:
            print(line)
        return 0

    # A missing sentinel means the wrapper crashed and must still be classified.
    if schema_task and exit_code != 0:
        block = schema_error_block(stderr_text)
        if block is not None:
            print("SCHEMA_REJECTED")
            for line in block:
                print(line)
            return 0

    print("NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
