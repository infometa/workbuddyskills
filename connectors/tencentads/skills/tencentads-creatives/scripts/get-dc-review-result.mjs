#!/usr/bin/env node
/**
 * get-dc-review-result.mjs — 查询动态创意审核详情
 *
 * 调用 POST /v3.0/dc_review_result/get
 * 参考: references/dc-review-result-get.md
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, dynamic_creative_id
 * 可选: need_return_has_violation_reason_interpretation（是否返回违规原因解读入口，默认 true）
 *
 * 示例入参:
 * { "account_id": "123456789", "dynamic_creative_id": 8362490722 }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "review_result": {
 *     "adgroup_id": 987654321,
 *     "total_component_compose_count": 12,
 *     "reject_component_compose_count": 3,
 *     "is_all_component_compose_pending": false,
 *     "delay_message_list": [],
 *     "element_result_list": [
 *       {
 *         "element_id": ...,
 *         "element_name": "...",
 *         "element_type": "ELEMENT_TYPE_IMAGE",
 *         "element_value": "...",
 *         "element_fingerprint": "...",
 *         "review_status": "AD_STATUS_NORMAL",
 *         "component_info": { "component_id": ..., "component_type": "...", ... },
 *         "element_reject_detail_info": [ { "reason": "...", ... } ]
 *       }
 *     ],
 *     "reject_component_compose_info_list": [
 *       { "reject_message": "...", "component_compose_element_list": [...] }
 *     ]
 *   }
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
const dynamicCreativeId = input.dynamic_creative_id;
const needInterpretation = input.need_return_has_violation_reason_interpretation ?? true;

const result = await callApi({
  method: "POST",
  path: "/v3.0/dc_review_result/get",
  accountId,
  body: {
    account_id: parseInt(accountId, 10),
    dynamic_creative_id_list: [dynamicCreativeId],
    need_return_has_violation_reason_interpretation: needInterpretation,
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

if (list.length === 0) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `未找到创意 ${dynamicCreativeId} 的审核详情` },
  }));
  process.exit(1);
}

console.log(JSON.stringify({ success: true, review_result: list[0] }, null, 2));
