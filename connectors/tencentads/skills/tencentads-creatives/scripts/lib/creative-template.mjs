/**
 * lib/creative-template.mjs — 拉取创意形式原始数据的共享函数
 *
 * 供 get-creative-templates.mjs 和 build-creative-params.mjs 共同使用，
 * 避免重复实现 adgroups/get + creative_template/get 两步拉取逻辑。
 */

import { callApi } from "tencentads-cli";

/**
 * 拉取创意形式原始列表
 *
 * @param {number} accountId - 广告账户 ID（数字）
 * @param {number|string} adgroupId - 广告组 ID
 * @param {object} options - 可选参数
 * @param {number} [options.creative_template_id] - 指定创意形式 ID
 * @param {string} [options.delivery_mode] - 投放模式，默认 DELIVERY_MODE_COMPONENT
 * @param {string} [options.dynamic_creative_type] - 创意类型；指定了 creative_template_id 时默认 DYNAMIC_CREATIVE_TYPE_COMMON，否则默认 DYNAMIC_CREATIVE_TYPE_PROGRAM
 * @param {string} [options.live_promoted_type] - 视频号投放形式
 * @returns {{ tplList: object[], adgroupMeta: object }|null} 原始模板列表及广告组元数据，失败时返回 null
 */
export async function fetchRawCreativeTemplates(accountId, adgroupId, options = {}) {
  // Step 1: 获取广告组四元组
  const adgroupResult = await callApi({
    method: "GET",
    path: "/v3.0/adgroups/get",
    accountId: String(accountId),
    params: {
      account_id: accountId,
      filtering: [{ field: "adgroup_id", operator: "EQUALS", values: [String(adgroupId)] }],
      fields: ["adgroup_id", "marketing_goal", "marketing_sub_goal", "marketing_target_type", "marketing_carrier_type", "smart_delivery_platform", "smart_delivery_goal", "brand_ad_type"],
    },
  });

  if (!adgroupResult.success) return null;

  const adgroupList = adgroupResult.data?.data?.list ?? adgroupResult.data?.list ?? [];
  if (adgroupList.length === 0) return null;

  const adgroupMeta = adgroupList[0];
  const { marketing_goal, marketing_sub_goal, marketing_target_type, marketing_carrier_type, smart_delivery_platform, smart_delivery_goal, brand_ad_type } = adgroupMeta;

  // Step 2: 拉取创意形式
  const tplResult = await callApi({
    method: "GET",
    path: "/v3.0/creative_template/get",
    accountId: String(accountId),
    params: {
      account_id: accountId,
      adgroup_id: adgroupId,
      marketing_goal,
      marketing_sub_goal,
      marketing_target_type,
      marketing_carrier_type,
      ...(smart_delivery_platform ? { smart_delivery_platform } : {}),
      ...(smart_delivery_goal ? { smart_delivery_goal } : {}),
      ...(options.creative_template_id != null ? { creative_template_id: options.creative_template_id } : {}),
      delivery_mode: options.delivery_mode ?? "DELIVERY_MODE_COMPONENT",
      // creative_template_id > 0 时为指定模板（固定创意形式），对应 COMMON；否则为不指定（程序化），对应 PROGRAM
      dynamic_creative_type: options.dynamic_creative_type
        ?? ((options.creative_template_id != null && options.creative_template_id > 0)
          ? "DYNAMIC_CREATIVE_TYPE_COMMON"
          : "DYNAMIC_CREATIVE_TYPE_PROGRAM"),
      use_new_version: true,
      ...(brand_ad_type != null ? { brand_ad_type } : {}),
      ...(options.live_promoted_type != null ? { live_promoted_type: options.live_promoted_type } : {}),
    },
  });

  if (!tplResult.success) return null;

  const tplList = tplResult.data?.data?.list ?? tplResult.data?.list ?? [];
  return { tplList, adgroupMeta };
}
