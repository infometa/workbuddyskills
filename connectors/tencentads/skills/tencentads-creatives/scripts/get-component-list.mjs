#!/usr/bin/env node
/**
 * get-component-list.mjs — 按组件子类型查询账户下可用组件列表
 *
 * 调用 integrated_list_multiaccount/get 接口（level=COMPONENT），
 * 按 component_sub_type 过滤，返回可用组件的 component_id 列表。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, component_sub_types（字符串数组，如 ["BRAND"]、["VIDEO_16X9","VIDEO_9X16"]）
 * 可选: page（默认1）、page_size（默认10，最大100）
 *
 * 示例入参:
 * { "account_id": "123456789", "component_sub_types": ["BRAND"] }
 * { "account_id": "123456789", "component_sub_types": ["VIDEO_16X9", "VIDEO_9X16"], "page_size": 20 }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "list": [
 *     {
 *       "component_id": 1234567890,
 *       "component_type": "BRAND",
 *       "component_sub_type": "BRAND",
 *       "component_custom_name": "品牌组件A",
 *       "brand_type": "common"          // brand 类专有：common|wechat_channels|h5_profile|search_brand|wechat_official|wecom
 *     },
 *     {
 *       "component_id": 9876543210,
 *       "component_type": "BRAND",
 *       "component_sub_type": "BRAND_WECHAT_CHANNEL",
 *       "component_custom_name": "视频号品牌",
 *       "brand_type": "wechat_channels",
 *       "wechat_channels_username": "v2_xxx@finder"
 *     }
 *   ],
 *   "total": 5
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
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` } }));
  process.exit(1);
}

for (const field of ["account_id", "component_sub_types"]) {
  if (input[field] == null || (Array.isArray(input[field]) && input[field].length === 0)) {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

if (!Array.isArray(input.component_sub_types)) {
  console.log(JSON.stringify({ success: false, error: { message: "component_sub_types 必须为字符串数组" } }));
  process.exit(1);
}

const accountId = parseInt(String(input.account_id), 10);

const result = await callApi({
  method: "GET",
  path: "/v3.0/integrated_list_multiaccount/get",
  accountId: String(accountId),
  params: {
    account_id_list: [accountId],
    level: "COMPONENT",
    group_by: ["component_id"],
    page: input.page ?? 1,
    page_size: input.page_size ?? 10,
    filtering: [
      {
        field: "component.component_sub_type",
        operator: "IN",
        values: input.component_sub_types,
      },
      {
        field: "component.operation_status",
        operator: "IN",
        values: ["CALCULATE_STATUS_EXCLUDE_DEL", "CALCULATE_STATUS_NORMAL"],
      },
      {
        field: "component.scene",
        operator: "IN",
        values: ["DEFAULT"],
      },
    ],
    fields: [
      "component.component_id",
      "component.component_type",
      "component.component_sub_type",
      "component.component_custom_name",
      "component.component_value",
    ],
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `查询组件列表失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
const rawList = data.list ?? [];
const total = data.page_info?.total_number ?? rawList.length;

const list = rawList.map(item => {
  const comp = item.component ?? item;

  let cv = comp.component_value ?? {};
  if (typeof cv === "string") { try { cv = JSON.parse(cv); } catch { /**/ } }

  // 解析 brand 类组件的类型摘要和视频号 username
  let brand_type;
  let wechat_channels_username;
  const isBrandType = comp.component_type === "BRAND"
    || String(comp.component_sub_type ?? "").startsWith("BRAND");

  if (isBrandType) {
    const jumpInfo = cv?.brand?.value?.jump_info ?? cv?.jump_info;
    const pageType = jumpInfo?.page_type ?? jumpInfo?.value?.page_type;

    if (pageType === "PAGE_TYPE_WECHAT_CHANNELS_PROFILE") {
      brand_type = "wechat_channels";
      const profileSpec = jumpInfo?.page_spec?.wechat_channels_profile_spec
        ?? jumpInfo?.value?.page_spec?.wechat_channels_profile_spec;
      wechat_channels_username = profileSpec?.username ?? undefined;
    } else if (pageType === "PAGE_TYPE_H5_PROFILE") {
      brand_type = "h5_profile";
    } else if (pageType === "PAGE_TYPE_SEARCH_BRAND_AREA") {
      brand_type = "search_brand";
    } else if (pageType === "PAGE_TYPE_WECHAT_OFFICIAL_ACCOUNT_DETAIL") {
      brand_type = "wechat_official";
    } else if (pageType === "PAGE_TYPE_WECOM_CONSULT") {
      brand_type = "wecom";
    } else {
      // 无 jump_info 或 page_type 为空 → 普通品牌形象（brand_name + brand_image_id，兼容小游戏等场景）
      brand_type = "common";
    }
  }

  const entry = {
    component_id: comp.component_id,
    component_type: comp.component_type,
    component_sub_type: comp.component_sub_type,
    component_custom_name: comp.component_custom_name,
  };
  if (brand_type) entry.brand_type = brand_type;
  if (wechat_channels_username) entry.wechat_channels_username = wechat_channels_username;
  return entry;
}).filter(item => item.component_id);

console.log(JSON.stringify({ success: true, list, total }, null, 2));
