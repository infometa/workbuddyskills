#!/usr/bin/env python3
"""附件上传模块单元测试。by AI.Coding"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seeyon_http import HttpResponse

import attachment_upload as upload

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "attachment.txt"


class AttachmentUploadTest(unittest.TestCase):
    """验证附件元数据、断点解析和批量上传门控。by AI.Coding"""

    def test_generate_current_page_id_uses_timestamp_prefix(self) -> None:
        """页面标识应使用毫秒时间戳和随机数字组成。"""
        value = upload.generate_current_page_id(now_ms=1786350903855)
        self.assertRegex(value, r"^1786350903855\.\d{16}$")

    def test_build_file_metadata_reads_file_properties(self) -> None:
        """文件元数据应包含文件名、总大小和毫秒修改时间。"""
        metadata = upload.build_file_metadata(FIXTURE_PATH)

        self.assertEqual(metadata.file_name, "attachment.txt")
        self.assertEqual(metadata.file_size, len(FIXTURE_PATH.read_bytes()))
        self.assertGreater(metadata.last_modified_ms, 0)
        self.assertEqual(metadata.mime_type, "text/plain")

    def test_build_file_metadata_rejects_missing_file(self) -> None:
        """不存在的附件必须在网络写操作前失败。"""
        with self.assertRaisesRegex(upload.AttachmentUploadError, "附件文件不存在"):
            upload.build_file_metadata(Path("missing-file.txt"))

    def test_parse_start_index_accepts_supported_shapes(self) -> None:
        """断点接口的明确数字形态均应被接受。"""
        self.assertEqual(upload.parse_start_index(0), 0)
        self.assertEqual(upload.parse_start_index("12"), 12)
        self.assertEqual(upload.parse_start_index({"startIndex": "7"}), 7)
        self.assertEqual(upload.parse_start_index({"data": 9}), 9)

    def test_parse_start_index_rejects_unknown_shape(self) -> None:
        """未知或负数断点不得静默降级为零。"""
        for value in (True, -1, "1.5", {"data": {}}, {"value": 0}):
            with self.subTest(value=value):
                with self.assertRaises(upload.AttachmentUploadError):
                    upload.parse_start_index(value)

    def test_query_start_index_posts_expected_form(self) -> None:
        """断点查询应发送 managerMethod 和二维 arguments。"""
        metadata = upload.FileMetadata(Path("a.md"), "a.md", 8, 1234, "text/markdown")
        with patch.object(upload, "post_form") as post_form:
            post_form.return_value = HttpResponse(200, "0", 0)
            result = upload.query_start_index(object(), "http://oa/seeyon/", metadata, "page-1")

        self.assertEqual(result, 0)
        _, url, fields = post_form.call_args.args
        self.assertEqual(url, "http://oa/seeyon/ajax.do?method=ajaxAction&managerName=fileManager")
        self.assertEqual(fields["managerMethod"], "getUploadFilesStartIndex")
        arguments = json.loads(fields["arguments"])
        self.assertEqual(arguments[1], "page-1")
        self.assertEqual(arguments[0][0]["fileName"], "a.md")
        self.assertTrue(arguments[0][0]["isEncrypt"])

    def test_upload_attachment_posts_remaining_bytes_and_returns_att(self) -> None:
        """附件上传应携带剩余字节、全部字段并返回 att。"""
        metadata = upload.build_file_metadata(FIXTURE_PATH)
        response_body = {"status": 200, "end": True, "att": {"fileUrl": "100", "filename": "attachment.txt"}}
        with (
            patch.object(upload, "encode_multipart", wraps=upload.encode_multipart) as encode,
            patch.object(upload, "post_multipart") as post_multipart,
        ):
            post_multipart.return_value = HttpResponse(200, json.dumps(response_body), response_body)
            att = upload.upload_attachment(object(), "http://oa/seeyon", metadata, "page-1", 2)

        self.assertEqual(att["fileUrl"], "100")
        fields = encode.call_args.args[0]
        self.assertEqual(fields["startIndex"], "2")
        self.assertEqual(fields["fileSize"], str(len(FIXTURE_PATH.read_bytes())))
        self.assertEqual(fields["secretLevel"], "undefined")
        self.assertEqual(encode.call_args.args[3], FIXTURE_PATH.read_bytes()[2:])

    def test_upload_attachment_rejects_incomplete_response(self) -> None:
        """服务端未确认上传结束或缺少 att 时应失败。"""
        metadata = upload.build_file_metadata(FIXTURE_PATH)
        with patch.object(upload, "post_multipart") as post_multipart:
            body = {"status": 200, "end": False, "att": {}}
            post_multipart.return_value = HttpResponse(200, json.dumps(body), body)
            with self.assertRaises(upload.AttachmentUploadError):
                upload.upload_attachment(object(), "http://oa/seeyon", metadata, "page", 0)

    def test_upload_attachments_empty_has_no_http_calls(self) -> None:
        """无附件时不应调用断点或上传接口。"""
        with (
            patch.object(upload, "query_start_index") as query,
            patch.object(upload, "upload_attachment") as upload_one,
        ):
            result = upload.upload_attachments(object(), "http://oa/seeyon", [], None)

        self.assertTrue(result.ok)
        self.assertEqual(result.attachments, [])
        query.assert_not_called()
        upload_one.assert_not_called()

    def test_upload_attachments_stops_after_partial_failure(self) -> None:
        """批量上传失败应返回已完成附件并停止后续文件。"""
        paths = [Path("a.txt"), Path("b.txt"), Path("c.txt")]
        metadata = [upload.FileMetadata(path, path.name, 1, 1, "text/plain") for path in paths]
        with (
            patch.object(upload, "build_file_metadata", side_effect=metadata),
            patch.object(upload, "query_start_index", side_effect=[0, 0]) as query,
            patch.object(
                upload,
                "upload_attachment",
                side_effect=[{"fileUrl": "1"}, upload.AttachmentUploadError("upload_failed", "失败")],
            ) as upload_one,
        ):
            result = upload.upload_attachments(object(), "http://oa/seeyon", paths, "fixed-page")

        self.assertFalse(result.ok)
        self.assertEqual(result.attachments, [{"fileUrl": "1"}])
        self.assertEqual(result.failed_file, "b.txt")
        self.assertEqual(result.current_page_id, "fixed-page")
        self.assertEqual(query.call_count, 2)
        self.assertEqual(upload_one.call_count, 2)


if __name__ == "__main__":
    unittest.main()
