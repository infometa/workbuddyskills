#!/usr/bin/env node
/**
 * create-adgroup.mjs — 创建智投广告组
 *
 * 接收完整的 adgroup 参数 JSON，调用 POST /v3.0/adgroups/add。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, adgroup_name, smart_delivery_platform, marketing_goal,
 *       marketing_sub_goal, marketing_target_type, marketing_carrier_type,
 *       conversion_id, bid_amount, begin_date, delivery_time_ranges,
 *       automatic_site_enabled=true
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
 *   carrier_id    — 载体 ID（ONEID 类和视频号直播类由 get-assets 返回；行业/商品库类需从用户处获取，≠ asset_id）
 *   catalog_id    — 商品库场景的 catalog_id（可选）
 *   asset_sub_id  — 子标识，写入 spec 的 marketing_asset_outer_sub_id（可选）
 *   asset_name    — 资产名称，写入 spec 的 marketing_asset_outer_name（可选，APP_QUICK_APP / PC_GAME）
 *   sub_carrier_id — 载体子标识，写入 carrier_detail 的 marketing_sub_carrier_id（可选）
 *   carrier_name  — 载体名称，写入 carrier_detail 的 marketing_carrier_name（可选）
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

import { callApi } from "tencentads-cli";
import { ONEID_TYPES, CHANNELS_LIVE_TYPES, CATALOG_TYPES } from "./get-assets.mjs";

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

const { account_id, ...bodyParams } = input;

// ─── 构造请求体 ───
// /v3.0/ 接口使用枚举字符串 key（如 "MARKETING_GOAL_PRODUCT_SALES"），
// 不需要转成数值。只有 /ap/ 接口才需要数值枚举。

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

// ─── 智投项目不支持使用一键起量 ───
if (body.auto_acquisition_enabled !== undefined || body.auto_acquisition_budget !== undefined) {
  console.log(JSON.stringify({
    success: false,
    error: { message: "智投项目不支持使用一键起量（auto_acquisition）功能，一键起量仅适用于标准投放广告。请移除 auto_acquisition_enabled / auto_acquisition_budget 字段后重试。" },
  }));
  process.exit(1);
}

// ─── 资产 + 载体 自动组装 ───
// Agent 只需传扁平化的原始 ID（asset_id / carrier_id / catalog_id / asset_sub_id），
// 脚本根据 marketing_target_type 确定性地组装 marketing_asset_outer_spec 或 marketing_asset_id，
// 根据 marketing_carrier_type 确定性地组装 marketing_carrier_detail。
// 向后兼容：如果 Agent 已传了 marketing_asset_outer_spec 或 marketing_asset_id，则保持原样不覆盖。

// ONEID_TYPES / CHANNELS_LIVE_TYPES / CATALOG_TYPES 从 get-assets.mjs import，
// 保持与资产查询侧分类定义完全一致，避免 flat_params 格式不匹配。
// 创建广告组时，视频号直播类也走 marketing_asset_outer_spec（ONEID 路由），
// 所以本地合并为 ONEID_TYPES_FOR_CREATE = ONEID_TYPES ∪ CHANNELS_LIVE_TYPES。
const ONEID_TYPES_FOR_CREATE = new Set([...ONEID_TYPES, ...CHANNELS_LIVE_TYPES]);

const CARRIER_NOT_NEEDED = new Set([
  "MARKETING_CARRIER_TYPE_JUMP_PAGE",
]);

// 仅当 Agent 传了 asset_id 且没有传 marketing_asset_outer_spec / marketing_asset_id 时触发
if (body.asset_id && !body.marketing_asset_outer_spec && !body.marketing_asset_id) {
  const targetType = body.marketing_target_type;
  const carrierType = body.marketing_carrier_type;

  // ── 1. 资产字段组装（三分类路由）──
  if (ONEID_TYPES_FOR_CREATE.has(targetType)) {
    // ONEID 类 → marketing_asset_outer_spec（target_type + outer_id + 可选 outer_sub_id / outer_name）
    // PC_GAME 特殊：sub_id 不传时默认填 "/"（后端 fromouterspec.go 逻辑）
    const subId = body.asset_sub_id
      ? String(body.asset_sub_id)
      : (targetType === "MARKETING_TARGET_TYPE_PC_GAME" ? "/" : null);
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
  const CARRIER_NAME_ALLOWED = new Set([
    "MARKETING_CARRIER_TYPE_APP_QUICK_APP",
    "MARKETING_CARRIER_TYPE_PC_GAME",
  ]);
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
        message: `carrier_id(${body.marketing_carrier_detail.marketing_carrier_id}) 与 marketing_asset_id(${body.marketing_asset_id}) 值相同，carrier_id 应为营销载体 ID，marketing_asset_id 为推广产品 ID，两者含义不同不可互换，请检查。`,
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

// ─── marketing_asset_outer_spec 自动修正 ───
// Agent 可能将 marketing_target_type 遗漏或误放在请求体顶层，
// 这里在发请求前自动检测并修正，避免 API 报错。

// 需要使用 marketing_asset_outer_spec 的 target_type 白名单（ONEID 类 + 视频号直播类 + 商品库类）
// 由 import 的分类集合动态合并，保持与 get-assets.mjs 分类定义完全一致。
const SPEC_REQUIRED_TARGET_TYPES = new Set([...ONEID_TYPES_FOR_CREATE, ...CATALOG_TYPES]);

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

// ─── 智投版位强制设置 ───
// 智投场景下版位固定为智能版位（automatic_site_enabled=true），不支持手动选择。
// 无论 Agent 传了什么，这里强制覆盖，与前端逻辑保持一致。
if (body.smart_delivery_platform) {
  body.automatic_site_enabled = true;
  delete body.site_set; // 智能版位不传 site_set
}

// ─── 周期达成（Period Completion）校验 ───
// 当 smart_delivery_period_switch = "PERIOD_SWITCH_ON" 时，执行关联字段校验
if (body.smart_delivery_period_switch === "PERIOD_SWITCH_ON") {
  // 必填字段检查
  if (!body.smart_delivery_period_days) {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时 smart_delivery_period_days 必填，可选值: PERIOD_DAYS_THREE (3天) / PERIOD_DAYS_SEVEN (7天)" } }));
    process.exit(1);
  }
  const validDays = ["PERIOD_DAYS_THREE", "PERIOD_DAYS_SEVEN"];
  if (!validDays.includes(body.smart_delivery_period_days)) {
    console.log(JSON.stringify({ success: false, error: { message: `smart_delivery_period_days 值无效: "${body.smart_delivery_period_days}"，可选值: ${validDays.join(", ")}` } }));
    process.exit(1);
  }
  if (!body.smart_delivery_period_budget || body.smart_delivery_period_budget <= 0) {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时 smart_delivery_period_budget（周期预算）必填且必须大于0（单位：分）" } }));
    process.exit(1);
  }
  if (!body.smart_delivery_period_continue) {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时 smart_delivery_period_continue 必填，可选值: PERIOD_CONTINUE_SWITCH_ON（续投）/ PERIOD_CONTINUE_SWITCH_OFF（不续投）" } }));
    process.exit(1);
  }
  const validContinue = ["PERIOD_CONTINUE_SWITCH_ON", "PERIOD_CONTINUE_SWITCH_OFF"];
  if (!validContinue.includes(body.smart_delivery_period_continue)) {
    console.log(JSON.stringify({ success: false, error: { message: `smart_delivery_period_continue 值无效: "${body.smart_delivery_period_continue}"，可选值: ${validContinue.join(", ")}` } }));
    process.exit(1);
  }
  // 预算约束: >= 3 * bid_amount * 周期天数
  const periodDaysMap = { PERIOD_DAYS_THREE: 3, PERIOD_DAYS_SEVEN: 7 };
  const periodDayNum = periodDaysMap[body.smart_delivery_period_days];
  const bidAmount = body.bid_amount || 0;
  const minBudget = 3 * bidAmount * periodDayNum;
  if (body.smart_delivery_period_budget < minBudget) {
    console.log(JSON.stringify({ success: false, error: { message: `smart_delivery_period_budget(${body.smart_delivery_period_budget}分) 不满足约束: 需 >= 3 × 出价(${bidAmount}分) × 周期天数(${periodDayNum}) = ${minBudget}分（${minBudget/100}元）` } }));
    process.exit(1);
  }
  // 出价限制：不允许自动出价
  if (body.smart_bid_type === "SMART_BID_TYPE_SYSTEMATIC") {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时不允许使用自动出价（smart_bid_type 不能为 SMART_BID_TYPE_SYSTEMATIC），请使用手动出价" } }));
    process.exit(1);
  }
  // 禁止字段检查
  if (body.daily_budget && body.daily_budget > 0) {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时不允许设置 daily_budget（日预算），请移除该字段" } }));
    process.exit(1);
  }
  if (body.total_budget && body.total_budget > 0) {
    console.log(JSON.stringify({ success: false, error: { message: "开启周期达成时不允许设置 total_budget（总预算），请移除该字段" } }));
    process.exit(1);
  }
  // Agent 不应传 end_date——脚本统一设 end_date=""，后端根据 begin_date + 周期天数自动计算实际结束日期。
  // 如果 Agent 传了 end_date，报错提醒让 Agent 知道不应传入此字段。
  if (body.end_date !== undefined && body.end_date !== "") {
    console.log(JSON.stringify({ success: false, error: { message: "周期达成项目不需要传 end_date，请移除该字段。无论续投还是不续投，脚本会自动将 end_date 设为空字符串，后端根据 begin_date + 周期天数计算实际结束日期。" } }));
    process.exit(1);
  }
  // 同时清除 daily_budget 和 total_budget，确保不传给 API
  delete body.daily_budget;
  delete body.total_budget;
  body.end_date = "";
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

// ─── targeting 白名单校验（通过 projects_config/get 获取场景支持的定向） ───
// 如果 body.targeting 非空且有 smart_delivery_platform，自动校验定向字段是否在白名单中。
// 不在白名单中的字段会报错返回，避免 API 静默忽略或报未知错误。

if (body.targeting && Object.keys(body.targeting).length > 0 && body.smart_delivery_platform) {
  const targetingValidation = await validateTargetingFields(
    String(account_id),
    body.smart_delivery_platform,
    body.targeting
  );
  if (!targetingValidation.success) {
    console.log(JSON.stringify(targetingValidation));
    process.exit(1);
  }
}

/**
 * 校验 targeting 字段是否在当前智投场景的白名单中。
 * 内部调用 projects_config/get 获取白名单，并将前端字段名映射为 API 字段名。
 */
async function validateTargetingFields(accountId, platform, targeting) {
  // 前端 adp2mkt 映射表（来自 adp_fe targeting/src/constant/index.ts）
  const ADP_TO_MKT_MAP = {
    aoi: "interested_area",
    resident_community_price: "residential_community_price",
    marriage_status: "marital_status",
    living_status: "working_status",
    asset_status: "financial_situation",
    consumption_ability: "consumption_status",
    appuser: "app_install_status",
    targeting_audience: ["custom_audience", "excluded_custom_audience"],
    exclude_converted_audience: "excluded_converted_audience",
    mobile_brand_model: "device_brand_model",
    scene: "network_scene",
    connectiontype: "network_type",
    telcom: "network_operator",
    mobileprice: "device_price",
    media_industry: "mobile_union_category",
    wechatflowclass: "wechat_official_account_category",
    uvindex: "uv_index",
    dressindex: "dressing_index",
    makeupindex: "makeup_index",
    airqualityindex: "air_quality_index",
    behavior_interest: "behavior_or_interest",
    os: ["user_os", "excluded_os"],
    personalized_scene: "personalized_scene",
  };

  function toMktFields(fieldName) {
    const mapped = ADP_TO_MKT_MAP[fieldName];
    if (mapped) return Array.isArray(mapped) ? mapped : [mapped];
    return [fieldName];
  }

  try {
    const rsp = await callApi({
      path: "/v3.0/projects_config/get",
      method: "GET",
      accountId: accountId,
      params: {
        account_id: accountId,
        smart_delivery_platform: platform,
      },
    });

    const data = rsp.data?.data ?? rsp.data;
    const code = rsp.data?.code ?? rsp.code ?? -1;

    if (code !== 0) {
      // projects_config 调用失败不阻断创建流程，仅输出 warning
      return { success: true, warning: "projects_config/get 调用失败，跳过定向白名单校验" };
    }

    const list = data?.list || [];
    const config = list.find((item) => item.smart_delivery_platform === platform) || list[0];

    if (!config) {
      // 未找到配置，不阻断
      return { success: true, warning: "未找到对应场景配置，跳过定向白名单校验" };
    }

    // 提取 targeting 白名单
    let rawTargetingFields = [];
    const abilityPermissions = config.ability_permissions || [];
    const targetingPermission = abilityPermissions.find((p) => p.name === "targeting");
    if (targetingPermission?.valid) {
      rawTargetingFields = targetingPermission.valid;
    }
    // 兼容 adgroup_rules 结构
    if (rawTargetingFields.length === 0 && config.adgroup_rules) {
      const targetingRule = config.adgroup_rules.find((r) => r.field_name === "targeting");
      if (targetingRule?.sub_field_whitelist) {
        rawTargetingFields = targetingRule.sub_field_whitelist.map((f) => f.field_name);
      }
    }

    // 如果接口没返回白名单，不阻断
    if (rawTargetingFields.length === 0) {
      return { success: true, warning: "场景未返回定向白名单，跳过校验" };
    }

    // 映射为 MKT API 字段名
    const allowedFields = new Set();
    for (const field of rawTargetingFields) {
      for (const mktField of toMktFields(field)) {
        allowedFields.add(mktField);
      }
    }

    // 校验 targeting 中的字段
    const targetingKeys = Object.keys(targeting);
    const unsupported = targetingKeys.filter((key) => !allowedFields.has(key));

    if (unsupported.length > 0) {
      return {
        success: false,
        error: {
          message: `当前智投场景(${platform})不支持以下定向字段: ${unsupported.join(", ")}。支持的定向字段为: ${[...allowedFields].sort().join(", ")}。请移除不支持的定向后重试，或告知用户该场景不支持这些定向。`,
        },
      };
    }

    return { success: true };
  } catch (err) {
    // 网络异常不阻断创建流程
    return { success: true, warning: `projects_config 校验异常: ${err.message}，跳过` };
  }
}

// smart_delivery_aigc_creative 开启时，supply_strategy_type 必须包含 SUPPLY_STRATEGY_TYPE_AIGC
// smart_delivery_history_comp_reused_creative 开启时，supply_strategy_type 必须包含 SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE
const BASE_STRATEGY_MAP = {
  smart_delivery_aigc_creative: "SUPPLY_STRATEGY_TYPE_AIGC",
  smart_delivery_history_comp_reused_creative: "SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE",
};

for (const [fieldName, requiredStrategy] of Object.entries(BASE_STRATEGY_MAP)) {
  const creative = body[fieldName];
  if (!creative || !creative.is_open) continue;

  const strategies = creative.supply_strategy_type;
  if (!Array.isArray(strategies) || !strategies.includes(requiredStrategy)) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `${fieldName} 的 is_open 为 true 时，supply_strategy_type 必须包含 ${requiredStrategy}。当前值: ${JSON.stringify(strategies)}。请补充后重试。`,
      },
    }));
    process.exit(1);
  }
}

// ─── 智投创意字段校验（sku_id / catalog_id / 品牌形象） ───

// Platform value constants for readability
const PLATFORM_1001 = "SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET";
const PLATFORM_3002 = "SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_PRODUCT_OR_LIVE";
const PLATFORM_3003 = "SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_MANAGEMENT";
const PLATFORM_3004 = "SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_LIVE";
const PLATFORM_3005 = "SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_PRODUCT";

const CHANNELS_LIVE_TARGET = "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE";
const CHANNELS_LIVE_CARRIER = "MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE";

const platform = body.smart_delivery_platform;
const targetType = body.marketing_asset_outer_spec?.marketing_target_type
  || body.marketing_target_type;
const carrierType = body.marketing_carrier_type;

// ─── 爆剧跑量场景：short_play_pay_type + sell_strategy_id 校验 ───
// 当 short_play_pay_type 为收费剧时，sell_strategy_id 必填
if (platform === PLATFORM_1001 && body.short_play_pay_type === "SHORT_PLAY_PAY_TYPE_CHARGE_PLAY") {
  if (!body.sell_strategy_id || body.sell_strategy_id === 0) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `当前为爆剧跑量场景且短剧售卖类型为收费剧(SHORT_PLAY_PAY_TYPE_CHARGE_PLAY)，sell_strategy_id（售卖策略ID）为必填字段且不能为 0。请提供售卖策略 ID 后重试。`,
      },
    }));
    process.exit(1);
  }
}

// 非爆剧跑量场景不应传入 short_play_pay_type 和 sell_strategy_id
if (platform !== PLATFORM_1001) {
  if (body.short_play_pay_type && body.short_play_pay_type !== "SHORT_PLAY_PAY_TYPE_UNKNOWN") {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `short_play_pay_type 仅适用于爆剧跑量场景(SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET)，当前场景为 ${platform}，请移除该字段后重试。`,
      },
    }));
    process.exit(1);
  }
}

// Rule 1: (3002 OR 3004) + target=视频号直播 + carrier=视频号直播
//   → smart_delivery_aigc_creative must contain sku_id and catalog_id
const isChannelsLiveScene = [PLATFORM_3002, PLATFORM_3004].includes(platform)
  && targetType === CHANNELS_LIVE_TARGET
  && carrierType === CHANNELS_LIVE_CARRIER;

if (isChannelsLiveScene && body.smart_delivery_aigc_creative?.is_open) {
  const aigc = body.smart_delivery_aigc_creative;
  const missing = [];
  if (!aigc.sku_id) missing.push("sku_id");
  if (aigc.catalog_id == null) missing.push("catalog_id");
  if (missing.length > 0) {
    console.log(JSON.stringify({
      success: false,
      error: {
        message: `当前场景(${platform})推广视频号直播时，smart_delivery_aigc_creative 必须包含 ${missing.join(" 和 ")}。请提供商品的 sku_id 和 catalog_id 后重试。`,
      },
    }));
    process.exit(1);
  }
}

// Rule 2: (3002 OR 3003 OR 3005) + target≠视频号直播 + carrier≠视频号直播
//   → smart_delivery_aigc_creative and smart_delivery_history_comp_reused_creative
//     must contain creative_components.brand[].component_id
//     and supply_strategy_type must include SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION
const isBrandRequiredScene = [PLATFORM_3002, PLATFORM_3003, PLATFORM_3005].includes(platform)
  && targetType !== CHANNELS_LIVE_TARGET
  && carrierType !== CHANNELS_LIVE_CARRIER;

if (isBrandRequiredScene) {
  const MANUAL_STRATEGY = "SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION";

  // Check if any open creative field is missing brand component_id
  const creativeFieldsMissingBrand = [];
  for (const fieldName of ["smart_delivery_aigc_creative", "smart_delivery_history_comp_reused_creative"]) {
    const creative = body[fieldName];
    if (!creative || !creative.is_open) continue;

    const brandList = creative.creative_components?.brand;
    if (!Array.isArray(brandList) || brandList.length === 0 || !brandList[0]?.component_id) {
      creativeFieldsMissingBrand.push(fieldName);
    }
  }

  // If any creative field is missing brand, auto-fetch brand component list for user to choose
  if (creativeFieldsMissingBrand.length > 0) {
    const brandComponents = await fetchBrandComponents(String(account_id));

    if (brandComponents === null) {
      // API call failed or no brand components found
      console.log(JSON.stringify({
        success: false,
        error: {
          message: `当前场景(${platform})非视频号直播推广时，${creativeFieldsMissingBrand.join(" 和 ")} 必须包含品牌形象(creative_components.brand[].component_id)。自动查询品牌形象列表失败，请手动提供品牌形象组件 ID 后重试。`,
        },
      }));
      process.exit(1);
    }

    // Return brand list for user to choose
    console.log(JSON.stringify({
      success: false,
      need_brand_selection: true,
      error: {
        message: `当前场景(${platform})非视频号直播推广时，${creativeFieldsMissingBrand.join(" 和 ")} 必须包含品牌形象。已自动查询到该账户下 ${brandComponents.length} 个可用品牌形象，请从以下列表中选择一个品牌形象后，将其 component_id 填入 creative_components.brand 中重试。`,
      },
      brand_components: brandComponents,
    }));
    process.exit(1);
  }

  // Validate supply_strategy_type includes MANUAL_CREATION for fields that have brand
  for (const fieldName of ["smart_delivery_aigc_creative", "smart_delivery_history_comp_reused_creative"]) {
    const creative = body[fieldName];
    if (!creative || !creative.is_open) continue;

    const strategies = creative.supply_strategy_type;
    if (!Array.isArray(strategies) || !strategies.includes(MANUAL_STRATEGY)) {
      console.log(JSON.stringify({
        success: false,
        error: {
          message: `当前场景(${platform})非视频号直播推广时，${fieldName} 的 supply_strategy_type 中必须包含 ${MANUAL_STRATEGY}（与品牌形象配套）。当前值: ${JSON.stringify(strategies)}。请补充后重试。`,
        },
      }));
      process.exit(1);
    }
  }
}

/**
 * Fetch available brand components for the given account via integrated_list_multiaccount/get.
 * Returns an array of brand component objects, or null if the query fails.
 */
async function fetchBrandComponents(accountId) {
  try {
    const now = new Date();
    const endDate = now.toISOString().slice(0, 10);
    const startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    const result = await callApi({
      method: "POST",
      path: "/v3.0/integrated_list_multiaccount/get",
      accountId,
      body: {
        account_id_list: [parseInt(accountId, 10)],
        page: 1,
        page_size: 10,
        date_range: { start_date: startDate, end_date: endDate },
        time_line: "REQUEST_TIME",
        level: "COMPONENT",
        group_by: ["component_id"],
        order_by: [{ sort_field: "component.component_id", sort_type: "DESCENDING" }],
        filtering: [
          { field: "component.component_sub_type", operator: "IN", values: ["BRAND"] },
          { field: "component.operation_status", operator: "IN", values: ["CALCULATE_STATUS_EXCLUDE_DEL", "CALCULATE_STATUS_NORMAL"] },
          { field: "component.scene", operator: "IN", values: ["DEFAULT"] },
        ],
        fields: [
          "component.component_id",
          "component.component_sub_type_cn",
          "component.component_custom_name",
          "component.component_source_type_cn",
          "component.component_value",
        ],
      },
    });

    if (!result.success) return null;

    const data = result.data?.data ?? result.data ?? {};
    const list = data?.list ?? [];

    if (list.length === 0) return null;

    return list.map((item) => {
      const comp = item?.component ?? {};
      const brandValue = comp.component_value?.brand?.value ?? {};
      return {
        component_id: comp.component_id,
        brand_name: brandValue.brand_name || "",
        brand_image_id: brandValue.brand_image_id || "",
        component_custom_name: comp.component_custom_name || "",
        source_type: comp.component_source_type_cn || "",
      };
    }).filter((c) => c.component_id);
  } catch {
    return null;
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
