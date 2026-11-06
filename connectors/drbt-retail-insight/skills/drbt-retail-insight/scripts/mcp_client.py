"""Minimal MCP streamable-HTTP client for the drbt retail MCP server.

Why this exists: the drbt MCP server can drop out of the agent's tool registry
mid-session (ToolSearch no longer finds it, DeferExecuteTool returns
"Tool not found"). The service itself is still up, so talk to it directly.

Credentials are read at runtime from ~/.workbuddy/mcp.json -> mcpServers.<name>,
so no token is stored in this skill.
"""

import json
import os
import urllib.request

CONFIG = os.path.join(os.path.expanduser("~"), ".workbuddy", "mcp.json")
DEFAULT_SERVER = "drbt-retail-insight"
PROTO = "2024-11-05"


def load_server(server=DEFAULT_SERVER):
    """Return (url, headers) for a server entry in ~/.workbuddy/mcp.json."""
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    entry = cfg["mcpServers"][server]
    if entry.get("type") != "http" or "url" not in entry:
        raise RuntimeError("server %r is not a streamable-http entry" % server)
    return entry["url"], dict(entry.get("headers") or {})


def _decode(body, ctype):
    """Accept both text/event-stream (SSE) and plain JSON responses."""
    msgs = []
    if "text/event-stream" in ctype:
        for line in body.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk:
                    msgs.append(json.loads(chunk))
    elif body.strip():
        msgs.append(json.loads(body))
    return msgs


class Session:
    def __init__(self, server=DEFAULT_SERVER, timeout=120):
        self.url, self.headers = load_server(server)
        self.timeout = timeout
        self.sid = None

    def _post(self, payload):
        headers = {
            "Content-Type": "application/json",
            # both media types are mandatory, otherwise the server rejects the call
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTO,
        }
        headers.update(self.headers)
        if self.sid:
            headers["mcp-session-id"] = self.sid
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            sid = resp.headers.get("mcp-session-id")
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8", "replace")
        if sid:
            self.sid = sid
        return _decode(body, ctype)

    def _rpc(self, payload):
        for msg in self._post(payload):
            if isinstance(msg, dict) and msg.get("id") == payload.get("id"):
                return msg
        return None

    def open(self):
        resp = self._rpc({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": PROTO,
                "capabilities": {},
                "clientInfo": {"name": "workbuddy-skill", "version": "1.0"},
            },
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return resp

    def list_tools(self):
        resp = self._rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        return ((resp or {}).get("result") or {}).get("tools", [])

    def call(self, name, args, rid=100):
        resp = self._rpc({
            "jsonrpc": "2.0", "id": rid, "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })
        if resp is None:
            raise RuntimeError("no response for %s" % name)
        if "error" in resp:
            raise RuntimeError("MCP error: %s" % json.dumps(resp["error"], ensure_ascii=False))
        return resp["result"]

    def payload(self, name, args, rid=100):
        """Call a tool and unwrap the JSON text content into a dict."""
        result = self.call(name, args, rid=rid)
        for c in result.get("content") or []:
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except ValueError:
                    return {"_raw": c["text"]}
        return result
