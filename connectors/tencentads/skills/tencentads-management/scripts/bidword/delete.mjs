#!/usr/bin/env node
/**
 * bidword-delete.mjs — Delete keywords (bidwords)
 *
 * Calls POST /v3.0/bidword/delete
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/bidword/delete
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id, list
 *
 * list: Array of bidword IDs (integer[]) to delete (min 1, max 1000)
 *   e.g. [51213, 51214, 51215]
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
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: list (must be a non-empty array of bidword IDs, max 1000)" } }));
  process.exit(1);
}
if (input.list.length > 1000) {
  console.log(JSON.stringify({ success: false, error: { message: "list exceeds max length of 1000" } }));
  process.exit(1);
}

// Validate each ID in the list
for (let i = 0; i < input.list.length; i++) {
  const id = parseInt(input.list[i], 10);
  if (!Number.isInteger(id) || id <= 0) {
    console.log(JSON.stringify({ success: false, error: { message: `list[${i}] must be a valid positive integer (bidword_id), got: ${JSON.stringify(input.list[i])}` } }));
    process.exit(1);
  }
}

// ─── Build request body ───

const { account_id, list } = input;

const body = {
  account_id: toSafeInt(account_id, "account_id"),
  list: list.map(id => parseInt(id, 10)),
};

// ─── Call API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/bidword/delete",
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
