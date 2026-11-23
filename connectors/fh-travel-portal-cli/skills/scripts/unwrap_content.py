#!/usr/bin/env python3
"""Unwrap the fh-travel MCP tools/call response.

读法：宿主常先给到 content[0].text 全文信封——先看 ok / error.message / summary。
业务只在协议层 ``structuredContent``（数组在 ``data``，标量在 ``value``）；
信封 ``summary`` 为指引，**不当业务**；``hasMore=true`` 表示还有 structuredContent。
正式 ``outputSchema`` 只在 ``tools/list``（可能没有），不在 content 里。
失败：``ok=false`` + ``error.message``（isError=true）；失败占位也可在 structuredContent。

Usage:
  python3 scripts/unwrap_content.py result.json
  python3 scripts/unwrap_content.py result.json --out r.json
  command-producing-json | python3 scripts/unwrap_content.py -
  python3 scripts/unwrap_content.py result.json --with-schema
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

KIND = "mcp-tool-content"
SUCCESS_SUMMARY = (
    "工具从成功执行，返回结果请从MCP标准协议的structuredContent 字段获取，"
    "不在content里面。outputSchema请从tool/list调用的返回结果中获取"
)
# 兼容旧常量名
RESULT_SEE_STRUCTURED_CONTENT = SUCCESS_SUMMARY


class EnvelopeError(Exception):
    """The server returned a failure envelope (ok=false); message is the server text."""


def _is_envelope(value: Any) -> bool:
    return isinstance(value, dict) and value.get("kind") == KIND and "ok" in value


def _is_structured_pointer(value: Any) -> bool:
    """True if value is a content-only guide (not business)."""
    if isinstance(value, dict) and _is_envelope(value) and value.get("ok") is True:
        return True
    if not isinstance(value, str):
        return False
    if value == SUCCESS_SUMMARY:
        return True
    if value == "内容请读 structuredContent":
        return True
    if value.startswith("当前内容在content[0].text，请把structuredContent"):
        return True
    if value.startswith("当前内容仅是指引，请把structuredContent"):
        return True
    return "structuredContent" in value and "不在content里面" in value


def _business_structured(value: Any) -> Optional[Any]:
    """Protocol structuredContent that holds business data (not ok=false placeholder)."""
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return None
    if value.get("ok") is False and "message" in value:
        return None
    keys = set(value.keys())
    if keys == {"data"}:
        return value.get("data")
    if keys == {"value"}:
        return value.get("value")
    return value


def _envelope_guide(value: dict[str, Any]) -> Any:
    if "summary" in value:
        return value.get("summary")
    if "result" in value:
        return value["result"]
    return SUCCESS_SUMMARY


def unwrap_envelope(value: Any, with_schema: bool = False) -> Any:
    """Unwrap one mcp-tool-content envelope (content 全文)。

    ok=false → EnvelopeError。
    ok=true → 返回 summary 指引（不是业务）。
    取业务请用 unwrap_payload（读 structuredContent）。
    """
    if not _is_envelope(value):
        return value
    ok = value.get("ok")
    if ok is False or (ok is None and isinstance(value.get("error"), dict)):
        error = value.get("error") if isinstance(value.get("error"), dict) else {}
        message = str(error.get("message") or "未知错误")
        raise EnvelopeError(message)
    guide = _envelope_guide(value)
    if with_schema:
        # content 不再带 outputSchema；正式 schema 在 tools/list
        return {"outputSchema": value.get("outputSchema"), "result": guide}
    return guide


def _add_candidate(out: list[Any], item: Any) -> None:
    if item is None:
        return
    for existing in out:
        if existing is item:
            return
    out.append(item)


def _iter_candidates(payload: Any) -> list[Any]:
    """Bare envelope, JSON-RPC / CallToolResult wrappers, content[].text."""
    out: list[Any] = []
    _add_candidate(out, payload)
    if isinstance(payload, dict):
        inner = payload.get("result")
        _add_candidate(out, inner)
        _add_candidate(out, payload.get("structuredContent"))
        blocks: list[Any] = []
        if isinstance(payload.get("content"), list):
            blocks.extend(payload["content"])
        if isinstance(inner, dict):
            _add_candidate(out, inner.get("structuredContent"))
            if isinstance(inner.get("content"), list):
                blocks.extend(inner["content"])
        for block in blocks:
            if not isinstance(block, dict):
                continue
            _add_candidate(out, block.get("structuredContent"))
            if isinstance(block.get("text"), str):
                _add_candidate(out, block["text"])
    elif isinstance(payload, list):
        for block in payload:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                _add_candidate(out, block["text"])
    return out


def _protocol_structured(payload: Any) -> Optional[Any]:
    if not isinstance(payload, dict):
        return None
    for node in (payload, payload.get("result") if isinstance(payload.get("result"), dict) else None):
        if not isinstance(node, dict):
            continue
        found = _business_structured(node.get("structuredContent"))
        if found is not None:
            return found
        if isinstance(node.get("content"), list):
            for block in node["content"]:
                if isinstance(block, dict):
                    found = _business_structured(block.get("structuredContent"))
                    if found is not None:
                        return found
    return None


def _parse_candidate(candidate: Any) -> Any:
    if not isinstance(candidate, str):
        return candidate
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        stripped = candidate.strip()
        if stripped.startswith("业务错误") or stripped.startswith("工具调用失败"):
            raise EnvelopeError(stripped)
        return None


def unwrap_payload(payload: Any, with_schema: bool = False) -> Any:
    """从完整 tools/call 响应取业务：先认 content 失败，再只认 structuredContent。

    信封 summary/旧 result 指引不当业务；没有可用 structuredContent 时显式报错。
    无信封的裸业务 JSON（脚本中间产物）原样返回。
    """
    saw_success_envelope = False

    for candidate in _iter_candidates(payload):
        parsed = _parse_candidate(candidate)
        if parsed is None:
            continue
        if _is_envelope(parsed) and (
            parsed.get("ok") is False
            or (parsed.get("ok") is None and isinstance(parsed.get("error"), dict))
        ):
            return unwrap_envelope(parsed, with_schema=with_schema)
        if _is_envelope(parsed) and parsed.get("ok") is True:
            saw_success_envelope = True

    structured = _protocol_structured(payload)
    if structured is not None:
        if with_schema:
            return {"outputSchema": None, "result": structured}
        return structured

    if saw_success_envelope:
        raise EnvelopeError(
            "content 指引去 structuredContent，但响应里没有可用的 structuredContent"
        )
    return payload


def call_tool_error_message(payload: Any) -> Optional[str]:
    """tools/call 业务/协议失败时返回可读原因，否则 None。

    覆盖：CallToolResult.isError、content 信封 ok=false、structuredContent.ok=false。
    传输层 JSON-RPC error 由 mcp_proxy 另抛；本函数专治「HTTP 200 但业务失败」。
    """
    if not isinstance(payload, dict):
        return None
    call = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    if not isinstance(call, dict):
        return None

    def _from_structured(sc: Any) -> Optional[str]:
        if isinstance(sc, dict) and sc.get("ok") is False:
            msg = sc.get("message")
            return str(msg).strip() if msg else "structuredContent.ok=false"
        return None

    def _from_content(blocks: Any) -> Optional[str]:
        if not isinstance(blocks, list):
            return None
        for block in blocks:
            if not isinstance(block, dict):
                continue
            text = block.get("text")
            if not isinstance(text, str):
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                stripped = text.strip()
                if stripped.startswith("业务错误") or stripped.startswith("工具调用失败"):
                    return stripped
                continue
            if _is_envelope(parsed) and (
                parsed.get("ok") is False
                or (parsed.get("ok") is None and isinstance(parsed.get("error"), dict))
            ):
                err = parsed.get("error") if isinstance(parsed.get("error"), dict) else {}
                return str(err.get("message") or "未知错误")
        return None

    msg = _from_content(call.get("content"))
    if msg:
        return msg
    msg = _from_structured(call.get("structuredContent"))
    if msg:
        return msg
    if call.get("isError") is True:
        return "tools/call.isError=true（未解析到具体 message）"
    return None


def _read_input(raw: str) -> Any:
    text = sys.stdin.read() if raw == "-" else Path(raw).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="saved tools/call JSON/TXT file, or - for stdin")
    parser.add_argument("--out", type=Path, help="write unwrapped JSON to this file instead of stdout")
    parser.add_argument("--with-schema", action="store_true", help="keep outputSchema next to result（content 已无 schema，常为 null）")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        result = unwrap_payload(_read_input(args.input), with_schema=args.with_schema)
    except EnvelopeError as exc:
        print(f"[工具失败] {exc}", file=sys.stderr)
        return 1

    if isinstance(result, str):
        output = result
    else:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"[信息] 已写出解封结果: {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(2)
