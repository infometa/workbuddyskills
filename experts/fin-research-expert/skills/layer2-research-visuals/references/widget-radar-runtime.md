# Radar Widget Runtime

Renderer version: `workbuddy-radar-svg/1`

Use only for `chart_type: "radar"` from a validated, renderable `research-visual/1` entry. `dimensions` and `values` must align, and finite `scale_min`, `scale_max` and a non-empty `scale_description` must be present. A radar without an explicit source scale is not calibrated evidence; use its dimension/value `fallback_table` instead.

This is the reviewed runtime used by `scripts/render_widget.mjs`. Do not copy or splice it in model output. Give the renderer a validated payload and pass its complete `show-widget` JSON output unchanged.

```html
<svg data-tongzhou-radar="workbuddy-radar-svg-1" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent;touch-action:none">
  <title>研究维度雷达图</title>
  <desc>基于当前已认证公开研究证据和来源量表生成的雷达图。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表未渲染，请参考数据表</text>
</svg>
<script type="application/json" data-tongzhou-chart-payload="workbuddy-radar-svg-1">__TONGZHOU_CHART_PAYLOAD__</script>
<script>
(() => {
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-radar="workbuddy-radar-svg-1"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const payloadNode = Array.from(document.querySelectorAll('script[data-tongzhou-chart-payload="workbuddy-radar-svg-1"]')).find(item => item.dataset.consumed !== 'true');
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
  const colors = { text:'#292927', muted:'#77766f', grid:'#deddd6', primary:'#185fa5', fill:'#e8f2fb', point:'#ba7517', panel:'#ffffff' };
  const finite = value => value !== null && value !== '' && Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const chartWidth = clamp(Math.round(svg.getBoundingClientRect().width || 680), 680, 1280);
  svg.setAttribute('viewBox', `0 0 ${chartWidth} 340`);
  const create = (name, attrs = {}, value = '', parent = svg) => { const node = document.createElementNS(ns, name); Object.entries(attrs).forEach(([key, attrValue]) => node.setAttribute(key, String(attrValue))); if (value !== '') node.textContent = String(value); parent.appendChild(node); return node; };
  const text = (x, y, value, attrs = {}, parent = svg) => create('text', { x, y, 'font-size':11, fill:colors.text, ...attrs }, value, parent);
  const line = (x1, y1, x2, y2, attrs = {}, parent = svg) => create('line', { x1, y1, x2, y2, stroke:colors.grid, 'stroke-width':0.7, ...attrs }, '', parent);
  const rect = (x, y, width, height, attrs = {}, parent = svg) => create('rect', { x, y, width, height, ...attrs }, '', parent);
  const short = (value, limit = 14) => { const raw = String(value ?? ''); return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw; };
  const empty = message => { svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove()); text(chartWidth / 2, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 }); };
  const radar = payload.evidence ?? {};
  const dimensions = (radar.dimensions ?? []).slice(0, 10).map(String); const values = (radar.values ?? []).slice(0, dimensions.length);
  const scale_min = radar.scale_min; const scale_max = radar.scale_max; const scale_description = String(radar.scale_description ?? '');
  if (payload.renderer_version !== 'workbuddy-radar-svg/1' || payload.schema_version !== 'research-visual/1' || payload.chart_type !== 'radar' || dimensions.length < 3 || values.length !== dimensions.length || values.some(value => !finite(value)) || !finite(scale_min) || !finite(scale_max) || number(scale_max) <= number(scale_min) || !scale_description) {
    empty('量表边界不足，已保留维度和值表格'); return;
  }
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '研究维度雷达图');
  const cx = chartWidth * 0.45, cy = 190, radius = 112, count = dimensions.length;
  const pointAt = (index, ratio = 1) => { const angle = -Math.PI / 2 + index * Math.PI * 2 / count; return [cx + Math.cos(angle) * radius * ratio, cy + Math.sin(angle) * radius * ratio]; };
  const polygon = ratio => Array.from({ length:count }, (_, index) => pointAt(index, ratio).map(value => value.toFixed(1)).join(',')).join(' ');
  text(32, 22, short(payload.title ?? '研究维度雷达图', chartWidth >= 960 ? 32 : 20), { 'font-size':15, 'font-weight':500 });
  text(32, 43, short(scale_description, chartWidth >= 960 ? 58 : 34), { fill:colors.muted });
  [0.25,0.5,0.75,1].forEach(ratio => create('polygon', { points:polygon(ratio), fill:'none', stroke:colors.grid, 'stroke-width':0.8 }));
  dimensions.forEach((dimension, index) => {
    const [x,y] = pointAt(index); line(cx, cy, x, y);
    const [labelX,labelY] = pointAt(index, 1.17); const anchor = labelX < cx - 8 ? 'end' : labelX > cx + 8 ? 'start' : 'middle';
    text(labelX, labelY + (labelY < cy ? 0 : 5), short(dimension, 10), { 'text-anchor':anchor, fill:colors.muted });
  });
  const ratios = values.map(value => clamp((number(value) - number(scale_min)) / (number(scale_max) - number(scale_min)), 0, 1));
  const evidencePoints = ratios.map((ratio,index) => pointAt(index, ratio));
  create('polygon', { points:evidencePoints.map(point => point.map(value => value.toFixed(1)).join(',')).join(' '), fill:colors.fill, 'fill-opacity':0.72, stroke:colors.primary, 'stroke-width':2, 'stroke-linejoin':'round' });
  const hitAreas = evidencePoints.map(([x,y],index) => {
    create('circle', { cx:x, cy:y, r:3.2, fill:colors.panel, stroke:colors.primary, 'stroke-width':1.8 });
    return { x, y, dimension:dimensions[index], value:values[index] };
  });
  const panelX = Math.max(cx + radius + 58, chartWidth - 230);
  rect(panelX, 82, 196, 174, { fill:colors.panel, stroke:colors.grid, rx:5 });
  text(panelX + 14, 105, '维度原始值', { 'font-size':12, 'font-weight':500 });
  hitAreas.slice(0, 7).forEach((item,index) => { text(panelX + 14, 130 + index * 20, short(item.dimension, 10), { fill:colors.muted }); text(panelX + 180, 130 + index * 20, String(item.value), { 'text-anchor':'end', 'font-weight':500 }); });
  const tip = rect(32, 300, Math.min(420, chartWidth - 64), 27, { fill:colors.panel, stroke:colors.grid, rx:4, opacity:0, 'pointer-events':'none' });
  const tipText = text(42, 318, '', { opacity:0, 'pointer-events':'none' });
  const hide = () => { tip.setAttribute('opacity','0'); tipText.setAttribute('opacity','0'); };
  svg.addEventListener('pointermove', event => {
    const point = svg.createSVGPoint(); point.x = event.clientX; point.y = event.clientY; const local = point.matrixTransform(svg.getScreenCTM().inverse());
    const hit = hitAreas.find(item => Math.hypot(local.x - item.x, local.y - item.y) <= 15);
    if (!hit) { hide(); return; }
    tipText.textContent = `${hit.dimension} ${hit.value} · ${scale_description}`; tip.setAttribute('opacity','0.96'); tipText.setAttribute('opacity','1');
  });
  svg.addEventListener('pointerleave', hide);
})();
</script>
```
