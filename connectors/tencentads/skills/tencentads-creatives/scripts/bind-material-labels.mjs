#!/usr/bin/env node
/**
 * bind-material-labels.mjs — 绑定标签素材关联关系（material_labels/bind）
 *
 * 调用 POST /v3.0/material_labels/bind 接口，管理一组图片/视频素材与一组素材标签的
 * 关联关系。支持三种模式（详见 binding_type 枚举）：覆盖绑定、新增绑定、解除绑定。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   account_id 或 organization_id（二选一）
 *   label_id_list — integer[]，目标标签 ID 列表
 *   image_id_list / media_id_list — 至少必须有一个非空数组
 *
 * 可选:
 *   image_id_list      — string[]，图片 ID 列表
 *   media_id_list      — string[]，视频 ID 列表
 *   binding_type       — enum BindingType，默认值由后端决定
 *   business_scenario  — enum BusinessScenario
 *
 * 枚举可选值:
 *   binding_type:
 *     LABEL_BINDING_TYPE_OVERWRITE   素材标签覆盖绑定（清空原绑定后重新绑定）
 *     LABEL_BINDING_TYPE_ADD         素材标签新增绑定（在原绑定基础上追加）
 *     LABEL_BINDING_TYPE_DELETE      素材标签删除绑定（解除指定素材与标签的关联关系）
 *   business_scenario:
 *     BUSINESS_SCENARIO_CREATIVE     素材库类型
 *     BUSINESS_SCENARIO_DELIVERY     投放素材包类型
 *
 * 示例:
 *   {
 *     "account_id": "123456789",
 *     "label_id_list": [1234, 5678],
 *     "image_id_list": ["img-aaa", "img-bbb"],
 *     "binding_type": "LABEL_BINDING_TYPE_ADD"
 *   }
 *
 *   {
 *     "account_id": "123456789",
 *     "label_id_list": [1234],
 *     "media_id_list": ["video-001"],
 *     "binding_type": "LABEL_BINDING_TYPE_OVERWRITE",
 *     "business_scenario": "BUSINESS_SCENARIO_DELIVERY"
 *   }
 *
 * 输出（成功）: { "success_id_list": [...], "fail_id_list": [...], "fail_reason_list": [...] }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 详细规范: references/material-labels.md
 */

import { callApi } from "tencentads-cli";

const BINDING_TYPE_VALUES = new Set([
  "LABEL_BINDING_TYPE_OVERWRITE",
  "LABEL_BINDING_TYPE_ADD",
  "LABEL_BINDING_TYPE_DELETE",
]);

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

if (!Array.isArray(input.label_id_list) || input.label_id_list.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: label_id_list 必须为非空数组" } }));
  process.exit(1);
}

const hasImage = Array.isArray(input.image_id_list) && input.image_id_list.length > 0;
const hasMedia = Array.isArray(input.media_id_list) && input.media_id_list.length > 0;
if (!hasImage && !hasMedia) {
  console.log(JSON.stringify({
    success: false,
    error: { message: "image_id_list 与 media_id_list 必须至少传入一个非空数组（图片或视频，二者可同时传）" },
  }));
  process.exit(1);
}

if (input.binding_type != null && input.binding_type !== "") {
  const v = String(input.binding_type);
  if (!BINDING_TYPE_VALUES.has(v)) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `binding_type 取值非法: "${v}"`,
        allowed: [...BINDING_TYPE_VALUES],
      },
    }));
    process.exit(1);
  }
}

if (input.business_scenario != null && input.business_scenario !== "") {
  const v = String(input.business_scenario);
  if (!BUSINESS_SCENARIO_VALUES.has(v)) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `business_scenario 取值非法: "${v}"`,
        allowed: [...BUSINESS_SCENARIO_VALUES],
      },
    }));
    process.exit(1);
  }
}

const accountId = hasAccount ? String(input.account_id) : undefined;

const body = {};
if (hasAccount) body.account_id = parseInt(accountId, 10);
if (hasOrg) body.organization_id = parseInt(String(input.organization_id), 10);
body.label_id_list = input.label_id_list.map(v => parseInt(String(v), 10));
if (hasImage) body.image_id_list = input.image_id_list.map(v => String(v));
if (hasMedia) body.media_id_list = input.media_id_list.map(v => String(v));
if (input.binding_type != null && input.binding_type !== "") body.binding_type = String(input.binding_type);
if (input.business_scenario != null && input.business_scenario !== "") body.business_scenario = String(input.business_scenario);

const result = await callApi({
  method: "POST",
  path: "/v3.0/material_labels/bind",
  accountId: accountId,
  body,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `绑定素材标签关联关系失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
