#!/usr/bin/env node
/**
 * add-material-labels.mjs — 创建素材标签（material_labels/add）
 *
 * 调用 POST /v3.0/material_labels/add 接口，在指定账户/业务单元下批量新增素材标签。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   account_id 或 organization_id（二选一）
 *   labels — 标签信息数组，每项至少含 label_name；可选 first_label_level_name / second_label_level_name / business_scenario
 *
 * labels[i] 字段:
 *   label_name                 — string，1-2048 字节，**必填**
 *   first_label_level_name     — string，可选，一级标签类目名称
 *   second_label_level_name    — string，可选，二级标签类目名称
 *   business_scenario          — enum BusinessScenario，可选，取值见下；**未传时脚本默认填 `BUSINESS_SCENARIO_DELIVERY`（投放素材包类型）**
 *
 * 业务场景（business_scenario）枚举:
 *   BUSINESS_SCENARIO_CREATIVE   素材库类型
 *   BUSINESS_SCENARIO_DELIVERY   投放素材包类型
 *
 * 示例:
 *   {
 *     "account_id": "123456789",
 *     "labels": [
 *       { "label_name": "618 大促主推", "first_label_level_name": "大促", "second_label_level_name": "618" },
 *       { "label_name": "夏装外套", "business_scenario": "BUSINESS_SCENARIO_CREATIVE" }
 *     ]
 *   }
 *
 * 输出（成功）: { "success_label_list": [...], "fail_label_list": [...] }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 详细规范: references/material-labels.md
 */

import { callApi } from "tencentads-cli";

const BUSINESS_SCENARIO_VALUES = new Set([
  "BUSINESS_SCENARIO_CREATIVE",
  "BUSINESS_SCENARIO_DELIVERY",
]);

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

const hasAccount = input.account_id != null && input.account_id !== "";
const hasOrg = input.organization_id != null && input.organization_id !== "";
if (!hasAccount && !hasOrg) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id 或 organization_id 必须填一个" } }));
  process.exit(1);
}

if (!Array.isArray(input.labels) || input.labels.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: labels 必须为非空数组" } }));
  process.exit(1);
}

const normalizedLabels = [];
for (let i = 0; i < input.labels.length; i++) {
  const item = input.labels[i];
  if (!item || typeof item !== "object") {
    console.log(JSON.stringify({ success: false, error: { message: `labels[${i}] 必须是对象` } }));
    process.exit(1);
  }
  if (!item.label_name || typeof item.label_name !== "string") {
    console.log(JSON.stringify({ success: false, error: { message: `labels[${i}].label_name 为必填字符串` } }));
    process.exit(1);
  }
  if (item.label_name.length < 1 || item.label_name.length > 2048) {
    console.log(JSON.stringify({ success: false, error: { message: `labels[${i}].label_name 长度需在 1-2048 字节之间` } }));
    process.exit(1);
  }
  const out = { label_name: item.label_name };
  if (item.first_label_level_name) out.first_label_level_name = String(item.first_label_level_name);
  if (item.second_label_level_name) out.second_label_level_name = String(item.second_label_level_name);
  if (item.business_scenario) {
    const v = String(item.business_scenario);
    if (!BUSINESS_SCENARIO_VALUES.has(v)) {
      console.log(JSON.stringify({
        success: false,
        error: {
          message: `labels[${i}].business_scenario 取值非法: "${v}"`,
          allowed: [...BUSINESS_SCENARIO_VALUES],
        },
      }));
      process.exit(1);
    }
    out.business_scenario = v;
  } else {
    // 默认填投放素材包类型（创建场景下最常见的用途），用户未指定时由脚本兜底
    out.business_scenario = "BUSINESS_SCENARIO_DELIVERY";
  }
  normalizedLabels.push(out);
}

const accountId = hasAccount ? String(input.account_id) : undefined;

const body = {};
if (hasAccount) body.account_id = parseInt(accountId, 10);
if (hasOrg) body.organization_id = parseInt(String(input.organization_id), 10);
body.labels = normalizedLabels;

const result = await callApi({
  method: "POST",
  path: "/v3.0/material_labels/add",
  accountId: accountId,
  body,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `创建素材标签失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
