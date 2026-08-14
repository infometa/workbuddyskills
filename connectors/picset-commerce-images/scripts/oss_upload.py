"""Aliyun OSS upload through Python's standard-library HTTP client."""

from __future__ import annotations

import base64
import email.utils
import hashlib
import hmac
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping


DEFAULT_UPLOAD_TIMEOUT_SECONDS = 120


class OssUploadError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _required_string(token: Mapping[str, Any], field: str) -> str:
    value = token.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"upload token missing {field}")
    return value


def _content_type(source_path: Path) -> str:
    return mimetypes.guess_type(source_path.name)[0] or "application/octet-stream"


def _detected_content_type(content: bytes) -> str | None:
    header = content[:12]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def _object_path(token: Mapping[str, Any], source_path: Path) -> str:
    prefix = _required_string(token, "pathPrefix").rstrip("/")
    suffix = source_path.suffix.lower() or ".bin"
    return f"{prefix}/{uuid.uuid4().hex}{suffix}"


def _put_url(token: Mapping[str, Any], object_path: str) -> str:
    bucket = _required_string(token, "bucket")
    region = _required_string(token, "region")
    encoded_path = urllib.parse.quote(object_path.lstrip("/"), safe="/")
    return f"https://{bucket}.{region}.aliyuncs.com/{encoded_path}"


def _authorization(
    token: Mapping[str, Any],
    object_path: str,
    content_type: str,
    date: str,
) -> str:
    access_key_id = _required_string(token, "accessKeyId")
    access_key_secret = _required_string(token, "accessKeySecret")
    security_token = _required_string(token, "securityToken")
    bucket = _required_string(token, "bucket")
    canonical_headers = f"x-oss-security-token:{security_token}\n"
    canonical_resource = f"/{bucket}/{object_path.lstrip('/')}"
    string_to_sign = (
        f"PUT\n\n{content_type}\n{date}\n"
        f"{canonical_headers}{canonical_resource}"
    )
    digest = hmac.new(
        access_key_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(digest).decode("ascii")
    return f"OSS {access_key_id}:{signature}"


def upload_file_to_oss(
    token: Mapping[str, Any],
    file_path: str | Path,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout_seconds: int = DEFAULT_UPLOAD_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    source_path = Path(file_path).expanduser()
    if not source_path.is_file():
        raise FileNotFoundError(f"local file not found: {source_path}")

    max_bytes = token.get("maxBytes")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError("upload token invalid maxBytes")

    content_type = _content_type(source_path)
    allowed_types = token.get("allowedMimeTypes")
    if (
        not isinstance(allowed_types, list)
        or not allowed_types
        or any(not isinstance(value, str) or not value for value in allowed_types)
    ):
        raise ValueError("upload token invalid allowedMimeTypes")
    if content_type not in allowed_types:
        raise ValueError(f"file type is not allowed: {content_type}")

    with source_path.open("rb") as source:
        file_content = source.read(max_bytes + 1)
    file_size = len(file_content)
    if file_size > max_bytes:
        raise ValueError(f"file exceeds maxBytes: {file_size} > {max_bytes}")
    detected_type = _detected_content_type(file_content)
    if detected_type is None:
        raise ValueError("unsupported image content")
    if detected_type != content_type:
        raise ValueError("file content does not match extension")

    object_path = _object_path(token, source_path)
    date = email.utils.formatdate(usegmt=True)
    security_token = _required_string(token, "securityToken")
    request = urllib.request.Request(
        _put_url(token, object_path),
        data=file_content,
        method="PUT",
        headers={
            "Authorization": _authorization(token, object_path, content_type, date),
            "Content-Type": content_type,
            "Date": date,
            "x-oss-security-token": security_token,
        },
    )

    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", 200))
            if not 200 <= status < 300:
                raise OssUploadError(status, f"OSS upload failed with HTTP {status}")
            response.read()
    except urllib.error.HTTPError as error:
        raise OssUploadError(
            int(error.code),
            f"OSS upload failed with HTTP {int(error.code)}",
        ) from None

    return {
        "oss_path": object_path,
        "file_type": content_type,
        "file_size": file_size,
    }
