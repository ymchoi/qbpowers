#!/usr/bin/env python3
"""Create one bridge work directory and print its absolute path.

Usage: python new_workdir.py [repo-root]

The repo root comes from this file's own location (see _paths.py), so the
bridge prompt that invokes this carries no host-specific path. The optional
argument is honoured only for bridges still running the previous procedure,
which passed one; rejecting it would kill those runs at step 1.

Directories collect under <root>/.temp_files/subcodex/ so codex bridge
residue stays in one place the user can sweep in bulk, and the name embeds
a timestamp so age is visible at a glance. The random mkdtemp suffix keeps
parallel bridges collision-free.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

from _paths import repo_root


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: new_workdir.py [repo-root]", file=sys.stderr)
        return 2
    root = Path(argv[1]) if len(argv) == 2 and Path(argv[1]).is_dir() else repo_root()
    parent = root / ".temp_files" / "subcodex"
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = tempfile.mkdtemp(prefix=f"bridge_{stamp}_", dir=parent)
    print(Path(work).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
