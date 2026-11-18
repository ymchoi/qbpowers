#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("count", nargs="?", type=int, default=1)
    count = parser.parse_args(argv).count
    if count < 1:
        parser.error("COUNT must be at least 1")
    parent = ROOT / ".temp_files" / "subcodex"
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for _ in range(count):
        print(Path(tempfile.mkdtemp(prefix=f"run_{stamp}_", dir=parent)).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
