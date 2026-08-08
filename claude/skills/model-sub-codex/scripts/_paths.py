#!/usr/bin/env python3
"""Locate the repo root from this package's own position on disk.

Bridge prompts must stay copy-verbatim across machines and checkouts, so they
carry no host-specific path. The scripts live at a fixed depth under the repo
(<root>/.claude/skills/model-sub-codex/scripts/), which makes the root
derivable from __file__ alone — no argument, no cwd assumption.
"""

from __future__ import annotations

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def repo_root() -> Path:
    """Return <root>, or raise SystemExit if the layout is not what we expect."""
    root = SCRIPTS_DIR.parents[3]
    if not (root / ".claude").is_dir():
        raise SystemExit(f"cannot locate repo root from {SCRIPTS_DIR}: no .claude in {root}")
    return root
