#!/usr/bin/env node
/**
 * get-asset-categories.mjs — 获取可用的推广内容资产类目（marketing_target_asset_categories/get）
 *
 * 调用 /v3.0/marketing_target_asset_categories/get 接口，查询指定资产类型下的类目。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   organization_id             — integer，业务单元 ID
 *   marketing_target_type       — string，推广内容资产类型（枚举 ApiMarketingTargetType）
 *
 * 可选:
 *   marketing_asset_type        — string，产品类型（枚举 MarketingAssetType），不传则返回所有类目
 *   page                        — integer，页码（默认 1）
 *   page_size                   — integer，每页条数（默认 10，最大 100）
 *   filtering                   — struct[]，过滤条件
 *
 * 示例:
 *   {
 *     "organization_id": 23919277,
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PLATFORM_CHANNEL"
 *   }
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "cate1_id": "网服",
 *       "cate1_name": "网服",
 *       "cate2_id": "网服-小剧场",
 *       "cate2_name": "小剧场",
 *       "cate3_id": "网服-小剧场-都市短剧",
 *       "cate3_name": "都市短剧",
 *       "cate4_id": "",
 *       "cate4_name": "",
 *       "last_cate_tips": "..."
 *     }
 *   ],
 *   "page_info": { "page": 1, "page_size": 10, "total_number": 100, "total_page": 10 }
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
if (input.organization_id == null || input.organization_id === "") missing.push("organization_id");
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
  organization_id: parseInt(String(input.organization_id), 10),
  marketing_target_type: String(input.marketing_target_type),
};

if (input.marketing_asset_type != null && input.marketing_asset_type !== "") {
  params.marketing_asset_type = String(input.marketing_asset_type);
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
  path: "/v3.0/marketing_target_asset_categories/get",
  accountId: undefined,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "获取推广内容资产类目失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ── Output ──
const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify({ list: data.list ?? [], page_info: data.page_info ?? {} }, null, 2));
