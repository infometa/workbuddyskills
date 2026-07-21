#!/usr/bin/env node
/**
 * get-asset-list.mjs — 获取可投放推广内容资产列表（marketing_target_assets/get）
 *
 * 调用 /v3.0/marketing_target_assets/get 接口，获取指定资产类型下的资产列表。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   marketing_target_type       — string，推广内容资产类型（枚举 ApiMarketingTargetType）
 *
 * 可选:
 *   account_id                  — integer，推广帐号 id（有操作权限的帐号 id）
 *   organization_id             — integer，业务单元 ID
 *   page                        — integer，页码（默认 1）
 *   page_size                   — integer，每页条数（默认 10，最大 100）
 *   filtering                   — struct[]，过滤条件
 *     - field: marketing_asset_id 时，operator 可选 EQUALS / IN / LESS
 *     - field: marketing_asset_name 时，operator 可选 EQUALS / CONTAINS
 *
 * 示例:
 *   {
 *     "account_id": 123456,
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PERSONAL_STORE",
 *     "page": 1,
 *     "page_size": 10
 *   }
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "marketing_asset_id": 12345,
 *       "marketing_asset_name": "我的个人店铺",
 *       "marketing_asset_type": "...",
 *       "created_time": 1491019858,
 *       "is_deleted": false,
 *       "properties": [...]
 *     }
 *   ],
 *   "page_info": { "page": 1, "page_size": 10, "total_number": 1, "total_page": 1 }
 * }
 */

import { callApi } from "tencentads-cli";

// ── Parse input ──
let input;
try {
  const raw = process.argv[2] != null
    ? process.argv[2]
    : await new Promise((res) => {
        let buf = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', (d) => (buf += d));
        process.stdin.on('end', () => res(buf.trim()));
      });
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数或通过 stdin 传入");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

// ── Validate required fields ──
const missing = [];
if (!input.marketing_target_type) missing.push("marketing_target_type");

if (missing.length > 0) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `缺少必填参数: ${missing.join(", ")}` },
  }));
  process.exit(1);
}

// ── Build request params ──
const params = {
  marketing_target_type: String(input.marketing_target_type),
};

if (input.account_id != null && input.account_id !== "") {
  params.account_id = parseInt(String(input.account_id), 10);
}
if (input.organization_id != null && input.organization_id !== "") {
  params.organization_id = parseInt(String(input.organization_id), 10);
}
if (input.page != null) {
  params.page = parseInt(String(input.page), 10);
}
if (input.page_size != null) {
  params.page_size = parseInt(String(input.page_size), 10);
}
if (Array.isArray(input.filtering) && input.filtering.length > 0) {
  params.filtering = input.filtering;
}

// ── Call API ──
const result = await callApi({
  method: "GET",
  path: "/v3.0/marketing_target_assets/get",
  accountId: input.account_id != null ? parseInt(String(input.account_id), 10) : undefined,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "获取推广内容资产列表失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ── Output ──
const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify({ list: data.list ?? [], page_info: data.page_info ?? {} }, null, 2));
