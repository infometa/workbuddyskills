#!/usr/bin/env node
/**
 * get-rules.mjs — 获取常规广告四元组
 *
 * 调用 get_rules_by_advertiser（不传 delivery_scene），内部解析 rules_json（嵌套 JSON 字符串），
 * 将四层嵌套树展开为扁平的组合列表返回。
 *
 * 入参: '{"account_id":"<ID>"}'
 *
 * 输出:
 * {
 *   "combinations": [
 *     {
 *       "marketing_goal": "MARKETING_GOAL_PRODUCT_SALES",
 *       "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
 *       "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
 *       "marketing_carrier_type": "MARKETING_CARRIER_TYPE_JUMP_PAGE",
 *       "product_type": 30
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

const { account_id } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}

// ─── 调用 API ───
// 常规广告不传 delivery_scene，获取默认（非智投）的四元组组合

const result = await callApi({
  method: "POST",
  path: "/v3.0/marketing_target/get_rules_by_advertiser",
  accountId: String(account_id),
  body: {
    account_id: parseInt(account_id, 10),
  },
});

if (!result.success) {
  console.log(JSON.stringify({ error: result.error?.message || "API 调用失败", detail: result.error }));
  process.exit(1);
}

// ─── 解析 rules_json ───

let rulesData;
try {
  const data = result.data;

  // rules_json 可能在 data.data.rules_json 或 data.rules_json
  const rulesJson =
    data?.data?.rules_json ??
    data?.rules_json ??
    null;

  if (!rulesJson) {
    console.log(JSON.stringify({ error: "API 返回中未找到 rules_json 字段", raw: data }));
    process.exit(1);
  }

  // rules_json 是 JSON 字符串，需要二次解析
  rulesData = typeof rulesJson === "string" ? JSON.parse(rulesJson) : rulesJson;
} catch (err) {
  console.log(JSON.stringify({ error: `rules_json 解析失败: ${err.message}` }));
  process.exit(1);
}

// ─── 展开四层嵌套树为扁平组合列表 ───
// 树结构: marketing_goal > marketing_target_type > marketing_sub_goal > marketing_carrier_type > PRODUCT_TYPE

const combinations = [];

for (const [marketingGoal, goalValue] of Object.entries(rulesData)) {
  if (typeof goalValue !== "object" || goalValue === null) continue;

  for (const [marketingTargetType, targetTypeValue] of Object.entries(goalValue)) {
    if (typeof targetTypeValue !== "object" || targetTypeValue === null) continue;

    for (const [marketingSubGoal, subGoalValue] of Object.entries(targetTypeValue)) {
      if (typeof subGoalValue !== "object" || subGoalValue === null) continue;

      for (const [marketingCarrierType, carrierTypeValue] of Object.entries(subGoalValue)) {
        if (typeof carrierTypeValue !== "object" || carrierTypeValue === null) continue;

        const productType = carrierTypeValue?.PRODUCT_TYPE ?? null;

        const combo = {
          marketing_goal: marketingGoal,
          marketing_sub_goal: marketingSubGoal,
          marketing_target_type: marketingTargetType,
          marketing_carrier_type: marketingCarrierType,
        };
        if (productType != null) combo.product_type = productType;
        combinations.push(combo);
      }
    }
  }
}

// ─── 紧凑输出：按 goal 分组，减少体积，只供 Agent 阅读和选择 ───

const subGoalCounts = {};
for (const c of combinations) {
  subGoalCounts[c.marketing_sub_goal] = (subGoalCounts[c.marketing_sub_goal] || 0) + 1;
}
let defaultSubGoal = null;
let maxCount = 0;
for (const [sg, count] of Object.entries(subGoalCounts)) {
  if (count > maxCount) { defaultSubGoal = sg; maxCount = count; }
}

const goals = [];
const byGoal = {};
for (const c of combinations) {
  if (!byGoal[c.marketing_goal]) {
    byGoal[c.marketing_goal] = [];
    goals.push(c.marketing_goal);
  }
  const item = { t: c.marketing_target_type, c: c.marketing_carrier_type };
  if (c.marketing_sub_goal !== defaultSubGoal) item.s = c.marketing_sub_goal;
  if (c.product_type != null) item.pt = c.product_type;
  byGoal[c.marketing_goal].push(item);
}

console.log(JSON.stringify({ goals, total: combinations.length, default_sub_goal: defaultSubGoal, by_goal: byGoal }));
