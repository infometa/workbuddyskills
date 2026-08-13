#!/usr/bin/env python3
"""自由协同流程与业务载荷核心模型。by AI.Coding"""

from __future__ import annotations

import secrets
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Optional


class CollaborationError(ValueError):
    """表示协同流程、载荷或业务响应不满足发送约束。by AI.Coding"""

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """保存稳定错误码、消息和诊断详情。"""
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化错误结构。"""
        return {
            "code": self.code,
            "message": str(self),
            "details": self.details,
        }


@dataclass(frozen=True)
class Participant:
    """表示可写入 Seeyon 工作流的人员。by AI.Coding"""

    name: str
    member_id: str
    department_id: str
    post_id: str
    account_id: str
    login_name: Optional[str] = None

    def workflow_value(self) -> str:
        """按 Seeyon 工作流约定组合部门、人员和岗位 ID。"""
        return f"{self.department_id}#{self.member_id}#{self.post_id}"

    def to_dict(self) -> dict[str, Any]:
        """转换为稳定的 JSON 输出结构。"""
        return {
            "name": self.name,
            "loginName": self.login_name,
            "memberId": self.member_id,
            "departmentId": self.department_id,
            "postId": self.post_id,
            "accountId": self.account_id,
            "workflowValue": self.workflow_value(),
        }


@dataclass(frozen=True)
class ContentSaveResult:
    """保存正文成功后的关联 ID。by AI.Coding"""

    ok: bool
    content_id: str
    summary_id: str


@dataclass(frozen=True)
class SendResult:
    """最终发送成功后的协同 ID。by AI.Coding"""

    ok: bool
    summary_id: str


class NodeIdGenerator:
    """为单个流程生成不重复的节点和连线 ID。by AI.Coding"""

    def __init__(self, seed: Optional[int] = None) -> None:
        """使用调用方种子或当前毫秒时间初始化序号。"""
        self.seed = seed if seed is not None else int(time.time() * 1000)
        self.counter = 0

    def next_id(self) -> str:
        """返回基于同一时间种子递增的字符串 ID。"""
        self.counter += 1
        return f"{self.seed}{self.counter:02d}"


def generate_negative_id() -> str:
    """生成位于 Java signed long 正数范围内的负数字符串 ID。"""
    return f"-{secrets.randbelow(9223372036854775806) + 1}"


def participant_value(participant: Participant) -> str:
    """返回 Seeyon 人员节点要求的部门、人员和岗位组合值。"""
    return participant.workflow_value()


def step_attributes(join_mode: str, name: str = "", description: str = "") -> dict[str, str]:
    """构造用户样例中流程步骤节点的公共属性。"""
    return {
        "i": "collaboration" if name else "",
        "n": name,
        "d": "",
        "t": "17",
        "l": "",
        "q": "",
        "p": "",
        "o": "",
        "u": "-1",
        "h": "-1",
        "v": "-1",
        "rs": "",
        "mu": "1",
        "w": "-1",
        "na": "-1",
        "nai": "",
        "nan": "",
        "na_b": "0",
        "na_i": "0",
        "k": "",
        "cy": "",
        "g": "0",
        "j": join_mode,
        "f": "",
        "fv": "",
        "FR": "",
        "DR": "",
        "s": "success",
        "m": "false",
        "ca": "false",
        "c": "1",
        "b": "0",
        "a": "",
        "tm": "1",
        "qid": "",
        "sid": "",
        "sa": "0",
        "md": "",
        "st": "0",
        "lk": "0",
        "oe": "0",
        "ft": "0",
        "ftv": "100",
        "mr": "",
        "otmn": "",
        "dfex": "",
        "dfexn": "",
        "sat": "",
        "nad": "",
        "nadt": "",
        "cov": "",
        "ct": "",
        "ma": "",
        "mc": "",
        "micr": "",
        "cr": "",
        "org4s": "",
        "org4m": "",
        "ds": description,
        "fc": "",
    }


def add_actor(node: ET.Element, participant: Participant, start_node: bool = False) -> None:
    """向流程节点加入发送人或接收人的人员属性。"""
    ET.SubElement(
        node,
        "a",
        {
            "k": "" if start_node else "roleadmin",
            "c": "1",
            "j": "false",
            "i": "false",
            "f": participant.member_id if start_node else participant.workflow_value(),
            "g": "user",
            "h": "false",
            "d": participant.name,
            "l": "",
            "m": "",
            "b": "" if start_node else participant.account_id,
            "vj": "0",
            "deptId": "",
        },
    )


def add_line(parent: ET.Element, line_id: str, source: str, target: str) -> None:
    """向流程定义加入一条有向连线。"""
    ET.SubElement(
        parent,
        "l",
        {
            "i": line_id,
            "n": "",
            "t": "11",
            "d": "",
            "k": source,
            "j": target,
            "o": "",
            "h": "3",
            "m": "",
            "e": "",
            "b": "",
            "a": "",
            "c": "",
        },
    )


def build_parallel_process_xml(
    sender: Participant,
    recipients: list[Participant],
    id_seed: Optional[int] = None,
) -> str:
    """构造 start、split、并行人员、join、end 工作流 XML。"""
    if not recipients:
        raise CollaborationError("recipients_required", "至少需要一个接收人。")

    generator = NodeIdGenerator(id_seed)
    root = ET.Element("ps")
    process = ET.SubElement(
        root,
        "p",
        {"t": "p", "s": "false", "w": "false", "i": "", "n": "", "d": "", "u": ""},
    )

    start = ET.SubElement(
        process,
        "n",
        {
            "i": "start",
            "n": sender.name,
            "t": "8",
            "d": "",
            "x": "0",
            "y": "0.5",
            "q": "",
            "ncn": "",
            "ncn_i18n": "",
            "h": "",
            "g": "",
            "f": "",
            "b": "normal",
        },
    )
    add_actor(start, sender, start_node=True)
    ET.SubElement(start, "s", step_attributes("all"))

    end = ET.SubElement(
        process,
        "n",
        {"i": "end", "n": "end", "t": "4", "d": "", "x": "4", "y": "0.5", "q": ""},
    )
    ET.SubElement(end, "s", step_attributes("all"))

    split_id = generator.next_id()
    join_id = generator.next_id()
    split = ET.SubElement(
        process,
        "n",
        {
            "i": split_id,
            "n": "split",
            "t": "2",
            "d": "",
            "x": "1",
            "y": "0.5",
            "q": "",
            "p": "true",
            "o": "",
        },
    )
    ET.SubElement(split, "s", step_attributes("single"))
    join = ET.SubElement(
        process,
        "n",
        {
            "i": join_id,
            "n": "join",
            "t": "2",
            "d": "",
            "x": "3",
            "y": "0.5",
            "q": "",
            "p": "false",
            "o": "",
        },
    )
    ET.SubElement(join, "s", step_attributes("single"))

    recipient_node_ids: list[str] = []
    for index, recipient in enumerate(recipients):
        node_id = generator.next_id()
        recipient_node_ids.append(node_id)
        node = ET.SubElement(
            process,
            "n",
            {
                "i": node_id,
                "n": recipient.name,
                "t": "6",
                "d": "",
                "x": "2",
                "y": str(index),
                "q": "",
                "ncn": "",
                "ncn_i18n": "",
                "h": "",
                "g": "",
                "f": "",
                "b": "normal",
                "e": "0",
                "l": "1000",
                "c": "1",
                "a": "",
                "rlhi": "",
                "olrt": "",
            },
        )
        add_actor(node, recipient)
        ET.SubElement(node, "s", step_attributes("single", "协同", "协同"))

    # 按固定拓扑生成连线，保证所有接收人都处于同一并行分支。
    add_line(process, generator.next_id(), "start", split_id)
    for node_id in recipient_node_ids:
        add_line(process, generator.next_id(), split_id, node_id)
        add_line(process, generator.next_id(), node_id, join_id)
    add_line(process, generator.next_id(), join_id, "end")
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def validate_raw_process_xml(process_xml: str) -> None:
    """校验原始流程 XML可解析且包含 start 和 end 节点。"""
    try:
        root = ET.fromstring(process_xml)
    except ET.ParseError as exc:
        raise CollaborationError(
            "raw_process_invalid_xml",
            "原始流程 XML无法解析。",
            {"reason": str(exc)},
        ) from exc
    missing = [
        node_id
        for node_id in ("start", "end")
        if root.find(f".//n[@i='{node_id}']") is None
    ]
    if missing:
        raise CollaborationError(
            "raw_process_nodes_missing",
            "原始流程 XML缺少必要节点。",
            {"missing": missing},
        )


def build_content_payload(
    summary_id: str,
    sender: Participant,
    subject: str,
    html_content: str,
) -> dict[str, Any]:
    """按 content.do 样例构造正文保存业务数据。"""
    return {
        "_currentDiv": {"_currentDiv": "0"},
        "secretLevelId": {"secretLevelId": ""},
        "mainbodyDataDiv_0": {
            "id": "",
            "createId": sender.member_id,
            "createDate": "",
            "modifyId": "",
            "modifyDate": "",
            "moduleType": "1",
            "moduleId": summary_id,
            "contentType": "10",
            "moduleTemplateId": "0",
            "contentTemplateId": "0",
            "sort": "0",
            "title": subject,
            "content": html_content,
            "rightId": "",
            "status": "STATUS_RESPONSE_NEW",
            "viewState": "1",
            "hasHtmlSignature": "0",
            "contentDataId": "",
            "properties": "",
        },
    }


def build_workflow_definition(process_xml: str) -> dict[str, Any]:
    """构造协同发送请求中的流程定义固定字段。"""
    return {
        "processDescBy": "",
        "caseId": "-1",
        "processId": "",
        "workflowNodeConditionInput": "",
        "workflowNodePeoplesInput": "",
        "processRuleContent": "",
        "workflowNewFlowInput": "",
        "moduleType": "1",
        "processSubsetting": "",
        "processInfoSelectvalue": "",
        "processInfo": "",
        "readyObjectJSON": "",
        "processXml": process_xml,
        "processChangeMessage": "",
        "processMessageData": "",
        "currentNodeId": "start",
        "subObjectId": "-1",
        "workflowThisNodeLastInput": "",
        "workflowLastInput": "",
        "dynamicFormMasterIds": "",
        "toReGo": "false",
        "processProperties": "",
        "processEvent": "",
        "newGenerateOtherNodeIds": "",
        "newGenerateNodeId": "",
        "workflowDataFlag": "WORKFLOW_SEEYON",
    }


def build_col_main_data(
    summary_id: str,
    content_id: str,
    subject: str,
    now_ms: int,
) -> dict[str, Any]:
    """构造自由协同主数据并保持正文关联 ID一致。"""
    return {
        "id": summary_id,
        "contentViewState": 1,
        "bodyType": "10",
        "createDate": now_ms,
        "trackType": "1",
        "trackMemberIds": "",
        "trackMemberNames": "",
        "hasTemplateColSubject": False,
        "resend": "false",
        "newBusiness": True,
        "isCap4Forward": "false",
        "isTransToColl": "0",
        "newFlowType": 0,
        "contentZwId": content_id,
        "contentIdUseDelete": "0",
        "canAddComment": "true",
        "mergeAttitude": "",
        "mergeContent": "",
        "isTemplateHasPigeonholePath": "false",
        "canForward": True,
        "canArchive": True,
        "canEditAttachment": True,
        "canEdit": True,
        "canModify": True,
        "canDeleteNode": False,
        "mergeContentLast": "1",
        "mergeContentNull": "",
        "mergeAttitudeLast": "2",
        "mergeAttitudeDefault": "1",
        "mergeAttitudeNull": "",
        "templateIsSystem": "false",
        "saveAsTempleteSubject": "",
        "useForSaveTemplate": "",
        "advanceRemind": "0",
        "importantLevel": "1",
        "subject": subject,
        "supervisorIds": "",
        "processTermType": "0",
        "processTermTypeCheck": False,
        "remindInterval": "0",
        "remindIntervalCheckBox": False,
        "canStartMerge": "",
        "canPreDealMerge": "",
        "canAnyDealMerge": "",
        "mergeIgnoreCommentRequired": "",
        "formViewOperation": "",
        "deadlineTemplate": "0",
        "templateBodyType": "10",
        "formRecordId": "",
        "contentSaveId": content_id,
        "contentRightId": "",
        "contentDataId": "",
        "contentTemplateId": "0",
    }


def build_workflow_context(
    sender: Participant,
    process_xml: str,
    request_token: str,
) -> dict[str, Any]:
    """构造最终发送所需的工作流运行上下文。"""
    return {
        "processId": "",
        "workitemId": "-1",
        "appName": "collaboration",
        "processXml": process_xml,
        "caseId": "-1",
        "activityId": "start",
        "currentActivityId": "start",
        "currentWorkitemId": "-1",
        "currentUserId": sender.member_id,
        "currentAccountId": sender.account_id,
        "processTemplateId": "-1",
        "matchRequestToken": request_token,
        "canBugReport": "false",
        "isValidate": "true",
        "changeMessageJSON": "",
        "messageDataListJSON": "",
        "readyObjectJson": "",
        "dynamicFormMasterIds": "",
        "toReGo": "",
        "currentNodeLast": "",
        "popNodeSubProcessJson": "",
        "selectedPeoplesOfNodes": "",
        "conditionsOfNodes": "",
        "newGenerateOtherNodeIds": "",
    }


def build_send_payload(
    summary_id: str,
    content_id: str,
    request_token: str,
    sender: Participant,
    recipients: list[Participant],
    subject: str,
    process_xml: str,
    attachments: list[dict[str, Any]],
    now_ms: int,
) -> dict[str, Any]:
    """按成功样例构造自由协同最终发送 JSON。"""
    if not recipients:
        raise CollaborationError("recipients_required", "至少需要一个接收人。")
    return {
        "collaborationParamData": {
            "commentDeal": {
                "moduleId": summary_id,
                "moduleType": 1,
                "pid": "0",
                "path": "",
                "ctype": -1,
                "content": "",
                "clevel": 1,
                "extAtt1": "",
                "attFileDomain": [],
            },
            "workflowDefinition": build_workflow_definition(process_xml),
            "assDocDomain": [],
            "attFileDomain": attachments,
            "colMainData": build_col_main_data(summary_id, content_id, subject, now_ms),
        },
        "workflowParamData": {
            "context": build_workflow_context(sender, process_xml, request_token),
            "cpMatchResult": {
                "allNotSelectNodes": [],
                "allSelectNodes": [],
                "allSelectInformNodes": [],
                "pop": "false",
                "token": "",
                "last": "false",
                "alreadyChecked": "false",
                "workflowPreCommitInfo": {},
            },
            "weekSubmit": False,
        },
        "otherParamData": {"from": ""},
        "thirdpartParamData": {"beforeEventBO": {}, "data": [], "thirdPartyContext": {}},
        "submitCode": "Send",
        "proofreadNextStep": False,
    }


def parse_content_save_result(
    response_body: Any,
    expected_summary_id: str,
) -> ContentSaveResult:
    """校验正文保存响应并提取服务端生成的正文 ID。"""
    if not isinstance(response_body, dict) or str(response_body.get("success")).lower() != "true":
        raise CollaborationError(
            "content_save_failed",
            "正文保存未明确成功。",
            {"response": response_body},
        )
    content_all = response_body.get("contentAll")
    if not isinstance(content_all, dict):
        raise CollaborationError("content_result_missing", "正文保存响应缺少 contentAll。")
    content_id = content_all.get("id")
    summary_id = content_all.get("moduleId")
    if not content_id:
        raise CollaborationError("content_id_missing", "正文保存响应缺少正文 ID。")
    if str(summary_id) != expected_summary_id:
        raise CollaborationError(
            "content_summary_mismatch",
            "正文保存响应的协同 ID与请求不一致。",
            {"expected": expected_summary_id, "actual": summary_id},
        )
    return ContentSaveResult(True, str(content_id), str(summary_id))


def parse_send_result(response_body: Any, expected_summary_id: str) -> SendResult:
    """校验最终发送业务结果并提取预期协同 ID。"""
    if not isinstance(response_body, dict) or str(response_body.get("code")) != "200":
        raise CollaborationError(
            "send_failed",
            "协同发送响应 code 不是 200。",
            {"response": response_body},
        )
    data = response_body.get("data")
    if not isinstance(data, dict) or data.get("passed") is not True:
        raise CollaborationError(
            "send_not_passed",
            "协同发送业务校验未通过。",
            {"response": response_body},
        )
    result_map = data.get("data")
    if not isinstance(result_map, dict):
        raise CollaborationError("send_summary_missing", "协同发送响应缺少结果集合。")

    # 响应键由服务端生成，只按值中的 summaryId 判断业务成功。
    summary_ids = [
        str(item.get("summaryId"))
        for item in result_map.values()
        if isinstance(item, dict) and item.get("summaryId") is not None
    ]
    if expected_summary_id not in summary_ids:
        raise CollaborationError(
            "send_summary_missing",
            "协同发送响应未返回预期协同 ID。",
            {"expected": expected_summary_id, "actual": summary_ids},
        )
    return SendResult(True, expected_summary_id)
