#!/usr/bin/env python3
"""Create codex work dirs under <root>/.temp_files/subcodex/ and print their absolute paths, one per line.

Usage: python new_workdir.py [COUNT]

Names embed a timestamp so age is visible at a glance; the random mkdtemp
suffix keeps parallel runs collision-free.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from _paths import repo_root


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("count", nargs="?", type=int, default=1)
    count = parser.parse_args(argv).count
    if count < 1:
        parser.error("COUNT must be at least 1")
    parent = repo_root() / ".temp_files" / "subcodex"
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for _ in range(count):
        print(Path(tempfile.mkdtemp(prefix=f"run_{stamp}_", dir=parent)).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
