#!/usr/bin/env node
/**
 * get-videos.mjs — 查询素材库视频列表
 *
 * 调用 videos/get 接口，按过滤条件查询账户下的视频素材。
 * 可用于确认 video_id 是否存在、查询转码状态、按尺寸筛选等。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id
 * 可选: filtering（过滤条件数组，最多 4 个）、page（默认1）、page_size（默认10，最大100）
 *
 * 常用过滤字段:
 *   video_id       — EQUALS / CONTAINS（按 ID 查询）
 *   media_id       — EQUALS / IN
 *   media_width    — EQUALS
 *   media_height   — EQUALS
 *   source_type    — EQUALS（SOURCE_TYPE_LOCAL / SOURCE_TYPE_API 等）
 *   status         — EQUALS（ADSTATUS_NORMAL / ADSTATUS_DELETED）
 *   video_duration_millisecond — GREATER_EQUALS / LESS_EQUALS（按时长过滤）
 *
 * 示例:
 * { "account_id": "123456789" }
 * { "account_id": "123456789", "filtering": [{"field": "media_width", "operator": "EQUALS", "values": ["1280"]}] }
 * { "account_id": "123456789", "filtering": [{"field": "video_id", "operator": "EQUALS", "values": ["123456"]}] }
 *
 * 输出（成功）: { "list": [...], "page_info": {...} }
 *   list[].system_status: MEDIA_STATUS_VALID（可用）| MEDIA_STATUS_PROCESSING（转码中）| MEDIA_STATUS_INVALID（失败）
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 注意: 不指定 created_time 时默认查询半年内数据
 * 详细规范: references/materials/videos-get.md
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

if (input.account_id == null || input.account_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

const accountId = String(input.account_id);

// ─── filtering 时间字段自动转换 ───

/** filtering 中需要从 'YYYY-MM-DD HH:mm:ss' 转为 Unix 时间戳的字段 */
const TIME_FILTER_FIELDS = new Set(["created_time", "last_modified_time"]);

/**
 * 将 'YYYY-MM-DD HH:mm:ss' 格式字符串转为 Unix 秒级时间戳字符串。
 * 如果输入已经是纯数字（时间戳），则原样返回。
 */
function parseDatetimeToTimestamp(value) {
  if (/^\d+$/.test(String(value))) return String(value);
  const parsed = Date.parse(String(value).replace(" ", "T") + "+08:00");
  if (isNaN(parsed)) return String(value);
  return String(Math.floor(parsed / 1000));
}

function convertFilteringTimeValues(filters) {
  if (!Array.isArray(filters)) return filters;
  return filters.map((f) => {
    const bareField = f.field?.includes(".") ? f.field.split(".").pop() : f.field;
    if (!TIME_FILTER_FIELDS.has(bareField)) return f;
    return { ...f, values: (f.values || []).map(parseDatetimeToTimestamp) };
  });
}

const params = {
  account_id: parseInt(accountId, 10),
  page: input.page ?? 1,
  page_size: input.page_size ?? 10,
};
if (input.filtering) params.filtering = convertFilteringTimeValues(input.filtering);

const result = await callApi({
  method: "GET",
  path: "/v3.0/videos/get",
  accountId,
  params,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询视频列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
