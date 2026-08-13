#!/usr/bin/env python3
"""Seeyon 组织机构查询单元测试。by AI.Coding"""

from __future__ import annotations

import io
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import query_organization


class QueryOrganizationTests(unittest.TestCase):
    """覆盖六类接口契约、分页、聚合和错误处理。by AI.Coding"""

    def test_cookie_uses_session_id_and_optional_route(self) -> None:
        """验证组织查询沿用 OA 会话 Cookie。"""
        self.assertEqual(
            "JSESSIONID=session-1; route=route-1",
            query_organization.build_cookie_header("session-1", "route-1"),
        )
        self.assertEqual(
            "JSESSIONID=session-1",
            query_organization.build_cookie_header("session-1", None),
        )

    def test_endpoint_urls_match_provided_contracts(self) -> None:
        """验证六类组织接口 URL 与抓包契约一致。"""
        expected = {
            "accounts": ("accountManager", "showAccounts"),
            "departments": ("departmentManager", None),
            "members": ("memberManager", "showByAccount"),
            "posts": ("postManager", "showPostList"),
            "roles": ("roleManager", "findRoles"),
            "job-levels": ("levelManager", "showLevelList"),
        }
        for entity, (manager, nn) in expected.items():
            with self.subTest(entity=entity):
                parsed = urllib.parse.urlparse(
                    query_organization.build_business_url("http://172.31.15.90/seeyon", entity)
                )
                query = urllib.parse.parse_qs(parsed.query)
                self.assertEqual("ajaxAction", query["method"][0])
                self.assertEqual(manager, query["managerName"][0])
                self.assertEqual(nn, query.get("nn", [None])[0])

    def test_argument_builders_match_examples(self) -> None:
        """验证各实体表单 arguments 的业务字段。"""
        self.assertEqual(
            [{"page": 1, "size": 20}, {}],
            query_organization.build_accounts_arguments(1, 20),
        )
        self.assertEqual(
            [{"accountId": "6701728939670654080"}],
            query_organization.build_departments_arguments("6701728939670654080"),
        )
        self.assertEqual(
            [
                {"page": 1, "size": 20},
                {
                    "advance_name": "",
                    "advance_loginName": "",
                    "advance_code": "",
                    "advance_enable": "true",
                    "accountId": "-1730833917365171641",
                    "searchType": "advance",
                    "newp": 1,
                },
            ],
            query_organization.build_members_arguments(1, 20, "-1730833917365171641"),
        )
        self.assertEqual(
            [{"page": 1, "size": 20}, {"accountId": "6701728939670654080"}],
            query_organization.build_posts_arguments(1, 20, "6701728939670654080"),
        )
        self.assertEqual(
            [
                {"page": 1, "size": 20},
                {"bond": 1, "accountId": "6701728939670654080", "newp": 1},
            ],
            query_organization.build_roles_arguments(1, 20, "6701728939670654080"),
        )
        self.assertEqual(
            [{"page": 1, "size": 20}, {"accountId": "6701728939670654080"}],
            query_organization.build_job_levels_arguments(1, 20, "6701728939670654080"),
        )

    def test_form_body_contains_manager_method_and_arguments(self) -> None:
        """验证表单编码包含 managerMethod 和 JSON arguments。"""
        body = query_organization.build_form_body(
            "showDepartmentTree", [{"accountId": "6701728939670654080"}]
        )
        form = urllib.parse.parse_qs(body.decode("utf-8"))
        self.assertEqual("showDepartmentTree", form["managerMethod"][0])
        self.assertEqual(
            '[{"accountId":"6701728939670654080"}]',
            form["arguments"][0],
        )

    def test_paginated_query_aggregates_pages(self) -> None:
        """验证分页接口会汇总所有页面。"""
        responses = [
            {
                "ok": True,
                "status": 200,
                "body": {"total": 3, "pages": 2, "data": [{"id": "1"}, {"id": "2"}]},
            },
            {
                "ok": True,
                "status": 200,
                "body": {"total": 3, "pages": 2, "data": [{"id": "3"}]},
            },
        ]
        with patch.object(query_organization, "request_entity", side_effect=responses) as mocked:
            result = query_organization.query_accounts(
                opener=object(),
                base_url="http://172.31.15.90/seeyon",
                page_size=2,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(["1", "2", "3"], [item["id"] for item in result["items"]])
        self.assertEqual(2, result["pagesFetched"])
        self.assertEqual(2, mocked.call_count)

    def test_department_query_preserves_tree(self) -> None:
        """验证部门查询保留服务端树结构。"""
        tree = [{"id": "d1", "name": "研发部", "children": []}]
        with patch.object(
            query_organization,
            "request_entity",
            return_value={"ok": True, "status": 200, "body": tree, "requestUrl": "url"},
        ):
            result = query_organization.query_departments(
                object(), "http://172.31.15.90/seeyon", "account-1"
            )

        self.assertTrue(result["ok"])
        self.assertEqual(tree, result["departmentTree"])

    def test_request_entity_handles_logout(self) -> None:
        """验证会话失效响应被明确识别。"""
        with patch.object(
            query_organization, "post_form", return_value=(200, "__LOGOUT", "__LOGOUT")
        ):
            result = query_organization.request_entity(
                object(),
                "http://172.31.15.90/seeyon",
                "accounts",
                query_organization.build_accounts_arguments(1, 20),
            )

        self.assertFalse(result["ok"])
        self.assertEqual("session_expired", result["failed_step"])

    def test_request_entity_handles_http_error(self) -> None:
        """验证 HTTP 错误保留状态和响应摘要。"""
        error = urllib.error.HTTPError(
            url="http://172.31.15.90/seeyon/ajax.do",
            code=500,
            msg="error",
            hdrs=None,
            fp=io.BytesIO(b"boom"),
        )
        with patch.object(query_organization, "post_form", side_effect=error):
            result = query_organization.request_entity(
                object(),
                "http://172.31.15.90/seeyon",
                "accounts",
                query_organization.build_accounts_arguments(1, 20),
            )

        self.assertFalse(result["ok"])
        self.assertEqual(500, result["error"]["status"])

    def test_extract_account_ids_supports_id_and_account_id(self) -> None:
        """验证单位 ID兼容 id 和 accountId 字段。"""
        self.assertEqual(
            ["1", "2"],
            query_organization.extract_account_ids(
                [{"id": 1}, {"accountId": "2"}, {"id": "1"}, {"name": "missing"}]
            ),
        )

    def test_query_all_uses_discovered_account_ids(self) -> None:
        """验证 all 模式按单位汇总全部组织实体。"""
        accounts = {"ok": True, "items": [{"id": "a1"}], "fetched": 1}
        success = {"ok": True}
        with (
            patch.object(query_organization, "query_accounts", return_value=accounts),
            patch.object(query_organization, "query_departments", return_value=success),
            patch.object(query_organization, "query_members", return_value=success),
            patch.object(query_organization, "query_posts", return_value=success),
            patch.object(query_organization, "query_roles", return_value=success),
            patch.object(query_organization, "query_job_levels", return_value=success),
        ):
            result = query_organization.query_all(
                object(), "http://172.31.15.90/seeyon", []
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(["a1"], result["accountIds"])
        self.assertIn("a1", result["organizations"])
        self.assertTrue(result["organizations"]["a1"]["jobLevels"]["ok"])

    def test_query_job_levels_uses_paginated_endpoint(self) -> None:
        """验证职务级别通过分页接口查询。"""
        with patch.object(
            query_organization,
            "query_paginated",
            return_value={"ok": True, "items": [{"id": "level-1"}]},
        ) as mocked:
            result = query_organization.query_job_levels(
                object(), "http://172.31.15.90/seeyon", "account-1"
            )

        self.assertTrue(result["ok"])
        self.assertEqual("account-1", result["accountId"])
        self.assertEqual("job-levels", mocked.call_args.args[2])

    def test_query_collaboration_snapshot_only_queries_required_entities(self) -> None:
        """验证自由协同快照只查询部门、人员和岗位。"""
        departments = {"ok": True, "departmentTree": [{"id": "d1"}]}
        members = {"ok": True, "items": [{"id": "m1"}]}
        posts = {"ok": True, "items": [{"id": "p1"}]}
        with (
            patch.object(query_organization, "query_departments", return_value=departments),
            patch.object(query_organization, "query_members", return_value=members),
            patch.object(query_organization, "query_posts", return_value=posts),
            patch.object(query_organization, "query_roles") as roles,
            patch.object(query_organization, "query_job_levels") as job_levels,
        ):
            result = query_organization.query_collaboration_snapshot(
                object(), "http://oa/seeyon", "account-1"
            )

        self.assertTrue(result["ok"])
        organization = result["organizations"]["account-1"]
        self.assertEqual(departments, organization["departments"])
        self.assertEqual(members, organization["members"])
        self.assertEqual(posts, organization["posts"])
        roles.assert_not_called()
        job_levels.assert_not_called()


if __name__ == "__main__":
    unittest.main()
