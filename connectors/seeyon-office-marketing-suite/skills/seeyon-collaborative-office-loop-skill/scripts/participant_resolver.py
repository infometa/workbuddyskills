#!/usr/bin/env python3
"""解析会议人员、部门和 Seeyon 直接组织值。by AI.Coding"""

from __future__ import annotations

import re
from typing import Any, Optional

from meeting_core import MeetingEntity
from organization_resolver import collect_department_records

RESOLVER_IMPORT_ERROR: Optional[Exception] = None

DIRECT_VALUE_PATTERN = re.compile(r"^(Member|Department)\|(-?\d+)$")


class ParticipantResolutionError(ValueError):
    """表示会议人员或部门无法唯一解析。by AI.Coding"""

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """保存稳定错误码、消息和诊断详情。"""
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化错误结构。"""
        return {"code": self.code, "message": str(self), "details": self.details}


def parse_direct_value(value: str) -> Optional[MeetingEntity]:
    """解析合法 Member|ID 或 Department|ID，非直接值返回空。"""
    match = DIRECT_VALUE_PATTERN.fullmatch(value.strip())
    if match is None:
        return None
    raw_kind, entity_id = match.groups()
    kind = "member" if raw_kind == "Member" else "department"
    return MeetingEntity(kind, entity_id, value.strip(), value.strip())


def requires_organization_snapshot(values: list[str]) -> bool:
    """判断输入中是否存在必须通过组织接口解析的名称。"""
    return any(parse_direct_value(value) is None for value in values)


def get_account_organization(snapshot: dict[str, Any], account_id: str) -> dict[str, Any]:
    """从组织快照取得指定单位数据。"""
    organizations = snapshot.get("organizations") if isinstance(snapshot, dict) else None
    organization = organizations.get(account_id) if isinstance(organizations, dict) else None
    if not isinstance(organization, dict):
        raise ParticipantResolutionError(
            "account_not_found",
            "组织快照中不存在指定单位。",
            {"accountId": account_id},
        )
    return organization


def member_records(organization: dict[str, Any], account_id: str) -> list[dict[str, Any]]:
    """提取指定单位的人员对象列表。"""
    body = organization.get("members")
    records = body.get("items") if isinstance(body, dict) else None
    if not isinstance(records, list):
        raise ParticipantResolutionError(
            "members_missing",
            "组织快照缺少人员列表。",
            {"accountId": account_id},
        )
    return [record for record in records if isinstance(record, dict)]


def department_records(organization: dict[str, Any], account_id: str) -> list[dict[str, str]]:
    """递归提取指定单位的部门 ID和名称。"""
    if RESOLVER_IMPORT_ERROR is not None:
        raise ParticipantResolutionError(
            "shared_dependency_missing",
            "缺少自由协同组织解析依赖。",
            {"reason": str(RESOLVER_IMPORT_ERROR)},
        )
    body = organization.get("departments")
    tree = body.get("departmentTree") if isinstance(body, dict) else None
    if tree is None:
        raise ParticipantResolutionError(
            "departments_missing",
            "组织快照缺少部门树。",
            {"accountId": account_id},
        )
    return collect_department_records(tree, account_id)


def unique_match(
    records: list[dict[str, Any]],
    field: str,
    expected: str,
    entity_label: str,
) -> Optional[dict[str, Any]]:
    """返回唯一匹配、无匹配返回空，多匹配抛出错误。"""
    matches = [record for record in records if str(record.get(field) or "") == expected]
    if len(matches) > 1:
        raise ParticipantResolutionError(
            "entity_not_unique",
            f"{entity_label}匹配数量大于 1。",
            {"field": field, "value": expected, "matchCount": len(matches)},
        )
    return matches[0] if matches else None


def entity_from_member(record: dict[str, Any], source: str) -> MeetingEntity:
    """把组织人员记录转换为会议人员实体。"""
    if record.get("id") is None:
        raise ParticipantResolutionError(
            "member_id_missing",
            "人员记录缺少 ID。",
            {"source": source},
        )
    name = record.get("name") or record.get("loginName") or source
    return MeetingEntity("member", str(record["id"]), str(name), source)


def entity_from_department(record: dict[str, Any], source: str) -> MeetingEntity:
    """把组织部门记录转换为会议部门实体。"""
    if record.get("id") is None:
        raise ParticipantResolutionError(
            "department_id_missing",
            "部门记录缺少 ID。",
            {"source": source},
        )
    return MeetingEntity("department", str(record["id"]), str(record.get("name") or source), source)


def resolve_member(
    value: str,
    snapshot: Optional[dict[str, Any]],
    account_id: str,
) -> MeetingEntity:
    """把主持人或记录人输入解析为唯一人员实体。"""
    raw_value = value.strip()
    direct = parse_direct_value(raw_value)
    if direct is not None:
        if direct.kind != "member":
            raise ParticipantResolutionError(
                "role_member_required",
                "主持人和记录人必须是人员。",
                {"value": raw_value},
            )
        return direct
    login_name = raw_value.removeprefix("member:")
    if raw_value.startswith("department:") or not login_name:
        raise ParticipantResolutionError(
            "role_member_required",
            "主持人和记录人必须使用人员登录名或 Member|ID。",
            {"value": raw_value},
        )
    if snapshot is None:
        raise ParticipantResolutionError(
            "organization_snapshot_required",
            "按登录名解析人员时需要组织快照。",
            {"value": raw_value},
        )
    organization = get_account_organization(snapshot, account_id)
    record = unique_match(member_records(organization, account_id), "loginName", login_name, "人员")
    if record is None:
        raise ParticipantResolutionError(
            "member_not_found",
            "人员登录名未匹配到唯一人员。",
            {"loginName": login_name, "matchCount": 0},
        )
    return entity_from_member(record, raw_value)


def resolve_entity(
    value: str,
    snapshot: Optional[dict[str, Any]],
    account_id: str,
) -> MeetingEntity:
    """解析与会人或知会人的人员、部门或直接组织值。"""
    raw_value = value.strip()
    if not raw_value:
        raise ParticipantResolutionError("entity_input_empty", "会议参与人输入不能为空。")
    direct = parse_direct_value(raw_value)
    if direct is not None:
        return direct
    if snapshot is None:
        raise ParticipantResolutionError(
            "organization_snapshot_required",
            "按名称解析会议参与人时需要组织快照。",
            {"value": raw_value},
        )
    organization = get_account_organization(snapshot, account_id)
    members = member_records(organization, account_id)
    departments = department_records(organization, account_id)

    if raw_value.startswith("member:"):
        login_name = raw_value.removeprefix("member:")
        member = unique_match(members, "loginName", login_name, "人员")
        if member is None:
            raise ParticipantResolutionError(
                "member_not_found",
                "人员登录名未匹配到唯一人员。",
                {"loginName": login_name, "matchCount": 0},
            )
        return entity_from_member(member, raw_value)
    if raw_value.startswith("department:"):
        department_name = raw_value.removeprefix("department:")
        department = unique_match(departments, "name", department_name, "部门")
        if department is None:
            raise ParticipantResolutionError(
                "department_not_found",
                "部门名称未匹配到唯一部门。",
                {"departmentName": department_name, "matchCount": 0},
            )
        return entity_from_department(department, raw_value)

    member = unique_match(members, "loginName", raw_value, "人员")
    department = unique_match(departments, "name", raw_value, "部门")
    if member is not None and department is not None:
        # 普通文本无法表达调用方意图，必须要求显式前缀而不是猜测类型。
        raise ParticipantResolutionError(
            "entity_ambiguous",
            "会议参与人输入存在人员与部门歧义，请使用 member: 或 department:。",
            {"value": raw_value},
        )
    if member is not None:
        return entity_from_member(member, raw_value)
    if department is not None:
        return entity_from_department(department, raw_value)
    raise ParticipantResolutionError(
        "entity_not_found",
        "会议参与人未匹配到人员或部门。",
        {"value": raw_value, "matchCount": 0},
    )


def resolve_entities(
    values: list[str],
    snapshot: Optional[dict[str, Any]],
    account_id: str,
) -> list[MeetingEntity]:
    """按输入顺序解析多个与会人或知会人。"""
    return [resolve_entity(value, snapshot, account_id) for value in values]
