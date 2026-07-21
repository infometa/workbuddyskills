#!/usr/bin/env node
/**
 * update-adgroup-general.mjs -- 广告通用更新（单账号单广告）
 *
 * 封装腾讯广告开放 API：
 *   1. adgroups/get -- 前置查询广告当前值（存在性校验 + 无变化字段跳过）
 *   2. adgroups/update -- 同步更新广告（多字段一次提交）
 *   3. adgroups/get -- 回查验证更新结果
 *
 *
 * 支持的更新字段（17 个 + 5 个相对调整字段）:
 *   - adgroup_name: 广告名称
 *   - begin_date / end_date: 投放日期
 *   - delivery_time_ranges: 投放时段（自动转 336 位 time_series）
 *   - first_day_begin_time: 首日开始投放时间（格式 HH:MM:SS，默认 00:00:00，可单独传入，投放时段需包含该时间）
 *   - bid_amount: 出价（单位：分）
 *   - bid_amount_adjustment: 出价相对调整（与 bid_amount 二选一，如 "+20%"、"-10%"、"*2"、"+50"）
 *   - daily_budget: 日预算（单位：分，0=不限）
 *   - daily_budget_adjustment: 日预算相对调整（与 daily_budget 二选一）
 *   - configured_status: 广告状态（AD_STATUS_NORMAL / AD_STATUS_SUSPEND）
 *   - targeting: 定向设置
 *   - deep_conversion_behavior_bid: 深度优化行为出价（单位：分）
 *   - deep_conversion_behavior_bid_adjustment: 深度优化行为出价相对调整
 *   - deep_conversion_worth_rate: 深度优化期望ROI系数（无单位）
 *   - deep_conversion_worth_rate_adjustment: 深度优化期望ROI系数相对调整
 *   - auto_acquisition_enabled: 一键起量开关
 *   - auto_acquisition_budget: 一键起量预算（单位：分）
 *   - auto_acquisition_budget_adjustment: 一键起量预算相对调整（与 auto_acquisition_budget 二选一，仅已开启时可用）
 *   - auto_derived_creative_enabled: 创意衍生开关（开启时自动查询可用衍生方式）
 *   - auto_derived_creative_method_type_list: 创意衍生偏好（开启时可选，不传自动用推荐项）
 *   - rta_id: RTA 策略 ID（字符串）
 *   - rta_target_id: RTA 目标 ID（字符串）
 *
 * 入参:
 * '{
 *   "account_id": "12345678",          // 必填，广告主账号 ID
 *   "adgroup_id": "111111",            // 必填，单个广告 ID
 *
 *   // === 以下字段全部可选，至少传一个 ===
 *   "adgroup_name": "新广告名称",
 *   "begin_date": "2026-04-10",
 *   "end_date": "2026-05-10",
 *   "delivery_time_ranges": ["Monday 09:00~18:00", "Friday 09:00~18:00"],
 *   "first_day_begin_time": "09:00:00",   // 可选，首日开始投放时间（格式 HH:MM:SS，默认 00:00:00，可单独传入，投放时段需包含该时间）
 *   "bid_amount": 12050,               // 单位：分（绝对值模式，如 120.50元 = 12050分）
 *   "bid_amount_adjustment": "-10%",   // 或用相对调整模式（与 bid_amount 二选一）
 *   "daily_budget": 60000,             // 单位：分，0=不限（绝对值模式，如 600元 = 60000分）
 *   "daily_budget_adjustment": "*2",   // 或用相对调整模式（与 daily_budget 二选一）
 *   "configured_status": "AD_STATUS_NORMAL",
 *   "targeting": {},
 *   "deep_conversion_behavior_bid": 5000,  // 单位：分（如 50元 = 5000分）
 *   "deep_conversion_worth_rate": 1.5,     // 比率，不转换（绝对值模式）
 *   "deep_conversion_worth_rate_adjustment": "+10%",  // 或用相对调整模式（与 deep_conversion_worth_rate 二选一）
 *   "auto_acquisition_enabled": true,
 *   "auto_acquisition_budget": 50000,      // 单位：分（绝对值模式，如 500元 = 50000分）
 *   "auto_acquisition_budget_adjustment": "+10%",  // 或用相对调整模式（与 auto_acquisition_budget 二选一，仅已开启时可用）
 *   "auto_derived_creative_enabled": true,
 *   "auto_derived_creative_method_type_list": ["AUTO_DERIVED_CREATIVE_METHOD_TYPE_AIGC"],
 *   "rta_id": "1001",                     // RTA 策略 ID
 *   "rta_target_id": "2001"               // RTA 目标 ID
 * }'
 *
 * 输出:
 * {
 *   "account_id": "12345678",
 *   "adgroup_id": 111111,
 *   "success": true,
 *   "updated_fields": { ... },
 *   "skipped_fields": [ ... ],
 *   "message": "广告 111111 更新成功: ..."
 * }
 */

import { callApi, resolveAutoDerivedCreativePreference, resolveTargetingFields } from "tencentads-cli";
import {
  UPDATE_FIELDS, ADJUSTMENT_FIELDS, QUERY_FIELDS, VERIFY_FIELDS,
  SEARCH_AD_SITE_SETS, hasAnyUpdateField, isSearchAd,
} from "./_update-helpers.mjs";
import { buildUpdateBody } from "./_build-update-body.mjs";

// =====================================================================
// 1. 参数解析
// =====================================================================

let input;
try {
  let raw;
  if (process.argv[2] === "--file") {
    const filePath = process.argv[3];
    if (!filePath) throw new Error("--file 后需指定 JSON 文件路径");
    const { readFileSync } = await import("node:fs");
    raw = readFileSync(filePath, "utf8").trim();
  } else {
    raw = process.argv[2];
  }
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串或使用 --file <path> 指定 JSON 文件");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({
    error: `参数解析失败: ${err.message}。支持两种传参方式：1) 直接传 JSON 字符串；2) --file params.json 从文件读取`,
  }));
  process.exit(1);
}

const { account_id, adgroup_id } = input;

// =====================================================================
// 2. 参数校验
// =====================================================================

if (!account_id) {
  console.log(JSON.stringify({ error: "缺少必填字段: account_id" }));
  process.exit(1);
}

if (!adgroup_id) {
  console.log(JSON.stringify({ error: "缺少必填字段: adgroup_id" }));
  process.exit(1);
}

const acctId = parseInt(String(account_id), 10);
const adgroupId = parseInt(String(adgroup_id), 10);

if (isNaN(acctId) || isNaN(adgroupId)) {
  console.log(JSON.stringify({ error: "account_id 和 adgroup_id 必须为有效数字" }));
  process.exit(1);
}

// 检查是否至少传入一个更新字段（含 adjustment 伴随字段）
if (!hasAnyUpdateField(input)) {
  console.log(JSON.stringify({
    error: "至少需要传入一个更新字段。支持的字段: " + UPDATE_FIELDS.concat(ADJUSTMENT_FIELDS).join(", "),
  }));
  process.exit(1);
}

// =====================================================================
// 3. 前置查询：获取广告当前数据
// =====================================================================

let currentAdgroup = null;

const queryParams = {
  method: "GET",
  path: "/v3.0/adgroups/get",
  accountId: String(account_id),
  params: {
    account_id: acctId,
    filtering: [
      {
        field: "adgroup_id",
        operator: "EQUALS",
        values: [String(adgroupId)],
      },
    ],
    fields: QUERY_FIELDS,
    page: 1,
    page_size: 1,
  },
};

try {
  console.error(`[API-LOG] >> adgroups/get (query) request: ${JSON.stringify(queryParams)}`);
  const queryResult = await callApi(queryParams);
  console.error(`[API-LOG] << adgroups/get (query) response: ${JSON.stringify(queryResult)}`);

  if (!queryResult.success) {
    console.log(JSON.stringify({
      error: `查询广告 ${adgroupId} 失败: ${queryResult.error?.message || "API 调用失败"}`,
    }));
    process.exit(1);
  }

  const queryData = queryResult.data?.data ?? queryResult.data ?? {};
  const list = queryData.list ?? [];

  if (list.length === 0) {
    console.log(JSON.stringify({
      error: `在账户 ${account_id} 下未找到广告 ${adgroupId}`,
    }));
    process.exit(1);
  }

  currentAdgroup = list[0];
} catch (err) {
  console.error(`[API-LOG] !! adgroups/get (query) exception: ${err.message}`);
  console.log(JSON.stringify({
    error: `查询广告失败: ${err.message}`,
  }));
  process.exit(1);
}

// -- 检查广告是否已删除 --
if (currentAdgroup.is_deleted) {
  console.log(JSON.stringify({
    error: `广告 ${adgroupId} 已被删除，不允许更新`,
  }));
  process.exit(1);
}

// -- 搜索广告拦截 --
if (isSearchAd(currentAdgroup)) {
  const adName = currentAdgroup.adgroup_name || String(adgroupId);
  console.log(JSON.stringify({
    error: `[搜索广告拦截] 广告「${adName}」(ID: ${adgroupId}) 是搜索广告，当前版本暂不支持搜索广告的更新操作。搜索广告的管理在投放端操作更灵活精准，建议前往广告投放端进行修改。`,
    is_search_ad: true,
    adgroup_id: adgroupId,
    adgroup_name: adName,
    site_set: currentAdgroup.site_set || [],
  }));
  process.exit(1);
}

// =====================================================================
// 4. 构建更新参数（使用共享 buildUpdateBody）
// =====================================================================

const buildResult = await buildUpdateBody(input, currentAdgroup, {
  callApi,
  resolveAutoDerivedCreativePreference,
  resolveTargetingFields,
});

if (buildResult.error) {
  console.log(JSON.stringify({ error: buildResult.error }));
  process.exit(1);
}

const { updateBody, updatedFields, skippedFields, sideEffects } = buildResult;

// =====================================================================
// 5. 检查是否有实际变更
// =====================================================================

if (Object.keys(updatedFields).length === 0) {
  const output = {
    account_id: String(account_id),
    adgroup_id: adgroupId,
    success: true,
    skipped: true,
    updated_fields: {},
    skipped_fields: skippedFields,
    message: `广告 ${adgroupId}: 所有字段值已与目标一致，无需更新。已跳过: ${skippedFields.join("; ")}`,
  };
  console.log(JSON.stringify(output, null, 2));
  process.exit(0);
}

// =====================================================================
// 6. 执行更新（同步 adgroups/update API）
// =====================================================================

let updateSuccess = false;
let updateError = null;

const updateParams = {
  method: "POST",
  path: "/v3.0/adgroups/update",
  accountId: String(account_id),
  body: updateBody,
};

try {
  console.error(`[API-LOG] >> adgroups/update request: ${JSON.stringify(updateParams)}`);
  const updateResult = await callApi(updateParams);
  console.error(`[API-LOG] << adgroups/update response: ${JSON.stringify(updateResult)}`);

  if (updateResult.success) {
    const respData = updateResult.data?.data ?? updateResult.data ?? {};
    const respCode = updateResult.data?.code ?? respData?.code;
    if (respCode !== undefined && respCode !== 0) {
      updateSuccess = false;
      const respMsg = updateResult.data?.message || respData?.message || "未知错误";
      const respMsgCn = updateResult.data?.message_cn || respData?.message_cn || "";
      updateError = `API 返回错误码 ${respCode}: ${respMsg}${respMsgCn ? `（${respMsgCn}）` : ""}`;
    } else {
      updateSuccess = true;
    }
  } else {
    updateSuccess = false;
    updateError = updateResult.error?.message || "API 调用失败";
  }
} catch (err) {
  console.error(`[API-LOG] !! adgroups/update exception: ${err.message}`);
  updateSuccess = false;
  updateError = err.message;
}

// =====================================================================
// 7. 构建输出结果
// =====================================================================

const fieldNames = Object.keys(updatedFields);
const updateDescParts = [];
for (const [field, val] of Object.entries(updatedFields)) {
  if (val.previous !== undefined && val.unit === "fen") {
    updateDescParts.push(`${field} ${val.previous} -> ${val.target} 分`);
  } else if (val.previous !== undefined) {
    updateDescParts.push(`${field} ${val.previous} -> ${val.target}`);
  } else {
    updateDescParts.push(`${field}: ${val.target}`);
  }
}

const output = {
  account_id: String(account_id),
  adgroup_id: adgroupId,
  success: updateSuccess,
  updated_fields: updatedFields,
};

if (skippedFields.length > 0) {
  output.skipped_fields = skippedFields;
}

if (updateSuccess) {
  output.message = `广告 ${adgroupId} 更新成功: ${updateDescParts.join("; ")}`;
} else {
  output.error = updateError;
  output.message = `广告 ${adgroupId} 更新失败: ${updateError}`;
  if (sideEffects && sideEffects.length > 0) {
    output.side_effects = sideEffects;
    output.message += `（注意: 已执行的副作用: ${sideEffects.join("; ")}）`;
  }
}

console.log(JSON.stringify(output, null, 2));

// =====================================================================
// 8. 更新后回查验证
// =====================================================================

const verifyParams = {
  method: "GET",
  path: "/v3.0/adgroups/get",
  accountId: String(account_id),
  params: {
    account_id: acctId,
    filtering: [
      {
        field: "adgroup_id",
        operator: "EQUALS",
        values: [String(adgroupId)],
      },
    ],
    fields: VERIFY_FIELDS,
    page: 1,
    page_size: 1,
  },
};

try {
  console.error(`[API-LOG] >> adgroups/get (verify) request: ${JSON.stringify(verifyParams)}`);
  const verifyResult = await callApi(verifyParams);
  console.error(`[API-LOG] << adgroups/get (verify) response: ${JSON.stringify(verifyResult)}`);

  if (verifyResult.success) {
    const verifyData = verifyResult.data?.data ?? verifyResult.data ?? {};
    const list = verifyData.list ?? [];
    console.log(
      "\n" +
        JSON.stringify(
          {
            _verify:
              "以下是更新后的最新广告数据。请与用户期望的修改内容进行对比，如有差异请明确告知用户。",
            updated_fields: fieldNames,
            adgroup: list[0] ?? null,
          },
          null,
          2
        )
    );
  } else {
    console.log(
      "\n" +
        JSON.stringify(
          {
            _verify:
              "更新后回查广告数据失败，请提醒用户手动确认。",
            error: verifyResult.error?.message || "回查 API 调用失败",
          },
          null,
          2
        )
    );
  }
} catch (err) {
  console.error(`[API-LOG] !! adgroups/get (verify) exception: ${err.message}`);
  console.log(
    "\n" +
      JSON.stringify(
        {
          _verify:
            "更新后回查广告数据异常，请提醒用户手动确认。",
          error: err.message,
        },
        null,
        2
      )
  );
}
