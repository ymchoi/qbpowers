"""Locate the repo root from this package's own position on disk.

The scripts live at <root>/.claude/skills/model-sub-codex/scripts/, so the root
is derivable from __file__ alone: no argument and no cwd assumption.
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
