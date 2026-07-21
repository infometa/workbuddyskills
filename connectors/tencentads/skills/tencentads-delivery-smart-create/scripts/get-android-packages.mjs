/**
 * get-android-packages.mjs — Android 应用与渠道包查询工具
 *
 * 包含：
 * - fetchAndroidApps: 获取安卓应用列表（含渠道包）
 * - fetchAndroidChannelPackages: 查询 Android App 的渠道包列表
 */

import { callApi } from "tencentads-cli";
import { callAvailableMarketingAssets } from "./get-available-marketing-assets.mjs";

/**
 * 获取安卓应用列表（含渠道包）
 *
 * @param {string|number} accountId - 广告主账号
 * @returns {{ asset_type: "ONEID", assets: Array }}
 */
export async function fetchAndroidApps(accountId) {
  const { list, error } = await callAvailableMarketingAssets(accountId, "MARKETING_TARGET_TYPE_APP_ANDROID");

  if (error && list.length === 0) {
    return { asset_type: "ONEID", assets: [], error: error.message || "API 调用失败" };
  }

  const assets = list.map((item) => ({
    marketing_asset_outer_id: item.marketing_asset_outer_id ?? item.marketing_asset_outer_spec?.marketing_asset_outer_id ?? "",
    marketing_carrier_id: item.marketing_asset_outer_id ?? item.marketing_asset_outer_spec?.marketing_asset_outer_id ?? "",
    name: item.marketing_target_name ?? item.asset_name ?? "",
    type: "APP_ANDROID",
  }));

  // 补充渠道包查询
  for (const asset of assets) {
    const appId = asset.marketing_asset_outer_id;
    if (appId) {
      asset.channel_packages = await fetchAndroidChannelPackages(accountId, appId);
    }
  }

  return { asset_type: "ONEID", assets };
}

/**
 * 查询 Android App 的渠道包列表
 * API: /v3.0/android_channel/get
 *
 * @param {string|number} accountId - 广告主账号
 * @param {string|number} appId - Android 应用 ID
 * @returns {Array<{channel_id: string, channel_name: string}>} 仅返回审核通过的渠道包
 */
export async function fetchAndroidChannelPackages(accountId, appId) {
  if (!appId) return [];

  const result = await callApi({
    method: "GET",
    path: "/v3.0/android_channel/get",
    accountId: String(accountId),
    params: {
      account_id: parseInt(accountId, 10),
      app_id: parseInt(appId, 10),
      page: 1,
      page_size: 100,
      fields: ["channel_id", "channel_name", "system_status"],
    },
  });

  if (!result.success) {
    console.warn(`[WARN] 查询 Android 渠道包失败 appId=${appId}: ${result.error?.message || "unknown"}`);
    return [];
  }

  const data = result.data?.data ?? result.data ?? {};
  const list = data.list ?? [];

  return list
    .filter((pkg) => pkg.system_status === "CHANNEL_PACKAGE_STATUS_PASSED")
    .map((pkg) => ({
      channel_id: String(pkg.channel_id ?? ""),
      channel_name: String(pkg.channel_name ?? ""),
    }));
}

// ═══════════════════════════════════════════════════════════════
// CLI 入口
// ═══════════════════════════════════════════════════════════════

const isMainScript = process.argv[1] && import.meta.url === `file://${process.argv[1]}`;
if (isMainScript) {
  let input;
  try {
    const raw = process.argv[2];
    if (!raw) throw new Error("缺少入参");
    input = JSON.parse(raw);
  } catch (err) {
    console.log(JSON.stringify({ error: `参数解析失败: ${err.message}` }));
    process.exit(1);
  }

  const { type, account_id, app_id } = input;

  if (!account_id) {
    console.log(JSON.stringify({ error: "missing required field: account_id" }));
    process.exit(1);
  }

  if (type === "apps") {
    const result = await fetchAndroidApps(account_id);
    console.log(JSON.stringify(result, null, 2));
  } else if (type === "channels") {
    if (!app_id) {
      console.log(JSON.stringify({ error: "查询渠道包需要 app_id" }));
      process.exit(1);
    }
    const packages = await fetchAndroidChannelPackages(account_id, app_id);
    console.log(JSON.stringify(packages, null, 2));
  } else {
    console.log(JSON.stringify({ error: `未知查询类型: ${type}，支持 apps / channels` }));
    process.exit(1);
  }
}
