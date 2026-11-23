#!/usr/bin/env python3
"""MCP 返回拆封（基建）。契约见 references/mcp-envelope.md。

先读 content 信封（ok / error / hasMore / summary）；业务只在 structuredContent。
正式 outputSchema 只在 tools/list（可能没有）；content 不再带 schema 块。

库用法：
  from mcp_envelope import unwrap, peel_candidates, decode, is_envelope

CLI：
  python3 scripts/mcp_envelope.py --result [文件|-]
  python3 scripts/mcp_envelope.py --schema [文件|-]
  python3 scripts/mcp_envelope.py --split  [文件|-]

stdin 用 - 或不给文件。不调用 MCP。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KIND = "mcp-tool-content"


def decode(value: Any) -> Any:
    """Parse JSON text; if the value is a JSON string, parse one more layer."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # 城市名、IATA 本来就不是 JSON，解析失败要原样返回，不能当成坏数据丢掉。
        return value
    if isinstance(parsed, str):
        # content[].text 经常是「字符串里再套一层 JSON」；二次转义后再读会出现。
        try:
            return json.loads(parsed)
        except json.JSONDecodeError:
            return parsed
    return parsed


def is_envelope(obj: Any) -> bool:
    # 普通 JSON-RPC 也有 result，不能只看有没有这个键；必须同时有我们的 kind 和 ok。
    return isinstance(obj, dict) and obj.get("kind") == KIND and "ok" in obj


def peel_candidates(value: Any) -> list[Any]:
    """Collect JSON-RPC result, CallToolResult content, envelope, and structuredContent."""
    out: list[Any] = []

    def add(item: Any) -> None:
        item = decode(item)
        if item is None:
            return
        for existing in out:
            if existing is item:
                return
        try:
            if item in out:
                return
        except TypeError:
            # dict 可比；混进不可哈希对象时 `in` 会炸。先用 is 挡住同一对象重复递归。
            pass
        out.append(item)
        if not isinstance(item, dict):
            return
        if is_envelope(item):
            # content 信封：只认失败/指引；业务不在 result，勿把指引句当候选业务。
            return
        if "result" in item:
            add(item.get("result"))
        structured = item.get("structuredContent")
        if isinstance(structured, (dict, list)):
            add(structured)
        content = item.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                inner = block.get("structuredContent")
                if isinstance(inner, (dict, list)):
                    add(inner)
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    add(block["text"])

    add(value)
    return out


def find_envelope(value: Any) -> dict[str, Any] | None:
    for candidate in peel_candidates(value):
        if is_envelope(candidate):
            return candidate
    return None


def unwrap(value: Any) -> Any:
    """Business payload from structuredContent only; None on failure / missing structured."""
    from unwrap_content import EnvelopeError, _is_structured_pointer, unwrap_payload

    try:
        out = unwrap_payload(value)
    except EnvelopeError:
        return None
    if _is_structured_pointer(out):
        return None
    return out


def output_schema(value: Any) -> dict[str, Any] | None:
    # content 信封不再带 outputSchema；正式 schema 只在 tools/list。
    envelope = find_envelope(value)
    if envelope is None or envelope.get("ok") is not True:
        return None
    schema = envelope.get("outputSchema")
    return schema if isinstance(schema, dict) else None


def split(value: Any) -> dict[str, Any]:
    envelope = find_envelope(value)
    if envelope is None:
        return {
            "kind": None,
            "ok": None,
            "requestSeqNo": None,
            "hasMore": None,
            "summary": None,
            "result": unwrap(value),
            "error": None,
            "outputSchema": None,
        }
    ok = envelope.get("ok") is True
    error = envelope.get("error") if not ok else None
    return {
        "kind": envelope.get("kind"),
        "ok": envelope.get("ok"),
        "requestSeqNo": envelope.get("requestSeqNo"),
        "hasMore": envelope.get("hasMore") if ok else None,
        "summary": envelope.get("summary") if ok else None,
        # 兼容旧字段名：旧 result 指引；新形态用 summary
        "result": (envelope.get("summary") if "summary" in envelope else envelope.get("result")) if ok else None,
        "error": error if isinstance(error, dict) else error,
        "outputSchema": envelope.get("outputSchema") if ok else None,
    }


def load_source(source: str) -> Any:
    if source == "-":
        return decode(sys.stdin.read())
    return decode(Path(source).read_text(encoding="utf-8"))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 控制台默认 GBK，拆出来的中文城市名会 UnicodeEncodeError。
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--result", action="store_true", help="只输出业务 result（失败为 null）")
    mode.add_argument("--schema", action="store_true", help="只输出 outputSchema（失败/缺失为 null）")
    mode.add_argument("--split", action="store_true", help="输出 kind/ok/requestSeqNo/result/error/outputSchema")
    parser.add_argument("input", nargs="?", default="-", help="JSON 文件，或 - 表示 stdin")
    args = parser.parse_args()
    try:
        payload = load_source(args.input)
        if args.result:
            out = unwrap(payload)
        elif args.schema:
            out = output_schema(payload)
        else:
            # 没指定 --result/--schema 时默认 --split：只看 result 容易把失败当成「没数据」。
            out = split(payload)
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
