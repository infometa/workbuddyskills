#!/usr/bin/env python3
"""统一认证上下文的离线单元测试。by AI.Coding"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import session_context


class FakeCookies:
    """模拟 requests CookieJar。by AI.Coding"""

    def __init__(self, values: dict[str, str]) -> None:
        """保存测试 Cookie。"""
        self.values = values

    def get(self, name: str, default: str | None = None) -> str | None:
        """按名称返回 Cookie。"""
        return self.values.get(name, default)


class FakeSession:
    """提供最小认证 Session 行为。by AI.Coding"""

    def __init__(self, cookies: dict[str, str]) -> None:
        """创建带 Cookie 的测试 Session。"""
        self.cookies = FakeCookies(cookies)


class SessionContextTests(unittest.TestCase):
    """验证服务地址推导和同一认证会话复用。by AI.Coding"""

    def test_derive_service_base_url_from_login_url(self) -> None:
        """登录地址应推导为 Seeyon 服务根地址。"""
        actual = session_context.derive_service_base_url(
            "https://oa.example.com/seeyon/main.do?method=login"
        )

        self.assertEqual("https://oa.example.com/seeyon", actual)

    def test_from_env_reuses_one_session_and_extracts_internal_cookies(self) -> None:
        """上下文应只获取一次 Session 并提取内部登录态。"""
        session = FakeSession({"JSESSIONID": "secret-session", "route": "node-a"})
        manager = Mock()
        manager.get_session.return_value = session
        factory = Mock(return_value=manager)
        environ = {
            "OA_BASE_URL": "http://oa.example.com/seeyon/main.do?method=login",
            "OA_AUTH_USERNAME": "ducl",
            "OA_AUTH_PASSWORD": "secret-password",
        }

        context = session_context.SessionContext.from_env(
            environ=environ,
            auth_manager_factory=factory,
        )

        self.assertIs(session, context.session)
        self.assertEqual("http://oa.example.com/seeyon", context.service_base_url)
        self.assertEqual("secret-session", context.session_id)
        self.assertEqual("node-a", context.route)
        self.assertEqual("ducl", context.username)
        factory.assert_called_once_with(environ)
        manager.get_session.assert_called_once_with()

    def test_base_url_override_is_normalized(self) -> None:
        """显式业务地址应覆盖登录地址推导结果。"""
        manager = Mock()
        manager.get_session.return_value = FakeSession({"JSESSIONID": "session"})

        context = session_context.SessionContext.from_env(
            base_url_override="http://172.31.15.158/seeyon/",
            environ={
                "OA_BASE_URL": "http://oa.example.com/main.do?method=login",
                "OA_AUTH_USERNAME": "ducl",
                "OA_AUTH_PASSWORD": "password",
            },
            auth_manager_factory=Mock(return_value=manager),
        )

        self.assertEqual("http://172.31.15.158/seeyon", context.service_base_url)
        self.assertIsNone(context.route)

    def test_missing_session_cookie_fails_without_exposing_credentials(self) -> None:
        """缺少 JSESSIONID 时应失败且错误不含密码。"""
        manager = Mock()
        manager.get_session.return_value = FakeSession({"route": "node-a"})

        with self.assertRaises(session_context.SessionContextError) as captured:
            session_context.SessionContext.from_env(
                environ={
                    "OA_BASE_URL": "http://oa.example.com/seeyon/main.do?method=login",
                    "OA_AUTH_USERNAME": "ducl",
                    "OA_AUTH_PASSWORD": "do-not-leak",
                },
                auth_manager_factory=Mock(return_value=manager),
            )

        self.assertNotIn("do-not-leak", str(captured.exception))

    def test_missing_environment_variables_reuse_connector_session(self) -> None:
        """缺少账号密码时应复用连接器浏览器会话。"""
        factory = Mock()
        loader = Mock(
            return_value={
                "serviceUrl": "http://oa.example.com/seeyon",
                "username": "browser-user",
                "JSESSIONID": "browser-session",
                "route": "node-b",
            }
        )

        context = session_context.SessionContext.from_env(
            environ={},
            auth_manager_factory=factory,
            connector_session_loader=loader,
        )

        self.assertEqual("http://oa.example.com/seeyon", context.service_base_url)
        self.assertEqual("browser-user", context.username)
        self.assertEqual("browser-session", context.session_id)
        self.assertEqual("node-b", context.route)
        factory.assert_not_called()
        loader.assert_called_once_with()

    def test_browser_session_error_does_not_expose_secret(self) -> None:
        """浏览器会话加载失败时不泄漏持久化秘密。"""
        loader = Mock(side_effect=RuntimeError("JSESSIONID=do-not-leak"))
        with self.assertRaises(session_context.SessionContextError) as captured:
            session_context.SessionContext.from_env(
                environ={},
                connector_session_loader=loader,
            )

        self.assertNotIn("do-not-leak", str(captured.exception))


if __name__ == "__main__":
    unittest.main()
