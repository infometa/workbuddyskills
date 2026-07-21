#!/usr/bin/env node
/**
 * get-audios.mjs — 查询妙思版权音频列表
 *
 * 调用 muse_audios/get 接口，获取妙思平台提供的版权音频，用于视频创意制作。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id
 * 可选: fields（返回字段列表，默认返回全部字段）
 *       page（默认1）、page_size（默认10，最大100）
 *
 * 可选 fields 值:
 *   audio_id, audio_name, cover_image_url, author, duration, expire_time, feel_tags, genre_tags
 *
 * 示例:
 * { "account_id": "123456789" }
 * { "account_id": "123456789", "page_size": 20 }
 * { "account_id": "123456789", "fields": ["audio_id", "audio_name", "author", "duration", "feel_tags"] }
 *
 * 输出（成功）: { "list": [...], "page_info": {...} }
 *   list[].expire_time: 版权过期时间戳，使用前请确认版权有效
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 详细规范: references/materials/muse-audios-get.md
 */

import { callApi } from "tencentads-cli";

const ALL_FIELDS = [
  "audio_id",
  "audio_name",
  "cover_image_url",
  "author",
  "duration",
  "expire_time",
  "feel_tags",
  "genre_tags",
];

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

if (input.account_id == null || input.account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

const accountId = String(input.account_id);

const result = await callApi({
  method: "POST",
  path: "/v3.0/muse_audios/get",
  accountId,
  body: {
    account_id: parseInt(accountId, 10),
    fields: input.fields ?? ALL_FIELDS,
    page: input.page ?? 1,
    page_size: input.page_size ?? 10,
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询音频列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
