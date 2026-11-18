from __future__ import annotations

import json
from pathlib import Path
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


def normalize_file(path: Path) -> None:
    schema = json.loads(path.read_text(encoding="utf-8"))
    walk(schema)
    path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
