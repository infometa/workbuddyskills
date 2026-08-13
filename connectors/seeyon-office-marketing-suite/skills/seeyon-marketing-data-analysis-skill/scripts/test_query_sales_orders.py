#!/usr/bin/env python3
"""Seeyon 销售订单报表查询单元测试。

作者：by AI.Coding
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import query_sales_orders


class QuerySalesOrdersTests(unittest.TestCase):
    """覆盖报表发现、请求构造、数据转换和主流程。"""

    def make_http_error(self, code: int, body: str) -> urllib.error.HTTPError:
        """构造可复用的 HTTP 错误对象。"""
        return urllib.error.HTTPError(
            url="http://localhost/seeyon/ajax.do",
            code=code,
            msg="error",
            hdrs=None,
            fp=io.BytesIO(body.encode("utf-8")),
        )

    def report_list_response(self) -> dict:
        """构造包含两个同名报表的列表响应。"""
        return {
            "success": True,
            "data": {
                "reportMap": {
                    "report-1": {
                        "id": "report-1",
                        "subject": "销售订单查询",
                        "createMember": "creator-1",
                    },
                    "report-2": {
                        "id": "report-2",
                        "subject": "销售订单查询",
                        "createMember": "creator-2",
                    },
                }
            },
        }

    def report_query_response(self) -> dict:
        """构造包含重复行的报表查询响应。"""
        payload = {
            "id": "report-1",
            "title": "销售订单查询",
            "fields": [
                {
                    "key": "order_no",
                    "name": "订单编号",
                    "displayField": {"aliasDisplayI18nName": "订单编号", "aliasDisplay": "订单编号"},
                },
                {
                    "key": "status",
                    "name": "订单状态",
                    "displayField": {"aliasDisplay": "订单状态"},
                },
                {"key": "remark", "name": "备注", "displayField": None},
            ],
            "data": [
                {"data": {"0": {"s": "SO-1", "v": "SO-1"}, "1": {"s": "1", "v": "已下单"}, "2": {"s": None, "v": None}}},
                {"data": {"0": {"s": "SO-1", "v": "SO-1"}, "1": {"s": "1", "v": "已下单"}, "2": {"s": None, "v": None}}},
            ],
            "page": "1",
            "pages": "1",
            "size": "100",
            "total": "2",
            "executeTime": "2026-08-10 18:17:39",
        }
        return {"code": "0", "data": {"success": True, "data": payload, "errorMsg": None}}

    def test_find_first_report_uses_response_order(self) -> None:
        """多个同名报表时应选择响应顺序中的第一个。"""
        result = query_sales_orders.find_first_report(self.report_list_response(), "销售订单查询")

        self.assertIsNotNone(result)
        self.assertEqual("report-1", result["id"])

    def test_build_report_list_request_uses_expected_ajax_manager(self) -> None:
        """报表列表请求应使用 vReportAjaxManager 和指定表单参数。"""
        url = query_sales_orders.build_report_list_url("http://localhost/seeyon", "59396")
        form = query_sales_orders.build_report_list_form()

        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual("ajaxAction", query["method"][0])
        self.assertEqual("vReportAjaxManager", query["managerName"][0])
        self.assertEqual("59396", query["rnd"][0])
        self.assertEqual("getVReportViewData", form["managerMethod"])
        self.assertIn('"countData":true', form["arguments"])

    def test_cookie_uses_optional_route_and_adds_scope_after_report_resolution(self) -> None:
        """route 是可选会话路由，sw_scope 仅在取得 createMember 后加入。"""
        list_cookie = query_sales_orders.build_cookie_header("jsid-1", "route-1")
        query_cookie = query_sales_orders.build_cookie_header("jsid-1", "route-1", "creator-1")

        self.assertEqual("JSESSIONID=jsid-1; route=route-1", list_cookie)
        self.assertEqual(
            "JSESSIONID=jsid-1; route=route-1; sw_scope=creator-1", query_cookie
        )

    def test_build_report_query_payload_requests_first_100_rows(self) -> None:
        """报表数据请求应固定为第一页、一页 100 条。"""
        result = query_sales_orders.build_report_query_payload("creator-1", "report-1", 1786357057173)

        self.assertEqual({"page": 1, "pageSize": 100}, result["pagination"])
        self.assertEqual("creator-1", result["queryParams"]["bizId"])
        self.assertEqual("creator-1", result["queryParams"]["bussId"])
        self.assertEqual("report-1", result["queryParams"]["appId"])
        self.assertEqual("1786357057173", result["queryParams"]["_t"])

    def test_format_report_rows_uses_display_names_values_and_keeps_duplicates(self) -> None:
        """格式转换应使用显示值并完整保留重复行和原始顺序。"""
        payload = query_sales_orders.extract_report_payload(self.report_query_response())

        result = query_sales_orders.format_report_rows(payload)

        self.assertEqual(2, len(result))
        self.assertEqual(result[0], result[1])
        self.assertEqual({"订单编号": "SO-1", "订单状态": "已下单", "备注": None}, result[0])

    def test_query_sales_orders_returns_formatted_first_page_without_deduplication(self) -> None:
        """主流程应返回格式化订单，并保持接口返回的重复数据。"""
        with patch.object(
            query_sales_orders,
            "post_form",
            return_value=(200, "report-list", self.report_list_response()),
        ), patch.object(
            query_sales_orders,
            "post_json",
            return_value=(200, "report-data", self.report_query_response()),
        ) as post_json_mock:
            result = query_sales_orders.query_sales_orders(
                base_url="http://localhost/seeyon",
                session_id="jsid-1",
                route="route-1",
                report_name="销售订单查询",
            )

        self.assertTrue(result["ok"])
        self.assertEqual("report-1", result["reportId"])
        self.assertIn("/creator-1/query1/report-1/1", post_json_mock.call_args.args[1])
        self.assertEqual("creator-1", post_json_mock.call_args.args[2]["queryParams"]["bizId"])
        self.assertEqual("2", result["total"])
        self.assertEqual(2, len(result["orders"]))
        self.assertEqual(result["orders"][0], result["orders"][1])
        self.assertNotIn("outStock", result)

    def test_query_sales_orders_returns_report_not_found(self) -> None:
        """没有指定名称的报表时应返回清晰的失败步骤。"""
        response = {"success": True, "data": {"reportMap": {}}}
        with patch.object(query_sales_orders, "post_form", return_value=(200, "{}", response)):
            result = query_sales_orders.query_sales_orders(
                "http://localhost/seeyon", "jsid-1", None, "销售订单查询"
            )

        self.assertFalse(result["ok"])
        self.assertEqual("find_report", result["failed_step"])

    def test_query_sales_orders_returns_http_error_for_report_query(self) -> None:
        """报表数据接口发生 HTTP 错误时应返回统一错误结构。"""
        with patch.object(
            query_sales_orders,
            "post_form",
            return_value=(200, "report-list", self.report_list_response()),
        ), patch.object(
            query_sales_orders,
            "post_json",
            side_effect=self.make_http_error(500, "boom"),
        ):
            result = query_sales_orders.query_sales_orders(
                "http://localhost/seeyon", "jsid-1", None, "销售订单查询"
            )

        self.assertFalse(result["ok"])
        self.assertEqual("query_report", result["failed_step"])
        self.assertEqual(500, result["error"]["status"])

    def test_query_sales_orders_requires_create_member_from_first_report(self) -> None:
        """首个同名报表缺少 createMember 时不应猜测 bizId。"""
        response = self.report_list_response()
        response["data"]["reportMap"]["report-1"].pop("createMember")
        with patch.object(query_sales_orders, "post_form", return_value=(200, "report-list", response)):
            result = query_sales_orders.query_sales_orders(
                "http://localhost/seeyon", "jsid-1", None, "销售订单查询"
            )

        self.assertFalse(result["ok"])
        self.assertEqual("resolve_biz_id", result["failed_step"])

    def test_main_without_required_args_returns_validate_args(self) -> None:
        """命令行缺少必填参数时应输出 validate_args 并返回状态码 1。"""
        # 清空相关环境变量，确保测试只验证无参数调用的确定性行为。
        with patch.object(sys, "argv", ["query_sales_orders.py"]), patch.dict(
            os.environ, {}, clear=True
        ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = query_sales_orders.main()

        output = json.loads(stdout.getvalue())
        self.assertEqual(1, exit_code)
        self.assertFalse(output["ok"])
        self.assertEqual("validate_args", output["failed_step"])
        self.assertIn("base_url", output["error"])
        self.assertIn("session_id", output["error"])


if __name__ == "__main__":
    unittest.main()
