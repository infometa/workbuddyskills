#!/usr/bin/env python3
"""查询 Seeyon 会议列表和会议正文。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from typing import Any, Optional

from session_context import SessionContext, SessionContextError, derive_service_base_url

DEFAULT_TIMEOUT = 20
DEFAULT_LIST_TYPE = "wait"
DEFAULT_PAGE = 1
DEFAULT_SIZE = 50
LIST_TYPE_ALIASES = {
    "pending": "pending",
    "代开": "pending",
    "done": "done",
    "已开": "done",
    "send": "send",
    "已发": "send",
    "wait": "wait",
    "待发": "wait",
}
DEFAULT_MEETING_VIEW_ARGUMENTS = {
    "proxyId": "-1",
    "showTab": "true",
    "recommendMenuId": "5d8b50c0f3039d0d8ddb564cbb68ef1b",
    "menuSummary": "add",
    "portalId": "12345678910",
}


class HttpStatusError(RuntimeError):
    """认证 Session 收到 HTTP 失败状态时抛出。"""

    def __init__(self, status: int, reason: str, body: str):
        """保存 HTTP 状态和脱敏响应摘要。"""
        super().__init__(f"HTTP {status}: {reason}")
        self.status = status
        self.reason = reason
        self.body_preview = truncate(body)


class RequestTransportError(RuntimeError):
    """认证 Session 请求发生网络或客户端异常时抛出。"""

    def __init__(self, category: str, message: str):
        """保存网络异常类别和消息。"""
        super().__init__(message)
        self.category = category


def truncate(text: str, limit: int = 500) -> str:
    """截断过长文本，避免输出过大。"""
    return text if len(text) <= limit else text[:limit] + "..."


def http_error_payload(exc: HttpStatusError) -> dict[str, Any]:
    """把 HTTP 状态错误转换成统一的脱敏结构。"""
    return {
        "status": exc.status,
        "reason": exc.reason,
        "body_preview": exc.body_preview,
    }


def network_error_payload(exc: RequestTransportError) -> dict[str, Any]:
    """把认证 Session 的请求异常转换成统一的脱敏结构。"""
    return {
        "category": exc.category,
        "reason": truncate(str(exc)),
    }


def get_json(session: Any, url: str) -> tuple[int, str, Any]:
    """使用统一认证上下文的原始 Session 发送请求并保留 route Cookie。"""
    try:
        response = session.get(
            url,
            headers={"Accept": "application/json,text/plain,*/*"},
            timeout=DEFAULT_TIMEOUT,
        )
    except Exception as exc:
        raise RequestTransportError(type(exc).__name__, str(exc)) from exc

    text = str(getattr(response, "text", ""))
    status = int(getattr(response, "status_code", 0))
    if status >= 400:
        raise HttpStatusError(status, str(getattr(response, "reason", "")), text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = text
    return status, text, parsed


def normalize_list_type(list_type: str) -> str:
    """把 listType 规范化为 Seeyon 接口需要的值。"""
    normalized = LIST_TYPE_ALIASES.get(list_type)
    if normalized:
        return normalized
    raise ValueError(f"Unsupported listType: {list_type}")


def build_meeting_filters(
    title: Optional[str],
    begin_date: Optional[str],
    end_date: Optional[str],
    list_type: str,
) -> dict[str, Any]:
    """组装会议查询条件。"""
    filters: dict[str, Any] = {"listType": normalize_list_type(list_type)}
    if title:
        filters["title"] = title
    if begin_date:
        filters["beginDate"] = begin_date
    if end_date:
        filters["endDate"] = end_date
    return filters


def build_meeting_arguments(
    title: Optional[str],
    begin_date: Optional[str],
    end_date: Optional[str],
    list_type: str,
    page: int,
    size: int,
) -> list[dict[str, Any]]:
    """按 findMeetingList 接口要求组装 arguments 数组。"""
    return [
        {"page": page, "size": size},
        build_meeting_filters(title, begin_date, end_date, list_type),
    ]


def build_business_url(
    base_url: str,
    title: Optional[str],
    begin_date: Optional[str],
    end_date: Optional[str],
    list_type: str,
    page: int,
    size: int,
) -> str:
    """构造会议列表查询接口 URL。"""
    arguments = json.dumps(
        build_meeting_arguments(title, begin_date, end_date, list_type, page, size),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    query_string = urllib.parse.urlencode(
        {
            "method": "ajaxAction",
            "managerName": "meetingAjaxManager",
            "managerMethod": "findMeetingList",
            "arguments": arguments,
        }
    )
    return f"{base_url.rstrip('/')}/ajax.do?{query_string}"


def build_meeting_detail_arguments(
    meeting_id: str,
    proxy_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["proxyId"],
    show_tab: str = DEFAULT_MEETING_VIEW_ARGUMENTS["showTab"],
    recommend_menu_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["recommendMenuId"],
    menu_summary: str = DEFAULT_MEETING_VIEW_ARGUMENTS["menuSummary"],
    portal_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["portalId"],
) -> list[dict[str, str]]:
    """按 meetingView 接口要求组装 arguments 数组。"""
    return [
        {
            "meetingId": meeting_id,
            "proxyId": proxy_id,
            "showTab": show_tab,
            "recommendMenuId": recommend_menu_id,
            "menuSummary": menu_summary,
            "portalId": portal_id,
        }
    ]


def build_meeting_detail_url(
    base_url: str,
    meeting_id: str,
    proxy_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["proxyId"],
    show_tab: str = DEFAULT_MEETING_VIEW_ARGUMENTS["showTab"],
    recommend_menu_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["recommendMenuId"],
    menu_summary: str = DEFAULT_MEETING_VIEW_ARGUMENTS["menuSummary"],
    portal_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["portalId"],
) -> str:
    """构造会议正文查询接口 URL。"""
    arguments = json.dumps(
        build_meeting_detail_arguments(meeting_id, proxy_id, show_tab, recommend_menu_id, menu_summary, portal_id),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    query_string = urllib.parse.urlencode(
        {
            "method": "ajaxAction",
            "managerName": "meetingAjaxManager",
            "managerMethod": "meetingView",
            "arguments": arguments,
        }
    )
    return f"{base_url.rstrip('/')}/ajax.do?{query_string}"


def build_query_output(
    filters: dict[str, Any],
    status: int,
    text: str,
    body: Any,
) -> dict[str, Any]:
    """统一组装会议查询成功结果。"""
    output = {
        "ok": body != "__LOGOUT",
        "filters": filters,
        "business_response": {
            "status": status,
            "body": body,
            "body_preview": truncate(text),
        },
    }
    if isinstance(body, dict):
        output["meetings"] = body.get("data")
        output["total"] = body.get("total")
        output["page"] = body.get("page")
        output["pages"] = body.get("pages")
    return output


def build_detail_output(
    meeting_id: str,
    status: int,
    text: str,
    body: Any,
) -> dict[str, Any]:
    """统一组装会议正文查询成功结果。"""
    return {
        "ok": body != "__LOGOUT",
        "meetingId": meeting_id,
        "business_response": {
            "status": status,
            "body": body,
            "body_preview": truncate(text),
        },
        "meetingDetail": body,
    }


def query_meetings(
    session: Any,
    base_url: str,
    title: Optional[str],
    begin_date: Optional[str],
    end_date: Optional[str],
    list_type: str = DEFAULT_LIST_TYPE,
    page: int = DEFAULT_PAGE,
    size: int = DEFAULT_SIZE,
) -> dict[str, Any]:
    """复用统一认证 Session 调用会议列表查询接口。"""
    try:
        filters = build_meeting_filters(title, begin_date, end_date, list_type)
    except ValueError as exc:
        return {
            "ok": False,
            "failed_step": "validate_args",
            "error": str(exc),
        }

    business_url = build_business_url(base_url, title, begin_date, end_date, list_type, page, size)
    try:
        status, text, body = get_json(session, business_url)
    except HttpStatusError as exc:
        return {
            "ok": False,
            "failed_step": "query_meetings",
            "filters": {
                **filters,
                "page": page,
                "size": size,
            },
            "error": http_error_payload(exc),
        }
    except RequestTransportError as exc:
        return {
            "ok": False,
            "failed_step": "query_meetings",
            "filters": {
                **filters,
                "page": page,
                "size": size,
            },
            "error": network_error_payload(exc),
        }

    output = build_query_output(
        filters={
            **filters,
            "page": page,
            "size": size,
        },
        status=status,
        text=text,
        body=body,
    )
    output["request_url"] = business_url
    return output


def query_meeting_detail(
    session: Any,
    base_url: str,
    meeting_id: str,
    proxy_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["proxyId"],
    show_tab: str = DEFAULT_MEETING_VIEW_ARGUMENTS["showTab"],
    recommend_menu_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["recommendMenuId"],
    menu_summary: str = DEFAULT_MEETING_VIEW_ARGUMENTS["menuSummary"],
    portal_id: str = DEFAULT_MEETING_VIEW_ARGUMENTS["portalId"],
) -> dict[str, Any]:
    """使用 meetingId 查询会议正文/详情。"""
    detail_url = build_meeting_detail_url(
        base_url=base_url,
        meeting_id=meeting_id,
        proxy_id=proxy_id,
        show_tab=show_tab,
        recommend_menu_id=recommend_menu_id,
        menu_summary=menu_summary,
        portal_id=portal_id,
    )
    try:
        status, text, body = get_json(session, detail_url)
    except HttpStatusError as exc:
        return {
            "ok": False,
            "failed_step": "query_meeting_detail",
            "meetingId": meeting_id,
            "error": http_error_payload(exc),
        }
    except RequestTransportError as exc:
        return {
            "ok": False,
            "failed_step": "query_meeting_detail",
            "meetingId": meeting_id,
            "error": network_error_payload(exc),
        }

    output = build_detail_output(
        meeting_id=meeting_id,
        status=status,
        text=text,
        body=body,
    )
    output["request_url"] = detail_url
    return output


def main() -> int:
    """通过本 Skill 的统一认证上下文查询会议。"""
    parser = argparse.ArgumentParser(description="Query Seeyon meeting list or meeting detail")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OA_SERVICE_BASE_URL"),
        help="可选 Seeyon 服务根地址；默认从 OA_BASE_URL 推导",
    )
    parser.add_argument("--meeting-id", help="会议详情查询需要的 meetingId")
    parser.add_argument("--title", help="会议名称")
    parser.add_argument("--begin-date", help="会议开始时间，例如 2026-04-14 20:15")
    parser.add_argument("--end-date", help="会议结束时间，例如 2026-04-14 20:15")
    parser.add_argument("--list-type", default=DEFAULT_LIST_TYPE, help="支持 pending/done/send/wait，或 代开/已开/已发/待发")
    parser.add_argument("--page", type=int, default=DEFAULT_PAGE, help="页码，默认 1")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="每页条数，默认 50")
    parser.add_argument("--proxy-id", default=DEFAULT_MEETING_VIEW_ARGUMENTS["proxyId"], help="meetingView 参数，默认 -1")
    parser.add_argument("--show-tab", default=DEFAULT_MEETING_VIEW_ARGUMENTS["showTab"], help="meetingView 参数，默认 true")
    parser.add_argument("--recommend-menu-id", default=DEFAULT_MEETING_VIEW_ARGUMENTS["recommendMenuId"], help="meetingView 参数")
    parser.add_argument("--menu-summary", default=DEFAULT_MEETING_VIEW_ARGUMENTS["menuSummary"], help="meetingView 参数")
    parser.add_argument("--portal-id", default=DEFAULT_MEETING_VIEW_ARGUMENTS["portalId"], help="meetingView 参数")
    args = parser.parse_args()

    try:
        context = SessionContext.from_env(base_url_override=args.base_url)
    except SessionContextError as exc:
        json.dump(
            {
                "ok": False,
                "failed_step": "authenticate",
                "error": str(exc),
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1

    if args.meeting_id:
        output = query_meeting_detail(
            session=context.session,
            base_url=context.service_base_url,
            meeting_id=args.meeting_id,
            proxy_id=args.proxy_id,
            show_tab=args.show_tab,
            recommend_menu_id=args.recommend_menu_id,
            menu_summary=args.menu_summary,
            portal_id=args.portal_id,
        )
    else:
        output = query_meetings(
            session=context.session,
            base_url=context.service_base_url,
            title=args.title,
            begin_date=args.begin_date,
            end_date=args.end_date,
            list_type=args.list_type,
            page=args.page,
            size=args.size,
        )

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
