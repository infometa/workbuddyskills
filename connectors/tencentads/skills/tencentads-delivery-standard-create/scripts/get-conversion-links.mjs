#!/usr/bin/env node
/**
 * get-conversion-links.mjs — 获取常规广告可投放营销链路
 *
 * 调用 /v3.0/conversion_link_asset_available/get，返回可投放的营销链路列表。
 * 常规广告 oCPM/oCPC 场景推荐配置营销链路。
 *
 * 入参:
 * '{
 *   "account_id": "<ID>",
 *   "marketing_goal": "MARKETING_GOAL_USER_GROWTH",
 *   "marketing_target_type": "MARKETING_TARGET_TYPE_APP_ANDROID"
 * }'
 *
 * 输出:
 * {
 *   "links": [
 *     {
 *       "conversion_link_asset_id": 56789,
 *       "name": "APP激活-点击归因",
 *       "desc": "优化目标: 激活"
 *     }
 *   ]
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

const { account_id, marketing_goal, marketing_target_type } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!marketing_goal) {
  console.log(JSON.stringify({ error: "missing required field: marketing_goal" }));
  process.exit(1);
}
if (!marketing_target_type) {
  console.log(JSON.stringify({ error: "missing required field: marketing_target_type" }));
  process.exit(1);
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/conversion_link_asset_available/get",
  accountId: String(account_id),
  params: {
    marketing_goal,
    marketing_target_type,
  },
});

if (!result.success) {
  console.log(JSON.stringify({ error: result.error?.message || "API 调用失败", detail: result.error }));
  process.exit(1);
}

// ─── 处理返回数据 ───

const rawList =
  result.data?.data?.list ??
  result.data?.list ??
  [];

const links = rawList.map((item) => ({
  conversion_link_asset_id: item.conversion_link_asset_id ?? item.id,
  name: item.name ?? "",
  desc: item.desc ?? item.description ?? "",
}));

console.log(JSON.stringify({ links }, null, 2));
