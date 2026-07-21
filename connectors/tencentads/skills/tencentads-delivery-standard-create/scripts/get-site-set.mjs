#!/usr/bin/env node
/**
 * get-site-set.mjs — 获取常规广告可用版位列表
 *
 * 调用 /v3.0/site_set_list/get（新接口），返回可用版位和自动版位列表。
 *
 * 入参（统一使用字符串枚举 key）:
 * '{
 *   "account_id": "<ID>",
 *   "marketing_goal": "MARKETING_GOAL_USER_GROWTH",
 *   "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
 *   "marketing_target_type": "MARKETING_TARGET_TYPE_APP_ANDROID",
 *   "marketing_carrier_type": "MARKETING_CARRIER_TYPE_APP_ANDROID",
 *   "product_type": 30          // 可选，来自 get-rules.mjs 返回的 product_type，优先使用
 * }'
 *
 * 输出:
 * {
 *   "available_site_set": ["SITE_SET_MOMENTS", "SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION", ...],
 *   "auto_site_set": ["SITE_SET_MOMENTS", "SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION", ...]
 * }
 */

import { callApi } from "tencentads-cli";

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
  marketing_goal,
  marketing_sub_goal,
  marketing_target_type,
  marketing_carrier_type,
} = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}

// ─── 构造请求参数（新接口统一传枚举字符串） ───

// MPA 多商品广告（商品集 / 微店商品集）
const MPA_TARGET_TYPES = new Set([
  "MARKETING_TARGET_TYPE_COMMODITY_SET",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT_SET",
]);
const isMPA = marketing_target_type != null && MPA_TARGET_TYPES.has(marketing_target_type);

const params = {
  account_id: parseInt(account_id, 10),
  // 必传枚举字段
  bid_mode: "BID_MODE_OCPM",
  buying_type: "BUYING_TYPE_AUCTION",
};

// campaign_type — 常规广告固定展示广告
params.campaign_type = "CAMPAIGN_TYPE_NORMAL";

// MPA 广告
if (isMPA) {
  params.dynamic_ad_type = "DYNAMIC_AD_TYPE_DYNAMIC_CREATIVE";
  params.is_mpa = true;
}

// 四元组参数（枚举字符串直传）
if (marketing_goal != null) params.marketing_goal = marketing_goal;
if (marketing_sub_goal != null) params.marketing_sub_goal = marketing_sub_goal;
if (marketing_target_type != null) params.marketing_target_type = marketing_target_type;
if (marketing_carrier_type != null) params.marketing_carrier_type = marketing_carrier_type;

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/site_set_list/get",
  accountId: String(account_id),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({ error: result.error?.message || "API 调用失败", detail: result.error }));
  process.exit(1);
}

// ─── 提取版位列表 ───
// 新接口直接返回枚举字符串的 site_id，无需数值→枚举转换

const data = result.data?.data ?? result.data ?? {};
const siteSetList = data.site_set_list ?? data.list ?? [];
const enableAutoSwitch = data.enable_auto_switch ?? false;

// 提取可用版位（未禁用的）
const availableSiteSet = siteSetList
  .filter((item) => !item.is_disabled)
  .map((item) => item.site_id)
  .filter((id) => id != null && id !== "");

// 提取不支持多版位组合的版位（site_set_multi: 0 且未禁用的）
const nonMultiSiteSet = siteSetList
  .filter((item) => !item.is_disabled && !item.site_set_multi)
  .map((item) => item.site_id)
  .filter((id) => id != null && id !== "");

// 提取自动版位（support_auto_site_set=true 的）
const autoSiteSet = siteSetList
  .filter((item) => !item.is_disabled && item.support_auto_site_set)
  .map((item) => item.site_id)
  .filter((id) => id != null && id !== "");

// 如果没有标记 support_auto_site_set 的，且 enable_auto_switch 为 true，则 auto = available
const finalAutoSiteSet = autoSiteSet.length > 0 ? autoSiteSet : (enableAutoSwitch ? availableSiteSet : []);

if (availableSiteSet.length === 0 && finalAutoSiteSet.length === 0) {
  console.log(JSON.stringify({
    error: "未找到版位数据，请检查 API 返回",
    raw_keys: data ? Object.keys(data) : null,
  }));
  process.exit(1);
}

console.log(JSON.stringify({
  available_site_set: availableSiteSet,
  auto_site_set: finalAutoSiteSet,
  non_multi_site_set: nonMultiSiteSet,
}, null, 2));
