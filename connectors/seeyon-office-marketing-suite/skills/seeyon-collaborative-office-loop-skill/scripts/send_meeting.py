#!/usr/bin/env python3
"""基于既有 OA 会话发起 Seeyon 会议。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from meeting_core import (
    MeetingEntity,
    MeetingError,
    MeetingType,
    build_conflict_payload,
    build_content_payload,
    build_meeting_info_payload,
    build_meeting_payload,
    parse_conflict_result,
    parse_content_save_result,
    parse_meeting_type,
    parse_meeting_send_result,
    parse_time_millis,
    summarize_meeting_info,
    to_meeting_attachment,
    validate_time_range,
)
from participant_resolver import (
    ParticipantResolutionError,
    requires_organization_snapshot,
    resolve_entities,
    resolve_member,
)
from attachment_upload import (
    AttachmentUploadError,
    build_file_metadata,
    generate_current_page_id,
    upload_attachments,
)
from collaboration_core import generate_negative_id
from query_organization import query_collaboration_snapshot
from seeyon_http import build_opener, normalize_http_error, post_form


@dataclass(frozen=True)
class MeetingConfig:
    """保存一次会议发起的完整业务输入。by AI.Coding"""

    base_url: str
    session_id: str
    route: Optional[str]
    account_id: str
    current_username: str
    title: str
    html_content: str
    begin_date: int | str
    end_date: int | str
    emcee_input: Optional[str]
    recorder_input: Optional[str]
    conferee_inputs: list[str]
    impart_inputs: list[str]
    meeting_place: str
    attachment_paths: list[Path]
    current_page_id: Optional[str]
    dry_run: bool
    before_time: int = 10
    meeting_type_id: Optional[str] = None
    meeting_type_name: str = "普通会议"
    meeting_type: Optional[str] = None
    project_id: str = "-1"
    project_name: str = "无"
    is_send_text_messages: int = 0
    qr_code_sign: int = 0
    is_public: int = 0
    sync_to_schedule: int = 0


class MeetingHttpClient:
    """封装组织、冲突、附件、正文和最终发送接口。by AI.Coding"""

    def __init__(self, base_url: str, session_id: str, route: Optional[str]) -> None:
        """使用统一认证上下文输出的会话信息创建请求客户端。"""
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(session_id, route)

    def query_organization(self, account_id: str) -> dict[str, Any]:
        """查询解析会议人员所需的指定单位组织快照。"""
        result = query_collaboration_snapshot(self.opener, self.base_url, account_id)
        if not result.get("ok"):
            raise MeetingError(
                "organization_query_failed",
                "组织机构查询失败。",
                {"response": result},
            )
        return result

    def query_conflicts(self, payload: dict[str, Any]) -> Any:
        """调用 messageConflictApi 查询会议时间冲突。"""
        url = f"{self.base_url}/ajax.do?method=ajaxAction&managerName=messageConflictApi"
        fields = {
            "managerMethod": "getConflictData",
            "arguments": json.dumps([payload], ensure_ascii=False, separators=(",", ":")),
        }
        response = post_form(self.opener, url, fields)
        if response.status < 200 or response.status >= 300:
            raise MeetingError(
                "conflict_http_failed",
                "会议冲突接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body

    def query_meeting_info(self, payload: dict[str, str]) -> Any:
        """调用 meetingInfo 取得当前单位可用的会议分类。"""
        url = (
            f"{self.base_url}/ajax.do?method=ajaxAction"
            "&managerName=meetingAjaxManager&nn=meetingInfo"
        )
        fields = {
            "managerMethod": "meetingInfo",
            "arguments": json.dumps([payload], ensure_ascii=False, separators=(",", ":")),
        }
        response = post_form(self.opener, url, fields)
        if response.status < 200 or response.status >= 300:
            raise MeetingError(
                "meeting_info_http_failed",
                "会议初始化接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body

    def upload(self, paths: list[Path], current_page_id: Optional[str]):
        """复用自由协同上传流程上传可选附件。"""
        return upload_attachments(self.opener, self.base_url, paths, current_page_id)

    def save_content(self, payload: dict[str, Any]) -> Any:
        """调用 content.do 保存会议正文。"""
        url = (
            f"{self.base_url}/content/content.do?method=saveOrUpdate&onlyGenerateSn=false"
            "&optType=undefined&_affairId=&_openFrom="
        )
        fields = {
            "_json_params": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        }
        response = post_form(self.opener, url, fields)
        if response.status < 200 or response.status >= 300:
            raise MeetingError(
                "content_http_failed",
                "会议正文接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body

    def send(self, payload: dict[str, Any]) -> Any:
        """调用 meetingAjaxManager 执行最终会议发送。"""
        url = (
            f"{self.base_url}/ajax.do?method=ajaxAction"
            "&managerName=meetingAjaxManager&nn=send"
        )
        fields = {
            "managerMethod": "send",
            "arguments": json.dumps([payload], ensure_ascii=False, separators=(",", ":")),
        }
        response = post_form(self.opener, url, fields)
        if response.status < 200 or response.status >= 300:
            raise MeetingError(
                "meeting_http_failed",
                "会议发送接口未返回成功 HTTP 状态。",
                {"status": response.status, "body": response.text[:500]},
            )
        return response.body


def validate_basic_input(config: MeetingConfig) -> tuple[int, int]:
    """在任何接口调用前校验会话、内容、时间和参与人。"""
    missing: list[str] = []
    required_values = {
        "baseUrl": config.base_url,
        "sessionId": config.session_id,
        "OA_AUTH_USERNAME": config.current_username,
        "accountId": config.account_id,
        "title": config.title,
        "content": config.html_content,
    }
    for name, value in required_values.items():
        if not str(value or "").strip():
            missing.append(name)
    if not config.conferee_inputs:
        missing.append("conferees")
    if missing:
        raise MeetingError(
            "required_input_missing",
            "发起会议输入缺少必填项。",
            {"missing": missing},
        )
    begin_date = parse_time_millis(config.begin_date)
    end_date = parse_time_millis(config.end_date)
    validate_time_range(begin_date, end_date)
    if config.before_time < 0:
        raise MeetingError("invalid_before_time", "提前提醒分钟数不能为负数。")
    return begin_date, end_date


def error_dict(exc: Exception) -> dict[str, Any]:
    """把业务、附件、网络和未知异常转换为稳定错误结构。"""
    if isinstance(exc, (MeetingError, ParticipantResolutionError)):
        return exc.to_dict()
    if isinstance(exc, AttachmentUploadError):
        return exc.to_dict()
    if isinstance(exc, (urllib.error.HTTPError, urllib.error.URLError)):
        details = normalize_http_error(exc)
        return {"code": "network_error", "message": "Seeyon 接口请求失败。", "details": details}
    return {
        "code": "unexpected_error",
        "message": str(exc) or exc.__class__.__name__,
        "details": {"type": exc.__class__.__name__},
    }


def preview_attachment(metadata) -> dict[str, Any]:
    """构造 dry-run 最终发送载荷中的待上传附件占位对象。"""
    return {
        "attachment_id": "",
        "attachment_reference": "1",
        "attachment_subReference": "Att",
        "attachment_category": 0,
        "attachment_type": 0,
        "attachment_filename": metadata.file_name,
        "attachment_mimeType": metadata.mime_type,
        "attachment_createDate": "__FROM_UPLOAD_RESPONSE__",
        "attachment_size": str(metadata.file_size),
        "attachment_fileUrl": "__FROM_UPLOAD_RESPONSE__",
        "attachment_description": "",
        "attachment_needClone": "false",
        "sourcePath": str(metadata.path),
        "pendingUpload": True,
    }


def build_result_base(
    config: MeetingConfig,
    meeting_temp_id: str,
    current_user: MeetingEntity,
    meeting_type: MeetingType,
    emcee: MeetingEntity,
    recorder: MeetingEntity,
    conferees: list[MeetingEntity],
    imparts: list[MeetingEntity],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    """构造 dry-run、成功和阶段失败共享的结果字段。"""
    return {
        "ok": False,
        "dryRun": config.dry_run,
        "meetingTempId": meeting_temp_id,
        "meetingId": None,
        "contentId": None,
        "hasConflicts": bool(conflicts),
        "conflicts": conflicts,
        "meetingType": meeting_type.to_dict(),
        "participants": {
            "currentUser": current_user.to_dict(),
            "emcee": emcee.to_dict(),
            "recorder": recorder.to_dict(),
            "conferees": [entity.to_dict() for entity in conferees],
            "imparts": [entity.to_dict() for entity in imparts],
        },
        "attachments": [],
        "completedStages": [
            "validate_input",
            "resolve_participants",
            "query_meeting_info",
            "query_conflicts",
        ],
    }


def send_meeting(
    config: MeetingConfig,
    http_client: Optional[MeetingHttpClient] = None,
) -> dict[str, Any]:
    """按严格阶段门控执行 dry-run 或真实会议发起。"""
    try:
        begin_date, end_date = validate_basic_input(config)
    except Exception as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "validate_input",
            "error": error_dict(exc),
            "completedStages": [],
        }

    try:
        client = http_client or MeetingHttpClient(config.base_url, config.session_id, config.route)
    except Exception as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "create_client",
            "error": error_dict(exc),
            "completedStages": ["validate_input"],
        }

    emcee_input = (config.emcee_input or config.current_username).strip()
    recorder_input = (config.recorder_input or config.current_username).strip()
    # 正文 createId 必须来自实际登录账号，因此当前用户始终参与组织解析。
    resolution_values = [
        config.current_username,
        emcee_input,
        recorder_input,
        *config.conferee_inputs,
        *config.impart_inputs,
    ]
    snapshot: Optional[dict[str, Any]] = None
    if requires_organization_snapshot(resolution_values):
        try:
            snapshot = client.query_organization(config.account_id)
        except Exception as exc:
            return {
                "ok": False,
                "dryRun": config.dry_run,
                "failed_step": "query_organization",
                "error": error_dict(exc),
                "completedStages": ["validate_input"],
            }

    try:
        current_user = resolve_member(config.current_username, snapshot, config.account_id)
        emcee = resolve_member(emcee_input, snapshot, config.account_id)
        recorder = resolve_member(recorder_input, snapshot, config.account_id)
        conferees = resolve_entities(config.conferee_inputs, snapshot, config.account_id)
        imparts = resolve_entities(config.impart_inputs, snapshot, config.account_id)
    except Exception as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "resolve_participants",
            "error": error_dict(exc),
            "completedStages": ["validate_input"],
        }

    meeting_info_payload = build_meeting_info_payload()
    try:
        meeting_info_response = client.query_meeting_info(meeting_info_payload)
        meeting_type = parse_meeting_type(
            meeting_info_response,
            requested_name=config.meeting_type_name,
            requested_id=config.meeting_type_id,
            requested_type=config.meeting_type,
        )
    except Exception as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "query_meeting_info",
            "error": error_dict(exc),
            "meetingInfoSummary": summarize_meeting_info(locals().get("meeting_info_response")),
            "completedStages": ["validate_input", "resolve_participants"],
        }

    conflict_payload = build_conflict_payload(
        begin_date,
        end_date,
        emcee,
        recorder,
        conferees,
    )
    try:
        conflict_response = client.query_conflicts(conflict_payload)
        conflicts = parse_conflict_result(conflict_response)
    except Exception as exc:
        return {
            "ok": False,
            "dryRun": config.dry_run,
            "failed_step": "query_conflicts",
            "error": error_dict(exc),
            "conflictResponse": locals().get("conflict_response"),
            "completedStages": [
                "validate_input",
                "resolve_participants",
                "query_meeting_info",
            ],
        }

    meeting_temp_id = generate_negative_id()
    content_payload = build_content_payload(
        meeting_temp_id,
        current_user.entity_id,
        config.title,
        config.html_content,
    )
    result = build_result_base(
        config,
        meeting_temp_id,
        current_user,
        meeting_type,
        emcee,
        recorder,
        conferees,
        imparts,
        conflicts,
    )

    try:
        metadata_list = [build_file_metadata(path) for path in config.attachment_paths]
    except Exception as exc:
        result.update(
            {
                "failed_step": "validate_attachments",
                "error": error_dict(exc),
            }
        )
        return result
    current_page_id = config.current_page_id
    if metadata_list and not current_page_id:
        current_page_id = generate_current_page_id()
    preview_attachments = [preview_attachment(metadata) for metadata in metadata_list]
    preview_send_payload = build_meeting_payload(
        meeting_temp_id=meeting_temp_id,
        title=config.title,
        begin_date=begin_date,
        end_date=end_date,
        emcee=emcee,
        recorder=recorder,
        conferees=conferees,
        imparts=imparts,
        content=config.html_content,
        attachments=preview_attachments,
        meeting_place=config.meeting_place,
        before_time=config.before_time,
        meeting_type_id=meeting_type.meeting_type_id,
        meeting_type_name=meeting_type.name,
        meeting_type=meeting_type.type_value,
        project_id=config.project_id,
        project_name=config.project_name,
        is_send_text_messages=config.is_send_text_messages,
        qr_code_sign=config.qr_code_sign,
        is_public=config.is_public,
        sync_to_schedule=config.sync_to_schedule,
    )
    result["completedStages"].append("validate_attachments")
    result["currentPageId"] = current_page_id
    if config.dry_run:
        # dry-run 在只读冲突查询后返回，禁止执行附件、正文和会议写接口。
        result.update(
            {
                "ok": True,
                "attachments": preview_attachments,
                "payloadPreview": {
                    "meetingInfo": meeting_info_payload,
                    "conflictQuery": conflict_payload,
                    "contentSave": content_payload,
                    "sendMeeting": preview_send_payload,
                },
            }
        )
        return result

    meeting_attachments: list[dict[str, Any]] = []
    if config.attachment_paths:
        try:
            upload_result = client.upload(config.attachment_paths, current_page_id)
        except Exception as exc:
            result.update({"failed_step": "upload_attachments", "error": error_dict(exc)})
            return result
        result["currentPageId"] = upload_result.current_page_id
        if not upload_result.ok:
            result.update(
                {
                    "failed_step": "upload_attachments",
                    "attachments": upload_result.attachments,
                    "failedFile": upload_result.failed_file,
                    "error": upload_result.error,
                }
            )
            return result
        try:
            meeting_attachments = [to_meeting_attachment(att) for att in upload_result.attachments]
        except Exception as exc:
            result.update(
                {
                    "failed_step": "convert_attachments",
                    "attachments": upload_result.attachments,
                    "error": error_dict(exc),
                }
            )
            return result
        result["attachments"] = meeting_attachments
        result["completedStages"].append("upload_attachments")

    try:
        content_response = client.save_content(content_payload)
        content_result = parse_content_save_result(content_response, meeting_temp_id)
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
    result["contentSaveResponse"] = content_response
    result["completedStages"].append("save_content")

    send_payload = build_meeting_payload(
        meeting_temp_id=meeting_temp_id,
        title=config.title,
        begin_date=begin_date,
        end_date=end_date,
        emcee=emcee,
        recorder=recorder,
        conferees=conferees,
        imparts=imparts,
        content=config.html_content,
        attachments=meeting_attachments,
        meeting_place=config.meeting_place,
        before_time=config.before_time,
        meeting_type_id=meeting_type.meeting_type_id,
        meeting_type_name=meeting_type.name,
        meeting_type=meeting_type.type_value,
        project_id=config.project_id,
        project_name=config.project_name,
        is_send_text_messages=config.is_send_text_messages,
        qr_code_sign=config.qr_code_sign,
        is_public=config.is_public,
        sync_to_schedule=config.sync_to_schedule,
    )
    try:
        send_response = client.send(send_payload)
        send_result = parse_meeting_send_result(send_response)
    except Exception as exc:
        result.update(
            {
                "failed_step": "send_meeting",
                "error": error_dict(exc),
                "sendResponse": locals().get("send_response"),
            }
        )
        return result
    result.update(
        {
            "ok": True,
            "meetingId": send_result.meeting_id,
            "sendResponse": send_response,
            "payloadSummary": {
                "meetingInfo": meeting_info_payload,
                "conflictQuery": conflict_payload,
                "contentSave": content_payload,
                "sendMeeting": send_payload,
            },
        }
    )
    result["completedStages"].append("send_meeting")
    return result


def load_text(inline_value: Optional[str], file_path: Optional[Path]) -> str:
    """从内联参数或 UTF-8 文件读取会议正文。"""
    if inline_value is not None and file_path is not None:
        raise MeetingError("conflicting_content_inputs", "正文不能同时使用 --content 和 --content-file。")
    if file_path is not None:
        try:
            value = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MeetingError(
                "content_file_unreadable",
                "无法读取会议正文文件。",
                {"path": str(file_path), "reason": str(exc)},
            ) from exc
    else:
        value = inline_value or ""
    if not value.strip():
        raise MeetingError("content_required", "会议正文不能为空。")
    return value


def build_parser() -> argparse.ArgumentParser:
    """创建发起会议命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="使用既有 OA 会话发起 Seeyon 会议")
    parser.add_argument("--base-url", default=os.getenv("SEIYON_BASE_URL", ""))
    parser.add_argument("--session-id", default=os.getenv("SEIYON_SESSION_ID", ""))
    parser.add_argument("--route", default=os.getenv("SEIYON_ROUTE"))
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--begin-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--emcee")
    parser.add_argument("--recorder")
    parser.add_argument("--conferee", action="append", default=[])
    parser.add_argument("--impart", action="append", default=[])
    parser.add_argument("--meeting-place", default="")
    parser.add_argument("--before-time", type=int, default=10)
    parser.add_argument("--meeting-type-id")
    parser.add_argument("--meeting-type-name", default="普通会议")
    parser.add_argument("--meeting-type")
    parser.add_argument("--project-id", default="-1")
    parser.add_argument("--project-name", default="无")
    parser.add_argument("--send-text-messages", action="store_true")
    parser.add_argument("--qr-code-sign", action="store_true")
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--sync-to-schedule", action="store_true")
    parser.add_argument("--attachment", action="append", default=[], type=Path)
    parser.add_argument("--current-page-id")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def config_from_args(args: argparse.Namespace) -> MeetingConfig:
    """把命令行参数和环境变量转换为会议配置。"""
    return MeetingConfig(
        base_url=args.base_url,
        session_id=args.session_id,
        route=args.route,
        account_id=args.account_id,
        current_username=os.getenv("OA_AUTH_USERNAME", ""),
        title=args.title,
        html_content=load_text(args.content, args.content_file),
        begin_date=args.begin_date,
        end_date=args.end_date,
        emcee_input=args.emcee,
        recorder_input=args.recorder,
        conferee_inputs=args.conferee,
        impart_inputs=args.impart,
        meeting_place=args.meeting_place,
        attachment_paths=args.attachment,
        current_page_id=args.current_page_id,
        dry_run=args.dry_run,
        before_time=args.before_time,
        meeting_type_id=args.meeting_type_id,
        meeting_type_name=args.meeting_type_name,
        meeting_type=args.meeting_type,
        project_id=args.project_id,
        project_name=args.project_name,
        is_send_text_messages=int(args.send_text_messages),
        qr_code_sign=int(args.qr_code_sign),
        is_public=int(args.public),
        sync_to_schedule=int(args.sync_to_schedule),
    )


def main(argv: Optional[list[str]] = None) -> int:
    """执行 CLI、输出单个 JSON 结果并返回与 ok 对应的退出码。"""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = send_meeting(config_from_args(args))
    except MeetingError as exc:
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
