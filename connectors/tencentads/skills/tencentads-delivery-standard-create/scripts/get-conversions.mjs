#!/usr/bin/env node
/**
 * get-conversions.mjs — 获取常规广告转化目标列表
 *
 * 调用 /v3.0/conversions/get（新接口），通过 filtering 传入投放上下文参数，
 * 标注哪些含深度转化目标，裁剪无关字段。
 * 常规广告不传 delivery_scene。
 *
 * 入参（统一使用字符串枚举 key）:
 * '{
 *   "account_id": "<ID>",
 *   "site_set": ["SITE_SET_WECHAT_MOMENTS", ...],              // 用户指定的版位列表
 *   "available_site_set": ["SITE_SET_CHANNELS", ...],          // get-site-set.mjs 返回的全量可用版位列表
 *   "non_multi_site_set": ["SITE_SET_MOBILE_YYB", ...],        // get-site-set.mjs 返回的不支持多版位组合的版位列表（site_set_multi=0）
 *   "marketing_carrier_id": "<载体ID>",     // 推广载体 ID（来自 get-assets 返回的 marketing_carrier_id / marketing_asset_outer_id），根据 carrier_type 决定是否作为 product_id 传入
 *   "asset_id": "<资产ID>",                 // 行业产品库资产 ID（来自 get-assets 返回的 marketing_asset_id），仅行业产品库类传 marketing_asset_id
 *   "marketing_goal": "MARKETING_GOAL_USER_GROWTH",
 *   "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
 *   "marketing_carrier_type": "MARKETING_CARRIER_TYPE_APP_ANDROID",
 *   "marketing_target_type": "MARKETING_TARGET_TYPE_APP_ANDROID",
 *   "bid_mode": "BID_MODE_OCPM",  // 出价方式，用于 cost_type 过滤
 *   "create_source_type": "SELF_CREATED"  // 可选，PLATFORM=平台预置 / SELF_CREATED=自建转化，不传则返回全部
 * }'
 *
 * 输出:
 * {
 *   "goals": [
 *     {
 *       "conversion_id": 12345,
 *       "name": "APP激活",
 *       "bid_mode": "BID_MODE_OCPM",
 *       "has_deep_conversion": false,
 *       "create_source_type": "PLATFORM"           // PLATFORM=平台预置 / SELF_CREATED=自建转化
 *     },
 *     {
 *       "conversion_id": 12346,
 *       "name": "注册-首日付费ROI",
 *       "optimization_goal": "OPTIMIZATIONGOAL_APP_REGISTER",
 *       "bid_mode": "BID_MODE_OCPM",
 *       "has_deep_conversion": true,
 *       "deep_conversion_type": "DEEP_CONVERSION_WORTH",
 *       "deep_conversion_worth_goal": "GOAL_1DAY_PURCHASE_ROAS",
 *       "create_source_type": "SELF_CREATED"
 *     }
 *   ]
 * }
 */

import { callApi, deriveProductType, deriveLiveVideoMode, resolveSiteSetAliases } from "tencentads-cli";

// ─── bid_mode → cost_type 映射 ───
// 旧接口的 filter_bid_mode（数值）→ 新接口的 cost_type filtering
const BID_MODE_TO_COST_TYPE = {
  BID_MODE_OCPM: "COST_TYPE_OCPM",
  BID_MODE_OCPC: "COST_TYPE_OCPC",
  BID_MODE_CPC: "COST_TYPE_CPC",
  BID_MODE_CPM: "COST_TYPE_CPM",
};

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` }));
  process.exit(1);
}

const {
  account_id,
  site_set,
  available_site_set,
  non_multi_site_set,
  marketing_carrier_id,
  marketing_goal,
  marketing_sub_goal,
  marketing_carrier_type,
  marketing_target_type,
  bid_mode: inputBidMode,
  create_source_type,
} = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!site_set || !Array.isArray(site_set)) {
  console.log(JSON.stringify({ error: "missing required field: site_set (数组，来自 get-site-set.mjs 返回)" }));
  process.exit(1);
}

// ─── 构造 filtering 数组 ───
// /v3.0/conversions/get 使用 filtering: [{field, operator, values}] 结构

const normalizedSiteSet = resolveSiteSetAliases(site_set);

// 如果传入了 available_site_set，取用户指定版位与可用版位的交集，
// 防止 Agent 误传全量可用版位而非用户实际选择的版位
const intersectedSiteSet = available_site_set && Array.isArray(available_site_set) && available_site_set.length > 0
  ? normalizedSiteSet.filter((s) => available_site_set.includes(s))
  : normalizedSiteSet;

// 过滤掉 SITE_SET_SEARCH_SCENE — 该版位不参与转化目标查询
// 过滤掉 site_set_multi=0 的版位 — 不支持多版位组合，除非用户只选了这一个版位
const nonMultiSet = new Set(non_multi_site_set ?? []);
const filteredSiteSet = intersectedSiteSet.length === 1
  ? intersectedSiteSet.filter((s) => s !== "SITE_SET_SEARCH_SCENE")
  : intersectedSiteSet.filter((s) => s !== "SITE_SET_SEARCH_SCENE" && !nonMultiSet.has(s));

const filtering = [];

// ── site_set → IN ──
if (filteredSiteSet.length > 0) {
  filtering.push({
    field: "site_set",
    operator: "IN",
    values: filteredSiteSet,
  });
}

// ── access_status — 只要已完成接入的 ──
filtering.push({ field: "access_status", operator: "IN", values: ["ACCESS_STATUS_COMPLETED"] });

// ── campaign_type — 展示广告 ──
filtering.push({ field: "campaign_type", operator: "EQUALS", values: ["CAMPAIGN_TYPE_NORMAL"] });

// ── promoted_object_type — 从四元组推导 ──
if (marketing_carrier_type != null) {
  const productType = deriveProductType(
    marketing_carrier_type,
    0, // delivery_scene: 常规广告固定为 0
    marketing_target_type ?? null,
    marketing_goal ?? null,
  );
  if (productType != null) {
    filtering.push({ field: "promoted_object_type", operator: "EQUALS", values: [String(productType)] });
  }
}

// ── promoted_object_id — 推广载体 ID ──
if (marketing_carrier_id != null) {
  filtering.push({ field: "promoted_object_id", operator: "EQUALS", values: [String(marketing_carrier_id)] });
}

// // ── create_source_type — 平台创建 ──
// filtering.push({ field: "create_source_type", operator: "EQUALS", values: ["PLATFORM"] });

// 仅当明确指定 PLATFORM 或 SELF_CREATED 时才传，UNLIMIT 或未传时不传（返回全部）
if (create_source_type && create_source_type !== 'UNLIMIT') {
  filtering.push({ field: "create_source_type", operator: "EQUALS", values: [create_source_type] });
}

// ── 四元组参数（传枚举字符串 key） ──

if (marketing_goal != null) {
  filtering.push({ field: "marketing_goal", operator: "EQUALS", values: [marketing_goal] });
}
if (marketing_sub_goal != null) {
  filtering.push({ field: "marketing_sub_goal", operator: "EQUALS", values: [marketing_sub_goal] });
}
if (marketing_carrier_type != null) {
  filtering.push({ field: "marketing_carrier_type", operator: "EQUALS", values: [marketing_carrier_type] });
}
if (marketing_target_type != null) {
  filtering.push({ field: "marketing_target_type", operator: "EQUALS", values: [marketing_target_type] });
}

// ── 条件字段 ──

// cost_type — 由 bid_mode 转换
if (inputBidMode != null) {
  const costType = BID_MODE_TO_COST_TYPE[inputBidMode];
  if (costType) {
    filtering.push({ field: "cost_type", operator: "EQUALS", values: [costType] });
  }
}

// live_video_mode / live_video_sub_mode — 视频号场景
if (marketing_carrier_type != null) {
  const liveMode = deriveLiveVideoMode(marketing_carrier_type);
  if (liveMode != null) {
    filtering.push({ field: "live_video_mode", operator: "EQUALS", values: [String(liveMode.live_video_mode)] });
    filtering.push({ field: "live_video_sub_mode", operator: "EQUALS", values: [String(liveMode.live_video_sub_mode)] });
  }
}

// ─── 分页查询（新接口 page_size 最大 100） ───

const PAGE_SIZE = 100;
let allItems = [];
let page = 1;
let hasMore = true;

while (hasMore) {
  const result = await callApi({
    method: "GET",
    path: "/v3.0/conversions/get",
    accountId: String(account_id),
    params: {
      account_id: parseInt(account_id, 10),
      filtering,
      page,
      page_size: PAGE_SIZE,
      fields: [
        "conversion_id",
        "conversion_name",
        "optimization_goal",
        "deep_behavior_optimization_goal",
        "deep_worth_optimization_goal",
        "deep_worth_advanced_goal",
        "deep_behavior_advanced_goal",
        "access_status",
        "conversion_scene",
        "create_source_type",
      ],
    },
  });

  if (!result.success) {
    if (allItems.length > 0) break;
    console.log(JSON.stringify({ error: result.error?.message || "API 调用失败", detail: result.error }));
    process.exit(1);
  }

  const data = result.data?.data ?? result.data ?? {};
  const list = data.list ?? [];
  allItems.push(...list);

  const pageInfo = data.page_info ?? {};
  const totalPage = pageInfo.total_page ?? 1;
  if (page >= totalPage || list.length < PAGE_SIZE) {
    hasMore = false;
  } else {
    page++;
  }
}

// ─── 处理返回数据 ───
// v3.0 新接口返回结构（深度转化字段均为 enum 枚举字符串）：
//   optimization_goal:                枚举字符串（如 "OPTIMIZATIONGOAL_APP_ACTIVATE"）
//   deep_behavior_optimization_goal:  深度优化行为目标
//   deep_worth_optimization_goal:     深度优化 ROI 目标
//   deep_worth_advanced_goal:         强化 ROI 目标
//   deep_behavior_advanced_goal:      加强优化行为目标
// access_status 已在 filtering 中强制为 COMPLETED，无需二次过滤

const isValidDeepGoal = (v) => v != null && v !== "" && v !== "OPTIMIZATIONGOAL_NONE";

const goals = allItems.map((item) => {
  // 按优先级检测 4 种深度转化类型（互斥，仅可填写其中一个）
  let deepConversionType = null;
  let deepConversionGoal = null;

  if (isValidDeepGoal(item.deep_worth_optimization_goal)) {
    deepConversionType = "DEEP_CONVERSION_WORTH";
    deepConversionGoal = item.deep_worth_optimization_goal;
  } else if (isValidDeepGoal(item.deep_worth_advanced_goal)) {
    deepConversionType = "DEEP_CONVERSION_WORTH_ADVANCED";
    deepConversionGoal = item.deep_worth_advanced_goal;
  } else if (isValidDeepGoal(item.deep_behavior_optimization_goal)) {
    deepConversionType = "DEEP_CONVERSION_BEHAVIOR";
    deepConversionGoal = item.deep_behavior_optimization_goal;
  } else if (isValidDeepGoal(item.deep_behavior_advanced_goal)) {
    deepConversionType = "DEEP_CONVERSION_BEHAVIOR_ADVANCED";
    deepConversionGoal = item.deep_behavior_advanced_goal;
  }

  const hasDeepConversion = deepConversionType !== null;

  const goal = {
    conversion_id: item.conversion_id,
    name: item.conversion_name ?? "",
    bid_mode: "BID_MODE_OCPM",
    has_deep_conversion: hasDeepConversion,
  };

  if (item.optimization_goal) {
    goal.optimization_goal = item.optimization_goal;
  }

  if (item.create_source_type) {
    goal.create_source_type = item.create_source_type;
  }

  if (hasDeepConversion) {
    goal.deep_conversion_type = deepConversionType;
    goal.deep_conversion_goal = deepConversionGoal;
  }

  return goal;
});

console.log(JSON.stringify({ goals }, null, 2));
