#!/usr/bin/env python3
"""Seeyon 自由协同可选附件上传能力。by AI.Coding"""

from __future__ import annotations

import json
import mimetypes
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from seeyon_http import encode_multipart, post_form, post_multipart


class AttachmentUploadError(ValueError):
    """表示附件校验、断点解析或上传结果不满足约束。by AI.Coding"""

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """保存稳定错误码、消息和诊断详情。"""
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化错误结构。"""
        return {"code": self.code, "message": str(self), "details": self.details}


@dataclass(frozen=True)
class FileMetadata:
    """保存上传接口需要的本地文件元数据。by AI.Coding"""

    path: Path
    file_name: str
    file_size: int
    last_modified_ms: int
    mime_type: str


@dataclass(frozen=True)
class UploadBatchResult:
    """保存批量上传成功项、失败位置和共用页面标识。by AI.Coding"""

    ok: bool
    attachments: list[dict[str, Any]]
    failed_file: Optional[str] = None
    error: Optional[dict[str, Any]] = None
    current_page_id: Optional[str] = None


def generate_current_page_id(now_ms: Optional[int] = None) -> str:
    """生成“毫秒时间戳.16位随机数字”格式的上传页面标识。"""
    timestamp = int(time.time() * 1000) if now_ms is None else int(now_ms)
    random_digits = "".join(str(secrets.randbelow(10)) for _ in range(16))
    return f"{timestamp}.{random_digits}"


def build_file_metadata(path: Path) -> FileMetadata:
    """校验本地附件并提取名称、大小、修改时间和 MIME 类型。"""
    actual_path = Path(path)
    if not actual_path.exists():
        raise AttachmentUploadError(
            "attachment_not_found",
            f"附件文件不存在: {actual_path}",
            {"path": str(actual_path)},
        )
    if not actual_path.is_file():
        raise AttachmentUploadError(
            "attachment_not_file",
            f"附件路径不是普通文件: {actual_path}",
            {"path": str(actual_path)},
        )
    try:
        stat = actual_path.stat()
    except OSError as exc:
        raise AttachmentUploadError(
            "attachment_unreadable",
            f"无法读取附件元数据: {actual_path}",
            {"path": str(actual_path), "reason": str(exc)},
        ) from exc
    mime_type = mimetypes.guess_type(actual_path.name)[0] or "application/octet-stream"
    return FileMetadata(
        path=actual_path,
        file_name=actual_path.name,
        file_size=stat.st_size,
        last_modified_ms=int(stat.st_mtime * 1000),
        mime_type=mime_type,
    )


def parse_start_index(response_body: Any) -> int:
    """从明确的数字、数字字符串或 startIndex/data 字段解析非负断点。"""
    candidate = response_body
    if isinstance(response_body, dict):
        if "startIndex" in response_body:
            candidate = response_body["startIndex"]
        elif "data" in response_body:
            candidate = response_body["data"]
        else:
            candidate = None

    # bool 是 int 的子类，但不是合法的文件偏移量输入。
    if isinstance(candidate, bool):
        candidate = None
    if isinstance(candidate, int):
        value = candidate
    elif isinstance(candidate, str) and candidate.strip().isdigit():
        value = int(candidate.strip())
    else:
        raise AttachmentUploadError(
            "parse_upload_start_index",
            "无法从断点接口响应中解析非负整数 startIndex。",
            {"response": response_body},
        )
    if value < 0:
        raise AttachmentUploadError(
            "parse_upload_start_index",
            "断点接口返回了负数 startIndex。",
            {"response": response_body},
        )
    return value


def query_start_index(opener, base_url: str, metadata: FileMetadata, current_page_id: str) -> int:
    """调用 fileManager 接口查询指定附件的上传起点。"""
    file_value = {
        "lastModifiedDate": str(metadata.last_modified_ms),
        "fileName": metadata.file_name,
        "fileSize": str(metadata.file_size),
        "isEncrypt": True,
    }
    fields = {
        "managerMethod": "getUploadFilesStartIndex",
        "arguments": json.dumps([[file_value], current_page_id], ensure_ascii=False, separators=(",", ":")),
    }
    url = f"{base_url.rstrip('/')}/ajax.do?method=ajaxAction&managerName=fileManager"
    response = post_form(opener, url, fields)
    if response.status < 200 or response.status >= 300:
        raise AttachmentUploadError(
            "query_start_index_http_failed",
            "断点查询接口未返回成功 HTTP 状态。",
            {"status": response.status, "body": response.text[:500]},
        )
    return parse_start_index(response.body)


def upload_attachment(
    opener,
    base_url: str,
    metadata: FileMetadata,
    current_page_id: str,
    start_index: int,
) -> dict[str, Any]:
    """从指定断点上传单个附件，并返回发送接口使用的 att 对象。"""
    if start_index < 0 or start_index > metadata.file_size:
        raise AttachmentUploadError(
            "invalid_upload_start_index",
            "附件上传起点超出文件范围。",
            {"startIndex": start_index, "fileSize": metadata.file_size},
        )
    try:
        file_bytes = metadata.path.read_bytes()
    except OSError as exc:
        raise AttachmentUploadError(
            "attachment_unreadable",
            f"无法读取附件内容: {metadata.path}",
            {"path": str(metadata.path), "reason": str(exc)},
        ) from exc

    fields = {
        "fileSize": str(metadata.file_size),
        "currentPageId": current_page_id,
        "lastModifiedDate": str(metadata.last_modified_ms),
        "startIndex": str(start_index),
        "fileName": metadata.file_name,
        "secretLevel": "undefined",
        "secretLevelName": "undefined",
        "isEncrypt": "true",
    }
    body, content_type = encode_multipart(
        fields,
        "file",
        metadata.file_name,
        file_bytes[start_index:],
        metadata.mime_type,
    )
    url = f"{base_url.rstrip('/')}/fileUpload.do?method=processUploadForH5"
    response = post_multipart(opener, url, body, content_type)
    result = response.body
    if (
        response.status < 200
        or response.status >= 300
        or not isinstance(result, dict)
        or str(result.get("status")) != "200"
        or result.get("end") is not True
        or not isinstance(result.get("att"), dict)
        or not result.get("att")
    ):
        raise AttachmentUploadError(
            "upload_failed",
            "附件上传接口未确认完整上传成功。",
            {"status": response.status, "response": result},
        )
    return result["att"]


def upload_attachments(
    opener,
    base_url: str,
    paths: list[Path],
    current_page_id: Optional[str],
) -> UploadBatchResult:
    """按顺序上传全部附件，首个失败后返回已完成项并停止。"""
    if not paths:
        return UploadBatchResult(True, [], current_page_id=current_page_id)

    page_id = current_page_id or generate_current_page_id()
    attachments: list[dict[str, Any]] = []
    for path in paths:
        try:
            metadata = build_file_metadata(path)
            start_index = query_start_index(opener, base_url, metadata, page_id)
            attachments.append(upload_attachment(opener, base_url, metadata, page_id, start_index))
        except AttachmentUploadError as exc:
            # 部分上传不可回滚，必须把已完成附件显式交给调用方诊断。
            return UploadBatchResult(
                False,
                attachments,
                failed_file=Path(path).name,
                error=exc.to_dict(),
                current_page_id=page_id,
            )
    return UploadBatchResult(True, attachments, current_page_id=page_id)
