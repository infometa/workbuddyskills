/**
 * get-available-marketing-assets.mjs — 通用资产分页查询工具
 *
 * 封装 available_marketing_assets/get 的分页查询逻辑，
 * 支持 hint（asset_id / asset_name）提前退出翻页。
 */

import { callApi } from "tencentads-cli";

/**
 * 分页查询 available_marketing_assets/get
 *
 * @param {string|number} accountId - 广告主账号
 * @param {string} targetType - MARKETING_TARGET_TYPE_*
 * @param {object} [opts] - 可选参数
 * @param {object} [opts.hint] - { asset_id, asset_name }，命中时提前退出翻页
 * @returns {{ list: Array, error?: object }}
 */
export async function callAvailableMarketingAssets(accountId, targetType, opts = {}) {
  const { hint } = opts;
  const hintId = hint?.asset_id != null ? String(hint.asset_id).trim() : null;
  const hintName = hint?.asset_name != null ? String(hint.asset_name).trim() : null;

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
      if (allAssets.length === 0 && !hint) {
        return { list: [], error: result.error };
      }
      break;
    }

    const list = result.data?.data?.list ?? result.data?.list ?? [];
    if (list.length === 0) break;

    allAssets = allAssets.concat(list);

    // hint 提前退出
    if (hintId || hintName) {
      const found = list.some((item) => {
        if (hintId) {
          const idFields = [
            item.marketing_asset_id,
            item.marketing_asset_outer_id,
            item.marketing_asset_outer_spec?.marketing_asset_outer_id,
            item.product_outer_id,
          ].filter(Boolean);
          if (idFields.some(f => String(f) === String(hintId))) return true;
        }
        if (hintName) {
          const nameFields = [item.marketing_target_name, item.asset_name, item.product_name].filter(Boolean);
          const lowerHint = hintName.toLowerCase();
          if (nameFields.some(n => {
            const lowerN = n.toLowerCase();
            return n === hintName || lowerN.includes(lowerHint) || lowerHint.includes(lowerN);
          })) return true;
        }
        return false;
      });
      if (found) break;
    }

    // 检查是否还有下一页
    const pageInfo = result.data?.data?.page_info ?? result.data?.page_info ?? {};
    const totalPage = pageInfo.total_page ?? 1;
    const totalNumber = pageInfo.total_number ?? allAssets.length;
    if (currentPage >= totalPage || allAssets.length >= totalNumber) break;

    currentPage++;
  }

  return { list: allAssets };
}
