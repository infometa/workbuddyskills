#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接对 barcode-generator MCP server 发 JSON-RPC 调用 alb_preview。

用法: python alb_preview_generic.py <输入.alb路径> <输出.png路径>
"""
import sys
import os
import json
import base64
import threading
import time
import queue
import urllib.request
import urllib.parse
import ssl

SSE_URL = "https://ai.masocloud.net/DoYsSV/maso/mcp/sse"


class SSEClient:
    def __init__(self, url):
        self.url = url
        self.events = queue.Queue()
        self.messages_url = None
        self._stop = threading.Event()

    def _read_loop(self):
        req = urllib.request.Request(self.url, headers={
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "src": "WorkBuddy",
        })
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx, timeout=300)
        buf = b""
        event = None
        data_lines = []
        while not self._stop.is_set():
            chunk = resp.read(1)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n\n"):
                block = buf.decode("utf-8", errors="replace")
                buf = b""
                self._parse_block(block)
        resp.close()

    def _parse_block(self, block):
        event = None
        data_lines = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:"):].strip())
        data = "\n".join(data_lines)
        if data:
            self.events.put((event, data))

    def start(self):
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()

    def wait_for_endpoint(self, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            try:
                event, data = self.events.get(timeout=1)
                if event == "endpoint":
                    self.messages_url = data
                    return data
                # some servers send endpoint as first data without event name
                if event is None and data.startswith("http"):
                    self.messages_url = data
                    return data
            except queue.Empty:
                continue
        raise RuntimeError("未收到 endpoint 事件")

    def wait_for_id(self, msg_id, timeout=120):
        end = time.time() + timeout
        while time.time() < end:
            try:
                event, data = self.events.get(timeout=2)
                if event != "message":
                    continue
                try:
                    payload = json.loads(data)
                except Exception:
                    continue
                if payload.get("id") == msg_id:
                    return payload
            except queue.Empty:
                continue
        return None


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "src": "WorkBuddy",
    })
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=60)
        body = resp.read()
        return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def resolve_endpoint(base_url, endpoint):
    if endpoint.startswith("http"):
        return endpoint
    return urllib.parse.urljoin(base_url, endpoint)


def main():
    alb_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(alb_path, "rb") as f:
        alb_bytes = f.read()
    file_b64 = base64.b64encode(alb_bytes).decode("ascii")
    file_name = os.path.basename(alb_path)

    client = SSEClient(SSE_URL)
    client.start()
    endpoint = client.wait_for_endpoint()
    print("endpoint:", endpoint, flush=True)
    messages_url = resolve_endpoint(SSE_URL, endpoint)
    print("messages_url:", messages_url, flush=True)

    # initialize
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "workbuddy", "version": "1.0.0"},
        },
    }
    post_json(messages_url, init_payload)
    init_resp = client.wait_for_id(1, timeout=60)
    print("initialize resp:", (init_resp or {}).get("result", {}).get("serverInfo"), flush=True)

    # notifications/initialized
    post_json(messages_url, {"jsonrpc": "2.0", "method": "notifications/initialized"})

    # tools/call alb_preview
    call_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "alb_preview",
            "arguments": {
                "fileName": file_name,
                "fileBase64": file_b64,
            },
        },
    }

    def do_call():
        post_json(messages_url, call_payload)

    t = threading.Thread(target=do_call, daemon=True)
    t.start()

    resp = client.wait_for_id(2, timeout=180)
    if resp is None:
        print("FAILED: 未收到 tools/call 响应", flush=True)
        sys.exit(2)

    if "error" in resp:
        print("ERROR:", json.dumps(resp["error"], ensure_ascii=False), flush=True)
        sys.exit(3)

    content = resp.get("result", {}).get("content", [])
    text = ""
    for c in content:
        if c.get("type") == "text":
            text += c.get("text", "")
    print("result text:", text, flush=True)

    # 解析 url
    url = None
    try:
        obj = json.loads(text)
        url = obj.get("url")
    except Exception:
        pass
    if not url:
        # 尝试从文本中直接提取 url
        import re
        m = re.search(r'https?://[^\s"\']+', text)
        if m:
            url = m.group(0)
    if not url:
        print("FAILED: 未找到 url", flush=True)
        sys.exit(4)
    print("image url:", url, flush=True)

    # 轮询下载
    last_err = None
    for attempt in range(30):
        try:
            req = urllib.request.Request(url, headers={"src": "WorkBuddy"})
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=30)
            data = resp.read()
            if len(data) > 1000:
                with open(out_path, "wb") as f:
                    f.write(data)
                print("SAVED:", out_path, len(data), "bytes", flush=True)
                sys.exit(0)
            else:
                last_err = "small data %d" % len(data)
        except urllib.error.HTTPError as e:
            last_err = "HTTP %d" % e.code
        except Exception as e:
            last_err = str(e)
        print("retry %d: %s" % (attempt, last_err), flush=True)
        time.sleep(3)

    print("FAILED download:", last_err, flush=True)
    sys.exit(5)


if __name__ == "__main__":
    main()
