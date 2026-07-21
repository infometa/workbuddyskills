#!/usr/bin/env node
/**
 * get-creative-templates.mjs — 查询指定广告组可用的创意形式，输出组件摘要
 *
 * 先调 adgroups/get 获取广告组四元组，再调 creative_template/get，最终输出压缩摘要。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, adgroup_id
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "templates": [
 *     {
 *       "template_id": 0,
 *       "template_name": "不指定创意形式",
 *       "support_impression_tracking_url": true,   // 仅 true 时出现，表示可填监测曝光链接
 *       "support_click_tracking_url": true,        // 仅 true 时出现，表示可填监测点击链接
 *       "components": [
 *         {
 *           "name": "video", "desc": "视频组件", "required": true, "min": 1, "max": 15, "has_depend": false,
 *           "sub_types": ["VIDEO_4X3", "VIDEO_16X9", "VIDEO_9X16"],
 *           "fields": [{ "name": "video_id", "required": true }, { "name": "cover_id", "required": false }]
 *         },
 *         {
 *           "name": "main_jump_info", "desc": "落地页组件", "required": true, "min": 1, "max": 3, "has_depend": false,
 *           "sub_types": ["JUMP_INFO_OFFICIAL", "JUMP_INFO_WECHAT_MINI_GAME"],
 *           "fields": [
 *             { "name": "page_type", "required": true, "enum": ["PAGE_TYPE_OFFICIAL", "PAGE_TYPE_WECHAT_MINI_GAME"] },
 *             { "name": "page_spec",  "required": false }
 *           ]
 *         },
 *         {
 *           "name": "brand", "desc": "品牌形象组件", "required": true, "min": 1, "max": 1, "has_depend": false,
 *           "sub_types": [
 *             { "name": "BRAND",               "fields": [{ "name": "brand_image_id", "required": true }, { "name": "brand_name", "required": true }] },
 *             { "name": "BRAND_WECHAT_CHANNEL", "fields": [{ "name": "brand_image_id", "required": true }, { "name": "brand_name", "required": true }, { "name": "jump_info", "required": true }] }
 *           ]
 *         },
 *         {
 *           "name": "action_button", "desc": "行动按钮组件", "required": true, "min": 1, "max": 1, "has_depend": true,
 *           "sub_types": ["ACTION_BUTTON"],
 *           "fields": [
 *             { "name": "button_text", "required": true, "enum": ["了解更多", "立即咨询", "..."] },
 *             { "name": "jump_info",   "required": true }
 *           ]
 *         },
 *         {
 *           "name": "wechat_channels", "desc": "视频号信息组件", "required": false, "min": 1, "max": 1, "has_depend": true,
 *           "auto_inferred": true, "note": "由 create-creative.mjs 脚本自动推断，无需手动填写"
 *         }
 *       ]
 *     }
 *   ]
 * }
 *
 * 说明:
 *   - 每个组件包含 name/desc/required/min/max/has_depend
 *   - sub_types 字段名集合相同时为字符串数组（如 video/image），字段集合有差异时为对象数组（如 brand，每项含 name 和 fields）
 *   - fields 为合并后的可用字段（enum 字段跨 sub_type 合并去重）
 *   - has_depend=true 表示该组件有字段联动约束，可进一步调用 get-component-depends.mjs 查询
 *   - auto_inferred=true 表示该组件由脚本自动推断，AI 无需填写
 *
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 */

import { fetchRawCreativeTemplates } from "./lib/creative-template.mjs";

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

for (const field of ["account_id", "adgroup_id"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

if (input.dynamic_creative_type != null && input.dynamic_creative_type !== "DYNAMIC_CREATIVE_TYPE_PROGRAM" && input.creative_template_id == null) {
  console.log(JSON.stringify({ success: false, error: { message: `dynamic_creative_type 为 ${input.dynamic_creative_type} 时必须传入 creative_template_id` } }));
  process.exit(1);
}

const accountId = parseInt(input.account_id, 10);
const adgroupId = input.adgroup_id;

// 拉取创意形式原始数据（Step1: adgroups/get + Step2: creative_template/get）
const fetchResult = await fetchRawCreativeTemplates(
  accountId,
  adgroupId,
  {
    creative_template_id: input.creative_template_id,
    delivery_mode: input.delivery_mode,
    dynamic_creative_type: input.dynamic_creative_type,
    live_promoted_type: input.live_promoted_type,
  },
);

if (!fetchResult) {
  console.log(JSON.stringify({ success: false, error: { message: `获取创意形式失败，请检查 account_id/adgroup_id 是否正确` } }));
  process.exit(1);
}

const { tplList } = fetchResult;

// Step 3: 压缩为组件摘要
function summarize(templateList) {

  if (!templateList || templateList.length === 0) {
    return { success: true, templates: [] };
  }

  // 将 value_field 数组转为简洁的字段描述列表
  function buildFields(valueFields) {
    return (valueFields ?? []).map(f => {
      const entry = { name: f.name, required: f.valid?.required ?? false };
      if (f.valid?.enum_options?.length) {
        entry.enum = f.valid.enum_options.map(e => e.value);
      }
      return entry;
    });
  }

  const templates = templateList.map(tpl => {
    const rawComponents = tpl.creative_permissions?.creative_components ?? [];

    const components = rawComponents
      .filter(comp => comp.name)
      .map(comp => {
        const subTypeOptions = comp.component_sub_type_options ?? [];

        // 检查各 sub_type 的字段名集合是否完全一致
        const fieldNameSigs = subTypeOptions.map(opt =>
          (opt.value_field ?? []).map(f => f.name).sort().join('\0')
        );
        const allSameFields = fieldNameSigs.length <= 1 ||
          fieldNameSigs.every(s => s === fieldNameSigs[0]);

        // wechat_channels 由 create-creative.mjs 脚本自动从 brand 组件推断，AI 无需填写
        const isAutoInferred = comp.name === 'wechat_channels';

        let subTypesOut;
        let fieldsOut;

        if (!allSameFields) {
          // 不同 sub_type 字段集合有差异（如 brand），按 sub_type 分别展开 fields
          subTypesOut = subTypeOptions
            .filter(opt => opt.component_sub_type)
            .map(opt => ({ name: opt.component_sub_type, fields: buildFields(opt.value_field) }));
        } else {
          // 各 sub_type 字段相同（如 video/image 的各比例子类型），仅列名并合并 fields
          subTypesOut = subTypeOptions.map(opt => opt.component_sub_type).filter(Boolean);
          if (!isAutoInferred) {
            const fieldMap = new Map();
            for (const opt of subTypeOptions) {
              for (const f of (opt.value_field ?? [])) {
                if (!fieldMap.has(f.name)) {
                  const entry = { name: f.name, required: f.valid?.required ?? false };
                  if (f.valid?.enum_options?.length) {
                    entry._enumSet = new Set(f.valid.enum_options.map(e => e.value));
                  }
                  fieldMap.set(f.name, entry);
                } else if (f.valid?.enum_options?.length) {
                  // 同名字段出现在多个 sub_type 时，合并 enum 值（如 page_type 在不同 sub_type 下枚举不同）
                  const entry = fieldMap.get(f.name);
                  if (entry._enumSet) {
                    for (const e of f.valid.enum_options) entry._enumSet.add(e.value);
                  } else {
                    entry._enumSet = new Set(f.valid.enum_options.map(e => e.value));
                  }
                }
              }
            }
            // 将临时 _enumSet 转为 enum 数组
            for (const entry of fieldMap.values()) {
              if (entry._enumSet) {
                entry.enum = [...entry._enumSet];
                delete entry._enumSet;
              }
            }
            if (fieldMap.size > 0) fieldsOut = [...fieldMap.values()];
          }
        }

        return {
          name: comp.name,
          ...(comp.desc ? { desc: comp.desc } : {}),
          required: comp.valid?.required ?? false,
          min: comp.valid?.min_occurs ?? 0,
          max: comp.valid?.max_occurs ?? 1,
          has_depend: comp.valid?.has_depend ?? false,
          ...(isAutoInferred ? { auto_inferred: true, note: "由 create-creative.mjs 脚本自动推断，无需手动填写" } : {}),
          ...(subTypesOut?.length > 0 ? { sub_types: subTypesOut } : {}),
          ...(fieldsOut ? { fields: fieldsOut } : {}),
        };
      });

    const supportImpressionTrackingUrl = tpl.creative_permissions?.support_impression_tracking_url ?? false;
    const supportClickTrackingUrl = tpl.creative_permissions?.support_click_tracking_url ?? false;
    const supportMpa = tpl.support_mpa ?? false;
    const supportMpaImageTemplate = tpl.support_mpa_image_template ?? false;
    const supportMpaVideoTemplate = tpl.support_mpa_video_template ?? false;

    return {
      template_id: tpl.creative_template_id,
      template_name: tpl.creative_template_appellation || (tpl.creative_template_id === 0 ? "不指定创意形式" : `创意形式${tpl.creative_template_id}`),
      ...(supportImpressionTrackingUrl ? { support_impression_tracking_url: true } : {}),
      ...(supportClickTrackingUrl ? { support_click_tracking_url: true } : {}),
      ...(supportMpa ? { support_mpa: true } : {}),
      ...(supportMpaImageTemplate ? { support_mpa_image_template: true } : {}),
      ...(supportMpaVideoTemplate ? { support_mpa_video_template: true } : {}),
      components,
    };
  });

  return { success: true, templates };
}

console.log(JSON.stringify(summarize(tplList), null, 2));
