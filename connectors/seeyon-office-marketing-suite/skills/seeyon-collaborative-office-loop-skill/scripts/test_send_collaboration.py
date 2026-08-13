#!/usr/bin/env python3
"""自由协同发送编排与 CLI 单元测试。by AI.Coding"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from attachment_upload import UploadBatchResult

import send_collaboration as sender


FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "attachment.txt"


def exact(name: str, member_id: str) -> dict[str, str]:
    """构造完整精确人员输入。"""
    return {
        "name": name,
        "loginName": name.lower(),
        "memberId": member_id,
        "departmentId": f"dept-{member_id}",
        "postId": f"post-{member_id}",
        "accountId": "account-1",
    }


def config(**overrides) -> sender.CollaborationConfig:
    """构造最小有效发送配置。"""
    values = {
        "base_url": "http://oa/seeyon",
        "session_id": "session-1",
        "route": None,
        "subject": "项目总结",
        "html_content": "<p>干得漂亮</p>",
        "sender_exact": exact("Sender", "sender-1"),
        "sender_login_name": None,
        "recipient_exact_values": [exact("Receiver", "receiver-1")],
        "recipient_login_names": [],
        "account_id": "account-1",
        "organization_snapshot": None,
        "process_xml": None,
        "attachment_paths": [],
        "current_page_id": None,
        "dry_run": False,
    }
    values.update(overrides)
    return sender.CollaborationConfig(**values)


class FakeClient:
    """记录编排阶段调用并返回预设服务端响应。by AI.Coding"""

    def __init__(self) -> None:
        """初始化调用记录和默认成功响应。"""
        self.calls: list[str] = []
        self.upload_result = UploadBatchResult(True, [], current_page_id=None)
        self.content_response = {
            "success": "true",
            "contentAll": {"id": "content-1", "moduleId": None},
        }
        self.send_response = None

    def upload(self, paths: list[Path], current_page_id: str | None) -> UploadBatchResult:
        """记录附件阶段。"""
        self.calls.append("upload")
        return self.upload_result

    def save_content(self, payload: dict) -> dict:
        """记录正文保存并把动态协同 ID写入默认响应。"""
        self.calls.append("save_content")
        body = dict(self.content_response)
        if isinstance(body.get("contentAll"), dict):
            body["contentAll"] = dict(body["contentAll"])
            if body["contentAll"].get("moduleId") is None:
                body["contentAll"]["moduleId"] = payload["mainbodyDataDiv_0"]["moduleId"]
        return body

    def send(self, payload: dict) -> dict:
        """记录最终发送并返回包含动态协同 ID的默认响应。"""
        self.calls.append("send")
        if self.send_response is not None:
            return self.send_response
        summary_id = payload["collaborationParamData"]["colMainData"]["id"]
        return {"code": 200, "data": {"passed": True, "data": {"1": {"summaryId": summary_id}}}}


class SendFreeCollaborationTest(unittest.TestCase):
    """验证 dry-run、阶段门控和最终结果判定。by AI.Coding"""

    def test_dry_run_returns_payload_without_client_calls(self) -> None:
        """dry-run 应生成预览载荷且完全不执行外部写操作。"""
        client = FakeClient()
        result = sender.send_free_collaboration(
            config(dry_run=True, attachment_paths=[FIXTURE_PATH]),
            http_client=client,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["dryRun"])
        self.assertEqual(client.calls, [])
        self.assertEqual(result["flowMode"], "parallel")
        self.assertEqual(result["contentIdSource"], "save-response")
        self.assertEqual(
            result["payloadPreview"]["send"]["collaborationParamData"]["colMainData"]["contentSaveId"],
            sender.CONTENT_ID_PLACEHOLDER,
        )
        self.assertEqual(result["attachments"][0]["fileName"], "attachment.txt")

    def test_real_send_without_attachments_skips_upload(self) -> None:
        """无附件真实发送应只保存正文并最终发送。"""
        client = FakeClient()
        result = sender.send_free_collaboration(config(), http_client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(client.calls, ["save_content", "send"])
        self.assertEqual(result["contentId"], "content-1")
        self.assertEqual(result["summaryId"], result["sendResult"]["summaryId"])
        self.assertEqual(result["attachments"], [])

    def test_attachment_failure_stops_content_and_send(self) -> None:
        """附件部分失败后不得保存正文或发送协同。"""
        client = FakeClient()
        client.upload_result = UploadBatchResult(
            False,
            [{"fileUrl": "uploaded-1"}],
            failed_file="attachment.txt",
            error={"code": "upload_failed", "message": "失败", "details": {}},
            current_page_id="page-1",
        )
        result = sender.send_free_collaboration(
            config(attachment_paths=[FIXTURE_PATH]),
            http_client=client,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_step"], "upload_attachments")
        self.assertEqual(client.calls, ["upload"])
        self.assertEqual(result["attachments"], [{"fileUrl": "uploaded-1"}])

    def test_content_failure_stops_final_send(self) -> None:
        """正文响应未明确成功时不得调用最终发送。"""
        client = FakeClient()
        client.content_response = {"success": "false", "message": "保存失败"}
        result = sender.send_free_collaboration(config(), http_client=client)

        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_step"], "save_content")
        self.assertEqual(client.calls, ["save_content"])

    def test_send_missing_summary_keeps_saved_content_diagnostics(self) -> None:
        """最终响应缺少协同 ID时应保留已保存正文 ID并返回失败。"""
        client = FakeClient()
        client.send_response = {"code": 200, "data": {"passed": True, "data": {}}}
        result = sender.send_free_collaboration(config(), http_client=client)

        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_step"], "send_collaboration")
        self.assertEqual(result["contentId"], "content-1")
        self.assertIsNotNone(result["summaryId"])
        self.assertEqual(client.calls, ["save_content", "send"])

    def test_raw_xml_is_preserved_and_marked(self) -> None:
        """有效原始 XML应原样进入预览载荷并标记 raw-xml。"""
        process_xml = '<ps><p><n i="start"/><n i="end"/></p></ps>'
        result = sender.send_free_collaboration(config(dry_run=True, process_xml=process_xml))

        self.assertTrue(result["ok"])
        self.assertEqual(result["flowMode"], "raw-xml")
        self.assertEqual(
            result["payloadPreview"]["send"]["collaborationParamData"]["workflowDefinition"]["processXml"],
            process_xml,
        )

    def test_missing_session_fails_before_client_construction(self) -> None:
        """缺少登录态时必须在所有业务请求前失败。"""
        client = FakeClient()
        result = sender.send_free_collaboration(config(session_id=""), http_client=client)

        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_step"], "validate_input")
        self.assertEqual(client.calls, [])

    def test_config_defaults_sender_to_oa_authenticated_username(self) -> None:
        """未指定发送人时应使用 OA_AUTH_USERNAME。"""
        parser = sender.build_parser()
        with patch.dict(os.environ, {"OA_AUTH_USERNAME": "ducl"}, clear=False):
            args = parser.parse_args(
                [
                    "--subject",
                    "会议纪要",
                    "--content",
                    "<p>纪要</p>",
                    "--recipient-login-name",
                    "lisi",
                ]
            )
            actual = sender.config_from_args(args)

        self.assertEqual("ducl", actual.sender_login_name)


if __name__ == "__main__":
    unittest.main()
