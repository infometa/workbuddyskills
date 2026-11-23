"""
eBay 对账 - MCP 客户端

通过 Streamable HTTP 调用 nexus-mcp 暴露的工具，替代脚本直连数据库/内置 SQL。
仅使用 Python 标准库（urllib），无需额外依赖。

用法（也可作为命令行工具自检 MCP 连通性）:
    python ebay_mcp.py --list-tools
    python ebay_mcp.py --call queryOrderByReferenceNo '{"orderId":"1234567890"}'

连接地址优先级: 参数 > 环境变量 NEXUS_MCP_URL > 默认值
"""

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MCP_URL = "https://datacenter.eccang.com/nexus/mcp/stream"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_NAME = "ebay-duizhang"
CLIENT_VERSION = "2.0"

# MCP 工具名（由 nexus-mcp 的 SettlementCheckBillTool 提供）
TOOL_QUERY_ORDER = "queryOrderByReferenceNo"
TOOL_QUERY_PROFIT_SETTLEMENT = "queryProfitSettlement"


class McpError(Exception):
    """MCP 调用异常"""


class McpClient:
    """MCP Streamable HTTP 客户端（initialize / tools/call）"""

    def __init__(self, url=None, timeout=60):
        self.url = (url or os.environ.get("NEXUS_MCP_URL") or DEFAULT_MCP_URL).rstrip("/")
        self.timeout = timeout
        self.session_id = None
        self._initialized = False
        self._next_id = 0

    # ── 底层传输 ──────────────────────────────────────────────────────────

    def _new_id(self):
        self._next_id += 1
        return self._next_id

    def _post(self, payload, expect_body=True):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        request = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session_id = session_id
                content_type = (response.headers.get("Content-Type") or "").lower()
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise McpError(f"MCP 服务返回 HTTP {e.code}: {detail[:300]}") from None
        except urllib.error.URLError as e:
            raise McpError(f"MCP 服务不可达（{self.url}）: {e.reason}") from None

        if not expect_body or not raw.strip():
            return None
        if "text/event-stream" in content_type or raw.lstrip().startswith(("event:", "data:", "id:", ":")):
            return self._parse_sse(raw)
        return json.loads(raw)

    @staticmethod
    def _parse_sse(text):
        """解析 SSE 响应体，返回包含 result/error 的那条 JSON-RPC 消息"""
        payloads = []
        data_lines = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
            elif not line.strip() and data_lines:
                payloads.append("\n".join(data_lines))
                data_lines = []
        if data_lines:
            payloads.append("\n".join(data_lines))

        fallback = None
        for payload in payloads:
            payload = payload.strip()
            if not payload:
                continue
            try:
                message = json.loads(payload)
            except ValueError:
                continue
            if "result" in message or "error" in message:
                return message
            if fallback is None:
                fallback = message
        if fallback is not None:
            return fallback
        raise McpError(f"MCP 响应中未解析出 JSON-RPC 消息: {text[:200]}")

    def _request(self, method, params=None):
        """发送 JSON-RPC 请求并返回 result"""
        payload = {"jsonrpc": "2.0", "id": self._new_id(), "method": method}
        if params is not None:
            payload["params"] = params
        message = self._post(payload)
        if message is None:
            raise McpError(f"MCP 请求 {method} 未返回内容")
        if "error" in message:
            error = message["error"] or {}
            raise McpError(f"MCP 请求 {method} 失败: {error.get('message') or error}")
        return message.get("result")

    # ── 协议流程 ──────────────────────────────────────────────────────────

    def initialize(self):
        """握手：initialize + notifications/initialized"""
        result = self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
        })
        # 已建立会话后必须补发 initialized 通知
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_body=False)
        self._initialized = True
        return result

    def list_tools(self):
        if not self._initialized:
            self.initialize()
        result = self._request("tools/list", {})
        return (result or {}).get("tools", [])

    def call_tool(self, name, arguments):
        """调用工具，返回工具输出的解析结果（JSON 数组/对象）"""
        if not self._initialized:
            self.initialize()
        result = self._request("tools/call", {"name": name, "arguments": arguments or {}})
        text = "".join(
            item.get("text", "") for item in (result or {}).get("content", [])
            if item.get("type") == "text"
        )
        if (result or {}).get("isError"):
            raise McpError(f"MCP 工具 {name} 执行失败: {text[:300]}")
        return parse_tool_payload(name, text)


def parse_tool_payload(tool_name, text):
    """工具返回的是 JSON 字符串，形如 DataResult{code,message,data,...}。

    统一取 data 字段；data 为 null 时返回空列表；非 DataResult 结构时原样返回。
    """
    if not text or not text.strip():
        return []
    try:
        payload = json.loads(text)
    except ValueError:
        raise McpError(f"MCP 工具 {tool_name} 返回内容不是 JSON: {text[:200]}") from None

    if isinstance(payload, dict) and "code" in payload:
        if payload.get("code") != "200":
            raise McpError(f"MCP 工具 {tool_name} 返回失败: "
                           f"{payload.get('code')} {payload.get('message')}")
        payload = payload.get("data")
    return payload if payload is not None else []


def main():
    url = None
    args = sys.argv[1:]
    if args and args[0] == "--mcp-url":
        url = args[1]
        args = args[2:]

    client = McpClient(url=url)
    print(f"MCP: {client.url}")
    try:
        if not args or args[0] == "--list-tools":
            for tool in client.list_tools():
                print(f"  - {tool.get('name')}: {tool.get('description')}")
        elif args[0] == "--call" and len(args) >= 2:
            arguments = json.loads(args[2]) if len(args) > 2 else {}
            print(json.dumps(client.call_tool(args[1], arguments), ensure_ascii=False, indent=2))
        else:
            print("用法: python ebay_mcp.py [--mcp-url URL] [--list-tools | --call <工具名> '<json入参>']")
    except McpError as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
