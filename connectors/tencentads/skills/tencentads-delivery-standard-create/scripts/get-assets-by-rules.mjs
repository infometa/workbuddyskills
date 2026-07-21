#!/usr/bin/env node
/**
 * get-assets-by-rules.mjs — 批量获取所有四元组对应的推广资产 + 可选资产匹配
 *
 * 脚本自动调用 get_rules_by_advertiser API 获取四元组组合（无需 Agent 透传 combinations），
 * 对每个不同的 marketing_target_type 调用 get-assets 的底层逻辑，
 * 返回 { 四元组key: 资产列表 } 的 map 结构。
 *
 * 当提供 match_hint 时，脚本会在查询完成后自动执行资产匹配，
 * 按优先级（ID精确 > 名称完全 > 名称包含）匹配用户指定的资产，
 * 返回 match_result 告知匹配结论。
 *
 * 入参: '{"account_id":"<ID>","marketing_goal":"<可选>","marketing_target_type":"<可选>","match_hint":{"asset_id":"...","asset_name":"..."},"carrier_hint":{"carrier_id":"...","carrier_name":"..."}}'
 *   account_id 必填
 *   marketing_goal 可选，传入后只查该 goal 下的 combinations（减少 API 调用）
 *   marketing_target_type 可选，传入后优先查该 target_type 的资产，命中则跳过其余类型；未命中自动 fallback 全量查询
 *   combinations 可选（向后兼容），传入时直接使用，不传时脚本自动调 API 获取
 *   match_hint 可选，至少包含 asset_id 或 asset_name 之一
 *   carrier_hint 可选，用于载体名称/ID匹配（当载体类型需要 carrier_id 且资产非 ONEID 时生效）
 *
 * 输出:
 * {
 *   "asset_dict": {
 *     "MARKETING_GOAL_LEAD_RETENTION|...|MARKETING_CARRIER_TYPE_JUMP_PAGE": {
 *       "combination": { "marketing_goal": "...", "marketing_sub_goal": "...", "marketing_target_type": "...", "marketing_carrier_type": "...", "product_type": 30 },
 *       "asset_type": "INDUSTRY",
 *       "assets": [ { "marketing_asset_id": "342574", "name": "京投发展森与天成" } ]
 *     }
 *   },
 *   "match_result": {
 *     "status": "unique_match" | "multiple_match" | "name_multiple_match" | "no_match" | "no_hint",
 *     "match_type": "id_exact" | "name_exact" | "name_contains" | null,
 *     "matched_items": [
 *       {
 *         "combination_key": "...",
 *         "combination": {...},
 *         "asset_type": "INDUSTRY",
 *         "asset": { "marketing_asset_id": "342574", "name": "..." },
 *         "flat_params": {
 *           "asset_id": "342574",
 *           "carrier_id": "417200582"
 *         }
 *       }
 *     ]
 *   },
 *   "carrier_result": {
 *     "status": "found" | "not_needed" | "no_carriers" | "match_failed" | "skipped",
 *     "carriers": [ { "carrier_id": "417200582", "carrier_name": "唯品会" } ],
 *     "matched_carrier": { "carrier_id": "417200582", "carrier_name": "唯品会" }
 *   },
 *   "flat_params": { ... }    // unique_match 时顶层也输出一份
 * }
 *
 * match_result.status 说明:
 * - unique_match: 恰好 1 个 combination 下命中 1 条资产，可直接使用
 * - multiple_match: 同一资产存在于多个 combination 下，需用户选择
 * - name_multiple_match: 名称匹配到多个不同资产，需用户确认
 * - no_match: 所有 combination 下都没找到匹配
 * - no_hint: 未传 match_hint，不执行匹配（兼容旧调用）
 *
 * 设计说明：
 * - 相同 marketing_target_type 只调一次 API，结果复用给所有含该 target_type 的四元组
 * - 查询失败或返回空的四元组，value 中 assets 为空数组（不中断流程）
 * - key 格式: marketing_goal|marketing_sub_goal|marketing_target_type|marketing_carrier_type
 * - unique_match 时自动裁剪非命中 combination 的 assets 以减少输出体积
 *
 * 载体自动查询：
 * - 当资产匹配成功（unique_match / multiple_match）且载体类型不是 JUMP_PAGE 时，
 *   如果资产类型不是 ONEID（ONEID 类的 carrier_id 已在资产中），自动查询载体列表。
 * - 统一通过 bff_promoted_objects/get 接口查询
 */

import { callApi } from "tencentads-cli";

import {
  CARRIER_NOT_NEEDED,
  fetchAssetsForTargetType,
  queryAndMatchCarriers,
  isCarrierNotNeeded,
  buildFlatParams,
} from "./asset-shared.mjs";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}` }));
  process.exit(1);
}

const { account_id } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}

// ─── 获取 combinations：优先使用传入的，否则自动调 API 获取 ───

let combinations = input.combinations;

if (!combinations || !Array.isArray(combinations) || combinations.length === 0) {
  try {
    const rulesResult = await callApi({
      method: "POST",
      path: "/v3.0/marketing_target/get_rules_by_advertiser",
      accountId: String(account_id),
      body: { account_id: parseInt(account_id, 10) },
    });

    if (!rulesResult.success) {
      console.log(JSON.stringify({ error: "自动获取四元组失败: " + (rulesResult.error?.message || "API 调用失败"), detail: rulesResult.error }));
      process.exit(1);
    }

    const rulesJson = rulesResult.data?.data?.rules_json ?? rulesResult.data?.rules_json ?? null;
    if (!rulesJson) {
      console.log(JSON.stringify({ error: "自动获取四元组失败: API 返回中未找到 rules_json 字段" }));
      process.exit(1);
    }

    const rulesData = typeof rulesJson === "string" ? JSON.parse(rulesJson) : rulesJson;

    combinations = [];
    for (const [marketingGoal, goalValue] of Object.entries(rulesData)) {
      if (typeof goalValue !== "object" || goalValue === null) continue;
      for (const [marketingTargetType, targetTypeValue] of Object.entries(goalValue)) {
        if (typeof targetTypeValue !== "object" || targetTypeValue === null) continue;
        for (const [marketingSubGoal, subGoalValue] of Object.entries(targetTypeValue)) {
          if (typeof subGoalValue !== "object" || subGoalValue === null) continue;
          for (const [marketingCarrierType, carrierTypeValue] of Object.entries(subGoalValue)) {
            if (typeof carrierTypeValue !== "object" || carrierTypeValue === null) continue;
            const productType = carrierTypeValue?.PRODUCT_TYPE ?? null;
            const combo = {
              marketing_goal: marketingGoal,
              marketing_sub_goal: marketingSubGoal,
              marketing_target_type: marketingTargetType,
              marketing_carrier_type: marketingCarrierType,
            };
            if (productType != null) combo.product_type = productType;
            combinations.push(combo);
          }
        }
      }
    }
  } catch (err) {
    console.log(JSON.stringify({ error: `自动获取四元组失败: ${err.message}` }));
    process.exit(1);
  }

  // 按 marketing_goal 预过滤
  if (input.marketing_goal) {
    combinations = combinations.filter(c => c.marketing_goal === input.marketing_goal);
  }

  if (combinations.length === 0) {
    console.log(JSON.stringify({ error: "无可用的四元组组合" + (input.marketing_goal ? `（marketing_goal=${input.marketing_goal} 下无组合）` : "") }));
    process.exit(1);
  }
}

// ─── 提前解构 match_hint ───

const { match_hint } = input;

// ─── 按 marketing_target_type 去重，每种只调一次 API ───

const allUniqueTargetTypes = [...new Set(combinations.map(c => c.marketing_target_type))];

// 存储每种 target_type 的查询结果
const targetTypeResults = {};

// ─── 优先查询：如果传了 marketing_target_type 且有 match_hint，先只查该类型 ───

const priorityTargetType = input.marketing_target_type || null;
const hasPriority = priorityTargetType && allUniqueTargetTypes.includes(priorityTargetType) && match_hint && (match_hint.asset_id || match_hint.asset_name);

let earlyMatchResult = null;

if (hasPriority) {
  try {
    const result = await fetchAssetsForTargetType(account_id, priorityTargetType, { hint: match_hint });
    targetTypeResults[priorityTargetType] = result;
  } catch (err) {
    targetTypeResults[priorityTargetType] = { asset_type: "UNKNOWN", assets: [] };
  }

  // 用优先组结果组装临时 assetDict，尝试提前匹配
  const priorityAssetDict = {};
  for (const combo of combinations) {
    if (combo.marketing_target_type !== priorityTargetType) continue;
    const key = [combo.marketing_goal, combo.marketing_sub_goal, combo.marketing_target_type, combo.marketing_carrier_type].join("|");
    const result = targetTypeResults[priorityTargetType] || { asset_type: "UNKNOWN", assets: [] };
    const combination = {
      marketing_goal: combo.marketing_goal,
      marketing_sub_goal: combo.marketing_sub_goal,
      marketing_target_type: combo.marketing_target_type,
      marketing_carrier_type: combo.marketing_carrier_type,
    };
    if (combo.product_type != null) combination.product_type = combo.product_type;
    priorityAssetDict[key] = { combination, asset_type: result.asset_type, assets: result.assets };
  }

  const tryMatch = performAssetMatch(priorityAssetDict, match_hint);
  if (tryMatch.status === "unique_match" || tryMatch.status === "multiple_match") {
    earlyMatchResult = tryMatch;
  }
}

// ─── 如果优先查询未命中，继续查剩余 target_type ───

if (!earlyMatchResult) {
  const remainingTypes = allUniqueTargetTypes.filter(t => !targetTypeResults[t]);
  for (const targetType of remainingTypes) {
    try {
      const result = await fetchAssetsForTargetType(account_id, targetType, { hint: match_hint });
      targetTypeResults[targetType] = result;
    } catch (err) {
      targetTypeResults[targetType] = { asset_type: "UNKNOWN", assets: [] };
    }
  }
}

// ─── 组装完整输出 map ───

const assetDict = {};

for (const combo of combinations) {
  const key = [
    combo.marketing_goal,
    combo.marketing_sub_goal,
    combo.marketing_target_type,
    combo.marketing_carrier_type,
  ].join("|");

  const result = targetTypeResults[combo.marketing_target_type] || { asset_type: "UNKNOWN", assets: [] };

  const combination = {
    marketing_goal: combo.marketing_goal,
    marketing_sub_goal: combo.marketing_sub_goal,
    marketing_target_type: combo.marketing_target_type,
    marketing_carrier_type: combo.marketing_carrier_type,
  };
  if (combo.product_type != null) combination.product_type = combo.product_type;

  assetDict[key] = {
    combination,
    asset_type: result.asset_type,
    assets: result.assets,
  };
}

// ─── 资产匹配 ───

const matchResult = earlyMatchResult || performAssetMatch(assetDict, match_hint);

// ─── unique_match 时裁剪非命中 combination 的 assets ───

if (matchResult.status === "unique_match") {
  const matchedKey = matchResult.matched_items[0].combination_key;
  for (const [key, entry] of Object.entries(assetDict)) {
    if (key !== matchedKey) {
      const count = Array.isArray(entry.assets) ? entry.assets.length : 0;
      entry.assets = `[${count} items, omitted]`;
    }
  }
}

// ─── 载体自动查询（资产匹配成功 + 载体类型需要 carrier_id + 资产非 ONEID 时触发） ───

const { carrier_hint } = input;
const carrierResult = await fetchCarrierIfNeeded(account_id, matchResult, carrier_hint);

// ─── 为每条 matched_items 挂载 flat_params ───

if (matchResult.matched_items && matchResult.matched_items.length > 0) {
  for (const item of matchResult.matched_items) {
    const fp = buildFlatParams(
      item.asset,
      item.asset_type,
      carrierResult,
    );
    if (fp) item.flat_params = fp;
  }
}

// unique_match 时顶层也输出一份
const topLevelFlatParams = (matchResult.status === "unique_match" && matchResult.matched_items[0]?.flat_params)
  ? matchResult.matched_items[0].flat_params
  : null;

// ─── 输出 ───

const output = {
  asset_dict: assetDict,
  match_result: matchResult,
  carrier_result: carrierResult,
  ...(topLevelFlatParams ? { flat_params: topLevelFlatParams } : {}),
};
console.log(JSON.stringify(output, null, 2));

// ═══════════════════════════════════════════════════════════════
// 本脚本专有函数
// ═══════════════════════════════════════════════════════════════

// ─── 资产匹配函数 ───

function performAssetMatch(assetDict, matchHint) {
  if (!matchHint || (!matchHint.asset_id && !matchHint.asset_name)) {
    return { status: "no_hint" };
  }

  const hintId = matchHint.asset_id != null ? String(matchHint.asset_id).trim() : null;
  const hintName = matchHint.asset_name != null ? String(matchHint.asset_name).trim() : null;

  const allMatches = [];

  for (const [comboKey, entry] of Object.entries(assetDict)) {
    if (!entry.assets || !Array.isArray(entry.assets) || entry.assets.length === 0) continue;

    for (const asset of entry.assets) {
      let matchType = null;

      // 优先级 1: ID 精确匹配
      if (hintId) {
        const idFields = [
          asset.marketing_asset_id,
          asset.marketing_asset_outer_id,
          asset.product_outer_id,
        ].filter(Boolean);

        if (idFields.some(f => String(f) === String(hintId))) {
          matchType = "id_exact";
        }
      }

      // 优先级 2: 名称完全匹配
      if (!matchType && hintName) {
        const nameFields = [asset.name, asset.asset_name, asset.description, asset.product_name].filter(Boolean);
        if (nameFields.some(n => n === hintName)) {
          matchType = "name_exact";
        }
      }

      // 优先级 3: 名称包含匹配
      if (!matchType && hintName) {
        const nameFields = [asset.name, asset.asset_name, asset.description, asset.product_name].filter(Boolean);
        const lowerHint = hintName.toLowerCase();
        if (nameFields.some(n => {
          const lowerN = n.toLowerCase();
          return lowerN.includes(lowerHint) || lowerHint.includes(lowerN);
        })) {
          matchType = "name_contains";
        }
      }

      if (matchType) {
        allMatches.push({
          combination_key: comboKey,
          combination: entry.combination,
          asset_type: entry.asset_type,
          asset,
          match_type: matchType,
        });
      }
    }
  }

  // 按优先级筛选
  const priorityOrder = ["id_exact", "name_exact", "name_contains"];
  let bestMatches = [];
  for (const priority of priorityOrder) {
    bestMatches = allMatches.filter(m => m.match_type === priority);
    if (bestMatches.length > 0) break;
  }

  if (bestMatches.length === 0) {
    return { status: "no_match", match_type: null, matched_items: [] };
  }

  if (bestMatches.length === 1) {
    return {
      status: "unique_match",
      match_type: bestMatches[0].match_type,
      matched_items: bestMatches,
    };
  }

  // 多条命中：区分"同一资产在多个 combination"和"多个不同资产"
  const uniqueAssetIds = new Set(bestMatches.map(m => {
    return m.asset.marketing_asset_id
      || m.asset.marketing_asset_outer_id
      || m.asset.product_outer_id
      || m.asset.name;
  }));

  if (uniqueAssetIds.size === 1) {
    return {
      status: "multiple_match",
      match_type: bestMatches[0].match_type,
      matched_items: bestMatches,
    };
  }

  return {
    status: "name_multiple_match",
    match_type: bestMatches[0].match_type,
    matched_items: bestMatches,
  };
}

// ─── 载体查询主函数（by-rules 专用） ───

async function fetchCarrierIfNeeded(accountId, matchResult, carrierHint) {
  // 只在资产匹配成功时才查载体
  if (matchResult.status !== "unique_match" && matchResult.status !== "multiple_match") {
    return { status: "skipped", reason: "asset_match_not_successful" };
  }

  const matchedItem = matchResult.matched_items[0];
  const carrierType = matchedItem.combination.marketing_carrier_type;

  // 不需要载体 ID 的类型
  if (CARRIER_NOT_NEEDED.has(carrierType)) {
    return { status: "not_needed", reason: `carrier_type=${carrierType} 不需要 carrier_id` };
  }

  // ONEID 类 / 小游戏类 / 门店类资产已经包含 carrier_id
  const targetType = matchedItem.combination.marketing_target_type;
  if (isCarrierNotNeeded(targetType)) {
    return {
      status: "not_needed",
      reason: "ONEID/视频号/门店类资产不需要额外查询载体",
      carrier_from_asset: matchedItem.asset.marketing_carrier_id || matchedItem.asset.marketing_asset_outer_id || null,
    };
  }

  // 载体 ID 短路
  const hintId = carrierHint?.carrier_id != null ? String(carrierHint.carrier_id).trim() : null;
  if (hintId) {
    return {
      status: "found",
      carriers: [{ carrier_id: hintId, carrier_name: carrierHint.carrier_name || "" }],
      matched_carrier: { carrier_id: hintId, carrier_name: carrierHint.carrier_name || "" },
      shortcut: true,
      reason: "用户已提供明确载体 ID，无需查询 API",
    };
  }

  // 查询载体
  try {
    const result = await queryAndMatchCarriers(accountId, carrierType, carrierHint);

    // 行业资产场景：明确提示 carrier_id 与 marketing_asset_id 的区别
    if (matchedItem.asset_type === "INDUSTRY" && result.matched_carrier && matchedItem.asset.marketing_asset_id) {
      result.note = `⚠️ 重要区分：carrier_id(${result.matched_carrier.carrier_id}) 用于 marketing_carrier_detail.marketing_carrier_id；asset_id(${matchedItem.asset.marketing_asset_id}) 用于 marketing_asset_id。两者含义不同，切勿混淆！此场景使用 marketing_asset_id，不使用 marketing_asset_outer_spec。`;
    }

    return result;
  } catch (err) {
    return { status: "match_failed", reason: `载体查询失败: ${err.message}` };
  }
}
