#!/usr/bin/env node
/**
 * bidword-add.mjs — Create keywords (bidwords)
 *
 * Calls POST /v3.0/bidword/add
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/bidword/add
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id, list
 *
 * list: Array of bidword objects (min 1, max 1000), each containing:
 *   - adgroup_id (int64, required): Ad group ID
 *   - bidword (string, required): Keyword text (1-20 full-width chars / 40 half-width chars, max 60 bytes)
 *   - match_type (enum, required): Match type
 *       EXACT_MATCH (精确匹配), WIDE_MATCH (广泛匹配), WORD_MATCH (词匹配), PHRASE_MATCH (短语匹配)
 *   - bid_price (integer, optional): Keyword bid in cents (1-99999)
 *   - use_group_price (enum, optional): Whether to use group bid
 *       USE_GROUP_PRICE, NOT_USE_GROUP_PRICE
 *   - configured_status (enum, optional): Pause status
 *       KEYWORD_STATUS_NORMAL, KEYWORD_STATUS_SUSPEND
 *   - dynamic_creative_id (integer, optional): Creative ID
 *   - pc_landing_page_info (struct, optional): Landing page info
 *
 * Output (success):
 * { "success": true, "success_list": [{ "index": 0, "bidword_id": 123, "bidword": "...", ... }], "error_list": [...] }
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
  console.log(JSON.stringify({ success: false, error: { message: `Parameter parsing failed: ${err.message}. Please check: 1) JSON params are complete; 2) quote escaping matches your terminal (Bash/Zsh/Git Bash use single quotes, Windows CMD use double quotes + backslash escape, PowerShell 5.x requires --% or use --base64)` } }));
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
const VALID_USE_GROUP_PRICE = new Set(["USE_GROUP_PRICE", "NOT_USE_GROUP_PRICE"]);
const VALID_CONFIGURED_STATUS = new Set(["KEYWORD_STATUS_NORMAL", "KEYWORD_STATUS_SUSPEND"]);

for (let i = 0; i < input.list.length; i++) {
  const item = input.list[i];

  // adgroup_id required
  if (item.adgroup_id == null || item.adgroup_id === "") {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].adgroup_id is required` } }));
    process.exit(1);
  }
  toSafeInt(item.adgroup_id, `list[${i}].adgroup_id`);

  // bidword required
  if (!item.bidword || typeof item.bidword !== "string" || item.bidword.trim() === "") {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].bidword is required and must be a non-empty string` } }));
    process.exit(1);
  }
  if (Buffer.byteLength(item.bidword, "utf8") > 60) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].bidword exceeds max length of 60 bytes` } }));
    process.exit(1);
  }

  // match_type required
  if (!item.match_type || !VALID_MATCH_TYPES.has(item.match_type)) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].match_type is required and must be one of: ${[...VALID_MATCH_TYPES].join(", ")}` } }));
    process.exit(1);
  }

  // bid_price optional validation
  if (item.bid_price != null) {
    const price = parseInt(item.bid_price, 10);
    if (!Number.isInteger(price) || price < 1 || price > 99999) {
      console.log(JSON.stringify({ success: false, error: { message: `list[${i}].bid_price must be an integer between 1 and 99999, got: ${JSON.stringify(item.bid_price)}` } }));
      process.exit(1);
    }
  }

  // use_group_price optional validation
  if (item.use_group_price != null && !VALID_USE_GROUP_PRICE.has(item.use_group_price)) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}].use_group_price must be one of: ${[...VALID_USE_GROUP_PRICE].join(", ")}` } }));
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
    const entry = {
      adgroup_id: parseInt(item.adgroup_id, 10),
      bidword: item.bidword.trim(),
      match_type: item.match_type,
    };
    if (item.bid_price != null) entry.bid_price = parseInt(item.bid_price, 10);
    if (item.use_group_price != null) entry.use_group_price = item.use_group_price;
    if (item.configured_status != null) entry.configured_status = item.configured_status;
    if (item.dynamic_creative_id != null) entry.dynamic_creative_id = parseInt(item.dynamic_creative_id, 10);
    if (item.pc_landing_page_info != null) entry.pc_landing_page_info = item.pc_landing_page_info;
    return entry;
  }),
};

// ─── Call API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/bidword/add",
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
