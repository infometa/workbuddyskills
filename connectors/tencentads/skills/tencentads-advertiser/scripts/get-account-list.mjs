#!/usr/bin/env node
/**
 * get-account-list.mjs — Query account info list associated with the current user_id
 *
 * Calls the user_account_list/get API to retrieve advertiser account information
 * under the authenticated user. Supports fuzzy matching by corporation name and pagination.
 *
 * Input: '{"corporation_name_fuzzy_list":["北京","腾讯"],"page":1,"page_size":10}'
 *
 * All parameters are optional:
 *   - corporation_name_fuzzy_list: Array of strings for fuzzy matching corporation names
 *     (max 2 items, each string length 2~50)
 *   - page: Page number (default: 1)
 *   - page_size: Page size (default: 10, max: 500)
 *
 * Output:
 * {
 *   "list": [
 *     {
 *       "account_id": 770592,
 *       "account_type": 1,
 *       "nick_name": "公司简称",
 *       "corporation_name": "公司全称"
 *     }
 *   ],
 *   "page_info": {
 *     "total_number": 38,
 *     "total_page": 4,
 *     "page": 1,
 *     "page_size": 10
 *   }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── Argument parsing ───

let input = {};
try {
  const raw = process.argv[2];
  if (raw) {
    input = JSON.parse(raw);
  }
} catch (err) {
  console.log(JSON.stringify({
    error: `Parameter parsing failed: ${err.message}. Please check: 1) JSON is well-formed; 2) Quote escaping matches your terminal (Bash/Zsh/Git Bash: single quotes; Windows CMD: double quotes + backslash; PowerShell 5.x: add --% or use \`" combo)`
  }));
  process.exit(1);
}

const {
  corporation_name_fuzzy_list,
  page,
  page_size,
} = input;

// ─── Input validation ───

if (corporation_name_fuzzy_list !== undefined) {
  if (!Array.isArray(corporation_name_fuzzy_list)) {
    console.log(JSON.stringify({ error: "corporation_name_fuzzy_list must be an array of strings" }));
    process.exit(1);
  }
  if (corporation_name_fuzzy_list.length > 2) {
    console.log(JSON.stringify({ error: "corporation_name_fuzzy_list supports at most 2 items" }));
    process.exit(1);
  }
  for (const item of corporation_name_fuzzy_list) {
    if (typeof item !== "string" || item.length < 2 || item.length > 50) {
      console.log(JSON.stringify({ error: `Each item in corporation_name_fuzzy_list must be a string with length 2~50, got: "${item}"` }));
      process.exit(1);
    }
  }
}

if (page !== undefined && (typeof page !== "number" || page < 1)) {
  console.log(JSON.stringify({ error: "page must be a positive integer (>= 1)" }));
  process.exit(1);
}

if (page_size !== undefined && (typeof page_size !== "number" || page_size < 1 || page_size > 500)) {
  console.log(JSON.stringify({ error: "page_size must be an integer between 1 and 500" }));
  process.exit(1);
}

const effectivePage = page ?? 1;
const effectivePageSize = page_size ?? 10;
if (effectivePage * effectivePageSize > 13000) {
  console.log(JSON.stringify({
    error: `page * page_size must be <= 13000, but got ${effectivePage} * ${effectivePageSize} = ${effectivePage * effectivePageSize}. Please reduce page or page_size.`
  }));
  process.exit(1);
}

// ─── Build query params ───

const params = {};

if (corporation_name_fuzzy_list && corporation_name_fuzzy_list.length > 0) {
  params.corporation_name_fuzzy_list = corporation_name_fuzzy_list;
}

if (page !== undefined) {
  params.page = page;
}

if (page_size !== undefined) {
  params.page_size = page_size;
}

// ─── Call API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/user_account_list/get",
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    error: result.error?.message || "API call failed",
    detail: result.error,
  }));
  process.exit(1);
}

// ─── Format output ───

const data = result.data?.data ?? result.data ?? {};
const list = data.list ?? [];
const pageInfo = data.page_info ?? {};

const output = {
  list: list.map((item) => ({
    account_id: item.account_id,
    account_type: item.account_type,
    nick_name: item.nick_name ?? "",
    corporation_name: item.corporation_name ?? "",
  })),
  page_info: {
    total_number: pageInfo.total_number ?? 0,
    total_page: pageInfo.total_page ?? 0,
    page: pageInfo.page ?? 1,
    page_size: pageInfo.page_size ?? 10,
  },
};

console.log(JSON.stringify(output, null, 2));
