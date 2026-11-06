#!/usr/bin/env python3
"""粉象 MCP Streamable HTTP 最小客户端（仅标准库）。

用法：
  python3 fenxiang_mcp.py goods_search '{"keyword":"iPhone 18","platform":"all"}'
  python3 fenxiang_mcp.py tools/list

环境变量：
  FENXIANG_MCP_URL          默认 https://api.fenxianglife.com/njia/mcp
  FENXIANG_MCP_API_KEY      可选；当前服务已关闭鉴权，无需设置

TLS：默认严格校验证书；仅内网自签名测试环境可显式加 --insecure。
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://api.fenxianglife.com/njia/mcp"


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(self, url, api_key, timeout=60, insecure=False):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.context = ssl._create_unverified_context() if insecure else None

    def rpc(self, method, params=None):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=self.context) as response:
                body = response.read().decode("utf-8")
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise McpError("HTTP %s: %s" % (error.code, body[:500])) from error
        except urllib.error.URLError as error:
            raise McpError("connection failed: %s" % error) from error

        if "text/event-stream" in content_type:
            body = _last_sse_data(body)
        try:
            data = json.loads(body)
        except json.JSONDecodeError as error:
            raise McpError("invalid JSON response: %s" % body[:500]) from error
        if data.get("error"):
            raise McpError(json.dumps(data["error"], ensure_ascii=False))
        return data.get("result") or {}

    def list_tools(self):
        result = self.rpc("tools/list")
        return result.get("tools") or []

    def call_tool(self, name, arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise McpError(_first_text(result) or "tool returned isError=true")
        text = _first_text(result)
        structured = result.get("structuredContent")
        return text, parse_text(text), structured


def _first_text(result):
    content = result.get("content") or []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            return block.get("text")
    return None


def _last_sse_data(body):
    data_lines = []
    for line in body.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return body
    for value in reversed(data_lines):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and ("result" in parsed or "error" in parsed):
            return json.dumps(parsed, ensure_ascii=False)
    return data_lines[-1]


def parse_text(text):
    if not text:
        return None
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return None
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return data


def load_api_key(path=None):
    key = os.environ.get("FENXIANG_MCP_API_KEY", "").strip()
    if not key and path:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as handle:
            key = handle.read().strip()
    return key


def build_client(args):
    url = args.url or os.environ.get("FENXIANG_MCP_URL") or DEFAULT_URL
    return McpClient(url, load_api_key(args.api_key_file), timeout=args.timeout, insecure=args.insecure)


def main():
    parser = argparse.ArgumentParser(description="粉象 MCP HTTP 客户端")
    parser.add_argument("tool", help="goods_search / history_price / compare_price / saving_plan / buy_advice / batch_analyze / tools/list")
    parser.add_argument("arguments", nargs="?", default="{}", help="工具参数 JSON，默认 {}")
    parser.add_argument("--url", help="MCP 地址，默认 FENXIANG_MCP_URL 或生产地址")
    parser.add_argument("--api-key-file", help="只包含 API Key 的文件")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--insecure", action="store_true",
                        help="仅内网自签名测试环境使用：跳过证书校验，生产环境不要使用")
    parser.add_argument("--pretty", action="store_true", help="尝试格式化 JSON 输出")
    args = parser.parse_args()

    try:
        client = build_client(args)
        if args.tool in ("tools/list", "tools_list", "list"):
            tools = client.list_tools()
            for tool in tools:
                print(tool.get("name"))
            return 0

        try:
            arguments = json.loads(args.arguments)
        except json.JSONDecodeError as error:
            raise McpError("工具参数不是合法 JSON: %s" % error) from error
        text, parsed, structured = client.call_tool(args.tool, arguments)
        if args.pretty and parsed is not None:
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        elif args.pretty and structured is not None:
            print(json.dumps(structured, ensure_ascii=False, indent=2))
        else:
            print(text if text is not None else json.dumps(structured, ensure_ascii=False))
        return 0
    except McpError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
