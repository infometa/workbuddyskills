#!/usr/bin/env python3
"""受控远程原文读取。

用于替代不稳定的网页抓取能力，直接读取指定 URL 的原始文本内容。
当前仅允许访问 open.wshoto.com，避免 Skill 运行时任意外连。
"""
from __future__ import annotations

import os
import ssl
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from utils import ValidationError, SCRMError

ALLOWED_HOSTS = {"open.wshoto.com"}
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_BYTES = 2 * 1024 * 1024


def _get_ssl_context() -> ssl.SSLContext:
    if os.getenv("SCRM_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def _detect_encoding(content_type: str | None) -> str:
    if not content_type:
        return "utf-8"
    for part in content_type.split(";"):
        item = part.strip().lower()
        if item.startswith("charset="):
            return item.split("=", 1)[1].strip() or "utf-8"
    return "utf-8"


def fetch_raw_text(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("只允许读取 http 或 https 地址")
    if parsed.netloc not in ALLOWED_HOSTS:
        raise ValidationError(f"当前只允许读取以下域名：{', '.join(sorted(ALLOWED_HOSTS))}")

    req = request.Request(
        url,
        headers={
            "User-Agent": "scrm-skill-raw-fetcher/1.0",
            "Accept": "text/plain, text/markdown, text/html;q=0.9, */*;q=0.1",
        },
        method="GET",
    )

    ssl_context = _get_ssl_context()
    try:
        with request.urlopen(req, timeout=timeout, context=ssl_context) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
            body = response.read(max_bytes + 1)
    except error.HTTPError as exc:
        raise SCRMError(f"读取远程文档失败，HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise SCRMError(f"读取远程文档失败：{exc.reason}") from exc

    truncated = len(body) > max_bytes
    if truncated:
        body = body[:max_bytes]

    encoding = _detect_encoding(content_type)
    text = body.decode(encoding, errors="replace")
    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "content_type": content_type,
        "encoding": encoding,
        "length": len(body),
        "truncated": truncated,
        "content": text,
    }