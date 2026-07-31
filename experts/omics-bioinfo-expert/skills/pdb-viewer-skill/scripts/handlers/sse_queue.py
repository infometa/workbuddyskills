"""
handlers/sse_queue.py — SSE 推送 + 命令队列管理
================================================

依赖 state 模块的全局变量（_sse_clients / _sse_lock / _command_queue / _cmd_lock）。
所有写操作均通过 state 模块的锁保护。

对外暴露：
  - enqueue_command(cmd_entry) -> None          入队并推送给所有 SSE 客户端
  - handle_sse_events(handler) -> None          处理 GET /api/events 的 SSE 长连接
  - drain_poll_queue() -> list[dict]            取出并清空队列（供 /api/command-poll 使用）
"""
from __future__ import annotations

import json
import queue as _queue
import sys
import os

# 将 scripts/ 目录加入 sys.path（支持从任意工作目录 import state）
_scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import state


def enqueue_command(cmd_entry: dict) -> None:
    """将命令入队，并实时推送给所有活跃的 SSE 客户端。"""
    with state.cmd_lock:
        state.cmd_queue.append(cmd_entry)

    with state.sse_lock:
        for cq in state.sse_clients:
            try:
                cq.put_nowait(cmd_entry)
            except _queue.Full:
                pass


def drain_poll_queue() -> list[dict]:
    """取出并清空命令队列（供 /api/command-poll 轮询端点使用）。"""
    with state.cmd_lock:
        if state.cmd_queue:
            cmds = list(state.cmd_queue)
            state.cmd_queue.clear()
            return cmds
    return []


def handle_sse_events(handler) -> None:
    """
    处理 GET /api/events 的 SSE 长连接。

    handler: PdbViewerHandler 实例（具有 send_response / send_header / wfile 等属性）
    """
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()

    client_q: _queue.Queue = _queue.Queue()
    with state.sse_lock:
        state.sse_clients.append(client_q)

    try:
        # 连接建立时，立即 flush 已排队的命令
        with state.cmd_lock:
            for cmd in state.cmd_queue:
                try:
                    client_q.put_nowait(cmd)
                except _queue.Full:
                    pass
            state.cmd_queue.clear()

        while True:
            try:
                cmd = client_q.get(timeout=30)
                data = json.dumps(cmd, ensure_ascii=False)
                handler.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                handler.wfile.flush()
            except _queue.Empty:
                # 每 30s 发心跳保活
                handler.wfile.write(b": hb\n\n")
                handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        with state.sse_lock:
            if client_q in state.sse_clients:
                state.sse_clients.remove(client_q)
