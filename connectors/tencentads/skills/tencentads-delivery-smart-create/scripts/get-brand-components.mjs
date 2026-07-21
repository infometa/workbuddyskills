#!/usr/bin/env node
/**
 * get-brand-components.mjs — 查询账户可用的品牌形象组件列表
 *
 * 通过 integrated_list_multiaccount/get 接口查询 COMPONENT 层级，
 * 筛选 component_sub_type = BRAND 的组件，返回品牌形象列表供用户选择。
 *
 * 入参: '{"account_id": "12345678"}'
 *   - account_id: 必填，广告账户 ID
 *   - page: 可选，页码（默认 1）
 *   - page_size: 可选，每页数量（默认 10）
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "brand_components": [
 *     {
 *       "component_id": 1917953657934,
 *       "brand_name": "品牌名称",
 *       "brand_image_id": "xxx",
 *       "component_custom_name": "自定义名称",
 *       "component_source_type": "来源类型"
 *     }
 *   ],
 *   "total": 5,
 *   "page_info": { "page": 1, "page_size": 10, "total_number": 5, "total_page": 1 }
 * }
 *
 * 输出（失败）:
 * {
 *   "success": false,
 *   "error": { "message": "..." }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数（至少包含 account_id）");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}` },
  }));
  process.exit(1);
}

const { account_id, page = 1, page_size = 20 } = input;

if (!account_id) {
  console.log(JSON.stringify({
    success: false,
    error: { message: "missing required field: account_id" },
  }));
  process.exit(1);
}

// ─── 构造请求体 ───

// Date range: last 7 days
const now = new Date();
const endDate = now.toISOString().slice(0, 10); // YYYY-MM-DD
const startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

const body = {
  account_id_list: [parseInt(String(account_id), 10)],
  page: Number(page),
  page_size: Number(page_size),
  date_range: {
    start_date: startDate,
    end_date: endDate,
  },
  time_line: "REQUEST_TIME",
  level: "COMPONENT",
  group_by: ["component_id"],
  order_by: [
    {
      sort_field: "component.component_id",
      sort_type: "DESCENDING",
    },
  ],
  filtering: [
    {
      field: "component.component_sub_type",
      operator: "IN",
      values: ["BRAND"],
    },
    {
      field: "component.operation_status",
      operator: "IN",
      values: ["CALCULATE_STATUS_EXCLUDE_DEL", "CALCULATE_STATUS_NORMAL"],
    },
    {
      field: "component.scene",
      operator: "IN",
      values: ["DEFAULT"],
    },
  ],
  fields: [
    "component.organization_id",
    "component.component_id",
    "component.component_type",
    "component.component_sub_type",
    "component.component_sub_type_cn",
    "component.component_custom_name",
    "component.component_source_type",
    "component.component_source_type_cn",
    "component.component_value",
    "component.similarity_status",
    "component.potential_status",
    "component.quality_status",
    "component.generation_type",
  ],
};

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/integrated_list_multiaccount/get",
  accountId: String(account_id),
  body,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API 调用失败",
      message_cn: result.error?.message_cn,
    },
  }));
  process.exit(1);
}

// ─── 解析返回数据 ───

const data = result.data?.data ?? result.data ?? {};
const list = data?.list ?? [];
const pageInfo = data?.page_info ?? {};

// Extract brand component info from each item
const brandComponents = list.map((item) => {
  const comp = item?.component ?? {};
  const componentValue = comp.component_value ?? {};
  const brandValue = componentValue?.brand?.value ?? {};

  return {
    component_id: comp.component_id,
    brand_name: brandValue.brand_name || "",
    brand_image_id: brandValue.brand_image_id || "",
    component_custom_name: comp.component_custom_name || "",
    component_source_type_cn: comp.component_source_type_cn || "",
    quality_status: comp.quality_status || "",
  };
}).filter((c) => c.component_id); // Filter out items without component_id

if (brandComponents.length === 0) {
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `账户 ${account_id} 下未找到可用的品牌形象组件。请先在腾讯广告后台创建品牌形象组件后重试。`,
    },
  }));
  process.exit(1);
}

console.log(JSON.stringify({
  success: true,
  brand_components: brandComponents,
  total: pageInfo.total_number ?? brandComponents.length,
  page_info: pageInfo,
}, null, 2));
