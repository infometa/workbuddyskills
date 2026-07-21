#!/usr/bin/env node
/**
 * generate-dynamic-ad-image.mjs — 从商品图片模版生成图片（MPA/DPA）
 *
 * 用户选择商品图片模版后，调用此脚本生成实际图片素材。
 * 返回的 image_id 可直接用于 creative_components 中 image/image_list 等组件。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, product_catalog_id, product_mode, product_source, dynamic_ad_template_id, dynamic_ad_template_size
 * 可选: remove_template_id
 *
 * 参数说明:
 *   product_catalog_id      — 商品库ID
 *   product_mode            — MULTIPLE（MPA多品）或 SINGLE（DPA/SDPA单品）
 *   product_source          — 商品来源ID。MULTIPLE 模式下为 product_series_id；SINGLE 模式下为商品ID
 *                             来源: mpa_spec.product_series_id 或 marketing_asset_outer_spec.marketing_asset_outer_sub_id
 *   dynamic_ad_template_id  — 模版ID，来自 get-dynamic-ad-image-templates.mjs 返回的列表
 *   dynamic_ad_template_size— 尺寸枚举，格式: SIZE_{width}_{height}，如 SIZE_1280_720, SIZE_800_800
 *   remove_template_id      — 可选，boolean，SINGLE 模式下移除模版标记（默认 false）
 *
 * 示例:
 * { "account_id": "123456789", "product_catalog_id": 100001, "product_mode": "MULTIPLE", "product_source": "200001", "dynamic_ad_template_id": 12345, "dynamic_ad_template_size": "SIZE_1280_720" }
 *
 * 输出（成功）: { "success": true, "image_id": "abc123456" }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 详细规范: references/dynamic-ad-templates.md
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2] != null
    ? process.argv[2]
    : await new Promise(res => {
        let buf = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', d => (buf += d));
        process.stdin.on('end', () => res(buf.trim()));
      });
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数或通过 stdin 传入");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

// ─── 参数校验 ───

const REQUIRED = ["account_id", "product_catalog_id", "product_mode", "product_source", "dynamic_ad_template_id", "dynamic_ad_template_size"];
for (const field of REQUIRED) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

if (!["SINGLE", "MULTIPLE"].includes(input.product_mode)) {
  console.log(JSON.stringify({ success: false, error: { message: `product_mode 必须为 SINGLE 或 MULTIPLE，当前值: ${input.product_mode}` } }));
  process.exit(1);
}

// 校验 dynamic_ad_template_size 格式
if (!/^SIZE_\d+_\d+$/.test(input.dynamic_ad_template_size)) {
  console.log(JSON.stringify({ success: false, error: { message: `dynamic_ad_template_size 格式错误，应为 SIZE_{width}_{height}，如 SIZE_1280_720。当前值: ${input.dynamic_ad_template_size}` } }));
  process.exit(1);
}

const accountId = String(input.account_id);

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(accountId, 10),
  product_catalog_id: Number(input.product_catalog_id),
  product_mode: input.product_mode,
  product_source: String(input.product_source),
  dynamic_ad_template_id: Number(input.dynamic_ad_template_id),
  dynamic_ad_template_size: input.dynamic_ad_template_size,
};

if (input.remove_template_id === true) {
  params.remove_template_id = true;
}

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/dynamic_ad_images/add",
  accountId,
  body: params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `生成图片失败: ${result.error?.message ?? "未知错误"}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};

if (!data.image_id) {
  console.log(JSON.stringify({ success: false, error: { message: "API 未返回 image_id" } }));
  process.exit(1);
}

console.log(JSON.stringify({ success: true, image_id: String(data.image_id) }, null, 2));
