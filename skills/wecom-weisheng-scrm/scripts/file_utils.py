#!/usr/bin/env python3
"""文件上传与下载辅助。"""
from __future__ import annotations

import mimetypes
import os
import ssl
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib import error, request
from urllib.parse import urlparse

from api_client import SCRMClient
from utils import ApiError, DOWNLOAD_DIR, DownloadError, UploadError, ensure_dir


def _get_ssl_context() -> ssl.SSLContext:
    """获取 SSL 上下文，支持通过环境变量跳过验证。"""
    if os.getenv("SCRM_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
        return ssl._create_unverified_context()
    return ssl.create_default_context()

UPLOAD_PATH = "/openapi/document/upload/bind"


def is_remote_url(value: str) -> bool:
    """判断给定值是否为公网 URL。"""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def download_file(url: str, *, target_dir: Optional[Path] = None, filename: Optional[str] = None) -> Path:
    """下载远程文件到本地。"""
    if not is_remote_url(url):
        raise DownloadError(f"非法下载地址：{url}")

    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix or ".bin"
    target = ensure_dir(target_dir or DOWNLOAD_DIR)
    resolved_name = filename or f"download-{uuid.uuid4().hex}{suffix}"
    output_path = target / resolved_name

    ssl_context = _get_ssl_context()
    try:
        with request.urlopen(url, timeout=30, context=ssl_context) as response:
            output_path.write_bytes(response.read())
    except error.URLError as exc:
        raise DownloadError(f"下载文件失败：{exc.reason}") from exc

    return output_path


def ensure_public_image_url(source: str, *, client: Optional[SCRMClient] = None) -> str:
    """确保图片来源最终可被开放平台访问。

    Args:
        source: 图片来源，远程 URL 或本地文件路径。
        client: SCRM 客户端实例，本地图片上传时必填。

    Returns:
        公网可访问的图片 URL。
    """
    if is_remote_url(source):
        return source

    path = Path(source).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise UploadError(f"本地图片不存在：{path}")
    result = upload_image(path, client=client)
    return result["url"]


def upload_image(path: Path, *, client: SCRMClient) -> dict[str, Any]:
    """上传本地图片，返回包含 url 和 file_id 的字典。

    Args:
        path: 本地图片文件路径。
        client: SCRM 客户端实例。

    Returns:
        {"url": "https://...", "file_id": 123456}

    Raises:
        UploadError: 上传失败时抛出。
    """
    body, content_type = _build_multipart_body(path, file_field="file", extra_fields={})
    try:
        payload = client.post_multipart(UPLOAD_PATH, body, content_type=content_type)
    except ApiError as exc:
        raise UploadError(str(exc), details=exc.details) from exc
    data = payload.get("data", {})
    url = data.get("url")
    file_id = data.get("file_id")
    if not url:
        raise UploadError("本地图片上传成功，但无法从返回中提取 URL")
    if not file_id:
        raise UploadError("本地图片上传成功，但无法从返回中提取 file_id")
    return {"url": url, "file_id": file_id}


def _build_multipart_body(path: Path, *, file_field: str, extra_fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----scrm-skills-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for key, value in extra_fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    file_bytes = path.read_bytes()
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{path.name}"\r\n'
            ).encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
