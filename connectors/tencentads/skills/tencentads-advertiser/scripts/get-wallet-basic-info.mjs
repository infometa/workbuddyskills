#!/usr/bin/env node
/**
 * get-wallet-basic-info.mjs — 通过钱包 ID 查询共享钱包基础信息
 *
 * 调用 GET /v3.0/wallet_basic_info/get
 * 通过钱包 ID 查询共享钱包基础信息，包含余额、代理商、主体、绑定账户、资金信息、监控预警等。
 *
 * 注意：account_id 为代理商 ID，wallet_id 为钱包账号 ID。
 *
 * 入参: '{"account_id": 78384, "wallet_id": 24111993}'
 * 必填: account_id, wallet_id
 *
 * 输出（成功）:
 * {
 *   "wallet_id": 24111993,
 *   "wallet_name": "name",
 *   "balance": 9954999,
 *   "agency_id": 78384,
 *   "agency_name": "腾讯",
 *   "mdm_id": 63444781,
 *   "mdm_name": "mdmName",
 *   "tag_list": ["视频", "tag1"],
 *   "bind_advertiser_cnt": 4,
 *   "binding_account_list": [23870009, 23878247, 23953986, 23954003],
 *   "balance_info_list": [...],
 *   "contact_info_list": [...],
 *   "contact_notify_condition": {...}
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
  if (!raw) throw new Error("缺少入参，请传入 JSON 参数，如 '{\"account_id\":78384,\"wallet_id\":24111993}'");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `参数解析失败: ${err.message}` },
  }));
  process.exit(1);
}

// ─── 必填校验 ───

const { account_id, wallet_id } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id (代理商 ID)" } }));
  process.exit(1);
}

if (wallet_id == null || wallet_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: wallet_id (钱包 ID)" } }));
  process.exit(1);
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/wallet_basic_info/get",
  params: {
    account_id: parseInt(account_id, 10),
    business_id: parseInt(account_id, 10),
    wallet_id: parseInt(wallet_id, 10),
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
const w = data.wallet_info ?? data ?? {};

console.log(JSON.stringify({
  wallet_id: w.wallet_id,
  wallet_name: w.wallet_name,
  balance: w.balance,
  agency_id: w.agency_id,
  agency_name: w.agency_name,
  mdm_id: w.mdm_id,
  mdm_name: w.mdm_name,
  tag_list: w.tag_list ?? [],
  bind_advertiser_cnt: w.bind_advertiser_cnt,
  binding_account_list: w.binding_account_list ?? [],
  balance_info_list: w.balance_info_list ?? [],
  contact_info_list: w.contact_info_list ?? [],
  contact_notify_condition: w.contact_notify_condition ?? null,
}, null, 2));
