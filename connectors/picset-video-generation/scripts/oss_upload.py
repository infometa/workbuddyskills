#!/usr/bin/env python3
"""Public OSS upload helper for WorkBuddy connector materials."""

from __future__ import annotations

import base64
import email.utils
import hashlib
import hmac
import json
import mimetypes
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Mapping


DEFAULT_UPLOAD_TIMEOUT_SECONDS = 120


class OssUploadError(RuntimeError):
    """Redacted upload failure suitable for public CLI output."""


def _required_string(token: Mapping[str, Any], key: str) -> str:
    value = token.get(key)
    if not isinstance(value, str) or not value:
        raise OssUploadError("INVALID_UPLOAD_TOKEN")
    return value


def _content_type(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return "audio/wav" if guessed in {"audio/x-wav", "audio/wave"} else guessed


def _authorization(token: Mapping[str, Any], oss_path: str, content_type: str, date: str) -> str:
    bucket = _required_string(token, "bucket")
    access_key_id = _required_string(token, "accessKeyId")
    access_key_secret = _required_string(token, "accessKeySecret")
    security_token = _required_string(token, "securityToken")
    string_to_sign = (
        f"PUT\n\n{content_type}\n{date}\n"
        f"x-oss-security-token:{security_token}\n"
        f"/{bucket}/{oss_path.lstrip('/')}"
    )
    signature = base64.b64encode(
        hmac.new(access_key_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")
    return f"OSS {access_key_id}:{signature}"


def upload_file_to_oss(token: Mapping[str, Any], file_path: str | Path) -> dict[str, Any]:
    source_path = Path(file_path).expanduser()
    if not source_path.is_file():
        raise OssUploadError("FILE_NOT_FOUND")

    max_bytes = token.get("maxBytes")
    file_size = source_path.stat().st_size
    if isinstance(max_bytes, int) and file_size > max_bytes:
        raise OssUploadError("FILE_TOO_LARGE")

    content_type = _content_type(source_path)
    allowed_types = token.get("allowedMimeTypes")
    if isinstance(allowed_types, list) and allowed_types and content_type not in allowed_types:
        raise OssUploadError("FILE_TYPE_NOT_ALLOWED")

    bucket = _required_string(token, "bucket")
    region = _required_string(token, "region")
    object_key = token.get("objectKey")
    if isinstance(object_key, str) and object_key:
        oss_path = object_key
    else:
        path_prefix = _required_string(token, "pathPrefix").rstrip("/")
        oss_path = f"{path_prefix}/{uuid.uuid4().hex}{source_path.suffix.lower() or '.bin'}"
    security_token = _required_string(token, "securityToken")
    date = email.utils.formatdate(usegmt=True)
    url = f"https://{bucket}.{region}.aliyuncs.com/{urllib.parse.quote(oss_path, safe='/')}"
    request = urllib.request.Request(
        url,
        data=source_path.read_bytes(),
        method="PUT",
        headers={
            "Authorization": _authorization(token, oss_path, content_type, date),
            "Content-Type": content_type,
            "Date": date,
            "x-oss-security-token": security_token,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_UPLOAD_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            if status < 200 or status >= 300:
                raise OssUploadError(f"OSS_HTTP_{status}")
            response.read()
    except urllib.error.HTTPError as error:
        raise OssUploadError(f"OSS_HTTP_{error.code}") from error
    result: dict[str, Any] = {
        "oss_path": oss_path,
        "file_type": content_type,
        "file_size": file_size,
    }
    upload_id = token.get("uploadId")
    if isinstance(upload_id, str) and upload_id:
        result["upload_id"] = upload_id
    return result


def load_token_from_stdin() -> dict[str, Any]:
    try:
        token = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        raise OssUploadError("INVALID_UPLOAD_TOKEN") from error
    if not isinstance(token, dict):
        raise OssUploadError("INVALID_UPLOAD_TOKEN")
    return token
