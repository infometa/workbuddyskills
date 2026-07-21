#!/usr/bin/env node
/**
 * update-material-labels.mjs — 更新素材标签（material_labels/update）
 *
 * 调用 POST /v3.0/material_labels/update 接口，更新指定素材标签的名称或类目归属。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   account_id 或 organization_id（二选一）
 *   label_id   — integer，待更新的标签 ID
 *   label_name — string，1-2048 字节，新的标签名称
 * 可选:
 *   first_label_level_name  — string，新的一级标签类目名称
 *   second_label_level_name — string，新的二级标签类目名称
 *
 * 注意: 协议层面 label_id 与 label_name 都是必填。如只想改类目而不改名称，
 *       请把原标签名再传一次。
 *
 * 示例:
 *   {
 *     "account_id": "123456789",
 *     "label_id": 12345,
 *     "label_name": "618 大促主推（更新）",
 *     "first_label_level_name": "大促",
 *     "second_label_level_name": "618"
 *   }
 *
 * 输出（成功）: { "success_label_list": [...], "fail_label_list": [...] }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 详细规范: references/material-labels.md
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

const hasAccount = input.account_id != null && input.account_id !== "";
const hasOrg = input.organization_id != null && input.organization_id !== "";
if (!hasAccount && !hasOrg) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id 或 organization_id 必须填一个" } }));
  process.exit(1);
}

if (input.label_id == null || input.label_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: label_id" } }));
  process.exit(1);
}

if (!input.label_name || typeof input.label_name !== "string") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: label_name" } }));
  process.exit(1);
}

if (input.label_name.length < 1 || input.label_name.length > 2048) {
  console.log(JSON.stringify({ success: false, error: { message: "label_name 长度需在 1-2048 字节之间" } }));
  process.exit(1);
}

const accountId = hasAccount ? String(input.account_id) : undefined;

const body = {};
if (hasAccount) body.account_id = parseInt(accountId, 10);
if (hasOrg) body.organization_id = parseInt(String(input.organization_id), 10);
body.label_id = parseInt(String(input.label_id), 10);
body.label_name = input.label_name;
if (input.first_label_level_name) body.first_label_level_name = String(input.first_label_level_name);
if (input.second_label_level_name) body.second_label_level_name = String(input.second_label_level_name);

const result = await callApi({
  method: "POST",
  path: "/v3.0/material_labels/update",
  accountId: accountId,
  body,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `更新素材标签失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
