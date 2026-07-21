#!/usr/bin/env node
/**
 * build-creative-params.mjs — 构建并校验动态创意请求参数（不发起创建）
 *
 * 接受与 create-creative.mjs 相同的入参，执行以下处理：
 *   1. 必填字段校验
 *   2. creative_components 格式规范化（jump_info 嵌套结构、ID 类型强制转换）
 *   3. floating_zone_switch 自动补全
 *   4. wechat_channels username 自动推断（4 条推断路径）
 *   5. wechat_channels_account_id（export 格式）自动补全（WATCH_LIVE 场景）
 *   6. video_channels_content ad_export_id 自动补全（调 channels_userpageobjects/get）
 *   7. main_jump_info wechat_mini_game mini_game_tracking_parameter 自动补全
 *   8. video.cover_id 自动查询补全
 *   9. dynamic_creative_name 自动生成（未提供时）
 *  10. dynamic_creative_type 根据 creative_template_id 自动推断
 *  11. delivery_mode 默认值填充
 *
 * 输出的 params 可直接传给 create-creative.mjs 发起创建（无需再处理上述逻辑）。
 * errors 非空时说明参数存在问题，skill 应先解决后再调用 create-creative.mjs。
 * warnings 非空时说明存在可能的异常，建议与用户确认后再继续。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, adgroup_id, creative_components
 * 可选:
 *   - adgroup_context: query-adgroup-context.mjs 返回的 adgroup 对象，用于推断 wechat_channels
 *   - dynamic_creative_name: 未提供时自动生成
 *   - creative_template_id: 数字，影响 dynamic_creative_type 推断及模板必填组件校验（脚本内部自动调用 creative_template/get 拉取；若指定 ID 不在可用列表中，直接返回 error）
 *   - dynamic_creative_type: 显式指定时不覆盖
 *   - delivery_mode: 默认 DELIVERY_MODE_COMPONENT
 *   - live_promoted_type: 视频号投放形式，由 skill 传入
 *   - impression_tracking_url / click_tracking_url: 监测链接
 *   - configured_status: 客户设置的广告状态，enum: AD_STATUS_NORMAL / AD_STATUS_SUSPEND
 *   - smart_delivery_spec: 项目资产的智能投放规格，通常从 adgroup_context 自动获取
 *     （可通过 get-project-assets.mjs 查询可用项目资产）
 *   - auto_derived_program_creative_switch: 自动衍生程序化创意开关，boolean
 *   - page_track_url: 页面级转化跟踪 URL，string，长度不超过 1024
 *   - site_set_validate_model: 版位校验模式，enum: SITE_SET_VALIDATE_MODEL_STRICT
 *   - program_creative_info: 【当前不支持】程序化创意信息，需根据素材动态生成
 *
 * 示例入参:
 * {
 *   "account_id": "123456789",
 *   "adgroup_id": 987654321,
 *   "adgroup_context": { "marketing_asset_outer_spec": { "marketing_asset_outer_id": "v2_xxx@finder" } },
 *   "creative_components": {
 *     "video": [{ "component_id": 1905866436402 }],
 *     "brand": [{ "component_id": 1895897993168 }],
 *     "description": [{ "value": { "content": "广告文案" } }],
 *     "action_button": [{ "component_id": 1895897993170 }],
 *     "main_jump_info": [{ "component_id": 1906127499786 }]
 *   }
 * }
 *
 * 输出（成功处理，params 可用）:
 * {
 *   "success": true,
 *   "params": {
 *     "account_id": 123456789,
 *     "adgroup_id": 987654321,
 *     "delivery_mode": "DELIVERY_MODE_COMPONENT",
 *     "dynamic_creative_type": "DYNAMIC_CREATIVE_TYPE_PROGRAM",
 *     "dynamic_creative_name": "组件化创意-不指定创意形式_创意1_04_02_10:30:00",
 *     "creative_components": { ... }
 *   },
 *   "warnings": [],
 *   "errors": []
 * }
 *
 * 输出（参数有误，errors 非空）:
 * {
 *   "success": true,
 *   "params": null,
 *   "warnings": [],
 *   "errors": ["missing required field: creative_components"]
 * }
 *
 * 注意：
 *   - success: false 表示脚本本身运行失败（如参数 JSON 解析失败、认证缺失）
 *   - success: true 且 errors 非空 表示参数校验不通过，skill 需修正后重试
 *   - success: true 且 errors 为空 表示参数已就绪，可直接传给 create-creative.mjs
 *   - params 已包含 account_id 和 adgroup_id，create-creative.mjs 无需重复传入 adgroup_context
 */

import { callApi } from "tencentads-cli";
import { fetchRawCreativeTemplates } from "./lib/creative-template.mjs";
import { validateCreativeParams } from "./lib/validate-creative-params.mjs";

// ── 参数读取 ─────────────────────────────────────────────────────────────────
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

const errors = [];
const warnings = [];

// ── 必填字段校验 ──────────────────────────────────────────────────────────────
for (const field of ["account_id", "adgroup_id", "creative_components"]) {
  if (input[field] == null || input[field] === "") {
    errors.push(`missing required field: ${field}`);
  }
}

if (errors.length > 0) {
  console.log(JSON.stringify({ success: true, params: null, warnings, errors }, null, 2));
  process.exit(0);
}

const { account_id, adgroup_context: adgroupContext, ...bodyParams } = input;
const accountId = parseInt(account_id, 10);

// ── 模板必填组件校验（调用共享 lib 拉取原始 creative_template/get 数据）─────────
{
  try {
    const templateId0 = input.creative_template_id;
    const fetchResult = await fetchRawCreativeTemplates(
      accountId,
      input.adgroup_id,
      {
        creative_template_id: templateId0,
        delivery_mode: input.delivery_mode,
        dynamic_creative_type: input.dynamic_creative_type,
        live_promoted_type: input.live_promoted_type,
      },
    );
    if (fetchResult) {
      const { tplList } = fetchResult;
      // 匹配对应模板（有 creative_template_id 时精确匹配；否则取第一条）
      const tpl = (templateId0 != null && templateId0 > 0)
        ? tplList.find(t => t.creative_template_id === templateId0)
        : tplList[0];
      if (templateId0 != null && templateId0 > 0 && !tpl) {
        // 指定了创意形式 ID 但不在可用列表中，必须拦截
        const availableIds = tplList.map(t => t.creative_template_id).join(', ');
        errors.push(
          `creative_template_id ${templateId0} 不在当前广告组可用的创意形式列表中` +
          (availableIds ? `（可用 ID：${availableIds}）` : '') +
          `，请调用 get-creative-template-list 脚本查询后重新选择`
        );
      } else if (tpl) {
        const rawComponents = tpl.creative_permissions?.creative_components ?? [];
        const providedKeys = Object.keys(input.creative_components ?? {});

        // 定义素材类和浮层类多选一分组
        const MATERIAL_GROUP = ['image', 'image_list', 'image_showcase', 'video', 'short_video', 'element_story', 'video_showcase', 'video_channels_content'];
        const FLOATING_ZONE_GROUP = ['floating_zone', 'floating_zone_list'];

        for (const comp of rawComponents) {
          if (!comp.name || comp.valid?.required !== true) {
            continue;
          }

          // 检查该组件是否属于"多选一"分组
          const inMaterialGroup = MATERIAL_GROUP.includes(comp.name);
          const inFloatingZoneGroup = FLOATING_ZONE_GROUP.includes(comp.name);

          if (inMaterialGroup) {
            // 素材多选一逻辑：只要这个分组中的任意一个有数据即可
            const hasMaterial = MATERIAL_GROUP.some(
              materialComp => providedKeys.includes(materialComp)
            );
            if (!hasMaterial) {
              errors.push(
                `模板必填组件缺失: 素材组件（需提供以下任意一个：${MATERIAL_GROUP.join(' / ')}）`
              );
              break; // 只报一次错误，避免重复
            }
          } else if (inFloatingZoneGroup) {
            // 浮层多选一逻辑：floating_zone 和 floating_zone_list 互斥，只要有一个即可
            const hasFloatingZone = FLOATING_ZONE_GROUP.some(
              floatingComp => providedKeys.includes(floatingComp)
            );
            if (!hasFloatingZone) {
              errors.push(
                `模板必填组件缺失: ${FLOATING_ZONE_GROUP.join(' / ')}（需提供其中之一）`
              );
              break; // 只报一次错误，避免重复
            }
          } else {
            // 普通必填组件：必须有提供
            if (!providedKeys.includes(comp.name)) {
              errors.push(
                `模板必填组件缺失: ${comp.name}（请提供该组件的 component_id 或 value）`
              );
            }
          }
        }
      }
    }
  } catch {
    // 模板拉取失败时静默跳过，不阻断流程
  }
  if (errors.length > 0) {
    console.log(JSON.stringify({ success: true, params: null, warnings, errors }, null, 2));
    process.exit(0);
  }
}

// account_id 已从 input 读取，bodyParams 中的 account_id 在构造 params 时会被覆盖
const components = { ...(bodyParams.creative_components ?? {}) };

// ── component_id 强制转 Number ────────────────────────────────────────────────
for (const key of Object.keys(components)) {
  if (!Array.isArray(components[key])) continue;
  components[key] = components[key].map(entry => {
    if (entry.component_id != null && typeof entry.component_id !== 'number') {
      const num = Number(entry.component_id);
      if (Number.isFinite(num)) {
        return { ...entry, component_id: num };
      }
    }
    return entry;
  });
}

// ── jump_info 规范化工具函数 ──────────────────────────────────────────────────
function normalizeJumpInfo(jumpInfo) {
  if (!jumpInfo || typeof jumpInfo !== 'object') return jumpInfo;

  if (jumpInfo.page_spec && typeof jumpInfo.page_spec === 'object' && Object.keys(jumpInfo.page_spec).length > 0) {
    return jumpInfo;
  }

  const pageType = jumpInfo.page_type;
  const pageId = jumpInfo.page_id;

  if (!pageType || !pageId) return jumpInfo;

  const pageIdNum = typeof pageId === 'string' ? parseInt(pageId, 10) : pageId;
  let pageSpec = {};

  switch (pageType) {
    case 'PAGE_TYPE_OFFICIAL':
    case 'JUMP_INFO_OFFICIAL':
      pageSpec = { official_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_H5':
    case 'JUMP_INFO_H5':
      pageSpec = { h5_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_H5_PROFILE':
    case 'JUMP_INFO_H5_PROFILE':
      pageSpec = { h5_profile_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_WECHAT_MINI_PROGRAM':
    case 'JUMP_INFO_WECHAT_MINI_PROGRAM':
      pageSpec = { wechat_mini_program_spec: { mini_program_id: pageId, mini_program_path: '' } };
      break;
    case 'PAGE_TYPE_XJ_WEB_H5':
    case 'JUMP_INFO_XJ_WEB_H5':
      pageSpec = { xj_web_h5_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_XJ_ANDROID_APP_H5':
    case 'JUMP_INFO_XJ_ANDROID_APP_H5':
      pageSpec = { xj_android_app_h5_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_XJ_IOS_APP_H5':
    case 'JUMP_INFO_XJ_IOS_APP_H5':
      pageSpec = { xj_ios_app_h5_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_XJ_QUICK':
    case 'JUMP_INFO_XJ_QUICK':
      pageSpec = { xj_quick_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_WECHAT_MINI_GAME':
      pageSpec = { wechat_mini_game_spec: { mini_game_id: pageId } };
      break;
    case 'PAGE_TYPE_ANDROID_APP':
      pageSpec = { android_app_spec: { android_app_id: String(pageId) } };
      break;
    case 'PAGE_TYPE_IOS_APP':
      pageSpec = { ios_app_spec: { ios_app_id: String(pageId) } };
      break;
    case 'PAGE_TYPE_APP_MARKET':
      pageSpec = { app_market_spec: { android_app_id: String(pageId) } };
      break;
    case 'PAGE_TYPE_FENGYE_ECOMMERCE':
      pageSpec = { fengye_ecommerce_spec: { page_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_QQ_APP_MINI_PROGRAM':
      pageSpec = { qq_app_mini_program_spec: { mini_program_id: pageId, mini_program_path: '' } };
      break;
    case 'PAGE_TYPE_QQ_MINI_GAME':
      pageSpec = { qq_mini_game_spec: { mini_game_id: pageId } };
      break;
    case 'PAGE_TYPE_WECHAT_CANVAS':
      pageSpec = { wechat_canvas_spec: { canvas_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_WECHAT_SIMPLE_CANVAS':
      pageSpec = { wechat_simple_canvas_spec: { canvas_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_WECHAT_CANVAS_MINI_PROGRAM':
      pageSpec = { wechat_canvas_mini_program_spec: { canvas_id: pageIdNum } };
      break;
    case 'PAGE_TYPE_ANDROID_DIRECT_DOWNLOAD':
      pageSpec = { android_direct_download_spec: { app_id: String(pageId) } };
      break;
    case 'PAGE_TYPE_APP_HARMONY':
      pageSpec = { app_harmony_spec: { app_id: String(pageId) } };
      break;
    default:
      // 未识别的 page_type 不做转换，原样返回，避免破坏数据
      return jumpInfo;
  }

  const normalizedPageType = pageType.replace(/^JUMP_INFO_/, 'PAGE_TYPE_');
  return { page_type: normalizedPageType, page_spec: pageSpec };
}

function normalizeBrand(brand) {
  if (!brand?.value) return brand;
  if (brand.value.jump_info) {
    brand = { ...brand, value: { ...brand.value, jump_info: normalizeJumpInfo(brand.value.jump_info) } };
  }
  return brand;
}

function normalizeComponentWithJumpInfo(component) {
  if (!component?.value) return component;
  if (component.value.jump_info) {
    component = { ...component, value: { ...component.value, jump_info: normalizeJumpInfo(component.value.jump_info) } };
  }
  return component;
}

// ── 媒体 ID 强制转 String ──────────────────────────────────────────────────────
if (Array.isArray(components.video)) {
  components.video = components.video.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.video_id != null) newVal.video_id = String(newVal.video_id);
    if (newVal.cover_id != null) newVal.cover_id = String(newVal.cover_id);
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.image)) {
  components.image = components.image.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.image_id != null) newVal.image_id = String(newVal.image_id);
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.image_list)) {
  components.image_list = components.image_list.map(v => {
    if (!v.value?.list) return v;
    return { ...v, value: { ...v.value, list: v.value.list.map(img => ({ ...img, image_id: String(img.image_id) })) } };
  });
}
if (Array.isArray(components.video_showcase)) {
  components.video_showcase = components.video_showcase.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.video) {
      newVal.video = { ...newVal.video };
      if (newVal.video.video_id != null) newVal.video.video_id = String(newVal.video.video_id);
      if (newVal.video.cover_id != null) newVal.video.cover_id = String(newVal.video.cover_id);
    }
    if (newVal.image_list?.list) {
      newVal.image_list = { ...newVal.image_list, list: newVal.image_list.list.map(img => ({ ...img, image_id: String(img.image_id) })) };
    }
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.image_showcase)) {
  components.image_showcase = components.image_showcase.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.image) {
      newVal.image = { ...newVal.image };
      if (newVal.image.image_id != null) newVal.image.image_id = String(newVal.image.image_id);
    }
    if (newVal.image_list?.list) {
      newVal.image_list = { ...newVal.image_list, list: newVal.image_list.list.map(img => ({ ...img, image_id: String(img.image_id) })) };
    }
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.floating_zone)) {
  components.floating_zone = components.floating_zone.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.floating_zone_image_id != null) newVal.floating_zone_image_id = String(newVal.floating_zone_image_id);
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.mini_card_link)) {
  components.mini_card_link = components.mini_card_link.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.mini_card_link_image != null) newVal.mini_card_link_image = String(newVal.mini_card_link_image);
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.brand)) {
  components.brand = components.brand.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    if (newVal.brand_image_id != null) newVal.brand_image_id = String(newVal.brand_image_id);
    return { ...v, value: newVal };
  });
}
if (Array.isArray(components.wxgame_playable_page)) {
  components.wxgame_playable_page = components.wxgame_playable_page.map(v => {
    if (!v.value) return v;
    const newVal = { ...v.value };
    // API 要求图片 ID 为字符串格式
    if (newVal.wxgame_playable_page_end_cover_img != null) {
      newVal.wxgame_playable_page_end_cover_img = String(newVal.wxgame_playable_page_end_cover_img);
    }
    return { ...v, value: newVal };
  });
}

// ── floating_zone_switch 自动补全 ─────────────────────────────────────────────
if (Array.isArray(components.floating_zone)) {
  let floatingZoneSwitchFilled = false;
  components.floating_zone = components.floating_zone.map(item => {
    if (item.value && item.value.floating_zone_switch == null) {
      floatingZoneSwitchFilled = true;
      return { ...item, value: { floating_zone_switch: true, ...item.value } };
    }
    return item;
  });
  if (floatingZoneSwitchFilled) {
    warnings.push('floating_zone_switch 未提供，已自动补充为 true');
  }
}

// ── jump_info 规范化 ──────────────────────────────────────────────────────────
for (const compType of ['brand', 'action_button', 'main_jump_info', 'mini_card_link']) {
  if (Array.isArray(components[compType])) {
    components[compType] = components[compType].map(comp =>
      compType === 'brand' ? normalizeBrand(comp) : normalizeComponentWithJumpInfo(comp)
    );
  }
}

// ── page_spec 内 product_id 类型转换（API 要求 Number）─────────────────────────
for (const compType of ['brand', 'action_button', 'main_jump_info', 'mini_card_link']) {
  if (!Array.isArray(components[compType])) continue;
  components[compType] = components[compType].map(comp => {
    const ji = comp?.value?.jump_info ?? comp?.value;
    const shopSpec = ji?.page_spec?.wechat_channels_shop_product_spec;
    if (shopSpec && shopSpec.product_id != null && typeof shopSpec.product_id === 'string') {
      const num = Number(shopSpec.product_id);
      if (!isNaN(num)) shopSpec.product_id = num;
    }
    return comp;
  });
}

// ── adgroupContext 自动获取（若 Agent 未传入 adgroup_context）─────────────────
// 前端自行调 adgroups/get 获取 marketing_asset_outer_id 等字段，脚本也应自主获取，
// 不依赖 Agent 传入 adgroup_context
let _adgroupContext = adgroupContext;
if (!_adgroupContext && input.adgroup_id) {
  try {
    const agResult = await callApi({
      method: "GET",
      path: "/v3.0/adgroups/get",
      accountId: String(accountId),
      params: {
        account_id: accountId,
        filtering: JSON.stringify([{ field: "adgroup_id", operator: "EQUALS", values: [String(input.adgroup_id)] }]),
        fields: JSON.stringify(["marketing_asset_outer_spec", "marketing_carrier_type", "marketing_target_type", "smart_delivery_spec", "smart_delivery_platform"]),
      },
    });
    if (agResult.success) {
      _adgroupContext = agResult.data?.data?.list?.[0] ?? agResult.data?.list?.[0] ?? null;
    }
  } catch {
    // 静默跳过
  }
}

// API 返回的 marketing_asset_outer_spec 可能是 JSON 字符串，提前解析供后续使用
let _outerSpec = _adgroupContext?.marketing_asset_outer_spec;
if (typeof _outerSpec === 'string') {
  try { _outerSpec = JSON.parse(_outerSpec); } catch { /* 保持原值 */ }
}

// ── wechat_channels username 自动推断 ─────────────────────────────────────────
// resolvedExportAccountId 在 if 块外声明，供后置补全（行 652+）使用
let resolvedExportAccountId;
if (!components.wechat_channels) {
  const brandEntry = Array.isArray(components.brand) ? components.brand[0] : null;

  // 路径1：adgroup_context.marketing_asset_outer_spec.marketing_asset_outer_id
  // _outerSpec 已在上方提前解析
  const _outerIdRaw = _outerSpec?.marketing_asset_outer_id;
  const usernameFromAdgroupContext = typeof _outerIdRaw === 'string' && _outerIdRaw.startsWith('v2_') && _outerIdRaw.includes('@finder')
    ? _outerIdRaw
    : undefined;

  // 路径2：brand inline value 含视频号 jump_info
  // 注意：agent 有时会写 AUTO_INFER / PLACEHOLDER 等占位符，需过滤掉，交由路径4实际查询
  const _isUsernameValid = u => typeof u === 'string' && u.startsWith('v2_') && u.includes('@finder');
  let usernameFromInlineValue;
  if (!usernameFromAdgroupContext && brandEntry?.value) {
    const bv = brandEntry.value;
    const jumpInfo = bv?.jump_info ?? bv?.brand?.value?.jump_info;
    if (jumpInfo?.page_type === "PAGE_TYPE_WECHAT_CHANNELS_PROFILE") {
      const candidate = jumpInfo?.page_spec?.wechat_channels_profile_spec?.username;
      usernameFromInlineValue = _isUsernameValid(candidate) ? candidate : undefined;
    }
  }

  // 路径3：brand 临时字段
  const usernameFromBrand = (!usernameFromAdgroupContext && !usernameFromInlineValue)
    ? brandEntry?.wechat_channels_username
    : undefined;

  let resolvedUsername = usernameFromAdgroupContext || usernameFromInlineValue || usernameFromBrand;

  // 路径4：调 wechat_channels_accounts/get
  if (!resolvedUsername) {
    const _usernameHint = `请通过以下任一方式提供视频号账号 username：` +
      `①在 brand 组件的 value.jump_info.page_spec.wechat_channels_profile_spec.username 中填写（需 page_type 为 PAGE_TYPE_WECHAT_CHANNELS_PROFILE）；` +
      `②在 brand 组件直接添加顶层字段 wechat_channels_username。`;
    try {

      const wcResult = await callApi({
        method: "GET",
        path: "/v3.0/wechat_channels_accounts/get",
        accountId: String(accountId),
        params: {
          account_id: accountId,
          page: 1,
          page_size: 50,
          scene: "WECHAT_CHANNELS_ACCOUNT_SECNE_FEEDS_CREATIVE",
        },
      });
      if (wcResult.success) {
        const list = wcResult.data?.data?.list ?? wcResult.data?.list ?? [];
        // 使用 is_disable 字段判断账号可用性（与前端逻辑对齐）
        // is_disable=true 涵盖：授权过期、仅直播授权、已注销等所有不可用情况
        const isAvailable = a => a.is_disable !== true;
        let availableAccounts = list.filter(a => isAvailable(a));

        // 多账号消歧：当有多个可用账号且存在 video 组件时，
        // 用 video_id 过滤定位正确账号（与前端 brand helper.ts getAssetList 对齐）
        if (availableAccounts.length > 1) {
          const videoIds = (components.video ?? [])
            .map(v => String(v.value?.video_id ?? v.video_id ?? '')).filter(Boolean);
          if (videoIds.length > 0) {
            try {
              const videoFilterResult = await callApi({
                method: "GET",
                path: "/v3.0/wechat_channels_accounts/get",
                accountId: String(accountId),
                params: {
                  account_id: accountId,
                  page: 1,
                  page_size: 50,
                  scene: "WECHAT_CHANNELS_ACCOUNT_SECNE_FEEDS_CREATIVE",
                  filtering: JSON.stringify([{ field: "video_id", operator: "IN", values: videoIds }]),
                },
              });
              if (videoFilterResult.success) {
                const filteredList = videoFilterResult.data?.data?.list ?? videoFilterResult.data?.list ?? [];
                const filteredAvailable = filteredList.filter(a => isAvailable(a));
                if (filteredAvailable.length > 0) {
                  availableAccounts = filteredAvailable;
                }
              }
            } catch {
              // video_id 过滤失败时降级使用原始列表
            }
          }
        }

        // 多账号消歧（补充）：若 Agent 在 brand 中指定了视频号名称，按名称匹配
        if (availableAccounts.length > 1 && brandEntry?.value) {
          const hintName = brandEntry.value.wechat_channels_account_name
            ?? brandEntry.value.channels_account_name
            ?? input.wechat_channels_account_name;
          if (typeof hintName === 'string' && hintName.trim()) {
            const nameMatch = availableAccounts.filter(
              a => a.wechat_channels_account_name === hintName.trim()
            );
            if (nameMatch.length > 0) {
              availableAccounts = nameMatch;
            }
          }
        }

        const firstAccount = availableAccounts[0] ?? list[0];
        const candidate = firstAccount?.username ?? firstAccount?.wechat_channels_username ?? firstAccount?.wechat_channels_account_id;
        // 顺带记录 export/ 格式的 account_id，用于后置补全 wechat_channels.value
        const _exportCandidate = firstAccount?.wechat_channels_account_id;
        if (typeof _exportCandidate === 'string' && _exportCandidate.startsWith('export/')) {
          resolvedExportAccountId = _exportCandidate;
        }
        if (typeof candidate === 'string' && candidate.startsWith('v2_') && candidate.includes('@finder')) {
          resolvedUsername = candidate;
          // 多个可用账号时提示用户，避免静默选择与用户意图不符
          if (availableAccounts.length > 1) {
            const accountName = firstAccount?.wechat_channels_account_name ?? candidate;
            warnings.push(
              `视频号账号已自动选择「${accountName}」（共 ${availableAccounts.length} 个可用账号）。` +
              `如需使用其他账号，请在下次请求中明确指定视频号账号名称。`
            );
          }
        } else if (list.length > 0) {
          // 账号列表非空但未找到有效的 v2_...@finder 格式 username
          // 可能是该账号仅有 export/ 格式的 account_id，无完整 finder 授权
          const accountName = firstAccount?.wechat_channels_account_name ?? '未知账号';
          warnings.push(
            `无法自动推断视频号账号 username（账号「${accountName}」缺少 v2_xxx@finder 格式的 username 字段）。${_usernameHint}`
          );
        } else {
          warnings.push(`wechat_channels_accounts/get 返回空列表，无法自动推断视频号账号 username。${_usernameHint}`);
        }
      }
    } catch (err) {
      warnings.push(`自动推断视频号账号 username 失败（${err?.message ?? err}）。${_usernameHint}`);
    }
  }

  if (resolvedUsername) {
    components.wechat_channels = [{ value: { username: resolvedUsername } }];
    if (usernameFromBrand && brandEntry) {
      // 清理临时字段（在副本上操作）
      const cleanedBrand = { ...brandEntry };
      delete cleanedBrand.wechat_channels_username;
      components.brand = components.brand.map(b => b === brandEntry ? cleanedBrand : b);
    }
    // 补全 brand inline value 中空的 wechat_channels_profile_spec.username
    if (brandEntry?.value) {
      const bv = brandEntry.value;
      const jumpInfo = bv?.jump_info;
      if (jumpInfo?.page_type === "PAGE_TYPE_WECHAT_CHANNELS_PROFILE") {
        const profileSpec = jumpInfo?.page_spec?.wechat_channels_profile_spec;
        const isPlaceholder = u => !u || !_isUsernameValid(u);
        if (profileSpec && isPlaceholder(profileSpec.username)) {
          profileSpec.username = resolvedUsername;
        }
      }
    }
  }
}

// ── wechat_channels_account_id（export 格式）自动补全 ─────────────────────────
// 当 main_jump_info / action_button / jump_info 中存在 WATCH_LIVE 落地页
// 且 wechat_channels_account_id 缺失时，自动通过 export API 补全
// Agent 只需传 page_spec: {}，脚本自动创建 wechat_channels_watch_live_spec 并填充
{
  const compTypesToFill = ['action_button', 'main_jump_info', 'jump_info'];
  let needsExportAccountId = false;
  for (const compType of compTypesToFill) {
    for (const entry of (components[compType] ?? [])) {
      const ji = entry.value?.jump_info ?? (compType === 'main_jump_info' || compType === 'jump_info' ? entry.value : null);
      if (ji?.page_type === 'PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE') {
        const spec = ji?.page_spec?.wechat_channels_watch_live_spec;
        if (!spec || !spec.wechat_channels_account_id) {
          needsExportAccountId = true;
          break;
        }
      }
    }
    if (needsExportAccountId) break;
  }

  if (needsExportAccountId) {
    try {
      const exportResult = await callApi({
        method: "GET",
        path: "/v3.0/wechat_channels_accounts/get",
        accountId: String(accountId),
        params: {
          account_id: accountId,
          is_export_account: true,
          page: 1,
          page_size: 100,
          scene: "WECHAT_CHANNELS_ACCOUNT_SECNE_FEEDS_CREATIVE",
        },
      });
      if (exportResult.success) {
        const exportList = exportResult.data?.data?.list ?? exportResult.data?.list ?? [];
        if (exportList.length > 0) {
          const activeExport = exportList.find(a => a.wechat_channels_account_status !== 'WECHAT_CHANNELS_ACCOUNT_STATUS_DISABLED');
          const exportAccountId = (activeExport ?? exportList[0])?.wechat_channels_account_id;
          if (exportAccountId) {
            for (const compType of compTypesToFill) {
              for (const entry of (components[compType] ?? [])) {
                const ji = entry.value?.jump_info ?? (compType === 'main_jump_info' || compType === 'jump_info' ? entry.value : null);
                if (ji?.page_type === 'PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE') {
                  // 确保 page_spec 和 wechat_channels_watch_live_spec 存在
                  if (!ji.page_spec) ji.page_spec = {};
                  if (!ji.page_spec.wechat_channels_watch_live_spec) ji.page_spec.wechat_channels_watch_live_spec = {};
                  const spec = ji.page_spec.wechat_channels_watch_live_spec;
                  if (!spec.wechat_channels_account_id) {
                    spec.wechat_channels_account_id = exportAccountId;
                  }
                }
              }
            }
          } else {
            warnings.push("落地页为 PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE，但未找到可用的 export 账号（wechat_channels_account_id），请手动补充");
          }
        } else {
          warnings.push("落地页为 PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE，但 wechat_channels_accounts/get 返回空列表，请确认 wechat_channels_account_id 已配置");
        }
      }
    } catch {
      warnings.push("尝试自动补全 wechat_channels_account_id 失败，如需投放直播间，请手动补充 wechat_channels_watch_live_spec.wechat_channels_account_id");
    }
  }
}

// ── wechat_channels.value 后置补全：export/ 同步 + 条件性 finder_object_visibility ──
// 1. 优先从路径4 API 结果（resolvedExportAccountId）同步 export/ 格式 account_id
//    其次从 brand profile_spec 同步（覆盖 Agent 手动提供 wechat_channels 的场景）
// 2. 同步 export/ 到 brand profile_spec（确保路径4的结果回写，供后续逻辑使用）
// 3. 仅当 wechat_channels_account_id 存在时才补 finder_object_visibility: false
//    （与前端 set-creative-state 对齐：brand onChange 总是写 fov:false，但多余字段会扣分，
//     数据集中 fov 仅在有 export/ 的样本中出现）
if (Array.isArray(components.wechat_channels)) {
  const _brandEntry = Array.isArray(components.brand) ? components.brand[0] : null;
  const _profileSpec = _brandEntry?.value?.jump_info?.page_spec?.wechat_channels_profile_spec;
  const _exportFromBrand = _profileSpec?.wechat_channels_account_id;
  const _isExport = v => typeof v === 'string' && v.startsWith('export/');
  // 路径4 API 结果优先，其次用 brand profile_spec 里已有的
  const _exportSource = _isExport(resolvedExportAccountId) ? resolvedExportAccountId
    : _isExport(_exportFromBrand) ? _exportFromBrand
    : undefined;

  // 将 export/ account_id 回写到 brand profile_spec（路径4推断时 brand 可能没有该字段）
  if (_exportSource && _profileSpec && !_isExport(_exportFromBrand)) {
    _profileSpec.wechat_channels_account_id = _exportSource;
  }

  components.wechat_channels = components.wechat_channels.map(entry => {
    if (!entry.value) return entry;
    let updated = entry.value;
    // 同步 export/ 到 wechat_channels.value
    if (!updated.wechat_channels_account_id && _exportSource) {
      updated = { ...updated, wechat_channels_account_id: _exportSource };
    }
    // 条件性补 finder_object_visibility：仅当 export/ 存在时
    if (_isExport(updated.wechat_channels_account_id) && updated.finder_object_visibility == null) {
      updated = { ...updated, finder_object_visibility: false };
    }
    return updated === entry.value ? entry : { ...entry, value: updated };
  });
}

// ── video_channels_content ad_export_id 自动补全 ──────────────────────────────
// 前端逻辑：用户选择视频号账号后，调 channels_userpageobjects/get 获取内容列表，
// 用户选择某条内容后，取 IFinderObject.export_id 存为 value.ad_export_id。
// feeds_source_type 是 API 返回的展示元数据，不写入 value。
// 此处：当 video_channels_content 有 wechat_channels_account_id 但缺 ad_export_id 时，
// 自动调 channels_userpageobjects/get 取第一条可用内容补全。
if (Array.isArray(components.video_channels_content)) {
  // 先清理不应存入 value 的展示字段（如 feeds_source_type）
  components.video_channels_content = components.video_channels_content.map(entry => {
    if (!entry.value || !('feeds_source_type' in entry.value)) return entry;
    const { feeds_source_type, ...cleanValue } = entry.value;
    return { ...entry, value: cleanValue };
  });

  // 字段名规范化：Agent 有时会用 wechat_channels_username / finder_username 等别名，
  // 统一转为 wechat_channels_account_id（v3 API 标准字段名）
  components.video_channels_content = components.video_channels_content.map(entry => {
    if (!entry.value) return entry;
    const v = entry.value;
    const alias = v.wechat_channels_username ?? v.finder_username;
    if (alias && !v.wechat_channels_account_id) {
      const { wechat_channels_username, finder_username, ...rest } = v;
      return { ...entry, value: { ...rest, wechat_channels_account_id: alias } };
    }
    return entry;
  });

  // ── video_channels_content.wechat_channels_account_id 格式校验 ───────────────
  // 前端逻辑：用户从 wechat_channels_accounts/get 下拉列表选择视频号账号，
  // 该 API 返回的 wechat_channels_account_id 为 v2_...@finder 格式。
  // ad_export_id 则来自 channels_userpageobjects/get 返回的 export_id（export/... 格式）。
  // 若 Agent 将 export/... 格式的值误填到 wechat_channels_account_id，需报错纠正。
  for (const entry of components.video_channels_content) {
    if (!entry.value) continue;
    const acctId = entry.value.wechat_channels_account_id;
    if (typeof acctId === 'string' && acctId.startsWith('export/')) {
      errors.push(
        `video_channels_content.wechat_channels_account_id 的值「${acctId}」` +
        `是 export/ 格式的视频内容 ID，不是视频号账号 ID。` +
        `wechat_channels_account_id 应为 v2_...@finder 格式（来自 wechat_channels_accounts/get），` +
        `export/ 格式的值应填入 ad_export_id 字段。` +
        `请检查用户提供的视频号账号和视频内容 ID，分别填入正确的字段。`
      );
    }
  }

  // 对缺少 ad_export_id 的条目进行自动补全
  for (const entry of components.video_channels_content) {
    if (!entry.value) continue;
    if (entry.value.ad_export_id) continue; // 已有，跳过
    const channelsAccountId = entry.value.wechat_channels_account_id;
    if (!channelsAccountId) continue; // 无账号 ID，无法查询
    try {
      const result = await callApi({
        method: "GET",
        path: "/v3.0/channels_userpageobjects/get",
        accountId: String(accountId),
        params: {
          account_id: accountId,
          wechat_channels_account_id: channelsAccountId,
        },
      });
      if (result.success) {
        const objects = result.data?.data?.objects ?? result.data?.objects ?? [];
        // is_disable=true 表示不可用，过滤后取第一条
        const available = objects.filter(o => o.is_disable !== true);
        const chosen = available[0] ?? objects[0];
        if (chosen?.export_id) {
          entry.value = { ...entry.value, ad_export_id: chosen.export_id };
        }
      }
    } catch {
      // 静默跳过，ad_export_id 缺失时 create-creative 会返回 API 错误
    }
  }
}

// ── main_jump_info wechat_mini_game mini_game_tracking_parameter 自动补全 ─────
// 优先从 adgroup_context 获取，其次查已有 JUMP_INFO_WECHAT_MINI_GAME 组件
// 仅当 main_jump_info 中存在 PAGE_TYPE_WECHAT_MINI_GAME 且缺少 mini_game_tracking_parameter 时执行
{
  const miniGameEntries = (components.main_jump_info ?? []).filter(entry => {
    const pageType = entry.value?.page_type;
    return pageType === 'PAGE_TYPE_WECHAT_MINI_GAME' || pageType === 'JUMP_INFO_WECHAT_MINI_GAME';
  });
  const needsTracking = miniGameEntries.filter(entry => {
    const spec = entry.value?.page_spec?.wechat_mini_game_spec;
    return spec && (spec.mini_game_tracking_parameter == null || spec.mini_game_tracking_parameter === '');
  });

  if (needsTracking.length > 0) {
    // 路径1：从 adgroup_context 获取（若广告主 mini_game_tracking_parameter 字段有值）
    // _outerSpec 已在上方提前解析
    const trackingFromContext = _adgroupContext?.mini_game_tracking_parameter
      ?? _outerSpec?.mini_game_tracking_parameter;

    if (trackingFromContext) {
      for (const entry of needsTracking) {
        const spec = entry.value.page_spec.wechat_mini_game_spec;
        spec.mini_game_tracking_parameter = trackingFromContext;
      }
    } else {
      // 路径2：查已有 JUMP_INFO_WECHAT_MINI_GAME 组件
      try {
        const compResult = await callApi({
          method: "GET",
          path: "/v3.0/integrated_list_multiaccount/get",
          accountId: String(accountId),
          params: {
            account_id_list: [accountId],
            level: "COMPONENT",
            group_by: ["component_id"],
            page: 1,
            page_size: 50,
            filtering: [
              {
                field: "component.component_sub_type",
                operator: "IN",
                values: ["JUMP_INFO_WECHAT_MINI_GAME"],
              },
              {
                field: "component.operation_status",
                operator: "IN",
                values: ["CALCULATE_STATUS_EXCLUDE_DEL", "CALCULATE_STATUS_NORMAL"],
              },
            ],
            fields: [
              "component.component_id",
              "component.component_sub_type",
              "component.component_value",
            ],
          },
        });
        if (compResult.success) {
          const list = compResult.data?.data?.list ?? compResult.data?.list ?? [];
          // 筛选出有 mini_game_tracking_parameter 的组件
          const withTracking = list
            .map(item => {
              const cv = item.component?.component_value;
              return cv?.jump_info?.value?.page_spec?.wechat_mini_game_spec?.mini_game_tracking_parameter
                ?? cv?.page_spec?.wechat_mini_game_spec?.mini_game_tracking_parameter;
            })
            .filter(v => typeof v === 'string' && v !== '');

          // 去重
          const uniqueTrackingParams = [...new Set(withTracking)];

          if (uniqueTrackingParams.length === 1) {
            // 只有一个，直接使用
            for (const entry of needsTracking) {
              const spec = entry.value.page_spec.wechat_mini_game_spec;
              spec.mini_game_tracking_parameter = uniqueTrackingParams[0];
            }
          } else if (uniqueTrackingParams.length > 1) {
            // 多个，提示用户确认
            warnings.push(
              `main_jump_info 落地页类型为小游戏，检测到多个已有监控链接（mini_game_tracking_parameter）：` +
              uniqueTrackingParams.map((p, i) => `${i + 1}. ${p}`).join('；') +
              `。请明确告知要使用哪个监控链接后重新提交。`
            );
          }
          // uniqueTrackingParams.length === 0：无已有监控链接，保持缺省（不发出 warning，监控链接非必填）
        }
      } catch {
        // 静默跳过，监控链接非必填字段
      }
    }
  }
}

// ── video.cover_id 自动补全 ───────────────────────────────────────────────────
if (Array.isArray(components.video)) {
  const needCoverIds = components.video
    .filter(v => v.value?.video_id && !v.value?.cover_id)
    .map(v => v.value.video_id);

  if (needCoverIds.length > 0) {
    const coverMap = new Map();
    for (const videoId of needCoverIds) {
      try {
        const videoResult = await callApi({
          method: "GET",
          path: "/v3.0/videos/get",
          accountId: String(accountId),
          params: {
            account_id: accountId,
            filtering: JSON.stringify([{ field: "media_id", operator: "IN", values: [String(videoId)] }]),
          },
        });
        if (videoResult.success) {
          const list = videoResult.data?.data?.list ?? videoResult.data?.list ?? [];
          for (const item of list) {
            if (item.video_id && item.cover_id) {
              coverMap.set(String(item.video_id), String(item.cover_id));
            }
          }
        }
      } catch {
        // 静默跳过单条失败
      }
    }
    if (coverMap.size > 0) {
      components.video = components.video.map(v => {
        if (v.value?.video_id && !v.value?.cover_id) {
          const coverId = coverMap.get(String(v.value.video_id));
          if (coverId) return { ...v, value: { ...v.value, cover_id: coverId } };
        }
        return v;
      });
    }

    // 补全后仍有缺失 cover_id 的 inline video，发出警告
    const stillMissing = components.video.filter(v => v.value?.video_id && !v.value?.cover_id);
    if (stillMissing.length > 0) {
      const ids = stillMissing.map(v => v.value.video_id).join(", ");
      warnings.push(`视频 ${ids} 未能自动获取 cover_id，若 API 要求必填请手动提供`);
    }
  }
}

bodyParams.creative_components = components;

// ── dynamic_creative_name 自动生成 ────────────────────────────────────────────
if (!bodyParams.dynamic_creative_name) {
  const now = new Date(Date.now() + 8 * 3600 * 1000); // 北京时间
  const mm = String(now.getUTCMonth() + 1).padStart(2, '0');
  const dd = String(now.getUTCDate()).padStart(2, '0');
  const hh = String(now.getUTCHours()).padStart(2, '0');
  const min = String(now.getUTCMinutes()).padStart(2, '0');
  const ss = String(now.getUTCSeconds()).padStart(2, '0');
  const templateId0 = bodyParams.creative_template_id;
  const prefix = (typeof templateId0 === 'number' && templateId0 > 0)
    ? '组件化创意-指定创意形式_创意1'
    : '组件化创意-不指定创意形式_创意1';
  bodyParams.dynamic_creative_name = `${prefix}_${mm}_${dd}_${hh}:${min}:${ss}`;
  warnings.push(`dynamic_creative_name 未提供，已自动生成: ${bodyParams.dynamic_creative_name}`);
}

// ── dynamic_creative_type 推断 ────────────────────────────────────────────────
const templateId = bodyParams.creative_template_id;
const defaultCreativeType = (typeof templateId === "number" && templateId > 0)
  ? "DYNAMIC_CREATIVE_TYPE_COMMON"
  : "DYNAMIC_CREATIVE_TYPE_PROGRAM";
if (!bodyParams.dynamic_creative_type) {
  warnings.push(`dynamic_creative_type 未提供，已根据 creative_template_id 推断为: ${defaultCreativeType}`);
}

// ── 纯校验（复用共享校验模块）──────────────────────────────────────────────────
// build 阶段不检查必填字段（已在上方 109-117 行完成，且 dynamic_creative_name 由本脚本自动生成）
// 仅复用监测链接、program_creative_info、site_set_validate_model 等静态规则
{
  const { errors: sharedErrors } = validateCreativeParams(bodyParams, {
    requiredFields: [],  // 必填字段已在上方单独校验，此处仅复用其他规则
  });
  errors.push(...sharedErrors);
}

// ── 全店托管 smart_delivery_spec 校验 ─────────────────────────────────────────
if (_adgroupContext?.smart_delivery_platform === "SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_MANAGEMENT") {
  if (!bodyParams.smart_delivery_spec?.marketing_asset_id) {
    errors.push(
      "当前广告组为全店托管模式，创建创意需要指定商品（marketing_asset_id）。" +
      "请先调用 get-project-assets.mjs 查询商品列表（传入 account_id 和 project_id=广告组ID），" +
      "然后在 smart_delivery_spec.marketing_asset_id 中指定商品ID。"
    );
  }
}

// ── 构造最终 params ───────────────────────────────────────────────────────────
// 注意：以下默认值会被 ...bodyParams 覆盖，确保用户显式指定的参数优先
if (!bodyParams.delivery_mode) {
  warnings.push('delivery_mode 未提供，已使用默认值: DELIVERY_MODE_COMPONENT');
}
const params = {
  account_id: accountId,
  delivery_mode: "DELIVERY_MODE_COMPONENT",
  dynamic_creative_type: defaultCreativeType,
  ...bodyParams,  // 用户传入的参数优先级最高，会覆盖上方默认值
};

// 程序化创意（不指定创意形式）时确保 creative_template_id = 0
// 仅在用户未指定时设置默认值
if (params.creative_template_id == null || params.creative_template_id === 0) {
  params.creative_template_id = 0;
}

// 移除 adgroup_context（已使用，不需要传给 create-creative.mjs）
delete params.adgroup_context;

// ── 输出 ──────────────────────────────────────────────────────────────────────
console.log(JSON.stringify({ success: true, params, warnings, errors }, null, 2));
