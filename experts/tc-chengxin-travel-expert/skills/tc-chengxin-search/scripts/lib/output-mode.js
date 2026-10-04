#!/usr/bin/env node

/**
 * 根据 channel / surface 解析输出形态（表格 vs 卡片、Markdown 链接 vs 纯文本 URL）。
 * 规则与 SKILL.md、references/output-format.md 一致。
 */

/**
 * @param {object} params
 * @param {string} [params.channel]
 * @param {string} [params.surface]
 * @returns {{ use_table: boolean, use_plain_link: boolean }}
 */
function resolve_output_mode(params) {
  const channel = String(params?.channel ?? '').trim();
  const surface = String(params?.surface ?? '').trim();

  let use_table = false;
  let use_plain_link = false;

  if (channel === 'webchat') {
    use_table = true;
  } else if (
    channel.includes('wechat') ||
    channel.includes('weixin') ||
    channel.includes('微信')
  ) {
    use_plain_link = true;
  } else if (surface === 'mobile') {
    use_table = false;
  }

  if (surface === 'table') {
    use_table = true;
  } else if (surface === 'card') {
    use_table = false;
  }

  return { use_table, use_plain_link };
}

module.exports = {
  resolve_output_mode
};
