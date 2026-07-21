#!/usr/bin/env node
/**
 * query-adgroup-context.mjs — 查询广告组上下文（供创意创建使用）
 *
 * 封装腾讯广告开放 API adgroups/get 接口，查询单个广告组的关键字段，
 * 用于创意创建前获取 marketing_asset_outer_spec 等上下文信息。
 *
 * 入参:
 * '{
 *   "account_id": "<ID>",
 *   "adgroup_id": 987654321
 * }'
 *
 * 输出（成功）:
 * { "success": true, "adgroup": { "adgroup_id": ..., "marketing_asset_outer_spec": { "marketing_asset_outer_id": "v2_xxx@finder" }, ... } }
 *
 * 输出（失败）:
 * { "success": false, "error": { ... } }
 *
 * 关键字段说明：
 * - marketing_asset_outer_spec.marketing_asset_outer_id：视频号账号 username（v2_xxx@finder 格式），
 *   可作为 adgroup_context 传入 create-creative.mjs，用于自动推断 wechat_channels 组件
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` } }));
  process.exit(1);
}

const { account_id, adgroup_id } = input;

// ─── 参数校验 ───

if (!account_id) {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: account_id" } }));
  process.exit(1);
}

if (adgroup_id == null || adgroup_id === "") {
  console.log(JSON.stringify({ success: false, error: { message: "missing required field: adgroup_id" } }));
  process.exit(1);
}

// ─── 请求字段（仅创意创建所需） ───

const FIELDS = [
  "adgroup_id",
  "marketing_goal",
  "marketing_sub_goal",
  "marketing_target_type",
  "marketing_carrier_type",
  "marketing_asset_outer_spec",
  "live_video_mode",
  "mpa_spec",
  "dynamic_ad_type",
  "site_set",
];

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(account_id, 10),
  fields: FIELDS,
  filtering: [
    {
      field: "adgroup_id",
      operator: "EQUALS",
      values: [String(adgroup_id)],
    },
  ],
  page: 1,
  page_size: 1,
};

// ─── 调用 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/adgroups/get",
  accountId: String(account_id),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: result.error ?? { message: "API 调用失败" },
  }));
  process.exit(1);
}
// ─── 处理返回数据 ───

const data = result.data?.data ?? result.data ?? {};
const list = data?.list ?? [];

if (list.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: `未找到广告组: ${adgroup_id}` } }));
  process.exit(1);
}

const item = list[0];

// 裁剪：移除空对象和 null/undefined 字段
const adgroup = {};
for (const [key, value] of Object.entries(item)) {
  if (value == null) continue;
  if (value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length === 0) continue;
  adgroup[key] = value;
}

console.log(JSON.stringify({ success: true, adgroup }, null, 2));
