#!/usr/bin/env node
/**
 * get-material-labels.mjs — 查询素材标签列表（material_labels/get）
 *
 * 调用 /v3.0/material_labels/get 接口，按过滤条件查询账户下的素材标签。
 * 用于在创建广告组前，根据用户给出的"标签名称 / 类目"等自然语言线索定位 label_id，
 * 进而将其作为 material_package_id 传入 create-adgroup.mjs。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id 或 organization_id（二选一）
 * 可选:
 *   label_id                       — integer，精确查询单个标签
 *   label_name                     — string，按标签名称过滤（1-2048 字节）
 *   first_label_level_id_list      — integer[]，一级标签类目 ID 列表
 *   second_label_level_id_list     — integer[]，二级标签类目 ID 列表
 *   business_scenario              — enum BusinessScenario
 *   ownership_type                 — enum OwnershipType（素材归属类型）
 *   need_count                     — boolean，是否返回关联图片/视频数（未传时默认 true）
 *   order_by                       — struct[]，排序字段
 *   page                           — integer，默认 1
 *   page_size                      — integer，默认 10，最大 100
 *
 * 示例:
 *   { "account_id": "123456789" }
 *   { "account_id": "123456789", "label_id": 1234, "need_count": true }
 *   { "account_id": "123456789", "label_name": "618 大促", "page_size": 50 }
 *   { "account_id": "123456789", "first_label_level_id_list": [10] }
 *
 * 输出（成功）: { "list": [...], "page_info": {...} }
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

const accountId = hasAccount ? String(input.account_id) : undefined;

const params = {};
if (hasAccount) params.account_id = parseInt(accountId, 10);
if (hasOrg) params.organization_id = parseInt(String(input.organization_id), 10);
if (input.label_id != null && input.label_id !== "") params.label_id = parseInt(String(input.label_id), 10);
if (input.label_name) params.label_name = String(input.label_name);
if (Array.isArray(input.first_label_level_id_list) && input.first_label_level_id_list.length > 0) {
  params.first_label_level_id_list = input.first_label_level_id_list.map(v => parseInt(String(v), 10));
}
if (Array.isArray(input.second_label_level_id_list) && input.second_label_level_id_list.length > 0) {
  params.second_label_level_id_list = input.second_label_level_id_list.map(v => parseInt(String(v), 10));
}
if (input.business_scenario) params.business_scenario = String(input.business_scenario);
if (input.ownership_type) params.ownership_type = String(input.ownership_type);
params.need_count = input.need_count != null ? Boolean(input.need_count) : true;
if (Array.isArray(input.order_by) && input.order_by.length > 0) params.order_by = input.order_by;
params.page = input.page ?? 1;
params.page_size = input.page_size ?? 10;

const result = await callApi({
  method: "GET",
  path: "/v3.0/material_labels/get",
  accountId: accountId,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询素材标签失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
