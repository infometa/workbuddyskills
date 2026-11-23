"""Command-line entry point for every fh-travel-portal tool（fh CLI 版）。

Examples:
  python scripts/fh_travel.py tools/list
  python scripts/fh_travel.py tools/call '{"name":"air_city","arguments":{"keyword":"北京","scope":"DOMESTIC"}}'

接口与旧 MCP 直连版完全一致（供 air_domestic_query.py / air_intl_query.py 等以子进程方式调用）；
内部经 mcp_proxy.py 兼容层走 fh CLI。--out 落盘完整 JSON-RPC 形状响应，便于大结果处理。
业务只在 structuredContent；content 是 kind=mcp-tool-content 信封，见 references/mcp-envelope.md。

认证由 fh CLI 自管（fh auth login 写 ~/.fh/<credentialsFile>，文件名见 config.json），不再读本脚本自己的环境变量。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp_proxy import McpProxy, McpProxyError  # noqa: E402


def parse_params(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"params 不是有效 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("params 必须是 JSON 对象")
    return value


def usage() -> str:
    return (
        "用法:\n"
        "  python scripts/fh_travel.py tools/list [--out <文件>]\n"
        "  python scripts/fh_travel.py tools/call '<JSON params>' [--out <文件>]\n"
        "  --out 把完整 JSON-RPC 响应写入文件（大响应如 intl_shopping 建议使用，避免刷屏）\n"
        "认证: fh CLI 自管（fh auth login 写 ~/.fh/<credentialsFile>，见 config.json）\n"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(usage())
        return 0 if len(sys.argv) >= 2 else 2

    method = sys.argv[1]
    if method == "tools/call" and len(sys.argv) < 3:
        print("[错误] tools/call 必须提供 params JSON", file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2

    out_path: Path | None = None
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 >= len(sys.argv):
            print("[错误] --out 缺少文件路径", file=sys.stderr)
            return 2
        out_path = Path(sys.argv[idx + 1])
        sys.argv = sys.argv[:idx] + sys.argv[idx + 2:]

    try:
        params = parse_params(sys.argv[2] if len(sys.argv) >= 3 else None)
        proxy = McpProxy()
        result = proxy.request(method, params)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if out_path is not None:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            print(f"[信息] 响应已写入: {out_path}", file=sys.stderr)
        else:
            print(text)
        return 0
    except (OSError, ValueError, McpProxyError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
