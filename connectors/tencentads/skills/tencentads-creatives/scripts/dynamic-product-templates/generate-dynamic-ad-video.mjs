#!/usr/bin/env node
/**
 * generate-dynamic-ad-video.mjs — 从商品视频模版生成视频（MPA/DPA）
 *
 * 用户选择商品视频模版后，调用此脚本生成实际视频素材。
 * 返回的 video_id 可直接用于 creative_components 中 video 组件。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, product_catalog_id, product_mode, product_source, dynamic_ad_template_id
 *
 * 参数说明:
 *   product_catalog_id      — 商品库ID
 *   product_mode            — MULTIPLE（MPA多品）或 SINGLE（单品）
 *   product_source          — 商品来源ID。MULTIPLE 模式下为 product_series_id；SINGLE 模式下为商品ID
 *                             来源: mpa_spec.product_series_id 或 marketing_asset_outer_spec.marketing_asset_outer_sub_id
 *   dynamic_ad_template_id  — 视频模版ID，来自 get-dynamic-ad-video-templates.mjs 返回的列表
 *
 * 示例:
 * { "account_id": "123456789", "product_catalog_id": 100001, "product_mode": "MULTIPLE", "product_source": "200001", "dynamic_ad_template_id": 67890 }
 *
 * 输出（成功）: { "success": true, "video_id": "abc123456", "video_preview_image_id": "def789" }
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

const REQUIRED = ["account_id", "product_catalog_id", "product_mode", "product_source", "dynamic_ad_template_id"];
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

const accountId = String(input.account_id);

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(accountId, 10),
  product_catalog_id: Number(input.product_catalog_id),
  product_mode: input.product_mode,
  product_source: String(input.product_source),
  dynamic_ad_template_id: Number(input.dynamic_ad_template_id),
};

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/dynamic_ad_video/add",
  accountId,
  body: params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `生成视频失败: ${result.error?.message ?? "未知错误"}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};

if (!data.video_id) {
  console.log(JSON.stringify({ success: false, error: { message: "API 未返回 video_id" } }));
  process.exit(1);
}

const output = {
  success: true,
  video_id: String(data.video_id),
};
if (data.video_preview_image_id) {
  output.video_preview_image_id = String(data.video_preview_image_id);
}
if (data.video_preview_image_url) {
  output.video_preview_image_url = data.video_preview_image_url;
}

console.log(JSON.stringify(output, null, 2));
