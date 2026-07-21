#!/usr/bin/env node
/**
 * get-components.mjs — 查询创意组件库
 *
 * 调用 components/get 接口，按组件类型拉取可用组件列表（status 非 disabled）。
 * 结果直接输出，可用 component_id 填写到 creative_components。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, component_type（大写枚举，如 "IMAGE_LIST"、"BRAND"）
 * 可选: page（默认1）、page_size（默认10，最大100）
 *
 * 示例入参:
 * { "account_id": "123456789", "component_type": "BRAND" }
 * { "account_id": "123456789", "component_type": "IMAGE_LIST", "page_size": 20 }
 *
 * 输出（成功）: { "list": [...], "page_info": {...} }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
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
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` } }));
  process.exit(1);
}

for (const field of ["account_id", "component_type"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const accountId = String(input.account_id);

const result = await callApi({
  method: "GET",
  path: "/v3.0/components/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    filtering: [
      { field: "component_type", operator: "EQUALS", values: [input.component_type] },
    ],
    fields: [
      "component_id",
      "component_type",
      "component_name",
      "component_value",
      "similarity_status",
    ],
    page: input.page ?? 1,
    page_size: input.page_size ?? 10,
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `获取组件列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
