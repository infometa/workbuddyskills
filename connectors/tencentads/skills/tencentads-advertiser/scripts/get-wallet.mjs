#!/usr/bin/env node
/**
 * get-wallet.mjs — 获取钱包信息
 *
 * 调用 GET /v3.0/wallet/get
 * 查询广告主账户所属共享钱包的余额、名称、代理商、主体及绑定账户等信息。
 *
 * 注意：account_id 仅支持广告主账号，不支持代理商 ID。
 *
 * 入参: '{"account_id": 123456}'
 * 必填: account_id
 *
 * 输出（成功）:
 * {
 *   "wallet_id": 24080128,
 *   "wallet_name": "xxx钱包",
 *   "balance": 10021001976591,      // 余额，单位：分
 *   "agency_id": 78384,
 *   "agency_name": "腾讯",
 *   "mdm_id": 51424622,
 *   "mdm_name": "深圳市腾讯计算机系统有限公司",
 *   "tag_list": ["标签"],
 *   "binding_account_list": [5897205],
 *   "bind_advertiser_cnt": 1
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

const { account_id } = input;

if (account_id == null || account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/wallet/get",
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
const w = data.wallet_info ?? data ?? {};

console.log(JSON.stringify({
  wallet_id: w.wallet_id,
  wallet_name: w.wallet_name,
  balance: w.balance,                         // 余额，单位：分
  agency_id: w.agency_id,
  agency_name: w.agency_name,
  mdm_id: w.mdm_id,
  mdm_name: w.mdm_name,
  tag_list: w.tag_list ?? [],
  binding_account_list: w.binding_account_list ?? [],
  bind_advertiser_cnt: w.bind_advertiser_cnt,
}, null, 2));
