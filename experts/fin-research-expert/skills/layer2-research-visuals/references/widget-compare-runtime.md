# Grouped Comparison Widget Runtime

Renderer version: `workbuddy-compare-svg/1`

Use only for `chart_type: "column"` or `chart_type: "grouped_column"` from a validated `research-visual/1` entry. Keep at most 12 categories and 4 series. Values, labels and units must be copied unchanged from the evidence. Red `#d92d20` means positive/up and green `#079455` means negative/down only when the source values are directional; otherwise the runtime uses neutral comparison colors.

This is the reviewed runtime used by `scripts/render_widget.mjs`. Do not copy or splice it in model output. If labels or values do not align, use `fallback_table`.

```html
<svg data-tongzhou-compare="workbuddy-compare-svg-1" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent;touch-action:none">
  <title>分组对比图</title>
  <desc>基于当前已认证公开研究证据生成的分组对比图。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表未渲染，请参考数据表</text>
</svg>
<script type="application/json" data-tongzhou-chart-payload="workbuddy-compare-svg-1">__TONGZHOU_CHART_PAYLOAD__</script>
<script>
(() => {
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-compare="workbuddy-compare-svg-1"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const payloadNode = Array.from(document.querySelectorAll('script[data-tongzhou-chart-payload="workbuddy-compare-svg-1"]')).find(item => item.dataset.consumed !== 'true');
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
  const colors = { text:'#292927', muted:'#77766f', grid:'#deddd6', blue:'#185fa5', teal:'#0f766e', gold:'#ba7517', violet:'#6554c0', up:'#d92d20', down:'#079455', neutral:'#888780', panel:'#ffffff' };
  const palette = [colors.blue, colors.teal, colors.gold, colors.violet];
  const finite = value => value !== null && value !== '' && Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const chartWidth = clamp(Math.round(svg.getBoundingClientRect().width || 680), 680, 1280);
  svg.setAttribute('viewBox', `0 0 ${chartWidth} 340`);
  const create = (name, attrs = {}, value = '', parent = svg) => {
    const node = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([key, attrValue]) => node.setAttribute(key, String(attrValue)));
    if (value !== '') node.textContent = String(value);
    parent.appendChild(node);
    return node;
  };
  const text = (x, y, value, attrs = {}, parent = svg) => create('text', { x, y, 'font-size':11, fill:colors.text, ...attrs }, value, parent);
  const line = (x1, y1, x2, y2, attrs = {}, parent = svg) => create('line', { x1, y1, x2, y2, stroke:colors.grid, 'stroke-width':0.7, ...attrs }, '', parent);
  const rect = (x, y, width, height, attrs = {}, parent = svg) => create('rect', { x, y, width, height, ...attrs }, '', parent);
  const short = (value, limit = 12) => { const raw = String(value ?? ''); return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw; };
  const format = value => Math.abs(number(value)) >= 1000 ? number(value).toLocaleString('zh-CN', { maximumFractionDigits:2 }) : number(value).toFixed(2).replace(/\.00$/, '');
  const empty = message => { svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove()); text(chartWidth / 2, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 }); };
  const chart = payload.evidence ?? {};
  if (payload.renderer_version !== 'workbuddy-compare-svg/1' || payload.schema_version !== 'research-visual/1' || !['column','grouped_column'].includes(payload.chart_type)) {
    empty('当前对比模板或数据版本不匹配'); return;
  }
  const categories = (chart.categories ?? []).slice(0, 12).map(String);
  const series = (chart.series ?? []).slice(0, 4).map(item => ({ name:String(item.name ?? ''), unit:String(item.unit ?? chart.unit ?? ''), values:(item.values ?? []).slice(0, categories.length) }));
  if (categories.length === 0 || series.length === 0 || series.some(item => item.values.length !== categories.length || item.values.some(value => !finite(value)))) {
    empty('对比数据不完整，已保留原始表格'); return;
  }
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '分组对比图');
  const x0 = 52, x1 = chartWidth - 34, y0 = 72, y1 = 270;
  const values = series.flatMap(item => item.values.map(number));
  const directional = values.some(value => value < 0);
  let min = Math.min(0, ...values), max = Math.max(0, ...values);
  if (min === max) max = min + 1;
  const pad = (max - min) * 0.08;
  min -= min < 0 ? pad : 0; max += pad;
  const yAt = value => y0 + (max - number(value)) * (y1 - y0) / (max - min);
  const zeroY = yAt(0);
  const groupWidth = (x1 - x0) / categories.length;
  const barWidth = Math.max(5, Math.min(28, groupWidth * 0.72 / series.length));
  text(x0, 22, short(payload.title ?? '分组对比图', chartWidth >= 960 ? 32 : 20), { 'font-size':15, 'font-weight':500 });
  text(x0, 43, `${categories.length} 个分类 · ${series.length} 组证据`, { fill:colors.muted });
  series.forEach((item, index) => text(chartWidth - 34 - (series.length - 1 - index) * 120, 43, `● ${short(item.name, 10)}`, { 'text-anchor':'end', fill:palette[index], 'font-weight':500 }));
  for (let index = 0; index < 5; index += 1) {
    const value = min + (max - min) * index / 4; const y = yAt(value); line(x0, y, x1, y); text(x0 - 8, y + 4, format(value), { 'text-anchor':'end', fill:colors.muted });
  }
  line(x0, zeroY, x1, zeroY, { stroke:colors.neutral, 'stroke-width':1 });
  const hitAreas = [];
  categories.forEach((category, categoryIndex) => {
    const center = x0 + groupWidth * (categoryIndex + 0.5);
    series.forEach((item, seriesIndex) => {
      const value = number(item.values[categoryIndex]); const y = yAt(value);
      const x = center + (seriesIndex - (series.length - 1) / 2) * barWidth - barWidth * 0.42;
      const color = directional ? value > 0 ? colors.up : value < 0 ? colors.down : colors.neutral : palette[seriesIndex];
      rect(x, Math.min(y, zeroY), barWidth * 0.84, Math.max(1, Math.abs(zeroY - y)), { fill:color, rx:1.5, opacity:0.88 });
    });
    text(center, 290, short(category, chartWidth >= 960 ? 12 : 8), { 'text-anchor':'middle', fill:colors.muted });
    hitAreas.push({ x:center - groupWidth / 2, width:groupWidth, category, values:series.map(item => `${item.name} ${format(item.values[categoryIndex])}${item.unit ? ` ${item.unit}` : ''}`) });
  });
  const guide = line(x0, y0, x0, y1, { stroke:colors.neutral, 'stroke-dasharray':'3 3', opacity:0, 'pointer-events':'none' });
  const tip = rect(x0, 302, Math.min(500, chartWidth - x0 - 22), 27, { fill:colors.panel, stroke:colors.grid, rx:4, opacity:0, 'pointer-events':'none' });
  const tipText = text(x0 + 8, 320, '', { opacity:0, 'pointer-events':'none' });
  const hide = () => { guide.setAttribute('opacity','0'); tip.setAttribute('opacity','0'); tipText.setAttribute('opacity','0'); };
  svg.addEventListener('pointermove', event => {
    const point = svg.createSVGPoint(); point.x = event.clientX; point.y = event.clientY; const local = point.matrixTransform(svg.getScreenCTM().inverse());
    const hit = hitAreas.find(item => local.x >= item.x && local.x <= item.x + item.width);
    if (!hit || local.y < y0 || local.y > y1) { hide(); return; }
    const center = hit.x + hit.width / 2; guide.setAttribute('x1',center); guide.setAttribute('x2',center); guide.setAttribute('opacity','0.75');
    tipText.textContent = short(`${hit.category} · ${hit.values.join(' · ')}`, chartWidth >= 960 ? 76 : 44); tip.setAttribute('opacity','0.96'); tipText.setAttribute('opacity','1');
  });
  svg.addEventListener('pointerleave', hide);
})();
</script>
```
