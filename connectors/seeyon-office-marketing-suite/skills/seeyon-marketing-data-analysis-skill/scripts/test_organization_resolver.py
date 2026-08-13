#!/usr/bin/env python3
"""自由协同组织人员解析测试。by AI.Coding"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import organization_resolver


def build_snapshot() -> dict:
    """构造包含人员、部门和岗位的最小组织快照。"""
    return {
        "organizations": {
            "account-1": {
                "members": {
                    "items": [
                        {
                            "id": "member-1",
                            "loginName": "lisi",
                            "name": "李四",
                            "departmentName": "开发部",
                            "postName": "dev",
                        }
                    ]
                },
                "departments": {
                    "departmentTree": [
                        {
                            "id": "department-1",
                            "name": "开发部",
                            "v3xOrgDepartment": {"orgAccountId": "account-1"},
                            "children": [
                                {
                                    "id": "department-child",
                                    "name": "开发一部",
                                    "v3xOrgDepartment": {"orgAccountId": "account-1"},
                                }
                            ],
                        }
                    ]
                },
                "posts": {
                    "items": [
                        {
                            "id": "post-1",
                            "name": "dev",
                            "orgAccountId": "account-1",
                        }
                    ]
                },
            }
        }
    }


class OrganizationResolverTests(unittest.TestCase):
    """覆盖精确人员与组织快照解析。by AI.Coding"""

    def test_load_organization_snapshot_reads_json(self) -> None:
        """验证组织快照从 UTF-8 JSON 文件读取。"""
        path = Path("organization.json")
        with patch.object(
            Path,
            "read_text",
            return_value=json.dumps(build_snapshot(), ensure_ascii=False),
        ):
            result = organization_resolver.load_organization_snapshot(path)

        self.assertIn("account-1", result["organizations"])

    def test_participant_from_exact_requires_all_ids(self) -> None:
        """验证精确人员字段完整时可直接转换。"""
        participant = organization_resolver.participant_from_exact(
            {
                "name": "李四",
                "loginName": "lisi",
                "memberId": "member-1",
                "departmentId": "department-1",
                "postId": "post-1",
                "accountId": "account-1",
            }
        )

        self.assertEqual("李四", participant.name)
        self.assertEqual("department-1#member-1#post-1", participant.workflow_value())

    def test_participant_from_exact_rejects_missing_field(self) -> None:
        """验证精确人员缺少岗位 ID时明确失败。"""
        with self.assertRaises(organization_resolver.ResolutionError) as context:
            organization_resolver.participant_from_exact(
                {
                    "name": "李四",
                    "memberId": "member-1",
                    "departmentId": "department-1",
                    "accountId": "account-1",
                }
            )

        self.assertEqual("invalid_exact_participant", context.exception.code)
        self.assertIn("postId", context.exception.details["missing"])

    def test_resolve_participant_matches_member_department_and_post(self) -> None:
        """验证登录名解析完整工作流人员数据。"""
        participant = organization_resolver.resolve_participant(
            build_snapshot(), "account-1", "lisi"
        )

        self.assertEqual("member-1", participant.member_id)
        self.assertEqual("department-1", participant.department_id)
        self.assertEqual("post-1", participant.post_id)
        self.assertEqual("account-1", participant.account_id)

    def test_resolve_participant_rejects_duplicate_login_name(self) -> None:
        """验证同单位重复登录名不会被猜测选择。"""
        snapshot = build_snapshot()
        snapshot["organizations"]["account-1"]["members"]["items"].append(
            {
                "id": "member-2",
                "loginName": "lisi",
                "name": "另一个李四",
                "departmentName": "开发部",
                "postName": "dev",
            }
        )

        with self.assertRaises(organization_resolver.ResolutionError) as context:
            organization_resolver.resolve_participant(snapshot, "account-1", "lisi")

        self.assertEqual("member_not_unique", context.exception.code)

    def test_resolve_participant_rejects_missing_department(self) -> None:
        """验证部门名称没有匹配时停止解析。"""
        snapshot = build_snapshot()
        snapshot["organizations"]["account-1"]["members"]["items"][0][
            "departmentName"
        ] = "不存在部门"

        with self.assertRaises(organization_resolver.ResolutionError) as context:
            organization_resolver.resolve_participant(snapshot, "account-1", "lisi")

        self.assertEqual("department_not_unique", context.exception.code)

    def test_resolve_participant_rejects_duplicate_post(self) -> None:
        """验证同名岗位多匹配时停止解析。"""
        snapshot = build_snapshot()
        snapshot["organizations"]["account-1"]["posts"]["items"].append(
            {"id": "post-2", "name": "dev", "orgAccountId": "account-1"}
        )

        with self.assertRaises(organization_resolver.ResolutionError) as context:
            organization_resolver.resolve_participant(snapshot, "account-1", "lisi")

        self.assertEqual("post_not_unique", context.exception.code)

    def test_resolve_participants_skips_login_already_supplied_exactly(self) -> None:
        """验证精确人员优先且不会被登录名解析重复覆盖。"""
        exact = {
            "name": "李四精确值",
            "loginName": "lisi",
            "memberId": "exact-member",
            "departmentId": "exact-department",
            "postId": "exact-post",
            "accountId": "account-1",
        }

        result = organization_resolver.resolve_participants(
            exact_values=[exact],
            login_names=["lisi"],
            snapshot=build_snapshot(),
            account_id="account-1",
        )

        self.assertEqual(1, len(result))
        self.assertEqual("exact-member", result[0].member_id)
        self.assertEqual("李四精确值", result[0].name)


if __name__ == "__main__":
    unittest.main()
