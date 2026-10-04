'use strict';

const fs = require('fs');
const path = require('path');
const { withArtifactDelivery } = require('./run-query-with-analysis');
const md = value => String(value == null ? '' : value).replace(/[\r\n]+/g, ' ').replace(/([\\`*_[\]<>|])/g, '\\$1');

function bookingLinks(item) {
  return [['PC 端预订', item.links?.pcUrl], ['手机打开', item.links?.mobileUrl]]
    .filter(([, url]) => /^https?:\/\/[^\s<>]+$/i.test(url || ''))
    // A literal pipe splits a Markdown table cell even inside a link.
    .map(([label, url]) => [label, url.replace(/\|/g, '%7C')])
    .map(([label, url]) => `[${label}](${/[()]/.test(url) ? `<${url}>` : url})`).join(' · ');
}

function resourceFacts(item) {
  const facts = [item.route, item.date, item.time, item.duration, item.score, item.address].filter(Boolean);
  if (item.raw?.arrDate && item.raw?.depDate && item.raw.arrDate !== item.raw.depDate) facts.push(`${item.raw.arrDate}抵达`);
  const details = (item.details || []).filter(d => /席别|票价|距离|参照|星级/.test(d.label) && d.value && d.value.length <= 120);
  details.forEach(d => facts.push(`${d.label}：${d.value}`));
  return facts;
}

function recommendationTable(cards) {
  if (!cards.length) return [];
  return ['| 推荐 | 资源 | 展示价 | 关键信息 | 选择理由 | 预订 |',
    '| --- | --- | --- | --- | --- | --- |',
    ...cards.map(({ resource: item, reason }, i) => {
      // Resolve actions from the selected resource, never from model-written text
      // or a name lookup (different resources may have the same title).
      const cells = [String(i + 1), md(item.title), item.price ? `${md(item.price)}起` : '未返回',
        md(resourceFacts(item).join(' · ')) || '—', md(reason) || '—',
        bookingLinks(item) || '未返回预订链接'];
      return `| ${cells.join(' | ')} |`;
    }), ''];
}

function directResultTable(items) {
  if (!items.length) return [];
  return ['| 序号 | 资源 | 展示价 | 关键信息 | 预订 |',
    '| --- | --- | --- | --- | --- |',
    ...items.map((item, index) => {
      const cells = [String(index + 1), md(item.title), item.price ? `${md(item.price)}起` : '未返回',
        md(resourceFacts(item).join(' · ')) || '—', bookingLinks(item) || '未返回预订链接'];
      return `| ${cells.join(' | ')} |`;
    }), ''];
}

function followUpGuidance(items) {
  const types = new Set((items || []).map(item => item && item.type).filter(Boolean));
  const allTransport = types.size > 0 && [...types].every(type => ['flight', 'train', 'bus'].includes(type));
  let examples;
  if (types.size === 1 && types.has('flight')) {
    examples = ['优先便宜', '只看直飞', '最早到达', '更看重行李额度'];
  } else if (types.size === 1 && types.has('train')) {
    examples = ['优先便宜', '尽量少换乘', '最早到达', '想坐卧铺'];
  } else if (types.size === 1 && types.has('bus')) {
    examples = ['优先便宜', '最早出发', '最晚出发', '耗时更短'];
  } else if (types.size === 1 && types.has('hotel')) {
    examples = ['离目标地点近', '价格低', '评分高', '需要含早餐'];
  } else if (types.size === 1 && types.has('scenery')) {
    examples = ['适合亲子', '室内为主', '游玩半天', '控制预算'];
  } else if (allTransport) {
    examples = ['优先便宜', '耗时更短', '尽量少换乘', '出发时间合适'];
  } else {
    examples = ['更看重价格', '时间更合适', '距离更近', '帮我比较怎么选'];
  }
  return `💡 想让我进一步帮您筛选，可以继续说${examples.map(item => `“${item}”`).join('、')}，或直接说“帮我综合解读推荐”。我会基于本次结果继续分析，无需重新查询。`;
}

function followUpPolicy(items) {
  return {
    mode: 'reuse_snapshot_for_preferences',
    script: path.join(__dirname, 'analyze-existing-snapshot.js'),
    argsTemplate: ['--snapshot', '<snapshotFilePath>', '--request', '<用户本轮原话>'],
    reuseWhen: '用户只补充筛选偏好、比较目标或要求解释本次结果',
    refreshWhen: '用户改变地点、方向、日期、查询对象，明确要求现在/最新/重新查询/可订状态，或原结果不可访问'
  };
}

function resourceCard(item, index, reason) {
  const facts = resourceFacts(item);
  const lines = [`#### ${index + 1}. ${md(item.title)}${item.price ? ` · ${md(item.price)}起` : ''}`, '',
    ...(facts.length ? [md(facts.join(' · ')), ''] : []), ...(reason ? [md(reason), ''] : [])];
  const links = bookingLinks(item);
  lines.push(links || '本条未返回可直接打开的预订入口，请查看完整产物中的可用入口。', '');
  return lines;
}

function compactPayload(payload, compiled) {
  const { reviewed, request } = compiled;
  const title = reviewed.mode === 'itinerary' ? `${[request.departure, request.destination].filter(Boolean).join(' → ')} 行程规划`
    : String(payload.markdown.split('\n')[0]).replace(/^#+\s*/, '');
  const adviceHeading = reviewed.mode === 'selection' ? '💡 **推荐建议**：' : '🧭 **行程安排建议**：';
  const lines = [`### ${md(title)}`, '',
    `✅ 共找到 **${payload.stats.total}** 条同程旅行结果。下方为精选推荐，全部候选保留在完整 HTML 和 Markdown 文件中。`, '',
    adviceHeading, '', md(reviewed.mode === 'selection' ? reviewed.selection.summary : reviewed.model.highlight), ''];
  let selected;
  if (reviewed.mode === 'selection') {
    selected = reviewed.selection.cards.map(c => c.resource);
    lines.push(selected.length ? `#### 精选推荐（${selected.length} 项）` : '本次暂无符合条件的推荐。', '');
    lines.push(...recommendationTable(reviewed.selection.cards));
    // Decision rationale and interpretation belong in the full artifact. Keep
    // every explicit booking caveat in chat; do not silently cut risk text.
    const notes = [...new Set(reviewed.selection.confirmations)];
    if (notes.length) lines.push('#### 预订前请确认', '', ...notes.map(t => `- ${md(t)}`), '');
  } else {
    lines.push('完整每日安排、全部资源和详细解读已保留在 HTML 与完整 Markdown 文件中。', '', '#### 行程节奏', '');
    for (const day of reviewed.model.days) {
      const itinerary = day.activities.map(a => a.name).join(' → ') || day.segments.map(s => s.label).join('、');
      lines.push(`- **Day ${day.dayNo} · ${md(day.title)}**：${md(itinerary)}`);
    }
    // Prefer transport/hotel booking actions in chat; all attractions stay in HTML.
    const all = compiled.chatResources || [];
    selected = [...all.filter(i => ['flight', 'train', 'bus', 'hotel'].includes(i.type)), ...all.filter(i => !['flight', 'train', 'bus', 'hotel'].includes(i.type))].slice(0, 5);
    lines.push('', '#### 方案中的预订选择', '');
    selected.forEach((item, i) => lines.push(...resourceCard(item, i)));
    if (reviewed.model.tips.length) lines.push('#### 预订前确认', '', ...reviewed.model.tips.map(t => `- ${md(t)}`), '');
  }
  lines.push('价格为查询时的展示价，实际价格、可订状态和适用条件以预订页为准。');
  // Keep the original Skill's support footer without duplicating its contact
  // details here. Only the selected body is brief; its layout is final output.
  const support = payload.markdown.match(/\n---\n\n#### 客服支持\n[\s\S]*$/);
  if (support) lines.push('', support[0].trim());
  const markdown = lines.join('\n').trim();
  return { ...payload, fullMarkdown: payload.markdown, markdown, summaryMarkdown: markdown,
    chatResourceCount: selected.length,
    responsePolicy: { finalAnswerField: 'markdown', mode: 'curated_verbatim', mustDisplayInChat: true,
      mustNotRewriteMarkdown: true, requiredMarkdownColumns: ['预订'],
      finalAnswerMustStartWith: `### ${md(title)}`,
      mustDisplayAllResources: false, allResourcesInArtifacts: true, draftCheckRequired: false,
      preserveSelectedBookingLinks: true },
    finalAnswerInstruction: 'markdown 已是排版完成的精选答复，原样输出这一短正文；保留标题、概况、建议、表格/行程、预订链接、提醒及客服，不再次摘要、重排或追加分析。HTML附件不能替代正文。不复制全量资源，不写草稿或运行全文指纹校验。' };
}

function compactDirectPayload(payload, items) {
  const title = String(payload.markdown.split('\n')[0]).replace(/^#+\s*/, '');
  const displayable = items.filter(item => item && item.type !== 'plan');
  const selected = displayable.slice(0, 5);
  const lines = [`### ${md(title)}`, '',
    `✅ 共找到 **${payload.stats.total}** 条同程旅行结果。以下按查询返回顺序展示前 **${selected.length}** 条，不做二次偏好排序；全部结果保留在完整 HTML 和 Markdown 文件中。`, '',
    '#### 查询结果', '', ...directResultTable(selected),
    followUpGuidance(displayable), '',
    '价格为查询时的展示价，实际价格、可订状态和适用条件以预订页为准。'];
  const support = payload.markdown.match(/\n---\n\n#### 客服支持\n[\s\S]*$/);
  if (support) lines.push('', support[0].trim());
  const markdown = lines.join('\n').trim();
  return { ...payload, fullMarkdown: payload.markdown, markdown, summaryMarkdown: markdown,
    chatResourceCount: selected.length, directRender: true,
    followUpPolicy: followUpPolicy(displayable),
    responsePolicy: { finalAnswerField: 'markdown', mode: 'direct_listing', mustDisplayInChat: true,
      mustNotRewriteMarkdown: true, requiredMarkdownColumns: ['预订'],
      finalAnswerMustStartWith: `### ${md(title)}`,
      mustDisplayAllResources: false, allResourcesInArtifacts: true, draftCheckRequired: false,
      preserveSelectedBookingLinks: true },
    finalAnswerInstruction: 'finalAnswer 已是程序按接口返回顺序生成的查询结果和自然偏好引导，原样输出；不要再做推荐、比较、摘要或追加分析，也不要删除末尾引导。HTML附件保留全部候选。' };
}

function saveDelivery(payload) {
  const directory = fs.mkdtempSync(path.join(path.dirname(payload.htmlFilePath), 'delivery-'));
  const markdownFilePath = path.join(directory, 'reply.md');
  const fullMarkdownFilePath = path.join(directory, 'full-result.md');
  const responseDataFilePath = path.join(directory, 'render-data.json');
  const manifestFilePath = path.join(directory, 'delivery-manifest.json');
  fs.writeFileSync(markdownFilePath, payload.markdown, 'utf8');
  fs.writeFileSync(fullMarkdownFilePath, payload.fullMarkdown, 'utf8');
  fs.writeFileSync(responseDataFilePath, JSON.stringify(payload, null, 2), 'utf8');
  const manifest = withArtifactDelivery({ type: 'workbuddy_expert_delivery', version: 4,
    expertStage: 'rendered', manifestFilePath, responseDataFilePath,
    markdownFilePath, fullMarkdownFilePath,
    markdownChunkFiles: [markdownFilePath], markdownChunkCount: 1,
    htmlFilePath: payload.htmlFilePath, stats: payload.stats, resourceDisplay: payload.resourceDisplay,
    chatResourceCount: payload.chatResourceCount, responsePolicy: payload.responsePolicy,
    ...(payload.followUpPolicy ? { followUpPolicy: payload.followUpPolicy } : {}),
    ...(payload.timings ? { timings: payload.timings } : {}),
    validationWarnings: payload.validationWarnings });
  const directListing = payload.responsePolicy && payload.responsePolicy.mode === 'direct_listing';
  manifest.finalAnswerInstruction = payload.finalAnswerInstruction;
  manifest.presentFilesInstruction = manifest.artifactDeliveryInstruction = manifest.artifactDeliveryMode === 'desktop-sidebar'
    ? directListing
      ? '最终回复前必须使用 presentFilesArgs 调用 present_files 并等待结果；随后原样输出回执 finalAnswer，不读取 reply.md。失败仅重试一次并如实说明。'
      : '最终回复前必须使用 presentFilesArgs 实际调用 present_files 并等待工具结果；读取 reply.md 可同轮进行。文件已生成不等于已展示，不能只贴正文结束。失败按原路径仅重试一次；仍失败或工具不可用，明确说明预览未成功，再交付精选正文；只有成功才能说已打开。'
    : directListing
      ? '使用当前可用的文件预览或附件工具交付 HTML；随后原样输出回执 finalAnswer，不读取 reply.md。工具不可用或失败时如实说明。'
      : '最终回复前使用当前可用的文件预览或附件工具交付 HTML，可用 present_files 展示文件卡片但不要求 PC 侧边栏；没有工具或失败时如实说明，再交付含预订链接的精选正文。';
  // Publish only after the final object is complete. Recovery reads this same
  // manifest, never the earlier render-data payload. No second draft is needed.
  fs.writeFileSync(manifestFilePath, JSON.stringify(manifest, null, 2), { mode: 0o600 });
  return manifest;
}

function deliveryReceipt(manifest, options = {}) {
  const presentRequired = Boolean(manifest.responsePolicy && manifest.responsePolicy.presentFilesRequired);
  const inlineFinalAnswer = options.inlineFinalAnswer
    ? fs.readFileSync(manifest.markdownFilePath, 'utf8')
    : '';
  return { expertStage: manifest.expertStage, stage: 'rendered', nextAction: 'deliver', manifestFilePath: manifest.manifestFilePath,
    markdownFilePath: manifest.markdownFilePath, fullMarkdownFilePath: manifest.fullMarkdownFilePath,
    artifactDeliveryMode: manifest.artifactDeliveryMode, presentFilesArgs: manifest.presentFilesArgs,
    presentFilesRequired: presentRequired,
    presentFilesInstruction: manifest.presentFilesInstruction,
    ...(manifest.followUpPolicy ? { followUpPolicy: manifest.followUpPolicy } : {}),
    ...(inlineFinalAnswer ? { finalAnswer: inlineFinalAnswer, responseFlow: 'direct_render' } : {}),
    allowedReads: inlineFinalAnswer ? [] : [manifest.markdownFilePath],
    allowedCalls: presentRequired && manifest.presentFilesArgs
      ? [{ tool: 'present_files', args: manifest.presentFilesArgs }]
      : manifest.presentFilesArgs ? [{ tool: 'file_preview', args: manifest.presentFilesArgs }] : [],
    retryBudget: { present: 1 },
    instruction: inlineFinalAnswer
      ? '按 allowedCalls 交付HTML（失败最多重试一次），再原样输出 finalAnswer；不要读取文件、重排、推荐或追加分析。'
      : '按 allowedCalls 交付HTML（失败最多重试一次），再原样输出 allowedReads 中的 reply.md；不要重排或读取 full-result.md。' };
}

module.exports = { compactDirectPayload, compactPayload, saveDelivery, deliveryReceipt, bookingLinks, followUpGuidance };
