# Event Return Widget Runtime

Renderer version: `workbuddy-event-svg/2`

Use only for `chart_type: "event_return_bar"`. `evidence.points` contains up to seven `{label,value,sample_count,missing_count}` items. Include only finite percentage values with `sample_count > 0`. `options.precision` is 0 to 4.

This is the reviewed runtime used by `scripts/render_widget.mjs`. Do not copy or splice it in model output. Give the renderer a validated payload and pass its complete `show-widget` JSON output unchanged.

```html
<svg data-tongzhou-event="workbuddy-event-svg-2" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent">
  <title>事件窗口历史表现图</title>
  <desc>基于当前已认证公开事件样本生成的历史描述统计，不代表预测。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表未渲染，请参考样本表</text>
</svg>
<script type="application/json" data-tongzhou-chart-payload="workbuddy-event-svg-2">__TONGZHOU_CHART_PAYLOAD__</script>
<script>
(() => {
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-event="workbuddy-event-svg-2"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const payloadNode = Array.from(document.querySelectorAll('script[data-tongzhou-chart-payload="workbuddy-event-svg-2"]')).find(item => item.dataset.consumed !== 'true');
  const placeholder = svg.querySelector('[data-runtime-placeholder]');
  if (!payloadNode) {
    if (placeholder) placeholder.textContent = '图表数据缺失，请参考样本表';
    return;
  }
  payloadNode.dataset.consumed = 'true';
  let payload;
  try {
    payload = JSON.parse(payloadNode.textContent || '');
  } catch {
    if (placeholder) placeholder.textContent = '图表数据格式错误，请参考样本表';
    return;
  }
  const ns = 'http://www.w3.org/2000/svg';
  const colors = { up:'#d92d20', down:'#079455', neutral:'#888780', text:'#292927', muted:'#77766f', grid:'#deddd6' };
  const finite = value => Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const chartWidth = clamp(Math.round(svg.getBoundingClientRect().width || 680), 680, 1280);
  svg.setAttribute('viewBox', `0 0 ${chartWidth} 340`);
  const precision = clamp(Number(payload.options?.precision ?? 2), 0, 4);
  const create = (name, attrs = {}, value = '') => {
    const node = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([key, attrValue]) => node.setAttribute(key, String(attrValue)));
    if (value !== '') node.textContent = String(value);
    svg.appendChild(node);
    return node;
  };
  const text = (x, y, value, attrs = {}) => create('text', { x, y, 'font-size':11, fill:colors.text, ...attrs }, value);
  const line = (x1, y1, x2, y2, attrs = {}) => create('line', { x1, y1, x2, y2, stroke:colors.grid, 'stroke-width':0.7, ...attrs });
  const rect = (x, y, width, height, attrs = {}) => create('rect', { x, y, width, height, ...attrs });
  const short = (value, limit = 28) => {
    const raw = String(value ?? '');
    return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw;
  };
  const empty = message => {
    svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
    text(chartWidth / 2, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 });
  };
  if (payload.renderer_version !== 'workbuddy-event-svg/2' || payload.schema_version !== 'chart-evidence/1' || payload.chart_type !== 'event_return_bar') {
    empty('当前事件模板或数据版本不匹配');
    return;
  }
  const points = (payload.evidence?.points ?? []).filter(point => finite(point.value) && Number(point.sample_count) > 0).slice(0, 7);
  if (points.length === 0) {
    empty('当前事件窗口没有有效样本，已保留数据口径说明');
    return;
  }
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '事件窗口历史表现图');
  svg.querySelector('desc').textContent = String(payload.description ?? '基于当前已认证公开事件样本生成的历史描述统计，不代表预测。');

  const categoryX = 142, plotLeft = 168, plotRight = chartWidth - 220, center = (plotLeft + plotRight) / 2, valueColumn = chartWidth - 44, top = 78;
  const rowHeight = Math.min(42, 220 / points.length);
  const maxAbs = Math.max(...points.map(point => Math.abs(number(point.value))), 0.000001);
  const totalSamples = points.reduce((sum, point) => sum + Number(point.sample_count), 0);
  const totalMissing = points.reduce((sum, point) => sum + Math.max(0, Number(point.missing_count ?? 0)), 0);

  text(44, 22, short(payload.title ?? '事件窗口历史表现图', chartWidth >= 960 ? 32 : 20), { 'font-size':15, 'font-weight':500 });
  text(chartWidth - 44, 22, `${points.length} 个有效窗口 · 样本合计 ${totalSamples}`, { 'text-anchor':'end', 'font-size':11, 'font-weight':500 });
  text(44, 43, '历史描述统计，不代表预测或策略回测', { fill:colors.muted });
  text(chartWidth - 44, 43, totalMissing > 0 ? `缺失样本 ${totalMissing}` : '无缺失样本记录', { 'text-anchor':'end', fill:colors.muted });
  line(center, top - 14, center, top + points.length * rowHeight, { stroke:colors.neutral, 'stroke-width':1 });
  text(center - 8, top - 24, '负值', { 'text-anchor':'end', fill:colors.down });
  text(center + 8, top - 24, '正值', { fill:colors.up });

  points.forEach((point, index) => {
    const value = number(point.value);
    const y = top + index * rowHeight;
    const width = Math.abs(value) / maxAbs * Math.min(center - plotLeft, plotRight - center);
    const color = value > 0 ? colors.up : value < 0 ? colors.down : colors.neutral;
    line(plotLeft, y + 11, plotRight, y + 11, { stroke:colors.grid, 'stroke-width':0.55 });
    text(categoryX, y + 16, short(point.label, 12), { 'text-anchor':'end', 'font-weight':500 });
    rect(value >= 0 ? center : center - width, y, Math.max(width, 1), 22, { rx:2, fill:color, 'fill-opacity':0.84 });
    const label = `${value > 0 ? '+' : ''}${value.toFixed(precision)}%  n=${Number(point.sample_count)}${Number(point.missing_count ?? 0) > 0 ? `  缺${Number(point.missing_count)}` : ''}`;
    text(valueColumn, y + 16, label, { 'text-anchor':'end', fill:color, 'font-weight':500 });
  });
})();
</script>
```

Do not add a placeholder bar for an empty long window. Explain the missing window only in the data-coverage note and fallback table.
