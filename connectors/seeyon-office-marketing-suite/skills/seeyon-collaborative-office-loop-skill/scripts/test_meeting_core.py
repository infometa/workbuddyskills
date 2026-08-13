#!/usr/bin/env python3
"""验证会议核心模型、载荷与响应解析。by AI.Coding"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from meeting_core import (  # noqa: E402
    MeetingEntity,
    MeetingError,
    build_conflict_payload,
    build_content_payload,
    build_meeting_info_payload,
    build_meeting_payload,
    parse_conflict_result,
    parse_content_save_result,
    parse_meeting_type,
    parse_meeting_send_result,
    parse_time_millis,
    to_meeting_attachment,
    validate_time_range,
)


class MeetingCoreTest(unittest.TestCase):
    """覆盖会议协议中可纯函数验证的关键规则。by AI.Coding"""

    def test_parse_text_time_in_shanghai(self) -> None:
        """文本时间应按 Asia/Shanghai 转为毫秒时间戳。"""
        self.assertEqual(1786429800000, parse_time_millis("2026-08-11 14:30"))

    def test_parse_millisecond_timestamp_and_validate_range(self) -> None:
        """毫秒值应保持不变且结束时间必须晚于开始时间。"""
        self.assertEqual(1786429800000, parse_time_millis("1786429800000"))
        validate_time_range(1786429800000, 1786433400000)
        with self.assertRaisesRegex(MeetingError, "结束时间"):
            validate_time_range(1786429800000, 1786429800000)

    def test_build_conflict_payload_preserves_role_duplicates(self) -> None:
        """冲突人员顺序应保留主持人、记录人和与会人角色重复。"""
        emcee = MeetingEntity("member", "-1", "主持人", "ducl")
        recorder = MeetingEntity("member", "-1", "记录人", "ducl")
        conferees = [MeetingEntity("department", "-2", "开发部", "开发部")]

        payload = build_conflict_payload(
            1786429800000,
            1786433400000,
            emcee,
            recorder,
            conferees,
        )

        self.assertEqual(
            "Member|-1,Member|-1,Department|-2",
            payload["otherID"],
        )
        self.assertEqual("meeting", payload["module"])

    def test_parse_default_meeting_type_from_meeting_info(self) -> None:
        """默认应从 meetingTypes 唯一选择名称为普通会议的分类。"""
        request_payload = build_meeting_info_payload()
        self.assertEqual({"meetingId": "", "templateId": ""}, request_payload)

        meeting_type = parse_meeting_type(
            {
                "meetingTypes": [
                    {"id": "2085071351685923001", "name": "普通会议", "type": 1},
                    {"id": "2085071351685923002", "name": "重要会议", "type": 2},
                ]
            }
        )

        self.assertEqual("2085071351685923001", meeting_type.meeting_type_id)
        self.assertEqual("普通会议", meeting_type.name)
        self.assertEqual("1", meeting_type.type_value)

    def test_meeting_type_must_match_uniquely(self) -> None:
        """分类列表无效、零匹配或多匹配都应失败。"""
        invalid_responses = (
            {},
            {"meetingTypes": "bad"},
            {"meetingTypes": [{"id": "2", "name": "重要会议", "type": 2}]},
            {
                "meetingTypes": [
                    {"id": "1", "name": "普通会议", "type": 1},
                    {"id": "2", "name": "普通会议", "type": 2},
                ]
            },
        )
        for response in invalid_responses:
            with self.subTest(response=response), self.assertRaises(MeetingError):
                parse_meeting_type(response)

    def test_build_content_payload_matches_meeting_contract(self) -> None:
        """正文载荷应使用会议模块类型并绑定临时会议 ID。"""
        payload = build_content_payload(
            "-8201595266208152362",
            "-2722680886302195637",
            "计划对称",
            "<p>对称下工作计划安排</p>",
        )

        body = payload["mainbodyDataDiv_0"]
        self.assertEqual("-1", body["id"])
        self.assertEqual("6", body["moduleType"])
        self.assertEqual("-8201595266208152362", body["moduleId"])
        self.assertEqual("10", body["contentType"])

    def test_convert_upload_attachment_to_meeting_attachment(self) -> None:
        """上传 att 应完整转换为 meetingAjaxManager 所需字段。"""
        attachment = to_meeting_attachment(
            {
                "id": None,
                "reference": "1",
                "subReference": "1",
                "category": 0,
                "type": 0,
                "filename": "报表excel.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "createdate": "2026-08-11 14:23:43",
                "size": "10169",
                "fileUrl": "9197788204910267317",
                "description": None,
            }
        )

        self.assertEqual("", attachment["attachment_id"])
        self.assertEqual("Att", attachment["attachment_subReference"])
        self.assertEqual("报表excel.xlsx", attachment["attachment_filename"])
        self.assertEqual("9197788204910267317", attachment["attachment_fileUrl"])
        self.assertEqual("false", attachment["attachment_needClone"])

    def test_build_meeting_payload_contains_defaults_and_entities(self) -> None:
        """最终载荷应包含默认会议字段、人员值和附件。"""
        payload = build_meeting_payload(
            meeting_temp_id="-8201595266208152362",
            title="计划对称",
            begin_date=1786429800000,
            end_date=1786433400000,
            emcee=MeetingEntity("member", "-1", "ducl", "ducl"),
            recorder=MeetingEntity("member", "-1", "ducl", "ducl"),
            conferees=[MeetingEntity("department", "-2", "开发部", "开发部")],
            imparts=[MeetingEntity("member", "-3", "李四", "lisi")],
            content="<p>对称下工作计划安排</p>",
            attachments=[{"attachment_fileUrl": "9197788204910267317"}],
            meeting_type_id="2085071351685923001",
            meeting_type_name="普通会议",
            meeting_type="1",
            meeting_place="会议室1303",
        )

        self.assertEqual("Member|-1", payload["emceeValue"])
        self.assertEqual("Department|-2", payload["conferees"])
        self.assertEqual("Member|-3", payload["impart"])
        self.assertEqual(10, payload["beforeTime"])
        self.assertEqual("2085071351685923001", payload["meetingTypeId"])
        self.assertEqual("无", payload["projectName"])
        self.assertEqual([], payload["selectedRoomApps"])

    def test_parse_three_endpoint_responses_strictly(self) -> None:
        """三个接口只在满足明确业务条件时返回成功模型。"""
        conflicts = [{"memberName": "ducl", "categoryName": "会议(主持人)"}]
        self.assertEqual(conflicts, parse_conflict_result(conflicts))
        content = parse_content_save_result(
            {
                "success": "true",
                "contentAll": {"id": "-9", "moduleId": "-8"},
            },
            "-8",
        )
        self.assertEqual("-9", content.content_id)
        send = parse_meeting_send_result({"roomAppState": 1, "id": "-8", "content": "<p>x</p>"})
        self.assertEqual("-8", send.meeting_id)

        invalid_values = ({}, "bad", {"data": []})
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(MeetingError):
                parse_conflict_result(value)
        with self.assertRaises(MeetingError):
            parse_content_save_result({"success": "true", "contentAll": {"id": "-9"}}, "-8")
        with self.assertRaises(MeetingError):
            parse_meeting_send_result({"roomAppState": 1, "id": ""})


if __name__ == "__main__":
    unittest.main()
