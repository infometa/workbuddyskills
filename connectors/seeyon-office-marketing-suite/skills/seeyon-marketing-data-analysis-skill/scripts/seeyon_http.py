#!/usr/bin/env python3
"""Seeyon HTTP 请求公共能力。by AI.Coding"""

from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_TIMEOUT = 20


@dataclass(frozen=True)
class HttpResponse:
    """保存 HTTP 状态、原始文本和解析后响应。by AI.Coding"""

    status: int
    text: str
    body: Any


def truncate(text: str, limit: int = 500) -> str:
    """截断过长文本，避免错误输出包含大段服务端内容。"""
    return text if len(text) <= limit else text[:limit] + "..."


def build_cookie_header(session_id: str, route: Optional[str]) -> str:
    """根据认证 Skill 输出组装 Seeyon 业务 Cookie。"""
    cookies = [f"JSESSIONID={session_id}"]
    if route:
        cookies.append(f"route={route}")
    return "; ".join(cookies)


def build_opener(session_id: str, route: Optional[str]) -> urllib.request.OpenerDirector:
    """创建带登录 Cookie 和通用请求头的 urllib opener。"""
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0"),
        ("Accept", "application/json,text/plain,*/*"),
        ("Cookie", build_cookie_header(session_id, route)),
    ]
    return opener


def parse_response(response) -> HttpResponse:
    """读取 urllib 响应并在可解析时转换为 JSON。"""
    text = response.read().decode("utf-8", errors="replace")
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        # Seeyon 会用纯文本 __LOGOUT 表示会话过期，必须保留原文供上层判断。
        body = text
    return HttpResponse(status=response.getcode(), text=text, body=body)


def post_form(
    opener: urllib.request.OpenerDirector,
    url: str,
    fields: dict[str, str],
    timeout: int = DEFAULT_TIMEOUT,
) -> HttpResponse:
    """以 UTF-8 application/x-www-form-urlencoded 发送 POST。"""
    data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        return parse_response(response)


def post_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    body: dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> HttpResponse:
    """以 UTF-8 JSON 发送 POST。"""
    data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        return parse_response(response)


def encode_multipart(
    fields: dict[str, str],
    file_field: str,
    file_name: str,
    file_bytes: bytes,
    mime_type: str,
    boundary: Optional[str] = None,
) -> tuple[bytes, str]:
    """按 multipart/form-data 规范编码文本字段和一个文件字段。"""
    actual_boundary = boundary or f"----SeeyonSkill{secrets.token_hex(16)}"
    boundary_bytes = actual_boundary.encode("ascii")
    parts: list[bytes] = []

    # 所有字段都按浏览器表单语义发送字符串，保持与抓包参数一致。
    for name, value in fields.items():
        parts.extend(
            [
                b"--" + boundary_bytes + b"\r\n",
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    # 文件名仅转义引号和反斜杠，避免破坏 Content-Disposition 属性。
    safe_file_name = file_name.replace("\\", "\\\\").replace('"', '\\"')
    parts.extend(
        [
            b"--" + boundary_bytes + b"\r\n",
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{safe_file_name}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("ascii"),
            file_bytes,
            b"\r\n",
            b"--" + boundary_bytes + b"--\r\n",
        ]
    )
    return b"".join(parts), f"multipart/form-data; boundary={actual_boundary}"


def post_multipart(
    opener: urllib.request.OpenerDirector,
    url: str,
    body: bytes,
    content_type: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> HttpResponse:
    """发送已经编码完成的 multipart 请求体。"""
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    with opener.open(request, timeout=timeout) as response:
        return parse_response(response)


def normalize_http_error(exc: urllib.error.HTTPError | urllib.error.URLError) -> dict[str, Any]:
    """把 urllib 网络异常转换为稳定、可序列化的诊断结构。"""
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return {
            "status": exc.code,
            "reason": str(exc.reason),
            "body_preview": truncate(body),
        }

    # URLError 没有 HTTP 状态码，仅保留底层网络失败原因。
    return {
        "status": None,
        "reason": str(exc.reason),
        "body_preview": "",
    }
