"""
debug_logger.py — pdb-viewer-skill 调试日志模块（Python 端）

╔══════════════════════════════════════════════════════════════════╗
║  [DBG-IMPORT] 标记：此文件仅用于调试，发布前注释掉 import 行   ║
║  在 serve_pdb.py 中查找 [DBG-IMPORT] 注释行以快速定位          ║
╚══════════════════════════════════════════════════════════════════╝

使用方式：
  调用点: dbg_log and dbg_log('message', level='info')
  级别: 'info'(默认) | 'warn' | 'error' | 'ok'

  注册调试路由（在 HTTP handler 中）:
  if _debug_routes and _debug_routes.handle(handler, path): return

发布清理方式：
  serve_pdb.py 中注释掉 [DBG-IMPORT] 那两行 import 即可
  → dbg_log 变为 None
  → 所有 dbg_log and dbg_log(...) 调用自动短路，0 改动
  → /api/log 和 /api/logs 路由不注册，返回 404（自然降级）
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

# ---------- 日志文件管理 ----------
# 日志存放于 SKILL_ROOT/.debug/ 目录，不污染 templates/scripts
# 文件名格式: pdb-viewer-{session_id}.log
# 7 天前的日志自动清理

_log_file: Path | None = None
_log_lock = threading.Lock()
_in_memory_logs: list[dict] = []   # 内存队列，供 /api/logs 读取
_MAX_MEM_LOGS = 500

_session_id: str = ""


def init(skill_root: Path, session_id: str) -> None:
    """初始化日志模块。在 serve_pdb.py 启动时调用。"""
    global _log_file, _session_id
    _session_id = session_id
    debug_dir = skill_root / ".debug"
    debug_dir.mkdir(exist_ok=True)
    _log_file = debug_dir / f"pdb-viewer-{session_id}.log"
    _log_file.write_text(
        f"=== pdb-viewer-skill debug log ===\n"
        f"session: {session_id}\n"
        f"started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'='*40}\n",
        encoding="utf-8"
    )
    # 清理 7 天前的日志
    _cleanup_old_logs(debug_dir, max_age_days=7)
    log(f"debug_logger initialized — session={session_id}", level="info")


def _cleanup_old_logs(debug_dir: Path, max_age_days: int = 7) -> None:
    """清理超过 max_age_days 天的日志文件。"""
    cutoff = time.time() - max_age_days * 86400
    for f in debug_dir.glob("pdb-viewer-*.log"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


def log(msg: str, level: str = "info") -> None:
    """写入日志（文件 + 内存队列）。"""
    entry = {
        "msg": str(msg),
        "level": level,
        "ts": time.strftime("%H:%M:%S"),
        "session": _session_id,
    }
    with _log_lock:
        # 写文件
        if _log_file is not None:
            try:
                with _log_file.open("a", encoding="utf-8") as fh:
                    fh.write(f"[{entry['ts']}][{level.upper():5s}] {msg}\n")
            except OSError:
                pass
        # 写内存队列
        _in_memory_logs.append(entry)
        if len(_in_memory_logs) > _MAX_MEM_LOGS:
            _in_memory_logs.pop(0)


def get_logs(last_n: int = 50) -> list[dict]:
    """返回最近 last_n 条日志。"""
    with _log_lock:
        return list(_in_memory_logs[-last_n:])


def get_log_file_path() -> str:
    """返回当前日志文件路径（用于调试输出）。"""
    return str(_log_file) if _log_file else "(not initialized)"


# ---------- HTTP 路由处理 ----------

class DebugRoutes:
    """
    注册调试相关的 HTTP 路由。
    在 serve_pdb.py 的 do_GET / do_POST 中：
        if _debug_routes and _debug_routes.handle(self, path): return
    """

    def handle(self, handler: Any, path: str) -> bool:
        """
        尝试处理调试路由。
        返回 True 表示已处理（调用方应 return），False 表示未处理。
        """
        if path == "/api/log":
            return self._handle_post_log(handler)
        if path == "/api/logs":
            return self._handle_get_logs(handler)
        return False

    def _handle_post_log(self, handler: Any) -> bool:
        """POST /api/log — 接收前端日志（单条或批量）。"""
        if handler.command != "POST":
            return False
        try:
            content_len = int(handler.headers.get("Content-Length", 0))
            raw = handler.rfile.read(content_len) if content_len > 0 else b"{}"
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            _send_json(handler, {"error": "invalid JSON"}, status=400)
            return True

        # 支持单条 {msg, level} 和批量 {batch: [{msg, level, ts}, ...]}
        batch = body.get("batch") if isinstance(body, dict) else None
        if batch and isinstance(batch, list):
            for entry in batch:
                msg = entry.get("msg", "")
                lvl = entry.get("level", "info")
                if msg:
                    log(f"[BROWSER] {msg}", level=lvl)
        else:
            msg = body.get("msg", "") if isinstance(body, dict) else ""
            lvl = body.get("level", "info") if isinstance(body, dict) else "info"
            if msg:
                log(f"[BROWSER] {msg}", level=lvl)

        _send_json(handler, {"ok": True})
        return True

    def _handle_get_logs(self, handler: Any) -> bool:
        """GET /api/logs — 返回内存中最近的日志。"""
        if handler.command != "GET":
            return False
        entries = get_logs(last_n=100)
        _send_json(handler, {"logs": entries, "file": get_log_file_path()})
        return True


def _send_json(handler: Any, data: dict, status: int = 200) -> None:
    """辅助：向 HTTP handler 发送 JSON 响应。"""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


# 模块级暴露的便捷引用（供 serve_pdb.py 使用）
dbg_log = log                     # serve_pdb.py 调用: dbg_log and dbg_log('msg')
_debug_routes = DebugRoutes()     # serve_pdb.py 调用: if _debug_routes and _debug_routes.handle(self, path): return
