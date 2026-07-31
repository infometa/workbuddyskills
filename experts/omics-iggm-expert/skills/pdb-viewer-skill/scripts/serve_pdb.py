#!/usr/bin/env python3
"""
pdb-viewer-skill 本地 HTTP 服务器
===================================

为本地 PDB 文件和腾讯健康组学平台 COS 上的 PDB 文件提供 HTTP 访问和自然语言控制能力。

路由:
  /viewer.html          -> serve Skill 自带 Mol* Viewer 模板（本地 molstar.js/css）
  /view/<ts>            -> 同 viewer.html（每次唯一路径，触发浏览器真正 GET 加载）
  /__healthz            -> 200 OK，含 session_id（每次启动随机生成）
  /__pid                -> 返回进程 PID
  /__file?path=...      -> 本地文件代理（base64 JSON）
  /__cos?uri=cos://...  -> COS 代理: omics 认证 + CosBucketService.GetObjectData
  /api/command          -> POST 自然语言命令入队（SSE 实时推送到浏览器）
  /api/ready            -> POST 浏览器就绪通知（Mol* 初始化完成后发送，自动推送预加载 PDB）
  /api/events           -> GET SSE 实时推送端点
  /api/status           -> GET 服务状态
  /api/pdb-url          -> GET 默认 PDB URL（--pdb-file 指定）
  /api/heartbeat        -> GET 心跳（页面关闭 30s 后自动退出）
  /api/save-pdb         -> POST 保存 PDB 文件
  /api/prepare-reload   -> GET 切换到 loading 模式（返回 loading.html），延迟关闭服务
  /api/shutdown         -> GET 优雅关闭服务（延迟 500ms 退出，给 HTTP 响应时间发出）

会话隔离 & 过渡动画工作流:
  1. LLM 新会话启动前先 GET /__healthz，检查 session_id
  2. 有旧服务 → GET /api/prepare-reload（旧服务切 loading 模式，1.5s 后退出）
  3. LLM 调用 present_files loading URL（用户立刻看到过渡动画，无空白窗口）
  4. LLM 同时后台启动新服务（新 session_id），新服务接管同一端口
  5. loading.html 每 500ms 轮询 /__healthz，检测 session_id 变化 → 自动跳转到新 viewer

COS 依赖: omics-platform-cli (不依赖 coscli / Python COS SDK)
  - 安装: https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases
  - 登录: omics login
  - 认证: ~/.omics-platform-cli/auth.json 中的 session_id
  - 接口: POST https://omics.qq.com/omics/api/cgi (CosBucketService.GetObjectData)
  - 入参: {EnvironmentId, Bucket, Key} + Cookie: omics_session=<session_id>
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import random
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import queue
import urllib.parse
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Any

# ---------- handlers/ 目录加入 sys.path ----------
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# [DBG-IMPORT] 调试时取消注释以下两行以启用日志功能
# from debug_logger import dbg_log as _dbg_log, _debug_routes as _debug_routes_obj
# _debug_routes_obj, _dbg_log  # noqa: 防止未使用警告

# 调试桩：发布时保持以下两行，无需修改任何调用点
dbg_log = None           # 调试时由 [DBG-IMPORT] 赋值为 debug_logger.dbg_log
_debug_routes = None     # 调试时由 [DBG-IMPORT] 赋值为 debug_logger._debug_routes

# ---------- 导入拆分后的 handler 模块 ----------
import state
from handlers.cos_handler import (
    find_omics_cli, read_omics_session, read_omics_config,
    parse_cos_uri, fetch_pdb_from_omics,
    find_coscli, get_coscli_buckets,
    OMICS_BASE_URL, OMICS_CGI_PATH, OMICS_AUTH_FILE, OMICS_CONFIG_FILE, COS_REGIONS,
)
from handlers.pdb_filter import filter_pdb, copy_pdb
from handlers.static_server import StaticServerMixin
from handlers.sse_queue import enqueue_command, handle_sse_events, drain_poll_queue
from handlers.preload import set_preloaded, get_preloaded, clear_preloaded
from handlers.api_routes import (
    handle_preload, handle_ready, handle_command,
    handle_query_result_post, handle_export_pdb, handle_save_pdb,
)

# ---------- 路径与常量 ----------
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_VIEWER = SKILL_ROOT / "templates" / "viewer.html"
TEMPLATE_LOADING = SKILL_ROOT / "templates" / "loading.html"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
PID_FILE = str(SKILL_ROOT / ".pdb-viewer.pid")

# ---------- 会话标识（每次启动随机生成）----------
SESSION_ID = "%08x" % random.randint(0, 0xFFFFFFFF)

# ---------- 全局变量别名（从 state 模块映射，方便现有代码过渡）----------
# 注意：修改这些变量时，必须通过 state.xxx = ... 赋值，不能直接赋值给下面的别名
# （Python 赋值给局部名会创建新绑定，不会修改 state 中的对象）
# 如需读取，两者等效；如需写入，用 state.xxx = ...
_cmd_lock     = state.cmd_lock
_cmd_queue_ref = state.cmd_queue          # 列表对象引用（append/clear 直接操作）
_preload_lock = state.preload_lock
_query_lock   = state.query_lock
_hb_lock      = state.hb_lock
_activity_lock = state.activity_lock
_loading_lock = state.loading_lock
_server_lock  = state.server_lock
_sse_lock     = state.sse_lock
_sse_clients  = state.sse_clients         # 列表对象引用


# ════════════════════════════════════════════════
#  自定义 HTTP Handler
# ════════════════════════════════════════════════

class PdbViewerHandler(StaticServerMixin, SimpleHTTPRequestHandler):
    """PDB Viewer HTTP 请求处理器。
    业务逻辑委托给 handlers/ 各模块，本类只做路由分发。
    """
    server_version = "PdbViewerHTTP/1.1"

    # 挂载常量供 StaticServerMixin 使用
    TEMPLATE_VIEWER  = None   # 在 run_foreground() 中设置
    TEMPLATE_LOADING = None
    SESSION_ID       = ""

    def do_GET(self) -> None:  # noqa: N802
        """GET 请求路由分发。"""
        # state vars: last_heartbeat, loading_mode, loading_pdb_param, server_ref
        # [DBG-ROUTE] 调试路由检查（debug_logger.py 提供）
        if _debug_routes and _debug_routes.handle(self, urlparse(self.path).path):
            return
        parsed = urlparse(self.path)
        path = parsed.path

        # 更新最近活跃时间（除心跳轮询外的所有请求）
        if path != "/api/heartbeat":
            with state.activity_lock:
                _last_activity = None  # unused, via state
                state.last_activity = time.time()

        # ────────────────────────────────────────────────────────────
        # Loading 模式拦截：服务正在交接时，所有路由返回 loading.html
        # 例外：/__healthz 必须保持正常响应，以便 loading.html 轮询检测新服务
        # ────────────────────────────────────────────────────────────
        with state.loading_lock:
            is_loading = state.loading_mode
            loading_pdb = state.loading_pdb_param
        if is_loading and path != "/__healthz":
            return self._serve_loading(loading_pdb)

        # 根路径 / 直接返回 viewer.html（支持所有查询参数透传）
        if path == "/" or path == "":
            return self._serve_template(TEMPLATE_VIEWER)

        # ★ /view/<任意子路径>  ←  每次用不同路径，present_files 会真正 GET 加载
        # 例：/view/1784614350  /view/1784614350?pdb=cos://...
        # 这样面板无论处于什么状态，都会把每个 /view/<ts> 当作全新资源加载
        if path.startswith("/view/"):
            # 剥掉 /view/ 前缀，看剩余部分是否是静态资源（molstar.js / molstar.css 等）
            remainder = path[len("/view/"):]
            # 如果 remainder 是纯数字（时间戳）或带 ?pdb= 的时间戳 → 返回 viewer.html
            # 如果 remainder 包含扩展名（.js/.css/.wasm 等）→ 重定向到根路径
            import re as _re
            if remainder and not _re.match(r'^\d+$', remainder.split('?')[0]):
                # 静态资源：重定向到 /<remainder>
                redirect_target = '/' + remainder
                self.send_response(302)
                self.send_header("Location", redirect_target)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            return self._serve_template(TEMPLATE_VIEWER)

        # /loading/<ts>  ←  返回 loading.html（过渡动画），同理每次时间戳不同触发真正 GET
        if path.startswith("/loading/"):
            qs_params = parse_qs(parsed.query)
            pdb_param = qs_params.get("pdb", [""])[0]
            return self._serve_loading(pdb_param)

        if path == "/viewer.html":
            return self._serve_template(TEMPLATE_VIEWER)
        if path == "/__healthz":
            # 始终返回 session_id（loading 模式也返回，供 loading.html 轮询检测新服务）
            return self._serve_json({"status": "ok", "session_id": SESSION_ID})
        if path == "/__pid":
            return self._serve_text(str(os.getpid()))
        if path == "/__cos":
            return self._handle_cos_proxy(parsed.query)
        if path == "/__file":
            return self._handle_local_file(parsed.query)

        # ────────────────────────────────────────────────────────────
        # /api/prepare-reload  —  切换到 loading 模式，延迟关闭服务
        # LLM 调用流程：
        #   1. 先 GET /api/prepare-reload?pdb=<encoded_pdb_path>
        #   2. 立刻 present_files loading URL（用户看到动画）
        #   3. 同时后台启动新服务
        #   4. 本服务 1.5s 后自动退出，新服务接管端口
        #   5. loading.html 检测到 session_id 变化，自动跳转到新 viewer
        # ────────────────────────────────────────────────────────────
        if path == "/api/prepare-reload":
            qs_params = parse_qs(parsed.query)
            pdb_param = qs_params.get("pdb", [""])[0]
            with state.loading_lock:
                state.loading_mode = True
                state.loading_pdb_param = pdb_param
            # 延迟 1.5s 后关闭服务（给浏览器时间加载 loading.html）
            def _delayed_shutdown():
                time.sleep(1.5)
                with state.server_lock:
                    srv = state.server_ref
                if srv:
                    print("[pdb-viewer] prepare-reload: 关闭旧服务…")
                    threading.Thread(target=srv.shutdown, daemon=True).start()
            threading.Thread(target=_delayed_shutdown, daemon=True).start()
            return self._serve_json({
                "ok": True,
                "session_id": SESSION_ID,
                "message": "已切换到 loading 模式，服务将在 1.5s 后关闭",
            })

        # ────────────────────────────────────────────────────────────
        # /api/shutdown  —  优雅关闭服务（500ms 后退出）
        # 适用于：LLM 想直接杀旧服务而不需要过渡动画时
        # ────────────────────────────────────────────────────────────
        if path == "/api/shutdown":
            def _shutdown_soon():
                time.sleep(0.5)
                with state.server_lock:
                    srv = state.server_ref
                if srv:
                    print("[pdb-viewer] /api/shutdown: 关闭服务…")
                    threading.Thread(target=srv.shutdown, daemon=True).start()
            threading.Thread(target=_shutdown_soon, daemon=True).start()
            return self._serve_json({"ok": True, "message": "服务将在 0.5s 后关闭"})

        # ────────────────────────────────────────────────────────────
        # /api/reload  —  自动重定向到带时间戳的 viewer.html（兼容旧调用）
        # ────────────────────────────────────────────────────────────
        if path == "/api/reload":
            ts = int(time.time())
            # 透传 ?pdb= 参数
            qs_params = parse_qs(parsed.query)
            pdb_param = qs_params.get("pdb", [""])[0]
            extra = (f"&pdb={urllib.parse.quote(pdb_param, safe='')}" if pdb_param else "")
            target = f"/viewer.html?t={ts}{extra}"
            html = (
                f'<!DOCTYPE html><html><head>'
                f'<meta http-equiv="refresh" content="0; url={target}" />'
                f'<style>body{{background:#1a1d24;color:#7fd97f;font-family:monospace;'
                f'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}</style>'
                f'</head><body>'
                f'<p>正在跳转到 PDB Viewer…</p>'
                f'<script>location.replace("{target}");</script>'
                f'</body></html>'
            )
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        # --- API 端点 ---
        if path == "/api/status":
            with state.cmd_lock:
                queue_len = len(state.cmd_queue)
            with state.preload_lock:
                preloaded_name = state.preloaded_pdb.get("name") if state.preloaded_pdb else None
            with state.loading_lock:
                loading = state.loading_mode
            with state.sse_lock:
                sse_count = len(state.sse_clients)
            return self._serve_json({
                "status": "running",
                "pid": os.getpid(),
                "session_id": SESSION_ID,
                "default_pdb": state.default_pdb_url,
                "pending_commands": queue_len,
                "preloaded_pdb": preloaded_name,
                "loading_mode": loading,
                "sse_clients": sse_count,
            })

        # /api/preloaded-pdb  —  返回已预加载的 PDB 数据（浏览器优先读此缓存）
        if path == "/api/preloaded-pdb":
            with state.preload_lock:
                cache = state.preloaded_pdb
            if cache:
                return self._serve_json(cache)
            return self._serve_json({"error": "no preloaded pdb"}, status=404)

        if path == "/api/pdb-url":
            url = state.default_pdb_url or ""
            name = (
                Path(state.default_pdb_abs_path).name if state.default_pdb_abs_path
                else (Path(url).name if url else "unknown.pdb")
            )
            return self._serve_json({
                "url": url,
                "name": name,
                "path": state.default_pdb_abs_path or "",
            })

        if path == "/api/query-result":
            # LLM 读取浏览器推送的查询结果（list_chains / list_ligands 等）
            qs_params = parse_qs(parsed.query)
            op_filter = qs_params.get("op", [""])[0]
            with state.query_lock:
                if op_filter:
                    result = state.query_results.get(op_filter)
                    return self._serve_json(result if result else {"error": f"no result for op={op_filter}"}, status=200 if result else 404)
                else:
                    return self._serve_json(dict(state.query_results))

        if path == "/api/command-poll":
            cmds = []
            with state.cmd_lock:
                if state.cmd_queue:
                    cmds = list(state.cmd_queue)
                    state.cmd_queue.clear()
            return self._serve_json({"commands": cmds})

        if path == "/api/heartbeat":
            with state.hb_lock:
                state.last_heartbeat = time.time()
            return self._serve_text("ok")

        if path == "/api/events":
            """SSE 实时推送端点：命令入队后立即推送到浏览器。"""
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            client_q: queue.Queue = queue.Queue()
            with state.sse_lock:
                state.sse_clients.append(client_q)

            try:
                # 连接时立即 flush 已排队的命令
                with state.cmd_lock:
                    for cmd in state.cmd_queue:
                        try:
                            client_q.put_nowait(cmd)
                        except queue.Full:
                            pass
                    state.cmd_queue.clear()

                while True:
                    try:
                        cmd = client_q.get(timeout=30)
                        data = json.dumps(cmd, ensure_ascii=False)
                        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        # 心跳保活
                        self.wfile.write(b": hb\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                with state.sse_lock:
                    if client_q in state.sse_clients:
                        state.sse_clients.remove(client_q)
            return

        # 静态文件兜底（molstar.js / molstar.css 等）
        return super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        """HEAD 请求处理：对已知路由返回 200，避免 present_files 可达性检查失败。"""
        parsed = urlparse(self.path)
        path = parsed.path
        # 对所有已知路由返回 200 OK（不发 body）
        known = {
            "/", "/viewer.html", "/__healthz", "/__pid", "/__cos", "/__file",
            "/api/reload", "/api/prepare-reload", "/api/shutdown",
            "/api/status", "/api/pdb-url", "/api/command-poll",
            "/api/heartbeat", "/api/events", "/api/save-pdb",
        }
        if (path in known
                or path.startswith("/api/")
                or path.startswith("/__")
                or path.startswith("/view/")
                or path.startswith("/loading/")):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return
        # 静态文件兜底
        return super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802
        """POST 路由分发 — 全部委托给 handlers/api_routes.py。"""
        # [DBG-ROUTE] 调试路由检查
        if _debug_routes and _debug_routes.handle(self, urlparse(self.path).path):
            return
        parsed = urlparse(self.path)
        path = parsed.path

        route_map = {
            "/api/preload":       handle_preload,
            "/api/ready":         handle_ready,
            "/api/command":       handle_command,
            "/api/query-result":  handle_query_result_post,
            "/api/export-pdb":    handle_export_pdb,
            "/api/save-pdb":      handle_save_pdb,
        }
        handler_fn = route_map.get(path)
        if handler_fn:
            return handler_fn(self)

        # POST /api/heartbeat：浏览器 beforeunload 时用 sendBeacon 发 POST
        if path == "/api/heartbeat":
            with state.hb_lock:
                state.last_heartbeat = time.time()
            return self._serve_text("ok")

        # POST /api/screenshot-save — 浏览器将截图 base64 数据发送到服务端保存（验证用）
        if path == "/api/screenshot-save":
            content_len = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                body = {}
            img_data = body.get("data", "")
            filename = body.get("filename", "screenshot.png")
            save_dir = body.get("save_dir", "/tmp/pdb-verify-screenshots")
            if img_data:
                import base64 as _b64
                os.makedirs(save_dir, exist_ok=True)
                # data 可能是 data:image/png;base64,xxxx 格式，去掉前缀
                if "," in img_data:
                    img_data = img_data.split(",", 1)[1]
                save_path = os.path.join(save_dir, filename)
                with open(save_path, "wb") as f:
                    f.write(_b64.b64decode(img_data))
                print(f"[pdb-viewer] screenshot saved: {save_path}")
                return self._serve_json({"ok": True, "path": save_path})
            return self._serve_json({"error": "no data"}, status=400)

        self.send_error(404, f"POST {path} not found")

    def translate_path(self, path: str) -> str:
        """重写路径解析：templates/ 目录下的静态文件（molstar.js/css）可从根路径访问。"""
        path = urllib.parse.unquote(path, errors="surrogatepass")
        sep = os.sep
        if sep != '/':
            path = path.replace('/', sep)
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]

        # API 和代理路由由 do_GET 处理，不走静态文件
        for prefix in ('/__cos', '/__file', '/__healthz', '/__pid', '/api/'):
            if path.startswith(prefix):
                return ''

        full = os.path.join(os.getcwd(), path.lstrip('/'))
        # Fallback: 根目录找不到时尝试 templates/ 子目录
        if not os.path.isfile(full) and not os.path.isdir(full):
            templates_dir = os.path.join(os.getcwd(), 'templates')
            alt = os.path.join(templates_dir, path.lstrip('/'))
            if os.path.isfile(alt) or os.path.isdir(alt):
                full = alt
        if os.path.isdir(full):
            for index in ("index.html", "index.htm"):
                idx = os.path.join(full, index)
                if os.path.isfile(idx):
                    return idx
        return full


# ════════════════════════════════════════════════
#  工具函数
# ════════════════════════════════════════════════

def find_free_port(host: str, preferred: int) -> int:
    """尝试绑定首选端口，被占用则返回随机可用端口。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, preferred))
        port = s.getsockname()[1]
        s.close()
        return port
    except OSError:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, 0))
        port = s.getsockname()[1]
        s.close()
        return port


def write_pid_file() -> None:
    Path(PID_FILE).write_text(str(os.getpid()), encoding="utf-8")


def read_pid_file() -> int | None:
    p = Path(PID_FILE)
    if not p.exists():
        return None
    try:
        return int(p.read_text("utf-8").strip())
    except (ValueError, OSError):
        return None


def stop_daemon() -> bool:
    pid = read_pid_file()
    if pid is None:
        print("No PID file found, nothing to stop.")
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
        try:
            os.kill(pid, 0)
        except OSError:
            pass
        print(f"Stopped pdb-viewer (pid={pid}).")
    except OSError as exc:
        print(f"Failed to stop pid={pid}: {exc}")
        return False
    try:
        Path(PID_FILE).unlink()
    except OSError:
        pass
    return True


# ════════════════════════════════════════════════
#  服务运行
# ════════════════════════════════════════════════

def run_foreground(
    serve_dir: Path,
    host: str,
    port: int,
    pdb_file: str | None = None,
    no_watchdog: bool = False,
    idle_timeout: int = 600,
) -> None:
    global _default_pdb_url, _default_pdb_abs_path, _server_ref, _last_activity  # legacy kept for compat
    serve_dir = serve_dir.resolve()
    if not serve_dir.is_dir():
        print(f"Error: serve directory does not exist: {serve_dir}", file=sys.stderr)
        sys.exit(2)

    port = find_free_port(host, port)
    os.chdir(serve_dir)

    if pdb_file:
        abs_pdb = Path(pdb_file).expanduser().resolve()
        state.default_pdb_url = f"/__file?path={urllib.parse.quote(str(abs_pdb))}"
        state.default_pdb_abs_path = str(abs_pdb)
        print(f"[pdb-viewer] default file: {abs_pdb} ({abs_pdb.stat().st_size} bytes)")
    else:
        state.default_pdb_url = None
        state.default_pdb_abs_path = None

    server = ThreadingHTTPServer((host, port), PdbViewerHandler)
    # 挂载常量供 StaticServerMixin 使用
    PdbViewerHandler.TEMPLATE_VIEWER  = TEMPLATE_VIEWER
    PdbViewerHandler.TEMPLATE_LOADING = TEMPLATE_LOADING
    PdbViewerHandler.SESSION_ID       = SESSION_ID
    with state.server_lock:
        state.server_ref = server

    # [DBG-INIT] 调试时初始化日志模块（debug_logger.py 提供 init 函数）
    # 注意：dbg_log 和 _debug_routes 已在文件顶部由 [DBG-IMPORT] 设置，
    # 此处仅在模块已导入时调用 init（避免 NameError）
    try:
        import debug_logger as _dl_mod
        if hasattr(_dl_mod, 'init'):
            _dl_mod.init(SKILL_ROOT, SESSION_ID)
    except ImportError:
        pass  # debug_logger.py 未安装，正常发布模式

    cli = find_omics_cli()
    _, session_valid = read_omics_session()
    coscli_bin = find_coscli()
    coscli_buckets = get_coscli_buckets()
    print(f"[pdb-viewer] session_id: {SESSION_ID}")
    print(f"[pdb-viewer] serving {serve_dir} at http://{host}:{port}")
    print(f"[pdb-viewer] viewer template: {TEMPLATE_VIEWER}")
    print(f"[pdb-viewer] loading template: {TEMPLATE_LOADING}")
    print(f"[pdb-viewer] omics CLI: {cli or '(未安装)'}")
    print(f"[pdb-viewer] omics 登录态: {'✓ 有效' if session_valid else '✗ 未登录或已过期 (执行 omics login)'}")
    print(f"[pdb-viewer] omics API: {OMICS_BASE_URL}")
    print(f"[pdb-viewer] coscli: {coscli_bin or '(未安装)'}")
    if coscli_buckets:
        print(f"[pdb-viewer] coscli 已配置桶: {', '.join(coscli_buckets)}")
    else:
        print(f"[pdb-viewer] coscli 已配置桶: (无，cos:// URI 将走 omics 通道)")
    print(f"[pdb-viewer] idle_timeout: {idle_timeout}s  (pid={os.getpid()})  (Ctrl-C to stop)")

    def _shutdown(signum, frame):
        print("\n[pdb-viewer] shutting down…")
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 初始化活跃时间
    with state.activity_lock:
        state.last_activity = time.time()

    # 心跳看门狗：无心跳则标记面板离线（服务继续，等空闲超时再退出）
    _watcher_stop = threading.Event()
    if not no_watchdog:
        def _heartbeat_watchdog() -> None:
            with state.hb_lock:
                state.last_heartbeat = time.time() + 20  # 启动后给 20 秒宽限
            while not _watcher_stop.wait(timeout=5):
                with state.hb_lock:
                    hb_gap = time.time() - state.last_heartbeat
                if hb_gap > state.heartbeat_timeout:
                    # 面板已离线，但服务继续运行，等待空闲超时或新会话接管
                    pass  # 不再自动退出，改由空闲超时控制

        threading.Thread(target=_heartbeat_watchdog, daemon=True).start()

        # 空闲超时看门狗：完全无 API 调用时自动退出
        if idle_timeout > 0:
            def _idle_watchdog() -> None:
                # 启动后给额外宽限（molstar.js 下载可能需要一段时间）
                extra_grace = 60
                time.sleep(extra_grace)
                while not _watcher_stop.wait(timeout=30):
                    with state.activity_lock:
                        gap = time.time() - state.last_activity
                    if gap > idle_timeout:
                        print(f"\n[pdb-viewer] 空闲超时 ({gap:.0f}s 无活动)，自动退出…")
                        threading.Thread(target=server.shutdown, daemon=True).start()
                        return

            threading.Thread(target=_idle_watchdog, daemon=True).start()
        else:
            print(f"[pdb-viewer] 空闲超时已禁用 (--idle-timeout=0)")
    else:
        print(f"[pdb-viewer] 心跳看门狗已禁用 (--no-watchdog)")

    try:
        server.serve_forever()
    finally:
        _watcher_stop.set()
        server.server_close()
        with state.server_lock:
            state.server_ref = None
        # 方案 A: 服务退出时清理所有跳板文件
        import glob as _glob
        for _f in _glob.glob("/tmp/pdb_jump_*.html"):
            try:
                os.remove(_f)
            except OSError:
                pass


def run_daemon(
    serve_dir: Path,
    host: str,
    port: int,
    pdb_file: str | None = None,
) -> None:
    global _default_pdb_url
    serve_dir = serve_dir.resolve()
    if not serve_dir.is_dir():
        print(f"Error: serve directory does not exist: {serve_dir}", file=sys.stderr)
        sys.exit(2)

    if read_pid_file() is not None:
        print("A pdb-viewer instance appears to be running. Use --stop first.", file=sys.stderr)
        sys.exit(3)

    port = find_free_port(host, port)

    pid = os.fork()
    if pid > 0:
        for _ in range(50):
            if Path(PID_FILE).exists():
                time.sleep(0.05)
                print(f"[pdb-viewer] daemon started, pid={Path(PID_FILE).read_text('utf-8').strip()}, http://{host}:{port}")
                return
            time.sleep(0.1)
        print("[pdb-viewer] daemon started, but PID file not detected yet.", file=sys.stderr)
        return

    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)

    os.chdir(serve_dir)
    sys.stdin = open(os.devnull, "r")
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

    write_pid_file()

    if pdb_file:
        abs_pdb = Path(pdb_file).expanduser().resolve()
        _default_pdb_url = f"/__file?path={urllib.parse.quote(str(abs_pdb))}"

    server = ThreadingHTTPServer((host, port), PdbViewerHandler)
    try:
        server.serve_forever()
    finally:
        try:
            Path(PID_FILE).unlink()
        except OSError:
            pass
        server.server_close()


# ════════════════════════════════════════════════
#  CLI 入口
# ════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PDB Viewer 本地 HTTP 服务器（Mol* 5.9.0 本地自托管 + omics COS 支持）"
    )
    parser.add_argument("directory", nargs="?", help="要 serve 的目录（通常为 SKILL_ROOT）")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"绑定地址 (默认 {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"绑定端口 (默认 {DEFAULT_PORT})")
    parser.add_argument("--pdb-file", default=None, dest="pdb_file",
                        help="默认加载的 PDB 文件绝对路径（服务启动后自动推送到浏览器）")
    parser.add_argument("--daemon", action="store_true", help="后台守护进程模式")
    parser.add_argument("--no-watchdog", action="store_true", dest="no_watchdog",
                        help="禁用心跳看门狗（服务不会因页面关闭而自动退出）")
    parser.add_argument("--idle-timeout", type=int, default=600, dest="idle_timeout",
                        help="空闲超时秒数（默认 600s，设为 0 禁用）。完全无 API 调用时自动退出释放端口。")
    parser.add_argument("--stop", action="store_true", help="停止后台进程")
    parser.add_argument("--status", action="store_true", help="查询后台进程状态")
    args = parser.parse_args()

    if args.stop:
        return 0 if stop_daemon() else 1

    if args.status:
        pid = read_pid_file()
        if pid is None:
            print("pdb-viewer: not running")
            return 1
        try:
            os.kill(pid, 0)
            print(f"pdb-viewer: running (pid={pid})")
            return 0
        except OSError:
            print(f"pdb-viewer: stale PID file (pid={pid} not alive)")
            return 1

    if not args.directory:
        # 未指定目录时默认用 SKILL_ROOT
        args.directory = str(SKILL_ROOT)

    serve_dir = Path(args.directory).expanduser()

    if not TEMPLATE_VIEWER.exists():
        print(f"Error: viewer template missing: {TEMPLATE_VIEWER}", file=sys.stderr)
        return 2

    if args.daemon:
        run_daemon(serve_dir, args.host, args.port, args.pdb_file)
    else:
        run_foreground(serve_dir, args.host, args.port, args.pdb_file, args.no_watchdog, args.idle_timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
