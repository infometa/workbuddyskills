# Event Return Widget Runtime

Renderer version: `workbuddy-event-svg/1`

Use only for `chart_type: "event_return_bar"`. `evidence.points` contains up to seven `{label,value,sample_count,missing_count}` items. Include only finite percentage values with `sample_count > 0`. `options.precision` is 0 to 4.

Copy the fragment unchanged, replace only `__TONGZHOU_CHART_PAYLOAD__`, and pass it directly to `show_widget`. The tool argument starts with `<svg` and ends with `</script>`; never add CDATA or Markdown wrappers.

```html
<svg data-tongzhou-event="workbuddy-event-svg-1" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent">
  <title>事件窗口历史表现图</title>
  <desc>基于当前已认证公开事件样本生成的历史描述统计，不代表预测。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表加载中，请同时参考样本表</text>
</svg>
<script>
(() => {
  const payload = __TONGZHOU_CHART_PAYLOAD__;
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-event="workbuddy-event-svg-1"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const ns = 'http://www.w3.org/2000/svg';
  const colors = { up:'#d92d20', down:'#079455', neutral:'#888780', text:'#292927', muted:'#77766f', grid:'#deddd6' };
  const finite = value => Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
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
    text(340, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 });
  };
  if (payload.renderer_version !== 'workbuddy-event-svg/1' || payload.schema_version !== 'chart-evidence/1' || payload.chart_type !== 'event_return_bar') {
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

  const left = 116, center = 350, right = 584, top = 76;
  const rowHeight = Math.min(38, 226 / points.length);
  const maxAbs = Math.max(...points.map(point => Math.abs(number(point.value))), 0.000001);
  const totalSamples = points.reduce((sum, point) => sum + Number(point.sample_count), 0);
  const totalMissing = points.reduce((sum, point) => sum + Math.max(0, Number(point.missing_count ?? 0)), 0);

  text(44, 22, short(payload.title ?? '事件窗口历史表现图', 20), { 'font-size':15, 'font-weight':500 });
  text(636, 22, `${points.length} 个有效窗口 · 样本合计 ${totalSamples}`, { 'text-anchor':'end', 'font-size':11, 'font-weight':500 });
  text(44, 43, '历史描述统计，不代表预测或策略回测', { fill:colors.muted });
  text(636, 43, totalMissing > 0 ? `缺失样本 ${totalMissing}` : '无缺失样本记录', { 'text-anchor':'end', fill:colors.muted });
  line(center, top - 14, center, top + points.length * rowHeight, { stroke:colors.neutral, 'stroke-width':1 });
  text(center - 8, top - 24, '负值', { 'text-anchor':'end', fill:colors.down });
  text(center + 8, top - 24, '正值', { fill:colors.up });

  points.forEach((point, index) => {
    const value = number(point.value);
    const y = top + index * rowHeight;
    const width = Math.abs(value) / maxAbs * Math.min(center - left, right - center);
    const color = value > 0 ? colors.up : value < 0 ? colors.down : colors.neutral;
    text(left - 10, y + 16, short(point.label, 12), { 'text-anchor':'end', 'font-weight':500 });
    rect(value >= 0 ? center : center - width, y, Math.max(width, 1), 22, { rx:2, fill:color, 'fill-opacity':0.84 });
    const label = `${value > 0 ? '+' : ''}${value.toFixed(precision)}%  n=${Number(point.sample_count)}${Number(point.missing_count ?? 0) > 0 ? `  缺${Number(point.missing_count)}` : ''}`;
    const labelX = value >= 0 ? Math.min(center + width + 7, 632) : Math.max(center - width - 7, 122);
    text(labelX, y + 16, label, { 'text-anchor':value >= 0 ? 'start' : 'end', fill:color, 'font-weight':500 });
  });
})();
</script>
```

Do not add a placeholder bar for an empty long window. Explain the missing window only in the data-coverage note and fallback table.
