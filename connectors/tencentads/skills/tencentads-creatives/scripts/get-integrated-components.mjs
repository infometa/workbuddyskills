#!/usr/bin/env node
/**
 * get-integrated-components.mjs — 组件模式查询素材（含报表排序）
 *
 * 调用 integrated_list_multiaccount/get 接口（level=COMPONENT），
 * 按 component_sub_type 过滤，支持按消耗/曝光/ROI 等报表指标排序，
 * 返回组件列表（含 component_value 和报表数据）。
 *
 * 与 get-component-list.mjs 的区别：
 * - 支持 11 种排序指标（含报表数据）
 * - 支持时间范围筛选（报表统计区间）
 * - 支持模糊搜索组件名称
 * - 支持业务单元维度查询
 * - 返回报表字段（cost、view_count 等）
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, component_sub_types（字符串数组）
 * 可选:
 *   sort_field    — 排序字段，默认 "component.component_id"（按时间）
 *                   可选: report.cost / report.view_count / report.order_roi /
 *                         report.conversions_rate / report.ctr / report.conversions_cost /
 *                         report.effective_leads_count / report.effective_cost /
 *                         report.effect_leads_purchase_count / report.effect_leads_purchase_cost
 *   sort_type     — ASCENDING / DESCENDING（默认 DESCENDING）
 *   date_range    — { start_date, end_date }（YYYY-MM-DD，默认近 7 天）
 *   fuzzy_name    — 模糊搜索组件名称
 *   potential_status — 起量潜力筛选（数组），可选值:
 *                      COMMON_POTENTIAL_STATUS_HIGH（高潜）/ COMMON_POTENTIAL_STATUS_LOW（低潜）
 *   first_publication_status — 首发状态筛选（数组），可选值:
 *                      FIRST_PUBLICATION_STATUS_FIRST_PUBLICATION（首发）
 *   quality_status — 素材质量筛选（数组），可选值:
 *                      QUALITY_STATUS_LOW_QUALITY（低质）
 *   generation_type — 生成方式筛选（数组），可选值:
 *                      COMPONENT_GENERATION_TYPE_USER_CREATE（客户自建）
 *                      COMPONENT_GENERATION_TYPE_SYSTEM_DERIVE（妙思衍生）
 *                      COMPONENT_GENERATION_TYPE_ECOLOGICAL_PULL（生态拉取）
 *   page          — 页码（默认 1）
 *   page_size     — 每页数量（默认 20，最大 100）
 *   organization_id — 业务单元 ID（可选）
 *
 * 示例:
 * { "account_id": "123456789", "component_sub_types": ["VIDEO_16X9","VIDEO_9X16"] }
 * { "account_id": "123456789", "component_sub_types": ["IMAGE_16X9"], "sort_field": "report.cost", "date_range": {"start_date":"2026-05-20","end_date":"2026-05-26"} }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     {
 *       "component_id": 1905866436402,
 *       "component_type": "VIDEO",
 *       "component_sub_type": "VIDEO_16X9",
 *       "component_sub_type_cn": "横版视频 16:9",
 *       "component_custom_name": "春节视频",
 *       "component_source_type_cn": "本地上传",
 *       "component_value": { "video": { "value": { "video_id": "xxx", ... } } },
 *       "cost": 1500,
 *       "view_count": 50000,
 *       "order_roi": 2.5,
 *       "conversions_rate": 0.03,
 *       "ctr": 0.05,
 *       "conversions_cost": 50
 *     }
 *   ],
 *   "page_info": { "page": 1, "page_size": 20, "total_number": 156, "total_page": 8 }
 * }
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

for (const field of ["account_id", "component_sub_types"]) {
  if (input[field] == null || (Array.isArray(input[field]) && input[field].length === 0)) {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

if (!Array.isArray(input.component_sub_types)) {
  console.log(JSON.stringify({ success: false, error: { message: "component_sub_types 必须为字符串数组" } }));
  process.exit(1);
}

const accountId = parseInt(String(input.account_id), 10);

// ─── 排序参数 ───

const sortField = input.sort_field || "component.component_id";
const sortType = input.sort_type || "DESCENDING";

// ─── 时间范围（默认近 7 天） ───

function getDefaultDateRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 6);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start_date: fmt(start), end_date: fmt(end) };
}

const dateRange = input.date_range || getDefaultDateRange();

// ─── 构造 filtering ───

const filtering = [
  {
    field: "component.component_sub_type",
    operator: "IN",
    values: input.component_sub_types,
  },
  {
    field: "component.operation_status",
    operator: "IN",
    values: ["CALCULATE_STATUS_EXCLUDE_DEL", "CALCULATE_STATUS_NORMAL"],
  },
];

if (input.fuzzy_name) {
  filtering.push({
    field: "component.fuzzy_name",
    operator: "EQUALS",
    values: [input.fuzzy_name],
  });
}

if (input.potential_status?.length) {
  filtering.push({
    field: "component.potential_status",
    operator: "IN",
    values: input.potential_status,
  });
}

if (input.first_publication_status?.length) {
  filtering.push({
    field: "component.first_publication_status",
    operator: "IN",
    values: input.first_publication_status,
  });
}

if (input.quality_status?.length) {
  filtering.push({
    field: "component.quality_status",
    operator: "IN",
    values: input.quality_status,
  });
}

if (input.generation_type?.length) {
  filtering.push({
    field: "component.generation_type",
    operator: "IN",
    values: input.generation_type,
  });
}

// ─── 构造来源参数 ───

const sourceParams = input.organization_id
  ? {
      organization_id: input.organization_id,
      account_id_list: [accountId],
      operating_scene_type: "OPERATING_SCENE_TYPE_ACCOUNT",
    }
  : {
      account_id_list: [accountId],
    };

// 业务单元时追加 shared_account_id 过滤
if (input.organization_id) {
  filtering.push({
    field: "component.shared_account_id",
    operator: "IN",
    values: [String(accountId)],
  });
}

// ─── 构造请求体 ───

const params = {
  ...sourceParams,
  order_by: [{ sort_field: sortField, sort_type: sortType }],
  date_range: dateRange,
  filtering,
  time_line: "REQUEST_TIME",
  level: "COMPONENT",
  page: input.page ?? 1,
  page_size: input.page_size ?? 20,
  group_by: ["component_id"],
  fields: [
    "component.component_id",
    "component.component_type",
    "component.component_sub_type",
    "component.component_sub_type_cn",
    "component.component_custom_name",
    "component.component_source_type_cn",
    "component.component_value",
    "component.similarity_status",
    "component.potential_status",
    "component.first_publication_status",
    "component.quality_status",
    "component.generation_type",
    "report.cost",
    "report.view_count",
    "report.order_roi",
    "report.conversions_rate",
    "report.ctr",
    "report.conversions_cost",
    "report.effective_leads_count",
    "report.effective_cost",
    "report.effect_leads_purchase_count",
    "report.effect_leads_purchase_cost",
  ],
};

// ─── 发起请求 ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/integrated_list_multiaccount/get",
  accountId: String(accountId),
  body: params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询组件列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

// ─── 解析输出 ───

const data = result.data?.data ?? result.data ?? {};
const rawList = data.list ?? [];
const pageInfo = data.page_info ?? { page: params.page, page_size: params.page_size, total_number: rawList.length };

const list = rawList.map(item => {
  const comp = item.component ?? {};
  const report = item.report ?? {};

  let componentValue = comp.component_value ?? {};
  if (typeof componentValue === "string") {
    try { componentValue = JSON.parse(componentValue); } catch { /**/ }
  }

  return {
    component_id: comp.component_id,
    component_type: comp.component_type,
    component_sub_type: comp.component_sub_type,
    component_sub_type_cn: comp.component_sub_type_cn,
    component_custom_name: comp.component_custom_name,
    component_source_type_cn: comp.component_source_type_cn,
    component_value: componentValue,
    similarity_status: comp.similarity_status,
    potential_status: comp.potential_status,
    first_publication_status: comp.first_publication_status,
    quality_status: comp.quality_status,
    generation_type: comp.generation_type,
    // 报表字段
    cost: report.cost,
    view_count: report.view_count,
    order_roi: report.order_roi,
    conversions_rate: report.conversions_rate,
    ctr: report.ctr,
    conversions_cost: report.conversions_cost,
    effective_leads_count: report.effective_leads_count,
    effective_cost: report.effective_cost,
    effect_leads_purchase_count: report.effect_leads_purchase_count,
    effect_leads_purchase_cost: report.effect_leads_purchase_cost,
  };
}).filter(item => item.component_id);

console.log(JSON.stringify({ success: true, list, page_info: pageInfo }, null, 2));
