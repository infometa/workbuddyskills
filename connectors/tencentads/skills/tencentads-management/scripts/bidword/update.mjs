#!/usr/bin/env node
/**
 * bidword-update.mjs — Update keywords (bidwords)
 *
 * Calls POST /v3.0/bidword/update
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/bidword/update
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id, list
 *
 * list: Array of bidword update objects (min 1, max 1000), each containing:
 *   - bidword_id (integer, required): Keyword ID
 *   - bid_price (integer, optional): Keyword bid in cents (1-99999)
 *   - bid_mode (enum, optional): Bid mode
 *       BID_MODE_CPC, BID_MODE_CPA, BID_MODE_CPS, BID_MODE_CPM, BID_MODE_OCPC, BID_MODE_OCPM
 *   - use_group_price (enum, optional): Whether to use group bid
 *       USE_GROUP_PRICE, NOT_USE_GROUP_PRICE
 *   - price_update_type (enum, optional): Price update type
 *       RAISE_PRICE_VALUE, RAISE_PRICE_PERCENT
 *   - raise_price (integer, optional): Price adjustment amount (-99999 to 99999)
 *   - match_type (enum, optional): Match type
 *       EXACT_MATCH, WIDE_MATCH, WORD_MATCH, PHRASE_MATCH
 *   - configured_status (enum, optional): Pause status
 *       KEYWORD_STATUS_NORMAL, KEYWORD_STATUS_SUSPEND
 *   - dynamic_creative_id (integer, optional): Creative ID
 *   - pc_landing_page_info (struct, optional): Landing page info
 *
 * Output (success):
 * { "success": true, "success_list": [{ "index": 0, "bidword_id": 123, ... }], "error_list": [...] }
 *
 * Output (failure):
 * { "success": false, "error": { "message": "..." } }
 */

import { callApi } from "tencentads-cli";

// ─── Helpers ───

function toSafeInt(value, fieldName) {
  const n = parseInt(value, 10);
  if (!Number.isInteger(n) || n <= 0) {
    console.log(JSON.stringify({ success: false, error: { message: `${fieldName} must be a valid positive integer, got: ${JSON.stringify(value)}` } }));
    process.exit(1);
  }
  return n;
}

// ─── Input parsing ───

let input;
try {
  let raw;
  if (process.argv[2] === "--base64") {
    const b64 = process.argv[3];
    if (!b64) throw new Error("--base64 requires a Base64-encoded JSON string");
    raw = Buffer.from(b64, "base64").toString("utf-8");
  } else {
    raw = process.argv[2] != null
      ? process.argv[2]
      : await new Promise(res => {
          let buf = '';
          process.stdin.setEncoding('utf8');
          process.stdin.on('data', d => (buf += d));
          process.stdin.on('end', () => res(buf.trim()));
        });
  }
  if (!raw) throw new Error("Missing input, please provide JSON params");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `Parameter parsing failed: ${err.message}` } }));
  process.exit(1);
}

// ─── Validation ───

if (input.account_id == null || input.account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}
toSafeInt(input.account_id, "account_id");

if (!Array.isArray(input.list) || input.list.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: list (must be a non-empty array, max 1000 items)" } }));
  process.exit(1);
}
if (input.list.length > 1000) {
  console.log(JSON.stringify({ success: false, error: { message: "list exceeds max length of 1000" } }));
  process.exit(1);
}

const VALID_MATCH_TYPES = new Set(["EXACT_MATCH", "WIDE_MATCH", "WORD_MATCH", "PHRASE_MATCH"]);
const VALID_CONFIGURED_STATUS = new Set(["KEYWORD_STATUS_NORMAL", "KEYWORD_STATUS_SUSPEND"]);

for (let i = 0; i < input.list.length; i++) {
  const item = input.list[i];

  // bidword_id required
  if (item.bidword_id == null) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].bidword_id is required` } }));
    process.exit(1);
  }
  toSafeInt(item.bidword_id, `list[${i}].bidword_id`);

  // bid_price optional validation
  if (item.bid_price != null) {
    const price = parseInt(item.bid_price, 10);
    if (!Number.isInteger(price) || price < 1 || price > 99999) {
      console.log(JSON.stringify({ success: false, error: { message: `list[${i}].bid_price must be an integer between 1 and 99999` } }));
      process.exit(1);
    }
  }

  // match_type optional validation
  if (item.match_type != null && !VALID_MATCH_TYPES.has(item.match_type)) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].match_type must be one of: ${[...VALID_MATCH_TYPES].join(", ")}` } }));
    process.exit(1);
  }

  // configured_status optional validation
  if (item.configured_status != null && !VALID_CONFIGURED_STATUS.has(item.configured_status)) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].configured_status must be one of: ${[...VALID_CONFIGURED_STATUS].join(", ")}` } }));
    process.exit(1);
  }
}

// ─── Build request body ───

const { account_id, list } = input;

const body = {
  account_id: toSafeInt(account_id, "account_id"),
  list: list.map((item) => {
    const entry = { bidword_id: parseInt(item.bidword_id, 10) };
    if (item.bid_price != null) entry.bid_price = parseInt(item.bid_price, 10);
    if (item.bid_mode != null) entry.bid_mode = item.bid_mode;
    if (item.use_group_price != null) entry.use_group_price = item.use_group_price;
    if (item.price_update_type != null) entry.price_update_type = item.price_update_type;
    if (item.raise_price != null) entry.raise_price = parseInt(item.raise_price, 10);
    if (item.match_type != null) entry.match_type = item.match_type;
    if (item.configured_status != null) entry.configured_status = item.configured_status;
    if (item.dynamic_creative_id != null) entry.dynamic_creative_id = parseInt(item.dynamic_creative_id, 10);
    if (item.pc_landing_page_info != null) entry.pc_landing_page_info = item.pc_landing_page_info;
    return entry;
  }),
};

// ─── Call API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/bidword/update",
  accountId: String(account_id),
  body,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API call failed",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
const successList = data.success_list ?? [];
const errorList = data.error_list ?? [];

console.log(JSON.stringify({ success: true, success_list: successList, error_list: errorList }, null, 2));
