#!/usr/bin/env node
/**
 * get-rules.mjs — 获取智投四元组
 *
 * 调用 get_rules_by_advertiser，内部解析 rules_json（嵌套 JSON 字符串），
 * 将四层嵌套树展开为扁平的组合列表返回。
 *
 * 入参: '{"account_id":"<ID>","delivery_scene":"<smart_delivery_platform枚举值>"}'
 *
 * 输出:
 * {
 *   "combinations": [
 *     {
 *       "marketing_goal": "MARKETING_GOAL_APP_PROMOTED",
 *       "marketing_sub_goal": "MARKETING_SUB_GOAL_APP_INSTALL",
 *       "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
 *       "marketing_carrier_type": "MARKETING_CARRIER_TYPE_MINI_PROGRAM"
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

const { account_id, delivery_scene } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!delivery_scene) {
  console.log(JSON.stringify({ error: "missing required field: delivery_scene (应为 smart_delivery_platform 字符串枚举)" }));
  process.exit(1);
}

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/marketing_target/get_rules_by_advertiser",
  accountId: String(account_id),
  body: {
    account_id: parseInt(account_id, 10),
    delivery_scene: String(delivery_scene),
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

        combinations.push({
          marketing_goal: marketingGoal,
          marketing_sub_goal: marketingSubGoal,
          marketing_target_type: marketingTargetType,
          marketing_carrier_type: marketingCarrierType,
        });
      }
    }
  }
}

console.log(JSON.stringify({ combinations }));
