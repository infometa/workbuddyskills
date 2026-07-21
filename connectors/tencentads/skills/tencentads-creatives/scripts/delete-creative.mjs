#!/usr/bin/env node
/**
 * delete-creative.mjs — 删除动态创意
 *
 * 调用 POST /v3.0/dynamic_creatives/delete
 * 注意：同一广告组下创意的新建、更新、删除必须串行执行，不可并发。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, dynamic_creative_id
 *
 * 输出（成功）:
 * { "success": true }
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
  path: "/v3.0/dynamic_creatives/delete",
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

console.log(JSON.stringify({ success: true }, null, 2));
