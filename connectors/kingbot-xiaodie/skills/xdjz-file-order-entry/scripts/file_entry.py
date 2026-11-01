#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件录单执行脚本（本地运行，文件内容不进入 Agent 上下文）。

作用：把「读取文件 -> Base64 编码 -> 调用 MCP 工具上传 -> 调用 MCP 工具发起录单」
整条链路放在脚本内完成，Agent 只传文件路径、只接收几十字节的结果 JSON，
避免大文件（最大 20MB）的 Base64 内容占用对话 Token。

用法：
    python file_entry.py check  --file <路径>            # 仅本地校验，不联网
    python file_entry.py upload --file <路径> [--sid <会话ID>] [--source-agent-id <ID>]
                                    [--source-agent-name <名称>] [--timeout <秒>]
    python file_entry.py tools  [--server <服务名>]      # 诊断：列出可用工具

输出：单行 JSON 到 stdout（成功/失败都是 JSON），退出码 0 成功，非 0 失败。
安全：脚本绝不输出 file_content_base64、Authorization 等敏感内容。
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20971520 字节
MCP_ENV_VAR = "CODEBUDDY_MCP_CONFIG"
SERVER_CANDIDATES = ("xdjz", "kingbot-xiaodie", "kingbot_xiaodie", "kingbot")
UPLOAD_TOOL = "kingbot_upload_file"
CHAT_TOOL = "kingbot_chat"
SOURCE_SKILL_ID = "xdjz-file-order-entry"
SOURCE_SKILL_NAME = "文件录单"

CONTENT_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    "xls": "application/vnd.ms-excel",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "txt": "text/plain",
}

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_ENV = 3
EXIT_MCP = 4
EXIT_TIMEOUT = 5

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def _init_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def emit(payload, exit_code=EXIT_OK):
    """输出单行 JSON 并退出。"""
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.flush()
    sys.exit(exit_code)


def fail(code, message, **extra):
    payload = {"ok": False, "error": {"code": code, "message": message}}
    payload.update(extra)
    exit_code = {
        "FILE_NOT_FOUND": EXIT_BAD_INPUT,
        "NOT_A_FILE": EXIT_BAD_INPUT,
        "UNSUPPORTED_FORMAT": EXIT_BAD_INPUT,
        "FILE_TOO_LARGE": EXIT_BAD_INPUT,
        "EMPTY_FILE": EXIT_BAD_INPUT,
        "NO_MCP_CONFIG": EXIT_ENV,
        "NO_UPLOAD_SERVER": EXIT_ENV,
        "STDIO_SERVER": EXIT_ENV,
        "MCP_HTTP_ERROR": EXIT_MCP,
        "MCP_PROTOCOL_ERROR": EXIT_MCP,
        "TOOL_ERROR": EXIT_MCP,
        "NO_DOCUMENT_ID": EXIT_MCP,
        "TIMEOUT": EXIT_TIMEOUT,
    }.get(code, EXIT_MCP)
    emit(payload, exit_code)


# ---------------------------------------------------------------------------
# 文件校验
# ---------------------------------------------------------------------------

def inspect_file(path_str):
    """本地校验文件，返回元信息；不读取文件内容到内存。"""
    path = Path(path_str).expanduser()
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path

    if not resolved.exists():
        fail("FILE_NOT_FOUND", "文件不存在：%s" % path_str)
    if not resolved.is_file():
        fail("NOT_A_FILE", "不是文件：%s" % path_str)

    ext = resolved.suffix.lower().lstrip(".")
    if ext not in CONTENT_TYPES:
        fail(
            "UNSUPPORTED_FORMAT",
            "不支持的文件格式：.%s，当前支持 %s"
            % (ext or "(无扩展名)", "/".join(sorted(set(CONTENT_TYPES)))),
            ext=ext,
        )

    size = resolved.stat().st_size
    if size <= 0:
        fail("EMPTY_FILE", "文件为空：%s" % resolved.name)
    if size > MAX_FILE_SIZE:
        fail(
            "FILE_TOO_LARGE",
            "文件 %s 大小 %d 字节，超过 20MB（20971520 字节）上限，不支持上传"
            % (resolved.name, size),
            size=size,
            limit=MAX_FILE_SIZE,
        )

    return {
        "path": str(resolved),
        "name": resolved.name,
        "ext": ext,
        "size": size,
        "content_type": CONTENT_TYPES[ext],
    }


def read_base64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


# ---------------------------------------------------------------------------
# MCP 客户端（streamable-http，JSON-RPC 2.0）
# ---------------------------------------------------------------------------

def resolve_server(preferred=None, url_override=None, token_override=None):
    """从环境变量注入的 MCP 配置里找到录单服务（xdjz）。

    优先级：--server 指定 > 常见服务名 > 名称含 xdjz/kingbot > URL 含 kingbot。
    """
    if url_override:
        headers = {"Content-Type": "application/json"}
        if token_override:
            headers["Authorization"] = "Bearer %s" % token_override
        return {"name": "override", "url": url_override, "headers": headers}

    raw = os.environ.get(MCP_ENV_VAR) or os.environ.get("CLAUDE_MCP_CONFIG")
    if not raw:
        fail(
            "NO_MCP_CONFIG",
            "当前执行环境未注入 MCP 服务配置（%s），无法连接录单服务" % MCP_ENV_VAR,
        )
    try:
        cfg = json.loads(raw)
    except Exception as exc:
        fail("NO_MCP_CONFIG", "MCP 服务配置解析失败：%s" % exc)

    servers = cfg.get("mcpServers") or {}
    if not isinstance(servers, dict) or not servers:
        fail("NO_UPLOAD_SERVER", "MCP 服务配置为空，录单服务未连接")

    names = ([preferred] if preferred else []) + list(SERVER_CANDIDATES)
    for name in names:
        if name and name in servers:
            return dict(servers[name], name=name)

    for name, conf in servers.items():
        low = name.lower()
        if "xdjz" in low or "kingbot" in low:
            return dict(conf, name=name)

    for name, conf in servers.items():
        blob = json.dumps(conf, ensure_ascii=False).lower()
        if "kingbot" in blob:
            return dict(conf, name=name)

    # 兜底：某些环境下录单工具挂在聚合服务下，按工具名反查
    for name, conf in servers.items():
        tools = conf.get("tools")
        if isinstance(tools, dict):
            for tool_name in tools:
                if "kingbot" in str(tool_name).lower():
                    return dict(conf, name=name)
        elif isinstance(tools, list):
            for tool_name in tools:
                if "kingbot" in str(tool_name).lower():
                    return dict(conf, name=name)

    fail(
        "NO_UPLOAD_SERVER",
        "未在已连接的 MCP 服务中找到录单服务（%s），请先在连接器面板连接「小蝶记账」"
        % "、".join(SERVER_CANDIDATES),
        available=sorted(servers.keys()),
    )


class McpClient(object):
    def __init__(self, url, headers=None, timeout=180):
        self.url = url
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json",
                       "Accept": "application/json, text/event-stream"}
        for key, value in (headers or {}).items():
            if key.lower() in ("content-type",):
                continue
            self.headers[key] = value
        self.session_id = None
        self._id = 0
        # 本地代理直连，绕过系统代理设置
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _post(self, payload, expect_response=True):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = dict(self.headers)
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
                if not self.session_id:
                    self.session_id = resp.headers.get("Mcp-Session-Id") or \
                        resp.headers.get("mcp-session-id")
                content_type = resp.headers.get("Content-Type", "")
                status = resp.status
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:500]
            except Exception:
                pass
            fail("MCP_HTTP_ERROR",
                 "录单服务返回 HTTP %s%s" % (exc.code, ("：" + detail) if detail else ""),
                 http_status=exc.code)
        except urllib.error.URLError as exc:
            fail("MCP_HTTP_ERROR", "无法连接录单服务：%s" % exc.reason)
        except TimeoutError:
            fail("TIMEOUT", "录单服务响应超时（%s 秒）" % self.timeout)

        if not expect_response or status in (202, 204) or not raw:
            return None
        return self._decode(raw, content_type, payload.get("id"))

    @staticmethod
    def _decode(raw, content_type, req_id):
        text = raw.decode("utf-8", "replace")
        candidates = []
        if "text/event-stream" in (content_type or "").lower():
            for block in text.split("\n\n"):
                for line in block.splitlines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if not data or data == "[DONE]":
                            continue
                        try:
                            candidates.append(json.loads(data))
                        except Exception:
                            pass
        else:
            try:
                candidates.append(json.loads(text))
            except Exception:
                fail("MCP_PROTOCOL_ERROR", "录单服务返回了无法解析的内容")

        for obj in candidates:
            if isinstance(obj, dict) and ("result" in obj or "error" in obj):
                if req_id is None or obj.get("id") == req_id:
                    return obj
        for obj in candidates:
            if isinstance(obj, dict) and ("result" in obj or "error" in obj):
                return obj
        fail("MCP_PROTOCOL_ERROR", "录单服务未返回有效的 JSON-RPC 结果")

    def _rpc(self, method, params=None, expect_response=True):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        return self._post(payload, expect_response=expect_response)

    def initialize(self):
        self._rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "xdjz-file-order-entry", "version": "1.1.0"},
        })
        try:
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                       expect_response=False)
        except SystemExit:
            raise
        except Exception:
            pass

    def list_tools(self):
        resp = self._rpc("tools/list", {})
        result = resp.get("result") or {}
        return [t.get("name") for t in (result.get("tools") or [])]

    def call_tool(self, name, arguments, timeout=None):
        old = self.timeout
        if timeout:
            self.timeout = timeout
        try:
            resp = self._rpc("tools/call", {"name": name, "arguments": arguments})
        finally:
            self.timeout = old
        if "error" in resp:
            err = resp["error"] or {}
            fail("TOOL_ERROR",
                 "录单服务调用失败：%s" % (err.get("message") or json.dumps(err, ensure_ascii=False)))
        result = resp.get("result") or {}
        if result.get("isError"):
            fail("TOOL_ERROR", "录单服务调用失败：%s" % extract_text(result)[:500])
        return result


def resolve_tool_names(client):
    """实际工具名可能带服务名前缀，这里做一次真实名单匹配。"""
    try:
        names = client.list_tools()
    except SystemExit:
        raise
    except Exception:
        names = []

    def pick(suffix):
        if suffix in names:
            return suffix
        for name in names:
            if isinstance(name, str) and name.endswith(suffix):
                return name
        return suffix

    return pick(UPLOAD_TOOL), pick(CHAT_TOOL)


def extract_text(result):
    """把 MCP 工具结果转成纯文本；结构化内容优先转 JSON 字符串。"""
    parts = []
    structured = result.get("structuredContent")
    if structured:
        try:
            parts.append(json.dumps(structured, ensure_ascii=False))
        except Exception:
            pass
    for item in result.get("content") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text":
            parts.append(item.get("text") or "")
        elif item.get("type") == "resource":
            res = item.get("resource") or {}
            parts.append(res.get("text") or "")
        elif "text" in item:
            parts.append(str(item.get("text")))
        else:
            try:
                parts.append(json.dumps(item, ensure_ascii=False))
            except Exception:
                pass
    return "\n".join(p for p in parts if p).strip()


def extract_document_id(result):
    """从上传结果里取 document_id，兼容多种返回形态。"""
    text = extract_text(result)
    structured = result.get("structuredContent")
    buckets = [structured] if isinstance(structured, dict) else []
    for raw in (text,):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                buckets.append(parsed)
        except Exception:
            pass
    keys = ("document_id", "documentId", "documentID", "id", "docId", "doc_id")
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        for key in keys:
            value = bucket.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in bucket.values():
            if isinstance(value, str) and UUID_RE.fullmatch(value.strip()):
                return value.strip()
    match = UUID_RE.search(text)
    if match:
        return match.group(0)
    return None


# ---------------------------------------------------------------------------
# 会话 ID
# ---------------------------------------------------------------------------

def _norm(p):
    return str(p).replace("/", "\\").rstrip("\\").lower()


def resolve_sid(cli_sid=None):
    """按优先级取得会话 ID：显式传入 > 环境变量 > 本机会话记录匹配 cwd > 随机 UUID。"""
    if cli_sid:
        return cli_sid, "cli"
    for env_key in ("WORKBUDDY_SESSION_ID", "CODEBUDDY_SESSION_ID", "CLAUDE_SESSION_ID"):
        value = os.environ.get(env_key)
        if value:
            return value, "env:%s" % env_key

    home = Path.home()
    cwd = _norm(os.getcwd())
    best = None
    for base in (home / ".workbuddy" / "sessions", home / ".claude" / "sessions"):
        if not base.is_dir():
            continue
        for entry in base.glob("*.json"):
            try:
                data = json.loads(entry.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            sid = data.get("sessionId") or data.get("id")
            if not sid or str(sid).startswith("prewarm"):
                continue
            if data.get("cwd") and _norm(data.get("cwd")) == cwd:
                stamp = data.get("lastHeartbeat") or data.get("startedAt") or 0
                if best is None or stamp > best[0]:
                    best = (stamp, sid)
    if best:
        return best[1], "session-store"

    return str(uuid.uuid4()), "generated"


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------

def cmd_check(args):
    info = inspect_file(args.file)
    emit({"ok": True, "stage": "check", "file": info})


def cmd_upload(args):
    started = time.time()
    info = inspect_file(args.file)

    server = resolve_server(args.server, args.url, args.token)
    if server.get("type") == "stdio" or server.get("command"):
        fail("STDIO_SERVER",
             "录单服务为本地 stdio 模式，脚本无法调用，请改用常规方式处理")

    url = server.get("url")
    if not url:
        fail("NO_UPLOAD_SERVER", "录单服务配置缺少连接地址")
    headers = server.get("headers") or {}

    client = McpClient(url, headers, timeout=args.timeout)
    client.initialize()

    sid, sid_source = resolve_sid(args.sid)
    upload_tool, chat_tool = resolve_tool_names(client)

    if args.dry_run:
        emit({
            "ok": True, "stage": "dry-run", "file": info,
            "server": server.get("name"), "sid_source": sid_source,
            "tools": [upload_tool, chat_tool],
        })

    # 1) 上传文件（Base64 由脚本生成，不回显）
    content_b64 = read_base64(info["path"])
    upload_args = {
        "file_name": info["name"],
        "content_type": info["content_type"],
        "file_size": info["size"],
        "file_content_base64": content_b64,
    }
    upload_result = client.call_tool(upload_tool, upload_args, timeout=max(args.timeout, 180))
    document_id = extract_document_id(upload_result)
    if not document_id:
        fail("NO_DOCUMENT_ID",
             "文件上传后未取到有效的文件标识，录单流程中止",
             raw=extract_text(upload_result)[:500])
    del content_b64

    # 2) 发起录单（Document 消息）
    chat_input = json.dumps({
        "documents": [{
            "documentId": document_id,
            "size": info["size"],
            "name": info["name"],
            "contentType": info["content_type"],
        }],
        "content": "保存",
    }, ensure_ascii=False)
    chat_args = {
        "title": "新对话",
        "sid": sid,
        "input": chat_input,
        "variables": {
            "messageType": "Document",
            "agent_id": "main",
            "source_agent_id": args.source_agent_id,
            "source_agent_name": args.source_agent_name,
            "source_skill_id": SOURCE_SKILL_ID,
            "source_skill_name": SOURCE_SKILL_NAME,
            "source_type": "workbuddy",
        },
    }
    chat_result = client.call_tool(chat_tool, chat_args, timeout=max(args.timeout, 300))
    reply = extract_text(chat_result)

    emit({
        "ok": True,
        "stage": "upload",
        "file": {"name": info["name"], "size": info["size"],
                 "ext": info["ext"], "content_type": info["content_type"]},
        "document_id": document_id,
        "reply": reply[:4000],
        "reply_truncated": len(reply) > 4000,
        "sid_source": sid_source,
        "elapsed_ms": int((time.time() - started) * 1000),
    })


def cmd_tools(args):
    server = resolve_server(args.server, args.url, args.token)
    client = McpClient(server.get("url"), server.get("headers") or {}, timeout=args.timeout)
    client.initialize()
    emit({"ok": True, "stage": "tools", "server": server.get("name"),
          "tools": client.list_tools()})


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    _init_stdio()
    parser = argparse.ArgumentParser(description="文件录单执行脚本")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="仅做本地校验，不联网")
    p_check.add_argument("--file", required=True)
    p_check.set_defaults(func=cmd_check)

    p_up = sub.add_parser("upload", help="上传文件并发起录单")
    p_up.add_argument("--file", required=True)
    p_up.add_argument("--sid", default=None, help="会话 ID，缺省自动解析")
    p_up.add_argument("--source-agent-id", default="",
                      help="来源 Agent ID，缺省为空（专家包副本固定传入专家标识）")
    p_up.add_argument("--source-agent-name", default="",
                      help="来源 Agent 名称，缺省为空（专家包副本固定传入专家名称）")
    p_up.add_argument("--server", default=None, help="MCP 服务名，缺省自动解析")
    p_up.add_argument("--url", default=None, help="直连 MCP 地址（调试用）")
    p_up.add_argument("--token", default=None, help="直连 MCP 的 Bearer Token（调试用）")
    p_up.add_argument("--timeout", type=int, default=120, help="单次请求超时秒数")
    p_up.add_argument("--dry-run", action="store_true", help="只校验与探活，不真正上传")
    p_up.set_defaults(func=cmd_upload)

    p_tools = sub.add_parser("tools", help="列出录单服务可用工具")
    p_tools.add_argument("--server", default=None)
    p_tools.add_argument("--url", default=None)
    p_tools.add_argument("--token", default=None)
    p_tools.add_argument("--timeout", type=int, default=60)
    p_tools.set_defaults(func=cmd_tools)

    args = parser.parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except TimeoutError:
        fail("TIMEOUT", "操作超时")
    except KeyboardInterrupt:
        fail("MCP_HTTP_ERROR", "操作被中断")
    except Exception as exc:  # noqa: BLE001
        fail("MCP_HTTP_ERROR", "脚本执行异常：%s" % exc)


if __name__ == "__main__":
    main()
