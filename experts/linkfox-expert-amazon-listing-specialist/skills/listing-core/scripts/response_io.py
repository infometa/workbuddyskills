#!/usr/bin/env python3
"""
LinkFox Skill I/O helper — wraps any main script to persist large API
responses to disk, then offers a `read` subcommand to extract specific fields
from those persisted files. Generic, business-agnostic.

This script is bundled into each skill's scripts/ directory by tools/sync_runtime.py.
The agent must pass --script <path> to identify which main script to execute.

Usage:
  python scripts/linkfox_io.py run --script <PATH> --out-dir <DIR> '<json_params>' [--label NAME] [--timeout SEC]
  python scripts/linkfox_io.py run --script <PATH> --out-dir <DIR> --params-file <PATH> [--label NAME] [--timeout SEC]
  python scripts/linkfox_io.py read <file> (--path "<JMESPath>" | --fields "f1,f2,...") [--limit N] [--offset M] [--format json|jsonl|csv|table]

Large requests: pass --params-file <PATH> instead of an inline JSON string so a
big payload (hundreds of ASINs / long text / an upstream persisted file) never
enters the command line or the agent's context.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Force UTF-8 stdout/stderr so non-ASCII chars in previews and API responses
# print correctly on Windows (default cp936 / gbk).
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

try:
    import jmespath  # type: ignore
    HAS_JMESPATH = True
except ImportError:
    HAS_JMESPATH = False


MAX_STRING_LEN = 120
MAX_DEPTH = 3
SAMPLE_KEY_CAP = 15
RAW_TEXT_PEEK = 500
DEFAULT_TIMEOUT_SEC = 300


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _err(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def _resolve_script(script_arg: str) -> Path:
    p = Path(script_arg).expanduser()
    if not p.is_absolute():
        # Resolve relative to the current working directory the agent invoked from.
        p = (Path.cwd() / p).resolve()
    else:
        p = p.resolve()
    if not p.is_file():
        _err(f"--script path not found: {p}")
    return p


def _resolve_skill_name(main_script: Path) -> str:
    """Best-effort skill name extraction for filename prefixing.

    main_script lives at <skill_dir>/scripts/<name>.py — return <skill_dir>'s
    folder name. Fall back to the script's stem if structure differs.
    """
    try:
        if main_script.parent.name == "scripts":
            return main_script.parents[1].name
    except IndexError:
        pass
    return main_script.stem


def _sanitize_label(label: str) -> str:
    """Allow only safe filename chars in --label to prevent path traversal."""
    cleaned = re.sub(r"[^\w\-]", "_", label)
    return cleaned[:64]  # cap length


def _truncate_string(s: str) -> str:
    if len(s) <= MAX_STRING_LEN:
        return s
    return s[:MAX_STRING_LEN] + f"...(truncated, total {len(s)} chars)"


def _truncate_value(value: Any, depth: int = 0) -> Any:
    """Recursively truncate strings, deep nesting, and large arrays for preview."""
    if depth >= MAX_DEPTH:
        if isinstance(value, dict):
            return f"<truncated nested object, keys: {list(value.keys())[:10]}>"
        if isinstance(value, list):
            return f"<truncated nested array, length: {len(value)}>"
        if isinstance(value, str):
            return _truncate_string(value)
        return value
    if isinstance(value, str):
        return _truncate_string(value)
    if isinstance(value, dict):
        out = {k: _truncate_value(v, depth + 1) for k, v in value.items()}
        return out
    if isinstance(value, list):
        if not value:
            return []
        truncated = [_truncate_value(value[0], depth + 1)]
        if len(value) > 1:
            # Note total length on the parent — keep the array type-homogeneous
            # so downstream consumers can iterate without special-casing strings.
            truncated.append({"_omitted_items": len(value) - 1})
        return truncated
    return value


def _shape_of(value: Any, top: bool = False) -> Any:
    """Lightweight schema description for the preview block."""
    if isinstance(value, dict):
        keys = list(value.keys())
        out: dict[str, Any] = {"type": "object", "top_keys" if top else "keys": keys}
        if top:
            for k in keys[:8]:
                out[k] = _shape_of(value[k])
        return out
    if isinstance(value, list):
        out = {"type": "array", "length": len(value)}
        if value and isinstance(value[0], dict):
            out["item_keys"] = list(value[0].keys())
        elif value:
            out["item_type"] = type(value[0]).__name__
        return out
    return {"type": type(value).__name__}


def _build_sample(value: Any) -> Any:
    """First-record sample with explicit truncation marker."""
    if isinstance(value, list):
        if not value:
            return {"_truncated_record": True, "_note": "array is empty"}
        first = value[0]
        if isinstance(first, dict):
            sample = {"_truncated_record": True, "_note": f"first of {len(value)} items"}
            sample.update(_truncate_value(first, depth=1))
            return sample
        return {"_truncated_record": True, "_note": f"first of {len(value)} items", "value": _truncate_value(first, depth=1)}
    if isinstance(value, dict):
        sample = {"_truncated_record": True, "_note": "top-level object (truncated)"}
        sample.update(_truncate_value(value, depth=1))
        return sample
    return {"_truncated_record": True, "value": _truncate_value(value, depth=1)}


def _shrink_preview(preview: dict) -> dict:
    """Cap the sample's value fields when it has many keys.

    `shape.*.item_keys` is the single source of truth for the full key list
    (always complete, no truncation). The sample only ever shows up to
    SAMPLE_KEY_CAP fields with their concrete values, since the agent only
    needs a feel for value shapes — for the full menu of available fields,
    they read `shape`.
    """
    sample = preview.get("sample")
    if isinstance(sample, dict):
        meta_keys = {"_truncated_record", "_note"}
        data_keys = [k for k in sample.keys() if k not in meta_keys]
        if len(data_keys) > SAMPLE_KEY_CAP:
            kept = data_keys[:SAMPLE_KEY_CAP]
            new_sample = {k: v for k, v in sample.items() if k in meta_keys or k in kept}
            base_note = sample.get("_note", "")
            extra = (
                f"showing first {SAMPLE_KEY_CAP} of {len(data_keys)} fields "
                f"(see `shape` for the complete key list)"
            )
            new_sample["_note"] = f"{base_note}; {extra}" if base_note else extra
            preview["sample"] = new_sample
    return preview


# ---------------------------------------------------------------------------
# `run` subcommand
# ---------------------------------------------------------------------------


def _resolve_params(args: argparse.Namespace) -> str:
    """Resolve the JSON params string from either the positional arg or a file.

    大请求暂存：参数包很大（几百个 ASIN / 长文本 / 来自上游落盘文件）时，
    用 --params-file 从文件读，避免把大 JSON 塞进命令行 argv + agent 上下文。
    位置参数 params 与 --params-file 恰好二选一。
    """
    has_inline = args.params is not None
    has_file = args.params_file is not None
    if has_inline and has_file:
        _err("run: positional params and --params-file are mutually exclusive")
    if not has_inline and not has_file:
        _err("run: provide JSON params inline or via --params-file <path>")
    if has_file:
        params_path = Path(args.params_file).expanduser().resolve()
        if not params_path.is_file():
            _err(f"--params-file not found: {params_path}")
        try:
            params_str = params_path.read_text(encoding="utf-8")
        except OSError as e:
            _err(f"Failed to read --params-file {params_path}: {e}")
        # 校验是合法 JSON，避免把脏数据透传给主脚本后才崩。
        try:
            json.loads(params_str)
        except json.JSONDecodeError as e:
            _err(f"--params-file is not valid JSON: {params_path}\n{e}")
        return params_str.strip()
    return args.params


def cmd_run(args: argparse.Namespace) -> int:
    main_script = _resolve_script(args.script)
    skill_name = _resolve_skill_name(main_script)
    params_str = _resolve_params(args)

    out_dir = Path(args.out_dir).expanduser().resolve()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        _err(f"Failed to create --out-dir {out_dir}: {e}")
    if not os.access(out_dir, os.W_OK):
        _err(f"--out-dir is not writable: {out_dir}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = secrets.token_hex(3)
    safe_label = _sanitize_label(args.label) if args.label else ""
    label_part = f"__{safe_label}" if safe_label else ""
    out_file = out_dir / f"{skill_name}__{timestamp}_{rand}{label_part}.json"

    # Force the child process to emit UTF-8 regardless of the host console
    # encoding (Windows defaults to cp936 / gbk and would otherwise corrupt
    # non-ASCII bytes when we read them back).
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"

    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, str(main_script), params_str],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env,
            timeout=args.timeout,
        )
        stdout_text = proc.stdout or ""
        stderr_text = proc.stderr or ""
        returncode = proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout_text = (e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) or ""
        stderr_text = (e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")) or ""
        returncode = 124  # convention for timeout

    # Always write the captured stdout to disk, even if not JSON.
    try:
        out_file.write_text(stdout_text, encoding="utf-8")
    except OSError as e:
        _err(f"Failed to write output file {out_file}: {e}")

    if stderr_text:
        sys.stderr.write(stderr_text)

    # Try to parse the captured stdout as JSON for the preview.
    try:
        parsed = json.loads(stdout_text) if stdout_text.strip() else None
        format_kind = "json"
    except json.JSONDecodeError:
        parsed = None
        format_kind = "raw_text"

    preview: dict[str, Any] = {
        "_preview": {
            "is_preview": True,
            "warning": (
                "PREVIEW ONLY — NOT FULL DATA. The full response is saved to `file`. "
                "Use `python scripts/linkfox_io.py read <file> --fields '...'` to extract "
                "specific fields, or `--path '<JMESPath>'` for complex projections."
            ),
        },
    }

    # Surface failures prominently so agents don't mistake a stub preview for success.
    if returncode != 0 or timed_out:
        stderr_snippet = stderr_text[-500:] if stderr_text else ""
        preview["_error"] = {
            "exit_code": returncode,
            "timed_out": timed_out,
            "stderr_snippet": stderr_snippet,
            "hint": "The wrapped script failed or timed out. The output file may be empty or partial.",
        }

    preview.update({
        "file": str(out_file),
        "size_bytes": out_file.stat().st_size,
        "skill": skill_name,
        "exit_code": returncode,
        "format": format_kind,
        "label": safe_label or None,
        "next_steps_hint": (
            "use: python scripts/linkfox_io.py read <file> --fields '...' | --path '...'"
        ),
    })

    if format_kind == "json":
        preview["shape"] = _shape_of(parsed, top=True)
        preview["sample"] = _build_sample(parsed)
    else:
        peek = stdout_text[:RAW_TEXT_PEEK]
        preview["raw_text_peek"] = peek
        preview["raw_text_total_chars"] = len(stdout_text)
        preview["sample"] = {
            "_truncated_record": True,
            "_note": f"stdout was not valid JSON; first {RAW_TEXT_PEEK} chars shown above in raw_text_peek",
        }

    preview = _shrink_preview(preview)
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    return returncode


# ---------------------------------------------------------------------------
# `read` subcommand
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        _err(f"Failed to read file {path}: {e}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        _err(f"File is not valid JSON: {path}\n{e}")


def _basic_dot_path(data: Any, path: str) -> Any:
    """Pure-stdlib dot-path resolver. No [*] support — callers fall back here only when jmespath is unavailable AND the path has no [*]."""
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _resolve_field(data: Any, expr: str) -> Any:
    if HAS_JMESPATH:
        return jmespath.search(expr, data)
    if "[" in expr or "*" in expr:
        _err(
            f"jmespath is required for expression '{expr}'. "
            f"Install with: pip install jmespath"
        )
    return _basic_dot_path(data, expr)


def _project_fields(data: Any, fields: list[str]) -> Any:
    """Run each field expr; if any returns a list, zip them into list-of-dicts."""
    resolved: dict[str, Any] = {f: _resolve_field(data, f) for f in fields}

    list_lengths = [len(v) for v in resolved.values() if isinstance(v, list)]
    if not list_lengths:
        return resolved

    # All list values must be same length to zip cleanly.
    if len(set(list_lengths)) > 1:
        # Fallback: return the dict as-is so caller can inspect mismatches.
        return resolved

    n = list_lengths[0]
    rows = []
    for i in range(n):
        row = {}
        for f, v in resolved.items():
            row[f] = v[i] if isinstance(v, list) else v
        rows.append(row)
    return rows


def _apply_slice(value: Any, limit: int | None, offset: int | None) -> Any:
    if not isinstance(value, list):
        return value
    start = offset or 0
    end = (start + limit) if limit is not None else None
    return value[start:end]


def _format_output(value: Any, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(value, ensure_ascii=False, indent=2)
    if fmt == "jsonl":
        if isinstance(value, list):
            return "\n".join(json.dumps(item, ensure_ascii=False) for item in value)
        return json.dumps(value, ensure_ascii=False)
    if fmt in ("csv", "table"):
        if not isinstance(value, list) or not value:
            _err(f"--format {fmt} requires a non-empty list result")
        if not all(isinstance(item, dict) for item in value):
            _err(f"--format {fmt} requires list-of-objects, got list of {type(value[0]).__name__}")
        keys: list[str] = []
        for item in value:
            for k in item.keys():
                if k not in keys:
                    keys.append(k)
        if fmt == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for item in value:
                writer.writerow({k: _stringify(item.get(k)) for k in keys})
            return buf.getvalue().rstrip("\n")
        # table: simple aligned columns
        rows = [[_stringify(item.get(k)) for k in keys] for item in value]
        widths = [len(k) for k in keys]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))
        lines = [
            "  ".join(k.ljust(widths[i]) for i, k in enumerate(keys)),
            "  ".join("-" * widths[i] for i in range(len(keys))),
        ]
        for row in rows:
            lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(keys))))
        return "\n".join(lines)
    _err(f"Unknown --format: {fmt}")
    return ""  # unreachable


def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def cmd_read(args: argparse.Namespace) -> int:
    if not args.path and not args.fields:
        _err("read: either --path or --fields is required")
    if args.path and args.fields:
        _err("read: --path and --fields are mutually exclusive")

    file_path = Path(args.file).expanduser().resolve()
    data = _load_json(file_path)

    if args.path:
        result = _resolve_field(data, args.path)
    else:
        fields = [f.strip() for f in args.fields.split(",") if f.strip()]
        if not fields:
            _err("--fields parsed to empty list")
        result = _project_fields(data, fields)

    result = _apply_slice(result, args.limit, args.offset)
    print(_format_output(result, args.format))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="linkfox_io.py",
        description="Persist large skill API responses to disk and read fields on demand.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser(
        "run",
        help="Execute a main script and persist its stdout to a file; "
             "print only a lightweight preview to stdout.",
    )
    p_run.add_argument("params", nargs="?", default=None, help="JSON params string passed verbatim to the main script (argv[1]). Omit when using --params-file.")
    p_run.add_argument("--params-file", dest="params_file", default=None, help="Path to a file holding the JSON params. Use for large requests (big arrays / long text / upstream persisted files) so the payload never enters the command line or agent context. Mutually exclusive with the positional params.")
    p_run.add_argument("--script", required=True, help="Path to the main script to execute, e.g. scripts/my_api.py")
    p_run.add_argument("--out-dir", required=True, help="Directory to write the response file into (created if missing).")
    p_run.add_argument("--label", default=None, help="Optional filename suffix; sanitized to safe filename characters.")
    p_run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help=f"Subprocess timeout in seconds (default: {DEFAULT_TIMEOUT_SEC}).")
    p_run.set_defaults(func=cmd_run)

    p_read = sub.add_parser(
        "read",
        help="Extract specific fields from a previously persisted response file.",
    )
    p_read.add_argument("file", help="Path to the persisted JSON response file.")
    g = p_read.add_mutually_exclusive_group()
    g.add_argument("--path", default=None, help="JMESPath expression, e.g. 'data[*].{asin: asin, title: title}'.")
    g.add_argument("--fields", default=None, help="Comma-separated field paths, e.g. 'data[*].asin,data[*].title'.")
    p_read.add_argument("--limit", type=int, default=None, help="Take at most N items (when result is a list).")
    p_read.add_argument("--offset", type=int, default=None, help="Skip the first M items (when result is a list).")
    p_read.add_argument("--format", choices=["json", "jsonl", "csv", "table"], default="json", help="Output format (default: json).")
    p_read.set_defaults(func=cmd_read)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
