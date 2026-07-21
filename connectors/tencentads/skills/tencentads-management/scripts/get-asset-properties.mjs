#!/usr/bin/env node
/**
 * get-asset-properties.mjs — 获取可用的推广内容资产属性（marketing_target_asset_properties/get）
 *
 * 调用 /v3.0/marketing_target_asset_properties/get 接口，查询指定资产类型和类目下的属性定义。
 * 返回每个属性是否必填、是否多选、属性值类型以及可选值列表。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   organization_id             — integer，业务单元 ID
 *   marketing_target_type       — string，推广内容资产类型（枚举 ApiMarketingTargetType）
 *
 * 可选:
 *   marketing_asset_type        — string，产品类型（枚举 MarketingAssetType）
 *   marketing_asset_category    — string，推广内容资产类目（类目之间通过 - 连接）
 *
 * 示例:
 *   {
 *     "organization_id": 23919277,
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PERSONAL_STORE"
 *   }
 *
 *   {
 *     "organization_id": 23879498,
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PRODUCT",
 *     "marketing_asset_category": "孕期至启蒙教育-孕期教育"
 *   }
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "property_name": "PROMOTED_ASSET_ATTR_KEY_PERSONAL_STORE_COMPANY_ENTITY",
 *       "property_cn": "公司主体",
 *       "is_required": true,
 *       "is_multiple": false,
 *       "property_class": "MARKETING_ASSET_ATTR_CLASS_MARKETING",
 *       "property_type": "ATTRIBUTE_TYPE_ENUM",
 *       "property_value": [
 *         "深圳市腾讯计算机系统有限公司"
 *       ]
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
if (input.marketing_asset_category != null && input.marketing_asset_category !== "") {
  params.marketing_asset_category = String(input.marketing_asset_category);
}

// ── Call API ──
const result = await callApi({
  method: "GET",
  path: "/v3.0/marketing_target_asset_properties/get",
  accountId: undefined,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "获取推广内容资产属性失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ── Output ──
const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify({ list: data.list ?? [] }, null, 2));
