"""Classify a failed codex attempt from the files in its work dir.

Verdicts, checked in this order:
  CONTEXT_EXHAUSTED  the session is full; a resume would fail identically
  USAGE_LIMIT        the account is out of quota; nothing more can start until it resets
  SCHEMA_REJECTED    the API refused schema.json itself (HTTP 400, before any work)
  NONE               unknown failure; the caller may make its one resume attempt

stderr echoes the task's own content, so every match is anchored to lines codex
itself prints (a leading "ERROR: "), and the schema check counts only when the
attempt did not exit 0.
"""

from __future__ import annotations

import re
from pathlib import Path

CONTEXT_RE = re.compile(r"^ERROR: .*Codex ran out of room in the model.*$", re.MULTILINE)
USAGE_LIMIT_RE = re.compile(r"^ERROR: .*hit your usage limit.*$", re.MULTILINE)
SCHEMA_CODE = '"code": "invalid_json_schema"'


def read_exit_code(work: Path, suffix: str) -> int | None:
    try:
        return int((work / f"exit_code{suffix}").read_text().strip())
    except OSError, ValueError:
        return None


def schema_error_block(stderr_text: str) -> list[str] | None:
    lines = stderr_text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("ERROR: {") and SCHEMA_CODE in "\n".join(lines[i : i + 5]):
            return lines[i : i + 40]
    return None


def diagnose(work: Path, suffix: str, schema: bool) -> tuple[str, list[str]]:
    """Return (verdict, evidence lines) for the attempt whose files carry `suffix`."""
    try:
        stderr_text = (work / f"stderr{suffix}.log").read_text(encoding="utf-8", errors="replace")
    except OSError:
        stderr_text = ""
    for verdict, pattern in (("CONTEXT_EXHAUSTED", CONTEXT_RE), ("USAGE_LIMIT", USAGE_LIMIT_RE)):
        hits = pattern.findall(stderr_text)
        if hits:
            return verdict, hits
    if schema and read_exit_code(work, suffix) != 0:
        block = schema_error_block(stderr_text)
        if block is not None:
            return "SCHEMA_REJECTED", block
    return "NONE", []
