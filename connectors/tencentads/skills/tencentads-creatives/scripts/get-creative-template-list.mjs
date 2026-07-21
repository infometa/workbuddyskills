#!/usr/bin/env node
/**
 * get-creative-template-list.mjs — 查询账户可用创意形式列表
 *
 * 调用 GET /v3.0/creative_template_list/get
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id
 * 可选: adgroup_id（填写后只返回该广告组适用的创意形式）
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     {
 *       "template_id": 721,
 *       "template_name": "竖版视频 9:16",
 *       "live_promoted_type_list": ["LIVE_PROMOTED_TYPE_SHORT_VIDEO"]
 *     },
 *     {
 *       "template_id": 0,
 *       "template_name": "不指定创意形式",
 *       "live_promoted_type_list": []
 *     }
 *   ]
 * }
 *
 * 主要用途：
 *   1. 验证用户指定的 creative_template_id 是否在可用列表中
 *   2. 检查 live_promoted_type_list 字段，确认是否需要填写 live_promoted_type
 *
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

if (input.account_id == null || input.account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

const accountId = parseInt(input.account_id, 10);

const params = {
  account_id: accountId,
  page: 1,
  page_size: 100,
  ...(input.adgroup_id != null ? { adgroup_id: input.adgroup_id } : {}),
};

const result = await callApi({
  method: "GET",
  path: "/v3.0/creative_template_list/get",
  accountId: String(accountId),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API 调用失败",
    },
  }));
  process.exit(1);
}

const rawList = result.data?.data?.list ?? result.data?.list ?? [];

const list = rawList.map(tpl => ({
  template_id: tpl.creative_template_id,
  template_name: tpl.creative_template_appellation || (tpl.creative_template_id === 0 ? "不指定创意形式" : `创意形式${tpl.creative_template_id}`),
  live_promoted_type_list: tpl.live_promoted_type_list ?? [],
}));

console.log(JSON.stringify({ success: true, list }, null, 2));
