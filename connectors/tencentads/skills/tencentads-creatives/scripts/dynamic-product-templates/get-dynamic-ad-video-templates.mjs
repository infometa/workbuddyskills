#!/usr/bin/env node
/**
 * get-dynamic-ad-video-templates.mjs — 查询动态商品视频模版列表（MPA/DPA）
 *
 * 当广告组为 MPA/DPA 模式且创意形式支持商品视频模版
 * （support_mpa_video_template=true）时，素材组件使用商品视频模版。
 * 此脚本查询可用的视频模版列表，供用户选择。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, product_catalog_id, adcreative_template_id, product_mode
 * 可选: support_channel, dynamic_ad_template_ownership_type, template_id_list, template_name, page, page_size
 *
 * 参数说明:
 *   product_catalog_id       — 商品库ID
 *   adcreative_template_id   — 创意形式ID（来自 get-creative-templates 输出的 template_id）
 *   product_mode             — MULTIPLE（MPA多品）或 SINGLE（单品，当前仅支持 MULTIPLE）
 *   support_channel          — 是否筛选支持视频号版位的模版（boolean）
 *   dynamic_ad_template_ownership_type — 模版归属: SELF_OWNED / PRODUCT_VIDEO_STRAIGHT_OUT
 *   template_id_list         — 按模版 ID 精确过滤（数组）
 *   template_name            — 按模版名称模糊搜索
 *
 * 示例:
 * { "account_id": "123456789", "product_catalog_id": 100001, "adcreative_template_id": 720, "product_mode": "MULTIPLE" }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     { "template_id": 67890, "template_name": "模版名称", "cover_image_url": "https://...", "intro_video_url": "https://...", "min_video_duration": 6, "max_video_duration": 30 }
 *   ],
 *   "page_info": { "page": 1, "page_size": 100, "total_number": 3, "total_page": 1 }
 * }
 *
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

const REQUIRED = ["account_id", "product_catalog_id", "adcreative_template_id", "product_mode"];
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
  adcreative_template_id: Number(input.adcreative_template_id),
  product_mode: input.product_mode,
  page: input.page ?? 1,
  page_size: input.page_size ?? 100,
};

if (input.support_channel != null) {
  params.support_channel = Boolean(input.support_channel);
}
if (input.dynamic_ad_template_ownership_type) {
  params.dynamic_ad_template_ownership_type = input.dynamic_ad_template_ownership_type;
}
if (input.template_id_list) {
  params.template_id_list = input.template_id_list;
}
if (input.template_name) {
  params.template_name = input.template_name;
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/dynamic_ad_video_templates/get",
  accountId,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询视频模版列表失败: ${result.error?.message ?? "未知错误"}` } }));
  process.exit(1);
}

// ─── 格式化输出 ───

const data = result.data?.data ?? result.data ?? {};
const list = (data.list ?? []).map(item => ({
  template_id: item.template_id,
  template_name: item.template_name,
  cover_image_url: item.cover_image_url,
  intro_video_url: item.intro_video_url,
  ...(item.min_video_duration != null ? { min_video_duration: item.min_video_duration } : {}),
  ...(item.max_video_duration != null ? { max_video_duration: item.max_video_duration } : {}),
  ...(item.support_channel != null ? { support_channel: item.support_channel } : {}),
}));

console.log(JSON.stringify({
  success: true,
  list,
  page_info: data.page_info ?? {},
}, null, 2));
