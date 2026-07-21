#!/usr/bin/env node
/**
 * get-playable-pages.mjs — 查询小游戏试玩页列表
 *
 * 调用 wx_game_playable_page/get 接口，返回指定小游戏 AppID 下的试玩页列表。
 * 结果中 playable_page_path 可直接填入 creative_components 的 playable_page 组件。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, app_id（小游戏的微信 AppID，wx 开头）
 *
 * 示例入参:
 * { "account_id": "78139785", "app_id": "wx4bde5ea0aa8c8968" }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     {
 *       "playable_page_path": "playable@wx7a727ff7d940bb3f@CBgAA...",
 *       "playable_page_name": "rdm测试",
 *       "nick_name": "上报unity启动数据、点击上报",
 *       "status": "PLAYABLE_PAGE_STATUS_ONLINE",
 *       "preview_appid": "wx81fb74b6f8ca18d6",
 *       "preview_path": "?playable_outid=..."
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

for (const field of ["account_id", "app_id"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const accountId = String(input.account_id);

const result = await callApi({
  method: "GET",
  path: "/v3.0/wx_game_playable_page/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    app_id: input.app_id,
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询试玩页列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
const list = data.list ?? [];

console.log(JSON.stringify({ success: true, list }, null, 2));
