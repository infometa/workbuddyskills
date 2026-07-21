#!/usr/bin/env node
/**
 * query-operation-logs.mjs — 腾讯广告管理 - 操作日志查询
 *
 * 封装腾讯广告开放 API operation_log_list/get 接口，查询广告/定向/创意对象的操作日志，
 * 返回每次操作（新建/修改）前后的字段变化详情。
 *
 * 入参:
 * '{
 *   "account_id": "<ID>",                     // 必填，广告主帐号 id（不支持代理商 id）
 *   "operation_object_type": "OPERATION_OBJECT_TYPE_ADGROUP",  // 必填，对象类型
 *                                             // OPERATION_OBJECT_TYPE_ADGROUP（广告）
 *                                             // OPERATION_OBJECT_TYPE_DYNAMIC_CREATIVE（创意）
 *                                             // OPERATION_OBJECT_TYPE_JOINT_BUDGET（联合预算）
 *   "start_date": "YYYY-MM-DD",               // 必填，开始日期，不支持查询 3 个月前的数据
 *   "end_date": "YYYY-MM-DD",                 // 必填，结束日期，与 start_date 差不超过 1 个月
 *
 *   // ─── 以下均为可选 ───
 *   "object_id": 123456789,                   // 指定查询的对象 id（广告/创意 id）
 *   "operation_action_list": ["新建"],         // 操作动作过滤，数组长度 1-2
 *   "operator_platform_list": ["投放管理平台"], // 操作平台过滤，数组长度 1-10
 *   "page": 1,                                // 页码，最大 100，默认 1
 *   "page_size": 20                           // 每页条数，最大 100，默认 20
 * }'
 *
 * 输出:
 * {
 *   "list": [
 *     {
 *       "operation_object_id": 103519996520,
 *       "operation_object_name": "...",
 *       "operation_action": "新建",
 *       "fronted_operator": "QQ(2849246071)",
 *       "fronted_operator_type": "客户",
 *       "fronted_operator_platform": "投放管理平台",
 *       "created_time": "2026-05-25 16:26:03",
 *       "operation_log": [{ "name": "广告名称", "before": null, "after": "..." }, ...],
 *       "adtarget": [...],
 *       "adcreative": [...]
 *     }
 *   ],
 *   "page_info": { "page": 1, "page_size": 20, "total_num": 1, "total_page": 1 }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  let raw;
  if (process.argv[2] === "--base64") {
    const b64 = process.argv[3];
    if (!b64) throw new Error("--base64 后需指定 Base64 编码的 JSON 字符串");
    raw = Buffer.from(b64, "base64").toString("utf-8");
  } else {
    raw = process.argv[2];
  }
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串或使用 --base64 <string>");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。支持两种传参方式：1) 直接传 JSON 字符串（Bash/Zsh）；2) --base64 <string> Base64 编码传参（PowerShell）` }));
  process.exit(1);
}

// ─── 参数解构 ───

const {
  account_id,
  operation_object_type = "OPERATION_OBJECT_TYPE_ADGROUP",
  start_date,
  end_date,
  object_id,
  operation_action_list,
  operator_platform_list,
  page = 1,
  page_size = 20,
} = input;

// ─── 参数校验 ───

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!start_date || !end_date) {
  console.log(JSON.stringify({ error: "missing required fields: start_date, end_date" }));
  process.exit(1);
}

const VALID_OBJECT_TYPES = new Set([
  "OPERATION_OBJECT_TYPE_ADGROUP",
  "OPERATION_OBJECT_TYPE_DYNAMIC_CREATIVE",
  "OPERATION_OBJECT_TYPE_JOINT_BUDGET",
]);
if (!VALID_OBJECT_TYPES.has(operation_object_type)) {
  console.log(JSON.stringify({
    error: `invalid operation_object_type: "${operation_object_type}", must be one of: ${[...VALID_OBJECT_TYPES].join(", ")}`,
  }));
  process.exit(1);
}

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(account_id, 10),
  operation_object_type,
  start_date,
  end_date,
  page: Math.min(Number(page), 100),
  page_size: Math.min(Number(page_size), 100),
};

if (object_id != null) params.object_id = parseInt(object_id, 10);
if (Array.isArray(operation_action_list) && operation_action_list.length > 0) {
  params.operation_action_list = operation_action_list;
}
if (Array.isArray(operator_platform_list) && operator_platform_list.length > 0) {
  params.operator_platform_list = operator_platform_list;
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/operation_log_list/get",
  accountId: String(account_id),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    error: result.error?.message || "API 调用失败",
    detail: result.error,
  }));
  process.exit(1);
}

// ─── 处理返回数据 ───

const data = result.data?.data ?? result.data ?? {};
const rawList = data?.list ?? [];
const conf = data?.conf ?? {};

// 过滤掉无实质内容的操作记录（operation_log 与 operation_info_list 均为空）
const list = rawList.filter(
  (item) => (item.operation_log?.length ?? 0) > 0 || (item.operation_info_list?.length ?? 0) > 0
);

console.log(JSON.stringify({
  list,
  page_info: {
    page: conf.page ?? page,
    page_size: conf.page_size ?? page_size,
    total_num: conf.total_num ?? 0,
    total_page: conf.total_page ?? 0,
  },
}, null, 2));
