#!/usr/bin/env node
/**
 * bidword-get.mjs — Query keywords (bidwords)
 *
 * Calls GET /v3.0/bidword/get
 * Official doc: https://developers.e.qq.com/v3.0/docs/api/bidword/get
 *
 * Input: '<JSON params>' or --base64 <Base64 string>
 * Required: account_id
 * Optional:
 *   filtering - Array of filter objects: [{ field, operator, values }]
 *     Supported fields: bidword_id, adgroup_id, campaign_id, bidword, match_type,
 *       created_time, last_modified_time, delete_time, configured_status, bidword_status
 *   page - Page number (default 1)
 *   page_size - Page size (default 20, max 100)
 *   fields - Array of fields to return
 *
 * Output (success):
 * { "list": [...], "page_info": {...} }
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

// Validate page/page_size if provided
const page = input.page ?? 1;
const page_size = input.page_size ?? 20;
const parsedPage = Number(page);
const parsedPageSize = Number(page_size);
if (!Number.isInteger(parsedPage) || parsedPage < 1) {
  console.log(JSON.stringify({ success: false, error: { message: `page must be a positive integer, got: ${JSON.stringify(page)}` } }));
  process.exit(1);
}
if (!Number.isInteger(parsedPageSize) || parsedPageSize < 1 || parsedPageSize > 100) {
  console.log(JSON.stringify({ success: false, error: { message: `page_size must be a positive integer between 1 and 100, got: ${JSON.stringify(page_size)}` } }));
  process.exit(1);
}

// ─── Build request params ───

const { account_id, filtering, fields } = input;

const params = {
  account_id: toSafeInt(account_id, "account_id"),
  page: parsedPage,
  page_size: parsedPageSize,
};

if (Array.isArray(filtering) && filtering.length > 0) {
  params.filtering = filtering;
}

if (Array.isArray(fields) && fields.length > 0) {
  params.fields = fields;
}

// ─── Call API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/bidword/get",
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
const list = data.list ?? [];
const pageInfo = data.page_info ?? {};

console.log(JSON.stringify({ list, page_info: pageInfo }, null, 2));
