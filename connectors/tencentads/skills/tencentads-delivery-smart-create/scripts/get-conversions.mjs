#!/usr/bin/env node
/**
 * get-conversions.mjs — 获取智投转化目标列表
 *
 * 调用 /v3.0/conversions/get（新接口），通过 filtering 传入投放上下文参数，
 * 标注哪些含深度转化目标，裁剪无关字段。
 *
 * 入参（统一使用字符串枚举 key）:
 * '{
 *   "account_id": "<ID>",
 *   "delivery_scene": <数值>,
 *   "site_set": ["SITE_SET_WECHAT", ...],
 *   "marketing_goal": "MARKETING_GOAL_USER_GROWTH",               // 字符串枚举
 *   "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",           // 字符串枚举
 *   "marketing_carrier_type": "MARKETING_CARRIER_TYPE_WECHAT_MINI_GAME",  // 字符串枚举
 *   "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",    // 字符串枚举
 *   "create_source_type": "PLATFORM"                              // 可选，PLATFORM=平台预置 / SELF_CREATED=自建转化，不传则返回全部
 * }'
 *
 * 注意：
 * - 四元组字段统一传字符串枚举 key，脚本内部自动转为数值
 * - product_type 不需要传入，由 marketing_carrier_type + delivery_scene 自动推导
 *
 * 输出:
 * {
 *   "goals": [
 *     {
 *       "conversion_id": 12345,
 *       "name": "小游戏注册",
 *       "bid_mode": "BID_MODE_OCPM",
 *       "has_deep_conversion": false,
 *       "create_source_type": "PLATFORM"           // PLATFORM=平台预置 / SELF_CREATED=自建转化
 *     },
 *     {
 *       "conversion_id": 12346,
 *       "name": "ROI优化",
 *       "bid_mode": "BID_MODE_OCPM",
 *       "has_deep_conversion": true,
 *       "deep_conversion_type": "DEEP_CONVERSION_WORTH",
 *       "deep_conversion_worth_goal": "OPTIMIZATIONGOAL_MONETIZATION_ROAS_7DAY",
 *       "create_source_type": "SELF_CREATED"
 *     }
 *   ]
 * }
 */

import { callApi, deriveProductType, deriveLiveVideoMode } from "tencentads-cli";

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
  delivery_scene,
  site_set,
  marketing_goal,
  marketing_sub_goal,
  marketing_carrier_type,
  marketing_target_type,
  create_source_type,
} = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (delivery_scene == null) {
  console.log(JSON.stringify({ error: "missing required field: delivery_scene (数值)" }));
  process.exit(1);
}
if (!site_set || !Array.isArray(site_set)) {
  console.log(JSON.stringify({ error: "missing required field: site_set (数组，来自 get-site-set.mjs 返回)" }));
  process.exit(1);
}

// ─── 构造 filtering 数组 ───
// 新接口 /v3.0/conversions/get 使用 filtering: [{field, operator, values}] 结构
// 按后端实际逻辑：product_type 和 site_set 必传，access_status 强制 COMPLETED

const filtering = [];

// ── 必传字段 ──

// product_type（必传）— 由 marketing_carrier_type + delivery_scene 自动推导
// if (marketing_carrier_type != null) {
//   const productType = deriveProductType(marketing_carrier_type, Number(delivery_scene), marketing_target_type);
//   if (productType != null) {
//     filtering.push({ field: "product_type", operator: "EQUALS", values: [String(productType)] });
//   }
// }

// site_set（必传）→ IN，传枚举字符串 key
if (site_set.length > 0) {
  filtering.push({
    field: "site_set",
    operator: "IN",
    values: site_set,
  });
}

// access_status — 后端 Service 层强制加入
filtering.push({ field: "access_status", operator: "IN", values: ["ACCESS_STATUS_COMPLETED"] });

// ── 固定字段 ──

// campaign_type 固定为 2（展示广告）
filtering.push({ field: "campaign_type", operator: "EQUALS", values: ["CAMPAIGN_TYPE_NORMAL"] });

// 仅当明确指定 PLATFORM 或 SELF_CREATED 时才传，UNLIMIT 或未传时不传（返回全部）
if (create_source_type && create_source_type !== 'UNLIMIT') {
  filtering.push({ field: "create_source_type", operator: "EQUALS", values: [create_source_type] });
}

// marketing_scene — 智投场景固定 DELIVERY_V3（V3 广告统一使用此值）
// filtering.push({ field: "marketing_scene", operator: "EQUALS", values: ["DELIVERY_V3"] });

// cost_type — 智投固定 oCPM
// filtering.push({ field: "cost_type", operator: "EQUALS", values: ["COST_TYPE_OCPM"] });

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
// 新接口返回结构：
//   optimization_goal: 枚举字符串（如 "OPTIMIZATIONGOAL_APP_ACTIVATE"）
//   deep_behavior_optimization_goal: 枚举字符串（深度行为优化目标）
//   deep_worth_optimization_goal: 枚举字符串（深度价值优化 ROI 目标）
// access_status 已在 filtering 中强制为 COMPLETED，无需二次过滤

const goals = allItems.map((item) => {
  const hasDeepBehavior = item.deep_behavior_optimization_goal != null
    && item.deep_behavior_optimization_goal !== ""
    && item.deep_behavior_optimization_goal !== "OPTIMIZATIONGOAL_NONE";
  const hasDeepWorth = item.deep_worth_optimization_goal != null
    && item.deep_worth_optimization_goal !== ""
    && item.deep_worth_optimization_goal !== "OPTIMIZATIONGOAL_NONE";
  const hasDeepConversion = hasDeepBehavior || hasDeepWorth;

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

  if (hasDeepWorth) {
    goal.deep_conversion_type = "DEEP_CONVERSION_WORTH";
    goal.deep_conversion_worth_goal = item.deep_worth_optimization_goal;
  } else if (hasDeepBehavior) {
    goal.deep_conversion_type = "DEEP_CONVERSION_BEHAVIOR";
    goal.deep_conversion_behavior_goal = item.deep_behavior_optimization_goal;
  }

  return goal;
});

console.log(JSON.stringify({ goals }, null, 2));
