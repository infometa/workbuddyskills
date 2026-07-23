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
  /api/log              -> POST 前端执行日志
  /api/logs             -> GET 执行日志读取
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

# ---------- 路径与常量 ----------
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_VIEWER = SKILL_ROOT / "templates" / "viewer.html"
TEMPLATE_LOADING = SKILL_ROOT / "templates" / "loading.html"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
PID_FILE = str(SKILL_ROOT / ".pdb-viewer.pid")
# [DEL-BEFORE-PUB] 日志文件路径定义（发布前删除此行及所有日志相关代码）
LOG_FILE = str(SKILL_ROOT / ".pdb-viewer.log")

# ---------- 会话标识（每次启动随机生成，用于浏览器侧检测新旧服务） ----------
SESSION_ID = "%08x" % random.randint(0, 0xFFFFFFFF)

# ---------- omics 配置（正式环境） ----------
OMICS_BASE_URL = "https://omics.qq.com"
OMICS_CGI_PATH = "/omics/api/cgi"
OMICS_AUTH_FILE = Path.home() / ".omics-platform-cli" / "auth.json"
OMICS_CONFIG_FILE = Path.home() / ".omics-platform-cli" / "omics_config.json"

# COS 地域白名单（用于区分 cos://bucket/region/key 与 cos://bucket/key）
COS_REGIONS = {
    "ap-beijing", "ap-shanghai", "ap-guangzhou", "ap-chengdu",
    "ap-chongqing", "ap-nanjing", "ap-hongkong", "ap-singapore",
    "ap-seoul", "ap-tokyo", "ap-bangkok", "ap-mumbai", "ap-jakarta",
    "na-toronto", "na-siliconvalley", "na-ashburn",
    "sa-saopaulo", "eu-frankfurt", "eu-moscow",
}

# ---------- 命令队列（自然语言控制） ----------
_command_queue: list[dict] = []
_cmd_lock = threading.Lock()
_default_pdb_url: str | None = None
_default_pdb_abs_path: str | None = None  # 服务端绝对路径（供 /api/save-pdb 使用）

# 预加载缓存：服务端主动读取文件，浏览器打开时直接命中缓存
# 由 POST /api/preload 触发，LLM 在 present_files 前调用
_preloaded_pdb: dict | None = None   # {"data": base64, "name": str, "uri": str}
_preload_lock = threading.Lock()

# 心跳机制：页面关闭时自动释放端口
_last_heartbeat = 0.0
_hb_lock = threading.Lock()
_heartbeat_timeout = 30  # 30 秒无心跳则标记"面板已离线"（服务继续）

# 空闲超时：完全无任何 API 调用时自动退出
_last_activity = 0.0   # 记录最近一次 API 调用时间
_activity_lock = threading.Lock()

# Loading 模式：服务正在交接，所有路由返回 loading.html（除 /__healthz）
_loading_mode = False
_loading_lock = threading.Lock()
_loading_pdb_param: str = ""   # 透传给 loading.html 的 pdb 参数

# 全局 server 引用（供 /api/shutdown 使用）
_server_ref: ThreadingHTTPServer | None = None
_server_lock = threading.Lock()

# [DEL-BEFORE-PUB] 执行日志收集（发布前删除此变量及所有 _exec_logs 引用）
_exec_logs: list[str] = []
_log_lock = threading.Lock()
MAX_LOG_SIZE = 200

# ---------- SSE 实时推送 ----------
_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()


# ════════════════════════════════════════════════
#  omics CLI / 认证工具函数
# ════════════════════════════════════════════════

def find_omics_cli() -> str | None:
    """查找 omics-platform-cli 可执行文件。返回路径或 None。"""
    local_bin = Path.home() / ".local" / "bin" / "omics"
    if local_bin.is_file() and os.access(local_bin, os.X_OK):
        return str(local_bin)
    return shutil.which("omics")


def read_omics_session() -> tuple[str, bool]:
    """读取 omics 登录态。
    返回 (session_id, is_valid):
      - session_id: 非空字符串（若已登录）
      - is_valid: True 表示 session 存在且未过期
    """
    if not OMICS_AUTH_FILE.exists():
        return "", False
    try:
        auth = json.loads(OMICS_AUTH_FILE.read_text("utf-8"))
        session_id = auth.get("session_id", "")
        expires_at = auth.get("expires_at", 0)
        if not session_id:
            return "", False
        # expires_at == 0 表示无过期限制
        if expires_at > 0 and time.time() > expires_at:
            return session_id, False  # 已过期
        return session_id, True
    except (OSError, ValueError, KeyError):
        return "", False


def read_omics_config() -> dict[str, Any]:
    """读取 omics-platform-cli 配置（EnvironmentId 等）。"""
    try:
        if OMICS_CONFIG_FILE.is_file():
            data = json.loads(OMICS_CONFIG_FILE.read_text("utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def parse_cos_uri(uri: str) -> tuple[str, str]:
    """解析 cos:// URI，返回 (bucket, key)。region 段自动识别并丢弃。
    支持两种格式:
      cos://<bucket>/<region>/<key>  →  region 通过白名单识别，丢弃
      cos://<bucket>/<key>
    """
    if not uri.startswith("cos://"):
        return "", ""
    rest = uri[len("cos://"):]
    parts = rest.split("/", 2)
    if len(parts) < 2:
        return "", ""
    bucket = parts[0]
    if len(parts) == 3 and parts[1] in COS_REGIONS:
        key = parts[2]
    else:
        key = parts[1] if len(parts) == 2 else f"{parts[1]}/{parts[2]}"
    return bucket, key


def fetch_pdb_from_omics(uri: str) -> tuple[bytes, str]:
    """通过 omics-platform-cli 认证调用 CosBucketService.GetObjectData 读取 COS 上的 PDB 文件。

    完整流程:
      1. 检查 omics CLI 是否安装
      2. 读取 ~/.omics-platform-cli/auth.json 中的 session_id
      3. 读取 ~/.omics-platform-cli/omics_config.json 中的 EnvironmentId
      4. 解析 cos:// URI → bucket + key（region 丢弃）
      5. POST /omics/api/cgi (CosBucketService.GetObjectData)
         入参: {EnvironmentId, Bucket, Key}，通过 Cookie 传 session_id
      6. 返回 (raw_bytes, file_name)

    抛异常时包含友好的错误信息和操作引导。
    """
    # --- 1. 检查 CLI 是否安装 ---
    cli = find_omics_cli()
    if cli is None:
        raise RuntimeError(
            "omics-platform-cli 未安装。\n"
            "请从官方 Release 页面下载对应平台的二进制文件：\n"
            "  https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases\n"
            "安装后执行 omics login 完成登录授权。"
        )

    # --- 2. 读取登录态 ---
    session_id, is_valid = read_omics_session()
    if not session_id:
        raise RuntimeError(
            "未检测到 omics 登录凭证 (~/.omics-platform-cli/auth.json)。\n"
            "请执行: omics login"
        )
    if not is_valid:
        raise RuntimeError(
            "omics 登录凭证已过期。\n"
            "请执行: omics login"
        )

    # --- 3. 读取 EnvironmentId ---
    config = read_omics_config()
    env_id = config.get("EnvironmentId", "")

    # --- 4. 解析 COS URI ---
    bucket, key = parse_cos_uri(uri)
    if not bucket or not key:
        raise ValueError(f"无效的 COS URI: {uri}，期望格式 cos://<bucket>/[<region>/]<key>")
    if not key.lower().endswith(".pdb"):
        raise ValueError(f"文件路径必须以 .pdb 结尾: {key}")
    file_name = key.rsplit("/", 1)[-1] if "/" in key else key

    # --- 5. 调用 CosBucketService.GetObjectData ---
    url = OMICS_BASE_URL + OMICS_CGI_PATH
    payload = {
        "id": str(int(time.time())),  # id 必须是字符串类型
        "jsonrpc": "2.0",
        "method": "CosBucketService.GetObjectData",
        "params": {
            "EnvironmentId": env_id,
            "Bucket": bucket,
            "Key": key,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Origin": OMICS_BASE_URL,
        "Referer": f"{OMICS_BASE_URL}/",
        "Cookie": f"omics_session={session_id}",
    }

    # 必须用 separators=(',',':') 紧凑格式，带空格会导致服务端 JSON-RPC 解析 400
    data = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, 'read') else ''
        raise RuntimeError(f"GetObjectData HTTP {exc.code}: {raw[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络请求失败: {exc.reason}") from exc

    # JSON-RPC 错误处理
    if "error" in result:
        err = result["error"]
        err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        code = err.get("code", "") if isinstance(err, dict) else ""
        if any(kw in err_msg.lower() for kw in ("401", "403", "session", "unauthorized")):
            raise RuntimeError(
                f"omics 登录凭证已失效 [{code}]: {err_msg}\n"
                "请执行: omics login"
            )
        raise RuntimeError(f"GetObjectData 失败 [{code}]: {err_msg}")

    result_obj = result.get("result", {})
    # 响应字段 Data 大写（与后端 Go struct json tag 一致）
    b64_data = result_obj.get("Data", "")
    if not b64_data:
        raise RuntimeError(
            f"GetObjectData 返回空数据 (bucket={bucket}, key={key})\n"
            "可能原因: bucket/key 不存在、无访问权限、或 EnvironmentId 配置错误"
        )

    try:
        raw = base64.b64decode(b64_data)
    except Exception as exc:
        raise RuntimeError(f"GetObjectData 返回的 base64 数据解码失败: {exc}") from exc

    return raw, file_name


# ════════════════════════════════════════════════
#  自定义 HTTP Handler
# ════════════════════════════════════════════════

class PdbViewerHandler(SimpleHTTPRequestHandler):
    server_version = "PdbViewerHTTP/1.1"

    # [DEL-BEFORE-PUB] 日志写入方法（发布前删除整个方法）
    def log_message(self, fmt: str, *args) -> None:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write("%s - - [%s] %s\n" % (
                    self.address_string(),
                    self.log_date_time_string(),
                    fmt % args,
                ))
        except Exception:
            pass

    def _serve_template(self, path: Path) -> None:
        if not path.exists():
            self.send_error(404, f"Template not found: {path}")
            return
        try:
            body = path.read_bytes()
        except OSError as exc:
            self.send_error(500, f"Read failed: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_text(self, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def _handle_cos_proxy(self, query: str) -> None:
        """COS 代理路由: /__cos?uri=cos://bucket/[region/]key
        流程: omics 认证 → POST CosBucketService.GetObjectData → base64 JSON 返回
        返回 JSON: {"data": "<base64>", "name": "xxx.pdb"}
        错误返回 JSON: {"error": "...", "action": "login"/"install"/"..."}
        """
        params = parse_qs(query)
        uri_list = params.get("uri", [])
        if not uri_list:
            self._serve_json({"error": "missing 'uri' parameter"}, status=400)
            return
        uri = uri_list[0]
        try:
            raw_bytes, file_name = fetch_pdb_from_omics(uri)
            b64_data = base64.b64encode(raw_bytes).decode("ascii")
            self._serve_json({
                "data": b64_data,
                "name": file_name,
                "uri": uri,
            })
        except RuntimeError as exc:
            msg = str(exc)
            action = "unknown"
            if "未安装" in msg:
                action = "install"
            elif "omics login" in msg or "已过期" in msg or "未检测到" in msg:
                action = "login"
            self._serve_json({"error": msg, "action": action, "uri": uri}, status=500)
        except ValueError as exc:
            self._serve_json({"error": str(exc), "action": "invalid_uri", "uri": uri}, status=400)
        except Exception as exc:
            self._serve_json({"error": str(exc), "action": "unknown", "uri": uri}, status=500)

    def _handle_local_file(self, query: str) -> None:
        """本地文件代理路由: /__file?path=/abs/path/to/file.pdb
        读取本机绝对路径的 pdb 文件，base64 编码后 JSON 返回。
        """
        params = parse_qs(query)
        path_list = params.get("path", [])
        if not path_list:
            self._serve_json({"error": "missing 'path' parameter"}, status=400)
            return
        abs_path = Path(urllib.parse.unquote(path_list[0]))
        if not abs_path.is_absolute():
            self._serve_json({"error": f"path 必须是绝对路径: {abs_path}"}, status=400)
            return
        if not abs_path.exists():
            self._serve_json({"error": f"文件不存在: {abs_path}"}, status=404)
            return
        if not abs_path.is_file():
            self._serve_json({"error": f"不是文件: {abs_path}"}, status=400)
            return
        if abs_path.suffix.lower() not in (".pdb", ".cif", ".mmcif"):
            self._serve_json({"error": f"仅支持 .pdb/.cif/.mmcif 文件，实际: {abs_path.name}"}, status=400)
            return
        try:
            content = abs_path.read_bytes()
            b64_data = base64.b64encode(content).decode("ascii")
            self._serve_json({
                "data": b64_data,
                "name": abs_path.name,
                "path": str(abs_path),
            })
        except OSError as exc:
            self._serve_json({"error": f"读取文件失败: {exc}"}, status=500)

    def _serve_loading(self, pdb_param: str = "") -> None:
        """返回 loading.html（过渡动画页面）。
        将 pdb_param 和当前 session_id 注入到页面中，
        loading.html 轮询 /__healthz 检测 session_id 变化后自动跳转。
        """
        if TEMPLATE_LOADING.exists():
            try:
                html = TEMPLATE_LOADING.read_text("utf-8")
                # 注入当前 session_id 和 pdb 参数（供 loading.html 的轮询逻辑使用）
                html = html.replace(
                    "/* __INJECT_SESSION_ID__ */",
                    f"var CURRENT_SESSION_ID = '{SESSION_ID}';"
                )
                html = html.replace(
                    "/* __INJECT_PDB_PARAM__ */",
                    f"var PDB_PARAM = '{urllib.parse.quote(pdb_param, safe='')}';"
                )
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            except OSError:
                pass
        # loading.html 不存在时降级到简单文本
        html_fallback = (
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<title>正在加载…</title>'
            '<style>body{background:#1a1d24;color:#7fd97f;font-family:monospace;'
            'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}'
            '</style></head><body><p>正在加载新结构…</p>'
            f'<script>/* __INJECT_SESSION_ID__ */ var CURRENT_SESSION_ID = "{SESSION_ID}";'
            f'/* __INJECT_PDB_PARAM__ */ var PDB_PARAM = "{urllib.parse.quote(pdb_param, safe="")}";'
            'setInterval(function(){'
            'fetch("/__healthz",{cache:"no-store"}).then(r=>r.json()).then(d=>{'
            'if(d.session_id && d.session_id !== CURRENT_SESSION_ID){'
            'var ts=Date.now();var url="/view/"+ts+(PDB_PARAM?"?pdb="+PDB_PARAM:"");'
            'location.replace(url);}}).catch(()=>{});},500);</script></body></html>'
        )
        body = html_fallback.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        """GET 请求路由分发。"""
        global _last_heartbeat, _exec_logs, _loading_mode, _loading_pdb_param, _server_ref
        parsed = urlparse(self.path)
        path = parsed.path

        # 更新最近活跃时间（除心跳轮询外的所有请求）
        if path != "/api/heartbeat":
            with _activity_lock:
                global _last_activity
                _last_activity = time.time()

        # ────────────────────────────────────────────────────────────
        # Loading 模式拦截：服务正在交接时，所有路由返回 loading.html
        # 例外：/__healthz 必须保持正常响应，以便 loading.html 轮询检测新服务
        # ────────────────────────────────────────────────────────────
        with _loading_lock:
            is_loading = _loading_mode
            loading_pdb = _loading_pdb_param
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
            with _loading_lock:
                _loading_mode = True
                _loading_pdb_param = pdb_param
            # 延迟 1.5s 后关闭服务（给浏览器时间加载 loading.html）
            def _delayed_shutdown():
                time.sleep(1.5)
                with _server_lock:
                    srv = _server_ref
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
                with _server_lock:
                    srv = _server_ref
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
            with _cmd_lock:
                queue_len = len(_command_queue)
            with _preload_lock:
                preloaded_name = _preloaded_pdb.get("name") if _preloaded_pdb else None
            with _loading_lock:
                loading = _loading_mode
            return self._serve_json({
                "status": "running",
                "pid": os.getpid(),
                "session_id": SESSION_ID,
                "default_pdb": _default_pdb_url,
                "pending_commands": queue_len,
                "preloaded_pdb": preloaded_name,
                "loading_mode": loading,
            })

        # /api/preloaded-pdb  —  返回已预加载的 PDB 数据（浏览器优先读此缓存）
        if path == "/api/preloaded-pdb":
            with _preload_lock:
                cache = _preloaded_pdb
            if cache:
                return self._serve_json(cache)
            return self._serve_json({"error": "no preloaded pdb"}, status=404)

        if path == "/api/pdb-url":
            url = _default_pdb_url or ""
            name = (
                Path(_default_pdb_abs_path).name if _default_pdb_abs_path
                else (Path(url).name if url else "unknown.pdb")
            )
            return self._serve_json({
                "url": url,
                "name": name,
                "path": _default_pdb_abs_path or "",
            })

        if path == "/api/command-poll":
            cmds = []
            with _cmd_lock:
                if _command_queue:
                    cmds = list(_command_queue)
                    _command_queue.clear()
            return self._serve_json({"commands": cmds})

        if path == "/api/heartbeat":
            with _hb_lock:
                _last_heartbeat = time.time()
            return self._serve_text("ok")

        # [DEL-BEFORE-PUB] 日志读取 API（发布前删除此路由块）
        if path == "/api/logs":
            with _log_lock:
                recent = list(_exec_logs[-60:])
            return self._serve_json({"logs": recent})

        if path == "/api/events":
            """SSE 实时推送端点：命令入队后立即推送到浏览器。"""
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            client_q: queue.Queue = queue.Queue()
            with _sse_lock:
                _sse_clients.append(client_q)

            try:
                # 连接时立即 flush 已排队的命令
                with _cmd_lock:
                    for cmd in _command_queue:
                        try:
                            client_q.put_nowait(cmd)
                        except queue.Full:
                            pass
                    _command_queue.clear()

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
                with _sse_lock:
                    if client_q in _sse_clients:
                        _sse_clients.remove(client_q)
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
            "/api/heartbeat", "/api/logs", "/api/events", "/api/log", "/api/save-pdb",
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
        global _exec_logs, _preloaded_pdb
        parsed = urlparse(self.path)
        path = parsed.path

        # /api/preload  —  LLM 在 present_files 之前调用，服务端主动读取文件到内存
        # 支持 uri=cos://... 或 uri=/__file?path=... 或 uri=/abs/path/to/file.pdb
        if path == "/api/preload":
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._serve_json({"error": "invalid JSON"}, status=400)
            uri = body.get("uri", "")
            if not uri:
                return self._serve_json({"error": "missing 'uri'"}, status=400)
            try:
                if uri.startswith("cos://"):
                    raw_bytes, file_name = fetch_pdb_from_omics(uri)
                    b64 = base64.b64encode(raw_bytes).decode("ascii")
                else:
                    # 本地绝对路径
                    abs_path = Path(uri).expanduser().resolve()
                    if not abs_path.exists():
                        return self._serve_json({"error": f"文件不存在: {abs_path}"}, status=404)
                    raw_bytes = abs_path.read_bytes()
                    b64 = base64.b64encode(raw_bytes).decode("ascii")
                    file_name = abs_path.name
                with _preload_lock:
                    _preloaded_pdb = {"data": b64, "name": file_name, "uri": uri}
                return self._serve_json({
                    "ok": True,
                    "name": file_name,
                    "bytes": len(raw_bytes),
                    "cached": True,
                })
            except Exception as exc:
                return self._serve_json({"error": str(exc)}, status=500)

        # /api/ready  —  浏览器 Mol* 初始化完成 + SSE/轮询就绪后主动通知
        # 服务端收到后，若有预加载缓存则自动推送 get_pdb 命令（无需 LLM sleep 等待）
        if path == "/api/ready":
            with _preload_lock:
                cached = _preloaded_pdb.copy() if _preloaded_pdb else None
            if cached:
                # 构造 get_pdb 命令，把预加载的 URI 推送给浏览器执行
                uri = cached.get("uri", "")
                cmd_entry = {"op": "get_pdb", "params": {"url": uri}}
                with _cmd_lock:
                    _command_queue.append(cmd_entry)
                with _sse_lock:
                    for cq in _sse_clients:
                        try:
                            cq.put_nowait(cmd_entry)
                        except queue.Full:
                            pass
                print(f"[pdb-viewer] /api/ready: 浏览器就绪，自动推送 get_pdb → {uri}")
                return self._serve_json({"ok": True, "pushed": cmd_entry})
            else:
                # 无预加载缓存（手动场景），仅确认就绪
                print("[pdb-viewer] /api/ready: 浏览器就绪，无预加载缓存")
                return self._serve_json({"ok": True, "pushed": None})

        if path == "/api/command":
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._serve_json({"error": "invalid JSON"}, status=400)

            # 兼容两种格式:
            #   新格式: { "op": "set_repr", "params": {"repr": "ball-and-stick"} }
            #   旧格式: { "action": "set_representation", "type": "ball_and_stick" }
            op = body.get("op") or body.get("action", "")
            params = body.get("params", {})
            if not params:
                params = {k: v for k, v in body.items() if k not in ("op", "action", "params")}

            if op and isinstance(op, str):
                cmd_entry = {"op": op, "params": params}
                with _cmd_lock:
                    _command_queue.append(cmd_entry)
                # 实时推送：通知所有 SSE 客户端
                with _sse_lock:
                    for cq in _sse_clients:
                        try:
                            cq.put_nowait(cmd_entry)
                        except queue.Full:
                            pass
                return self._serve_json({"ok": True, "queued": cmd_entry})

            return self._serve_json({"error": "missing or invalid 'op'/'action'"}, status=400)

        # [DEL-BEFORE-PUB] 日志写入 API（发布前删除此路由块）
        if path == "/api/log":
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._serve_json({"error": "invalid JSON"}, status=400)
            msg = body.get("msg", "")
            level = body.get("level", "info")
            ts = time.strftime("%H:%M:%S")
            entry = f"[{ts}] [{level}] {msg}"
            with _log_lock:
                _exec_logs.append(entry)
                if len(_exec_logs) > MAX_LOG_SIZE:
                    _exec_logs = _exec_logs[-MAX_LOG_SIZE:]
            return self._serve_json({"ok": True})

        if path == "/api/save-pdb":
            """用户确认后保存 PDB 文件
            支持两种模式:
            1. 覆盖已有文件: 先备份 .bak，再写入
            2. 保存到新路径 (create_if_missing): 直接创建新文件
            """
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._serve_json({"error": "invalid JSON"}, status=400)

            file_path_str = body.get("path", "")
            pdb_data = body.get("data", "")
            action = body.get("action", "backup")
            create_if_missing = body.get("create_if_missing", False)

            if not file_path_str:
                return self._serve_json({"error": "missing 'path' parameter"}, status=400)

            abs_path = Path(file_path_str).expanduser().resolve()
            if abs_path.suffix.lower() not in (".pdb", ".cif", ".mmcif"):
                return self._serve_json({"error": "仅支持 .pdb/.cif/.mmcif 文件"}, status=400)

            # 模式 1: 文件已存在 → 备份 + 写入
            if abs_path.exists():
                backup_path = abs_path.with_suffix(abs_path.suffix + ".bak")
                try:
                    shutil.copy2(str(abs_path), str(backup_path))
                except OSError as exc:
                    return self._serve_json({"error": f"备份失败: {exc}"}, status=500)

                if action == "overwrite" and pdb_data:
                    try:
                        abs_path.write_text(pdb_data, encoding="utf-8")
                        return self._serve_json({
                            "ok": True,
                            "saved": str(abs_path),
                            "backup_path": str(backup_path),
                        })
                    except OSError as exc:
                        return self._serve_json({"error": f"写入失败: {exc}"}, status=500)
                else:
                    return self._serve_json({
                        "ok": True,
                        "action": "backup_only",
                        "original": str(abs_path),
                        "backup_path": str(backup_path),
                    })

            # 模式 2: 文件不存在但允许创建
            elif create_if_missing:
                try:
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    if pdb_data:
                        abs_path.write_text(pdb_data, encoding="utf-8")
                    elif _default_pdb_url and _default_pdb_url.startswith("http"):
                        import urllib.request as _req
                        with _req.urlopen(_default_pdb_url, timeout=30) as resp:
                            pdb_content = resp.read().decode("utf-8", errors="replace")
                        abs_path.write_text(pdb_content, encoding="utf-8")
                    elif _default_pdb_abs_path and Path(_default_pdb_abs_path).exists():
                        shutil.copy2(_default_pdb_abs_path, str(abs_path))
                    else:
                        abs_path.write_text(
                            f"# PDB file placeholder\n# Original source: unknown\n",
                            encoding="utf-8",
                        )
                    return self._serve_json({
                        "ok": True,
                        "action": "created_new",
                        "saved": str(abs_path),
                    })
                except OSError as exc:
                    return self._serve_json({"error": f"创建文件失败: {exc}"}, status=500)
            else:
                return self._serve_json({
                    "error": f"文件不存在: {abs_path}。请指定有效的保存路径。",
                    "hint": "使用 save_pdb 命令时传入 path 参数指定保存位置",
                }, status=404)

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
    global _default_pdb_url, _default_pdb_abs_path, _server_ref, _last_activity
    serve_dir = serve_dir.resolve()
    if not serve_dir.is_dir():
        print(f"Error: serve directory does not exist: {serve_dir}", file=sys.stderr)
        sys.exit(2)

    port = find_free_port(host, port)
    os.chdir(serve_dir)

    if pdb_file:
        abs_pdb = Path(pdb_file).expanduser().resolve()
        _default_pdb_url = f"/__file?path={urllib.parse.quote(str(abs_pdb))}"
        _default_pdb_abs_path = str(abs_pdb)
        print(f"[pdb-viewer] default file: {abs_pdb} ({abs_pdb.stat().st_size} bytes)")
    else:
        _default_pdb_url = None
        _default_pdb_abs_path = None

    server = ThreadingHTTPServer((host, port), PdbViewerHandler)
    with _server_lock:
        _server_ref = server

    cli = find_omics_cli()
    _, session_valid = read_omics_session()
    print(f"[pdb-viewer] session_id: {SESSION_ID}")
    print(f"[pdb-viewer] serving {serve_dir} at http://{host}:{port}")
    print(f"[pdb-viewer] viewer template: {TEMPLATE_VIEWER}")
    print(f"[pdb-viewer] loading template: {TEMPLATE_LOADING}")
    print(f"[pdb-viewer] omics CLI: {cli or '(未安装)'}")
    print(f"[pdb-viewer] omics 登录态: {'✓ 有效' if session_valid else '✗ 未登录或已过期 (执行 omics login)'}")
    print(f"[pdb-viewer] omics API: {OMICS_BASE_URL}")
    print(f"[pdb-viewer] idle_timeout: {idle_timeout}s  (pid={os.getpid()})  (Ctrl-C to stop)")

    def _shutdown(signum, frame):
        print("\n[pdb-viewer] shutting down…")
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 初始化活跃时间
    with _activity_lock:
        _last_activity = time.time()

    # 心跳看门狗：无心跳则标记面板离线（服务继续，等空闲超时再退出）
    _watcher_stop = threading.Event()
    if not no_watchdog:
        def _heartbeat_watchdog() -> None:
            global _last_heartbeat
            with _hb_lock:
                _last_heartbeat = time.time() + 20  # 启动后给 20 秒宽限
            while not _watcher_stop.wait(timeout=5):
                with _hb_lock:
                    hb_gap = time.time() - _last_heartbeat
                if hb_gap > _heartbeat_timeout:
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
                    with _activity_lock:
                        gap = time.time() - _last_activity
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
        with _server_lock:
            _server_ref = None
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
    with open(LOG_FILE, "a", encoding="utf-8") as logf:
        os.dup2(logf.fileno(), sys.stdout.fileno())
        os.dup2(logf.fileno(), sys.stderr.fileno())
        sys.stdin = open(os.devnull, "r")

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
