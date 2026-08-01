#!/usr/bin/env python3
"""Rewrite a JSON Schema in place to OpenAI strict structured-output form.

Usage: python normalize_schema.py <schema.json>

codex forwards --output-schema verbatim to the API as a strict:true response
format, which rejects anything looser with HTTP 400 invalid_json_schema
before any work runs. This normalizer mechanically enforces the two rules a
Claude-side schema most often misses, preserving semantics:

- every object level gets "additionalProperties": false
- every property key joins "required"; a formerly optional field becomes
  required-but-nullable instead (null-unioned type / anyOf null branch; enum
  member lists are null-extended as well)

It is idempotent. It deliberately does NOT touch what it cannot fix
faithfully (a non-object root, composition keywords like allOf/if/then, or a
schema-valued additionalProperties); those still fail loudly at the API.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def nullable(v: Any) -> Any:
    if not isinstance(v, dict):
        return v
    enum = v.get("enum")
    if isinstance(enum, list) and None not in enum:
        enum.append(None)
    t = v.get("type")
    if isinstance(t, str):
        v["type"] = [t, "null"]
        return v
    if isinstance(t, list):
        if "null" not in t:
            t.append("null")
        return v
    if "anyOf" in v:
        if not any(isinstance(b, dict) and b.get("type") == "null" for b in v["anyOf"]):
            v["anyOf"].append({"type": "null"})
        return v
    return {"anyOf": [v, {"type": "null"}]}


def walk(s: Any) -> None:
    if not isinstance(s, dict):
        return
    props = s.get("properties")
    t = s.get("type")
    is_obj = t == "object" or (isinstance(t, list) and "object" in t)
    if isinstance(props, dict) and (is_obj or t is None):
        if t is None:
            s["type"] = "object"
        s.setdefault("additionalProperties", False)
        req = s.get("required") or []
        for k in props:
            if k not in req:
                props[k] = nullable(props[k])
        s["required"] = list(props)
        for v in props.values():
            walk(v)
    elif is_obj:
        s.setdefault("additionalProperties", False)
    walk(s.get("items"))
    for key in ("$defs", "definitions"):
        d2 = s.get(key)
        if isinstance(d2, dict):
            for v in d2.values():
                walk(v)
    for key in ("anyOf", "oneOf"):
        for v in s.get(key) or []:
            walk(v)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: normalize_schema.py <schema.json>", file=sys.stderr)
        return 2
    path = argv[1]
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    walk(d)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)
    print(f"strict-normalized: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
