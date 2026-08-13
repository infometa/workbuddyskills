#!/usr/bin/env python3
"""Seeyon 会议实体、协议载荷与响应解析核心。by AI.Coding"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def load_shanghai_zone():
    """加载 Asia/Shanghai，系统无 IANA 数据时回退到现代中国 UTC+8。"""
    try:
        return ZoneInfo("Asia/Shanghai")
    except ZoneInfoNotFoundError:
        # Windows 精简 Python 可能未携带 tzdata；会议业务使用现代日期，固定 UTC+8 等价。
        return timezone(timedelta(hours=8), name="Asia/Shanghai")


SHANGHAI_ZONE = load_shanghai_zone()
TEXT_TIME_FORMAT = "%Y-%m-%d %H:%M"


class MeetingError(ValueError):
    """表示会议输入、载荷或业务响应不满足发送约束。by AI.Coding"""

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """保存稳定错误码、消息和诊断详情。"""
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化错误结构。"""
        return {"code": self.code, "message": str(self), "details": self.details}


@dataclass(frozen=True)
class MeetingEntity:
    """表示会议中的人员或部门实体。by AI.Coding"""

    kind: str
    entity_id: str
    name: str
    source: str

    def __post_init__(self) -> None:
        """拒绝非法实体类型和空 ID。"""
        if self.kind not in {"member", "department"}:
            raise MeetingError(
                "invalid_entity_kind",
                "会议实体类型必须是 member 或 department。",
                {"kind": self.kind},
            )
        if not str(self.entity_id).strip():
            raise MeetingError("entity_id_missing", "会议实体 ID不能为空。")

    def value(self) -> str:
        """转换为 Seeyon 人员选择控件值。"""
        prefix = "Member" if self.kind == "member" else "Department"
        return f"{prefix}|{self.entity_id}"

    def to_dict(self) -> dict[str, str]:
        """转换为稳定 JSON 输出。"""
        return {
            "kind": self.kind,
            "id": self.entity_id,
            "name": self.name,
            "source": self.source,
            "value": self.value(),
        }


@dataclass(frozen=True)
class ContentSaveResult:
    """保存会议正文后的正文 ID和临时会议 ID。by AI.Coding"""

    content_id: str
    meeting_temp_id: str


@dataclass(frozen=True)
class MeetingSendResult:
    """最终会议发送成功后的会议 ID和原始正文。by AI.Coding"""

    meeting_id: str
    content: str
    room_app_state: Any


@dataclass(frozen=True)
class MeetingType:
    """表示 meetingInfo 返回的可用会议分类。by AI.Coding"""

    meeting_type_id: str
    name: str
    type_value: str

    def to_dict(self) -> dict[str, str]:
        """转换为发送结果中的稳定分类结构。"""
        return {
            "id": self.meeting_type_id,
            "name": self.name,
            "type": self.type_value,
        }


def parse_time_millis(value: int | str) -> int:
    """把毫秒时间戳或上海时区文本时间转换为毫秒整数。"""
    if isinstance(value, bool):
        raise MeetingError("invalid_time", "会议时间不能是布尔值。", {"value": value})
    if isinstance(value, int) or (isinstance(value, str) and value.strip().lstrip("-").isdigit()):
        timestamp = int(value)
        # 抓包协议使用毫秒；拒绝秒级值，避免生成 1970 年附近的错误会议。
        if timestamp < 100_000_000_000:
            raise MeetingError(
                "invalid_time",
                "会议时间戳必须是正的毫秒时间戳。",
                {"value": value},
            )
        return timestamp
    if not isinstance(value, str):
        raise MeetingError("invalid_time", "会议时间格式无效。", {"value": value})
    try:
        parsed = datetime.strptime(value.strip(), TEXT_TIME_FORMAT).replace(tzinfo=SHANGHAI_ZONE)
    except ValueError as exc:
        raise MeetingError(
            "invalid_time",
            "会议时间必须是毫秒时间戳或 YYYY-MM-DD HH:mm。",
            {"value": value},
        ) from exc
    return int(parsed.timestamp() * 1000)


def validate_time_range(begin_date: int, end_date: int) -> None:
    """校验会议结束时间严格晚于开始时间。"""
    if end_date <= begin_date:
        raise MeetingError(
            "invalid_time_range",
            "会议结束时间必须晚于开始时间。",
            {"beginDate": begin_date, "endDate": end_date},
        )


def join_entity_values(entities: list[MeetingEntity]) -> str:
    """按输入顺序用逗号连接组织实体值。"""
    return ",".join(entity.value() for entity in entities)


def build_conflict_payload(
    begin_date: int,
    end_date: int,
    emcee: MeetingEntity,
    recorder: MeetingEntity,
    conferees: list[MeetingEntity],
) -> dict[str, Any]:
    """构造 messageConflictApi 的单个业务参数对象。"""
    validate_time_range(begin_date, end_date)
    # 角色重复必须保留，服务端据此区分主持人与记录人冲突来源。
    conflict_entities = [emcee, recorder, *conferees]
    return {
        "id": "",
        "startDate": begin_date,
        "endDate": end_date,
        "otherID": join_entity_values(conflict_entities),
        "module": "meeting",
    }


def build_meeting_info_payload() -> dict[str, str]:
    """构造 meetingInfo 新建会议初始化参数。"""
    return {"meetingId": "", "templateId": ""}


def summarize_meeting_info(response_body: Any) -> dict[str, Any]:
    """只保留分类字段摘要，避免错误输出泄露 currentUser.sessionId。"""
    if not isinstance(response_body, dict):
        return {"responseType": type(response_body).__name__}
    raw_types = response_body.get("meetingTypes")
    categories = []
    if isinstance(raw_types, list):
        categories = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "type": item.get("type"),
            }
            for item in raw_types
            if isinstance(item, dict)
        ]
    return {
        "responseKeys": sorted(str(key) for key in response_body.keys()),
        "meetingTypes": categories,
    }


def parse_meeting_type(
    response_body: Any,
    requested_name: str = "普通会议",
    requested_id: Optional[str] = None,
    requested_type: Optional[str] = None,
) -> MeetingType:
    """从 meetingTypes 按 ID优先、否则按名称唯一选择会议分类。"""
    if not isinstance(response_body, dict) or not isinstance(
        response_body.get("meetingTypes"), list
    ):
        raise MeetingError(
            "meeting_info_invalid",
            "meetingInfo 响应缺少 meetingTypes 数组。",
            summarize_meeting_info(response_body),
        )
    records = [item for item in response_body["meetingTypes"] if isinstance(item, dict)]
    if requested_id:
        matches = [item for item in records if str(item.get("id") or "") == requested_id]
        selector = {"id": requested_id}
    else:
        matches = [item for item in records if str(item.get("name") or "") == requested_name]
        selector = {"name": requested_name}
    if len(matches) != 1:
        raise MeetingError(
            "meeting_type_not_unique",
            "会议分类匹配数量不是 1。",
            {**selector, "matchCount": len(matches)},
        )

    selected = matches[0]
    missing = [
        field
        for field in ("id", "name", "type")
        if selected.get(field) is None or str(selected.get(field)).strip() == ""
    ]
    if missing:
        raise MeetingError(
            "meeting_type_fields_missing",
            "选中的会议分类字段不完整。",
            {"missing": missing, "meetingType": selected},
        )
    type_value = str(selected["type"])
    if requested_type is not None and type_value != str(requested_type):
        raise MeetingError(
            "meeting_type_mismatch",
            "选中的会议分类 type 与显式参数不一致。",
            {"expected": str(requested_type), "actual": type_value},
        )
    return MeetingType(str(selected["id"]), str(selected["name"]), type_value)


def build_content_payload(
    meeting_temp_id: str,
    creator_id: str,
    title: str,
    html_content: str,
) -> dict[str, Any]:
    """构造 content.do 会议正文保存业务数据。"""
    return {
        "_currentDiv": {"_currentDiv": "0"},
        "secretLevelId": {"secretLevelId": ""},
        "mainbodyDataDiv_0": {
            "id": "-1",
            "createId": creator_id,
            "createDate": "",
            "modifyId": "",
            "modifyDate": "",
            "moduleType": "6",
            "moduleId": meeting_temp_id,
            "contentType": "10",
            "moduleTemplateId": "0",
            "contentTemplateId": "0",
            "sort": "0",
            "title": title,
            "content": html_content,
            "rightId": "",
            "status": "STATUS_RESPONSE_NEW",
            "viewState": "1",
            "hasHtmlSignature": "0",
            "contentDataId": "",
            "properties": "",
        },
    }


def to_meeting_attachment(att: dict[str, Any]) -> dict[str, Any]:
    """把自由协同上传接口的 att 转换为会议发送附件字段。"""
    required = ("filename", "mimeType", "createdate", "size", "fileUrl")
    missing = [name for name in required if att.get(name) is None or str(att.get(name)) == ""]
    if missing:
        raise MeetingError(
            "attachment_fields_missing",
            "上传附件响应缺少会议转换字段。",
            {"missing": missing},
        )
    return {
        "attachment_id": "" if att.get("id") is None else str(att.get("id")),
        "attachment_reference": str(att.get("reference") or "1"),
        "attachment_subReference": "Att",
        "attachment_category": int(att.get("category") or 0),
        "attachment_type": int(att.get("type") or 0),
        "attachment_filename": str(att["filename"]),
        "attachment_mimeType": str(att["mimeType"]),
        "attachment_createDate": str(att["createdate"]),
        "attachment_size": str(att["size"]),
        "attachment_fileUrl": str(att["fileUrl"]),
        "attachment_description": str(att.get("description") or ""),
        "attachment_needClone": "false",
    }


def build_meeting_payload(
    *,
    meeting_temp_id: str,
    title: str,
    begin_date: int,
    end_date: int,
    emcee: MeetingEntity,
    recorder: MeetingEntity,
    conferees: list[MeetingEntity],
    imparts: list[MeetingEntity],
    content: str,
    attachments: list[dict[str, Any]],
    meeting_type_id: str,
    meeting_type_name: str,
    meeting_type: str,
    meeting_place: str = "",
    before_time: int = 10,
    project_id: str = "-1",
    project_name: str = "无",
    is_send_text_messages: int = 0,
    qr_code_sign: int = 0,
    is_public: int = 0,
    sync_to_schedule: int = 0,
) -> dict[str, Any]:
    """构造 meetingAjaxManager.send 的会议对象。"""
    if not conferees:
        raise MeetingError("conferees_required", "至少需要一个与会人或与会部门。")
    validate_time_range(begin_date, end_date)
    return {
        "meetingId": "",
        "id_temp": meeting_temp_id,
        "isBatch": None,
        "title": title,
        "beginDate": begin_date,
        "endDate": end_date,
        "emceeValue": emcee.value(),
        "recorderValue": recorder.value(),
        "conferees": join_entity_values(conferees),
        "impart": join_entity_values(imparts),
        "beforeTime": before_time,
        "meetingTypeId": meeting_type_id,
        "meetingTypeName": meeting_type_name,
        "meetingType": meeting_type,
        "isSendTextMessages": is_send_text_messages,
        "projectId": project_id,
        "projectName": project_name,
        "qrCodeSign": qr_code_sign,
        "isPublic": is_public,
        "syncToSchedule": sync_to_schedule,
        "mtTitle": "",
        "attender": "",
        "tel": "",
        "notice": None,
        "plan": None,
        "meetPlace": meeting_place,
        "selectedRoomApps": [],
        "selectedVideoRoom": {},
        "meetingPassword": "",
        "videoRoomShow": "",
        "content": content,
        "bodyType": "10",
        "attachments": attachments,
        "sourceId": "0",
        "sourceType": "0",
        "linkConfigId": "",
    }


def parse_conflict_result(response_body: Any) -> list[dict[str, Any]]:
    """要求冲突接口返回对象数组并原样保留详情。"""
    if not isinstance(response_body, list) or not all(
        isinstance(item, dict) for item in response_body
    ):
        raise MeetingError(
            "conflict_response_invalid",
            "会议冲突接口必须返回对象数组。",
            {"response": response_body},
        )
    return response_body


def parse_content_save_result(response_body: Any, expected_temp_id: str) -> ContentSaveResult:
    """校验正文成功标志、正文 ID和临时会议 ID关联。"""
    if not isinstance(response_body, dict) or str(response_body.get("success")).lower() != "true":
        raise MeetingError(
            "content_save_failed",
            "会议正文保存未明确成功。",
            {"response": response_body},
        )
    content_all = response_body.get("contentAll")
    if not isinstance(content_all, dict) or not content_all.get("id"):
        raise MeetingError("content_id_missing", "会议正文保存响应缺少正文 ID。")
    actual_temp_id = content_all.get("moduleId")
    if str(actual_temp_id) != expected_temp_id:
        raise MeetingError(
            "content_meeting_mismatch",
            "正文响应关联的临时会议 ID与请求不一致。",
            {"expected": expected_temp_id, "actual": actual_temp_id},
        )
    return ContentSaveResult(str(content_all["id"]), expected_temp_id)


def parse_meeting_send_result(response_body: Any) -> MeetingSendResult:
    """仅在最终响应包含非空会议 ID时确认发送成功。"""
    if not isinstance(response_body, dict) or not response_body.get("id"):
        raise MeetingError(
            "meeting_send_failed",
            "会议发送响应缺少会议 ID。",
            {"response": response_body},
        )
    return MeetingSendResult(
        meeting_id=str(response_body["id"]),
        content=str(response_body.get("content") or ""),
        room_app_state=response_body.get("roomAppState"),
    )
