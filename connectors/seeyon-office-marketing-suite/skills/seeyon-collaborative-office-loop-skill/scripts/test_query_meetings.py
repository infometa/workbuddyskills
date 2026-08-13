#!/usr/bin/env python3
"""Seeyon 会议查询单元测试。by AI.Coding"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
import urllib.parse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import query_meetings


class QueryMeetingsTests(unittest.TestCase):
    """覆盖会议查询参数组装和主流程。"""

    def make_http_error(self, code: int, body: str) -> query_meetings.HttpStatusError:
        """构造可复用的 HTTP 状态错误。"""
        return query_meetings.HttpStatusError(code, "error", body)

    def test_build_meeting_arguments_supports_title_dates_and_done(self) -> None:
        """会议参数应包含标题、时间和已开列表类型。"""
        result = query_meetings.build_meeting_arguments(
            title="1",
            begin_date="2026-04-14 20:15",
            end_date="2026-04-14 21:15",
            list_type="done",
            page=1,
            size=50,
        )

        self.assertEqual(
            [
                {"page": 1, "size": 50},
                {
                    "listType": "done",
                    "title": "1",
                    "beginDate": "2026-04-14 20:15",
                    "endDate": "2026-04-14 21:15",
                },
            ],
            result,
        )

    def test_normalize_list_type_supports_chinese_alias(self) -> None:
        """列表类型应支持中文别名。"""
        self.assertEqual("send", query_meetings.normalize_list_type("已发"))
        self.assertEqual("wait", query_meetings.normalize_list_type("待发"))

    def test_build_business_url_contains_encoded_filters(self) -> None:
        """会议列表 URL 应正确编码筛选条件。"""
        result = query_meetings.build_business_url(
            base_url="http://localhost/seeyon",
            title="1",
            begin_date="2026-04-14 20:15",
            end_date="2026-04-14 21:15",
            list_type="send",
            page=1,
            size=50,
        )

        parsed = urllib.parse.urlparse(result)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual("ajaxAction", query["method"][0])
        self.assertEqual("meetingAjaxManager", query["managerName"][0])
        self.assertEqual("findMeetingList", query["managerMethod"][0])
        arguments = query["arguments"][0]
        self.assertIn('"title":"1"', arguments)
        self.assertIn('"beginDate":"2026-04-14 20:15"', arguments)
        self.assertIn('"endDate":"2026-04-14 21:15"', arguments)
        self.assertIn('"listType":"send"', arguments)

    def test_build_meeting_detail_url_contains_meeting_id(self) -> None:
        """会议详情 URL 应包含 meetingId 和默认参数。"""
        result = query_meetings.build_meeting_detail_url(
            base_url="http://localhost/seeyon",
            meeting_id="4938207133842951073",
        )

        parsed = urllib.parse.urlparse(result)
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual("meetingAjaxManager", query["managerName"][0])
        self.assertEqual("meetingView", query["managerMethod"][0])
        arguments = query["arguments"][0]
        self.assertIn('"meetingId":"4938207133842951073"', arguments)
        self.assertIn('"proxyId":"-1"', arguments)

    def test_derive_service_base_url_from_oa_login_url(self) -> None:
        """登录地址应推导为业务服务根地址。"""
        result = query_meetings.derive_service_base_url(
            "https://oa.example.com:8443/seeyon/main.do?method=login"
        )

        self.assertEqual("https://oa.example.com:8443/seeyon", result)

    def test_get_json_reuses_authenticated_session(self) -> None:
        """JSON 请求应直接复用传入的认证 Session。"""
        response = Mock(status_code=200, reason="OK", text='{"success":true}')
        session = Mock()
        session.get.return_value = response

        status, _, body = query_meetings.get_json(
            session,
            "http://localhost/seeyon/ajax.do",
        )

        self.assertEqual(200, status)
        self.assertEqual({"success": True}, body)
        session.get.assert_called_once_with(
            "http://localhost/seeyon/ajax.do",
            headers={"Accept": "application/json,text/plain,*/*"},
            timeout=query_meetings.DEFAULT_TIMEOUT,
        )

    def test_get_json_preserves_route_cookie_from_authenticated_session(self) -> None:
        """请求过程不得清除 Session 中的路由 Cookie。"""
        response = Mock(status_code=200, reason="OK", text='{"success":true}')
        session = Mock()
        session.cookies = {"JSESSIONID": "jsid-1", "route": "route-1"}

        def get_with_route(url: str, **kwargs: object) -> Mock:
            """模拟请求并检查路由 Cookie 保持不变。"""
            self.assertEqual("route-1", session.cookies["route"])
            return response

        session.get.side_effect = get_with_route

        query_meetings.get_json(session, "http://localhost/seeyon/ajax.do")

        self.assertEqual("route-1", session.cookies["route"])
        self.assertEqual("jsid-1", session.cookies["JSESSIONID"])

    def test_query_meetings_rejects_invalid_list_type(self) -> None:
        """无效会议列表类型应在请求前失败。"""
        result = query_meetings.query_meetings(
            session=object(),
            base_url="http://localhost/seeyon",
            title="1",
            begin_date="2026-04-14 20:15",
            end_date="2026-04-14 21:15",
            list_type="xxx",
        )

        self.assertFalse(result["ok"])
        self.assertEqual("validate_args", result["failed_step"])

    def test_query_meetings_returns_query_result(self) -> None:
        """会议列表成功响应应转换为稳定结果。"""
        with patch.object(
            query_meetings,
            "get_json",
            return_value=(200, '{"total":1,"pages":1,"page":1,"data":[{"title":"1"}]}', {"total": 1, "pages": 1, "page": 1, "data": [{"title": "1"}]}),
        ):
            result = query_meetings.query_meetings(
                session=object(),
                base_url="http://localhost/seeyon",
                title="1",
                begin_date="2026-04-14 20:15",
                end_date="2026-04-14 21:15",
                list_type="send",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(1, result["total"])
        self.assertEqual("1", result["meetings"][0]["title"])
        self.assertNotIn("sessionId", result)
        self.assertNotIn("route", result)

    def test_query_meeting_detail_returns_detail_result(self) -> None:
        """会议详情成功响应应返回正文对象。"""
        with patch.object(
            query_meetings,
            "get_json",
            return_value=(200, '{"subject":"会议正文"}', {"subject": "会议正文"}),
        ):
            result = query_meetings.query_meeting_detail(
                session=object(),
                base_url="http://localhost/seeyon",
                meeting_id="4938207133842951073",
            )

        self.assertTrue(result["ok"])
        self.assertEqual("4938207133842951073", result["meetingId"])
        self.assertEqual("会议正文", result["meetingDetail"]["subject"])
        self.assertNotIn("sessionId", result)
        self.assertNotIn("route", result)

    def test_query_meetings_returns_http_error(self) -> None:
        """会议列表 HTTP 错误应返回结构化失败。"""
        with patch.object(query_meetings, "get_json", side_effect=self.make_http_error(500, "boom")):
            result = query_meetings.query_meetings(
                session=object(),
                base_url="http://localhost/seeyon",
                title="1",
                begin_date="2026-04-14 20:15",
                end_date="2026-04-14 21:15",
                list_type="done",
            )

        self.assertFalse(result["ok"])
        self.assertEqual("query_meetings", result["failed_step"])
        self.assertEqual(500, result["error"]["status"])

    def test_query_meeting_detail_returns_http_error(self) -> None:
        """会议详情 HTTP 错误应返回结构化失败。"""
        with patch.object(query_meetings, "get_json", side_effect=self.make_http_error(500, "boom")):
            result = query_meetings.query_meeting_detail(
                session=object(),
                base_url="http://localhost/seeyon",
                meeting_id="4938207133842951073",
            )

        self.assertFalse(result["ok"])
        self.assertEqual("query_meeting_detail", result["failed_step"])
        self.assertEqual(500, result["error"]["status"])

    def test_query_meetings_returns_transport_error(self) -> None:
        """网络异常应保留异常类别并返回失败。"""
        error = query_meetings.RequestTransportError("Timeout", "request timed out")
        with patch.object(query_meetings, "get_json", side_effect=error):
            result = query_meetings.query_meetings(
                session=object(),
                base_url="http://localhost/seeyon",
                title=None,
                begin_date=None,
                end_date=None,
                list_type="wait",
            )

        self.assertFalse(result["ok"])
        self.assertEqual("query_meetings", result["failed_step"])
        self.assertEqual("Timeout", result["error"]["category"])

    def test_main_uses_local_session_context(self) -> None:
        """独立脚本入口应使用本 Skill 内的认证上下文。"""
        authenticated_session = object()
        successful_output = {"ok": True, "meetings": []}
        with patch.object(sys, "argv", ["query_meetings.py"]), patch.dict(
            os.environ, {}, clear=True
        ), patch.object(
            query_meetings.SessionContext,
            "from_env",
            return_value=SimpleNamespace(
                session=authenticated_session,
                service_base_url="http://localhost/seeyon",
            ),
        ), patch.object(
            query_meetings,
            "query_meetings",
            return_value=successful_output,
        ) as query_mock, patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = query_meetings.main()

        output = json.loads(stdout.getvalue())
        self.assertEqual(0, exit_code)
        self.assertEqual(successful_output, output)
        query_mock.assert_called_once_with(
            session=authenticated_session,
            base_url="http://localhost/seeyon",
            title=None,
            begin_date=None,
            end_date=None,
            list_type="wait",
            page=1,
            size=50,
        )


if __name__ == "__main__":
    unittest.main()
