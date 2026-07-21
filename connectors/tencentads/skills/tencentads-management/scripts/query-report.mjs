#!/usr/bin/env node
/**
 * query-report.mjs — 腾讯广告管理 - 综合数据报表查询
 *
 * 封装 integrated_list_multiaccount/get 接口，自动处理：
 * - 标准过滤条件构建（根据 level 自动推导 filtering prefix + 智投/非智投区分）
 * - group_by 自动推导
 * - fields 校验与补全
 * - 返回数据裁剪（只保留有效字段）
 *
 * ─── 特殊模式 ───
 * --query-fields [关键词]    查询报表指标字段字典，可选按分类/字段名/中文名过滤
 *   示例: query-report.mjs --query-fields           // 返回全部字段
 *         query-report.mjs --query-fields "视频"     // 返回视频相关字段
 *         query-report.mjs --query-fields "cost"     // 返回包含 cost 的字段
 *         query-report.mjs --query-fields "cost,click,impression"  // 多关键词批量查询
 *
 * ─── 标准模式 ───
 * 入参:
 * '{
 *   "account_ids": ["<ID1>", "<ID2>", ...],  // 账户 ID 数组（单账户也用数组格式）
 *   "date_range": { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" },
 *   "level": "ADGROUP",
 *
 *   // ─── 以下均为可选 ───
 *   "tencent_ads_type": "smart" | "standard" | "all",   // 实体类型："smart"=智能投放项目, "standard"=竞价广告（非智投）, "all"=所有广告（默认），全权控制智投/非智投过滤
 *   "adgroup_ids": ["123456"],           // 指定广告 ID 列表（内部自动切为 specified 模式）
 *   "creative_ids": ["789"],             // 指定创意 ID 列表
 *   "component_ids": ["456"],            // 指定组件 ID 列表
 *   "fields": ["report.cost", ...],      // 自定义返回字段
 *   "group_by": ["adgroup_id"],          // 自定义聚合维度
 *   "time_line": "REQUEST_TIME",         // 时间口径
 *   "order_by": [{"sort_field": "report.cost", "sort_type": "DESCENDING"}],
 *   "filtering": [...],                  // 额外自定义过滤条件（会追加到标准过滤之后）
 *   "post_filtering": [...],             // 后置过滤条件
 *   "page": 1,
 *   "page_size": 20,
 *   "fetch_all": false,                   // 是否自动分页拉取全部数据（默认 false，开启后忽略 page 参数，自动翻页直到拉完所有数据）
 *   "is_total": false,
 *   "report_only": false,
 *   "fuzzy_name": "关键词"               // 广告名称模糊搜索
 * }'
 *
 * 输出（数据写入文件，stdout 返回文件路径 + 摘要 + 预览）:
 * {
 *   "file_path": "/absolute/path/to/output/report_xxx.json",
 *   "summary": { "total_rows": 150, "page_info": {...}, "level": "ADGROUP", ... },
 *   "preview": [ // 前 3 条数据 ]
 * }
 */

// ─── --query-fields 模式：输出报表指标字段字典（必须在所有 import 之前执行） ───

if (process.argv[2] === "--query-fields") {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, resolve } = await import("node:path");
  const __dirname = dirname(fileURLToPath(import.meta.url));
  const fieldsPath = resolve(__dirname, "../resources/report-fields.json");
  try {
    const fields = JSON.parse(readFileSync(fieldsPath, "utf8"));
    // 支持按分类、关键词过滤（逗号分隔支持多关键词批量查询）
    const filterArg = process.argv[3]; // 可选：分类名或关键词，多个用逗号分隔
    let result = fields;
    if (filterArg) {
      const keywords = filterArg.split(",").map((k) => k.trim()).filter(Boolean);
      result = fields.filter((f) =>
        keywords.some((kw) => {
          const k = kw.toLowerCase();
          return (
            f.category.toLowerCase().includes(k) ||
            f.field.toLowerCase().includes(k) ||
            f.label.toLowerCase().includes(k) ||
            (f.description && f.description.toLowerCase().includes(k))
          );
        })
      );
    }
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.log(JSON.stringify({ error: `读取字段字典失败: ${err.message}` }));
  }
  process.exit(0);
}

import { callApi } from "tencentads-cli";
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// ─── 缓存配置 ───
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 分钟缓存有效期

// ─── 字段中文名映射表（合并 adgroup-fields + report-fields） ───

const __filename_main = fileURLToPath(import.meta.url);
const __dirname_main = dirname(__filename_main);

const fieldLabelMap = (() => {
  const map = {};
  const load = (file, prefix = "") => {
    try {
      const fields = JSON.parse(readFileSync(join(__dirname_main, "..", "resources", file), "utf8"));
      for (const f of fields) {
        const key = prefix ? `${prefix}.${f.field}` : f.field;
        map[key] = f.label;
      }
    } catch { /* ignore */ }
  };
  load("adgroup-fields.json");         // adgroup.* 字段已带前缀或无前缀（广告详情）
  load("report-fields.json", "report"); // 报表指标加 report. 前缀
  return map;
})();

/**
 * 为对象的每个 key 附加中文名：{ cost: 123 } → { cost: 123, "花费": 123 }
 * 递归处理嵌套对象，使用点号路径匹配（如 "adgroup.adgroup_id"、"report.cost"）
 * 仅对叶子值附加中文别名，避免 struct 类型字段整体复制导致数据膨胀。
 */
function attachChineseLabels(obj, parentPath = "") {
  if (Array.isArray(obj)) return obj.map((item) => attachChineseLabels(item, parentPath));
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const fullPath = parentPath ? `${parentPath}.${key}` : key;
      const label = fieldLabelMap[fullPath];
      const isLeaf = value == null || typeof value !== "object" || (Array.isArray(value) && value.every((v) => v == null || typeof v !== "object"));
      result[key] = (value && typeof value === "object") ? attachChineseLabels(value, fullPath) : value;
      if (label && isLeaf) {
        result[label] = result[key];
      }
    }
    return result;
  }
  return obj;
}

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
  account_ids: rawAccountId,
  date_range,
  level = "ADGROUP",
  tencent_ads_type = TENCENT_ADS_TYPE.ALL,
  adgroup_ids,
  creative_ids,
  component_ids,
  fields: userFields,
  group_by: userGroupBy,
  time_line = "REQUEST_TIME",
  order_by,
  filtering: userFiltering,
  post_filtering,
  page = 1,
  page_size = 20,
  fetch_all = false,
  is_total = false,
  report_only = false,
  fuzzy_name,
} = input;

// ─── 参数校验 ───

if (!rawAccountId) {
  console.log(JSON.stringify({ error: "missing required field: account_ids (数组格式如 [\"123\", \"456\"])" }));
  process.exit(1);
}

// 统一处理 account_ids：统一转为数组
const accountIdList = (Array.isArray(rawAccountId) ? rawAccountId : [rawAccountId]).map((id) => parseInt(String(id), 10));
if (accountIdList.some((id) => isNaN(id) || id <= 0)) {
  console.log(JSON.stringify({ error: "account_ids 包含无效值，请传入有效的账户 ID（数字）" }));
  process.exit(1);
}
// 取第一个账户 ID 用于 callApi 鉴权标识（鉴权本身不依赖具体账户）
const primaryAccountId = String(accountIdList[0]);

if (!VALID_ADS_TYPES.has(tencent_ads_type)) {
  console.log(JSON.stringify({ error: `invalid tencent_ads_type: "${tencent_ads_type}", must be one of: ${[...VALID_ADS_TYPES].join(", ")}` }));
  process.exit(1);
}

if (!date_range?.start_date || !date_range?.end_date) {
  console.log(JSON.stringify({ error: "missing required field: date_range (需要 start_date 和 end_date)" }));
  process.exit(1);
}

// ─── 内部状态：是否为指定 ID 查询模式 ───

const isSpecifiedMode = !!(adgroup_ids?.length || creative_ids?.length || component_ids?.length);

// ─── 根据 level 推导 mergeFiltering 前缀 ───

/**
 * 各 level 对应的 mergeFiltering prefix 映射
 * 参考 3.0-report-pages-level-filtering.md 汇总表
 */
const LEVEL_FILTERING_CONFIG = {
  ADVERTISER:          { prefix: null, supportSD: false },       // 无 filtering
  ADGROUP:             { prefix: "adgroup", supportSD: true },
  BIDWORD:             { prefix: "report", supportSD: true },
  QUERYWORD:           { prefix: "report", supportSD: true },
  IMAGE:               { prefix: "image", supportSD: true },
  VIDEO:               { prefix: "video", supportSD: true },
  VIDEO_AGGREGATION:   { prefix: null, supportSD: false },       // 无 filtering
  DYNAMIC_CREATIVE:    { prefix: "dynamic_creative", supportSD: true },
  CHANNEL:             { prefix: "report", supportSD: true },
  LANDING_PAGE:        { prefix: "report", supportSD: true },
  MARKETING_ASSET:     { prefix: "report", supportSD: true },
  PRODUCT_CATALOG:     { prefix: "product_catalog", supportSD: true },
  REGION:              { prefix: "report", supportSD: true },
  AGE:                 { prefix: "report", supportSD: true },
  GENDER:              { prefix: "report", supportSD:  true},
  CITY:                { prefix: "report", supportSD: true },
  AUDIENCE:            { prefix: "report", supportSD: true },
  AOI:                 { prefix: "report", supportSD: true },
  WECHAT_SHOP_PRODUCT: { prefix: "wechat-shop", supportSD: true },
  CREATIVE_ASSET:      { prefix: "report", supportSD: true },
  COMPONENT:           { prefix: "report", supportSD: true },
};

// ─── filtering 时间字段自动转换 ───

/** filtering 中需要从 'YYYY-MM-DD HH:mm:ss' 转为 Unix 时间戳的字段（匹配最后一段） */
const FILTERING_TIME_FIELDS = new Set(["created_time", "last_modified_time", "completed_time"]);

/**
 * 将 'YYYY-MM-DD HH:mm:ss' 格式字符串转为 Unix 秒级时间戳字符串。
 * 如果输入已经是纯数字（时间戳），则原样返回。
 */
function parseDatetimeToTimestamp(value) {
  if (/^\d+$/.test(value)) return value; // 已是时间戳
  const d = new Date(value.replace(" ", "T"));
  if (isNaN(d.getTime())) return value; // 无法解析，原样返回
  return String(Math.floor(d.getTime() / 1000));
}

/**
 * 遍历 filtering 数组，将时间字段的 values 从可读格式转为时间戳
 */
function convertFilteringTimeValues(filters) {
  if (!Array.isArray(filters)) return filters;
  return filters.map((f) => {
    if (FILTERING_TIME_FIELDS.has(f.field) || FILTERING_TIME_FIELDS.has(f.field?.split(".").pop())) {
      return { ...f, values: f.values?.map(parseDatetimeToTimestamp) };
    }
    return f;
  });
}

// ─── filtering 操作符白名单 ───

const VALID_OPERATORS = new Set([
  "EQUALS",          // 等于
  "CONTAINS",        // 模糊匹配
  "LESS",            // 小于
  "LESS_EQUALS",     // 小于等于
  "GREATER",         // 大于
  "GREATER_EQUALS",  // 大于等于
  "IN",              // IN 操作符
]);

/**
 * 校验 filtering 数组中每个条件的 operator 是否在白名单内，
 * 不支持的操作符直接报错退出。
 */
function validateFilteringOperators(filters) {
  if (!Array.isArray(filters)) return;
  for (const f of filters) {
    if (f.operator && !VALID_OPERATORS.has(f.operator)) {
      console.log(JSON.stringify({
        error: `不支持的 filtering 操作符: "${f.operator}"（字段: ${f.field}）。仅支持: ${[...VALID_OPERATORS].join(", ")}`,
      }));
      process.exit(1);
    }
  }
}

// ─── 构建 filtering ───

// 判断当前 level 是否属于创意层级（即 filtering 字段应使用 dynamic_creative.* 前缀）
const isCreativeLevel = level === "DYNAMIC_CREATIVE";

function buildFiltering() {
  const filters = [];

  // 指定 ID 模式：先添加 ID 过滤条件
  if (isSpecifiedMode) {
    if (adgroup_ids?.length) {
      filters.push({
        field: "adgroup.adgroup_id",
        operator: "IN",
        values: adgroup_ids.map(String),
      });
    }
    if (creative_ids?.length) {
      filters.push({
        field: "dynamic_creative.dynamic_creative_id",
        operator: creative_ids.length === 1 ? "EQUALS" : "IN",
        values: creative_ids.map(String),
      });
    }
    if (component_ids?.length) {
      filters.push({
        field: "component.component_id",
        operator: component_ids.length === 1 ? "EQUALS" : "IN",
        values: component_ids.map(String),
      });
    }
  }

  // 标准过滤条件：列表模式始终追加，specified 模式在非主体级别（如 REGION/AGE 等维度查询）时也需要追加
  const needStandardFilters = !isSpecifiedMode || !isEntityLevel(level);
  if (needStandardFilters) {
    const config = LEVEL_FILTERING_CONFIG[level];
    const prefix = config ? config.prefix : "adgroup";
    const supportSD = config?.supportSD ?? false;

    // ADVERTISER / VIDEO_AGGREGATION 等无 prefix 的 level 不追加默认 filtering
    if (prefix !== null) {
      // brand_ad_type：前缀跟随 level 对应的 prefix
      filters.push({
        field: `${prefix}.brand_ad_type`,
        operator: "EQUALS",
        values: ["BRAND_AD_TYPE_NONE"],
      });

      // campaign_type：CREATIVE_ASSET 特殊使用 report 前缀，其余使用 adgroup
      const campaignPrefix = level === "CREATIVE_ASSET" ? "report" : "adgroup";
      filters.push({
        field: `${campaignPrefix}.campaign_type`,
        operator: "EQUALS",
        values: ["CAMPAIGN_TYPE_NORMAL"],
      });

      // 智投/非智投区分 —— 完全由 tencent_ads_type 决定
      if (supportSD) {
        if (tencent_ads_type === TENCENT_ADS_TYPE.SMART) {
          // 智能投放项目：smart_delivery_platform >= SMART_DELIVERY_PLATFORM_EDITION_SCENE
          filters.push({
            field: "adgroup.smart_delivery_platform",
            operator: "GREATER_EQUALS",
            values: ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"],
          });
        } else if (tencent_ads_type === TENCENT_ADS_TYPE.STANDARD) {
          // 竞价广告（非智投）：smart_delivery_platform < SMART_DELIVERY_PLATFORM_EDITION_SCENE
          filters.push({
            field: "adgroup.smart_delivery_platform",
            operator: "LESS",
            values: ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"],
          });
        }
        // "all" → 不加过滤，返回所有广告
      }
    }
  }

  // 模糊搜索：创意层级用 dynamic_creative.fuzzy_name，广告层级用 adgroup.fuzzy_name
  if (fuzzy_name) {
    filters.push({
      field: isCreativeLevel ? "dynamic_creative.fuzzy_name" : "adgroup.fuzzy_name",
      operator: "EQUALS",
      values: [String(fuzzy_name)],
    });
  }

  // 追加用户自定义过滤条件（校验操作符 + 自动转换时间字段）
  if (Array.isArray(userFiltering)) {
    validateFilteringOperators(userFiltering);
    filters.push(...convertFilteringTimeValues(userFiltering));
  }

  return filters.length > 0 ? filters : undefined;
}

// ─── 自动推导 group_by ───

/**
 * 判断 level 是否为主体级别（广告/创意/组件等）
 * 非主体级别为维度级别（地域/年龄/性别/受众等），在 specified 模式下仍需标准过滤
 */
function isEntityLevel(lvl) {
  const entityLevels = new Set([
    "ADVERTISER", "ADGROUP", "DYNAMIC_CREATIVE", "COMPONENT",
    "CHANNEL", "BIDWORD", "QUERYWORD", "IMAGE", "VIDEO",
    "VIDEO_AGGREGATION", "MARKETING_ASSET", "CREATIVE_ASSET",
    "LANDING_PAGE", "PRODUCT_CATALOG", "WECHAT_SHOP_PRODUCT",
  ]);
  return entityLevels.has(lvl);
}

function buildGroupBy() {
  // 如果用户显式指定了 group_by，直接使用
  if (userGroupBy?.length) return userGroupBy;

  // 根据 level 和查询模式自动推导
  switch (level) {
    case "ADGROUP":
      return ["adgroup_id"];
    case "DYNAMIC_CREATIVE":
      // 真实请求 group_by 为 ["dynamic_creative_id", "adgroup_id"]，需同时包含所属广告 ID
      return ["dynamic_creative_id", "adgroup_id"];
    case "COMPONENT":
      return ["component_id"];
    case "CHANNEL":
      return ["channel_id"];
    case "BIDWORD":
      return ["bidword_id"];
    case "QUERYWORD":
      return ["queryword_id"];
    case "IMAGE":
      return ["image_id"];
    case "VIDEO":
      return ["video_id"];
    case "MARKETING_ASSET":
      return ["marketing_asset_id"];
    case "CREATIVE_ASSET":
      return ["creative_asset_id", "adgroup_id", "dynamic_creative_id"];
    case "ADVERTISER":
      return ["date"];
    case "REGION":
      return ["area_id"];
    case "AGE":
      return ["age"];
    case "GENDER":
      return ["gender"];
    case "CITY":
      return ["city_id"];
    case "AUDIENCE":
      return ["audience_id", "account_id"];
    case "AOI":
      return ["aoi_id"];
    case "LANDING_PAGE":
      return ["landing_page_url"];
    case "PRODUCT_CATALOG":
      return ["product_catalog_id"];
    default:
      return ["adgroup_id"];
  }
}

// ─── 自动推导 fields ───

/** 各 level 的默认属性字段（与真实请求对齐） */
const DEFAULT_ATTR_FIELDS = {
  ADGROUP: [
    "account_id",
    "adgroup.adgroup_id",
    "adgroup.adgroup_name",
    "adgroup.is_deleted",
    "adgroup.smart_delivery_platform",
    "adgroup.smart_delivery_scene",
    "adgroup.smart_delivery_scene_spec",
    "adgroup.boost_source_project_id",
    "adgroup.marketing_target_type",
    "adgroup.marketing_target_type_cn",
    "adgroup.marketing_goal",
    "adgroup.marketing_goal_cn",
    "adgroup.marketing_sub_goal",
    "adgroup.marketing_sub_goal_cn",
    "adgroup.marketing_carrier_type",
    "adgroup.marketing_carrier_type_cn",
    "adgroup.marketing_carrier_detail",
    "adgroup.marketing_target_id",
    "adgroup.marketing_asset_id",
    "adgroup.marketing_asset_outer_spec",
    "adgroup.optimization_goal",
    "adgroup.optimization_goal_cn",
    "adgroup.incubation_optimization_goal",
    "adgroup.incubation_optimization_goal_cn",
    "adgroup.deep_coversion_worth_goal_cn",
    "adgroup.deep_coversion_behavior_goal_cn",
    "adgroup.deep_coversion_behavior_advanced_goal_cn",
    "adgroup.deep_coversion_worth_advanced_goal_cn",
    "adgroup.total_budget",
    "adgroup.daily_budget",
    "adgroup.begin_date",
    "adgroup.end_date",
    "adgroup.first_day_begin_time",
    "adgroup.time_series",
    "adgroup.og_completion_type",
    "adgroup.system_status",
    "adgroup.system_status_cn",
    "adgroup.system_status_tips",
    "adgroup.configured_status",
    "adgroup.created_by_industry_platform",
    "adgroup.ad_approval_status",
    "adgroup.auto_acquisition_enabled",
    "adgroup.auto_acquisition_budget",
    "adgroup.auto_acquisition_status",
    "adgroup.auto_acquisition_status_text",
    "adgroup.auto_acquisition_status_message",
    "adgroup.cost_guarantee_status",
    "adgroup.cost_guarantee_status_message",
    "adgroup.site_set",
    "adgroup.site_set_cn",
    "adgroup.automatic_site_enabled",
    "adgroup.exploration_strategy",
    "adgroup.priority_site_set",
    "adgroup.cloud_union_spec",
    "adgroup.material_package_id",
    "adgroup.mpa_spec",
    "adgroup.dca_spec",
    "adgroup.flow_lock_status",
    "adgroup.bid_amount",
    "adgroup.bid_mode",
    "adgroup.bid_scene",
    "adgroup.smart_bid_type",
    "adgroup.smart_bid_type_cn",
    "adgroup.project_ability_spec",
    "adgroup.targeting_translation",
    "adgroup.deep_conversion_spec",
    "adgroup.deep_conversion_behavior_bid",
    "adgroup.deep_conversion_behavior_advanced_bid",
    "adgroup.deep_conversion_worth_rate",
    "adgroup.deep_conversion_worth_advanced_rate",
    "adgroup.joint_budget_rule_id",
    "adgroup.live_video_mode",
    "adgroup.live_video_sub_mode",
    "adgroup.ecom_pkam_switch",
    "adgroup.is_rta",
    "adgroup.rta_policy_uuid",
  ],
  DYNAMIC_CREATIVE: [
    "account_id",
    "adgroup.site_set",
    "adgroup.marketing_carrier_type",
    "adgroup.marketing_carrier_detail",
    "adgroup.marketing_target_type",
    "adgroup.smart_delivery_platform",
    "adgroup.boost_source_project_id",
    "adgroup.cloud_union_spec",
    "adgroup.material_package_id",
    "adgroup.mpa_spec",
    "adgroup.dca_spec",
    "dynamic_creative.dynamic_creative_id",
    "dynamic_creative.adgroup_id",
    "dynamic_creative.dynamic_creative_name",
    "dynamic_creative.is_deleted",
    "dynamic_creative.configured_status",
    "dynamic_creative.system_status",
    "dynamic_creative.system_status_cn",
    "dynamic_creative.system_status_tips",
    "dynamic_creative.system_status_explanation",
    "dynamic_creative.dynamic_creative_status_info",
    "dynamic_creative.source",
    "dynamic_creative.creative_insight",
    "dynamic_creative.dynamic_creative_similarity_status",
    "dynamic_creative.creative_components",
    "dynamic_creative.component_selector_type",
    "dynamic_creative.creative_template_id",
    "dynamic_creative.program_creative_info",
  ],
  COMPONENT: [
    "account_id",
    "component.component_id",
    "component.component_type",
    "component.component_sub_type",
    "component.approval_status",
    "component.operation_status",
  ],
  ADVERTISER: [
  ],
  BIDWORD: [
    "account_id",
    "report.bidword_id",
    "report.bidword",
  ],
  QUERYWORD: [
    "account_id",
    "report.queryword",
  ],
  IMAGE: [
    "account_id",
    "image.image_name",
    "image.image_id",
  ],
  VIDEO: [
    "account_id",
    "video.video_name",
    "video.video_id",
  ],
  VIDEO_AGGREGATION: [
    "account_id",
  ],
  MARKETING_ASSET: [
    "account_id",
    "marketing_asset.marketing_asset_id",
    "marketing_asset.marketing_asset_name",
  ],
  REGION: [
    "account_id",
  ],
  AGE: [
    "account_id",
  ],
  GENDER: [
    "account_id",
  ],
  CITY: [
    "account_id",
  ],
  AUDIENCE: [
    "account_id",
  ],
  AOI: [
    "account_id",
  ],
  WECHAT_SHOP_PRODUCT: [
    "account_id",
    "product_catalog.wechat_channels_product_name",
    "product_catalog.wechat_channels_shop_name",
    "product_catalog.wechat_channels_product_id",
    "product_catalog.wechat_channels_shop_id"
  ],
  LANDING_PAGE: [
    "account_id",
    "report.vangogh_landing_page_id",
    "report.vangogh_landing_page_name"
  ],
  PRODUCT_CATALOG: [
    "account_id",
    "product_catalog.product_catalog_name",
    "product_catalog.product_catalog_id"
  ],
  CREATIVE_ASSET: [
    "account_id",
    "creative_asset.creative_asset_id",
    "creative_asset.component_id",
    "creative_asset.component_type",
    "creative_asset.component_value",
    "creative_asset.organization_id"
  ],
};

/** 默认报表字段 */
const DEFAULT_REPORT_FIELDS = [
  "report.cost",
  "report.view_count",
  "report.valid_click_count",
  "report.ctr",
  "report.conversions_count",
  "report.conversions_cost",
  "report.conversions_by_click_count",
  "report.preview_conversions_count",
  "report.click_nick_count",
  "report.balance",
  "report.wechat_cost_stage1",
  "report.wechat_cost_stage2",
];

function buildFields() {
  // 如果用户显式指定了 fields，直接使用
  if (userFields?.length) return userFields;

  // 指定 ID 模式 + 分时/按天查询时，只需报表字段
  if (isSpecifiedMode && userGroupBy?.length) {
    const isTimeSeries = userGroupBy.some((g) => g === "date" || g === "hour");
    if (isTimeSeries) {
      return [...DEFAULT_REPORT_FIELDS];
    }
  }

  // report_only 模式只返回报表字段
  if (report_only) {
    return [...DEFAULT_REPORT_FIELDS];
  }

  // 默认同时返回属性 + 报表字段
  const attrFields = DEFAULT_ATTR_FIELDS[level] ?? [];
  return [...attrFields, ...DEFAULT_REPORT_FIELDS];
}

// ─── 构造请求体 ───

const body = {
  account_id_list: accountIdList,
  page: Number(page),
  page_size: Number(page_size),
  date_range: {
    start_date: date_range.start_date,
    end_date: date_range.end_date,
  },
  time_line,
  is_total,
  level,
  group_by: buildGroupBy(),
  fields: buildFields(),
};

// 可选字段：filtering 为空时不传（接口要求 filtering 为 nil 或至少包含 1 个有效条件）
const filtering = buildFiltering();
if (filtering) body.filtering = filtering;

if (report_only) body.report_only = true;
if (order_by?.length) {
  body.order_by = order_by;
} else {
  // 默认排序：当包含 report.* 字段时，必须传 order_by，否则接口可能返回空数据
  const hasReportFields = body.fields.some(f => f.startsWith("report."));
  if (hasReportFields) {
    body.order_by = [{ sort_field: "report.default_order_by", sort_type: "ASCENDING" }];
  }
}
if (post_filtering?.length) body.post_filtering = post_filtering;

// ─── 缓存检查：相同参数 10 分钟内复用已有结果 ───

const outputDir = join(__dirname_main, "..", "output");
if (!existsSync(outputDir)) {
  mkdirSync(outputDir, { recursive: true });
}

// 根据完整请求参数生成缓存 key（MD5 哈希）
const cacheKey = createHash("md5").update(JSON.stringify(body)).digest("hex").slice(0, 12);
const accountTag = accountIdList.length <= 3
  ? accountIdList.join("-")
  : `${accountIdList[0]}_etc${accountIdList.length}`;
const dateTag = `${date_range.start_date}_${date_range.end_date}`.replace(/-/g, "");
const fileName = `report_${accountTag}_${level}_${dateTag}_${cacheKey}.json`;
const filePath = join(outputDir, fileName);

// 检查缓存是否命中（文件存在且未超过 10 分钟）
if (existsSync(filePath)) {
  const fileStat = statSync(filePath);
  const ageMs = Date.now() - fileStat.mtimeMs;
  if (ageMs < CACHE_TTL_MS) {
    // 缓存命中，直接读取并返回
    const cachedData = JSON.parse(readFileSync(filePath, "utf-8"));
    const cachedList = cachedData.list ?? [];
    console.log(JSON.stringify({
      file_path: filePath,
      cached: true,
      cache_age_seconds: Math.round(ageMs / 1000),
      summary: {
        total_rows: cachedList.length,
        page_info: cachedData.page_info,
        level,
        date_range,
        account_ids: accountIdList,
        tencent_ads_type,
      },
      preview: cachedList.slice(0, 3),
    }, null, 2));
    process.exit(0);
  }
}

// ─── 调用 API ───

/**
 * 单次请求封装
 */
async function fetchPage(requestBody) {
  const result = await callApi({
    method: "POST",
    path: "/v3.0/integrated_list_multiaccount/get",
    accountId: primaryAccountId,
    body: requestBody,
  });

  if (!result.success) {
    console.log(JSON.stringify({
      error: result.error?.message || "API 调用失败",
      detail: result.error,
    }));
    process.exit(1);
  }

  return result.data?.data ?? result.data ?? {};
}

// ─── 处理返回数据 ───

let list;
let pageInfo;

if (fetch_all) {
  // ─── 自动分页拉取全部数据 ───
  const allList = [];
  let currentPage = 1;
  // fetch_all 模式下使用较大的 page_size 以减少请求次数，但不超过用户指定值（如果用户指定了更大的值）
  const fetchPageSize = Math.max(Number(page_size), 100);
  let totalPage = 1; // 初始值，第一次请求后更新

  while (currentPage <= totalPage) {
    const pageBody = { ...body, page: currentPage, page_size: fetchPageSize };
    const data = await fetchPage(pageBody);
    const pageList = data?.list ?? [];
    const info = data?.page_info ?? {};

    allList.push(...pageList);

    // 更新总页数
    totalPage = info.total_page ?? 1;

    // 如果当前页返回数据为空或已到最后一页，停止翻页
    if (pageList.length === 0 || currentPage >= totalPage) break;

    // 请求间隔 100ms，避免请求过于频繁
    await new Promise((resolve) => setTimeout(resolve, 100));

    currentPage++;
  }

  list = allList;
  pageInfo = {
    page: 1,
    page_size: allList.length,
    total_number: allList.length,
    total_page: 1,
  };
} else {
  // ─── 单次请求（默认行为） ───
  const data = await fetchPage(body);
  list = data?.list ?? [];
  pageInfo = data?.page_info ?? {};
}

// ─── 字段名映射（屏蔽技术债：智投项目复用广告接口） ───

// "all" 模式不做字段重命名，保持原始 adgroup_* 字段
const isProject = tencent_ads_type === TENCENT_ADS_TYPE.SMART;

/**
 * 将对象中所有包含 "adgroup" 的 key 替换为 "project"，递归处理嵌套对象/数组。
 * 例：adgroup_id → project_id, adgroup_name → project_name, adgroup → project
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

// 裁剪返回数据：移除空对象和无效字段
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
  return isProject ? renameAdgroupToProject(cleaned) : cleaned;
}).map((item) => attachChineseLabels(item));

// ─── 将查询结果写入缓存文件并返回文件路径 + 摘要 ───

const outputData = {
  list: cleanedList,
  page_info: pageInfo,
};

writeFileSync(filePath, JSON.stringify(outputData, null, 2), "utf-8");

// 输出摘要 + 文件路径，供模型后续读取文件做深度分析
console.log(JSON.stringify({
  file_path: filePath,
  cached: false,
  summary: {
    total_rows: cleanedList.length,
    page_info: pageInfo,
    level,
    date_range,
    account_ids: accountIdList,
    tencent_ads_type,
  },
  // 预览前 3 条数据，帮助模型快速了解数据结构
  preview: cleanedList.slice(0, 3),
}, null, 2));
