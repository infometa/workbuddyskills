#!/usr/bin/env node
/**
 * query-adgroups.mjs — 腾讯广告管理 - 广告详情查询
 *
 * 封装腾讯广告开放 API adgroups/get 接口，用于获取广告的完整配置信息，
 * 包括定向设置、出价策略、转化规格、版位配置、投放时段等详细属性。
 *
 * 特性：返回数据中每个字段自动附加中文名（从 resources/adgroup-fields.json 映射）
 *
 * --query-fields [关键词]    查询广告字段字典，可选按分类/字段名/中文名过滤
 *   示例: query-adgroups.mjs --query-fields           // 返回全部字段
 *         query-adgroups.mjs --query-fields "定向"     // 返回定向相关字段
 *         query-adgroups.mjs --query-fields "bid"      // 返回包含 bid 的字段
 *         query-adgroups.mjs --query-fields "出价,预算,定向"  // 多关键词批量查询
 *
 * 入参:
 * '{
 *   "account_id": "<ID>",
 *
 *   // ─── 以下均为可选 ───
 *   "tencent_ads_type": "smart" | "standard" | "all",   // 实体类型："smart"=智能投放项目, "standard"=竞价广告（非智投）, "all"=所有广告（默认）
 *   "adgroup_ids": ["123456"],           // 指定广告 ID 列表
 *   "fields": ["adgroup_id", ...],       // 自定义返回字段
 *   "filtering": [...],                  // 过滤条件
 *   "page": 1,                           // 页码（最大 100）
 *   "page_size": 10,                     // 每页条数（最大 100）
 *   "is_deleted": false,                 // 是否查询已删除广告
 *   "pagination_mode": "PAGINATION_MODE_NORMAL",  // 分页方式
 *   "cursor": ""                         // 游标值（配合游标分页）
 * }'
 *
 * 输出:
 * {
 *   "list": [...],
 *   "page_info": { "page": 1, "page_size": 10, "total_number": 50, "total_page": 5 }
 * }
 */

// ─── --query-fields 模式：输出广告字段字典（在所有 import 之前执行） ───

if (process.argv[2] === "--query-fields") {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);

  const fields = JSON.parse(
    readFileSync(join(__dirname, "..", "resources", "adgroup-fields.json"), "utf8")
  );
  const filterArg = process.argv[3];
  let result = fields;
  if (filterArg) {
    const keywords = filterArg.split(",").map((k) => k.trim()).filter(Boolean);
    result = fields.filter((f) =>
      keywords.some(
        (kw) => {
          const k = kw.toLowerCase();
          return (
            f.category.toLowerCase().includes(k) ||
            f.field.toLowerCase().includes(k) ||
            f.label.toLowerCase().includes(k) ||
            (f.description && f.description.toLowerCase().includes(k))
          );
        }
      )
    );
  }
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  let raw;
  if (process.argv[2] === "--base64") {
    const b64 = process.argv[3];
    if (!b64) throw new Error("--base64 后需指定 Base64 编码的 JSON 字符串");
    raw = Buffer.from(b64, "base64").toString("utf-8");
  } else {
    raw = process.argv[2];
  }
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串或使用 --base64 <string>");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。支持两种传参方式：1) 直接传 JSON 字符串（Bash/Zsh）；2) --base64 <string> Base64 编码传参（PowerShell）` }));
  process.exit(1);
}

// ─── tencent_ads_type 枚举 ───
const TENCENT_ADS_TYPE = {
  SMART: "smart",         // 智能投放项目
  STANDARD: "standard",   // 竞价广告（非智投）
  ALL: "all",             // 所有广告（默认）
};
const VALID_ADS_TYPES = new Set(Object.values(TENCENT_ADS_TYPE));

const {
  account_id,
  tencent_ads_type = TENCENT_ADS_TYPE.ALL,
  adgroup_ids,
  fields: userFields,
  filtering: userFiltering,
  page = 1,
  page_size = 10,
  is_deleted = false,
  pagination_mode,
  cursor,
} = input;

// ─── 参数校验 ───

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!VALID_ADS_TYPES.has(tencent_ads_type)) {
  console.log(JSON.stringify({ error: `invalid tencent_ads_type: "${tencent_ads_type}", must be one of: ${[...VALID_ADS_TYPES].join(", ")}` }));
  process.exit(1);
}

// ─── 默认字段 ───

const DEFAULT_FIELDS = [
  "adgroup_id",
  "adgroup_name",
  "auto_acquisition_budget",
  "auto_acquisition_enabled",
  "auto_derived_creative_enabled",
  "auto_derived_creative_status",
  "auto_derived_landing_page_switch",
  "automatic_site_enabled",
  "begin_date",
  "bid_amount",
  "bid_mode",
  "bid_scene",
  "bid_strategy",
  "configured_status",
  "conversion_id",
  "created_time",
  "daily_budget",
  "data_model_version",
  "deep_conversion_behavior_advanced_bid",
  "deep_conversion_behavior_bid",
  "deep_conversion_spec",
  "deep_conversion_worth_advanced_rate",
  "deep_conversion_worth_rate",
  "deep_optimization_type",
  "end_date",
  "first_day_begin_time",
  "flow_optimization_enabled",
  "is_deleted",
  "last_modified_time",
  "marketing_scenario",
  "brand_ad_type",
  "marketing_carrier_detail",
  "marketing_carrier_type",
  "marketing_goal",
  "marketing_sub_goal",
  "marketing_target_detail",
  "marketing_target_id",
  "marketing_asset_id",
  "marketing_target_type",
  "optimization_goal",
  "product_spec",
  "scene_spec",
  "search_expand_targeting_switch",
  "search_expansion_switch",
  "site_set",
  "smart_bid_type",
  "smart_cost_cap",
  "smart_deep_roi",
  "system_status",
  "targeting",
  "targeting_id",
  "targeting_translation",
  "time_series",
  "user_action_sets",
  "material_package_id",
  "auto_acquisition_status",
  "mpa_spec",
  "rta_policy",
  "custom_cost_roi_cap",
  "exploration_strategy",
  "priority_site_set",
  "poi_list",
  "poi_info",
  "marketing_asset_outer_spec",
  "live_video_mode",
  "live_video_sub_mode",
  "deep_optimization_goal",
  "deep_conversion_optimization_goal",
  "deep_advanced_optimization_goal",
  "deep_advanced_conversion_optimization_goal",
  "ecom_pkam_switch",
  "marketing_scene",
  "marketing_target_attachment",
  "promoted_asset_type",
  "cost_constraint_scene",
  "custom_cost_cap",
  "sell_strategy_id",
  "short_play_pay_type",
  "enable_steady_exploration",
  "rta_id",
  "rta_target_id",
  "feedback_id",
  "forward_link_assist",
  "dynamic_ad_type",
  "dca_spec",
  "og_completion_type",
  "joint_budget_rule_id",
  "smart_delivery_platform",
  "smart_delivery_scene",
  "smart_delivery_scene_spec",
  "smart_delivery_aigc_option",
  "aoi_optimization_strategy",
  "flow_lock_status",
  "total_budget",
  "cloud_union_spec",
  "additional_product_spec",
  "incubation_optimization_goal",
  "enable_breakthrough_siteset",
  "live_recommend_strategy_enabled",
  "audience_model_bid_adjustment",
  "project_ability_list",
  "smart_targeting_status",
  "smart_delivery_auto_creative",
  "smart_delivery_history_comp_reused_creative",
  "smart_delivery_aigc_creative",
  "auto_derived_creative_preference",
  "smart_delivery_live_boost",
  "boost_source_project_id",
  "project_ability_spec",
  "expected_roi_mix_factor",
  "smart_coupon_mode",
  "conversion_name",
  "completed_time",
  "cost_guarantee_status",
  "cost_guarantee_money",
  "smart_delivery_period_switch",
  "smart_delivery_period_budget",
  "smart_delivery_period_days",
  "smart_delivery_period_continue",
  "smart_delivery_period_begin_date",
  "smart_delivery_period_end_date",
];

// ─── 构建 filtering ───

/** 需要从 'YYYY-MM-DD HH:mm:ss' 转为 Unix 时间戳的过滤字段 */
const TIME_FILTER_FIELDS = new Set(["created_time", "last_modified_time", "completed_time"]);

/**
 * 将 filtering 中时间字段的值从 'YYYY-MM-DD HH:mm:ss' 格式自动转为 Unix 时间戳（秒）。
 * 如果值已经是纯数字（时间戳），则原样保留。
 */
function convertFilteringTimeValues(filters) {
  return filters.map((f) => {
    // 提取字段名（去掉前缀如 "adgroup."）
    const bareField = f.field?.includes(".") ? f.field.split(".").pop() : f.field;
    if (!TIME_FILTER_FIELDS.has(bareField)) return f;

    return {
      ...f,
      values: (f.values || []).map((v) => {
        // 已经是纯数字（时间戳），原样返回
        if (/^\d+$/.test(String(v))) return v;
        // 尝试解析 'YYYY-MM-DD HH:mm:ss' 格式
        const parsed = Date.parse(String(v).replace(" ", "T") + "+08:00");
        if (isNaN(parsed)) return v; // 无法解析则原样返回
        return String(Math.floor(parsed / 1000));
      }),
    };
  });
}

function buildFiltering() {
  const filters = [];

  // 智投/非智投区分：根据 tencent_ads_type 自动注入 smart_delivery_platform 条件
  // "all" 模式不注入过滤，返回所有广告（不区分普通广告和项目）
  if (tencent_ads_type === TENCENT_ADS_TYPE.SMART) {
    // 智能投放项目：smart_delivery_platform >= SMART_DELIVERY_PLATFORM_EDITION_SCENE
    filters.push({
      field: "smart_delivery_platform",
      operator: "GREATER_EQUALS",
      values: ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"],
    });
  } else if (tencent_ads_type === TENCENT_ADS_TYPE.STANDARD) {
    // 竞价广告（非智投）：smart_delivery_platform < SMART_DELIVERY_PLATFORM_EDITION_SCENE
    filters.push({
      field: "smart_delivery_platform",
      operator: "LESS",
      values: ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"],
    });
  }
  // "all" → 不加过滤，返回所有广告

  // 如果传了 adgroup_ids，构建 ID 过滤
  if (adgroup_ids?.length) {
    filters.push({
      field: "adgroup_id",
      operator: adgroup_ids.length === 1 ? "EQUALS" : "IN",
      values: adgroup_ids.map(String),
    });
  }

  // 追加用户自定义过滤条件（自动转换时间字段）
  if (Array.isArray(userFiltering)) {
    filters.push(...convertFilteringTimeValues(userFiltering));
  }

  return filters.length > 0 ? filters : undefined;
}

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(account_id, 10),
  fields: userFields?.length ? userFields : DEFAULT_FIELDS,
  page: Math.min(Number(page), 100),
  page_size: Math.min(Number(page_size), 100),
};

// 可选参数
if (is_deleted) params.is_deleted = true;

const filtering = buildFiltering();
if (filtering) params.filtering = filtering;

if (pagination_mode) params.pagination_mode = pagination_mode;
if (cursor) params.cursor = cursor;

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/adgroups/get",
  accountId: String(account_id),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    error: result.error?.message || "API 调用失败",
    detail: result.error,
  }));
  process.exit(1);
}
// ─── 处理返回数据 ───

const data = result.data?.data ?? result.data ?? {};
const list = data?.list ?? [];
const pageInfo = data?.page_info ?? {};
const cursorPageInfo = data?.cursor_page_info ?? undefined;

// ─── 时间戳 → 可读时间格式转换 ───

/** 需要从 Unix 时间戳转为 'YYYY-MM-DD HH:mm:ss' 的字段 */
const TIMESTAMP_FIELDS = new Set(["created_time", "last_modified_time", "completed_time"]);

/**
 * 将 Unix 时间戳（秒）转为 'YYYY-MM-DD HH:mm:ss' 格式字符串
 */
function formatTimestamp(ts) {
  const d = new Date(Number(ts) * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

/**
 * 递归遍历对象，将时间戳字段转为可读格式
 */
function convertTimestampFields(obj) {
  if (Array.isArray(obj)) return obj.map(convertTimestampFields);
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      if (TIMESTAMP_FIELDS.has(key) && typeof value === "number") {
        result[key] = formatTimestamp(value);
      } else if (value && typeof value === "object") {
        result[key] = convertTimestampFields(value);
      } else {
        result[key] = value;
      }
    }
    return result;
  }
  return obj;
}

// ─── 加载字段中文名映射表 ───

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** @type {Record<string, string>} field → label 平铺映射（支持嵌套路径如 "targeting.gender" → "性别定向"） */
const fieldLabelMap = (() => {
  try {
    const raw = readFileSync(
      join(__dirname, "..", "resources", "adgroup-fields.json"),
      "utf8"
    );
    const fields = JSON.parse(raw);
    const map = {};
    for (const f of fields) {
      map[f.field] = f.label;
    }
    return map;
  } catch {
    return {};
  }
})();

/**
 * 为对象的每个 key 附加中文名：{ adgroup_name: "xxx" } → { adgroup_name: "xxx", "广告名称": "xxx" }
 * 递归处理嵌套对象，使用点号路径匹配（如 "targeting.gender"）
 * 仅对叶子值（非对象/数组为叶子，或数组内全是原始值）附加中文别名，
 * 避免 struct 类型字段整体复制导致数据膨胀。
 */
function attachChineseLabels(obj, parentPath = "") {
  if (Array.isArray(obj)) return obj.map((item) => attachChineseLabels(item, parentPath));
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const fullPath = parentPath ? `${parentPath}.${key}` : key;
      const label = fieldLabelMap[fullPath];
      const isLeaf = value == null || typeof value !== "object" || (Array.isArray(value) && value.every((v) => v == null || typeof v !== "object"));
      // 递归处理嵌套对象/数组
      result[key] = (value && typeof value === "object") ? attachChineseLabels(value, fullPath) : value;
      // 仅对叶子值附加中文别名
      if (label && isLeaf) {
        result[label] = result[key];
      }
    }
    return result;
  }
  return obj;
}

// ─── 字段名映射（屏蔽技术债：智投项目复用广告接口） ───

// "all" 模式不做字段重命名，保持原始 adgroup_* 字段
const isProject = tencent_ads_type === TENCENT_ADS_TYPE.SMART;

/**
 * 将对象中所有包含 "adgroup" 的 key 替换为 "project"，递归处理嵌套对象/数组。
 * 例：adgroup_id → project_id, adgroup_name → project_name
 */
function renameAdgroupToProject(obj) {
  if (Array.isArray(obj)) return obj.map(renameAdgroupToProject);
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const newKey = key.replace(/adgroup/g, "project");
      result[newKey] = renameAdgroupToProject(value);
    }
    return result;
  }
  return obj;
}

// 裁剪返回数据：移除空对象和无效字段，并转换时间戳
const cleanedList = list.map((item) => {
  const cleaned = {};
  for (const [key, value] of Object.entries(item)) {
    // 跳过空对象 {}
    if (value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length === 0) {
      continue;
    }
    // 跳过 null/undefined
    if (value == null) continue;
    cleaned[key] = value;
  }
  const converted = convertTimestampFields(cleaned);
  const labeled = attachChineseLabels(converted);
  return isProject ? renameAdgroupToProject(labeled) : labeled;
});

const output = {
  list: cleanedList,
  page_info: pageInfo,
};

// 如果使用游标分页，附加游标信息
if (cursorPageInfo) {
  output.cursor_page_info = cursorPageInfo;
}

console.log(JSON.stringify(output, null, 2));
