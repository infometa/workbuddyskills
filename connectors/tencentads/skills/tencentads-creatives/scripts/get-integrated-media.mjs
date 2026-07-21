#!/usr/bin/env node
/**
 * get-integrated-media.mjs — 素材库模式查询单图/视频
 *
 * 调用 integrated_image_list/get 或 integrated_media_list/get 接口，
 * 按素材粒度查询单图/视频素材库，支持可用性过滤（比例/宽高/时长）、
 * 报表排序、模糊搜索、标签、首发/低质/相似度/生成方式等筛选。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, type（IMAGE 或 VIDEO）
 * 可选:
 *   sort           — 排序字段，默认 "created_time"
 *   sort_type      — ASCENDING / DESCENDING（默认 DESCENDING）
 *   date_range     — 报表时间范围 { start_date, end_date }（YYYY-MM-DD，默认近 7 天）
 *   create_range   — 素材创建时间范围 { start_date, end_date }（YYYY-MM-DD）
 *   ratios         — 可用比例过滤（如 ["16:9","9:16"]），需配合 ratio_valids
 *   ratio_valids   — 每个比例的规格约束数组
 *   fuzzy_name     — 模糊搜索素材名称
 *   label_id       — 内容标签 ID
 *   similarity_status — 相似度状态筛选（数组）
 *   quality_status — 素材质量筛选（数组）
 *   first_publication_status — 首发状态筛选（数组）
 *   generation_type — 生成方式筛选（数组）
 *   duration       — 视频时长筛选（如 "0-15" 表示 0~15 秒，"61" 表示 60 秒以上）
 *   watermark      — 水印筛选（"true" / "false"）
 *   page           — 页码（默认 1）
 *   page_size      — 每页数量（默认 20，最大 100）
 *   organization_id — 业务单元 ID
 *
 * 详细参数说明: references/integrated-media-get.md
 *
 * 示例:
 * { "account_id": "123456789", "type": "VIDEO" }
 * { "account_id": "123456789", "type": "IMAGE", "fuzzy_name": "产品主图", "sort": "cost" }
 *
 * 输出（成功）: { "success": true, "list": [...], "page_info": {...} }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
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

for (const field of ["account_id", "type"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const resourceType = String(input.type).toUpperCase();
if (resourceType !== "IMAGE" && resourceType !== "VIDEO") {
  console.log(JSON.stringify({ success: false, error: { message: "type 必须为 IMAGE 或 VIDEO" } }));
  process.exit(1);
}

const accountId = parseInt(String(input.account_id), 10);

// ─── 默认时间范围（近 7 天） ───

function getDefaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 6);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start_date: fmt(start), end_date: fmt(end) };
}

// ─── 构造请求 ───

const sort = input.sort || "created_time";
const sortType = input.sort_type || "DESCENDING";
const dateRange = input.date_range || getDefaultDateRange();

// 来源参数
const sourceParams = input.organization_id
  ? { organization_id: input.organization_id, shared_account_id: accountId }
  : { account_id: accountId };

// filtering
const filtering = [
  { field: "status", operator: "EQUALS", values: ["ADSTATUS_NORMAL"] },
];

// 素材创建时间范围
if (input.create_range?.start_date) {
  filtering.push({
    field: "created_time",
    operator: "GREATER_EQUALS",
    values: [toTimestamp(input.create_range.start_date + " 00:00:00")],
  });
}
if (input.create_range?.end_date) {
  filtering.push({
    field: "created_time",
    operator: "LESS_EQUALS",
    values: [toTimestamp(input.create_range.end_date + " 23:59:59")],
  });
}

// 标签
if (input.label_id) {
  filtering.push({ field: "label_id", operator: "EQUALS", values: [String(input.label_id)] });
}

// 模糊搜索
if (input.fuzzy_name) {
  filtering.push({ field: "fuzzy_name", operator: "CONTAINS", values: [input.fuzzy_name] });
}

// 通用 IN/EQUALS 筛选字段
const inFilterFields = ["similarity_status", "quality_status", "first_publication_status", "generation_type", "owner_id"];
for (const key of inFilterFields) {
  if (input[key]?.length) {
    const values = Array.isArray(input[key]) ? input[key].map(String) : [String(input[key])];
    filtering.push({
      field: key,
      operator: values.length > 1 ? "IN" : "EQUALS",
      values,
    });
  }
}

// 视频时长
if (input.duration && resourceType === "VIDEO") {
  const parts = String(input.duration).split("-").map(Number);
  const [start, end] = parts;
  if (start > 0) {
    filtering.push({ field: "video_duration_millisecond", operator: "GREATER_EQUALS", values: [String(start * 1000)] });
  }
  if (end && !isNaN(end)) {
    filtering.push({ field: "video_duration_millisecond", operator: "LESS", values: [String((end + 1) * 1000)] });
  }
}

// 水印
if (input.watermark === "true" || input.watermark === "false") {
  filtering.push({ field: "watermark_text_added", operator: "EQUALS", values: [input.watermark] });
}

// or_filtering（可用性过滤：比例+宽高+时长）
const orFiltering = [];
if (input.ratios?.length && input.ratio_valids?.length) {
  for (const valid of input.ratio_valids) {
    const andFiltering = [];

    // 文件大小
    if (valid.file_size_kb_limit) {
      andFiltering.push({ field: "file_size_kb", operator: "LESS_EQUALS", values: [String(valid.file_size_kb_limit)] });
    }

    // 比例
    if (valid.ratio) {
      andFiltering.push({ field: "ratio", operator: "EQUALS", values: [valid.ratio] });
    }

    // 视频时长（仅 VIDEO）
    if (resourceType === "VIDEO") {
      if (valid.min_duration) {
        andFiltering.push({ field: "video_duration_millisecond", operator: "GREATER_EQUALS", values: [String(valid.min_duration * 1000)] });
      }
      if (valid.max_duration) {
        andFiltering.push({ field: "video_duration_millisecond", operator: "LESS_EQUALS", values: [String(valid.max_duration * 1000)] });
      }
    }

    // 宽高约束（min_width/min_height 优先，否则用 width/height 精确匹配）
    if (valid.min_width && valid.min_height) {
      andFiltering.push({ field: "width", operator: "GREATER_EQUALS", values: [String(valid.min_width)] });
      andFiltering.push({ field: "height", operator: "GREATER_EQUALS", values: [String(valid.min_height)] });
    } else if (valid.width && valid.height) {
      andFiltering.push({ field: "width", operator: "EQUALS", values: [String(valid.width)] });
      andFiltering.push({ field: "height", operator: "EQUALS", values: [String(valid.height)] });
    }

    if (andFiltering.length > 0) {
      orFiltering.push({ and_filtering: andFiltering });
    }
  }
}

// 排序
const orderBy = [];
const reportOrderBy = [];
if (sort === "created_time") {
  orderBy.push({ field: "created_time", order: sortType });
} else {
  reportOrderBy.push({ sort_field: sort, sort_type: sortType });
}

// 报表字段
const reportFields = [
  "cost", "view_count", "order_roi", "conversions_rate", "ctr",
  "conversions_cost", "effective_leads_count", "effective_cost",
  "effect_leads_purchase_count", "effect_leads_purchase_cost",
];

const params = {
  ...sourceParams,
  page: input.page ?? 1,
  page_size: input.page_size ?? 20,
  filtering,
  or_filtering: orFiltering.length > 0 ? orFiltering : undefined,
  date_range: dateRange,
  order_by: orderBy,
  report_order_by: reportOrderBy,
  report_fields: reportFields,
};

// ─── 发起请求 ───

const apiPath = resourceType === "IMAGE"
  ? "/v3.0/integrated_image_list/get"
  : "/v3.0/integrated_media_list/get";

const result = await callApi({
  method: "POST",
  path: apiPath,
  accountId: String(accountId),
  body: params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询素材列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

// ─── 解析输出 ───

const data = result.data?.data ?? result.data ?? {};
const rawList = data.list ?? [];
const pageInfo = data.page_info ?? { page: params.page, page_size: params.page_size, total_number: rawList.length };

const list = rawList.map(item => {
  // API 返回结构: item.image（图片）或 item.video（视频），兼容旧的 item.detail 路径
  const detail = item.image ?? item.video ?? item.detail ?? item;
  const report = item.report ?? {};

  const entry = {};

  // 图片字段
  if (resourceType === "IMAGE") {
    entry.image_id = detail.image_id;
    entry.width = detail.width;
    entry.height = detail.height;
    entry.ratio = detail.ratio;
    entry.file_size_kb = detail.file_size_kb;
    entry.preview_url = detail.preview_url ?? detail.image_url;
    entry.description = detail.description ?? detail.image_description;
    entry.signature = detail.signature ?? detail.image_signature;
  }

  // 视频字段
  if (resourceType === "VIDEO") {
    entry.video_id = detail.video_id ?? detail.media_id;
    entry.width = detail.width ?? detail.media_width;
    entry.height = detail.height ?? detail.media_height;
    entry.ratio = detail.ratio;
    entry.file_size_kb = detail.file_size_kb;
    entry.duration_ms = detail.video_duration_millisecond;
    entry.preview_url = detail.preview_url ?? detail.key_frame_image_url;
    entry.description = detail.description ?? detail.media_description;
    entry.system_status = detail.system_status;
  }

  // 通用字段
  entry.similarity_status = detail.similarity_status;
  entry.quality_status = detail.quality_status;
  entry.first_publication_status = detail.first_publication_status;
  entry.generation_type = detail.generation_type;
  entry.created_time = detail.created_time;

  // 报表字段
  entry.cost = report.cost;
  entry.view_count = report.view_count;
  entry.order_roi = report.order_roi;
  entry.conversions_rate = report.conversions_rate;
  entry.ctr = report.ctr;
  entry.conversions_cost = report.conversions_cost;

  return entry;
});

console.log(JSON.stringify({ success: true, list, page_info: pageInfo }, null, 2));

// ─── 工具函数 ───

function toTimestamp(dateStr) {
  if (/^\d+$/.test(String(dateStr))) return String(dateStr);
  const parsed = Date.parse(String(dateStr).replace(" ", "T") + "+08:00");
  if (isNaN(parsed)) return String(dateStr);
  return String(Math.floor(parsed / 1000));
}
