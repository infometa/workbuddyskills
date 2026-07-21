#!/usr/bin/env node
/**
 * update-daily-budget.mjs — 修改广告主账户日预算
 *
 * 调用 POST /v3.0/advertiser_daily_budget/update
 *
 * 入参: '{"account_id": "<ACCOUNT_ID>", "daily_budget": <分>, "use_min_daily_budget": false}'
 * 必填: account_id, daily_budget
 * 选填: use_min_daily_budget（默认 false）
 *
 * daily_budget 取值规则（单位：分）：
 *   - 0 = 不限预算
 *   - 非零时范围：5000 ~ 4000000000（即 50元 ~ 4000万元）
 *   - 每次调整幅度至少 5000 分（50元）
 *   - 微信公众号/小程序账户每次最少提升 50000 分（500元）
 *   - 不得低于今日消耗 × 1.2 + 冻结金额
 *   - 不得低于今日消耗 + 5000 分
 *
 * use_min_daily_budget:
 *   - false（默认）：严格按传入的 daily_budget 执行，若因消耗限制无法降到目标值则报错返回
 *   - true：若降预算失败，自动降至系统允许的最低值（可能高于目标值，即"想降反而升"）
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "account_id": 123456789,
 *   "daily_budget": 100000,         // 实际设置后的日预算（单位：分）
 *   "use_min_daily_budget": false   // 是否触发了最低值兜底
 * }
 *
 * 输出（失败）:
 * {
 *   "success": false,
 *   "error": { "code": 1000014, "message": "...", "message_cn": "..." }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数，如 '{\"account_id\":\"123456\",\"daily_budget\":100000}'");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}。请检查引号转义是否适配当前终端（Bash/Zsh 用单引号包裹，Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义）` },
  }));
  process.exit(1);
}

// ─── 必填校验 ───

const { account_id, daily_budget, use_min_daily_budget } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

if (daily_budget == null) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: daily_budget（单位：分，传 0 表示不限预算）" } }));
  process.exit(1);
}

const budgetInt = parseInt(daily_budget, 10);
if (isNaN(budgetInt) || budgetInt < 0) {
  console.log(JSON.stringify({ success: false, error: { message: `daily_budget 必须为非负整数（单位：分），当前值: ${daily_budget}` } }));
  process.exit(1);
}

// 非零时校验范围下限（5000 分 = 50 元）
if (budgetInt !== 0 && budgetInt < 5000) {
  console.log(JSON.stringify({ success: false, error: { message: `daily_budget 非零时最小值为 5000 分（50元），当前值: ${budgetInt} 分` } }));
  process.exit(1);
}

// 非零时校验范围上限（4000000000 分 = 4000万元）
if (budgetInt > 4000000000) {
  console.log(JSON.stringify({ success: false, error: { message: `daily_budget 最大值为 4000000000 分（4000万元），当前值: ${budgetInt} 分` } }));
  process.exit(1);
}

// ─── 构造请求体 ───

const body = {
  account_id: parseInt(account_id, 10),
  daily_budget: budgetInt,
};

// use_min_daily_budget 仅在明确传 true 时才带上，避免不必要的字段
if (use_min_daily_budget === true) {
  body.use_min_daily_budget = true;
}

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/advertiser_daily_budget/update",
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
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ─── 提取并输出结果 ───

const data = result.data?.data ?? result.data ?? {};

console.log(JSON.stringify({
  success: true,
  account_id: data.account_id,
  daily_budget: data.daily_budget,                  // 实际设置后的日预算（分）
  use_min_daily_budget: data.use_min_daily_budget ?? false, // 是否触发了最低值兜底
}, null, 2));
