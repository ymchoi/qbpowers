#!/bin/sh
# Resolve a Python interpreter, then run one of this directory's scripts.
#
# Usage: sh bridge.sh <script.py> [args...]
#
# This lives in a file rather than in SKILL.md prose because the relay model
# copies prose, and a step it can paraphrase is a step it can skip. The name
# `python3` is not enough on either platform: on Windows it is a Microsoft Store
# alias that prints an ad and exits non-zero, and on macOS it is the system 3.9
# at /usr/bin/python3 whenever PATH is not a login one.
#
# The script name is passed through instead of being aliased to a subcommand, so
# the bridge's Bash command still literally contains "run_codex.py" — which is
# what audit_compliance.py greps for to tell a real delegation from a faked one.
#
# Invoke it as `sh bridge.sh`, never `./bridge.sh`: that needs no executable bit
# and never reads the shebang, which is the line a CRLF checkout would break.
set -e

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
script=$1
shift

# The probe asks for a version, not merely for something that runs: these scripts
# use 3.14 syntax, so an unchecked pick fails as a SyntaxError partway into a
# delegation rather than here, where the message can say what is wrong.
for py in python3 python py; do
    if "$py" -c "import sys; assert sys.version_info >= (3, 14)" >/dev/null 2>&1; then
        exec "$py" "$here/$script" "$@"
    fi
done

echo "bridge.sh: no python 3.14+ found (tried python3, python, py)" >&2
exit 127
