#!/usr/bin/env python3
"""基于既有 OA 会话发起 Seeyon 自由协同。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from attachment_upload import (
    AttachmentUploadError,
    UploadBatchResult,
    build_file_metadata,
    generate_current_page_id,
    upload_attachments,
)
from collaboration_core import (
    CollaborationError,
    Participant,
    build_content_payload,
    build_parallel_process_xml,
    build_send_payload,
    generate_negative_id,
    parse_content_save_result,
    parse_send_result,
    validate_raw_process_xml,
)
from organization_resolver import (
    ResolutionError,
    load_organization_snapshot,
    participant_from_exact,
    resolve_participant,
    resolve_participants,
)
from seeyon_http import build_opener, normalize_http_error, post_form, post_json


CONTENT_ID_PLACEHOLDER = "__CONTENT_ID_FROM_SAVE_RESPONSE__"


@dataclass(frozen=True)
class CollaborationConfig:
    """保存一次自由协同发送的完整业务输入。by AI.Coding"""

    base_url: str
    session_id: str
    route: Optional[str]
    subject: str
    html_content: str
    sender_exact: Optional[dict[str, Any]]
    sender_login_name: Optional[str]
    recipient_exact_values: list[dict[str, Any]]
    recipient_login_names: list[str]
    account_id: str
    organization_snapshot: Optional[dict[str, Any]]
    process_xml: Optional[str]
    attachment_paths: list[Path]
    current_page_id: Optional[str]
    dry_run: bool


@dataclass(frozen=True)
class PreparedCollaboration:
    """保存全部前置校验完成后的人员、流程、ID和附件描述。by AI.Coding"""

    config: CollaborationConfig
    sender: Participant
    recipients: list[Participant]
    summary_id: str
    request_token: str
    process_xml: str
    flow_mode: str
    attachment_descriptors: list[dict[str, Any]]
    current_page_id: Optional[str]
    content_payload: dict[str, Any]


class CollaborationHttpClient:
    """封装附件、正文和最终发送三个写阶段。by AI.Coding"""

    def __init__(self, base_url: str, session_id: str, route: Optional[str]) -> None:
        """使用统一认证上下文提供的会话信息创建请求客户端。"""
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(session_id, route)

    def upload(self, paths: list[Path], current_page_id: Optional[str]) -> UploadBatchResult:
        """上传可选附件并返回批量阶段结果。"""
        return upload_attachments(self.opener, self.base_url, paths, current_page_id)

    def save_content(self, payload: dict[str, Any]) -> Any:
        """调用 content.do 保存协同正文并返回 JSON 响应体。"""
        url = (
            f"{self.base_url}/content/content.do?method=saveOrUpdate&onlyGenerateSn=false"
            "&optType=send&_affairId=&_openFrom="
        )
        fields = {
            "_json_params": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        }
        response = post_form(self.opener, url, fields)
        if response.status < 200 or response.status >= 300:
            raise CollaborationError(
                "content_http_failed",
                "正文保存接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body

    def send(self, payload: dict[str, Any]) -> Any:
        """调用协同 REST 接口执行最终发送并返回 JSON 响应体。"""
        url = f"{self.base_url}/rest/collaboration/v1/web/new/send"
        response = post_json(self.opener, url, payload)
        if response.status < 200 or response.status >= 300:
            raise CollaborationError(
                "send_http_failed",
                "协同发送接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body


def parse_json_argument(value: str, label: str) -> dict[str, Any]:
    """解析单个 JSON 对象命令行参数并返回明确错误。"""
    try:
        body = json.loads(value)
    except json.JSONDecodeError as exc:
        raise CollaborationError(
            "invalid_json_argument",
            f"{label} 不是有效 JSON。",
            {"label": label, "reason": str(exc)},
        ) from exc
    if not isinstance(body, dict):
        raise CollaborationError(
            "invalid_json_argument",
            f"{label} 必须是 JSON 对象。",
            {"label": label},
        )
    return body


def load_text(
    inline_value: Optional[str],
    file_path: Optional[Path],
    label: str,
) -> str:
    """从内联值或 UTF-8 文件读取正文，并拒绝冲突或空输入。"""
    if inline_value is not None and file_path is not None:
        raise CollaborationError(
            "conflicting_text_inputs",
            f"{label} 不能同时使用内联值和文件。",
            {"label": label},
        )
    if file_path is not None:
        try:
            value = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CollaborationError(
                "text_file_unreadable",
                f"无法读取 {label} 文件。",
                {"path": str(file_path), "reason": str(exc)},
            ) from exc
    else:
        value = inline_value or ""
    if not value.strip():
        raise CollaborationError("required_text_missing", f"{label} 不能为空。")
    return value


def validate_basic_input(config: CollaborationConfig) -> None:
    """在任何外部写操作前校验会话、地址、主题和人员入口。"""
    missing: list[str] = []
    if not config.base_url.strip():
        missing.append("baseUrl")
    if not config.session_id.strip():
        missing.append("sessionId")
    if not config.subject.strip():
        missing.append("subject")
    if not config.html_content.strip():
        missing.append("content")
    if config.sender_exact is None and not (config.sender_login_name or "").strip():
        missing.append("sender")
    if not config.recipient_exact_values and not config.recipient_login_names:
        missing.append("recipients")
    if missing:
        raise CollaborationError(
            "required_input_missing",
            "自由协同输入缺少必填项。",
            {"missing": missing},
        )


def resolve_sender(config: CollaborationConfig) -> Participant:
    """优先使用精确发送人，否则按单位和登录名从快照解析。"""
    if config.sender_exact is not None:
        return participant_from_exact(config.sender_exact)
    if config.organization_snapshot is None:
        raise ResolutionError(
            "organization_snapshot_required",
            "按登录名解析发送人时必须提供组织机构快照。",
            {"loginName": config.sender_login_name},
        )
    if not config.account_id.strip():
        raise ResolutionError("account_id_required", "按登录名解析人员时必须提供单位 ID。")
    return resolve_participant(
        config.organization_snapshot,
        config.account_id,
        config.sender_login_name or "",
    )


def prepare_collaboration(config: CollaborationConfig) -> PreparedCollaboration:
    """完成输入、人员、流程、附件文件和关联 ID的全部前置准备。"""
    validate_basic_input(config)
    sender = resolve_sender(config)
    account_id = config.account_id or sender.account_id
    recipients = resolve_participants(
        config.recipient_exact_values,
        config.recipient_login_names,
        config.organization_snapshot,
        account_id,
    )
    if not recipients:
        raise CollaborationError("recipients_required", "至少需要一个接收人。")

    if config.process_xml is not None:
        validate_raw_process_xml(config.process_xml)
        process_xml = config.process_xml
        flow_mode = "raw-xml"
    else:
        process_xml = build_parallel_process_xml(sender, recipients)
        flow_mode = "parallel"

    # 先校验全部本地文件，避免上传到一半才发现后续路径无效。
    descriptors: list[dict[str, Any]] = []
    for path in config.attachment_paths:
        metadata = build_file_metadata(path)
        descriptors.append(
            {
                "sourcePath": str(metadata.path),
                "fileName": metadata.file_name,
                "fileSize": metadata.file_size,
                "lastModifiedDate": str(metadata.last_modified_ms),
                "mimeType": metadata.mime_type,
                "pendingUpload": True,
            }
        )
    current_page_id = config.current_page_id
    if descriptors and not current_page_id:
        current_page_id = generate_current_page_id()

    summary_id = generate_negative_id()
    request_token = generate_negative_id()
    content_payload = build_content_payload(
        summary_id,
        sender,
        config.subject,
        config.html_content,
    )
    return PreparedCollaboration(
        config=config,
        sender=sender,
        recipients=recipients,
        summary_id=summary_id,
        request_token=request_token,
        process_xml=process_xml,
        flow_mode=flow_mode,
        attachment_descriptors=descriptors,
        current_page_id=current_page_id,
        content_payload=content_payload,
    )


def error_dict(exc: Exception) -> dict[str, Any]:
    """把业务、网络和未知异常转换为稳定错误结构。"""
    if isinstance(exc, (CollaborationError, ResolutionError, AttachmentUploadError)):
        return exc.to_dict()
    if isinstance(exc, (urllib.error.HTTPError, urllib.error.URLError)):
        return {
            "code": "network_error",
            "message": "Seeyon 接口请求失败。",
            "details": normalize_http_error(exc),
        }
    return {
        "code": "unexpected_error",
        "message": str(exc) or exc.__class__.__name__,
        "details": {"type": exc.__class__.__name__},
    }


def result_base(prepared: PreparedCollaboration, dry_run: bool) -> dict[str, Any]:
    """构造成功和阶段失败共享的非敏感结果字段。"""
    return {
        "ok": False,
        "dryRun": dry_run,
        "summaryId": prepared.summary_id,
        "contentId": None,
        "sender": prepared.sender.to_dict(),
        "recipients": [participant.to_dict() for participant in prepared.recipients],
        "attachments": [],
        "currentPageId": prepared.current_page_id,
        "flowMode": prepared.flow_mode,
        "completedStages": ["validate_input", "resolve_participants", "prepare_workflow"],
    }


def send_free_collaboration(
    config: CollaborationConfig,
    http_client: Optional[CollaborationHttpClient] = None,
) -> dict[str, Any]:
    """按严格阶段门控执行 dry-run 或真实自由协同发送。"""
    try:
        prepared = prepare_collaboration(config)
    except AttachmentUploadError as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "validate_attachments",
            "error": error_dict(exc),
            "completedStages": ["validate_input", "resolve_participants", "prepare_workflow"],
        }
    except (CollaborationError, ResolutionError) as exc:
        code = getattr(exc, "code", "")
        if code.startswith("raw_process"):
            failed_step = "prepare_workflow"
        elif isinstance(exc, ResolutionError):
            failed_step = "resolve_participants"
        else:
            failed_step = "validate_input"
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": failed_step,
            "error": error_dict(exc),
            "completedStages": [],
        }

    result = result_base(prepared, config.dry_run)
    preview_attachments = prepared.attachment_descriptors
    preview_send_payload = build_send_payload(
        prepared.summary_id,
        CONTENT_ID_PLACEHOLDER,
        prepared.request_token,
        prepared.sender,
        prepared.recipients,
        config.subject,
        prepared.process_xml,
        preview_attachments,
        int(time.time() * 1000),
    )
    if config.dry_run:
        # dry-run 只构造本地预览，禁止创建会话客户端或调用任何写接口。
        result.update(
            {
                "ok": True,
                "attachments": preview_attachments,
                "contentIdSource": "save-response",
                "payloadPreview": {
                    "contentSave": prepared.content_payload,
                    "send": preview_send_payload,
                },
            }
        )
        return result

    client = http_client or CollaborationHttpClient(config.base_url, config.session_id, config.route)
    attachments: list[dict[str, Any]] = []
    if config.attachment_paths:
        try:
            upload_result = client.upload(config.attachment_paths, prepared.current_page_id)
        except Exception as exc:
            result.update({"failed_step": "upload_attachments", "error": error_dict(exc)})
            return result
        attachments = upload_result.attachments
        result["attachments"] = attachments
        result["currentPageId"] = upload_result.current_page_id
        if not upload_result.ok:
            result.update(
                {
                    "failed_step": "upload_attachments",
                    "error": upload_result.error,
                    "failedFile": upload_result.failed_file,
                }
            )
            return result
        result["completedStages"].append("upload_attachments")

    try:
        content_response = client.save_content(prepared.content_payload)
        content_result = parse_content_save_result(content_response, prepared.summary_id)
    except Exception as exc:
        result.update(
            {
                "failed_step": "save_content",
                "error": error_dict(exc),
                "contentSaveResponse": locals().get("content_response"),
            }
        )
        return result

    result["contentId"] = content_result.content_id
    result["contentSaveResult"] = {
        "success": True,
        "contentId": content_result.content_id,
        "summaryId": content_result.summary_id,
    }
    result["contentSaveResponse"] = content_response
    result["completedStages"].append("save_content")
    send_payload = build_send_payload(
        prepared.summary_id,
        content_result.content_id,
        prepared.request_token,
        prepared.sender,
        prepared.recipients,
        config.subject,
        prepared.process_xml,
        attachments,
        int(time.time() * 1000),
    )
    try:
        send_response = client.send(send_payload)
        send_result = parse_send_result(send_response, prepared.summary_id)
    except Exception as exc:
        result.update(
            {
                "failed_step": "send_collaboration",
                "error": error_dict(exc),
                "sendResponse": locals().get("send_response"),
            }
        )
        return result

    result.update(
        {
            "ok": True,
            "sendResult": {"success": True, "summaryId": send_result.summary_id},
            "sendResponse": send_response,
        }
    )
    result["completedStages"].append("send_collaboration")
    return result


def send_collaboration(
    config: CollaborationConfig,
    http_client: Optional[CollaborationHttpClient] = None,
) -> dict[str, Any]:
    """以新 Skill 的统一命名调用自由协同发送流程。"""
    return send_free_collaboration(config, http_client=http_client)


def build_parser() -> argparse.ArgumentParser:
    """创建自由协同命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="使用既有 OA 会话发起 Seeyon 自由协同")
    parser.add_argument("--base-url", default=os.getenv("SEIYON_BASE_URL", ""))
    parser.add_argument("--session-id", default=os.getenv("SEIYON_SESSION_ID", ""))
    parser.add_argument("--route", default=os.getenv("SEIYON_ROUTE"))
    parser.add_argument("--subject", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--sender-json")
    parser.add_argument("--sender-login-name")
    parser.add_argument("--recipient-json", action="append", default=[])
    parser.add_argument("--recipient-login-name", action="append", default=[])
    parser.add_argument("--account-id", default="")
    parser.add_argument("--organization-data", type=Path)
    parser.add_argument("--process-xml-file", type=Path)
    parser.add_argument("--attachment", action="append", default=[], type=Path)
    parser.add_argument("--current-page-id")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def config_from_args(args: argparse.Namespace) -> CollaborationConfig:
    """把命令行参数转换为业务配置并读取可选输入文件。"""
    html_content = load_text(args.content, args.content_file, "HTML 正文")
    sender_exact = parse_json_argument(args.sender_json, "--sender-json") if args.sender_json else None
    recipient_exact_values = [
        parse_json_argument(value, "--recipient-json") for value in args.recipient_json
    ]
    organization_snapshot = (
        load_organization_snapshot(args.organization_data) if args.organization_data else None
    )
    process_xml = (
        load_text(None, args.process_xml_file, "流程 XML") if args.process_xml_file else None
    )
    return CollaborationConfig(
        base_url=args.base_url,
        session_id=args.session_id,
        route=args.route,
        subject=args.subject,
        html_content=html_content,
        sender_exact=sender_exact,
        sender_login_name=args.sender_login_name or os.getenv("OA_AUTH_USERNAME"),
        recipient_exact_values=recipient_exact_values,
        recipient_login_names=args.recipient_login_name,
        account_id=args.account_id,
        organization_snapshot=organization_snapshot,
        process_xml=process_xml,
        attachment_paths=args.attachment,
        current_page_id=args.current_page_id,
        dry_run=args.dry_run,
    )


def prepare_request(args: argparse.Namespace) -> PreparedCollaboration:
    """按设计接口从命令行参数生成已校验请求。"""
    return prepare_collaboration(config_from_args(args))


def main(argv: Optional[list[str]] = None) -> int:
    """执行 CLI、输出单个 JSON 结果并返回与 ok 对应的退出码。"""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        config = config_from_args(args)
        result = send_collaboration(config)
    except (CollaborationError, ResolutionError, AttachmentUploadError) as exc:
        result = {
            "ok": False,
            "dryRun": bool(getattr(locals().get("args"), "dry_run", False)),
            "failed_step": "parse_input",
            "error": error_dict(exc),
            "completedStages": [],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
