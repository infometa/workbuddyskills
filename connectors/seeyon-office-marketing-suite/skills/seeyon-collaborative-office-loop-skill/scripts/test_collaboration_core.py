#!/usr/bin/env python3
"""自由协同流程和载荷核心测试。by AI.Coding"""

from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collaboration_core


def participant(
    name: str,
    member_id: str,
    department_id: str = "department-1",
    post_id: str = "post-1",
    account_id: str = "account-1",
) -> collaboration_core.Participant:
    """构造流程测试参与人。"""
    return collaboration_core.Participant(
        name=name,
        member_id=member_id,
        department_id=department_id,
        post_id=post_id,
        account_id=account_id,
        login_name=name,
    )


class CollaborationCoreTests(unittest.TestCase):
    """覆盖 ID、XML、正文和发送业务载荷。by AI.Coding"""

    def test_generate_negative_id_returns_signed_long_text(self) -> None:
        """验证生成 ID为非零负整数字符串。"""
        value = collaboration_core.generate_negative_id()

        self.assertTrue(value.startswith("-"))
        self.assertLess(int(value), 0)
        self.assertLessEqual(abs(int(value)), 9223372036854775807)

    def test_build_parallel_process_xml_contains_all_branches(self) -> None:
        """验证双接收人的 split/join 并行流程。"""
        sender = participant("发起人", "sender-1")
        recipients = [
            participant("王二", "member-1", "department-1", "post-1"),
            participant('李四 & "审批"', "member-2", "department-2", "post-2"),
        ]

        process_xml = collaboration_core.build_parallel_process_xml(
            sender,
            recipients,
            id_seed=1786350516606,
        )
        root = ET.fromstring(process_xml)
        nodes = root.findall(".//n")
        lines = root.findall(".//l")

        self.assertIsNotNone(root.find(".//n[@i='start']"))
        self.assertIsNotNone(root.find(".//n[@i='end']"))
        self.assertEqual(6, len(nodes))
        self.assertEqual(6, len(lines))
        recipient_values = {
            element.get("f")
            for element in root.findall(".//n[@t='6']/a")
        }
        self.assertEqual(
            {"department-1#member-1#post-1", "department-2#member-2#post-2"},
            recipient_values,
        )
        self.assertEqual('李四 & "审批"', root.findall(".//n[@t='6']")[1].get("n"))

    def test_build_parallel_process_xml_rejects_empty_recipients(self) -> None:
        """验证没有接收人时拒绝生成流程。"""
        with self.assertRaises(collaboration_core.CollaborationError) as context:
            collaboration_core.build_parallel_process_xml(participant("发起人", "sender-1"), [])

        self.assertEqual("recipients_required", context.exception.code)

    def test_validate_raw_process_xml_requires_start_and_end(self) -> None:
        """验证原始 XML必须包含必要节点。"""
        valid = '<ps><p><n i="start"/><n i="end"/></p></ps>'
        collaboration_core.validate_raw_process_xml(valid)

        with self.assertRaises(collaboration_core.CollaborationError) as context:
            collaboration_core.validate_raw_process_xml('<ps><p><n i="start"/></p></ps>')

        self.assertEqual("raw_process_nodes_missing", context.exception.code)

    def test_build_content_payload_uses_sender_summary_and_body(self) -> None:
        """验证正文保存载荷关联发起人和协同 ID。"""
        result = collaboration_core.build_content_payload(
            summary_id="summary-1",
            sender=participant("发起人", "sender-1"),
            subject="项目总结",
            html_content="<p>干得漂亮</p>",
        )

        body = result["mainbodyDataDiv_0"]
        self.assertEqual("summary-1", body["moduleId"])
        self.assertEqual("sender-1", body["createId"])
        self.assertEqual("项目总结", body["title"])
        self.assertEqual("<p>干得漂亮</p>", body["content"])
        self.assertEqual("", body["id"])

    def test_parse_content_save_result_requires_success_and_matching_summary(self) -> None:
        """验证正文响应成功条件和协同 ID一致性。"""
        result = collaboration_core.parse_content_save_result(
            {
                "success": "true",
                "contentAll": {"id": "content-1", "moduleId": "summary-1"},
            },
            "summary-1",
        )

        self.assertTrue(result.ok)
        self.assertEqual("content-1", result.content_id)

        with self.assertRaises(collaboration_core.CollaborationError) as context:
            collaboration_core.parse_content_save_result(
                {
                    "success": "true",
                    "contentAll": {"id": "content-1", "moduleId": "other-summary"},
                },
                "summary-1",
            )
        self.assertEqual("content_summary_mismatch", context.exception.code)

    def test_build_send_payload_keeps_ids_xml_and_attachments_consistent(self) -> None:
        """验证最终发送载荷的关键关联字段。"""
        sender = participant("发起人", "sender-1")
        recipients = [participant("李四", "member-1")]
        process_xml = collaboration_core.build_parallel_process_xml(
            sender, recipients, id_seed=1786350516606
        )
        attachments = [{"fileUrl": "file-1", "filename": "报告.md"}]

        result = collaboration_core.build_send_payload(
            summary_id="summary-1",
            content_id="content-1",
            request_token="token-1",
            sender=sender,
            recipients=recipients,
            subject="项目总结",
            process_xml=process_xml,
            attachments=attachments,
            now_ms=1786350575834,
        )

        collaboration = result["collaborationParamData"]
        context = result["workflowParamData"]["context"]
        self.assertEqual("summary-1", collaboration["commentDeal"]["moduleId"])
        self.assertEqual("summary-1", collaboration["colMainData"]["id"])
        self.assertEqual("content-1", collaboration["colMainData"]["contentZwId"])
        self.assertEqual("content-1", collaboration["colMainData"]["contentSaveId"])
        self.assertEqual(process_xml, collaboration["workflowDefinition"]["processXml"])
        self.assertEqual(process_xml, context["processXml"])
        self.assertEqual("sender-1", context["currentUserId"])
        self.assertEqual("account-1", context["currentAccountId"])
        self.assertEqual("token-1", context["matchRequestToken"])
        self.assertEqual(attachments, collaboration["attFileDomain"])

    def test_parse_send_result_requires_passed_and_summary_id(self) -> None:
        """验证最终响应必须业务通过且返回预期协同 ID。"""
        result = collaboration_core.parse_send_result(
            {
                "message": "",
                "code": 200,
                "data": {
                    "passed": True,
                    "data": {"1": {"summaryId": "summary-1"}},
                },
            },
            "summary-1",
        )

        self.assertTrue(result.ok)
        self.assertEqual("summary-1", result.summary_id)

        with self.assertRaises(collaboration_core.CollaborationError) as context:
            collaboration_core.parse_send_result(
                {"code": 200, "data": {"passed": True, "data": {}}},
                "summary-1",
            )
        self.assertEqual("send_summary_missing", context.exception.code)


if __name__ == "__main__":
    unittest.main()
