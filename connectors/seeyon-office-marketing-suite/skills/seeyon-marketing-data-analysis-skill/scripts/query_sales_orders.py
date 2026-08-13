#!/usr/bin/env python3
"""查询 Seeyon VReport 销售订单，并转换为字段显示名到显示值的结构。

作者：by AI.Coding
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

DEFAULT_TIMEOUT = 20
DEFAULT_REPORT_NAME = "销售订单查询"
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 100
DEFAULT_PLATFORM = "1"
REPORT_QUERY_VERSION = "1"


def truncate(text: str, limit: int = 500) -> str:
    """截断过长文本，避免错误输出携带完整报表数据。"""
    return text if len(text) <= limit else text[:limit] + "..."


def http_error_payload(exc: urllib.error.HTTPError) -> dict[str, Any]:
    """把 HTTPError 转换为统一错误结构。"""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return {
        "status": exc.code,
        "reason": exc.reason,
        "body_preview": truncate(body),
    }


def network_error_payload(exc: urllib.error.URLError) -> dict[str, Any]:
    """把网络连接错误转换为统一错误结构。"""
    return {
        "reason": str(exc.reason),
    }


def build_cookie_header(
    session_id: str, route: Optional[str], biz_id: Optional[str] = None
) -> str:
    """组装登录态 Cookie，并在已解析报表创建人后附加业务范围。"""
    cookies = [f"JSESSIONID={session_id}"]
    if route:
        cookies.append(f"route={route}")
    if biz_id:
        cookies.append(f"sw_scope={biz_id}")
    return "; ".join(cookies)


def build_opener(
    session_id: str, route: Optional[str], biz_id: Optional[str] = None
) -> urllib.request.OpenerDirector:
    """创建 HTTP opener；bizId 仅在查询具体报表时设置。"""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0"),
        ("Accept", "application/json,text/plain,*/*"),
        ("X-Requested-With", "XMLHttpRequest"),
        ("Cookie", build_cookie_header(session_id, route, biz_id)),
    ]
    # 报表列表尚未解析 createMember，不应提前猜测业务范围。
    if biz_id:
        opener.addheaders.append(("Sw-Scope", biz_id))
    return opener


def parse_response_text(text: str) -> Any:
    """优先把响应文本解析为 JSON，非 JSON 时保留原始文本。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def post_form(
    opener: urllib.request.OpenerDirector,
    url: str,
    form: dict[str, str],
    headers: Optional[dict[str, str]] = None,
) -> tuple[int, str, Any]:
    """发送表单 POST 请求并返回状态码、原始文本和解析结果。"""
    request_headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(form).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with opener.open(request, timeout=DEFAULT_TIMEOUT) as response:
        text = response.read().decode("utf-8", errors="replace")
        return response.getcode(), text, parse_response_text(text)


def post_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    body: dict[str, Any],
    headers: Optional[dict[str, str]] = None,
) -> tuple[int, str, Any]:
    """发送 JSON POST 请求并返回状态码、原始文本和解析结果。"""
    request_headers = {"Content-Type": "application/json; charset=UTF-8"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with opener.open(request, timeout=DEFAULT_TIMEOUT) as response:
        text = response.read().decode("utf-8", errors="replace")
        return response.getcode(), text, parse_response_text(text)


def build_origin(base_url: str) -> str:
    """从 Seeyon 基础地址提取 Origin。"""
    parsed = urllib.parse.urlsplit(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def build_report_list_url(base_url: str, rnd: str) -> str:
    """构造获取全部可访问报表的 AJAX 地址。"""
    query = urllib.parse.urlencode(
        {
            "method": "ajaxAction",
            "managerName": "vReportAjaxManager",
            "rnd": rnd,
        }
    )
    return f"{base_url.rstrip('/')}/ajax.do?{query}"


def build_report_list_form() -> dict[str, str]:
    """构造 getVReportViewData 所需的表单参数。"""
    arguments = json.dumps(
        [{"countData": True, "showDemoData": True, "categoryId": ""}],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "managerMethod": "getVReportViewData",
        "arguments": arguments,
    }


def find_first_report(response_body: Any, report_name: str) -> Optional[dict[str, Any]]:
    """按 reportMap 原始顺序查找第一个名称完全匹配的报表。"""
    if not isinstance(response_body, dict):
        return None
    response_data = response_body.get("data")
    if not isinstance(response_data, dict):
        return None
    report_map = response_data.get("reportMap")
    if not isinstance(report_map, dict):
        return None

    expected_name = report_name.strip()
    # Python 字典保留 JSON 对象解析后的响应顺序，因此直接遍历即可实现“同名取第一个”。
    for report in report_map.values():
        if isinstance(report, dict) and str(report.get("subject", "")).strip() == expected_name:
            return report
    return None


def build_report_query_url(base_url: str, biz_id: str, report_id: str) -> str:
    """构造 CAP4 销售订单报表查询地址。"""
    encoded_biz_id = urllib.parse.quote(str(biz_id), safe="")
    encoded_report_id = urllib.parse.quote(str(report_id), safe="")
    return (
        f"{base_url.rstrip('/')}/rest/cap4/report/"
        f"{encoded_biz_id}/query1/{encoded_report_id}/{REPORT_QUERY_VERSION}"
    )


def build_report_query_payload(biz_id: str, report_id: str, timestamp_ms: int) -> dict[str, Any]:
    """构造固定查询第一页、每页 100 条的报表请求体。"""
    timestamp_text = str(timestamp_ms)
    return {
        "platform": DEFAULT_PLATFORM,
        "op": "default",
        "queryParams": {
            "userConditions": [],
            "customOrderFields": [],
            "bizId": str(biz_id),
            "appId": str(report_id),
            "_t": timestamp_text,
            "isShowCondition": True,
            "hideToolbar": False,
            "schlogId": None,
            "preview": None,
            "conditionId": None,
            "addFrom": None,
            "templateId": None,
            "isMobile": False,
            "print": False,
            "bussId": str(biz_id),
            "platform": DEFAULT_PLATFORM,
        },
        "pagination": {
            "page": DEFAULT_PAGE,
            "pageSize": DEFAULT_PAGE_SIZE,
        },
        "enableConStyle": True,
    }


def extract_report_payload(response_body: Any) -> dict[str, Any]:
    """从 CAP4 REST 包装结构中提取实际报表数据。"""
    if not isinstance(response_body, dict):
        raise ValueError("报表接口未返回 JSON 对象")
    outer_code = response_body.get("code")
    if outer_code not in (None, 0, "0"):
        raise ValueError(f"报表接口返回失败 code={outer_code}")

    wrapper = response_body.get("data")
    if not isinstance(wrapper, dict):
        raise ValueError("报表接口响应缺少 data")
    if wrapper.get("success") is not True:
        error_message = wrapper.get("errorMsg") or "报表查询失败"
        raise ValueError(str(error_message))

    payload = wrapper.get("data")
    if not isinstance(payload, dict):
        raise ValueError("报表接口响应缺少实际报表数据")
    return payload


def resolve_field_display_name(field: Any, index: int) -> str:
    """按显示名优先级解析最终 JSON 字段名称。"""
    if not isinstance(field, dict):
        return str(index)
    display_field = field.get("displayField")
    if isinstance(display_field, dict):
        for key in ("aliasDisplayI18nName", "aliasDisplay"):
            value = display_field.get(key)
            if value is not None and str(value).strip():
                return str(value)
    for key in ("name", "key"):
        value = field.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return str(index)


def resolve_cell_display_value(cell: Any) -> Any:
    """读取报表单元格显示值，缺少 v 时回退到原始值 s。"""
    if not isinstance(cell, dict):
        return cell
    if "v" in cell:
        return cell.get("v")
    return cell.get("s")


def format_report_rows(report_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """把报表数字列索引转换为字段显示名到显示值的 Map 列表。"""
    fields = report_payload.get("fields")
    rows = report_payload.get("data")
    if not isinstance(fields, list):
        raise ValueError("报表数据缺少 fields 数组")
    if not isinstance(rows, list):
        raise ValueError("报表数据缺少 data 数组")

    formatted_rows: list[dict[str, Any]] = []
    # 严格按接口行顺序逐行转换，不做去重、分组、排序或数据修正。
    for row in rows:
        row_cells = row.get("data") if isinstance(row, dict) else None
        if not isinstance(row_cells, dict):
            row_cells = {}
        formatted_row: dict[str, Any] = {}
        for index, field in enumerate(fields):
            display_name = resolve_field_display_name(field, index)
            formatted_row[display_name] = resolve_cell_display_value(row_cells.get(str(index)))
        formatted_rows.append(formatted_row)
    return formatted_rows


def is_logout_response(body: Any) -> bool:
    """识别 Seeyon 登录态失效响应。"""
    if not isinstance(body, str):
        return False
    normalized = body.strip().lower()
    return normalized == "__logout" or "<html" in normalized


def query_sales_orders(
    base_url: str,
    session_id: str,
    route: Optional[str],
    report_name: str = DEFAULT_REPORT_NAME,
) -> dict[str, Any]:
    """从首个同名报表的 createMember 取得 bizId，并返回前 100 条订单。"""
    timestamp_ms = int(time.time() * 1000)
    list_opener = build_opener(session_id, route)
    origin = build_origin(base_url)

    report_list_url = build_report_list_url(base_url, str(timestamp_ms % 100000))
    report_list_headers = {
        "Accept": "text/plain, */*; q=0.01",
        "Origin": origin,
        "Referer": f"{base_url.rstrip('/')}/vreport/vReport.do?method=vReportView",
    }
    try:
        list_status, list_text, list_body = post_form(
            list_opener,
            report_list_url,
            build_report_list_form(),
            report_list_headers,
        )
    except urllib.error.HTTPError as exc:
        return {"ok": False, "failed_step": "list_reports", "error": http_error_payload(exc)}
    except urllib.error.URLError as exc:
        return {"ok": False, "failed_step": "list_reports", "error": network_error_payload(exc)}

    if is_logout_response(list_body):
        return {"ok": False, "failed_step": "list_reports", "error": "登录态已失效"}

    report = find_first_report(list_body, report_name)
    if report is None or not report.get("id"):
        return {
            "ok": False,
            "failed_step": "find_report",
            "reportName": report_name,
            "error": f"未找到报表：{report_name}",
            "report_list_response": {"status": list_status, "body_preview": truncate(list_text)},
        }

    report_id = str(report["id"])
    create_member = report.get("createMember")
    biz_id = str(create_member).strip() if create_member is not None else ""
    if not biz_id:
        return {
            "ok": False,
            "failed_step": "resolve_biz_id",
            "reportName": report_name,
            "reportId": report_id,
            "error": "首个同名报表缺少 createMember，无法确定 bizId",
        }

    # 使用首个匹配报表的 createMember 作为本次查询业务范围，不猜测其他来源。
    query_opener = build_opener(session_id, route, biz_id)
    query_timestamp_ms = int(time.time() * 1000)
    report_query_url = build_report_query_url(base_url, biz_id, report_id)
    report_query_headers = {
        "Origin": origin,
        "Referer": (
            f"{base_url.rstrip('/')}/rest/cap4/report/{urllib.parse.quote(str(biz_id), safe='')}/"
            f"{urllib.parse.quote(report_id, safe='')}/{REPORT_QUERY_VERSION}/index.html"
        ),
    }
    try:
        query_status, query_text, query_body = post_json(
            query_opener,
            report_query_url,
            build_report_query_payload(biz_id, report_id, query_timestamp_ms),
            report_query_headers,
        )
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "failed_step": "query_report",
            "reportName": report_name,
            "reportId": report_id,
            "error": http_error_payload(exc),
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "failed_step": "query_report",
            "reportName": report_name,
            "reportId": report_id,
            "error": network_error_payload(exc),
        }

    if is_logout_response(query_body):
        return {
            "ok": False,
            "failed_step": "query_report",
            "reportName": report_name,
            "reportId": report_id,
            "error": "登录态已失效",
        }

    try:
        report_payload = extract_report_payload(query_body)
        orders = format_report_rows(report_payload)
    except ValueError as exc:
        return {
            "ok": False,
            "failed_step": "format_report",
            "reportName": report_name,
            "reportId": report_id,
            "error": str(exc),
            "report_response": {"status": query_status, "body_preview": truncate(query_text)},
        }

    return {
        "ok": True,
        "reportName": report_payload.get("title") or report_name,
        "reportId": report_id,
        "page": report_payload.get("page"),
        "pages": report_payload.get("pages"),
        "size": report_payload.get("size"),
        "total": report_payload.get("total"),
        "executeTime": report_payload.get("executeTime"),
        "orders": orders,
        "report_list_response": {"status": list_status},
        "report_response": {"status": query_status},
    }


def main() -> int:
    """读取命令行参数，查询销售订单并输出 JSON。"""
    parser = argparse.ArgumentParser(description="Query Seeyon sales orders from VReport")
    parser.add_argument("--base-url", default=os.getenv("SEIYON_BASE_URL"), help="Seeyon 基础地址")
    parser.add_argument("--session-id", default=os.getenv("SEIYON_SESSION_ID"), help="登录 Skill 返回的 sessionId")
    parser.add_argument("--jsessionid", dest="session_id_alias", help="兼容旧参数，等价于 --session-id")
    parser.add_argument("--route", default=os.getenv("SEIYON_ROUTE"), help="登录 Skill 返回的可选 route")
    parser.add_argument(
        "--report-name",
        default=os.getenv("SEIYON_SALES_ORDER_REPORT_NAME", DEFAULT_REPORT_NAME),
        help=f"销售订单报表名称，默认 {DEFAULT_REPORT_NAME}",
    )
    args = parser.parse_args()

    session_id = args.session_id or args.session_id_alias
    required_values = {
        "base_url": args.base_url,
        "session_id": session_id,
    }
    missing = [name for name, value in required_values.items() if not value]
    if missing:
        output = {
            "ok": False,
            "failed_step": "validate_args",
            "error": f"Missing required values: {', '.join(missing)}",
        }
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 1

    output = query_sales_orders(
        base_url=args.base_url,
        session_id=session_id,
        route=args.route,
        report_name=args.report_name,
    )
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
