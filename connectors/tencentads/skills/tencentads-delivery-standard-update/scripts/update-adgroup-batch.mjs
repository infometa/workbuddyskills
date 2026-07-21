#!/usr/bin/env node
/**
 * update-adgroup-batch.mjs -- 多账号多广告异构字段批量更新
 *
 * 支持一次调用中更新多个不同账号、不同广告、不同字段组合。
 * 每个广告的更新字段格式与 update-adgroup-general.mjs 完全一致。
 *
 * 执行流程:
 *   1. 解析 tasks 数组，按 account_id 分组
 *   2. 各账号并行：批量 adgroups/get 前置查询
 *   3. 逐个广告：buildUpdateBody + adgroups/update
 *   4. 各账号并行：批量 adgroups/get 回查验证
 *   5. 汇总输出所有结果
 *
 * 入参:
 * '{
 *   "tasks": [
 *     { "account_id": "123", "adgroup_id": "111", "bid_amount": 12050 },
 *     { "account_id": "123", "adgroup_id": "222", "adgroup_name": "新名", "configured_status": "AD_STATUS_SUSPEND" },
 *     { "account_id": "456", "adgroup_id": "333", "bid_amount_adjustment": "+20%" }
 *   ]
 * }'
 *
 * 输出:
 * {
 *   "total": 3,
 *   "success_count": 2,
 *   "fail_count": 1,
 *   "skip_count": 0,
 *   "results": [ ... ]
 * }
 */

import { callApi, resolveAutoDerivedCreativePreference, resolveTargetingFields } from "tencentads-cli";
import { QUERY_FIELDS, VERIFY_FIELDS, SEARCH_AD_SITE_SETS, hasAnyUpdateField, isSearchAd } from "./_update-helpers.mjs";
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
  if (!raw) throw new Error("缺少入参");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}` }));
  process.exit(1);
}

const { tasks } = input;

if (!Array.isArray(tasks) || tasks.length === 0) {
  console.log(JSON.stringify({ error: "tasks 必须为非空数组" }));
  process.exit(1);
}

if (tasks.length > 50) {
  console.log(JSON.stringify({ error: `tasks 数组长度 ${tasks.length} 超出上限 50` }));
  process.exit(1);
}

// =====================================================================
// 2. 预校验每个 task
// =====================================================================

for (let i = 0; i < tasks.length; i++) {
  const t = tasks[i];
  if (!t.account_id) {
    console.log(JSON.stringify({ error: `tasks[${i}]: 缺少 account_id` }));
    process.exit(1);
  }
  if (!t.adgroup_id) {
    console.log(JSON.stringify({ error: `tasks[${i}]: 缺少 adgroup_id` }));
    process.exit(1);
  }
  if (!hasAnyUpdateField(t)) {
    console.log(JSON.stringify({ error: `tasks[${i}] (adgroup_id=${t.adgroup_id}): 至少需要一个更新字段` }));
    process.exit(1);
  }
}

// =====================================================================
// 3. 按 account_id 分组
// =====================================================================

const accountGroups = new Map(); // Map<string, task[]>
for (const t of tasks) {
  const key = String(t.account_id);
  if (!accountGroups.has(key)) accountGroups.set(key, []);
  accountGroups.get(key).push(t);
}

// =====================================================================
// 4. 处理单个账号下的所有任务
// =====================================================================

/**
 * 处理一个账号下的所有广告更新任务。
 * @param {string} accountId
 * @param {object[]} accountTasks
 * @returns {Promise<object[]>} 每个广告的更新结果
 */
async function processAccount(accountId, accountTasks) {
  const acctId = parseInt(accountId, 10);
  const adgroupIds = accountTasks.map(t => parseInt(String(t.adgroup_id), 10));
  const results = [];

  // -- 4a. 批量前置查询 --
  let adgroupMap = new Map(); // Map<number, adgroupData>
  let queryFailed = false;
  let queryFailReason = "";
  try {
    const queryParams = {
      method: "GET",
      path: "/v3.0/adgroups/get",
      accountId: accountId,
      params: {
        account_id: acctId,
        filtering: [{
          field: "adgroup_id",
          operator: adgroupIds.length === 1 ? "EQUALS" : "IN",
          values: adgroupIds.map(String),
        }],
        fields: QUERY_FIELDS,
        page: 1,
        page_size: Math.min(adgroupIds.length, 100),
      },
    };
    console.error(`[BATCH] >> adgroups/get (account ${accountId}, ${adgroupIds.length} ads)`);
    const queryResult = await callApi(queryParams);
    if (queryResult.success) {
      const list = queryResult.data?.data?.list ?? queryResult.data?.list ?? [];
      for (const ad of list) {
        adgroupMap.set(ad.adgroup_id, ad);
      }
    } else {
      queryFailed = true;
      queryFailReason = queryResult.error?.message || "API 调用失败";
      console.error(`[BATCH] !! adgroups/get failed for account ${accountId}: ${queryFailReason}`);
    }
  } catch (err) {
    queryFailed = true;
    queryFailReason = err.message;
    console.error(`[BATCH] !! adgroups/get exception for account ${accountId}: ${err.message}`);
  }

  // -- 4b. 逐个任务处理 --
  for (const task of accountTasks) {
    const adgroupId = parseInt(String(task.adgroup_id), 10);
    const curAd = adgroupMap.get(adgroupId);

    // 广告不存在
    if (!curAd) {
      const reason = queryFailed
        ? `前置查询失败（${queryFailReason}），无法获取广告数据`
        : `在账户 ${accountId} 下未找到广告 ${adgroupId}`;
      results.push({
        account_id: accountId,
        adgroup_id: adgroupId,
        success: false,
        error: reason,
        message: `广告 ${adgroupId} 更新失败: ${reason}`,
      });
      continue;
    }

    // 已删除
    if (curAd.is_deleted) {
      results.push({
        account_id: accountId,
        adgroup_id: adgroupId,
        success: false,
        error: `广告 ${adgroupId} 已被删除`,
        message: `广告 ${adgroupId} 更新失败: 已删除`,
      });
      continue;
    }

    // 搜索广告拦截
    if (isSearchAd(curAd)) {
      results.push({
        account_id: accountId,
        adgroup_id: adgroupId,
        success: false,
        error: `广告 ${adgroupId} 是搜索广告，暂不支持更新`,
        is_search_ad: true,
        message: `广告 ${adgroupId} 更新失败: 搜索广告暂不支持`,
      });
      continue;
    }

    // 构建更新参数
    const buildResult = await buildUpdateBody(task, curAd, {
      callApi,
      resolveAutoDerivedCreativePreference,
      resolveTargetingFields,
    });

    if (buildResult.error) {
      const r = {
        account_id: accountId,
        adgroup_id: adgroupId,
        success: false,
        error: buildResult.error,
        message: `广告 ${adgroupId} 更新失败: ${buildResult.error}`,
      };
      if (buildResult.sideEffects && buildResult.sideEffects.length > 0) {
        r.side_effects = buildResult.sideEffects;
        r.message += `（注意: 已执行的副作用: ${buildResult.sideEffects.join("; ")}）`;
      }
      results.push(r);
      continue;
    }

    const { updateBody, updatedFields, skippedFields, sideEffects } = buildResult;

    // 无实际变更
    if (Object.keys(updatedFields).length === 0) {
      results.push({
        account_id: accountId,
        adgroup_id: adgroupId,
        success: true,
        skipped: true,
        updated_fields: {},
        skipped_fields: skippedFields,
        message: `广告 ${adgroupId}: 所有字段已与目标一致，无需更新`,
      });
      continue;
    }

    // 调用 adgroups/update
    try {
      const updateParams = {
        method: "POST",
        path: "/v3.0/adgroups/update",
        accountId: accountId,
        body: updateBody,
      };
      console.error(`[BATCH] >> adgroups/update (ad ${adgroupId})`);
      const updateResult = await callApi(updateParams);

      let updateSuccess = false;
      let updateError = null;
      if (updateResult.success) {
        const respData = updateResult.data?.data ?? updateResult.data ?? {};
        const respCode = updateResult.data?.code ?? respData?.code;
        if (respCode !== undefined && respCode !== 0) {
          const respMsg = updateResult.data?.message || respData?.message || "未知错误";
          const respMsgCn = updateResult.data?.message_cn || respData?.message_cn || "";
          updateError = `API 错误码 ${respCode}: ${respMsg}${respMsgCn ? `（${respMsgCn}）` : ""}`;
        } else {
          updateSuccess = true;
        }
      } else {
        updateError = updateResult.error?.message || "API 调用失败";
      }

      // 构建变更描述
      const descParts = [];
      for (const [field, val] of Object.entries(updatedFields)) {
        if (val.previous !== undefined && val.unit === "fen") {
          descParts.push(`${field} ${val.previous} -> ${val.target} 分`);
        } else if (val.previous !== undefined) {
          descParts.push(`${field} ${val.previous} -> ${val.target}`);
        } else {
          descParts.push(`${field}: ${val.target}`);
        }
      }

      const result = {
        account_id: accountId,
        adgroup_id: adgroupId,
        success: updateSuccess,
        updated_fields: updatedFields,
      };
      if (skippedFields.length > 0) result.skipped_fields = skippedFields;
      if (updateSuccess) {
        result.message = `广告 ${adgroupId} 更新成功: ${descParts.join("; ")}`;
      } else {
        result.error = updateError;
        result.message = `广告 ${adgroupId} 更新失败: ${updateError}`;
        if (sideEffects && sideEffects.length > 0) {
          result.side_effects = sideEffects;
          result.message += `（注意: 已执行的副作用: ${sideEffects.join("; ")}）`;
        }
      }
      results.push(result);
    } catch (err) {
      results.push({
        account_id: accountId,
        adgroup_id: adgroupId,
        success: false,
        error: err.message,
        message: `广告 ${adgroupId} 更新异常: ${err.message}`,
      });
    }
  }

  // -- 4c. 批量回查 --
  const successIds = results.filter(r => r.success && !r.skipped).map(r => r.adgroup_id);
  if (successIds.length > 0) {
    try {
      const verifyResult = await callApi({
        method: "GET",
        path: "/v3.0/adgroups/get",
        accountId: accountId,
        params: {
          account_id: acctId,
          filtering: [{
            field: "adgroup_id",
            operator: successIds.length === 1 ? "EQUALS" : "IN",
            values: successIds.map(String),
          }],
          fields: VERIFY_FIELDS,
          page: 1,
          page_size: Math.min(successIds.length, 100),
        },
      });
      if (verifyResult.success) {
        const list = verifyResult.data?.data?.list ?? verifyResult.data?.list ?? [];
        const verifyMap = new Map();
        for (const ad of list) verifyMap.set(ad.adgroup_id, ad);
        for (const r of results) {
          if (r.success && !r.skipped && verifyMap.has(r.adgroup_id)) {
            r._verify = verifyMap.get(r.adgroup_id);
          }
        }
      } else {
        // 回查 API 调用失败，标记所有成功广告需手动确认
        const verifyError = verifyResult.error?.message || "回查 API 调用失败";
        for (const r of results) {
          if (r.success && !r.skipped) {
            r._verify_failed = true;
            r._verify_error = verifyError;
          }
        }
        console.error(`[BATCH] !! verify adgroups/get failed for account ${accountId}: ${verifyError}`);
      }
    } catch (err) {
      // 回查异常，标记所有成功广告需手动确认
      for (const r of results) {
        if (r.success && !r.skipped) {
          r._verify_failed = true;
          r._verify_error = err.message;
        }
      }
      console.error(`[BATCH] !! verify adgroups/get exception for account ${accountId}: ${err.message}`);
    }
  }

  return results;
}

// =====================================================================
// 5. 各账号并行执行 + 汇总输出
// =====================================================================

const allResultsNested = await Promise.all(
  Array.from(accountGroups.entries()).map(([acctId, acctTasks]) =>
    processAccount(acctId, acctTasks)
  )
);

const allResults = allResultsNested.flat();

const successCount = allResults.filter(r => r.success && !r.skipped).length;
const skipCount = allResults.filter(r => r.success && r.skipped).length;
const failCount = allResults.filter(r => !r.success).length;

const output = {
  total: allResults.length,
  success_count: successCount,
  fail_count: failCount,
  skip_count: skipCount,
  results: allResults,
};

if (failCount === 0 && skipCount === 0) {
  output.message = `全部 ${successCount} 个广告更新成功`;
} else if (failCount === 0) {
  output.message = `${successCount} 个广告更新成功，${skipCount} 个无变化已跳过`;
} else {
  output.message = `${successCount} 个成功，${failCount} 个失败，${skipCount} 个跳过。请务必将失败详情告知用户`;
}

console.log(JSON.stringify(output, null, 2));

// 输出回查汇总
const verifyItems = allResults.filter(r => r._verify);
const verifyFailedItems = allResults.filter(r => r._verify_failed);
if (verifyItems.length > 0) {
  console.log("\n" + JSON.stringify({
    _verify: "以下是更新后的广告最新数据。请与用户期望对比，如有差异请明确告知用户。",
    adgroups: verifyItems.map(r => ({
      adgroup_id: r.adgroup_id,
      account_id: r.account_id,
      updated_fields: Object.keys(r.updated_fields),
      data: r._verify,
    })),
  }, null, 2));
}
if (verifyFailedItems.length > 0) {
  console.log("\n" + JSON.stringify({
    _verify: "更新后回查广告数据失败，请提醒用户手动确认以下广告的更新结果。",
    failed_adgroups: verifyFailedItems.map(r => ({
      adgroup_id: r.adgroup_id,
      account_id: r.account_id,
      error: r._verify_error,
    })),
  }, null, 2));
}
