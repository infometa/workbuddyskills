#!/usr/bin/env node
/**
 * get-daily-budget.mjs — 查询广告主账户日预算
 *
 * 调用 GET /v3.0/advertiser_daily_budget/get
 * 固定返回全部三个字段：account_id、daily_budget、min_daily_budget
 *
 * 入参: '{"account_id": "<ACCOUNT_ID>"}'
 * 必填: account_id
 *
 * 输出（成功）:
 * {
 *   "account_id": 123456789,
 *   "daily_budget": 100000,       // 单位：分（100000分 = 1000元）
 *   "min_daily_budget": 50000     // 单位：分，当前可设置的最低日预算（基于今日消耗估算）
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
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数，如 '{\"account_id\":\"123456\"}'");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}。请检查引号转义是否适配当前终端（Bash/Zsh 用单引号包裹，Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义）` },
  }));
  process.exit(1);
}

// ─── 必填校验 ───

const { account_id } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/advertiser_daily_budget/get",
  accountId: String(account_id),
  params: {
    account_id: parseInt(account_id, 10),
    fields: ["account_id", "daily_budget", "min_daily_budget"],
  },
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
  account_id: data.account_id,
  daily_budget: data.daily_budget,       // 单位：分，0 表示不限预算
  min_daily_budget: data.min_daily_budget, // 单位：分，基于今日消耗估算，供降预算时参考
}, null, 2));
