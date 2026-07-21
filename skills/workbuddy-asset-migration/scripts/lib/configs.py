"""JSON config semantic merge: settings, mcp, models, marketplaces."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def shallow_target_wins(src: Path, dst: Path, *, overwrite: bool) -> Dict[str, Any]:
    """Top-level dict merge. Target keys win unless overwrite."""
    s = _read_json(src) or {}
    d = _read_json(dst) or {}
    if not isinstance(s, dict) or not isinstance(d, dict):
        # Can't merge non-dict; if dst missing, just copy
        if not dst.exists() and src.is_file():
            _write_json(dst, s)
            return {"action": "created", "added": list(s.keys()) if isinstance(s, dict) else []}
        return {"action": "skipped", "reason": "non-dict json"}
    added, replaced, skipped = [], [], []
    out = dict(d)
    for k, v in s.items():
        if k in out:
            if overwrite:
                out[k] = v
                replaced.append(k)
            else:
                skipped.append(k)
        else:
            out[k] = v
            added.append(k)
    _write_json(dst, out)
    return {"action": "merged", "added": added, "replaced": replaced, "skipped": skipped}


def merge_mcp_servers(src: Path, dst: Path, *, overwrite: bool) -> Dict[str, Any]:
    """Merge mcp.json. mcpServers dict merged by server name; other keys shallow."""
    s = _read_json(src) or {}
    d = _read_json(dst) or {}
    if not isinstance(s, dict):
        return {"action": "skipped", "reason": "src not dict"}
    if not isinstance(d, dict):
        d = {}
    out = dict(d)

    # mcpServers
    src_servers = s.get("mcpServers", {}) if isinstance(s.get("mcpServers"), dict) else {}
    dst_servers = out.get("mcpServers", {}) if isinstance(out.get("mcpServers"), dict) else {}
    merged_servers = dict(dst_servers)
    added, replaced, skipped = [], [], []
    for name, cfg in src_servers.items():
        if name in merged_servers:
            if overwrite:
                merged_servers[name] = cfg
                replaced.append(name)
            else:
                skipped.append(name)
        else:
            merged_servers[name] = cfg
            added.append(name)
    if merged_servers:
        out["mcpServers"] = merged_servers

    # Other top-level keys
    other_added, other_replaced, other_skipped = [], [], []
    for k, v in s.items():
        if k == "mcpServers":
            continue
        if k in out:
            if overwrite:
                out[k] = v
                other_replaced.append(k)
            else:
                other_skipped.append(k)
        else:
            out[k] = v
            other_added.append(k)

    _write_json(dst, out)
    return {
        "action": "merged",
        "servers_added": added,
        "servers_replaced": replaced,
        "servers_skipped": skipped,
        "other_added": other_added,
        "other_replaced": other_replaced,
        "other_skipped": other_skipped,
    }


def merge_list_by_id(
    src: Path, dst: Path, *, list_field: str, id_field: str, overwrite: bool
) -> Dict[str, Any]:
    """Merge JSON of shape {list_field: [{id_field: ...}, ...]}."""
    s = _read_json(src)
    d = _read_json(dst)
    if not isinstance(s, dict) or list_field not in s:
        # If dst doesn't exist and src is plain list, treat top-level as the list itself
        if isinstance(s, list):
            s = {list_field: s}
        else:
            return {"action": "skipped", "reason": f"src missing {list_field}"}
    if not isinstance(d, dict):
        d = {}
    src_list = s.get(list_field) or []
    dst_list = d.get(list_field) or []
    if not isinstance(src_list, list) or not isinstance(dst_list, list):
        return {"action": "skipped", "reason": "non-list"}

    dst_by_id = {item.get(id_field): item for item in dst_list if isinstance(item, dict)}
    added, replaced, skipped = [], [], []
    for item in src_list:
        if not isinstance(item, dict):
            continue
        item_id = item.get(id_field)
        if item_id is None:
            continue
        if item_id in dst_by_id:
            if overwrite:
                dst_by_id[item_id] = item
                replaced.append(item_id)
            else:
                skipped.append(item_id)
        else:
            dst_by_id[item_id] = item
            added.append(item_id)
    d[list_field] = list(dst_by_id.values())
    _write_json(dst, d)
    return {"action": "merged", "added": added, "replaced": replaced, "skipped": skipped}


# --- path rewrite in JSON files (cross-machine) ---

def rewrite_paths_in_json(
    file_path: Path,
    spec: dict,
    mapper,
) -> dict:
    """Rewrite path-bearing fields in a JSON file according to spec.

    spec: {"json_path": "cwd"} for top-level scalar, or
          {"json_pattern": "mcpServers.*.{command,cwd}"} for wildcard.

    Returns {"rewritten": N, "fields": [...]}.
    """
    if not file_path.is_file():
        return {"rewritten": 0, "fields": []}
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"rewritten": 0, "fields": [], "error": "invalid json"}

    rewritten = 0
    touched_fields = []

    def rewrite_value(v):
        nonlocal rewritten
        if isinstance(v, str):
            r = mapper.rewrite(v)
            if r:
                rewritten += 1
                return r.new_path
            return v
        return v

    if "json_path" in spec:
        # Simple top-level field
        key = spec["json_path"]
        if isinstance(data, dict) and key in data:
            new_val = rewrite_value(data[key])
            if new_val != data[key]:
                data[key] = new_val
                touched_fields.append(key)
    elif "json_pattern" in spec:
        # Pattern: "mcpServers.*.{command,cwd}"
        # Simple parser: dot-separated segments. "*" matches any key in dict.
        # "{a,b}" matches multiple alternative final keys.
        pattern = spec["json_pattern"]
        _apply_pattern(data, pattern.split("."), rewrite_value, touched_fields)

    if rewritten:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return {"rewritten": rewritten, "fields": touched_fields[:20]}


def _apply_pattern(node, segments, rewrite_fn, touched, *, path_so_far=""):
    if not segments:
        return
    head, rest = segments[0], segments[1:]
    if not rest:
        # Final segment, may be "{a,b}" or single key
        keys = _expand_brace_segment(head)
        if isinstance(node, dict):
            for k in keys:
                if k in node:
                    new = rewrite_fn(node[k])
                    if new != node[k]:
                        node[k] = new
                        touched.append(f"{path_so_far}.{k}".lstrip("."))
                # Also walk into lists if the value is a list of strings
                # (e.g. args[*])
        return
    if head == "*":
        if isinstance(node, dict):
            for k, v in node.items():
                _apply_pattern(v, rest, rewrite_fn, touched,
                               path_so_far=f"{path_so_far}.{k}".lstrip("."))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                _apply_pattern(v, rest, rewrite_fn, touched,
                               path_so_far=f"{path_so_far}[{i}]")
    else:
        if isinstance(node, dict) and head in node:
            _apply_pattern(node[head], rest, rewrite_fn, touched,
                           path_so_far=f"{path_so_far}.{head}".lstrip("."))


def _expand_brace_segment(seg: str):
    if seg.startswith("{") and seg.endswith("}"):
        return [s.strip() for s in seg[1:-1].split(",") if s.strip()]
    return [seg]
