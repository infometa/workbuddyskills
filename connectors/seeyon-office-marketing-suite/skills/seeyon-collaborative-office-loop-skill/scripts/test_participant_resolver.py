#!/usr/bin/env python3
"""验证会议人员与部门解析规则。by AI.Coding"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from participant_resolver import (  # noqa: E402
    ParticipantResolutionError,
    requires_organization_snapshot,
    resolve_entity,
    resolve_entities,
    resolve_member,
)


def build_snapshot() -> dict:
    """构造包含同名人员/部门边界的最小组织快照。"""
    return {
        "organizations": {
            "6701728939670654080": {
                "members": {
                    "items": [
                        {"id": "-1", "loginName": "ducl", "name": "ducl"},
                        {"id": "-2", "loginName": "lisi", "name": "李四"},
                        {"id": "-3", "loginName": "研发部", "name": "同名人员"},
                    ]
                },
                "departments": {
                    "departmentTree": [
                        {
                            "v3xOrgDepartment": {
                                "id": "-10",
                                "name": "研发部",
                                "orgAccountId": "6701728939670654080",
                                "entityType": "Department",
                            }
                        },
                        {
                            "v3xOrgDepartment": {
                                "id": "-11",
                                "name": "测试部",
                                "orgAccountId": "6701728939670654080",
                                "entityType": "Department",
                            }
                        },
                    ]
                },
            }
        }
    }


class ParticipantResolverTest(unittest.TestCase):
    """覆盖直接值、强制类型、普通输入和唯一性约束。by AI.Coding"""

    def setUp(self) -> None:
        """为每个用例准备独立组织快照。"""
        self.snapshot = build_snapshot()
        self.account_id = "6701728939670654080"

    def test_direct_values_do_not_need_snapshot(self) -> None:
        """直接 Member/Department 值应跳过组织查询。"""
        self.assertFalse(requires_organization_snapshot(["Member|-1", "Department|-10"]))
        entities = resolve_entities(
            ["Member|-1", "Department|-10"],
            None,
            self.account_id,
        )
        self.assertEqual(["Member|-1", "Department|-10"], [item.value() for item in entities])

    def test_member_and_department_prefixes_resolve_uniquely(self) -> None:
        """显式前缀应只在目标实体类型中解析。"""
        member = resolve_entity("member:ducl", self.snapshot, self.account_id)
        department = resolve_entity("department:研发部", self.snapshot, self.account_id)
        self.assertEqual("Member|-1", member.value())
        self.assertEqual("Department|-10", department.value())

    def test_role_member_resolver_rejects_department(self) -> None:
        """主持人与记录人必须最终解析为人员。"""
        member = resolve_member("ducl", self.snapshot, self.account_id)
        self.assertEqual("Member|-1", member.value())
        with self.assertRaisesRegex(ParticipantResolutionError, "人员"):
            resolve_member("Department|-10", None, self.account_id)

    def test_plain_input_can_resolve_department(self) -> None:
        """普通输入仅命中部门时应解析为部门。"""
        department = resolve_entity("测试部", self.snapshot, self.account_id)
        self.assertEqual("Department|-11", department.value())

    def test_plain_input_ambiguous_between_member_and_department(self) -> None:
        """普通输入同时命中人员和部门时应拒绝猜测。"""
        with self.assertRaisesRegex(ParticipantResolutionError, "歧义"):
            resolve_entity("研发部", self.snapshot, self.account_id)

    def test_missing_or_duplicate_match_fails(self) -> None:
        """零匹配和同类型多匹配都应失败。"""
        with self.assertRaises(ParticipantResolutionError):
            resolve_entity("不存在", self.snapshot, self.account_id)

        self.snapshot["organizations"][self.account_id]["members"]["items"].append(
            {"id": "-4", "loginName": "ducl", "name": "重复人员"}
        )
        with self.assertRaises(ParticipantResolutionError):
            resolve_entity("member:ducl", self.snapshot, self.account_id)


if __name__ == "__main__":
    unittest.main()
