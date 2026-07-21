#!/usr/bin/env node
/**
 * update-creative.mjs — 更新动态创意
 *
 * 调用 POST /v3.0/dynamic_creatives/update
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, dynamic_creative_id
 * 可选: dynamic_creative_name, creative_components（全量覆盖）
 *
 * creative_components 格式与 create-creative.mjs 相同。
 *
 * 输出（成功）:
 * { "success": true, "dynamic_creative_id": 8362490722 }
 *
 * 输出（失败）:
 * { "success": false, "error": { "code": 40001, "message": "..." } }
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

for (const field of ["account_id", "dynamic_creative_id"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const { account_id, ...bodyParams } = input;

const body = {
  account_id: parseInt(account_id, 10),
  ...bodyParams,
};

const result = await callApi({
  method: "POST",
  path: "/v3.0/dynamic_creatives/update",
  accountId: String(account_id),
  body,
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

const creativeId =
  result.data?.data?.dynamic_creative_id ??
  result.data?.dynamic_creative_id ??
  input.dynamic_creative_id;

console.log(JSON.stringify({ success: true, dynamic_creative_id: creativeId }, null, 2));
