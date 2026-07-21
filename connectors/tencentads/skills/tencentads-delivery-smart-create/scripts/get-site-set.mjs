#!/usr/bin/env node
/**
 * get-site-set.mjs — 获取智投可用版位列表
 *
 * 调用 /v3.0/site_set_list/get（新接口），返回自动版位列表。
 *
 * 入参（统一使用字符串枚举 key）:
 * '{
 *   "account_id": "<ID>",
 *   "marketing_goal": "MARKETING_GOAL_USER_GROWTH",
 *   "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
 *   "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
 *   "marketing_carrier_type": "MARKETING_CARRIER_TYPE_WECHAT_MINI_GAME"
 * }'
 *
 * 输出:
 * {
 *   "auto_site_set": ["SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION", ...]
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

const params = {
  account_id: parseInt(account_id, 10),
  // 必传枚举字段
  bid_mode: "BID_MODE_OCPM",
  buying_type: "BUYING_TYPE_AUCTION",
  campaign_type: "CAMPAIGN_TYPE_NORMAL",
};

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

// ─── 提取 auto_site_set ───
// 新接口直接返回枚举字符串的 site_id，无需数值→枚举转换

const data = result.data?.data ?? result.data ?? {};
const siteSetList = data.site_set_list ?? data.list ?? [];

// 提取自动版位（support_auto_site_set=true 且未禁用的）
let autoSiteSet = siteSetList
  .filter((item) => !item.is_disabled && item.support_auto_site_set)
  .map((item) => item.site_id)
  .filter((id) => id != null && id !== "");

// 如果没有标记 support_auto_site_set，则取所有未禁用的版位
if (autoSiteSet.length === 0) {
  autoSiteSet = siteSetList
    .filter((item) => !item.is_disabled)
    .map((item) => item.site_id)
    .filter((id) => id != null && id !== "");
}

if (autoSiteSet.length === 0) {
  console.log(JSON.stringify({
    error: "未找到 auto_site_set 数据，请检查 API 返回",
    raw_keys: data ? Object.keys(data) : null,
  }));
  process.exit(1);
}

console.log(JSON.stringify({ auto_site_set: autoSiteSet }, null, 2));
