#!/usr/bin/env node
/**
 * get-component-depends.mjs — 查询组件字段联动约束，输出依赖摘要（含合法枚举值）
 *
 * 先调 adgroups/get 获取广告组四元组，再调 component_depends/get，最终输出压缩摘要。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, adgroup_id, component_type（大写枚举，如 "WECHAT_CHANNELS"）
 *
 * 示例入参:
 * { "account_id": "123456789", "adgroup_id": 987654321, "component_type": "SHOW_DATA" }
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "component": "SHOW_DATA",
 *   "depends": [
 *     {
 *       "field": "conversion_data_type",
 *       "depends_on": "main_jump_info/page_type",
 *       "note": "conversion_data_type 的可选值因 main_jump_info/page_type 的值而变化",
 *       "options": [
 *         {
 *           "when": [{ "path": "main_jump_info/page_type", "value": "PAGE_TYPE_OFFICIAL" }],
 *           "values": ["CONVERSION_DATA_ADMETRIC", "CONVERSION_DATA_DEFAULT"]
 *         },
 *         {
 *           "when": [{ "path": "main_jump_info/page_type", "value": "PAGE_TYPE_WECHAT_MINI_GAME" }],
 *           "values": ["CONVERSION_DATA_ADMETRIC", "CONVERSION_DATA_FRIEND_PLAY"]
 *         }
 *       ]
 *     }
 *   ]
 * }
 *
 * 说明:
 *   - depends[].options[].values 是该字段在对应 when 条件下的唯一合法枚举值，必须直接使用
 *   - 若 depends 为空数组，说明该组件无字段联动约束，可直接填写
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

for (const field of ["account_id", "adgroup_id", "component_type"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

if (input.dynamic_creative_type != null && input.dynamic_creative_type !== "DYNAMIC_CREATIVE_TYPE_PROGRAM" && input.creative_template_id == null) {
  console.log(JSON.stringify({ success: false, error: { message: `dynamic_creative_type 为 ${input.dynamic_creative_type} 时必须传入 creative_template_id` } }));
  process.exit(1);
}

const accountId = String(input.account_id);
const adgroupId = input.adgroup_id;

// Step 1: 拉取广告组四元组
const adgroupResult = await callApi({
  method: "GET",
  path: "/v3.0/adgroups/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    filtering: [{ field: "adgroup_id", operator: "EQUALS", values: [String(adgroupId)] }],
    fields: ["adgroup_id", "marketing_goal", "marketing_sub_goal", "marketing_target_type", "marketing_carrier_type", "brand_ad_type"],
  },
});

if (!adgroupResult.success) {
  console.log(JSON.stringify({ success: false, error: { message: `获取广告组信息失败: ${adgroupResult.error?.message}` } }));
  process.exit(1);
}

const adgroupList = adgroupResult.data?.data?.list ?? adgroupResult.data?.list ?? [];
if (adgroupList.length === 0) {
  console.log(JSON.stringify({ success: false, error: { message: `未找到广告组 ${adgroupId}` } }));
  process.exit(1);
}

const { marketing_goal, marketing_sub_goal, marketing_target_type, marketing_carrier_type, brand_ad_type } = adgroupList[0];

// Step 2: 查询组件依赖
const result = await callApi({
  method: "GET",
  path: "/v3.0/component_depends/get",
  accountId,
  params: {
    account_id: parseInt(accountId, 10),
    adgroup_id: adgroupId,
    marketing_goal,
    marketing_sub_goal,
    marketing_target_type,
    marketing_carrier_type,
    delivery_mode: input.delivery_mode ?? "DELIVERY_MODE_COMPONENT",
    component_type: input.component_type,
    ...(input.creative_template_id != null ? { creative_template_id: input.creative_template_id } : {}),
    dynamic_creative_type: input.dynamic_creative_type
      ?? ((input.creative_template_id != null && input.creative_template_id > 0)
        ? "DYNAMIC_CREATIVE_TYPE_COMMON"
        : "DYNAMIC_CREATIVE_TYPE_PROGRAM"),
    ...(brand_ad_type != null ? { brand_ad_type } : {}),
    ...(input.live_promoted_type != null ? { live_promoted_type: input.live_promoted_type } : {}),
  },
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `获取组件依赖失败: ${result.error?.message}` } }));
  process.exit(1);
}

// Step 3: 压缩为依赖摘要（含合法枚举值）
function summarize(data) {
  // API 响应两种结构：data.data（list 模式）或 data.data 直接是对象
  const dataObj = data?.data ?? data ?? {};
  // list 模式：data.data.list[0]；单对象模式：data.data 本身
  const componentData = (dataObj.list ?? [dataObj])[0] ?? {};

  const componentType = componentData.component_type ?? "";
  const componentDepends = componentData.component_depends ?? [];

  const depends = [];

  for (const dep of componentDepends) {
    const targetPath = dep.target_path ?? "";
    const dependPaths = dep.depend_paths ?? [];
    const targetOptions = dep.target_options ?? [];

    if (dependPaths.length === 0) continue;

    // 提取字段名：去掉路径中第一段（组件类型前缀），保留后续部分
    const fieldName = targetPath.split("/").filter(Boolean).slice(1).join("/") || targetPath;

    // 将 target_options 中的 support_options 整理为 when → values 映射
    const options = targetOptions.map(opt => ({
      when: (opt.depends ?? []).map(d => ({
        path: (d.path ?? "").replace(/^\//, ""),
        value: d.value,
      })),
      values: (opt.support_options ?? []).map(s => s.value).filter(Boolean),
    })).filter(o => o.values.length > 0);

    for (const depPath of dependPaths) {
      const depField = depPath.replace(/^\//, "");
      const entry = {
        field: fieldName,
        depends_on: depField,
        note: `${fieldName} 的可选值因 ${depField} 的值而变化`,
      };
      if (options.length > 0) entry.options = options;
      depends.push(entry);
    }
  }

  return { success: true, component: componentType, depends };
}

console.log(JSON.stringify(summarize(result.data), null, 2));
