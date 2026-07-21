#!/usr/bin/env node
/**
 * negativewords-update.mjs — Update negative keywords for an adgroup
 *
 * Calls POST /v3.0/adgroup_negativewords/update
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/adgroup_negativewords/update
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id, adgroup_id, phrase_negative_words, exact_negative_words
 *
 * Parameters:
 *   - account_id (integer, required): Advertiser account ID
 *   - adgroup_id (int64, required): Ad group ID
 *   - phrase_negative_words (string[], required): Phrase negative keywords (full replacement)
 *       Each word: 1-20 full-width chars (max 150 bytes), array min 0, max 900
 *   - exact_negative_words (string[], required): Exact negative keywords (full replacement)
 *       Each word: 1-20 full-width chars (max 150 bytes), array min 0, max 900
 *
 * Note: This is a full replacement operation. Pass the complete list of negative words.
 *
 * Output (success):
 * {
 *   "success": true,
 *   "adgroup_id": 123,
 *   "status": "OPER_SUCCESS",
 *   "duplicate_words": { "phrase_negative_words": [], "exact_negative_words": [] },
 *   "exceed_length_words": { "phrase_negative_words": [], "exact_negative_words": [] },
 *   "exceed_limit_words": { "phrase_negative_words": [], "exact_negative_words": [] },
 *   "has_special_words": { "phrase_negative_words": [], "exact_negative_words": [] },
 *   "success_words": { "phrase_negative_words": [...], "exact_negative_words": [...] }
 * }
 *   status: OPER_SUCCESS (all succeeded) or OPER_FAIL (some failed)
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

if (input.adgroup_id == null || input.adgroup_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: adgroup_id" } }));
  process.exit(1);
}
toSafeInt(input.adgroup_id, "adgroup_id");

// phrase_negative_words required (can be empty array)
if (!Array.isArray(input.phrase_negative_words)) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: phrase_negative_words (must be a string array)" } }));
  process.exit(1);
}
if (input.phrase_negative_words.length > 900) {
  console.log(JSON.stringify({ success: false, error: { message: "phrase_negative_words exceeds max length of 900" } }));
  process.exit(1);
}
for (let i = 0; i < input.phrase_negative_words.length; i++) {
  const w = input.phrase_negative_words[i];
  if (typeof w !== "string" || w.trim() === "") {
    console.log(JSON.stringify({ success: false, error: { message: `phrase_negative_words[${i}] must be a non-empty string` } }));
    process.exit(1);
  }
  if (Buffer.byteLength(w, "utf8") > 150) {
    console.log(JSON.stringify({ success: false, error: { message: `phrase_negative_words[${i}] exceeds max length of 150 bytes` } }));
    process.exit(1);
  }
}

// exact_negative_words required (can be empty array)
if (!Array.isArray(input.exact_negative_words)) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: exact_negative_words (must be a string array)" } }));
  process.exit(1);
}
if (input.exact_negative_words.length > 900) {
  console.log(JSON.stringify({ success: false, error: { message: "exact_negative_words exceeds max length of 900" } }));
  process.exit(1);
}
for (let i = 0; i < input.exact_negative_words.length; i++) {
  const w = input.exact_negative_words[i];
  if (typeof w !== "string" || w.trim() === "") {
    console.log(JSON.stringify({ success: false, error: { message: `exact_negative_words[${i}] must be a non-empty string` } }));
    process.exit(1);
  }
  if (Buffer.byteLength(w, "utf8") > 150) {
    console.log(JSON.stringify({ success: false, error: { message: `exact_negative_words[${i}] exceeds max length of 150 bytes` } }));
    process.exit(1);
  }
}

// ─── Build request body ───

const { account_id, adgroup_id, phrase_negative_words, exact_negative_words } = input;

const body = {
  account_id: toSafeInt(account_id, "account_id"),
  adgroup_id: parseInt(adgroup_id, 10),
  phrase_negative_words,
  exact_negative_words,
};

// ─── Call API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/adgroup_negativewords/update",
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

console.log(JSON.stringify({
  success: true,
  adgroup_id: data.adgroup_id,
  status: data.status,
  duplicate_words: data.duplicate_words ?? { phrase_negative_words: [], exact_negative_words: [] },
  exceed_length_words: data.exceed_length_words ?? { phrase_negative_words: [], exact_negative_words: [] },
  exceed_limit_words: data.exceed_limit_words ?? { phrase_negative_words: [], exact_negative_words: [] },
  has_special_words: data.has_special_words ?? { phrase_negative_words: [], exact_negative_words: [] },
  success_words: data.success_words ?? { phrase_negative_words: [], exact_negative_words: [] },
}, null, 2));
