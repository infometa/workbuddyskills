#!/usr/bin/env node
/**
 * get-dynamic-ad-image-templates.mjs — 查询动态商品图片模版列表（MPA/DPA）
 *
 * 当广告组为 MPA/DPA 模式（mpa_spec 非空）且创意形式支持商品模版
 * （support_mpa_image_template=true）时，素材组件使用商品图片模版而非直接上传图片。
 * 此脚本查询可用的图片模版列表，供用户选择。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, product_catalog_id, product_mode, dynamic_ad_template_width, dynamic_ad_template_height
 * 可选: dynamic_ad_template_ownership_type, template_id_list, template_name, page, page_size, filtering
 *
 * 参数说明:
 *   product_catalog_id — 商品库ID，来源: mpa_spec.product_catalog_id 或 marketing_asset_outer_spec.marketing_asset_outer_id
 *   product_mode       — MULTIPLE（MPA多品）或 SINGLE（DPA/SDPA单品）
 *   dynamic_ad_template_width  — 模版宽度(px)，来自 get-creative-templates 输出的组件尺寸 valid.width
 *   dynamic_ad_template_height — 模版高度(px)，来自 get-creative-templates 输出的组件尺寸 valid.height
 *   dynamic_ad_template_ownership_type — 模版归属类型: ALL(默认)/SELF_OWNED/GRANTED/COMMON/PRODUCT_CATALOG_OWNED
 *   template_id_list   — 按模版 ID 精确过滤（数组）
 *   template_name      — 按模版名称模糊搜索
 *
 * 示例:
 * { "account_id": "123456789", "product_catalog_id": 100001, "product_mode": "MULTIPLE", "dynamic_ad_template_width": 1280, "dynamic_ad_template_height": 720 }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     { "dynamic_ad_template_id": 12345, "dynamic_ad_template_name": "模版名称", "image_url": "https://...", "width": 1280, "height": 720 }
 *   ],
 *   "page_info": { "page": 1, "page_size": 100, "total_number": 5, "total_page": 1 }
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

const REQUIRED = ["account_id", "product_catalog_id", "product_mode", "dynamic_ad_template_width", "dynamic_ad_template_height"];
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
  dynamic_ad_template_width: Number(input.dynamic_ad_template_width),
  dynamic_ad_template_height: Number(input.dynamic_ad_template_height),
  page: input.page ?? 1,
  page_size: input.page_size ?? 100,
};

if (input.dynamic_ad_template_ownership_type) {
  params.dynamic_ad_template_ownership_type = input.dynamic_ad_template_ownership_type;
}
if (input.template_id_list) {
  params.template_id_list = input.template_id_list;
}
if (input.template_name) {
  params.template_name = input.template_name;
}
if (input.filtering) {
  params.filtering = input.filtering;
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/dynamic_ad_image_templates/get",
  accountId,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询图片模版列表失败: ${result.error?.message ?? "未知错误"}` } }));
  process.exit(1);
}

// ─── 格式化输出 ───

const data = result.data?.data ?? result.data ?? {};
const list = (data.list ?? []).map(item => ({
  dynamic_ad_template_id: item.dynamic_ad_template_id,
  dynamic_ad_template_name: item.dynamic_ad_template_name,
  image_url: item.image_url,
  width: item.dynamic_ad_template_width,
  height: item.dynamic_ad_template_height,
  ...(item.product_item_display_quantity ? { product_item_display_quantity: item.product_item_display_quantity } : {}),
}));

console.log(JSON.stringify({
  success: true,
  list,
  page_info: data.page_info ?? {},
}, null, 2));
