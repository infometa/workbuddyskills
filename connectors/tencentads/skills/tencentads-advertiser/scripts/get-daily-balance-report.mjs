#!/usr/bin/env node
/**
 * get-daily-balance-report.mjs — 获取资金账户日结明细
 *
 * 调用 GET /v3.0/daily_balance_report/get
 * 查询指定广告主账户的资金账户日结明细，包含日终结余数据。
 *
 * 注意：account_id 仅支持广告主账号，不支持代理商 ID。
 * 日期范围单次查询跨度不能超过 10 天，支持两年内的数据查询。
 *
 * 入参: '{"account_id": 123456, "date_range": {"start_date": "2024-05-10", "end_date": "2024-05-15"}}'
 * 必填: account_id, date_range (含 start_date, end_date)
 * 选填: page (默认1), page_size (默认10, 最大100)
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "account_id": 123456,
 *       "fund_type": "FUND_TYPE_CASH",
 *       "time": 1715270400,
 *       "deposit": 100000,
 *       "paid": 50000,
 *       "trans_in": 1100000,
 *       "trans_out": 55000,
 *       "credit_modify": 400000,
 *       "balance": 300000,
 *       "preauth_balance": 11,
 *       "preauth_out_pay": 2,
 *       "preauth_in_refund": 20,
 *       "acct_out_pay": 0,
 *       "acct_out_pay_share": 50,
 *       "share_out_pay": 10
 *     }
 *   ],
 *   "page_info": {
 *     "page": 1,
 *     "page_size": 10,
 *     "total_number": 1,
 *     "total_page": 1
 *   }
 * }
 *
 * 输出（失败）:
 * {
 *   "success": false,
 *   "error": { "code": 1000014, "message": "...", "message_cn": "..." }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数，如 '{\"account_id\":123456,\"date_range\":{\"start_date\":\"2024-05-10\",\"end_date\":\"2024-05-15\"}}'");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}` },
  }));
  process.exit(1);
}

// ─── 必填校验 ───

const { account_id, date_range, page, page_size } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

if (!date_range || typeof date_range !== "object") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: date_range (must be an object with start_date and end_date)" } }));
  process.exit(1);
}

const { start_date, end_date } = date_range;

if (!start_date || typeof start_date !== "string") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: date_range.start_date (format: YYYY-MM-DD)" } }));
  process.exit(1);
}

if (!end_date || typeof end_date !== "string") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: date_range.end_date (format: YYYY-MM-DD)" } }));
  process.exit(1);
}

// ─── 日期格式校验 ───

const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

if (!DATE_REGEX.test(start_date)) {
  console.log(JSON.stringify({ success: false, error: { message: `invalid start_date format: "${start_date}", expected YYYY-MM-DD` } }));
  process.exit(1);
}

if (!DATE_REGEX.test(end_date)) {
  console.log(JSON.stringify({ success: false, error: { message: `invalid end_date format: "${end_date}", expected YYYY-MM-DD` } }));
  process.exit(1);
}

// ─── 日期范围校验（不超过 10 天） ───

const startMs = new Date(start_date).getTime();
const endMs = new Date(end_date).getTime();

if (isNaN(startMs) || isNaN(endMs)) {
  console.log(JSON.stringify({ success: false, error: { message: "invalid date value in date_range" } }));
  process.exit(1);
}

if (startMs > endMs) {
  console.log(JSON.stringify({ success: false, error: { message: "start_date must be less than or equal to end_date" } }));
  process.exit(1);
}

const diffDays = (endMs - startMs) / (1000 * 60 * 60 * 24);
if (diffDays > 10) {
  console.log(JSON.stringify({ success: false, error: { message: `date_range span is ${diffDays} days, maximum allowed is 10 days` } }));
  process.exit(1);
}

// ─── 可选参数校验 ───

if (page !== undefined && (typeof page !== "number" || page < 1 || page > 99999)) {
  console.log(JSON.stringify({ success: false, error: { message: "page must be an integer between 1 and 99999" } }));
  process.exit(1);
}

if (page_size !== undefined && (typeof page_size !== "number" || page_size < 1 || page_size > 100)) {
  console.log(JSON.stringify({ success: false, error: { message: "page_size must be an integer between 1 and 100" } }));
  process.exit(1);
}

// ─── 构建请求参数 ───

const params = {
  account_id: parseInt(account_id, 10),
  date_range: {
    start_date,
    end_date,
  },
};

if (page !== undefined) params.page = page;
if (page_size !== undefined) params.page_size = page_size;

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/daily_balance_report/get",
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API 调用失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ─── 提取并输出结果 ───

const data = result.data?.data ?? result.data ?? {};
const list = data.list ?? [];
const page_info = data.page_info ?? {};

console.log(JSON.stringify({ list, page_info }, null, 2));
