#!/usr/bin/env python3
"""Seeyon HTTP 公共模块测试。by AI.Coding"""

from __future__ import annotations

import io
import json
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import seeyon_http


class FakeResponse:
    """模拟 urllib 响应上下文。by AI.Coding"""

    def __init__(self, status: int, body: str) -> None:
        """保存测试响应状态和正文。"""
        self.status = status
        self.body = body.encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        """进入响应上下文。"""
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        """退出响应上下文且不吞掉异常。"""
        return False

    def read(self) -> bytes:
        """返回响应字节。"""
        return self.body

    def getcode(self) -> int:
        """返回 HTTP 状态码。"""
        return self.status


class FakeOpener:
    """记录 urllib 请求并返回预设响应。by AI.Coding"""

    def __init__(self, response: FakeResponse) -> None:
        """保存预设响应。"""
        self.response = response
        self.requests = []

    def open(self, request, timeout: int):
        """记录请求和超时时间。"""
        self.requests.append((request, timeout))
        return self.response


class SeeyonHttpTests(unittest.TestCase):
    """覆盖 Cookie 和三类 POST 请求。by AI.Coding"""

    def test_build_cookie_header_supports_optional_route(self) -> None:
        """验证 route 存在和缺失时的 Cookie。"""
        self.assertEqual(
            "JSESSIONID=session-1; route=route-1",
            seeyon_http.build_cookie_header("session-1", "route-1"),
        )
        self.assertEqual(
            "JSESSIONID=session-1",
            seeyon_http.build_cookie_header("session-1", None),
        )

    def test_post_form_encodes_utf8_fields(self) -> None:
        """验证表单请求方法、类型和中文编码。"""
        opener = FakeOpener(FakeResponse(200, '{"success":"true"}'))

        result = seeyon_http.post_form(
            opener,
            "http://localhost/seeyon/content.do",
            {"subject": "项目总结", "content": "正文"},
        )

        request, _ = opener.requests[0]
        form = urllib.parse.parse_qs(request.data.decode("utf-8"))
        self.assertEqual("POST", request.get_method())
        self.assertEqual(
            "application/x-www-form-urlencoded;charset=UTF-8",
            request.get_header("Content-type"),
        )
        self.assertEqual("项目总结", form["subject"][0])
        self.assertEqual({"success": "true"}, result.body)

    def test_post_json_serializes_unicode(self) -> None:
        """验证 JSON 请求保留业务中文内容。"""
        opener = FakeOpener(FakeResponse(200, '{"code":200}'))

        result = seeyon_http.post_json(
            opener,
            "http://localhost/seeyon/rest/send",
            {"subject": "项目总结"},
        )

        request, _ = opener.requests[0]
        self.assertEqual("application/json;charset=UTF-8", request.get_header("Content-type"))
        self.assertEqual("项目总结", json.loads(request.data.decode("utf-8"))["subject"])
        self.assertEqual(200, result.body["code"])

    def test_encode_multipart_contains_fields_and_file(self) -> None:
        """验证 multipart 包含上传字段和原始文件字节。"""
        body, content_type = seeyon_http.encode_multipart(
            fields={"fileSize": "4", "currentPageId": "123.456"},
            file_field="file",
            file_name="报告.md",
            file_bytes=b"test",
            mime_type="application/octet-stream",
            boundary="fixed-boundary",
        )

        self.assertEqual("multipart/form-data; boundary=fixed-boundary", content_type)
        self.assertIn(b'name="fileSize"', body)
        self.assertIn(b"123.456", body)
        self.assertIn('filename="报告.md"'.encode("utf-8"), body)
        self.assertIn(b"test", body)
        self.assertTrue(body.endswith(b"--fixed-boundary--\r\n"))

    def test_post_multipart_uses_supplied_content_type(self) -> None:
        """验证 multipart 请求不会重新编码请求体。"""
        opener = FakeOpener(FakeResponse(200, '{"status":200}'))
        content_type = "multipart/form-data; boundary=fixed-boundary"

        result = seeyon_http.post_multipart(
            opener,
            "http://localhost/seeyon/fileUpload.do",
            b"raw-body",
            content_type,
        )

        request, _ = opener.requests[0]
        self.assertEqual(content_type, request.get_header("Content-type"))
        self.assertEqual(b"raw-body", request.data)
        self.assertEqual(200, result.body["status"])

    def test_normalize_http_error_reads_response_preview(self) -> None:
        """验证 HTTPError 被转换为可诊断结构。"""
        error = urllib.error.HTTPError(
            url="http://localhost/seeyon/send",
            code=500,
            msg="error",
            hdrs=None,
            fp=io.BytesIO(b"boom"),
        )

        result = seeyon_http.normalize_http_error(error)

        self.assertEqual(500, result["status"])
        self.assertEqual("boom", result["body_preview"])


if __name__ == "__main__":
    unittest.main()
