#!/usr/bin/env node
/**
 * get-asset-detail.mjs — 获取推广内容资产详情（marketing_target_asset_detail/get）
 *
 * 调用 /v3.0/marketing_target_asset_detail/get 接口，根据营销资产 ID 和推广内容资产类型获取资产详情。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   marketing_asset_id             — integer，推广内容资产 ID
 *   marketing_target_type          — string，推广内容资产类型（枚举 ApiMarketingTargetType）
 *
 * 可选:
 *   account_id                     — integer，广告主帐号 ID
 *   organization_id                — integer，业务单元 ID
 *
 * 示例:
 *   {
 *     "marketing_asset_id": 123456789,
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PERSONAL_STORE",
 *     "organization_id": 23919277
 *   }
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "marketing_asset_id": 123456789,
 *       "marketing_asset_name": "个人店铺测试",
 *       "marketing_asset_type": "...",
 *       "marketing_target_type": "MARKETING_TARGET_TYPE_PERSONAL_STORE",
 *       "created_time": "2026-01-01 00:00:00",
 *       "properties": [...],
 *       "extra_properties": [...]
 *     }
 *   ]
 * }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
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
if (input.marketing_asset_id == null || input.marketing_asset_id === "") missing.push("marketing_asset_id");
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
  marketing_asset_id: parseInt(String(input.marketing_asset_id), 10),
  marketing_target_type: String(input.marketing_target_type),
};

if (input.account_id != null && input.account_id !== "") {
  params.account_id = parseInt(String(input.account_id), 10);
}
if (input.organization_id != null && input.organization_id !== "") {
  params.organization_id = parseInt(String(input.organization_id), 10);
}

// ── Call API ──
const result = await callApi({
  method: "GET",
  path: "/v3.0/marketing_target_asset_detail/get",
  accountId: input.account_id != null ? String(input.account_id) : undefined,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "获取推广内容资产详情失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ── Output ──
const data = result.data?.data ?? result.data ?? {};
const list = data.list ?? [];
console.log(JSON.stringify({ list }, null, 2));
