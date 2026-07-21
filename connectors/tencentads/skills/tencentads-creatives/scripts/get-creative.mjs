#!/usr/bin/env node
/**
 * get-creative.mjs — 查询动态创意详情
 *
 * 调用 GET /v3.0/dynamic_creatives/get
 * 参考: references/dynamic-creatives-get.md
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, dynamic_creative_id（单个 ID 或 ID 数组）
 * 可选: fields（返回字段列表，默认包含全量核心字段）
 *
 * 示例入参（单个）:
 * { "account_id": "123456789", "dynamic_creative_id": 8362490722 }
 *
 * 示例入参（多个）:
 * { "account_id": "123456789", "dynamic_creative_id": [8362490722, 8362490723] }
 *
 * 输出（单个 ID，成功）:
 * {
 *   "success": true,
 *   "creative": {
 *     "dynamic_creative_id": 8362490722,
 *     "adgroup_id": 987654321,
 *     "dynamic_creative_name": "创意名称_20240324",
 *     "creative_template_id": 0,
 *     "delivery_mode": "DELIVERY_MODE_COMPONENT",
 *     "dynamic_creative_type": "DYNAMIC_CREATIVE_TYPE_PROGRAM",
 *     "configured_status": "AD_STATUS_NORMAL",
 *     "creative_components": { ... }
 *   }
 * }
 *
 * 输出（多个 ID，成功）:
 * {
 *   "success": true,
 *   "list": [ { ... }, { ... } ]
 * }
 *
 * 输出（失败）:
 * { "success": false, "error": { "message": "..." } }
 */

import { callApi } from "tencentads-cli";

let input;
try {
  const raw = process.argv[2] != null
    ? process.argv[2]
    : await new Promise(res => {
        let buf = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', d => (buf += d));
        process.stdin.on('end', () => res(buf.trim()));
      });
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数或通过 stdin 传入");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

for (const field of ["account_id", "dynamic_creative_id"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const accountId = String(input.account_id);
const rawId = input.dynamic_creative_id;
const isSingle = !Array.isArray(rawId);
const idList = isSingle ? [rawId] : rawId;

const defaultFields = [
  "dynamic_creative_id",
  "adgroup_id",
  "dynamic_creative_name",
  "creative_template_id",
  "delivery_mode",
  "dynamic_creative_type",
  "creative_components",
  "configured_status",
];

const fields = input.fields ?? defaultFields;

const result = await callApi({
  method: "GET",
  path: "/v3.0/dynamic_creatives/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    filtering: [
      {
        field: "dynamic_creative_id",
        operator: isSingle ? "EQUALS" : "IN",
        values: isSingle ? [String(rawId)] : idList.map(String),
      },
    ],
    fields,
    page: 1,
    page_size: Math.min(idList.length, 100),
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

const list = result.data?.data?.list ?? result.data?.list ?? [];

if (isSingle) {
  if (list.length === 0) {
    console.log(JSON.stringify({
      success: false,
      error: { message: `未找到创意 ${rawId}` },
    }));
    process.exit(1);
  }
  console.log(JSON.stringify({ success: true, creative: list[0] }, null, 2));
} else {
  console.log(JSON.stringify({ success: true, list }, null, 2));
}
