#!/usr/bin/env python3
"""统一 Seeyon 营销数据分析 CLI 的离线单元测试。by AI.Coding"""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import seeyon_marketing


def fake_context() -> SimpleNamespace:
    """构造不包含真实凭据的统一测试上下文。"""
    return SimpleNamespace(
        session=object(),
        service_base_url="http://oa.example.com/seeyon",
        session_id="session-secret",
        route="route-secret",
        username="ducl",
    )


class SeeyonMarketingTests(unittest.TestCase):
    """验证三个子命令、直接发送、单会话和脱敏输出。by AI.Coding"""

    def test_parser_accepts_three_commands(self) -> None:
        """统一入口应注册订单、组织和协同三个命令。"""
        parser = seeyon_marketing.build_parser()
        commands = [
            parser.parse_args(["order-query"]).command,
            parser.parse_args(["organization", "accounts"]).command,
            parser.parse_args(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "销售分析",
                    "--content",
                    "<p>正文</p>",
                    "--recipient-login-name",
                    "lisi",
                ]
            ).command,
        ]

        self.assertEqual(["order-query", "organization", "collaboration-send"], commands)

    def test_order_query_uses_one_authenticated_context(self) -> None:
        """订单查询应复用统一上下文中的服务地址和登录态。"""
        context = fake_context()
        factory = Mock(return_value=context)
        with patch.object(
            seeyon_marketing.query_sales_orders,
            "query_sales_orders",
            return_value={"ok": True, "orders": []},
        ) as query:
            result = seeyon_marketing.dispatch(
                ["order-query", "--report-name", "销售订单查询"],
                context_factory=factory,
            )

        self.assertTrue(result["ok"])
        self.assertEqual("order-query", result["command"])
        factory.assert_called_once_with(base_url_override=None)
        self.assertEqual(context.service_base_url, query.call_args.kwargs["base_url"])
        self.assertEqual(context.session_id, query.call_args.kwargs["session_id"])
        self.assertEqual(context.route, query.call_args.kwargs["route"])

    def test_organization_uses_internal_cookie_context(self) -> None:
        """组织查询应从统一上下文创建本地 opener。"""
        context = fake_context()
        opener = object()
        with patch.object(
            seeyon_marketing.query_organization,
            "build_opener",
            return_value=opener,
        ) as build_opener, patch.object(
            seeyon_marketing.query_organization,
            "query_accounts",
            return_value={"ok": True, "items": []},
        ) as query:
            result = seeyon_marketing.dispatch(
                ["organization", "accounts"],
                context_factory=Mock(return_value=context),
            )

        self.assertTrue(result["ok"])
        build_opener.assert_called_once_with(context.session_id, context.route)
        self.assertIs(opener, query.call_args.args[0])

    def test_collaboration_defaults_to_direct_send_and_authenticated_sender(self) -> None:
        """协同未指定 dry-run 时应直接发送并使用认证账号作为发送人。"""
        context = fake_context()
        factory = Mock(return_value=context)
        with patch.object(
            seeyon_marketing.send_collaboration,
            "send_collaboration",
            return_value={"ok": True, "dryRun": False, "completedStages": ["send_collaboration"]},
        ) as sender, patch.object(
            seeyon_marketing.query_organization,
            "query_collaboration_snapshot",
            return_value={"ok": True, "complete": True, "organizations": {}},
        ):
            result = seeyon_marketing.dispatch(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "销售分析",
                    "--content",
                    "<p>正文</p>",
                    "--recipient-login-name",
                    "lisi",
                ],
                context_factory=factory,
            )

        config = sender.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertFalse(config.dry_run)
        self.assertEqual("ducl", config.sender_login_name)
        factory.assert_called_once_with(base_url_override=None)

    def test_collaboration_dry_run_is_forwarded(self) -> None:
        """显式 dry-run 应传给协同业务模块。"""
        context = fake_context()
        with patch.object(
            seeyon_marketing.send_collaboration,
            "send_collaboration",
            return_value={"ok": True, "dryRun": True, "completedStages": []},
        ) as sender, patch.object(
            seeyon_marketing.query_organization,
            "query_collaboration_snapshot",
            return_value={"ok": True, "complete": True, "organizations": {}},
        ):
            result = seeyon_marketing.dispatch(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "销售分析",
                    "--content",
                    "<p>正文</p>",
                    "--recipient-login-name",
                    "lisi",
                    "--dry-run",
                ],
                context_factory=Mock(return_value=context),
            )

        self.assertTrue(result["ok"])
        self.assertTrue(sender.call_args.args[0].dry_run)

    def test_missing_collaboration_input_rejects_before_authentication(self) -> None:
        """缺少正文或接收人时不得创建认证上下文。"""
        factory = Mock()
        result = seeyon_marketing.dispatch(
            [
                "collaboration-send",
                "--account-id",
                "a1",
                "--subject",
                "销售分析",
                "--content",
                "正文",
            ],
            context_factory=factory,
        )

        self.assertFalse(result["ok"])
        self.assertEqual("validate_args", result["failed_step"])
        factory.assert_not_called()

    def test_removed_confirm_write_argument_is_rejected(self) -> None:
        """统一入口不应注册额外确认参数。"""
        factory = Mock()
        result = seeyon_marketing.dispatch(
            [
                "collaboration-send",
                "--account-id",
                "a1",
                "--subject",
                "销售分析",
                "--content",
                "正文",
                "--recipient-login-name",
                "lisi",
                "--confirm-write",
            ],
            context_factory=factory,
        )

        self.assertFalse(result["ok"])
        self.assertEqual("validate_args", result["failed_step"])
        factory.assert_not_called()

    def test_sanitize_result_removes_nested_secrets(self) -> None:
        """递归脱敏不得保留认证键或 Cookie 字符串。"""
        result = seeyon_marketing.sanitize_result(
            {
                "ok": False,
                "password": "pw",
                "nested": {
                    "JSESSIONID": "session-secret",
                    "message": "Cookie: JSESSIONID=session-secret; route=node-a",
                    "token": "bearer-secret",
                },
            }
        )
        encoded = json.dumps(result, ensure_ascii=False)

        self.assertNotIn("pw", encoded)
        self.assertNotIn("session-secret", encoded)
        self.assertNotIn("node-a", encoded)
        self.assertNotIn("bearer-secret", encoded)

    def test_main_outputs_one_json_document(self) -> None:
        """CLI 主函数应输出单个 JSON 文档和稳定退出码。"""
        expected = {"ok": True, "command": "order-query", "completedStages": ["query"]}
        with patch.object(seeyon_marketing, "dispatch", return_value=expected), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as stdout:
            exit_code = seeyon_marketing.main(["order-query"])

        self.assertEqual(0, exit_code)
        self.assertEqual(expected, json.loads(stdout.getvalue()))


if __name__ == "__main__":
    unittest.main()
