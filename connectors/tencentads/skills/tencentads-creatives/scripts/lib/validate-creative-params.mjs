/**
 * validate-creative-params.mjs — 创意参数纯校验（不依赖外部 API）
 *
 * 提供共享校验逻辑，供 create-creative.mjs 守门和 build-creative-params.mjs 复用。
 * 仅包含不需要外部 API 调用的静态校验规则。
 *
 * @param {object} params - 待提交给 API 的最终参数对象
 * @param {object} [options]
 * @param {string[]} [options.requiredFields] - 覆盖默认必填字段列表
 * @returns {{ errors: string[] }}
 */
export function validateCreativeParams(params, options = {}) {
  const errors = [];

  // ── 必填字段校验 ──────────────────────────────────────────────────────────────
  const requiredFields = options.requiredFields ??
    ["account_id", "adgroup_id", "creative_components", "dynamic_creative_name", "dynamic_creative_type"];
  for (const field of requiredFields) {
    if (params[field] == null || params[field] === "") {
      errors.push(`missing required field: ${field}`);
    }
  }

  // ── dynamic_creative_name 等宽字符长度校验 ──────────────────────────────────────
  // API 限制：最大 60 等宽字符（1个中文/全角=1，1个英文/半角=0.5）
  const name = params.dynamic_creative_name;
  if (typeof name === 'string' && name !== '') {
    const CREATIVE_NAME_MAX_WIDTH = 60;
    let width = 0;
    for (const ch of name) {
      const code = ch.codePointAt(0);
      // ASCII 可打印字符（U+0020-U+007E）算 0.5，其余（中文、全角等）算 1
      width += (code >= 0x20 && code <= 0x7E) ? 0.5 : 1;
    }
    if (width > CREATIVE_NAME_MAX_WIDTH) {
      errors.push(
        `dynamic_creative_name 超过上限（${width} > ${CREATIVE_NAME_MAX_WIDTH} 等宽字符），请缩短名称`
      );
    }
  }

  // ── 监测链接长度校验 ───────────────────────────────────────────────────────────
  const TRACKING_URL_MAX_LENGTH = 1024;
  for (const field of ['impression_tracking_url', 'click_tracking_url', 'page_track_url']) {
    const val = params[field];
    if (val != null && val !== '') {
      if (typeof val !== 'string') {
        errors.push(`${field} 必须为字符串`);
      } else if (val.length > TRACKING_URL_MAX_LENGTH) {
        errors.push(`${field} 长度超过上限（${val.length} > ${TRACKING_URL_MAX_LENGTH}），请缩短链接`);
      }
    }
  }

  // ── 程序化创意参数校验 ─────────────────────────────────────────────────────────
  if (params.program_creative_info != null) {
    errors.push(
      'program_creative_info 需要根据当前选中的素材动态生成，当前不支持用户直接传入。' +
      '如需使用程序化创意，请开启 auto_derived_program_creative_switch，由系统自动处理'
    );
  }

  // ── 版位校验模式枚举值校验 ─────────────────────────────────────────────────────
  if (params.site_set_validate_model != null) {
    const validModels = ['SITE_SET_VALIDATE_MODEL_STRICT'];
    if (!validModels.includes(params.site_set_validate_model)) {
      errors.push(`site_set_validate_model 枚举值不合法，可选值：${validModels.join(', ')}`);
    }
  }

  // ── APP 类落地页必填字段校验 ────────────────────────────────────────────────────
  const components = params.creative_components;
  if (components && typeof components === 'object') {
    const JUMP_INFO_COMP_TYPES = ['main_jump_info', 'action_button', 'mini_card_link'];
    for (const compType of JUMP_INFO_COMP_TYPES) {
      const entries = components[compType];
      if (!Array.isArray(entries)) continue;
      for (const entry of entries) {
        const ji = entry.value?.jump_info;
        if (!ji?.page_type) continue;
        const spec = ji.page_spec;
        switch (ji.page_type) {
          case 'PAGE_TYPE_IOS_APP':
            if (!spec?.ios_app_spec?.ios_app_id) {
              errors.push(`${compType}: PAGE_TYPE_IOS_APP 缺少 ios_app_spec.ios_app_id，请补充 iOS 应用 ID`);
            }
            break;
          case 'PAGE_TYPE_ANDROID_APP':
            if (!spec?.android_app_spec?.android_app_id) {
              errors.push(`${compType}: PAGE_TYPE_ANDROID_APP 缺少 android_app_spec.android_app_id，请补充 Android 应用 ID`);
            }
            break;
          case 'PAGE_TYPE_APP_DEEP_LINK':
            if (!spec?.app_deep_link_spec) {
              errors.push(`${compType}: PAGE_TYPE_APP_DEEP_LINK 缺少 app_deep_link_spec，请提供完整的 Deep Link 参数`);
            } else {
              const dls = spec.app_deep_link_spec;
              if (!dls.android_deep_link_url && !dls.ios_deep_link_url && !dls.universal_link_url) {
                errors.push(
                  `${compType}: PAGE_TYPE_APP_DEEP_LINK 的 app_deep_link_spec 中至少需要一个链接` +
                  `（android_deep_link_url / ios_deep_link_url / universal_link_url）`
                );
              }
            }
            break;
          case 'PAGE_TYPE_APP_MARKET':
            if (!spec?.app_market_spec?.android_app_id) {
              errors.push(`${compType}: PAGE_TYPE_APP_MARKET 缺少 app_market_spec.android_app_id，请补充应用市场 ID`);
            }
            break;
        }
      }
    }
  }

  return { errors };
}
