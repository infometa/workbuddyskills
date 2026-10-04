'use strict';

const RESPONSE_MODES = new Set(['auto', 'direct', 'expert']);

const DIRECT_RESPONSE_SIGNALS = [
  /(?:只|就)(?:做)?(?:简单|快速)?查(?:询|一下)?/,
  /(?:快速|简单)查询/,
  /直接(?:查|查询|展示|列出|给结果)/,
  /(?:不用|不要|无需)(?:做)?(?:分析|解读|推荐|比较)/
];

const EXPERT_RESPONSE_SIGNALS = [
  /综合解读|综合推荐|分析推荐|专家解读|帮我分析|详细分析|给出建议/
];

function normalizeResponseMode(value = 'auto') {
  const mode = String(value || 'auto').trim().toLowerCase();
  if (!RESPONSE_MODES.has(mode)) {
    throw new Error('--response-mode 只能是 auto、direct 或 expert');
  }
  return mode;
}

function inferExplicitResponseMode(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  if (DIRECT_RESPONSE_SIGNALS.some(pattern => pattern.test(text))) return 'direct';
  if (EXPERT_RESPONSE_SIGNALS.some(pattern => pattern.test(text))) return 'expert';
  return '';
}

module.exports = {
  DIRECT_RESPONSE_SIGNALS,
  EXPERT_RESPONSE_SIGNALS,
  RESPONSE_MODES,
  inferExplicitResponseMode,
  normalizeResponseMode
};
