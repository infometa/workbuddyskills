#!/usr/bin/env python3
"""从组织机构快照解析自由协同参与人。by AI.Coding"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from collaboration_core import Participant


class ResolutionError(ValueError):
    """表示人员、部门或岗位无法唯一解析。by AI.Coding"""

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """保存稳定错误码、消息和诊断详情。"""
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化错误结构。"""
        return {
            "code": self.code,
            "message": str(self),
            "details": self.details,
        }


def load_organization_snapshot(path: Path) -> dict[str, Any]:
    """读取并校验组织机构 Skill 输出的 JSON 快照。"""
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ResolutionError(
            "organization_snapshot_unreadable",
            f"无法读取组织机构快照: {path}",
            {"path": str(path), "reason": str(exc)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise ResolutionError(
            "organization_snapshot_invalid_json",
            "组织机构快照不是有效 JSON。",
            {"path": str(path), "reason": str(exc)},
        ) from exc

    if not isinstance(body, dict) or not isinstance(body.get("organizations"), dict):
        raise ResolutionError(
            "organization_snapshot_invalid",
            "组织机构快照缺少 organizations 对象。",
            {"path": str(path)},
        )
    return body


def participant_from_exact(data: dict[str, Any]) -> Participant:
    """校验精确人员输入并转换为统一 Participant。"""
    required = {
        "name": data.get("name"),
        "memberId": data.get("memberId"),
        "departmentId": data.get("departmentId"),
        "postId": data.get("postId"),
        "accountId": data.get("accountId"),
    }
    missing = [name for name, value in required.items() if value is None or str(value).strip() == ""]
    if missing:
        raise ResolutionError(
            "invalid_exact_participant",
            "精确人员数据字段不完整。",
            {"missing": missing},
        )
    return Participant(
        name=str(required["name"]),
        member_id=str(required["memberId"]),
        department_id=str(required["departmentId"]),
        post_id=str(required["postId"]),
        account_id=str(required["accountId"]),
        login_name=str(data["loginName"]) if data.get("loginName") else None,
    )


def get_account_organization(snapshot: dict[str, Any], account_id: str) -> dict[str, Any]:
    """取得指定单位的组织数据，不存在时返回明确错误。"""
    organizations = snapshot.get("organizations")
    organization = organizations.get(account_id) if isinstance(organizations, dict) else None
    if not isinstance(organization, dict):
        raise ResolutionError(
            "account_not_found",
            "组织机构快照中不存在指定单位。",
            {"accountId": account_id},
        )
    return organization


def collect_department_records(value: Any, account_id: str) -> list[dict[str, str]]:
    """递归收集部门树中的部门 ID和名称，并按 ID去重。"""
    records: dict[str, dict[str, str]] = {}

    def visit(node: Any) -> None:
        """递归访问列表和字典节点。"""
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return

        department_body = node.get("v3xOrgDepartment")
        candidate = department_body if isinstance(department_body, dict) else node
        entity_type = candidate.get("entityType") or candidate.get("type")
        icon_skin = str(node.get("iconSkin") or "").lower()
        is_department = (
            isinstance(department_body, dict)
            or entity_type == "Department"
            or "department" in icon_skin
        )
        candidate_id = candidate.get("id") or node.get("id")
        candidate_name = candidate.get("name") or node.get("name")
        candidate_account = candidate.get("orgAccountId") or node.get("orgAccountId")
        if is_department and candidate_id is not None and candidate_name:
            # 单位字段存在时必须匹配，避免跨单位同名部门被错误选中。
            if candidate_account is None or str(candidate_account) == account_id:
                records[str(candidate_id)] = {
                    "id": str(candidate_id),
                    "name": str(candidate_name),
                }

        for child in node.values():
            if isinstance(child, (dict, list)):
                visit(child)

    visit(value)
    return list(records.values())


def find_unique(
    records: list[dict[str, Any]],
    field: str,
    expected: str,
    code: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    """按字段完全匹配唯一记录，否则抛出稳定解析错误。"""
    matches = [record for record in records if str(record.get(field) or "") == expected]
    if len(matches) != 1:
        raise ResolutionError(
            code,
            f"{field}={expected} 的匹配数量不是 1。",
            {**details, "matchCount": len(matches)},
        )
    return matches[0]


def resolve_participant(
    snapshot: dict[str, Any],
    account_id: str,
    login_name: str,
) -> Participant:
    """在指定单位内按登录名唯一解析人员、部门和岗位。"""
    organization = get_account_organization(snapshot, account_id)
    members_body = organization.get("members")
    members = members_body.get("items") if isinstance(members_body, dict) else None
    if not isinstance(members, list):
        raise ResolutionError(
            "members_missing",
            "组织机构快照缺少人员列表。",
            {"accountId": account_id},
        )

    member = find_unique(
        [item for item in members if isinstance(item, dict)],
        "loginName",
        login_name,
        "member_not_unique",
        {"accountId": account_id, "loginName": login_name},
    )
    member_id = member.get("id")
    member_name = member.get("name")
    department_name = member.get("departmentName")
    post_name = member.get("postName")
    missing_member_fields = [
        field
        for field, value in {
            "id": member_id,
            "name": member_name,
            "departmentName": department_name,
            "postName": post_name,
        }.items()
        if value is None or str(value).strip() == ""
    ]
    if missing_member_fields:
        raise ResolutionError(
            "member_fields_missing",
            "人员记录缺少流程解析字段。",
            {"loginName": login_name, "missing": missing_member_fields},
        )

    departments_body = organization.get("departments")
    department_tree = (
        departments_body.get("departmentTree") if isinstance(departments_body, dict) else None
    )
    departments = collect_department_records(department_tree, account_id)
    department = find_unique(
        departments,
        "name",
        str(department_name),
        "department_not_unique",
        {"accountId": account_id, "loginName": login_name, "departmentName": department_name},
    )

    posts_body = organization.get("posts")
    raw_posts = posts_body.get("items") if isinstance(posts_body, dict) else None
    if not isinstance(raw_posts, list):
        raise ResolutionError(
            "posts_missing",
            "组织机构快照缺少岗位列表。",
            {"accountId": account_id},
        )
    posts = [
        item
        for item in raw_posts
        if isinstance(item, dict)
        and (item.get("orgAccountId") is None or str(item.get("orgAccountId")) == account_id)
    ]
    post = find_unique(
        posts,
        "name",
        str(post_name),
        "post_not_unique",
        {"accountId": account_id, "loginName": login_name, "postName": post_name},
    )

    return Participant(
        name=str(member_name),
        member_id=str(member_id),
        department_id=str(department["id"]),
        post_id=str(post["id"]),
        account_id=account_id,
        login_name=login_name,
    )


def resolve_participants(
    exact_values: list[dict[str, Any]],
    login_names: list[str],
    snapshot: Optional[dict[str, Any]],
    account_id: str,
) -> list[Participant]:
    """合并精确人员和登录名解析结果，精确输入优先。"""
    exact_participants = [participant_from_exact(value) for value in exact_values]
    exact_login_names = {
        participant.login_name
        for participant in exact_participants
        if participant.login_name is not None
    }
    unresolved_login_names = [name for name in login_names if name not in exact_login_names]
    if unresolved_login_names and snapshot is None:
        raise ResolutionError(
            "organization_snapshot_required",
            "使用登录名解析人员时必须提供组织机构快照。",
            {"loginNames": unresolved_login_names},
        )

    # 精确人员先加入结果，登录名模式只补充尚未显式提供的人员。
    resolved = list(exact_participants)
    for login_name in unresolved_login_names:
        resolved.append(resolve_participant(snapshot or {}, account_id, login_name))
    return resolved
