#!/usr/bin/env node
/**
 * get-funds.mjs — 获取资金账户信息
 *
 * 调用 GET /v3.0/funds/get
 * 查询指定广告主账户的各类资金账户余额、消耗及状态。
 *
 * 入参: '{"account_id": 123456, "fund_type_list": ["GENERAL_CASH"]}'
 * 必填: account_id
 * 选填: fund_type_list — 按资金账户类型过滤，不传则返回全部类型
 *
 * fund_type 枚举值:
 *   GENERAL_CASH    — 现金账户
 *   GENERAL_SHARED  — 共享账户（所属共享钱包的余额）
 *   GENERAL_GIFT    — 赠金账户
 *   BANK            — 银行账户
 *
 * 输出（成功）:
 * {
 *   "list": [
 *     {
 *       "fund_type": "GENERAL_CASH",
 *       "balance": 120000,            // 余额，单位：分
 *       "bill_deposit_amount": 100,   // 锁定金额，单位：分
 *       "fund_status": "FUND_STATUS_NORMAL",
 *       "realtime_cost": 100          // 今日消耗，单位：分
 *     }
 *   ]
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
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数，如 '{\"account_id\":123456}'");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}` },
  }));
  process.exit(1);
}

// ─── 必填校验 ───

const { account_id, fund_type_list } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

// ─── 可选参数校验 ───

const VALID_FUND_TYPES = new Set(["GENERAL_CASH", "GENERAL_SHARED", "GENERAL_GIFT", "BANK"]);

if (fund_type_list !== undefined) {
  if (!Array.isArray(fund_type_list) || fund_type_list.length === 0) {
    console.log(JSON.stringify({ success: false, error: { message: "fund_type_list 必须为非空数组" } }));
    process.exit(1);
  }
  for (const t of fund_type_list) {
    if (!VALID_FUND_TYPES.has(t)) {
      console.log(JSON.stringify({
        success: false,
        error: { message: `无效的 fund_type: "${t}"，可选值: GENERAL_CASH, GENERAL_SHARED, GENERAL_GIFT, BANK` },
      }));
      process.exit(1);
    }
  }
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/funds/get",
  accountId: String(account_id),
  params: {
    account_id: parseInt(account_id, 10),
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
let list = data.list ?? [];

// 按 fund_type_list 过滤
if (fund_type_list && fund_type_list.length > 0) {
  const filterSet = new Set(fund_type_list);
  list = list.filter((item) => filterSet.has(item.fund_type));
}

console.log(JSON.stringify({ list }, null, 2));
