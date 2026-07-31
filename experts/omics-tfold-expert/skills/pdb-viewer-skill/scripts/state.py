"""
state.py — pdb-viewer-skill 全局状态中心
========================================

所有模块（serve_pdb.py + handlers/*.py）统一从此模块导入全局变量和锁，
确保多线程场景下的锁对象为同一实例，不产生竞态条件。

使用方式：
    from state import cmd_queue, cmd_lock, sse_clients, sse_lock  # 等

⚠️  只做 import，不在这里修改值（赋值操作在各 handler 中通过 state.xxx = ... 进行）
"""
from __future__ import annotations

import queue
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Optional

# ── 命令队列（自然语言控制） ──────────────────────────────────────────
cmd_queue: list[dict] = []
cmd_lock = threading.Lock()

# ── 默认 PDB 路径（启动时 --pdb-file 设定） ──────────────────────────
default_pdb_url: Optional[str] = None
default_pdb_abs_path: Optional[str] = None

# ── 预加载缓存（LLM 在 present_files 前调用 /api/preload 预读文件）────
preloaded_pdb: Optional[dict] = None   # {"data": base64, "name": str, "uri": str}
preload_lock = threading.Lock()

# ── 查询结果缓存（浏览器推送 list_chains 等，LLM 通过 /api/query-result 读取）──
query_results: dict = {}
query_lock = threading.Lock()

# ── 心跳与空闲超时 ───────────────────────────────────────────────────
last_heartbeat: float = 0.0
hb_lock = threading.Lock()
heartbeat_timeout: int = 30          # 30s 无心跳视为面板离线

last_activity: float = 0.0
activity_lock = threading.Lock()

# ── Loading 模式（服务交接期间返回 loading.html）──────────────────────
loading_mode: bool = False
loading_lock = threading.Lock()
loading_pdb_param: str = ""

# ── 全局 HTTP server 引用（/api/shutdown 使用）───────────────────────
server_ref: Optional[ThreadingHTTPServer] = None
server_lock = threading.Lock()

# ── SSE 客户端队列（实时推送）────────────────────────────────────────
sse_clients: list[queue.Queue] = []
sse_lock = threading.Lock()
