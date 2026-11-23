#!/usr/bin/env python3
"""McpProxy 兼容层（fh CLI 实现）——skill 内所有业务脚本经本模块调用服务端工具。

保持与旧 MCP 直连版相同的接口（`McpProxy(token, base_url, ...).request("tools/call", ...)`），
内部改为子进程调 fh CLI（`fh dev call <op>`），认证/刷新/信封/重试全部由 fh CLI 承担。

- `token` / `base_url` 形参仅为兼容旧调用签名，实际不使用（fh CLI 自己管凭据与端点）。
- 返回 JSON-RPC 形状：fh 若给出完整 CallToolResult（content / structuredContent）则原样放进
  ``result``；否则仍包成 ``content[0].text``，下游 unwrap 逻辑不变。
- fh CLI 退出码非 0 时抛 McpProxyError（message 取信封里的业务消息）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from portal_config import credentials_file, fh_base_url, workspace_root


class McpProxyError(RuntimeError):
    """Raised when the fh CLI call fails."""


def _cli_js() -> Path:
    """技能根目录下的 cli/cli.js。scripts/ 的上一级就是技能根，不看当前目录，也不找 PATH 上的 fh。"""
    return Path(__file__).resolve().parent.parent / "cli" / "cli.js"


def _fh_argv(*args: str) -> list[str]:
    js = _cli_js()
    if not js.is_file():
        raise McpProxyError(
            f"技能包内没有 {js}。它应在 SKILL.md 同层的 cli/cli.js。不要全盘搜索。"
        )
    node = shutil.which("node") or "node"
    return [node, str(js), "--base-url", fh_base_url(), "--credentials-file", credentials_file(), *args]


def _fh_call(op: str, arguments: dict[str, Any], timeout: int) -> Any:
    """调 fh CLI，返回工具业务数据（--out 文件内容）；失败抛 McpProxyError。"""
    fd, args_path = tempfile.mkstemp(prefix="fh-args-", suffix=".json")
    fd2, out_path = tempfile.mkstemp(prefix="fh-out-", suffix=".json")
    os.close(fd)
    os.close(fd2)
    try:
        Path(args_path).write_text(json.dumps(arguments, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(
            _fh_argv("dev", "call", op, "--args", f"@{args_path}", "--out", out_path,
                     "--quiet", "--timeout", str(timeout)),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout + 30,
        )
        if r.returncode != 0:
            try:
                env = json.loads(r.stdout or "{}")
                msg = env.get("message") or f"fh 退出码 {r.returncode}"
            except json.JSONDecodeError:
                msg = (r.stderr or r.stdout or f"fh 退出码 {r.returncode}").strip()[:300]
            raise McpProxyError(msg)
        return json.loads(Path(out_path).read_text(encoding="utf-8"))
    except subprocess.TimeoutExpired:
        raise McpProxyError(f"fh 调用超时（{timeout}s）: {op}")
    finally:
        for p in (args_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


class McpProxy:
    """fh CLI 驱动的 McpProxy 兼容实现（构造签名与旧版一致，token/base_url 忽略）。"""

    def __init__(self, token: str = "", base_url: str = "", timeout: int = 90,
                 max_retries: int = 4, retry_backoff: float = 2.0) -> None:
        self.timeout = timeout

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        if method == "tools/list":
            r = subprocess.run(
                _fh_argv("dev", "tools", "--full", "--quiet"),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=self.timeout + 30,
            )
            if r.returncode != 0:
                raise McpProxyError(f"fh dev tools 失败（rc={r.returncode}）")
            env = json.loads(r.stdout)
            return {"result": {"tools": env.get("data", {}).get("tools", [])}}
        if method == "tools/call":
            name = params.get("name")
            if not name:
                raise McpProxyError("tools/call 缺少 name")
            data = _fh_call(name, params.get("arguments") or {}, self.timeout)
            if isinstance(data, dict) and (
                "structuredContent" in data or isinstance(data.get("content"), list)
            ):
                # fh --out 现在写 CallToolResult 原文，不要再压成 content[0].text
                return {"result": data}
            text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
            return {"result": {"content": [{"type": "text", "text": text}]}}
        raise McpProxyError(f"不支持的方法: {method}")
