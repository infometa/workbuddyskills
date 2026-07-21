#!/usr/bin/env node
/**
 * get-assets.mjs — 获取推广产品 + 营销载体
 *
 * 根据 marketing_target_type 自动判断分类（ONEID / 商品库 / 行业产品库 / 视频号直播），
 * 调用对应 API，返回统一格式的可选资产列表。
 *
 * 可选：当传入 carrier_hint + product_type 时，自动查询并匹配载体，
 * 返回 carrier_result 字段（与 get-assets-by-rules.mjs 的 carrier_result 格式一致）。
 *
 * 分类路由:
 * - 视频号直播类 (CHANNELS_LIVE_TYPES) → /bff/mktapi/proxy (promoted_objects/get)
 * - ONEID 类 (ONEID_TYPES) → 优先 BFF，回退 /v3.0/available_marketing_assets/get
 *   - 微信小游戏 → BFF (pot=46)，回退 AMA
 *   - 门店 → /v3.0/local_stores/get
 *   - 门店包 → /v3.0/local_store_packages/get
 *   - 企业微信 → /v3.0/wechat_pages_csgroup_auth_info/get
 * - 商品库类 (CATALOG_TYPES) → /v3.0/asset_catalog/get + /v3.0/asset_product/get (或 asset_commodity_set_list/get)
 * - 行业产品库类 (其他) → /v3.0/available_marketing_assets/get
 *
 * ONEID 和行业产品库走同一个接口，但输出格式不同。
 *
 * 入参: '{"account_id":"<ID>","marketing_target_type":"<...>","marketing_carrier_type":"<...>","marketing_goal":"<...>","product_type":<number>,"carrier_hint":{"carrier_id":"...","carrier_name":"..."},"asset_hint":{"asset_id":"...","asset_name":"..."}}'
 *   account_id, marketing_target_type 必填
 *   marketing_carrier_type, marketing_goal 可选
 *   product_type 可选，载体查询时使用（来自 get-rules.mjs 返回的 combination.product_type）
 *   carrier_hint 可选，用于载体名称/ID匹配，至少包含 carrier_id 或 carrier_name 之一
 *   asset_hint 可选，用户给了明确的资产 ID/名称时传入。ONEID 类传 asset_id 时脚本自动短路（不调 API）
 *
 * 输出 (ONEID 类):
 * {
 *   "asset_type": "ONEID",
 *   "assets": [
 *     {
 *       "marketing_asset_outer_id": "wx1234567890",
 *       "marketing_carrier_id": "wx1234567890",
 *       "name": "以闪亮之名",
 *       "type": "WECHAT_MINI_GAME",
 *       "flat_params": {                        // ← 每条 asset 都带，Agent 选完后直接取对应项的 flat_params 透传
 *         "asset_id": "wx1234567890",
 *         "carrier_id": "wx1234567890"
 *       }
 *     }
 *   ],
 *   "flat_params": { ... },                    // ← assets 恰好 1 条时顶层也输出（= assets[0].flat_params）
 *   "carrier_result": {                    // 仅当传入 carrier_hint 或 product_type 时返回
 *     "status": "found" | "not_needed" | "no_carriers" | "match_failed" | "skipped",
 *     "carriers": [ { "carrier_id": "417200582", "carrier_name": "唯品会" } ],
 *     "matched_carrier": { "carrier_id": "417200582", "carrier_name": "唯品会" }
 *   }
 * }
 *
 * 输出 (视频号直播预约类，额外包含 live_notices):
 * {
 *   "asset_type": "ONEID",
 *   "assets": [ ... ],           // 视频号账号列表
 *   "live_notices": {             // 每个视频号下的直播预约场次
 *     "<finder_username>": [
 *       {
 *         "notice_id": "finderlivenotice-...",
 *         "introduction": "直播简介",
 *         "start_time": 1774785600,
 *         "status_wording": "可预约"
 *       }
 *     ]
 *   },
 *   "carrier_result": { ... }
 * }
 *
 * 输出 (商品库类 - CONSUMER_PRODUCT / WECHAT_STORE_PRODUCT):
 * {
 *   "asset_type": "CATALOG",
 *   "assets": [
 *     {
 *       "catalog_id": "12345",
 *       "product_outer_id": "SKU001",
 *       "name": "商品名"
 *     }
 *   ],
 *   "carrier_result": { ... }
 * }
 *
 * 输出 (商品库类 - WECHAT_STORE 微信小店店铺):
 * {
 *   "asset_type": "CATALOG",
 *   "assets": [
 *     {
 *       "catalog_id": "12345",
 *       "catalog_name": "店铺商品库名",
 *       "wechat_store_id": "wx...",
 *       "store_name": "店铺名",
 *       "name": "店铺商品库名",
 *       "type": "WECHAT_STORE"
 *     }
 *   ],
 *   "carrier_result": { ... }
 * }
 *
 * 输出 (商品库类 - COMMODITY_SET 商品集合):
 * {
 *   "asset_type": "CATALOG",
 *   "assets": [
 *     {
 *       "catalog_id": "12345",
 *       "catalog_name": "商品库名",
 *       "commodity_set_id": "67890",
 *       "commodity_set_name": "商品集合名",
 *       "name": "商品集合名",
 *       "type": "COMMODITY_SET"
 *     }
 *   ],
 *   "carrier_result": { ... }
 * }
 *
 * 输出 (行业产品库类):
 * {
 *   "asset_type": "INDUSTRY",
 *   "assets": [
 *     {
 *       "marketing_asset_id": "67890",
 *       "name": "资产名"
 *     }
 *   ],
 *   "carrier_result": { ... },
 *   "flat_params": {                          // ← 仅当 assets 恰好 1 条时输出
 *     "asset_id": "67890",
 *     "carrier_id": "417200582",
 *     "catalog_id": "12345",
 *     "asset_sub_id": "..."
 *   }
 * }
 */

import { callApi } from "tencentads-cli";
import { fetchAndroidChannelPackages } from "./get-android-packages.mjs";

import {
  CARRIER_NOT_NEEDED,
  ALL_ONEID_LIKE_TYPES,
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
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` }));
  process.exit(1);
}

const { account_id, marketing_target_type, marketing_carrier_type, marketing_goal, product_type, carrier_hint, asset_hint } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!marketing_target_type) {
  console.log(JSON.stringify({ error: "missing required field: marketing_target_type" }));
  process.exit(1);
}

// ─── ONEID 短路：用户已给明确资产 ID 时，不调 API 直接返回 ───
// ONEID 类（含视频号直播类、微信小游戏类）的 carrier_id = asset_id = outer_id，
// 后端支持新 ID 自动绑定（BuildMarketingTargetAttrFromOuterID），无需先查询是否已存在。
// 当 Agent 通过 asset_hint.asset_id 传入了用户给的明确资产 ID 时，直接短路返回。
// 如果只传了 asset_hint.asset_name（名称），则不短路，走正常查询后按名称匹配。

if (ALL_ONEID_LIKE_TYPES.has(marketing_target_type) && asset_hint?.asset_id) {
  let assetId = String(asset_hint.asset_id).trim();
  if (assetId) {
    // ── 门店特殊处理：用户可能只给了 poi_id，补全为 "poi_id@account_id" ──
    if (marketing_target_type === "MARKETING_TARGET_TYPE_LOCAL_STORE" && !assetId.includes("@")) {
      assetId = `${assetId}@${account_id}`;
    }

    const shortcutAsset = {
      marketing_asset_outer_id: assetId,
      marketing_carrier_id: assetId,
      name: asset_hint.asset_name || assetId,
      type: marketing_target_type.replace("MARKETING_TARGET_TYPE_", ""),
      flat_params: {
        asset_id: assetId,
        carrier_id: assetId,
      },
    };
    const output = {
      asset_type: "ONEID",
      assets: [shortcutAsset],
      shortcut: true,
      reason: "ONEID 类 + 用户已提供明确资产 ID，无需查询 API",
      carrier_result: { status: "not_needed", reason: "ONEID 类 carrier_id = asset_id" },
      flat_params: shortcutAsset.flat_params,
    };
    console.log(JSON.stringify(output, null, 2));
    process.exit(0);
  }
}

// ─── 查询资产 ───
// 路由完全由 marketing_target_type 决定，与 marketing_carrier_type 无关。
// marketing_carrier_type=JUMP_PAGE 只意味着不需要营销载体信息（marketing_carrier_detail），
// 但推广资产（marketing_asset_outer_spec）仍需正常查询。

const assetResult = await fetchAssetsForTargetType(account_id, marketing_target_type, {
  hint: asset_hint,
  includeLiveNotices: true,    // get-assets.mjs 需要直播预约场次
  enableFallback: true,        // 商品库类启用 CONSUMER↔WECHAT_STORE 自动回退
});

// 如果查询返回了错误且无资产，输出错误并退出
if (assetResult.error && (!assetResult.assets || assetResult.assets.length === 0)) {
  console.log(JSON.stringify({ error: assetResult.error }));
  process.exit(1);
}

// ─── 载体查询（当传入 carrier_hint 或 marketing_carrier_type 时自动执行） ───

const carrierResult = await fetchCarrierResult(
  account_id, marketing_target_type, marketing_carrier_type, carrier_hint
);

// ─── 计算 flat_params ───

const assets = assetResult.assets;
if (Array.isArray(assets)) {
  for (const asset of assets) {
    const fp = buildFlatParams(asset, assetResult.asset_type, carrierResult);
    if (fp) asset.flat_params = fp;
  }

  // 对 APP_ANDROID 补充渠道包查询
  if (marketing_target_type === "MARKETING_TARGET_TYPE_APP_ANDROID" && assets.length > 0) {
    for (const asset of assets) {
      const appId = asset.marketing_asset_outer_id;
      if (appId) {
        asset.channel_packages = await fetchAndroidChannelPackages(account_id, appId);
      }
    }
  }
}

// 1 条时顶层也输出一份，方便直接透传
const topLevelFlatParams = (Array.isArray(assets) && assets.length === 1 && assets[0].flat_params)
  ? assets[0].flat_params
  : null;

// ─── 输出 ───

const output = { ...assetResult };
if (carrierResult) {
  output.carrier_result = carrierResult;
}
if (topLevelFlatParams) {
  output.flat_params = topLevelFlatParams;
}
console.log(JSON.stringify(output, null, 2));

// ─── 载体查询主函数（get-assets.mjs 专用，逻辑与 by-rules 略有不同） ───

async function fetchCarrierResult(accountId, targetType, carrierType, carrierHint) {
  // 没有载体类型信息，跳过
  if (!carrierType) {
    return null;
  }

  // 不需要载体 ID 的类型
  if (CARRIER_NOT_NEEDED.has(carrierType)) {
    return { status: "not_needed", reason: `carrier_type=${carrierType} 不需要 carrier_id` };
  }

  // ONEID 类 / 视频号类 / 小游戏类资产的 carrier_id 已内含，不需要额外查询载体
  if (isCarrierNotNeeded(targetType)) {
    return {
      status: "not_needed",
      reason: "ONEID/视频号/门店类资产不需要额外查询载体",
    };
  }

  // 载体 ID 短路：用户已给明确载体 ID 时，直接返回，不调 API
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

  // 需要额外查询载体（用户只给了名称，或未给任何 hint）
  try {
    return await queryAndMatchCarriers(accountId, carrierType, carrierHint);
  } catch (err) {
    return { status: "match_failed", reason: `载体查询失败: ${err.message}` };
  }
}
