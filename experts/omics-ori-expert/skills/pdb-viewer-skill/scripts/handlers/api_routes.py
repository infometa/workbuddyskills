"""
handlers/api_routes.py — POST API 路由处理
==========================================

处理所有 POST 请求路由：
  /api/preload       LLM 预加载 PDB 到服务端缓存
  /api/ready         浏览器 Mol* 就绪通知
  /api/command       自然语言命令入队
  /api/query-result  浏览器推送查询结果（list_chains 等）
  /api/export-pdb    过滤并导出 PDB 文件
  /api/save-pdb      保存 PDB 文件（需确认）

依赖 state 模块读写全局状态，使用 sse_queue 推送命令，使用 preload 管理缓存。
"""
from __future__ import annotations

import base64
import json
import shutil
import sys
import os
from pathlib import Path
from typing import Any

_scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import state
from handlers.cos_handler import (
    fetch_pdb_from_omics, fetch_pdb_from_coscli, resolve_cos_route,
)
from handlers.pdb_filter import filter_pdb
from handlers.sse_queue import enqueue_command
from handlers import preload as _preload


def _read_body(handler) -> tuple[dict, bool]:
    """读取并解析 POST body JSON。返回 (body_dict, success)。"""
    content_len = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(content_len) if content_len > 0 else b"{}"
    try:
        return json.loads(raw.decode("utf-8")), True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}, False


def handle_preload(handler) -> None:
    """POST /api/preload — LLM 在 present_files 之前预读 PDB 文件到内存缓存。"""
    body, ok = _read_body(handler)
    if not ok:
        return handler._serve_json({"error": "invalid JSON"}, status=400)

    uri = body.get("uri", "")
    if not uri:
        return handler._serve_json({"error": "missing 'uri'"}, status=400)

    try:
        if uri.startswith("cos://"):
            # 路由决策：coscli（通用桶）或 omics（平台绑定桶）
            route = resolve_cos_route(uri)
            if route == "coscli":
                raw_bytes, file_name = fetch_pdb_from_coscli(uri)
            else:
                raw_bytes, file_name = fetch_pdb_from_omics(uri)
            b64 = base64.b64encode(raw_bytes).decode("ascii")
        else:
            abs_path = Path(uri).expanduser().resolve()
            if not abs_path.exists():
                return handler._serve_json({"error": f"文件不存在: {abs_path}"}, status=404)
            raw_bytes = abs_path.read_bytes()
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            file_name = abs_path.name

        _preload.set_preloaded({"data": b64, "name": file_name, "uri": uri})
        return handler._serve_json({
            "ok": True,
            "name": file_name,
            "bytes": len(raw_bytes),
            "cached": True,
        })
    except Exception as exc:
        return handler._serve_json({"error": str(exc)}, status=500)


def handle_ready(handler) -> None:
    """POST /api/ready — 浏览器 Mol* 初始化完成，有预加载缓存时自动推送 get_pdb。"""
    cached = _preload.get_preloaded()
    if cached:
        uri = cached.get("uri", "")
        cmd_entry = {"op": "get_pdb", "params": {"url": uri}}
        enqueue_command(cmd_entry)
        print(f"[pdb-viewer] /api/ready: 浏览器就绪，自动推送 get_pdb → {uri}")
        return handler._serve_json({"ok": True, "pushed": cmd_entry})
    else:
        print("[pdb-viewer] /api/ready: 浏览器就绪，无预加载缓存")
        return handler._serve_json({"ok": True, "pushed": None})


def handle_command(handler) -> None:
    """POST /api/command — 接收自然语言命令，入队并通过 SSE 推送给浏览器。"""
    body, ok = _read_body(handler)
    if not ok:
        return handler._serve_json({"error": "invalid JSON"}, status=400)

    op = body.get("op") or body.get("action", "")
    params = body.get("params", {})
    if not params:
        params = {k: v for k, v in body.items() if k not in ("op", "action", "params")}

    if op and isinstance(op, str):
        cmd_entry = {"op": op, "params": params}
        enqueue_command(cmd_entry)
        return handler._serve_json({"ok": True, "queued": cmd_entry})

    return handler._serve_json({"error": "missing or invalid 'op'/'action'"}, status=400)


def handle_query_result_post(handler) -> None:
    """POST /api/query-result — 浏览器推送 list_chains / list_ligands 等查询结果。"""
    body, ok = _read_body(handler)
    if not ok:
        return handler._serve_json({"error": "invalid JSON"}, status=400)

    op = body.get("op", "")
    result = body.get("result")
    if op:
        import time
        with state.query_lock:
            state.query_results[op] = {"result": result, "timestamp": time.time()}

    return handler._serve_json({"ok": True, "op": op})


def handle_export_pdb(handler) -> None:
    """POST /api/export-pdb — 过滤并导出 PDB 文件（derive_file 模式）。"""
    body, ok = _read_body(handler)
    if not ok:
        return handler._serve_json({"error": "invalid JSON"}, status=400)

    file_path_str = body.get("path", "")
    source_str = body.get("source", "") or state.default_pdb_abs_path or ""
    remove_list = [r.upper() for r in (body.get("remove") or [])]
    keep_chains = [c.upper() for c in (body.get("keep_chains") or [])]
    keep_altloc = body.get("keep_altloc")

    if not file_path_str:
        return handler._serve_json({"error": "missing 'path' parameter"}, status=400)
    if not source_str:
        return handler._serve_json({"error": "无原始文件路径，请先加载本地 PDB 文件"}, status=400)

    source_path = Path(source_str).expanduser().resolve()
    if not source_path.exists():
        return handler._serve_json({"error": f"源文件不存在: {source_path}"}, status=404)

    out_path = Path(file_path_str).expanduser().resolve()
    if out_path.suffix.lower() not in (".pdb", ".cif", ".mmcif"):
        return handler._serve_json({"error": "输出文件必须是 .pdb/.cif/.mmcif"}, status=400)

    result = filter_pdb(
        source_path=source_path,
        out_path=out_path,
        remove=remove_list or None,
        keep_chains=keep_chains or None,
        keep_altloc=keep_altloc,
    )
    if result["ok"]:
        result["source"] = str(source_path)
        return handler._serve_json(result)
    else:
        return handler._serve_json(result, status=500)


def handle_save_pdb(handler) -> None:
    """POST /api/save-pdb — 保存或备份 PDB 文件（两种模式）。"""
    body, ok = _read_body(handler)
    if not ok:
        return handler._serve_json({"error": "invalid JSON"}, status=400)

    file_path_str = body.get("path", "")
    pdb_data = body.get("data", "")
    action = body.get("action", "backup")
    create_if_missing = body.get("create_if_missing", False)

    if not file_path_str:
        return handler._serve_json({"error": "missing 'path' parameter"}, status=400)

    abs_path = Path(file_path_str).expanduser().resolve()
    if abs_path.suffix.lower() not in (".pdb", ".cif", ".mmcif"):
        return handler._serve_json({"error": "仅支持 .pdb/.cif/.mmcif 文件"}, status=400)

    # 模式 1：文件已存在 → 备份 + 可选覆盖
    if abs_path.exists():
        backup_path = abs_path.with_suffix(abs_path.suffix + ".bak")
        try:
            shutil.copy2(str(abs_path), str(backup_path))
        except OSError as exc:
            return handler._serve_json({"error": f"备份失败: {exc}"}, status=500)

        if action == "overwrite" and pdb_data:
            try:
                abs_path.write_text(pdb_data, encoding="utf-8")
                return handler._serve_json({
                    "ok": True, "saved": str(abs_path), "backup_path": str(backup_path),
                })
            except OSError as exc:
                return handler._serve_json({"error": f"写入失败: {exc}"}, status=500)
        else:
            return handler._serve_json({
                "ok": True, "action": "backup_only",
                "original": str(abs_path), "backup_path": str(backup_path),
            })

    # 模式 2：文件不存在但允许创建
    elif create_if_missing:
        try:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            if pdb_data:
                abs_path.write_text(pdb_data, encoding="utf-8")
            elif state.default_pdb_url and state.default_pdb_url.startswith("http"):
                import urllib.request as _req
                with _req.urlopen(state.default_pdb_url, timeout=30) as resp:
                    pdb_content = resp.read().decode("utf-8", errors="replace")
                abs_path.write_text(pdb_content, encoding="utf-8")
            elif state.default_pdb_abs_path and Path(state.default_pdb_abs_path).exists():
                shutil.copy2(state.default_pdb_abs_path, str(abs_path))
            else:
                abs_path.write_text(
                    "# PDB file placeholder\n# Original source: unknown\n", encoding="utf-8"
                )
            return handler._serve_json({"ok": True, "action": "created_new", "saved": str(abs_path)})
        except OSError as exc:
            return handler._serve_json({"error": f"创建文件失败: {exc}"}, status=500)
    else:
        return handler._serve_json({
            "error": f"文件不存在: {abs_path}。请指定有效的保存路径。",
            "hint": "使用 save_pdb 命令时传入 path 参数指定保存位置",
        }, status=404)
