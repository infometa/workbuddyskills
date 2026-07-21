#!/usr/bin/env node
/**
 * negativewords-get.mjs — Query negative keywords for adgroups
 *
 * Calls GET /v3.0/adgroup_negativewords/get
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/adgroup_negativewords/get
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id, adgroup_ids
 *
 * Parameters:
 *   - account_id (integer, required): Advertiser account ID
 *   - adgroup_ids (integer[], required): Ad group ID list (min 1, max 100)
 *
 * Output (success):
 * { "adgroup_list": [{ "adgroup_id": 123, "phrase_negative_words": [...], "exact_negative_words": [...] }], "adgroup_error_list": [...] }
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

if (!Array.isArray(input.adgroup_ids) || input.adgroup_ids.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: adgroup_ids (must be a non-empty integer array, max 100)" } }));
  process.exit(1);
}
if (input.adgroup_ids.length > 100) {
  console.log(JSON.stringify({ success: false, error: { message: "adgroup_ids exceeds max length of 100" } }));
  process.exit(1);
}
for (let i = 0; i < input.adgroup_ids.length; i++) {
  const id = parseInt(input.adgroup_ids[i], 10);
  if (!Number.isInteger(id) || id <= 0) {
    console.log(JSON.stringify({ success: false, error: { message: `adgroup_ids[${i}] must be a valid positive integer, got: ${JSON.stringify(input.adgroup_ids[i])}` } }));
    process.exit(1);
  }
}

// ─── Build request params ───

const { account_id, adgroup_ids } = input;

const params = {
  account_id: toSafeInt(account_id, "account_id"),
  adgroup_ids: adgroup_ids.map(id => parseInt(id, 10)),
};

// ─── Call API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/adgroup_negativewords/get",
  accountId: String(account_id),
  params,
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
const adgroupList = data.adgroup_list ?? [];
const adgroupErrorList = data.adgroup_error_list ?? [];

console.log(JSON.stringify({ adgroup_list: adgroupList, adgroup_error_list: adgroupErrorList }, null, 2));
