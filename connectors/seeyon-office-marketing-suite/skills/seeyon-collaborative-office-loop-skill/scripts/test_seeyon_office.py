#!/usr/bin/env python3
"""统一 Seeyon 协同办公 CLI 的离线单元测试。by AI.Coding"""

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

import seeyon_office


def fake_context() -> SimpleNamespace:
    """构造不包含真实凭据的统一测试上下文。"""
    return SimpleNamespace(
        session=object(),
        service_base_url="http://oa.example.com/seeyon",
        session_id="session-secret",
        route="route-secret",
        username="ducl",
    )


class SeeyonOfficeTests(unittest.TestCase):
    """验证五个子命令、直接写入、单会话和脱敏输出。by AI.Coding"""

    def test_parser_accepts_five_commands(self) -> None:
        """统一入口应注册五个独立子命令。"""
        parser = seeyon_office.build_parser()
        commands = [
            parser.parse_args(["meeting-list"]).command,
            parser.parse_args(["meeting-detail", "--meeting-id", "1"]).command,
            parser.parse_args(["organization", "accounts"]).command,
            parser.parse_args(
                [
                    "meeting-create",
                    "--account-id",
                    "a1",
                    "--title",
                    "主题",
                    "--content",
                    "<p>正文</p>",
                    "--begin-date",
                    "2026-08-11 14:30",
                    "--end-date",
                    "2026-08-11 15:30",
                    "--conferee",
                    "member:lisi",
                    "--dry-run",
                ]
            ).command,
            parser.parse_args(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "纪要",
                    "--content",
                    "<p>正文</p>",
                    "--recipient-login-name",
                    "lisi",
                    "--dry-run",
                ]
            ).command,
        ]

        self.assertEqual(
            [
                "meeting-list",
                "meeting-detail",
                "organization",
                "meeting-create",
                "collaboration-send",
            ],
            commands,
        )

    def test_write_commands_default_to_direct_execution(self) -> None:
        """未指定 dry-run 时，会议和协同命令应认证后直接执行写流程。"""
        context = fake_context()
        factory = Mock(return_value=context)
        with patch.object(
            seeyon_office.send_meeting,
            "send_meeting",
            return_value={"ok": True, "dryRun": False, "completedStages": ["sendMeeting"]},
        ) as meeting_sender, patch.object(
            seeyon_office.send_collaboration,
            "send_collaboration",
            return_value={"ok": True, "dryRun": False, "completedStages": ["sendCollaboration"]},
        ) as collaboration_sender, patch.object(
            seeyon_office.query_organization,
            "query_collaboration_snapshot",
            return_value={"ok": True, "complete": True, "organizations": {}},
        ):
            meeting_result = seeyon_office.dispatch(
                [
                    "meeting-create",
                    "--account-id",
                    "a1",
                    "--title",
                    "主题",
                    "--content",
                    "正文",
                    "--begin-date",
                    "2026-08-11 14:30",
                    "--end-date",
                    "2026-08-11 15:30",
                    "--conferee",
                    "member:lisi",
                ],
                context_factory=factory,
            )
            collaboration_result = seeyon_office.dispatch(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "纪要",
                    "--content",
                    "正文",
                    "--recipient-login-name",
                    "lisi",
                ],
                context_factory=factory,
            )

        self.assertTrue(meeting_result["ok"])
        self.assertTrue(collaboration_result["ok"])
        self.assertFalse(meeting_sender.call_args.args[0].dry_run)
        self.assertFalse(collaboration_sender.call_args.args[0].dry_run)
        self.assertEqual(2, factory.call_count)

    def test_removed_confirm_write_argument_is_rejected(self) -> None:
        """旧确认参数应作为未知参数在认证前拒绝。"""
        factory = Mock()
        result = seeyon_office.dispatch(
            [
                "meeting-create",
                "--account-id",
                "a1",
                "--title",
                "主题",
                "--content",
                "正文",
                "--begin-date",
                "2026-08-11 14:30",
                "--end-date",
                "2026-08-11 15:30",
                "--conferee",
                "member:lisi",
                "--confirm-write",
            ],
            context_factory=factory,
        )

        self.assertFalse(result["ok"])
        self.assertEqual("validate_args", result["failed_step"])
        factory.assert_not_called()

    def test_missing_business_input_rejects_before_authentication(self) -> None:
        """缺少接收人等必填业务参数时不得建立认证会话。"""
        factory = Mock()
        result = seeyon_office.dispatch(
            [
                "collaboration-send",
                "--account-id",
                "a1",
                "--subject",
                "纪要",
                "--content",
                "正文",
                "--dry-run",
            ],
            context_factory=factory,
        )

        self.assertFalse(result["ok"])
        self.assertEqual("validate_args", result["failed_step"])
        factory.assert_not_called()

    def test_meeting_list_reuses_context_session_once(self) -> None:
        """会议列表查询应只创建一次上下文并直接复用原 Session。"""
        context = fake_context()
        factory = Mock(return_value=context)
        with patch.object(
            seeyon_office.query_meetings,
            "query_meetings",
            return_value={"ok": True, "meetings": []},
        ) as query:
            result = seeyon_office.dispatch(["meeting-list", "--list-type", "send"], factory)

        self.assertTrue(result["ok"])
        self.assertEqual("meeting-list", result["command"])
        factory.assert_called_once_with(base_url_override=None)
        self.assertIs(context.session, query.call_args.kwargs["session"])
        self.assertEqual(context.service_base_url, query.call_args.kwargs["base_url"])

    def test_organization_dispatch_uses_internal_cookie_context(self) -> None:
        """组织查询应从统一上下文创建本地 opener。"""
        context = fake_context()
        opener = object()
        with patch.object(
            seeyon_office.query_organization,
            "build_opener",
            return_value=opener,
        ) as build_opener, patch.object(
            seeyon_office.query_organization,
            "query_accounts",
            return_value={"ok": True, "items": []},
        ) as query:
            result = seeyon_office.dispatch(
                ["organization", "accounts"],
                context_factory=Mock(return_value=context),
            )

        self.assertTrue(result["ok"])
        build_opener.assert_called_once_with(context.session_id, context.route)
        self.assertIs(opener, query.call_args.args[0])

    def test_meeting_create_injects_current_user_and_dry_run(self) -> None:
        """会议配置应使用认证账号并传递 dry-run。"""
        context = fake_context()
        with patch.object(
            seeyon_office.send_meeting,
            "send_meeting",
            return_value={"ok": True, "dryRun": True, "completedStages": []},
        ) as sender:
            result = seeyon_office.dispatch(
                [
                    "meeting-create",
                    "--account-id",
                    "a1",
                    "--title",
                    "主题",
                    "--content",
                    "<p>正文</p>",
                    "--begin-date",
                    "2026-08-11 14:30",
                    "--end-date",
                    "2026-08-11 15:30",
                    "--conferee",
                    "member:lisi",
                    "--dry-run",
                ],
                context_factory=Mock(return_value=context),
            )

        config = sender.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertEqual("ducl", config.current_username)
        self.assertTrue(config.dry_run)
        self.assertEqual("session-secret", config.session_id)

    def test_collaboration_defaults_sender_to_authenticated_username(self) -> None:
        """自由协同配置应默认使用认证账号作为发送人。"""
        context = fake_context()
        with patch.object(
            seeyon_office.send_collaboration,
            "send_collaboration",
            return_value={"ok": True, "dryRun": True, "completedStages": []},
        ) as sender, patch.object(
            seeyon_office.query_organization,
            "query_collaboration_snapshot",
            return_value={"ok": True, "complete": True, "organizations": {}},
        ):
            result = seeyon_office.dispatch(
                [
                    "collaboration-send",
                    "--account-id",
                    "a1",
                    "--subject",
                    "纪要",
                    "--content",
                    "<p>正文</p>",
                    "--recipient-login-name",
                    "lisi",
                    "--dry-run",
                ],
                context_factory=Mock(return_value=context),
            )

        config = sender.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertEqual("ducl", config.sender_login_name)
        self.assertTrue(config.dry_run)

    def test_sanitize_result_removes_nested_secrets(self) -> None:
        """递归脱敏不得保留认证键或 Cookie 字符串。"""
        result = seeyon_office.sanitize_result(
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
        self.assertEqual("[REDACTED]", result["password"])

    def test_main_outputs_one_json_document(self) -> None:
        """CLI 主函数应输出单个 JSON 文档和稳定退出码。"""
        expected = {"ok": True, "command": "meeting-list", "completedStages": []}
        with patch.object(seeyon_office, "dispatch", return_value=expected), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as stdout:
            exit_code = seeyon_office.main(["meeting-list"])

        self.assertEqual(0, exit_code)
        self.assertEqual(expected, json.loads(stdout.getvalue()))


if __name__ == "__main__":
    unittest.main()
