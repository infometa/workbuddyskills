"""
handlers/static_server.py — HTTP 响应辅助方法 & 静态文件服务
============================================================

提供 PdbViewerHandler 中用于发送 HTTP 响应的所有辅助方法，
以及 translate_path 路径解析（静态文件 fallback 到 templates/ 目录）。

引用常量：SKILL_ROOT / TEMPLATE_VIEWER / TEMPLATE_LOADING / SESSION_ID
这些常量从 serve_pdb.py 顶部传入（通过 mixin 的 _CONSTANTS 类变量），
避免循环导入。

使用方式（在 PdbViewerHandler 中混入）：
    from handlers.static_server import StaticServerMixin
    class PdbViewerHandler(StaticServerMixin, SimpleHTTPRequestHandler):
        TEMPLATE_VIEWER = ...
        TEMPLATE_LOADING = ...
        SESSION_ID = ...
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # 仅用于类型提示，不在运行时产生循环导入

# handlers/ 目录加入 sys.path（供 cos_handler 导入）
_THIS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _THIS_DIR.parent
for _d in (_THIS_DIR, _SCRIPTS_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


class StaticServerMixin:
    """
    HTTP 响应辅助方法 mixin。

    使用类在子类中设置以下类变量（通常在 serve_pdb.py 的 PdbViewerHandler 中）：
        TEMPLATE_VIEWER:  Path
        TEMPLATE_LOADING: Path
        SESSION_ID:       str
    """

    def _serve_template(self, path: Path) -> None:
        """发送 HTML 模板文件。"""
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
        """发送纯文本响应。"""
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, obj: dict, status: int = 200) -> None:
        """发送 JSON 响应。"""
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_loading(self, pdb_param: str = "") -> None:
        """返回 loading.html（过渡动画页面），注入 session_id 和 pdb 参数。"""
        template_loading = getattr(self, 'TEMPLATE_LOADING', None)
        session_id = getattr(self, 'SESSION_ID', '')

        if template_loading and Path(template_loading).exists():
            try:
                html = Path(template_loading).read_text("utf-8")
                html = html.replace(
                    "/* __INJECT_SESSION_ID__ */",
                    f"var CURRENT_SESSION_ID = '{session_id}';"
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

        # 降级到内联 HTML
        html_fallback = (
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<title>正在加载…</title>'
            '<style>body{background:#1a1d24;color:#7fd97f;font-family:monospace;'
            'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}'
            '</style></head><body><p>正在加载新结构…</p>'
            f'<script>var CURRENT_SESSION_ID = "{session_id}";'
            f'var PDB_PARAM = "{urllib.parse.quote(pdb_param, safe="")}";'
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

    # ----------------------------------------------------------------
    # /__file 代理：读取本地文件，返回 base64 JSON
    # ----------------------------------------------------------------
    def _handle_local_file(self, query_string: str) -> None:
        """GET /__file?path=<abs_path> → 读取本地文件，返回 base64 JSON。"""
        params = urllib.parse.parse_qs(query_string)
        file_path = params.get("path", [""])[0]
        if not file_path:
            return self._serve_json({"error": "missing path parameter"}, status=400)

        abs_path = Path(urllib.parse.unquote(file_path)).expanduser().resolve()
        if not abs_path.exists():
            return self._serve_json({"error": f"文件不存在: {abs_path}"}, status=404)
        if not abs_path.is_file():
            return self._serve_json({"error": f"路径不是文件: {abs_path}"}, status=400)

        try:
            raw = abs_path.read_bytes()
            b64 = base64.b64encode(raw).decode("ascii")
            return self._serve_json({
                "data": b64,
                "name": abs_path.name,
                "path": str(abs_path),
                "size": len(raw),
            })
        except OSError as exc:
            return self._serve_json({"error": f"读取失败: {exc}"}, status=500)

    # ----------------------------------------------------------------
    # /__cos 代理：通过 omics CLI 或 coscli 读取 COS 文件，返回 base64 JSON
    # ----------------------------------------------------------------
    def _handle_cos_proxy(self, query_string: str) -> None:
        """GET /__cos?uri=cos://bucket/key → 路由到 omics 或 coscli，返回 base64 JSON。"""
        params = urllib.parse.parse_qs(query_string)
        uri = params.get("uri", [""])[0]
        if not uri:
            return self._serve_json({"error": "missing uri parameter"}, status=400)

        try:
            # 延迟导入，避免循环
            from handlers.cos_handler import (  # type: ignore
                fetch_pdb_from_omics, fetch_pdb_from_coscli, resolve_cos_route,
            )
        except ImportError as ie:
            return self._serve_json({"error": f"cos_handler 不可用: {ie}"}, status=500)

        try:
            # 路由决策：coscli（通用桶）或 omics（平台绑定桶）
            route = resolve_cos_route(uri)
            if route == "coscli":
                raw_bytes, file_name = fetch_pdb_from_coscli(uri)
            else:
                raw_bytes, file_name = fetch_pdb_from_omics(uri)

            b64 = base64.b64encode(raw_bytes).decode("ascii")
            return self._serve_json({
                "data": b64,
                "name": file_name,
                "path": uri,
                "size": len(raw_bytes),
                "route": route,
            })
        except Exception as exc:
            return self._serve_json({"error": str(exc)}, status=500)

    def translate_path(self, path: str) -> str:
        """重写路径解析：templates/ 目录下的静态文件（molstar.js/css 等）可从根路径访问。
        包括 templates/js/*.js 子目录。
        """
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

        # Fallback 1: 根目录找不到时尝试 templates/ 子目录
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
