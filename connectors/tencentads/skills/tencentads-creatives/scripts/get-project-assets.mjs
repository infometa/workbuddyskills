#!/usr/bin/env node
/**
 * get-project-assets.mjs — 查询全店托管商品列表
 *
 * 调用 project_assets/get 接口，返回指定广告组（项目）下投放的商品详情列表。
 * 全店托管场景下创建创意时，需要用户选择一个商品，将其 marketing_asset_id 传入 smart_delivery_spec。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, project_id（广告组ID / adgroup_id）
 *
 * 示例入参:
 * { "account_id": "47192563", "project_id": "91629327927" }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     {
 *       "marketing_asset_id": 143180361,
 *       "marketing_asset_name": "商品名称",
 *       "image_url": "https://...",
 *       "related_creatives_nums": 9
 *     }
 *   ]
 * }
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
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

for (const field of ["account_id", "project_id"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const accountId = String(input.account_id);

const result = await callApi({
  method: "GET",
  path: "/v3.0/project_assets/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    project_id: parseInt(String(input.project_id), 10),
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询商品列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
const list = data.list ?? [];

console.log(JSON.stringify({ success: true, list }, null, 2));
