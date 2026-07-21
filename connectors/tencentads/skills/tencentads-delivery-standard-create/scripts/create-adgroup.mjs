#!/usr/bin/env node
/**
 * create-adgroup.mjs — 创建常规广告组
 *
 * 接收完整的 adgroup 参数 JSON，调用 POST /v3.0/adgroups/add。
 * 常规广告不传 smart_delivery_platform，使用 conversion_id + bid_mode 组合。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, adgroup_name, marketing_goal,
 *       marketing_sub_goal, marketing_target_type, marketing_carrier_type,
 *       bid_amount, begin_date, delivery_time_ranges
 *
 * delivery_time_ranges（新参数，替代 time_series）:
 *   数组格式，描述投放时段，半小时精度，脚本内部自动转为 336 位 time_series。
 *   示例:
 *     全时段: ["all"]
 *     每天 09:00~18:00: ["Monday 09:00~18:00","Tuesday 09:00~18:00",...,"Sunday 09:00~18:00"]
 *     工作日 09:00~18:00: ["Monday 09:00~18:00","Tuesday 09:00~18:00","Wednesday 09:00~18:00","Thursday 09:00~18:00","Friday 09:00~18:00"]
 *     分段: ["Monday 09:00~12:00","Monday 14:00~18:00","Saturday 10:00~16:00"]
 *   规则: 每条格式为 "<Weekday> <HH:MM>~<HH:MM>"，时间精度为半小时（:00 或 :30）。
 *   不在列表中的时段默认不投放。若传 ["all"]，则全时段投放。
 *
 * 资产/载体字段支持两种传入方式（向后兼容）：
 *
 * 方式一（推荐，扁平 ID 由脚本自动组装）：
 *   asset_id      — 推广产品 ID（ONEID 的 outer_id / 行业的 asset_id）
 *   carrier_id    — 载体 ID（来自 carrier_result，≠ asset_id）
 *   catalog_id    — 商品库场景的 catalog_id（可选）
 *   asset_sub_id  — 子标识，写入 spec 的 marketing_asset_outer_sub_id（可选）
 *                   商品库: product_outer_id / wechat_store_id / commodity_set_id
 *                   ONEID: APP_ANDROID 子包 / PC_GAME 区服 / 直播预约 notice_id 等
 *   asset_name    — 资产名称，写入 spec 的 marketing_asset_outer_name（可选，APP_QUICK_APP / PC_GAME）
 *   sub_carrier_id — 载体子标识，写入 carrier_detail 的 marketing_sub_carrier_id（可选）
 *                   通常与 asset_sub_id 同值
 *   carrier_name  — 载体名称，写入 carrier_detail 的 marketing_carrier_name（可选）
 *                   仅 APP_QUICK_APP / PC_GAME 可传，其他类型传了会被安全过滤
 *   → 脚本根据 marketing_target_type 自动组装 marketing_asset_outer_spec 或 marketing_asset_id，
 *     根据 marketing_carrier_type 自动组装 marketing_carrier_detail。
 *
 * 方式二（旧方式，透传）：
 *   直接传 marketing_asset_outer_spec / marketing_asset_id / marketing_carrier_detail
 *   → 脚本原样透传，不做任何变换。
 *
 * 输出（成功）:
 * {
 *   "success": true,
 *   "adgroup_id": 987654321
 * }
 *
 * 输出（失败）:
 * {
 *   "success": false,
 *   "error": { "code": 1000014, "message": "...", "message_cn": "..." }
 * }
 */

import { callApi, resolveTargetingFields, resolveAutoDerivedCreativePreference, resolveSiteSetAliases, resolveExplorationStrategy } from "tencentads-cli";
import {
  ALL_ONEID_LIKE_TYPES,
  CATALOG_TYPES,
  CARRIER_NOT_NEEDED,
  SPEC_REQUIRED_TARGET_TYPES,
  INDUSTRY_TYPES,
} from "./asset-shared.mjs";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` } }));
  process.exit(1);
}

// ─── 基础校验 ───

const requiredFields = ["account_id", "adgroup_name"];
for (const field of requiredFields) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

// ─── end_date 兜底 ───
// API 要求 end_date 为必填字段，长期投放时传空字符串 ""。
// 如果 Agent 漏传 end_date，这里自动补上空字符串以避免 18001 报错。
if (input.end_date === undefined || input.end_date === null) {
  input.end_date = "";
}

// ─── 常规广告 vs 智投互斥校验 ───
// 本脚本仅用于常规（标准）广告创建，smart_delivery_* 字段属于智投专用。

const smartDeliveryKeys = Object.keys(input).filter((k) => k.startsWith("smart_delivery_"));
if (smartDeliveryKeys.length > 0) {
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `本脚本仅用于常规广告创建，不支持智投字段: ${smartDeliveryKeys.join(", ")}。请使用 tencentads-delivery-smart-create 技能创建智投广告。`
    }
  }));
  process.exit(1);
}

const { account_id, ...bodyParams } = input;

// ─── 构造请求体 ───
// /v3.0/ 接口使用枚举字符串 key（如 "MARKETING_GOAL_PRODUCT_SALES"），
// 不需要转成数值。只有 /ap/ 接口才需要数值枚举。
// 常规广告不传 smart_delivery_platform。

const body = {
  account_id: parseInt(account_id, 10),
  ...bodyParams,
};

// ─── configured_status 默认暂停 ───
// 创建广告时，若 Agent 未传 configured_status，则默认设为暂停状态。
// 用户明确指定上线时，Agent 会传入 AD_STATUS_NORMAL 覆盖此默认值。
if (body.configured_status === undefined) {
  body.configured_status = "AD_STATUS_SUSPEND";
}

// ─── 资产 + 载体 自动组装 ───
// Agent 只需传扁平化的原始 ID（asset_id / carrier_id / catalog_id / asset_sub_id），
// 脚本根据 marketing_target_type 确定性地组装 marketing_asset_outer_spec 或 marketing_asset_id，
// 根据 marketing_carrier_type 确定性地组装 marketing_carrier_detail。
// 向后兼容：如果 Agent 已传了 marketing_asset_outer_spec 或 marketing_asset_id，则保持原样不覆盖。

// carrier_name 仅 APP_QUICK_APP 和 PC_GAME 可传（后端 validator.go ValidateMarketingCarrierName），
// 其他类型传了会报错，下方载体组装逻辑统一用此常量做安全过滤。
const CARRIER_NAME_ALLOWED = new Set([
  "MARKETING_CARRIER_TYPE_APP_QUICK_APP",
  "MARKETING_CARRIER_TYPE_PC_GAME",
]);

// 仅当 Agent 传了 asset_id 且没有传 marketing_asset_outer_spec / marketing_asset_id 时触发
if (body.asset_id && !body.marketing_asset_outer_spec && !body.marketing_asset_id) {
  const targetType = body.marketing_target_type;
  const carrierType = body.marketing_carrier_type;

  // ── 1. 资产字段组装（三分类路由）──
  if (ALL_ONEID_LIKE_TYPES.has(targetType)) {
    // ONEID 类 → marketing_asset_outer_spec（target_type + outer_id + 可选 outer_sub_id / outer_name）
    const subId = body.asset_sub_id ? String(body.asset_sub_id) : null;
    body.marketing_asset_outer_spec = {
      marketing_target_type: targetType,
      marketing_asset_outer_id: String(body.asset_id),
      ...(subId ? { marketing_asset_outer_sub_id: subId } : {}),
      ...(body.asset_name ? { marketing_asset_outer_name: String(body.asset_name) } : {}),
    };
  } else if (CATALOG_TYPES.has(targetType)) {
    // 商品库类 → marketing_asset_outer_spec（target_type + outer_id=catalog_id + sub_id）
    body.marketing_asset_outer_spec = {
      marketing_target_type: targetType,
      marketing_asset_outer_id: String(body.catalog_id || body.asset_id),
      ...(body.asset_sub_id ? { marketing_asset_outer_sub_id: String(body.asset_sub_id) } : {}),
    };
  } else {
    // 行业产品库类 → marketing_asset_id（扁平字段，API 要求 Integer 类型）
    body.marketing_asset_id = parseInt(body.asset_id, 10);
  }

  // ── 2. 载体字段组装 ──
  // carrier_name 仅 APP_QUICK_APP 和 PC_GAME 可传（后端 validator.go ValidateMarketingCarrierName），
  // 其他类型传了会报错，这里做安全过滤。
  const safeCarrierName = (body.carrier_name && CARRIER_NAME_ALLOWED.has(carrierType))
    ? String(body.carrier_name)
    : null;

  if (!body.marketing_carrier_detail && body.carrier_id && !CARRIER_NOT_NEEDED.has(carrierType)) {
    body.marketing_carrier_detail = {
      marketing_carrier_id: String(body.carrier_id),
      marketing_sub_carrier_id: body.sub_carrier_id != null ? String(body.sub_carrier_id) : "",
      ...(safeCarrierName ? { marketing_carrier_name: safeCarrierName } : {}),
    };
  }

  // ── 3. 防混淆校验：行业产品库场景 carrier_id ≠ marketing_asset_id ──
  if (body.marketing_asset_id
    && body.marketing_carrier_detail?.marketing_carrier_id
    && String(body.marketing_carrier_detail.marketing_carrier_id) === String(body.marketing_asset_id)) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `carrier_id(${body.marketing_carrier_detail.marketing_carrier_id}) 与 marketing_asset_id(${body.marketing_asset_id}) 值相同，两者含义不同不可互换。carrier_id 来自 carrier_result，marketing_asset_id 来自资产查询，请检查。`,
      },
    }));
    process.exit(1);
  }

  // ── 4. 必填校验 ──
  if (body.marketing_asset_outer_spec && !body.marketing_asset_outer_spec.marketing_asset_outer_id) {
    console.log(JSON.stringify({
      success: false,
      error: { message: "marketing_asset_outer_spec.marketing_asset_outer_id 不能为空" },
    }));
    process.exit(1);
  }
  if (!CARRIER_NOT_NEEDED.has(body.marketing_carrier_type)
    && body.marketing_carrier_detail
    && !body.marketing_carrier_detail.marketing_carrier_id) {
    console.log(JSON.stringify({
      success: false,
      error: { message: "marketing_carrier_detail.marketing_carrier_id 不能为空" },
    }));
    process.exit(1);
  }

  // ── 5. 清理临时字段（不传给 API）──
  delete body.asset_id;
  delete body.carrier_id;
  delete body.catalog_id;
  delete body.asset_sub_id;
  delete body.sub_carrier_id;
  delete body.asset_name;
  delete body.carrier_name;
  // marketing_target_type 已在 marketing_asset_outer_spec 内，顶层传会导致 API 校验冲突
  if (body.marketing_asset_outer_spec) {
    delete body.marketing_target_type;
  }
}

// ─── 独立载体组装（兜底：覆盖 Agent 直传 marketing_asset_id + carrier_id 的场景） ───
// 上面的资产自动组装块仅在 body.asset_id 存在时触发，
// 但 Agent 可能直接传 marketing_asset_id（行业产品库类）+ carrier_id，
// 此时 carrier_id 不会被组装为 marketing_carrier_detail。
// 这里做一次独立的载体组装，确保 carrier_id 始终被正确转换。

if (!body.marketing_carrier_detail
  && body.carrier_id
  && body.marketing_carrier_type
  && !CARRIER_NOT_NEEDED.has(body.marketing_carrier_type)) {

  const safeCarrierName = (body.carrier_name && CARRIER_NAME_ALLOWED.has(body.marketing_carrier_type))
    ? String(body.carrier_name)
    : null;

  body.marketing_carrier_detail = {
    marketing_carrier_id: String(body.carrier_id),
    marketing_sub_carrier_id: body.sub_carrier_id != null ? String(body.sub_carrier_id) : "",
    ...(safeCarrierName ? { marketing_carrier_name: safeCarrierName } : {}),
  };

  // 清理临时字段（不传给 API）
  delete body.carrier_id;
  delete body.sub_carrier_id;
  delete body.carrier_name;
}

// ─── marketing_asset_outer_spec 自动修正 ───
// Agent 可能将 marketing_target_type 遗漏或误放在请求体顶层，
// 这里在发请求前自动检测并修正，避免 API 报错。

// 尝试从多个位置推断 marketing_target_type
const topLevelTargetType = body.marketing_target_type;
const specTargetType = body.marketing_asset_outer_spec?.marketing_target_type;
const resolvedTargetType = specTargetType || topLevelTargetType;

if (body.marketing_asset_outer_spec && typeof body.marketing_asset_outer_spec === "object") {
  // 情况 1：spec 存在但内部缺少 marketing_target_type → 从顶层补入
  if (!specTargetType && resolvedTargetType) {
    body.marketing_asset_outer_spec.marketing_target_type = resolvedTargetType;
  }
  // 情况 2：顶层有 marketing_target_type 且属于白名单类型，清理顶层多余字段
  // （marketing_target_type 应在 spec 内部，不应在请求体顶层）
  if (topLevelTargetType && SPEC_REQUIRED_TARGET_TYPES.has(topLevelTargetType)) {
    delete body.marketing_target_type;
  }
} else if (!body.marketing_asset_outer_spec && !body.marketing_asset_id
  && topLevelTargetType && SPEC_REQUIRED_TARGET_TYPES.has(topLevelTargetType)) {
  // 情况 3：既没有 spec 也没有 marketing_asset_id，但顶层有白名单类型的 target_type
  // 说明 Agent 完全忘记构造 spec，此时无法自动修复（缺少 outer_id 等信息），报错退出
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `marketing_target_type="${topLevelTargetType}" 属于 ONEID/商品库类，必须传 marketing_asset_outer_spec（或传 asset_id 由脚本自动组装），当前两者均未提供。`,
    },
  }));
  process.exit(1);
}

// 互斥校验：marketing_asset_id 和 marketing_asset_outer_spec 不能同时存在
if (body.marketing_asset_id && body.marketing_asset_outer_spec) {
  if (resolvedTargetType && SPEC_REQUIRED_TARGET_TYPES.has(resolvedTargetType)) {
    // 白名单类型 → marketing_asset_outer_spec 优先，移除 marketing_asset_id
    delete body.marketing_asset_id;
  } else {
    // 行业产品库类 → marketing_asset_id 优先，移除 spec
    delete body.marketing_asset_outer_spec;
  }
}

// ─── 必填字段兜底（打 API 前本地拦截） ───
// 对应 API 错误 1800464 "该营销载体类型下必传营销载体信息" 等，
// 本地拦截并在 message 中直接指明下一步动作（回步骤 2 跑 get-assets.mjs）。

// 兜底 A：非 JUMP_PAGE 载体类型必须传载体信息
if (body.marketing_carrier_type
  && !CARRIER_NOT_NEEDED.has(body.marketing_carrier_type)
  && !body.marketing_carrier_detail
  && !body.carrier_id) {
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `marketing_carrier_type="${body.marketing_carrier_type}" 需要载体信息，缺少 carrier_id / marketing_carrier_detail。请先执行 get-assets.mjs 获取 flat_params.carrier_id。`,
    },
  }));
  process.exit(1);
}

// 兜底 B：已知行业产品库类 marketing_target_type 必须有 marketing_asset_id
// ONEID / 商品库类已由"情况 3"校验覆盖，这里补齐行业产品库类分支。
// 未在任何分类集合中的未知 target_type 不拦截，放行交由 API 判断。
if (body.marketing_target_type
  && INDUSTRY_TYPES.has(body.marketing_target_type)
  && !body.marketing_asset_id
  && !body.asset_id) {
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `marketing_target_type="${body.marketing_target_type}" 属于行业产品库类，缺少 marketing_asset_id / asset_id。请先执行 get-assets.mjs 获取 flat_params.asset_id。`,
    },
  }));
  process.exit(1);
}

// ─── site_set 别名自动纠正 ───
// Agent 可能误用别名（如 SITE_SET_SEARCH），这里统一纠正为 canonical key
if (Array.isArray(body.site_set)) {
  body.site_set = resolveSiteSetAliases(body.site_set);
}
if (Array.isArray(body.priority_site_set)) {
  body.priority_site_set = resolveSiteSetAliases(body.priority_site_set);
}

// ─── exploration_strategy 枚举自动匹配 ───
if (body.exploration_strategy != null) {
  try {
    body.exploration_strategy = resolveExplorationStrategy(body.exploration_strategy);
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: { message: err.message } }));
    process.exit(1);
  }
  if (body.exploration_strategy === "STEADY_EXPLORATION" && !Array.isArray(body.priority_site_set)) {
    console.log(JSON.stringify({ success: false, error: { message: "exploration_strategy 为 STEADY_EXPLORATION 时，必须传 priority_site_set 数组" } }));
    process.exit(1);
  }
}
if (body.exploration_strategy !== "STEADY_EXPLORATION") delete body.priority_site_set;

// ─── 深度转化参数处理 ───
if (body.deep_conversion_type && !body.deep_conversion_spec) {
  if (body.conversion_id) {
    // 使用 conversion_id 场景：直接保留一级字段，不构造 deep_conversion_spec
    delete body.deep_conversion_type;
    // deep_conversion_worth_rate / deep_conversion_worth_advanced_rate /
    // deep_conversion_behavior_bid / deep_conversion_behavior_advanced_bid
    // 保留为一级字段直接透传给 API
  }
}

// ─── targeting 子字段位置校验 ───
// 检测 Agent 是否将 targeting 子字段误放到请求体顶层，如果是则报错引导修正。
// 同时确保 targeting 始终存在（API 必填，通投时传空对象即可）。
if (!body.targeting) body.targeting = {};
const TARGETING_SUBFIELDS = new Set([
  "age", "gender", "geo_location", "user_os", "excluded_os",
  "education", "marital_status", "network_type", "device_price",
  "device_brand_model", "app_install_status", "game_consumption_level",
  "custom_audience", "excluded_custom_audience",
  "excluded_converted_audience", "wechat_ad_behavior",
]);
const misplacedFields = [];
for (const key of TARGETING_SUBFIELDS) {
  if (body[key] !== undefined) misplacedFields.push(key);
}
if (misplacedFields.length > 0) {
  console.log(JSON.stringify({
    success: false,
    error: {
      message: `字段 [${misplacedFields.join(", ")}] 应放在 targeting 对象内，而非请求体顶层。请改为 targeting: { ${misplacedFields[0]}: ... }`,
    },
  }));
  process.exit(1);
}

// ─── targeting 枚举自动匹配 ───
if (body.targeting) {
  resolveTargetingFields(body.targeting);
}

// ─── auto_derived_creative_preference 枚举自动匹配 ───
if (body.auto_derived_creative_preference) {
  resolveAutoDerivedCreativePreference(body.auto_derived_creative_preference);
}

// ─── delivery_time_ranges → time_series 转化 ───
// Agent 传 delivery_time_ranges（人类可读数组），脚本内部转为 336 位 time_series 字符串。
// 如果 Agent 直接传了 time_series（向后兼容），也接受。

if (body.delivery_time_ranges && !body.time_series) {
  body.time_series = convertDeliveryTimeRanges(body.delivery_time_ranges);
  delete body.delivery_time_ranges;
} else if (body.delivery_time_ranges && body.time_series) {
  // 两者都传了，优先使用 delivery_time_ranges
  body.time_series = convertDeliveryTimeRanges(body.delivery_time_ranges);
  delete body.delivery_time_ranges;
}

// ─── time_series 长度校验 ───
// API 要求 time_series 必须恰好 336 位（7天 × 48半小时）。
if (body.time_series) {
  const ts = body.time_series;
  if (ts.length !== 336) {
    if (/^1+$/.test(ts)) {
      // 全时段投放意图明确，自动修正
      body.time_series = "1".repeat(336);
    } else {
      // 非全1且长度不对，语义无法保证，报错
      console.log(JSON.stringify({
        success: false,
        error: {
          message: `time_series 长度为 ${ts.length}，API 要求恰好 336 位（7天×48半小时）。请改用 delivery_time_ranges 参数让脚本自动生成正确编码。`,
        },
      }));
      process.exit(1);
    }
  }
}

/**
 * 将 delivery_time_ranges 数组转为 336 位 time_series 字符串。
 *
 * 编码规则（与前端 timeset 组件一致）：
 *   - 总长度 336 = 7天 × 48个半小时
 *   - '1' = 该半小时投放, '0' = 不投放
 *   - 日期顺序: [0-47]=周一, [48-95]=周二, ..., [288-335]=周日
 *   - 每天时间: 位置0=00:00-00:30, 位置1=00:30-01:00, ..., 位置47=23:30-24:00
 *
 * @param {string[]} ranges - 如 ["Monday 09:00~18:00", "Saturday 10:00~16:00"] 或 ["all"]
 * @returns {string} 336 位 '0'/'1' 字符串
 */
function convertDeliveryTimeRanges(ranges) {
  if (!Array.isArray(ranges) || ranges.length === 0) {
    return "1".repeat(336); // 默认全时段
  }

  // 特殊值：全时段
  if (ranges.length === 1 && ranges[0].toLowerCase().trim() === "all") {
    return "1".repeat(336);
  }

  const DAY_MAP = {
    monday: 0, tuesday: 1, wednesday: 2, thursday: 3,
    friday: 4, saturday: 5, sunday: 6,
    mon: 0, tue: 1, wed: 2, thu: 3, fri: 4, sat: 5, sun: 6,
  };

  // 初始化 336 位全 0
  const bits = new Array(336).fill(0);

  for (const entry of ranges) {
    const trimmed = entry.trim();
    // 解析格式: "<Weekday> <HH:MM>~<HH:MM>"
    const match = trimmed.match(/^(\w+)\s+(\d{1,2}:\d{2})\s*[~\-]\s*(\d{1,2}:\d{2})$/i);
    if (!match) {
      console.log(JSON.stringify({
        success: false,
        error: { message: `delivery_time_ranges 格式错误: "${trimmed}"，期望格式: "Monday 09:00~18:00"` },
      }));
      process.exit(1);
    }

    const dayName = match[1].toLowerCase();
    const startStr = match[2];
    const endStr = match[3];

    const dayIndex = DAY_MAP[dayName];
    if (dayIndex === undefined) {
      console.log(JSON.stringify({
        success: false,
        error: { message: `delivery_time_ranges 中的星期名无法识别: "${match[1]}"，支持: Monday-Sunday 或 Mon-Sun` },
      }));
      process.exit(1);
    }

    // 解析时间为半小时 slot 索引
    const startSlot = parseTimeToSlot(startStr);
    const endSlot = parseTimeToSlot(endStr);

    if (startSlot >= endSlot) {
      console.log(JSON.stringify({
        success: false,
        error: { message: `delivery_time_ranges 时间范围无效: "${trimmed}"，开始时间必须小于结束时间` },
      }));
      process.exit(1);
    }

    // 设置对应 bit 位
    const dayOffset = dayIndex * 48;
    for (let s = startSlot; s < endSlot; s++) {
      bits[dayOffset + s] = 1;
    }
  }

  return bits.join("");
}

/**
 * 将 "HH:MM" 时间字符串解析为半小时 slot 索引 (0-48)。
 * 例如: "00:00" → 0, "00:30" → 1, "09:00" → 18, "24:00" → 48
 * 非整半小时向上取整到下一个半小时。
 */
function parseTimeToSlot(timeStr) {
  const [hStr, mStr] = timeStr.split(":");
  const h = parseInt(hStr, 10);
  const m = parseInt(mStr, 10);
  // 半小时精度：0分 → slot 偶数位，30分 → slot 奇数位
  // 非整半小时向上取整
  if (m === 0) return h * 2;
  if (m <= 30) return h * 2 + 1;
  return (h + 1) * 2; // > 30分，进到下一个整点
}

// ─── 兜底类型修正：marketing_asset_id 必须为 Integer ───
// Agent 可能直传 String 类型的 marketing_asset_id（来源于 get-assets 返回的字符串），
// API 要求该字段为 Integer，这里统一做一次安全转换。
if (body.marketing_asset_id != null) {
  body.marketing_asset_id = parseInt(body.marketing_asset_id, 10);
  if (Number.isNaN(body.marketing_asset_id)) {
    console.log(JSON.stringify({
      success: false,
      error: { message: `marketing_asset_id 值无效，无法转为整数。请检查传入值。` },
    }));
    process.exit(1);
  }
}

// ─── 调用 API ───

const result = await callApi({
  method: "POST",
  path: "/v3.0/adgroups/add",
  accountId: String(account_id),
  body,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API 调用失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

// ─── 提取 adgroup_id ───

const adgroupId =
  result.data?.data?.adgroup_id ??
  result.data?.adgroup_id ??
  null;

if (!adgroupId) {
  // 成功但结构不符合预期，原样返回
  console.log(JSON.stringify({ success: true, data: result.data }, null, 2));
} else {
  console.log(JSON.stringify({ success: true, adgroup_id: adgroupId }, null, 2));
}
