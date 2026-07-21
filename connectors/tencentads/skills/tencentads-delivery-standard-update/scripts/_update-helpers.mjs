/**
 * _update-helpers.mjs -- 广告更新共享模块（内部模块，不直接调用）
 *
 * 从 update-adgroup-general.mjs 提取的纯函数和常量，
 * 供 update-adgroup-general.mjs 和 update-adgroup-batch.mjs 共用。
 */

// =====================================================================
// 常量
// =====================================================================

export const UPDATE_FIELDS = [
  "adgroup_name", "begin_date", "end_date", "delivery_time_ranges",
  "first_day_begin_time",
  "bid_amount", "daily_budget", "configured_status", "targeting",
  "deep_conversion_behavior_bid", "deep_conversion_worth_rate",
  "auto_acquisition_enabled", "auto_acquisition_budget",
  "auto_derived_creative_enabled", "auto_derived_creative_method_type_list",
  "rta_id", "rta_target_id",
  "bid_adjustment", "aoi_optimization_strategy",
  "smart_delivery_aigc_creative", "smart_delivery_history_comp_reused_creative",
  "poi_list", "re_open_auto_acquisition", "industry_value_explore",
  "smart_delivery_period_budget", "smart_delivery_period_continue",
];

export const ADJUSTMENT_FIELDS = [
  "bid_amount_adjustment",
  "daily_budget_adjustment",
  "deep_conversion_behavior_bid_adjustment",
  "deep_conversion_worth_rate_adjustment",
  "auto_acquisition_budget_adjustment",
];

export const INVALID_TARGETING_KEYS = new Set([
  "marketing_asset_id", "marketing_target_type",
  "marketing_asset_outer_spec", "subordinate_product_id",
  "asset_name", "marketing_goal", "marketing_sub_goal",
  "marketing_carrier_type", "site_set",
  "bid_mode", "optimization_goal",
]);

export const QUERY_FIELDS = [
  "adgroup_id", "adgroup_name", "configured_status", "system_status",
  "is_deleted", "begin_date", "end_date", "time_series",
  "first_day_begin_time",
  "bid_amount", "daily_budget", "bid_mode",
  "site_set",
  "targeting", "targeting_translation",
  "deep_conversion_behavior_bid", "deep_conversion_worth_rate",
  "auto_acquisition_enabled", "auto_acquisition_budget",
  "auto_derived_creative_enabled", "auto_derived_creative_preference",
  "marketing_target_type", "marketing_carrier_type", "automatic_site_enabled",
  "smart_delivery_platform",
  "rta_id", "rta_target_id",
  "bid_adjustment", "aoi_optimization_strategy",
  "smart_delivery_aigc_creative", "smart_delivery_history_comp_reused_creative",
  "poi_list", "re_open_auto_acquisition", "industry_value_explore",
  "smart_delivery_period_switch", "smart_delivery_period_days",
  "smart_delivery_period_budget", "smart_delivery_period_continue",
];

export const VERIFY_FIELDS = [
  "adgroup_id", "adgroup_name", "configured_status", "system_status",
  "begin_date", "end_date", "time_series",
  "bid_amount", "daily_budget",
  "targeting", "targeting_translation",
  "deep_conversion_behavior_bid", "deep_conversion_worth_rate",
  "auto_acquisition_enabled", "auto_acquisition_budget",
  "auto_derived_creative_enabled", "auto_derived_creative_preference",
  "rta_id", "rta_target_id",
  "bid_adjustment", "aoi_optimization_strategy",
  "smart_delivery_aigc_creative", "smart_delivery_history_comp_reused_creative",
  "poi_list", "re_open_auto_acquisition", "industry_value_explore",
  "smart_delivery_period_switch", "smart_delivery_period_days",
  "smart_delivery_period_budget", "smart_delivery_period_continue",
];

export const SEARCH_AD_SITE_SETS = new Set([
  "SITE_SET_WECHAT_SEARCH",
  "SITE_SET_QBSEARCH",
  "SITE_SET_SEARCH_MOBILE_UNION",
]);

// =====================================================================
// 纯函数
// =====================================================================

export function convertDeliveryTimeRanges(ranges) {
  if (!Array.isArray(ranges) || ranges.length === 0) {
    return "1".repeat(336);
  }
  if (ranges.length === 1 && ranges[0].toLowerCase().trim() === "all") {
    return "1".repeat(336);
  }
  const DAY_MAP = {
    monday: 0, tuesday: 1, wednesday: 2, thursday: 3,
    friday: 4, saturday: 5, sunday: 6,
    mon: 0, tue: 1, wed: 2, thu: 3, fri: 4, sat: 5, sun: 6,
  };
  const bits = new Array(336).fill(0);
  for (const entry of ranges) {
    const trimmed = entry.trim();
    const match = trimmed.match(/^(\w+)\s+(\d{1,2}:\d{2})\s*[~\-]\s*(\d{1,2}:\d{2})$/i);
    if (!match) {
      throw new Error(`delivery_time_ranges 格式错误: "${trimmed}"，期望格式: "Monday 09:00~18:00"`);
    }
    const dayName = match[1].toLowerCase();
    const dayIndex = DAY_MAP[dayName];
    if (dayIndex === undefined) {
      throw new Error(`无法识别的星期名称: "${match[1]}"，支持: Monday-Sunday 或 Mon-Sun`);
    }
    const startSlot = parseTimeToSlot(match[2]);
    const endSlot = parseTimeToSlot(match[3]);
    if (startSlot >= endSlot) {
      throw new Error(`delivery_time_ranges 时间范围无效: "${trimmed}"，开始时间必须小于结束时间`);
    }
    const dayOffset = dayIndex * 48;
    for (let s = startSlot; s < endSlot; s++) {
      bits[dayOffset + s] = 1;
    }
  }
  return bits.join("");
}

export function parseTimeToSlot(timeStr) {
  const [hStr, mStr] = timeStr.split(":");
  const h = parseInt(hStr, 10);
  const m = parseInt(mStr, 10);
  if (m === 0) return h * 2;
  if (m <= 30) return h * 2 + 1;
  return (h + 1) * 2;
}

export function equalWidthLength(str) {
  let count = 0;
  for (const ch of str) {
    count += ch.charCodeAt(0) > 127 ? 2 : 1;
  }
  return count;
}

/**
 * 相对调整表达式解析（金额字段，单位：分）。
 * @param {string} expr - 调整表达式，如 "+20%"、"-10%"、"*2"、"+50"（加50分）、"-30"（减30分）
 * @param {number} currentFen - 当前值（分）
 * @returns {{ valid: boolean, value?: number, description?: string, error?: string }}
 *          value 单位为分
 */
export function parseAdjustment(expr, currentFen) {
  const s = String(expr).trim();
  let valueFen;
  let description;

  const pctMatch = s.match(/^([+-])(\d+(?:\.\d+)?)%$/);
  if (pctMatch) {
    const sign = pctMatch[1];
    const pct = parseFloat(pctMatch[2]);
    if (isNaN(pct) || pct <= 0) return { valid: false, error: `百分比数值无效: "${s}"` };
    const factor = sign === "+" ? (1 + pct / 100) : (1 - pct / 100);
    valueFen = Math.round(currentFen * factor);
    description = (sign === "+" ? `增加${pct}%` : `减少${pct}%`) + `（${currentFen} -> ${valueFen} 分）`;
  }
  if (valueFen === undefined) {
    const mulMatch = s.match(/^\*(\d+(?:\.\d+)?)$/);
    if (mulMatch) {
      const factor = parseFloat(mulMatch[1]);
      if (isNaN(factor) || factor <= 0) return { valid: false, error: `乘数必须为正数: "${s}"` };
      valueFen = Math.round(currentFen * factor);
      description = `乘以${factor}（${currentFen} -> ${valueFen} 分）`;
    }
  }
  if (valueFen === undefined) {
    const addMatch = s.match(/^([+-])(\d+(?:\.\d+)?)$/);
    if (addMatch) {
      const sign = addMatch[1];
      const delta = parseFloat(addMatch[2]);
      if (isNaN(delta) || delta <= 0) return { valid: false, error: `调整数值无效: "${s}"` };
      const deltaFen = Math.round(delta);
      valueFen = sign === "+" ? currentFen + deltaFen : currentFen - deltaFen;
      description = (sign === "+" ? `加${delta}分` : `减${delta}分`) + `（${currentFen} -> ${valueFen} 分）`;
    }
  }
  if (valueFen === undefined) {
    return { valid: false, error: `不支持的调整表达式: "${s}"。支持的格式: "+20%"、"-10%"、"*2"、"+50"（加50分）、"-30"（减30分）` };
  }
  if (valueFen === currentFen) {
    return { valid: false, error: `调整表达式 "${s}" 变化量不足 1 分：当前 ${currentFen} 分，计算后仍为 ${valueFen} 分。API 最小精度为分，请加大调整幅度` };
  }
  return { valid: true, value: valueFen, description };
}

export function parseRateAdjustment(expr, currentRate) {
  const s = String(expr).trim();
  const currentMilli = Math.round(currentRate * 1000);
  let valueMilli;
  let description;

  const pctMatch = s.match(/^([+-])(\d+(?:\.\d+)?)%$/);
  if (pctMatch) {
    const sign = pctMatch[1];
    const pct = parseFloat(pctMatch[2]);
    if (isNaN(pct) || pct <= 0) return { valid: false, error: `百分比数值无效: "${s}"` };
    const factor = sign === "+" ? (1 + pct / 100) : (1 - pct / 100);
    valueMilli = Math.round(currentMilli * factor);
    description = (sign === "+" ? `增加${pct}%` : `减少${pct}%`) + `（${currentRate} -> ${valueMilli / 1000}）`;
  }
  if (valueMilli === undefined) {
    const mulMatch = s.match(/^\*(\d+(?:\.\d+)?)$/);
    if (mulMatch) {
      const factor = parseFloat(mulMatch[1]);
      if (isNaN(factor) || factor <= 0) return { valid: false, error: `乘数必须为正数: "${s}"` };
      valueMilli = Math.round(currentMilli * factor);
      description = `乘以${factor}（${currentRate} -> ${valueMilli / 1000}）`;
    }
  }
  if (valueMilli === undefined) {
    const addMatch = s.match(/^([+-])(\d+(?:\.\d+)?)$/);
    if (addMatch) {
      const sign = addMatch[1];
      const delta = parseFloat(addMatch[2]);
      if (isNaN(delta) || delta <= 0) return { valid: false, error: `调整数值无效: "${s}"` };
      const deltaMilli = Math.round(delta * 1000);
      valueMilli = sign === "+" ? currentMilli + deltaMilli : currentMilli - deltaMilli;
      description = (sign === "+" ? `加${delta}` : `减${delta}`) + `（${currentRate} -> ${valueMilli / 1000}）`;
    }
  }
  if (valueMilli === undefined) {
    return { valid: false, error: `不支持的调整表达式: "${s}"。支持的格式: "+20%"、"-10%"、"*2"、"+0.5"、"-0.3"` };
  }
  if (valueMilli === currentMilli) {
    return { valid: false, error: `调整表达式 "${s}" 变化量不足：当前 ${currentRate}，计算后仍为 ${valueMilli / 1000}。最小精度为 0.001，请加大调整幅度` };
  }
  return { valid: true, value: valueMilli / 1000, description };
}

/**
 * 检查输入是否包含至少一个更新字段。
 */
export function hasAnyUpdateField(input) {
  return UPDATE_FIELDS.some((f) => input[f] !== undefined)
    || ADJUSTMENT_FIELDS.some((f) => input[f] !== undefined);
}

/**
 * 检查广告是否为搜索广告。
 */
export function isSearchAd(currentAdgroup) {
  const siteSet = currentAdgroup.site_set || [];
  return siteSet.some((s) => SEARCH_AD_SITE_SETS.has(s));
}
