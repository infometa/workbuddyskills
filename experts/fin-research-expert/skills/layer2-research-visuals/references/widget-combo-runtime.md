# Line-Column Combination Widget Runtime

Renderer version: `workbuddy-combo-svg/1`

Use only for `chart_type: "line_column"` from a validated `research-visual/1` entry. Preserve each series type. A right axis is used only when `requires_dual_axis=true` and the line and column units are incompatible. Never normalize one unit into another or imply that the axes share a scale.

This is the reviewed runtime used by `scripts/render_widget.mjs`. Do not copy or splice it in model output. If categories, types, values or units are incomplete, use `fallback_table`.

```html
<svg data-tongzhou-combo="workbuddy-combo-svg-1" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent;touch-action:none">
  <title>折柱组合图</title>
  <desc>基于当前已认证公开研究证据生成的折柱组合图。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表未渲染，请参考数据表</text>
</svg>
<script type="application/json" data-tongzhou-chart-payload="workbuddy-combo-svg-1">__TONGZHOU_CHART_PAYLOAD__</script>
<script>
(() => {
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-combo="workbuddy-combo-svg-1"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const payloadNode = Array.from(document.querySelectorAll('script[data-tongzhou-chart-payload="workbuddy-combo-svg-1"]')).find(item => item.dataset.consumed !== 'true');
  const placeholder = svg.querySelector('[data-runtime-placeholder]');
  if (!payloadNode) {
    if (placeholder) placeholder.textContent = '图表数据缺失，请参考数据表';
    return;
  }
  payloadNode.dataset.consumed = 'true';
  let payload;
  try {
    payload = JSON.parse(payloadNode.textContent || '');
  } catch {
    if (placeholder) placeholder.textContent = '图表数据格式错误，请参考数据表';
    return;
  }
  const ns = 'http://www.w3.org/2000/svg';
  const colors = { text:'#292927', muted:'#77766f', grid:'#deddd6', column:'#185fa5', line:'#ba7517', up:'#d92d20', down:'#079455', panel:'#ffffff' };
  const finite = value => value !== null && value !== '' && Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const chartWidth = clamp(Math.round(svg.getBoundingClientRect().width || 680), 680, 1280);
  svg.setAttribute('viewBox', `0 0 ${chartWidth} 340`);
  const create = (name, attrs = {}, value = '', parent = svg) => { const node = document.createElementNS(ns, name); Object.entries(attrs).forEach(([key, attrValue]) => node.setAttribute(key, String(attrValue))); if (value !== '') node.textContent = String(value); parent.appendChild(node); return node; };
  const text = (x, y, value, attrs = {}, parent = svg) => create('text', { x, y, 'font-size':11, fill:colors.text, ...attrs }, value, parent);
  const line = (x1, y1, x2, y2, attrs = {}, parent = svg) => create('line', { x1, y1, x2, y2, stroke:colors.grid, 'stroke-width':0.7, ...attrs }, '', parent);
  const rect = (x, y, width, height, attrs = {}, parent = svg) => create('rect', { x, y, width, height, ...attrs }, '', parent);
  const short = (value, limit = 12) => { const raw = String(value ?? ''); return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw; };
  const format = value => Math.abs(number(value)) >= 1000 ? number(value).toLocaleString('zh-CN', { maximumFractionDigits:2 }) : number(value).toFixed(2).replace(/\.00$/, '');
  const empty = message => { svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove()); text(chartWidth / 2, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 }); };
  const chart = payload.evidence ?? {};
  if (payload.renderer_version !== 'workbuddy-combo-svg/1' || payload.schema_version !== 'research-visual/1' || payload.chart_type !== 'line_column') { empty('当前折柱模板或数据版本不匹配'); return; }
  const categories = (chart.categories ?? []).slice(0, 12).map(String);
  const series = (chart.series ?? []).slice(0, 4).map(item => ({ name:String(item.name ?? ''), type:String(item.type ?? ''), unit:String(item.unit ?? chart.unit ?? ''), values:(item.values ?? []).slice(0, categories.length) }));
  const columns = series.filter(item => item.type === 'column'); const lines = series.filter(item => item.type === 'line');
  if (categories.length === 0 || columns.length === 0 || lines.length === 0 || series.some(item => item.values.length !== categories.length || item.values.some(value => !finite(value)))) { empty('折柱数据不完整，已保留原始表格'); return; }
  const requires_dual_axis = chart.requires_dual_axis === true;
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '折柱组合图');
  const x0 = 58, x1 = chartWidth - 58, y0 = 72, y1 = 270, groupWidth = (x1 - x0) / categories.length;
  const domain = items => { const values = items.flatMap(item => item.values.map(number)); let min = Math.min(0, ...values), max = Math.max(0, ...values); if (min === max) max = min + 1; const pad = (max - min) * 0.08; return [min < 0 ? min - pad : min, max + pad]; };
  const leftDomain = domain(columns); const rightDomain = requires_dual_axis ? domain(lines) : domain(series);
  const leftY = value => y0 + (leftDomain[1] - number(value)) * (y1 - y0) / (leftDomain[1] - leftDomain[0]);
  const rightY = value => y0 + (rightDomain[1] - number(value)) * (y1 - y0) / (rightDomain[1] - rightDomain[0]);
  text(x0, 22, short(payload.title ?? '折柱组合图', chartWidth >= 960 ? 32 : 20), { 'font-size':15, 'font-weight':500 });
  text(x0, 43, requires_dual_axis ? '双轴仅表示不同单位，不代表同一尺度' : '折线与柱使用同一证据尺度', { fill:colors.muted });
  text(chartWidth - 205, 43, `■ ${short(columns[0].name, 10)} ${columns[0].unit}`, { fill:colors.column, 'font-weight':500 });
  text(chartWidth - 34, 43, `● ${short(lines[0].name, 10)} ${lines[0].unit}`, { fill:colors.line, 'font-weight':500, 'text-anchor':'end' });
  for (let index = 0; index < 5; index += 1) {
    const leftValue = leftDomain[0] + (leftDomain[1] - leftDomain[0]) * index / 4; const y = leftY(leftValue); line(x0, y, x1, y); text(x0 - 8, y + 4, format(leftValue), { 'text-anchor':'end', fill:colors.muted });
    if (requires_dual_axis) { const rightValue = rightDomain[0] + (rightDomain[1] - rightDomain[0]) * index / 4; text(x1 + 8, y + 4, format(rightValue), { fill:colors.muted }); }
  }
  const barWidth = Math.max(8, Math.min(34, groupWidth * 0.55 / columns.length)); const zeroY = leftY(0);
  categories.forEach((category, categoryIndex) => {
    const center = x0 + groupWidth * (categoryIndex + 0.5);
    columns.forEach((item, index) => { const value = number(item.values[categoryIndex]); const y = leftY(value); const x = center + (index - (columns.length - 1) / 2) * barWidth - barWidth * 0.42; rect(x, Math.min(y, zeroY), barWidth * 0.84, Math.max(1, Math.abs(y - zeroY)), { fill:colors.column, rx:1.5, opacity:0.82 }); });
    text(center, 290, short(category, chartWidth >= 960 ? 12 : 8), { 'text-anchor':'middle', fill:colors.muted });
  });
  lines.forEach((item, lineIndex) => {
    const points = item.values.map((value, index) => [x0 + groupWidth * (index + 0.5), requires_dual_axis ? rightY(value) : leftY(value)]);
    create('path', { d:points.map(([x,y], index) => `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`).join(' '), fill:'none', stroke:lineIndex === 0 ? colors.line : colors.up, 'stroke-width':2.2, 'stroke-linejoin':'round' });
    points.forEach(([x,y]) => create('circle', { cx:x, cy:y, r:2.8, fill:colors.panel, stroke:lineIndex === 0 ? colors.line : colors.up, 'stroke-width':1.6 }));
  });
  const guide = line(x0, y0, x0, y1, { stroke:colors.muted, 'stroke-dasharray':'3 3', opacity:0, 'pointer-events':'none' });
  const tip = rect(x0, 302, Math.min(540, chartWidth - x0 - 22), 27, { fill:colors.panel, stroke:colors.grid, rx:4, opacity:0, 'pointer-events':'none' });
  const tipText = text(x0 + 8, 320, '', { opacity:0, 'pointer-events':'none' });
  const hide = () => { guide.setAttribute('opacity','0'); tip.setAttribute('opacity','0'); tipText.setAttribute('opacity','0'); };
  svg.addEventListener('pointermove', event => {
    const point = svg.createSVGPoint(); point.x = event.clientX; point.y = event.clientY; const local = point.matrixTransform(svg.getScreenCTM().inverse());
    if (local.x < x0 || local.x > x1 || local.y < y0 || local.y > y1) { hide(); return; }
    const index = clamp(Math.floor((local.x - x0) / groupWidth), 0, categories.length - 1); const center = x0 + groupWidth * (index + 0.5);
    const values = series.map(item => `${item.name} ${format(item.values[index])}${item.unit ? ` ${item.unit}` : ''}`);
    guide.setAttribute('x1',center); guide.setAttribute('x2',center); guide.setAttribute('opacity','0.75'); tipText.textContent = short(`${categories[index]} · ${values.join(' · ')}`, chartWidth >= 960 ? 80 : 46); tip.setAttribute('opacity','0.96'); tipText.setAttribute('opacity','1');
  });
  svg.addEventListener('pointerleave', hide);
})();
</script>
```
