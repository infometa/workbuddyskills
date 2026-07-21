#!/usr/bin/env node
/**
 * get-assets.mjs — 获取推广产品 + 营销载体
 *
 * 根据 marketing_target_type 自动判断分类（ONEID / 商品库 / 行业产品库 / 视频号直播），
 * 调用对应 API，返回统一格式的可选资产列表。
 *
 * 分类路由:
 * - 视频号直播类 (CHANNELS_LIVE_TYPES) → /v3.0/bff_promoted_objects/get
 *   - 直播预约场次补充查询 → /bff/mktapi/proxy 代理 channels_getlivenoticeinfo/get
 * - ONEID 类 (ONEID_TYPES) → /v3.0/available_marketing_assets/get
 * - 商品库类 (CATALOG_TYPES) → /v3.0/asset_catalog/get + /v3.0/asset_product/get
 * - 行业产品库类 (其他) → /v3.0/available_marketing_assets/get
 *
 * ONEID 和行业产品库走同一个接口，但输出格式不同。
 *
 * 入参: '{"account_id":"<ID>","marketing_target_type":"<...>"}'
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
 *       "flat_params": {
 *         "asset_id": "wx1234567890",
 *         "carrier_id": "wx1234567890",
 *         "asset_name": "以闪亮之名",
 *         "carrier_name": "以闪亮之名"
 *       }
 *     }
 *   ]
 * }
 *
 * 输出 (商品库类):
 * {
 *   "asset_type": "CATALOG",
 *   "assets": [
 *     {
 *       "catalog_id": "12345",
 *       "product_outer_id": "SKU001",
 *       "name": "商品名",
 *       "flat_params": {
 *         "asset_id": "12345",
 *         "catalog_id": "12345",
 *         "asset_sub_id": "SKU001"
 *       }
 *     }
 *   ]
 * }
 *
 * 输出 (行业产品库类):
 * {
 *   "asset_type": "INDUSTRY",
 *   "assets": [
 *     {
 *       "marketing_asset_id": "67890",
 *       "name": "资产名",
 *       "flat_params": {
 *         "asset_id": "67890"
 *       }
 *     }
 *   ]
 * }
 *
 * flat_params 说明：
 * 每条 asset 挂载 flat_params 对象，key 与 create-adgroup.mjs 方式一入参完全对齐（共 7 个）：
 *   asset_id       — 推广产品 ID（ONEID 的 outer_id / 行业的 asset_id / 商品库的 catalog_id）
 *   carrier_id     — 载体 ID（ONEID 类和视频号直播类 = outer_id；行业/商品库类不含此字段，若需要载体需从用户处获取）
 *   catalog_id     — 商品库场景的 catalog_id
 *   asset_sub_id   — 子标识（商品库的 product_outer_id；直播预约需 Agent 选择 notice_id 后补入）
 *   asset_name     — 资产名称（ONEID 类自动填入；create-adgroup.mjs 写入 marketing_asset_outer_name）
 *   carrier_name   — 载体名称（ONEID 类自动填入；create-adgroup.mjs 内部仅 QUICK_APP/PC_GAME 生效）
 *   sub_carrier_id — 载体子标识（直播预约需 Agent 选择 notice_id 后补入 → marketing_sub_carrier_id）
 * Agent 选完 asset 后，将 flat_params 直接透传（展开）给 create-adgroup.mjs 即可，
 * create-adgroup.mjs 会根据 marketing_target_type 自动组装 API 所需的嵌套结构。
 * 注意：asset_name / carrier_name 多传无害，create-adgroup.mjs 内部会按类型安全过滤。
 *
 * 输出 (视频号直播预约类，额外包含 live_notices):
 * {
 *   "asset_type": "ONEID",
 *   "assets": [...],
 *   "live_notices": {             // 每个视频号下的直播预约场次
 *     "<finder_username>": [
 *       {
 *         "notice_id": "finderlivenotice-xxx",  // = marketing_sub_carrier_id / marketing_asset_outer_sub_id
 *         "introduction": "直播预约标题",
 *         "start_time": 1234567890,
 *         "status_wording": "预约中",
 *         "nickname": "视频号昵称"
 *       }
 *     ]
 *   }
 * }
 */

import { callApi } from "tencentads-cli";
import { fetchAndroidChannelPackages } from "./get-android-packages.mjs";

// ─── 分类定义（统一在此维护，get-assets-by-rules.mjs 通过 import 复用） ───

// ONEID 类：返回 marketing_asset_outer_id（如微信小游戏 AppID、视频号 ID 等）
// create-adgroup.mjs 也 import 此定义，确保分类一致。
export const ONEID_TYPES = new Set([
  "MARKETING_TARGET_TYPE_APP_ANDROID",
  "MARKETING_TARGET_TYPE_APP_IOS",
  "MARKETING_TARGET_TYPE_APP_HARMONY",
  "MARKETING_TARGET_TYPE_APP_QUICK_APP",
  "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
  "MARKETING_TARGET_TYPE_MINI_PROGRAM_WECHAT",
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS",
  "MARKETING_TARGET_TYPE_WECHAT_OFFICIAL_ACCOUNT",
  "MARKETING_TARGET_TYPE_MINI_GAME_QQ",
  "MARKETING_TARGET_TYPE_PC_GAME",
  "MARKETING_TARGET_TYPE_LOCAL_STORE",
  "MARKETING_TARGET_TYPE_LOCAL_STORE_PACKAGE",
  "MARKETING_TARGET_TYPE_WECHAT_WORK",
]);

//  视频号直播类：通过 /v3.0/bff_promoted_objects/get 查询视频号列表
export const CHANNELS_LIVE_TYPES = new Set([
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE",
  "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE_RESERVATION",
]);

// 商品库类：需要两步查询 (asset_catalog/get → asset_product/get)
// create-adgroup.mjs 也 import 此定义，确保分类一致。
export const CATALOG_TYPES = new Set([
  "MARKETING_TARGET_TYPE_CONSUMER_PRODUCT",
  "MARKETING_TARGET_TYPE_COMMODITY_SET",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
  "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT_SET",
  "MARKETING_TARGET_TYPE_WECHAT_STORE",
]);

// ─── flat_params 构建（与 create-adgroup.mjs 扁平参数对齐） ───
// 每条 asset 挂载 flat_params，Agent 选完后直接透传给 create-adgroup.mjs，
// 消除 SKILL 层手动组装字段的不确定性。
//
// flat_params 的 key 与 create-adgroup.mjs 方式一的入参完全一致（共 7 个）：
//   asset_id       — 推广产品 ID（ONEID 的 outer_id / 行业的 asset_id / 商品库的 catalog_id）
//   carrier_id     — 载体 ID（ONEID 类和视频号直播类 = outer_id；行业/商品库类不含此字段，若需要载体需从用户处获取）
//   catalog_id     — 商品库场景的 catalog_id
//   asset_sub_id   — 子标识（商品库的 product_outer_id；直播预约需 Agent 从 live_notices 选择后补入 notice_id）
//   asset_name     — 资产名称 → create-adgroup.mjs 写入 marketing_asset_outer_name（APP_QUICK_APP / PC_GAME）
//   sub_carrier_id — 载体子标识 → create-adgroup.mjs 写入 marketing_sub_carrier_id（如直播预约的 notice_id）
//   carrier_name   — 载体名称 → create-adgroup.mjs 写入 marketing_carrier_name（仅 QUICK_APP / PC_GAME 允许）

function buildFlatParams(asset, assetType, targetType) {
  const params = {};

  if (assetType === "INDUSTRY") {
    // 行业产品库：asset_id = marketing_asset_id
    if (asset.marketing_asset_id) {
      params.asset_id = String(asset.marketing_asset_id);
    }
  } else if (assetType === "ONEID") {
    // ONEID 类：asset_id = outer_id, carrier_id = outer_id（同值）
    if (asset.marketing_asset_outer_id) {
      params.asset_id = String(asset.marketing_asset_outer_id);
    }
    if (asset.marketing_carrier_id) {
      params.carrier_id = String(asset.marketing_carrier_id);
    }
    // asset_name：APP_QUICK_APP / PC_GAME 需要，其他类型 create-adgroup.mjs 会忽略，多传无害
    if (asset.name) {
      params.asset_name = String(asset.name);
    }
    // carrier_name：仅 APP_QUICK_APP / PC_GAME 的载体类型需要，create-adgroup.mjs 内部做安全过滤
    if (asset.name) {
      params.carrier_name = String(asset.name);
    }
  } else if (assetType === "CATALOG") {
    // 商品库类：asset_id = catalog_id, catalog_id 也单独给, asset_sub_id = product_outer_id
    if (asset.catalog_id) {
      params.asset_id = String(asset.catalog_id);
      params.catalog_id = String(asset.catalog_id);
    }
    if (asset.product_outer_id) {
      params.asset_sub_id = String(asset.product_outer_id);
    }
  }

  // sub_carrier_id：直播预约场景需要 notice_id，但需 Agent 选择后补入，此处不填
  // （Agent 从 live_notices 选定 notice_id 后，手动追加 flat_params.sub_carrier_id = notice_id
  //   以及 flat_params.asset_sub_id = notice_id）

  // 清理 undefined 和空字符串
  for (const k of Object.keys(params)) {
    if (params[k] === undefined || params[k] === "") delete params[k];
  }

  return Object.keys(params).length > 0 ? params : undefined;
}

// ─── 核心路由函数（供 CLI 和外部 import 共用） ───
// 路由完全由 marketing_target_type 决定，与 marketing_carrier_type 无关。
// marketing_carrier_type=JUMP_PAGE 只意味着不需要营销载体信息（marketing_carrier_detail），
// 但推广资产（marketing_asset_outer_spec）仍需正常查询。

export async function fetchAssetsForTargetType(accountId, targetType) {
  if (CHANNELS_LIVE_TYPES.has(targetType)) {
    return await fetchChannelsLiveAssets(accountId, targetType);
  } else if (ONEID_TYPES.has(targetType)) {
    return await fetchOneidAssets(accountId, targetType);
  } else if (CATALOG_TYPES.has(targetType)) {
    return await fetchCatalogAssets(accountId, targetType);
  } else {
    return await fetchIndustryAssets(accountId, targetType);
  }
}

// ─── CLI 入口（仅直接执行时运行，被 import 时不执行） ───

const isMainScript = process.argv[1] && import.meta.url === `file://${process.argv[1]}`;
if (isMainScript) {
  let input;
  try {
    const raw = process.argv[2];
    if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
    input = JSON.parse(raw);
  } catch (err) {
    console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` }));
    process.exit(1);
  }

  const { account_id, marketing_target_type } = input;

  if (!account_id) {
    console.log(JSON.stringify({ error: "missing required field: account_id" }));
    process.exit(1);
  }
  if (!marketing_target_type) {
    console.log(JSON.stringify({ error: "missing required field: marketing_target_type" }));
    process.exit(1);
  }

  const result = await fetchAssetsForTargetType(account_id, marketing_target_type);
  console.log(JSON.stringify(result, null, 2));
}

// ─── 视频号直播类资产查询（通过 bff_promoted_objects/get） ───
// 对于直播预约类 (LIVE_RESERVATION)，额外调用 channels_livenoticeinfo/get
// 获取每个视频号下的直播预约场次 (notice_id)，
// notice_id 即为 marketing_sub_carrier_id / marketing_asset_outer_sub_id。

async function fetchChannelsLiveAssets(accountId, targetType) {
  // 视频号直播/直播预约 → promoted_object_type 对应 WECHAT_CHANNELS，枚举 value = 51
  // 注意：bff_promoted_objects/get 的 filtering.values 需要传枚举 value，而不是枚举名。
  const promotedObjectTypeValue = "51";

  let allList = [];
  let currentPage = 1;
  const pageSize = 100;

  while (true) {
    const result = await callApi({
      method: "GET",
      path: "/v3.0/bff_promoted_objects/get",
      accountId: String(accountId),
      params: {
        account_id: parseInt(accountId, 10),
        filtering: [
          { field: "promoted_object_type", operator: "EQUALS", values: [promotedObjectTypeValue] },
        ],
        page: currentPage,
        page_size: pageSize,
        fields: [
          "promoted_object_type",
          "promoted_object_id",
          "promoted_object_name",
          "promoted_object_spec",
        ],
      },
    });

    if (!result.success) {
      if (allList.length === 0) {
        return { asset_type: "ONEID", assets: [], error: result.error?.message || "API 调用失败" };
      }
      break;
    }

    const data = result.data?.data ?? result.data ?? {};
    const list = data.list ?? [];
    if (list.length === 0) break;

    allList = allList.concat(list);

    // 检查是否还有下一页
    const pageInfo = data.page_info ?? {};
    const totalNumber = pageInfo.total_number ?? allList.length;
    if (allList.length >= totalNumber) break;

    currentPage++;
  }

  const assets = allList.map((item) => {
    const outerId = item.promoted_object_id ?? "";
    const asset = {
      marketing_asset_outer_id: outerId,
      marketing_carrier_id: outerId,
      name: item.promoted_object_name ?? "",
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    };
    // flat_params：与 create-adgroup.mjs 扁平参数对齐，Agent 选完后直接透传
    asset.flat_params = buildFlatParams(asset, "ONEID", targetType);
    return asset;
  });

  // ── 直播预约类：额外获取每个视频号下的直播预约场次 ──
  const isLiveReservation = targetType === "MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE_RESERVATION";
  let liveNotices = null;

  if (isLiveReservation && allList.length > 0) {
    liveNotices = {};
    for (const item of allList) {
      const channelsId = item.promoted_object_id ?? "";
      if (!channelsId) continue;

      // channels_livenoticeinfo/get — 直接调 v3.0 API
      // finder_username 和 wechat_channels_account_id 不可同时传，根据 ID 格式二选一：
      // - @finder 结尾 → 加密前格式，传 finder_username
      // - export 开头 → 加密后格式，传 wechat_channels_account_id
      const isExport = channelsId.startsWith("export");
      const noticeParams = {
        account_id: parseInt(accountId, 10),
        ...(isExport
          ? { wechat_channels_account_id: channelsId }
          : { finder_username: channelsId }),
      };
      const noticeResult = await callApi({
        method: "GET",
        path: "/v3.0/channels_livenoticeinfo/get",
        accountId: String(accountId),
        params: noticeParams,
      });

      if (!noticeResult.success) {
        // 单个视频号获取预约失败不中断整体流程
        continue;
      }

      const noticeData = noticeResult.data?.data ?? noticeResult.data ?? {};
      const noticeList = noticeData.live_notice_record_list ?? [];

      if (noticeList.length > 0) {
        liveNotices[channelsId] = noticeList.map((notice) => ({
          notice_id: notice.notice_id ?? "",
          introduction: notice.introduction ?? "",
          start_time: notice.start_time ?? 0,
          status_wording: notice.status_wording ?? "",
          nickname: notice.nickname ?? "",
        }));
      }
    }
  }

  const output = { asset_type: "ONEID", assets };
  if (liveNotices && Object.keys(liveNotices).length > 0) {
    output.live_notices = liveNotices;
  }

  return output;
}

// ─── ONEID 类资产查询 ───

async function fetchOneidAssets(accountId, targetType) {
  const list = await callAvailableMarketingAssets(accountId, targetType);

  const assets = list.map((item) => {
    const outerId = item.marketing_asset_outer_id ?? item.marketing_asset_outer_spec?.marketing_asset_outer_id ?? "";
    const asset = {
      marketing_asset_outer_id: outerId,
      marketing_carrier_id: outerId,
      name: item.marketing_target_name ?? item.asset_name ?? "",
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    };
    // flat_params：与 create-adgroup.mjs 扁平参数对齐，Agent 选完后直接透传
    asset.flat_params = buildFlatParams(asset, "ONEID", targetType);
    return asset;
  });

  // 对 APP_ANDROID 补充渠道包查询
  if (targetType === "MARKETING_TARGET_TYPE_APP_ANDROID" && assets.length > 0) {
    for (const asset of assets) {
      const appId = asset.marketing_asset_outer_id;
      if (appId) {
        asset.channel_packages = await fetchAndroidChannelPackages(accountId, appId);
      }
    }
  }

  return { asset_type: "ONEID", assets };
}

// ─── 行业产品库类资产查询 ───

async function fetchIndustryAssets(accountId, targetType) {
  const list = await callAvailableMarketingAssets(accountId, targetType);

  const assets = list.map((item) => {
    const asset = {
      marketing_asset_id: String(item.marketing_asset_id ?? ""),
      name: item.marketing_target_name ?? item.asset_name ?? "",
      type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
    };
    // flat_params：与 create-adgroup.mjs 扁平参数对齐，Agent 选完后直接透传
    asset.flat_params = buildFlatParams(asset, "INDUSTRY", targetType);
    return asset;
  });

  return { asset_type: "INDUSTRY", assets };
}

// ─── 通用资产接口（ONEID 和行业产品库共用） ───

export async function callAvailableMarketingAssets(accountId, targetType) {
  let allAssets = [];
  let currentPage = 1;
  const pageSize = 100;

  while (true) {
    const result = await callApi({
      method: "POST",
      path: "/v3.0/available_marketing_assets/get",
      accountId: String(accountId),
      body: {
        account_id: parseInt(accountId, 10),
        marketing_target_type: targetType,
        page: currentPage,
        page_size: pageSize,
      },
    });

    if (!result.success) {
      // 第一页就失败则返回空
      if (allAssets.length === 0) return [];
      break;
    }

    const list = result.data?.data?.list ?? result.data?.list ?? [];
    if (list.length === 0) break;

    allAssets = allAssets.concat(list);

    // 检查是否还有下一页
    const pageInfo = result.data?.data?.page_info ?? result.data?.page_info ?? {};
    const totalPage = pageInfo.total_page ?? 1;
    const totalNumber = pageInfo.total_number ?? allAssets.length;
    if (currentPage >= totalPage || allAssets.length >= totalNumber) break;

    currentPage++;
  }

  return allAssets;
}

// ─── 商品库类资产查询 ───
// 两步流程：
//   步骤 A: asset_catalog/get → 获取商品目录列表 (catalog_id)
//   步骤 B: asset_product/get → 在每个可用目录下获取具体商品 (product_outer_id)

async function fetchCatalogAssets(accountId, targetType) {
  // 根据 marketing_target_type 推断 catalog_type
  const catalogType = targetType === "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT"
    ? "CATALOG_TYPE_CHANNELS_STORE"
    : "CATALOG_TYPE_STANDARD";

  // ── 步骤 A: 获取商品目录列表 ──
  const catalogResult = await callApi({
    method: "GET",
    path: "/v3.0/asset_catalog/get",
    accountId: String(accountId),
    params: {
      account_id: parseInt(accountId, 10),
      page: 1,
      page_size: 50,
      catalog_type: catalogType,
    },
  });

  if (!catalogResult.success) {
    return { asset_type: "CATALOG", assets: [] };
  }

  const catalogs = catalogResult.data?.data?.list ?? catalogResult.data?.list ?? [];

  // 过滤出可用的目录（available_status === 1 或无此字段时全部保留）
  const availableCatalogs = catalogs.filter(
    (c) => c.available_status === undefined || c.available_status === 1
  );

  if (availableCatalogs.length === 0) {
    return { asset_type: "CATALOG", assets: [] };
  }

  // ── 步骤 B: 对每个可用目录，查询商品列表（支持分页） ──
  const assets = [];
  for (const catalog of availableCatalogs) {
    let currentPage = 1;

    while (true) {
      const productResult = await callApi({
        method: "GET",
        path: "/v3.0/asset_product/get",
        accountId: String(accountId),
        params: {
          account_id: parseInt(accountId, 10),
          catalog_id: catalog.catalog_id,
          catalog_type: catalogType,
          page: currentPage,
          page_size: 100,
          filtering: [{ field: "ad_status", operator: "EQUALS", values: ["1"] }],
        },
      });

      if (!productResult.success) break;

      const products = productResult.data?.data?.list ?? productResult.data?.list ?? [];
      if (products.length === 0) break;

      for (const product of products) {
        const asset = {
          catalog_id: String(catalog.catalog_id ?? ""),
          catalog_name: catalog.catalog_name ?? "",
          product_outer_id: String(product.product_outer_id ?? ""),
          product_name: product.product_name ?? "",
          name: product.product_name || catalog.catalog_name || "",
          type: targetType.replace("MARKETING_TARGET_TYPE_", ""),
        };
        // flat_params：与 create-adgroup.mjs 扁平参数对齐，Agent 选完后直接透传
        asset.flat_params = buildFlatParams(asset, "CATALOG", targetType);
        assets.push(asset);
      }

      // 检查是否还有下一页
      const pageInfo = productResult.data?.data?.page_info ?? productResult.data?.page_info ?? {};
      const totalPage = pageInfo.total_page ?? 1;
      if (currentPage >= totalPage) break;

      currentPage++;
    }
  }

  return { asset_type: "CATALOG", assets };
}
