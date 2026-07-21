/**
 * _build-update-body.mjs -- buildUpdateBody 核心函数
 *
 * 从 update-adgroup-general.mjs 提取的字段构建逻辑。
 * 接收 (input, currentAdgroup, deps) 返回 { updateBody, updatedFields, skippedFields, error? }
 */

import {
  convertDeliveryTimeRanges, parseTimeToSlot, equalWidthLength,
  parseAdjustment, parseRateAdjustment,
  INVALID_TARGETING_KEYS,
} from "./_update-helpers.mjs";

/**
 * @param {object} input - 用户传入的参数（含 account_id, adgroup_id, 更新字段）
 * @param {object} cur - adgroups/get 返回的当前广告数据
 * @param {object} deps - { callApi, resolveAutoDerivedCreativePreference, resolveTargetingFields }
 * @returns {Promise<{updateBody?, updatedFields?, skippedFields?, sideEffects?, error?}>}
 */
export async function buildUpdateBody(input, cur, deps) {
  const { callApi: callApiFn, resolveAutoDerivedCreativePreference: resolveADCP, resolveTargetingFields: resolveTF } = deps;
  const acctId = parseInt(String(input.account_id), 10);
  const adgroupId = parseInt(String(input.adgroup_id), 10);

  const updateBody = { account_id: acctId, adgroup_id: adgroupId };
  const updatedFields = {};
  const skippedFields = [];
  const sideEffects = []; // 记录已执行的不可逆操作（如一键起量先关后开的关闭步骤）

  // -- adgroup_name --
  if (input.adgroup_name !== undefined) {
    const name = String(input.adgroup_name);
    if (name.length === 0) return { error: "adgroup_name 不能为空" };
    const charCount = equalWidthLength(name);
    if (charCount > 120) return { error: `adgroup_name 超出长度限制（最多 60 个等宽字符 / 120 个 ASCII 字符），当前: ${charCount} 个 ASCII 字符` };
    if (cur.adgroup_name === name) { skippedFields.push(`adgroup_name（已是 "${name}"）`); }
    else { updateBody.adgroup_name = name; updatedFields.adgroup_name = { previous: cur.adgroup_name, target: name }; }
  }

  // -- begin_date --
  if (input.begin_date !== undefined) {
    const bd = String(input.begin_date);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(bd)) return { error: `begin_date 格式错误: "${bd}"，期望格式 YYYY-MM-DD` };
    if (cur.begin_date === bd) { skippedFields.push(`begin_date（已是 ${bd}）`); }
    else { updateBody.begin_date = bd; updatedFields.begin_date = { previous: cur.begin_date, target: bd }; }
  }

  // -- end_date --
  if (input.end_date !== undefined) {
    const ed = String(input.end_date);
    if (ed !== "" && !/^\d{4}-\d{2}-\d{2}$/.test(ed)) return { error: `end_date 格式错误: "${ed}"，期望格式 YYYY-MM-DD 或空字符串` };
    if (cur.end_date === ed) { skippedFields.push(`end_date（已是 ${ed || "长期投放"}）`); }
    else { updateBody.end_date = ed; updatedFields.end_date = { previous: cur.end_date || "长期投放", target: ed || "长期投放" }; }
  }

  // -- delivery_time_ranges -> time_series --
  if (input.delivery_time_ranges !== undefined) {
    try {
      const ts = convertDeliveryTimeRanges(input.delivery_time_ranges);
      if (cur.time_series === ts) { skippedFields.push("delivery_time_ranges（time_series 未变化）"); }
      else { updateBody.time_series = ts; updatedFields.time_series = { target: "通过 delivery_time_ranges 更新" }; }
    } catch (err) { return { error: err.message }; }
  }

  // -- first_day_begin_time --
  if (input.first_day_begin_time !== undefined) {
    const fdbt = String(input.first_day_begin_time).trim();
    if (!/^\d{2}:\d{2}:\d{2}$/.test(fdbt)) return { error: "first_day_begin_time 格式错误，期望格式 HH:MM:SS（如 09:00:00）" };
    updateBody.first_day_begin_time = fdbt;
    updatedFields.first_day_begin_time = { target: fdbt };
  }

  // -- 交叉校验 time_series vs first_day_begin_time --
  // 仅在用户本次显式传入了 first_day_begin_time 时才校验。
  // 如果用户只改了投放时段（time_series），没有传 first_day_begin_time，
  // 则不用已有的默认值做交叉校验，避免误拦（典型场景：历史默认值 00:00:00
  // 与新时段 09:00~21:00 冲突，但用户根本没有主动设置过首日开始时间）。
  {
    const userSetFdbt = updateBody.first_day_begin_time; // 本次用户显式传入的值
    const ets = updateBody.time_series || cur.time_series;
    const ebd = updateBody.begin_date || cur.begin_date;
    if (userSetFdbt && ets && ebd) {
      // 用户本次显式传入了 first_day_begin_time，校验它是否在投放时段内
      const [hStr, mStr] = userSetFdbt.split(":");
      const h = parseInt(hStr, 10), m = parseInt(mStr, 10);
      const slot = m === 0 ? h * 2 : (m <= 30 ? h * 2 + 1 : (h + 1) * 2);
      const dateObj = new Date(ebd + "T00:00:00");
      const jsDay = dateObj.getDay();
      const dayIndex = jsDay === 0 ? 6 : jsDay - 1;
      if (ets[dayIndex * 48 + slot] !== "1") {
        const dayNames = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
        const dayName = dayNames[dayIndex];
        return { error: `投放时段与首日开始时间不兼容: 广告开始日期 ${ebd} 是${dayName}，但${dayName} ${userSetFdbt} 对应的时间槽不在投放范围内。请调整 delivery_time_ranges 覆盖该时间，或同时修改 first_day_begin_time。` };
      }
    }
  }

  // -- bid_amount / bid_amount_adjustment --
  if (input.bid_amount !== undefined && input.bid_amount_adjustment !== undefined) return { error: "bid_amount 和 bid_amount_adjustment 不能同时传入，请二选一" };
  if (input.bid_amount !== undefined || input.bid_amount_adjustment !== undefined) {
    const curFen = cur.bid_amount ?? 0;
    let fen;
    if (input.bid_amount_adjustment !== undefined) {
      if (curFen === 0) return { error: "bid_amount_adjustment: 当前出价为 0，无法进行相对调整，请使用 bid_amount 传入绝对值（单位：分）" };
      const adj = parseAdjustment(input.bid_amount_adjustment, curFen);
      if (!adj.valid) return { error: `bid_amount_adjustment: ${adj.error}` };
      fen = adj.value;
      if (fen <= 0) return { error: `bid_amount_adjustment "${input.bid_amount_adjustment}" 计算后的出价为 ${fen} 分（<=0），不合法` };
    } else {
      fen = parseInt(input.bid_amount, 10);
      if (isNaN(fen) || fen <= 0) return { error: "bid_amount 必须为正整数（单位: 分）" };
    }
    if (fen === curFen) {
      if (input.bid_amount_adjustment !== undefined) return { error: `bid_amount_adjustment "${input.bid_amount_adjustment}" 变化量不足 1 分：当前出价 ${curFen} 分，计算后仍为 ${fen} 分。API 最小精度为分，请加大调整幅度` };
      skippedFields.push(`bid_amount（已是 ${fen} 分）`);
    } else {
      updateBody.bid_amount = fen;
      updatedFields.bid_amount = { previous: curFen, target: fen, unit: "fen", ...(input.bid_amount_adjustment !== undefined && { adjustment: input.bid_amount_adjustment }) };
    }
  }

  // -- daily_budget / daily_budget_adjustment --
  if (input.daily_budget !== undefined && input.daily_budget_adjustment !== undefined) return { error: "daily_budget 和 daily_budget_adjustment 不能同时传入，请二选一" };
  if (input.daily_budget !== undefined || input.daily_budget_adjustment !== undefined) {
    const curFen = cur.daily_budget ?? 0;
    let fen;
    if (input.daily_budget_adjustment !== undefined) {
      if (curFen === 0) return { error: "daily_budget_adjustment: 当前预算为不限（0），无法进行相对调整，请使用 daily_budget 传入绝对值（单位：分）" };
      const adj = parseAdjustment(input.daily_budget_adjustment, curFen);
      if (!adj.valid) return { error: `daily_budget_adjustment: ${adj.error}` };
      fen = adj.value;
      if (fen <= 0) return { error: `daily_budget_adjustment "${input.daily_budget_adjustment}" 计算后的预算为 ${fen} 分（<=0），不合法。adjustment 不能将预算减至 0（0 在 API 中表示"不限预算"）` };
    } else {
      fen = parseInt(input.daily_budget, 10);
      if (isNaN(fen) || fen < 0) return { error: "daily_budget 必须 >= 0（分，0=不限）" };
    }
    if (fen !== 0 && (fen < 5000 || fen > 400000000)) return { error: `daily_budget 超出范围: ${fen} 分。必须为 0（不限）或 5000~400,000,000 分（50~4,000,000 元）` };
    if (fen === curFen) {
      skippedFields.push(`daily_budget（已是 ${fen === 0 ? "不限" : fen + " 分"}）`);
    } else {
      updateBody.daily_budget = fen;
      updatedFields.daily_budget = { previous: curFen, target: fen, unit: "fen", ...(input.daily_budget_adjustment !== undefined && { adjustment: input.daily_budget_adjustment }) };
    }
  }

  // -- configured_status --
  if (input.configured_status !== undefined) {
    const valid = ["AD_STATUS_NORMAL", "AD_STATUS_SUSPEND"];
    if (!valid.includes(input.configured_status)) return { error: `configured_status 值无效: "${input.configured_status}"，可选值: ${valid.join(", ")}` };
    if (cur.configured_status === input.configured_status) {
      skippedFields.push(`configured_status（已是 ${input.configured_status === "AD_STATUS_NORMAL" ? "投放中" : "暂停"}）`);
    } else {
      updateBody.configured_status = input.configured_status;
      const m = { AD_STATUS_NORMAL: "投放中", AD_STATUS_SUSPEND: "暂停" };
      updatedFields.configured_status = { previous: m[cur.configured_status] || cur.configured_status, target: m[input.configured_status] || input.configured_status };
    }
  }

  // -- rta_id --
  if (input.rta_id !== undefined) {
    const rtaId = String(input.rta_id);
    if (rtaId.length === 0) return { error: "rta_id 不能为空" };
    if (String(cur.rta_id ?? "") === rtaId) { skippedFields.push(`rta_id（已是 "${rtaId}"）`); }
    else { updateBody.rta_id = rtaId; updatedFields.rta_id = { previous: cur.rta_id ?? "", target: rtaId }; }
  }

  // -- rta_target_id --
  if (input.rta_target_id !== undefined) {
    const rtaTargetId = String(input.rta_target_id);
    if (rtaTargetId.length === 0) return { error: "rta_target_id 不能为空" };
    if (String(cur.rta_target_id ?? "") === rtaTargetId) { skippedFields.push(`rta_target_id（已是 "${rtaTargetId}"）`); }
    else { updateBody.rta_target_id = rtaTargetId; updatedFields.rta_target_id = { previous: cur.rta_target_id ?? "", target: rtaTargetId }; }
  }

  // -- bid_adjustment --
  if (input.bid_adjustment !== undefined) {
    if (typeof input.bid_adjustment !== "object" || input.bid_adjustment === null) return { error: "bid_adjustment 必须为对象" };
    updateBody.bid_adjustment = input.bid_adjustment;
    updatedFields.bid_adjustment = { target: "分版位出价已更新" };
  }

  // -- aoi_optimization_strategy --
  if (input.aoi_optimization_strategy !== undefined) {
    updateBody.aoi_optimization_strategy = input.aoi_optimization_strategy;
    updatedFields.aoi_optimization_strategy = { target: String(input.aoi_optimization_strategy) };
  }

  // -- smart_delivery_aigc_creative --
  if (input.smart_delivery_aigc_creative !== undefined) {
    if (typeof input.smart_delivery_aigc_creative !== "object" || input.smart_delivery_aigc_creative === null) return { error: "smart_delivery_aigc_creative 必须为对象" };
    updateBody.smart_delivery_aigc_creative = input.smart_delivery_aigc_creative;
    updatedFields.smart_delivery_aigc_creative = { target: "AIGC创意配置已更新" };
  }

  // -- smart_delivery_history_comp_reused_creative --
  if (input.smart_delivery_history_comp_reused_creative !== undefined) {
    if (typeof input.smart_delivery_history_comp_reused_creative !== "object" || input.smart_delivery_history_comp_reused_creative === null) return { error: "smart_delivery_history_comp_reused_creative 必须为对象" };
    updateBody.smart_delivery_history_comp_reused_creative = input.smart_delivery_history_comp_reused_creative;
    updatedFields.smart_delivery_history_comp_reused_creative = { target: "全库智选配置已更新" };
  }

  // -- poi_list --
  if (input.poi_list !== undefined) {
    if (!Array.isArray(input.poi_list)) return { error: "poi_list 必须为数组" };
    updateBody.poi_list = input.poi_list;
    updatedFields.poi_list = { target: input.poi_list.length === 0 ? "已清空" : `${input.poi_list.length} 个 POI` };
  }

  // -- re_open_auto_acquisition --
  if (input.re_open_auto_acquisition !== undefined) {
    updateBody.re_open_auto_acquisition = input.re_open_auto_acquisition;
    updatedFields.re_open_auto_acquisition = { target: String(input.re_open_auto_acquisition) };
  }

  // -- industry_value_explore --
  if (input.industry_value_explore !== undefined) {
    if (typeof input.industry_value_explore !== "object" || input.industry_value_explore === null) return { error: "industry_value_explore 必须为对象" };
    updateBody.industry_value_explore = input.industry_value_explore;
    updatedFields.industry_value_explore = { target: "行业探索配置已更新" };
  }

  // -- targeting --
  if (input.targeting !== undefined) {
    if (typeof input.targeting !== "object" || input.targeting === null || Array.isArray(input.targeting)) return { error: "targeting 必须为对象类型" };
    const badKeys = Object.keys(input.targeting).filter((k) => INVALID_TARGETING_KEYS.has(k));
    if (badKeys.length > 0) return { error: `targeting 包含不可修改的字段: ${badKeys.join(", ")}。这些字段在创建时绑定，无法通过 API 修改。` };
    resolveTF(input.targeting);
    // 合并策略：用户传入的 key 覆盖原值，未传入的保留原有定向（防止清空）
    // 传空对象 {} 表示通投（清空所有定向）
    const curTargeting = cur.targeting && typeof cur.targeting === "object" ? cur.targeting : {};
    const merged = Object.keys(input.targeting).length === 0
      ? {}  // 空对象 = 通投，不合并
      : { ...curTargeting, ...input.targeting };
    // 清除 merged 中的无效 key（可能从 cur 带入）
    for (const k of Object.keys(merged)) {
      if (INVALID_TARGETING_KEYS.has(k)) delete merged[k];
    }
    updateBody.targeting = merged;
    updatedFields.targeting = { target: "定向已更新" };
  }

  // -- deep_conversion_behavior_bid / adjustment --
  if (input.deep_conversion_behavior_bid !== undefined && input.deep_conversion_behavior_bid_adjustment !== undefined) return { error: "deep_conversion_behavior_bid 和 adjustment 不能同时传入，请二选一" };
  if (input.deep_conversion_behavior_bid !== undefined || input.deep_conversion_behavior_bid_adjustment !== undefined) {
    const curFen = cur.deep_conversion_behavior_bid ?? 0;
    let fen;
    if (input.deep_conversion_behavior_bid_adjustment !== undefined) {
      if (curFen === 0) return { error: "deep_conversion_behavior_bid_adjustment: 当前深度出价为 0，无法进行相对调整" };
      const adj = parseAdjustment(input.deep_conversion_behavior_bid_adjustment, curFen);
      if (!adj.valid) return { error: `deep_conversion_behavior_bid_adjustment: ${adj.error}` };
      fen = adj.value;
      if (fen <= 0) return { error: `deep_conversion_behavior_bid_adjustment "${input.deep_conversion_behavior_bid_adjustment}" 计算后 ${fen} 分（<=0），不合法` };
    } else { fen = parseInt(input.deep_conversion_behavior_bid, 10); }
    if (isNaN(fen) || fen < 0 || fen > 1000000) return { error: `deep_conversion_behavior_bid 超出范围: ${fen} 分` };
    if (fen === curFen) { skippedFields.push(`deep_conversion_behavior_bid（已是 ${fen} 分）`); }
    else {
      updateBody.deep_conversion_behavior_bid = fen;
      updatedFields.deep_conversion_behavior_bid = { previous: curFen, target: fen, unit: "fen", ...(input.deep_conversion_behavior_bid_adjustment !== undefined && { adjustment: input.deep_conversion_behavior_bid_adjustment }) };
    }
  }

  // -- deep_conversion_worth_rate / adjustment --
  if (input.deep_conversion_worth_rate !== undefined && input.deep_conversion_worth_rate_adjustment !== undefined) return { error: "deep_conversion_worth_rate 和 adjustment 不能同时传入，请二选一" };
  if (input.deep_conversion_worth_rate !== undefined || input.deep_conversion_worth_rate_adjustment !== undefined) {
    const curR = cur.deep_conversion_worth_rate ?? 0;
    let tgt;
    if (input.deep_conversion_worth_rate_adjustment !== undefined) {
      if (curR === 0) return { error: "deep_conversion_worth_rate_adjustment: 当前 ROI 系数为 0" };
      const adj = parseRateAdjustment(input.deep_conversion_worth_rate_adjustment, curR);
      if (!adj.valid) return { error: `deep_conversion_worth_rate_adjustment: ${adj.error}` };
      tgt = adj.value;
      if (tgt <= 0) return { error: `deep_conversion_worth_rate_adjustment 计算后 ${tgt}（<=0）` };
    } else { tgt = parseFloat(input.deep_conversion_worth_rate); }
    if (isNaN(tgt) || tgt < 0.001 || tgt > 1000) return { error: `deep_conversion_worth_rate 超出范围: ${tgt}` };
    const rounded = Math.round(tgt * 1000) / 1000;
    if (Math.abs(curR - rounded) < 0.001) { skippedFields.push(`deep_conversion_worth_rate（已是 ${rounded}）`); }
    else {
      updateBody.deep_conversion_worth_rate = rounded;
      updatedFields.deep_conversion_worth_rate = { previous: curR, target: rounded, ...(input.deep_conversion_worth_rate_adjustment !== undefined && { adjustment: input.deep_conversion_worth_rate_adjustment }) };
    }
  }

  // -- auto_acquisition 联动 --
  // 智投项目不支持使用一键起量
  const isSmartDelivery = !!cur.smart_delivery_platform && cur.smart_delivery_platform !== "SMART_DELIVERY_PLATFORM_EDITION_STANDARD";
  const hasAnyAa = input.auto_acquisition_enabled !== undefined || input.auto_acquisition_budget !== undefined || input.auto_acquisition_budget_adjustment !== undefined;
  if (isSmartDelivery && hasAnyAa) {
    return { error: "智投项目不支持使用一键起量（auto_acquisition）功能，一键起量仅适用于标准投放广告。请移除相关字段后重试。" };
  }

  const curAaEnabled = cur.auto_acquisition_enabled === true;
  const hasAbsBudget = input.auto_acquisition_budget !== undefined;
  const hasAdjBudget = input.auto_acquisition_budget_adjustment !== undefined;
  const hasEnabled = input.auto_acquisition_enabled !== undefined;
  if (hasAbsBudget && hasAdjBudget) return { error: "auto_acquisition_budget 和 adjustment 不能同时传入，请二选一" };
  const hasBudget = hasAbsBudget || hasAdjBudget;
  if (hasEnabled && typeof input.auto_acquisition_enabled !== "boolean") return { error: "auto_acquisition_enabled 必须为布尔值（true/false）" };
  const isNewlyEnabling = hasEnabled && input.auto_acquisition_enabled === true && !curAaEnabled;
  if (isNewlyEnabling && hasAdjBudget) return { error: "新开启一键起量时请使用 auto_acquisition_budget 绝对值" };
  const isAdjBudget = curAaEnabled && hasBudget && (!hasEnabled || input.auto_acquisition_enabled === true);
  const bfn = hasAdjBudget ? "auto_acquisition_budget_adjustment" : "auto_acquisition_budget";
  if (hasBudget && !isNewlyEnabling && !isAdjBudget) {
    if (hasEnabled && input.auto_acquisition_enabled === false) return { error: `关闭一键起量时不可设置 ${bfn}` };
    return { error: `一键起量未开启，不可调整 ${bfn}` };
  }
  if (isNewlyEnabling && !hasBudget) return { error: "开启一键起量（auto_acquisition_enabled=true）时，必须同时设置 auto_acquisition_budget" };

  let aaBudgetFen = null, aaAdjExpr = null;
  if (hasBudget) {
    if (hasAdjBudget) {
      const cFen = cur.auto_acquisition_budget ?? 0;
      if (cFen === 0) return { error: "auto_acquisition_budget_adjustment: 当前起量预算为 0，无法进行相对调整，请使用 auto_acquisition_budget 传入绝对值（单位：分）" };
      const adj = parseAdjustment(input.auto_acquisition_budget_adjustment, cFen);
      if (!adj.valid) return { error: `auto_acquisition_budget_adjustment: ${adj.error}` };
      aaBudgetFen = adj.value; aaAdjExpr = input.auto_acquisition_budget_adjustment;
      if (aaBudgetFen <= 0) return { error: `auto_acquisition_budget_adjustment "${input.auto_acquisition_budget_adjustment}" 计算后的预算为 ${aaBudgetFen} 分（<=0），不合法` };
    } else { aaBudgetFen = parseInt(input.auto_acquisition_budget, 10); }
    if (isNaN(aaBudgetFen) || aaBudgetFen < 20000 || aaBudgetFen > 10000000) return { error: `auto_acquisition_budget 超出范围（20000-10000000 分，即 200-100000 元）: ${aaBudgetFen}${aaAdjExpr ? `（由 adjustment "${aaAdjExpr}" 计算得出）` : ""}` };
  }

  // 已开启时调整 budget：先关后开
  if (isAdjBudget) {
    const cFen = cur.auto_acquisition_budget ?? 0;
    if (aaBudgetFen === cFen) {
      if (aaAdjExpr !== null) return { error: `auto_acquisition_budget_adjustment "${aaAdjExpr}" 变化量不足 1 分：当前起量预算 ${cFen} 分，计算后仍为 ${aaBudgetFen} 分。API 最小精度为分，请加大调整幅度` };
      skippedFields.push(`auto_acquisition_budget（已是 ${aaBudgetFen} 分）`);
    } else {
      const closeParams = { method: "POST", path: "/v3.0/adgroups/update", accountId: String(input.account_id), body: { account_id: acctId, adgroup_id: adgroupId, auto_acquisition_enabled: false } };
      try {
        console.error(`[API-LOG] >> adgroups/update (close auto_acquisition) request: ${JSON.stringify(closeParams)}`);
        const closeResult = await callApiFn(closeParams);
        console.error(`[API-LOG] << adgroups/update (close auto_acquisition) response: ${JSON.stringify(closeResult)}`);
        const cc = closeResult.data?.code ?? closeResult.data?.data?.code;
        if (!closeResult.success || (cc !== undefined && cc !== 0)) {
          const msg = closeResult.data?.message || closeResult.data?.data?.message || closeResult.error?.message || "API 调用失败";
          const msgCn = closeResult.data?.message_cn || closeResult.data?.data?.message_cn || "";
          return { error: `调整起量预算失败：关闭一键起量步骤出错 — ${msg}${msgCn ? `（${msgCn}）` : ""}` };
        }
        sideEffects.push("auto_acquisition_enabled 已关闭（先关后开流程的关闭步骤已执行，如主更新失败需手动重新开启）");
      } catch (err) {
        console.error(`[API-LOG] !! adgroups/update (close auto_acquisition) exception: ${err.message}`);
        return { error: `调整起量预算失败：关闭一键起量步骤异常 — ${err.message}` };
      }
      updateBody.auto_acquisition_enabled = true;
      updateBody.auto_acquisition_budget = aaBudgetFen;
      updatedFields.auto_acquisition_enabled = { target: "已开启（先关后开以调整预算）" };
      updatedFields.auto_acquisition_budget = { previous: cFen, target: aaBudgetFen, unit: "fen", ...(aaAdjExpr !== null && { adjustment: aaAdjExpr }) };
    }
  }
  if (hasEnabled && !isAdjBudget) {
    if (input.auto_acquisition_enabled === curAaEnabled) { skippedFields.push(`auto_acquisition_enabled（已是 ${curAaEnabled ? "已开启" : "已关闭"}）`); }
    else { updateBody.auto_acquisition_enabled = input.auto_acquisition_enabled; updatedFields.auto_acquisition_enabled = { previous: curAaEnabled ? "已开启" : "已关闭", target: input.auto_acquisition_enabled ? "已开启" : "已关闭" }; }
  }
  if (hasBudget && isNewlyEnabling) {
    const cFen = cur.auto_acquisition_budget ?? 0;
    if (aaBudgetFen === cFen) { skippedFields.push(`auto_acquisition_budget（已是 ${aaBudgetFen} 分）`); }
    else { updateBody.auto_acquisition_budget = aaBudgetFen; updatedFields.auto_acquisition_budget = { previous: cFen, target: aaBudgetFen, unit: "fen" }; }
  }

  // -- auto_derived_creative --
  if (Array.isArray(input.auto_derived_creative_method_type_list)) {
    const _pref = { auto_derived_creative_method_type_list: input.auto_derived_creative_method_type_list };
    resolveADCP(_pref);
    input.auto_derived_creative_method_type_list = _pref.auto_derived_creative_method_type_list;
  }
  if (input.auto_derived_creative_enabled !== undefined) {
    if (typeof input.auto_derived_creative_enabled !== "boolean") return { error: "auto_derived_creative_enabled 必须为布尔值（true/false）" };
    if (input.auto_derived_creative_enabled) {
      const deriveSiteSet = cur.site_set || [];
      const deriveQueryParams = { method: "GET", path: "/v3.0/muse_derive_switch_info/get", accountId: String(input.account_id), params: { account_id: acctId, marketing_target_type: cur.marketing_target_type, marketing_carrier_type: cur.marketing_carrier_type, site_set: JSON.stringify(deriveSiteSet), auto_siteset_switch: cur.automatic_site_enabled ?? false } };
      let deriveMethods = [], showDeriveMethod = false;
      try {
        console.error(`[API-LOG] >> muse_derive_switch_info/get request: ${JSON.stringify(deriveQueryParams)}`);
        const deriveResult = await callApiFn(deriveQueryParams);
        console.error(`[API-LOG] << muse_derive_switch_info/get response: ${JSON.stringify(deriveResult)}`);
        const deriveRespData = deriveResult.data?.data ?? deriveResult.data ?? {};
        const bizCode = deriveResult.data?.code ?? deriveRespData?.code;
        if (bizCode !== undefined && bizCode !== 0) {
          console.error(`[API-LOG] muse_derive_switch_info/get biz error: code=${bizCode}`);
        }
        showDeriveMethod = deriveRespData.show_derive_method ?? false;
        deriveMethods = deriveRespData.derive_method_list ?? [];
      } catch (err) {
        console.error(`[API-LOG] !! muse_derive_switch_info/get exception: ${err.message}`);
        console.error(`[WARN] 创意衍生可用方式查询失败，将直接使用用户传入的衍生方式列表`);
      }
      const availableTypes = deriveMethods.map(m => m.derive_method_type);
      const defaultSelectedTypes = deriveMethods.filter(m => m.is_selected).map(m => m.derive_method_type);
      let finalMethodTypeList;
      if (input.auto_derived_creative_method_type_list !== undefined) {
        if (!Array.isArray(input.auto_derived_creative_method_type_list)) return { error: "auto_derived_creative_method_type_list 必须为数组" };
        if (input.auto_derived_creative_method_type_list.length === 0) return { error: "开启创意衍生时 auto_derived_creative_method_type_list 不能为空数组" };
        if (availableTypes.length > 0) {
          const invalidTypes = input.auto_derived_creative_method_type_list.filter(t => !availableTypes.includes(t));
          if (invalidTypes.length > 0) return {
            error: `以下创意衍生方式不可用: ${invalidTypes.join(", ")}。当前广告可用的衍生方式: ${availableTypes.join(", ")}`,
            available_derive_methods: deriveMethods.map(m => ({ type: m.derive_method_type, name: m.derive_method_name })),
          };
        }
        finalMethodTypeList = input.auto_derived_creative_method_type_list;
      } else if (showDeriveMethod && defaultSelectedTypes.length > 0) { finalMethodTypeList = defaultSelectedTypes; }
      else if (showDeriveMethod && availableTypes.length > 0) { finalMethodTypeList = availableTypes; }
      else if (!showDeriveMethod && deriveMethods.length === 0) { return { error: "该广告当前不支持创意衍生功能（muse_derive_switch_info/get 返回 show_derive_method=false 且无可用衍生方式）。可能原因: 营销目标/版位组合不支持创意衍生。" }; }
      else { finalMethodTypeList = null; }
      updateBody.auto_derived_creative_enabled = true;
      updatedFields.auto_derived_creative_enabled = { target: "已开启" };
      if (finalMethodTypeList && finalMethodTypeList.length > 0) {
        updateBody.auto_derived_creative_preference = { auto_derived_creative_method_type_list: finalMethodTypeList };
        const methodNames = deriveMethods.length > 0
          ? finalMethodTypeList.map(t => { const m = deriveMethods.find(dm => dm.derive_method_type === t); return m ? `${m.derive_method_name}(${t})` : t; })
          : finalMethodTypeList;
        updatedFields.auto_derived_creative_preference = { target: `衍生创意类型: ${methodNames.join(", ")}` };
      }
    } else {
      updateBody.auto_derived_creative_enabled = false;
      updatedFields.auto_derived_creative_enabled = { target: "已关闭" };
      if (input.auto_derived_creative_method_type_list !== undefined) skippedFields.push("auto_derived_creative_method_type_list（关闭创意衍生时衍生方式偏好无效，已忽略）");
    }
  } else if (input.auto_derived_creative_method_type_list !== undefined) {
    if (!Array.isArray(input.auto_derived_creative_method_type_list)) return { error: "auto_derived_creative_method_type_list 必须为数组" };
    updateBody.auto_derived_creative_preference = { auto_derived_creative_method_type_list: input.auto_derived_creative_method_type_list };
    updatedFields.auto_derived_creative_preference = { target: `衍生创意类型: ${input.auto_derived_creative_method_type_list.join(", ")}` };
  }

  // -- 周期达成字段联合校验 --
  const isPeriodProject = cur.smart_delivery_period_switch === "PERIOD_SWITCH_ON";
  const hasPeriodFields = input.smart_delivery_period_budget !== undefined || input.smart_delivery_period_continue !== undefined;

  // 非周期达成项目不允许传周期相关字段
  if (!isPeriodProject && hasPeriodFields) {
    return { error: "该项目不是周期达成项目，不允许设置 smart_delivery_period_budget 或 smart_delivery_period_continue。周期达成开关仅在创建时设置，无法后续开启。" };
  }

  // 周期达成项目禁止设置 daily_budget
  if (isPeriodProject && input.daily_budget !== undefined && input.daily_budget > 0) {
    return { error: "周期达成项目不允许设置 daily_budget（日预算），周期达成使用 smart_delivery_period_budget（周期预算）控制预算" };
  }

  // -- smart_delivery_period_budget （周期达成预算）--
  if (input.smart_delivery_period_budget !== undefined) {
    const curPeriodBudget = cur.smart_delivery_period_budget ?? 0;
    const newBudget = parseInt(input.smart_delivery_period_budget, 10);
    if (isNaN(newBudget) || newBudget <= 0) return { error: "smart_delivery_period_budget 必须为正整数（单位: 分）" };
    // 周期达成项目只允许提升预算
    if (curPeriodBudget > 0 && newBudget < curPeriodBudget) {
      return { error: `smart_delivery_period_budget 只允许提升：当前 ${curPeriodBudget} 分（${curPeriodBudget / 100}元），不允许降低到 ${newBudget} 分（${newBudget / 100}元）` };
    }
    // 预算联合约束：>= 3 * 出价 * 周期天数
    const periodDaysMap = { PERIOD_DAYS_THREE: 3, PERIOD_DAYS_SEVEN: 7 };
    const curPeriodDays = cur.smart_delivery_period_days;
    const periodDayNum = periodDaysMap[curPeriodDays] || 0;
    const bidAmount = (input.bid_amount !== undefined ? parseInt(input.bid_amount, 10) : cur.bid_amount) || 0;
    if (periodDayNum > 0 && bidAmount > 0) {
      const minBudget = 3 * bidAmount * periodDayNum;
      if (newBudget < minBudget) {
        return { error: `smart_delivery_period_budget(${newBudget}分) 不满足约束: 需 >= 3 × 出价(${bidAmount}分) × 周期天数(${periodDayNum}) = ${minBudget}分（${minBudget / 100}元）` };
      }
    }
    if (newBudget === curPeriodBudget) {
      skippedFields.push(`smart_delivery_period_budget（已是 ${newBudget} 分）`);
    } else {
      updateBody.smart_delivery_period_budget = newBudget;
      updatedFields.smart_delivery_period_budget = { previous: curPeriodBudget, target: newBudget, unit: "fen" };
    }
  }

  // 周期达成项目提高出价时也需要校验预算约束
  if (isPeriodProject && input.bid_amount !== undefined && input.smart_delivery_period_budget === undefined) {
    const periodDaysMap = { PERIOD_DAYS_THREE: 3, PERIOD_DAYS_SEVEN: 7 };
    const curPeriodDays = cur.smart_delivery_period_days;
    const periodDayNum = periodDaysMap[curPeriodDays] || 0;
    const curPeriodBudget = cur.smart_delivery_period_budget ?? 0;
    const newBid = parseInt(input.bid_amount, 10) || 0;
    if (periodDayNum > 0 && newBid > 0 && curPeriodBudget > 0) {
      const minBudget = 3 * newBid * periodDayNum;
      if (curPeriodBudget < minBudget) {
        return { error: `提高出价到 ${newBid} 分后，当前周期预算 ${curPeriodBudget} 分不满足约束（需 >= 3 × ${newBid} × ${periodDayNum} = ${minBudget}分）。请同时提高 smart_delivery_period_budget` };
      }
    }
  }

  // -- smart_delivery_period_continue （周期达成续投开关）--
  if (input.smart_delivery_period_continue !== undefined) {
    const validContinue = ["PERIOD_CONTINUE_SWITCH_ON", "PERIOD_CONTINUE_SWITCH_OFF"];
    if (!validContinue.includes(input.smart_delivery_period_continue)) {
      return { error: `smart_delivery_period_continue 值无效: "${input.smart_delivery_period_continue}"，可选值: ${validContinue.join(", ")}` };
    }
    const curContinue = cur.smart_delivery_period_continue;
    if (curContinue === input.smart_delivery_period_continue) {
      skippedFields.push(`smart_delivery_period_continue（已是 ${input.smart_delivery_period_continue === "PERIOD_CONTINUE_SWITCH_ON" ? "续投" : "不续投"}）`);
    } else {
      updateBody.smart_delivery_period_continue = input.smart_delivery_period_continue;
      const m = { PERIOD_CONTINUE_SWITCH_ON: "续投", PERIOD_CONTINUE_SWITCH_OFF: "不续投" };
      updatedFields.smart_delivery_period_continue = { previous: m[curContinue] || curContinue || "未知", target: m[input.smart_delivery_period_continue] };
    }
  }

  return { updateBody, updatedFields, skippedFields, sideEffects };
}
