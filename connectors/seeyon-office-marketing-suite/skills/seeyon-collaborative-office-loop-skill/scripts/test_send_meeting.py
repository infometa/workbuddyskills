#!/usr/bin/env python3
"""验证会议发送阶段门控、冲突处理与 dry-run。by AI.Coding"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from meeting_core import build_meeting_info_payload  # noqa: E402
from seeyon_http import HttpResponse  # noqa: E402
from send_meeting import MeetingConfig, MeetingHttpClient, send_meeting  # noqa: E402


class FakeMeetingClient:
    """记录各接口调用并返回测试配置的业务响应。by AI.Coding"""

    def __init__(self) -> None:
        """初始化默认成功响应和调用计数。"""
        self.calls = {
            "organization": 0,
            "meeting_info": 0,
            "conflict": 0,
            "upload": 0,
            "content": 0,
            "send": 0,
        }
        self.organization_response = {
            "organizations": {
                "6701728939670654080": {
                    "members": {
                        "items": [
                            {"id": "-1", "loginName": "ducl", "name": "ducl"},
                            {"id": "-2", "loginName": "lisi", "name": "李四"},
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
                            }
                        ]
                    },
                }
            }
        }
        self.conflict_response = []
        self.meeting_info_response = {
            "meetingTypes": [
                {"id": "2085071351685923001", "name": "普通会议", "type": 1},
                {"id": "2085071351685923002", "name": "重要会议", "type": 2},
            ]
        }
        self.upload_result = None
        self.content_response = None
        self.send_response = {"roomAppState": 1, "id": "-8201595266208152362", "content": "<p>x</p>"}
        self.last_send_payload = None

    def query_organization(self, account_id: str) -> dict:
        """返回预设组织快照。"""
        self.calls["organization"] += 1
        return self.organization_response

    def query_conflicts(self, payload: dict) -> object:
        """返回预设冲突结果。"""
        self.calls["conflict"] += 1
        return self.conflict_response

    def query_meeting_info(self, payload: dict) -> object:
        """返回预设会议初始化信息。"""
        self.calls["meeting_info"] += 1
        return self.meeting_info_response

    def upload(self, paths: list[Path], current_page_id: str | None):
        """返回预设上传结果。"""
        self.calls["upload"] += 1
        return self.upload_result

    def save_content(self, payload: dict) -> dict:
        """返回与载荷临时会议 ID关联的正文响应。"""
        self.calls["content"] += 1
        if self.content_response is not None:
            return self.content_response
        temp_id = payload["mainbodyDataDiv_0"]["moduleId"]
        return {"success": "true", "contentAll": {"id": "-9", "moduleId": temp_id}}

    def send(self, payload: dict) -> dict:
        """返回预设最终会议发送响应。"""
        self.calls["send"] += 1
        self.last_send_payload = payload
        return self.send_response


def base_config(**overrides) -> MeetingConfig:
    """创建使用直接组织值的默认会议配置。"""
    values = {
        "base_url": "http://172.31.15.158/seeyon",
        "session_id": "sid",
        "route": None,
        "account_id": "6701728939670654080",
        "current_username": "ducl",
        "title": "计划对称",
        "html_content": "<p>对称下工作计划安排</p>",
        "begin_date": "2026-08-11 14:30",
        "end_date": "2026-08-11 15:30",
        "emcee_input": "Member|-1",
        "recorder_input": "Member|-1",
        "conferee_inputs": ["Department|-10"],
        "impart_inputs": [],
        "meeting_place": "会议室1303",
        "attachment_paths": [],
        "current_page_id": None,
        "dry_run": False,
    }
    values.update(overrides)
    return MeetingConfig(**values)


class SendMeetingTest(unittest.TestCase):
    """覆盖会议发起编排的主要成功和失败路径。by AI.Coding"""

    def test_conflicts_are_returned_but_send_continues(self) -> None:
        """冲突数组非空时应展示详情并继续发送。"""
        client = FakeMeetingClient()
        client.conflict_response = [{"memberName": "ducl", "categoryName": "会议(主持人)"}]

        result = send_meeting(base_config(), client)

        self.assertTrue(result["ok"])
        self.assertTrue(result["hasConflicts"])
        self.assertEqual(client.conflict_response, result["conflicts"])
        self.assertEqual(0, client.calls["upload"])
        self.assertEqual(1, client.calls["content"])
        self.assertEqual(1, client.calls["send"])
        self.assertEqual("2085071351685923001", client.last_send_payload["meetingTypeId"])
        self.assertEqual("普通会议", client.last_send_payload["meetingTypeName"])
        self.assertEqual("1", client.last_send_payload["meetingType"])

    def test_meeting_info_http_contract(self) -> None:
        """分类查询应使用 meetingInfo 方法和空会议、模板 ID。"""
        client = MeetingHttpClient.__new__(MeetingHttpClient)
        client.base_url = "http://172.31.15.158/seeyon"
        client.opener = object()
        response = HttpResponse(200, '{"meetingTypes":[]}', {"meetingTypes": []})

        with patch("send_meeting.post_form", return_value=response) as mocked_post:
            result = client.query_meeting_info(build_meeting_info_payload())

        self.assertEqual({"meetingTypes": []}, result)
        _, url, fields = mocked_post.call_args.args
        self.assertIn("managerName=meetingAjaxManager", url)
        self.assertIn("nn=meetingInfo", url)
        self.assertEqual("meetingInfo", fields["managerMethod"])
        self.assertEqual(
            [{"meetingId": "", "templateId": ""}],
            json.loads(fields["arguments"]),
        )

    def test_invalid_meeting_info_stops_conflict_and_all_writes(self) -> None:
        """分类响应无效时不得查询冲突或执行任何写阶段。"""
        client = FakeMeetingClient()
        client.meeting_info_response = {
            "currentUser": {"sessionId": "SENSITIVE_SESSION"},
            "meetingTypes": [],
        }

        result = send_meeting(base_config(), client)

        self.assertFalse(result["ok"])
        self.assertEqual("query_meeting_info", result["failed_step"])
        self.assertEqual(1, client.calls["meeting_info"])
        self.assertEqual(0, client.calls["conflict"])
        self.assertEqual(0, client.calls["upload"])
        self.assertEqual(0, client.calls["content"])
        self.assertEqual(0, client.calls["send"])
        self.assertNotIn("SENSITIVE_SESSION", json.dumps(result, ensure_ascii=False))

    def test_invalid_conflict_response_stops_all_writes(self) -> None:
        """冲突响应非数组时不得上传、保存正文或发送会议。"""
        client = FakeMeetingClient()
        client.conflict_response = {"data": []}

        result = send_meeting(base_config(), client)

        self.assertFalse(result["ok"])
        self.assertEqual("query_conflicts", result["failed_step"])
        self.assertEqual(0, client.calls["upload"])
        self.assertEqual(0, client.calls["content"])
        self.assertEqual(0, client.calls["send"])

    def test_dry_run_queries_names_and_conflicts_without_writes(self) -> None:
        """dry-run 应解析组织并查询冲突，但不执行三个写阶段。"""
        client = FakeMeetingClient()
        config = base_config(
            emcee_input="Member|-2",
            recorder_input=None,
            conferee_inputs=["department:研发部", "member:lisi"],
            dry_run=True,
        )

        result = send_meeting(config, client)

        self.assertTrue(result["ok"])
        self.assertTrue(result["dryRun"])
        self.assertEqual(1, client.calls["organization"])
        self.assertEqual(1, client.calls["meeting_info"])
        self.assertEqual(1, client.calls["conflict"])
        self.assertEqual(0, client.calls["upload"])
        self.assertEqual(0, client.calls["content"])
        self.assertEqual(0, client.calls["send"])
        self.assertIn("sendMeeting", result["payloadPreview"])
        self.assertEqual("普通会议", result["meetingType"]["name"])
        self.assertEqual(
            "-1",
            result["payloadPreview"]["contentSave"]["mainbodyDataDiv_0"]["createId"],
        )

    def test_attachment_upload_failure_stops_content_and_send(self) -> None:
        """附件部分失败时应保留已上传项并停止后续阶段。"""
        from attachment_upload import UploadBatchResult

        client = FakeMeetingClient()
        client.upload_result = UploadBatchResult(
            False,
            [{"filename": "a.txt", "fileUrl": "1"}],
            failed_file="b.txt",
            error={"code": "upload_failed"},
            current_page_id="page",
        )
        path = Path(__file__).resolve().parents[1] / "fixtures" / "attachment.txt"
        result = send_meeting(base_config(attachment_paths=[path]), client)

        self.assertFalse(result["ok"])
        self.assertEqual("upload_attachments", result["failed_step"])
        self.assertEqual(1, client.calls["upload"])
        self.assertEqual(0, client.calls["content"])
        self.assertEqual(0, client.calls["send"])

    def test_content_failure_stops_final_send(self) -> None:
        """正文响应不明确成功时不得调用最终发送。"""
        client = FakeMeetingClient()
        client.content_response = {"success": "false"}

        result = send_meeting(base_config(), client)

        self.assertFalse(result["ok"])
        self.assertEqual("save_content", result["failed_step"])
        self.assertEqual(0, client.calls["send"])

    def test_missing_required_input_makes_zero_calls(self) -> None:
        """缺少会话或当前用户时所有接口调用应为零。"""
        client = FakeMeetingClient()

        result = send_meeting(base_config(session_id="", current_username=""), client)

        self.assertFalse(result["ok"])
        self.assertEqual("validate_input", result["failed_step"])
        self.assertEqual(0, sum(client.calls.values()))


if __name__ == "__main__":
    unittest.main()
