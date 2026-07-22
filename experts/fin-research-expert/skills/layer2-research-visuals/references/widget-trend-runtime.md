# Trend Widget Runtime

Renderer version: `workbuddy-trend-svg/2`

Use only for `chart_type: "line"`. `evidence.series` contains one or two comparable named series with 2 to 120 ascending `{time,value}` points. `options.precision` is 0 to 4 and `options.unit` is a short display unit.

This is the reviewed runtime used by `scripts/render_widget.mjs`. Do not copy or splice it in model output. Give the renderer a validated payload and pass its complete `show-widget` JSON output unchanged.

```html
<svg data-tongzhou-trend="workbuddy-trend-svg-2" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent;touch-action:none">
  <title>行情趋势图</title>
  <desc>基于当前已认证公开行情证据生成的趋势图。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表未渲染，请参考数据表</text>
</svg>
<script type="application/json" data-tongzhou-chart-payload="workbuddy-trend-svg-2">__TONGZHOU_CHART_PAYLOAD__</script>
<script>
(() => {
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-trend="workbuddy-trend-svg-2"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const payloadNode = Array.from(document.querySelectorAll('script[data-tongzhou-chart-payload="workbuddy-trend-svg-2"]')).find(item => item.dataset.consumed !== 'true');
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
  const colors = { text:'#292927', muted:'#77766f', grid:'#deddd6', primary:'#185fa5', secondary:'#ba7517', up:'#d92d20', down:'#079455', neutral:'#888780', panel:'#ffffff' };
  const finite = value => Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const chartWidth = clamp(Math.round(svg.getBoundingClientRect().width || 680), 680, 1280);
  svg.setAttribute('viewBox', `0 0 ${chartWidth} 340`);
  const precision = clamp(Number(payload.options?.precision ?? 2), 0, 4);
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
  const format = value => number(value).toFixed(precision);
  const short = (value, limit = 26) => {
    const raw = String(value ?? '');
    return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw;
  };
  const empty = message => {
    svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
    text(chartWidth / 2, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 });
  };
  if (payload.renderer_version !== 'workbuddy-trend-svg/2' || payload.schema_version !== 'chart-evidence/1' || payload.chart_type !== 'line') {
    empty('当前趋势模板或数据版本不匹配');
    return;
  }
  const series = (payload.evidence?.series ?? []).slice(0, 2).map(item => ({
    name:String(item.name ?? ''),
    points:(item.points ?? []).filter(point => finite(point.value)).slice(-120)
  })).filter(item => item.points.length > 1);
  if (series.length === 0) {
    empty('有效趋势数据不足，已保留文字与表格说明');
    return;
  }
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '行情趋势图');
  svg.querySelector('desc').textContent = String(payload.description ?? '基于当前已认证公开行情证据生成的趋势图。');

  const x0 = 44, x1 = chartWidth - 66, y0 = 66, y1 = 286;
  const values = series.flatMap(item => item.points.map(point => number(point.value)));
  let valueMin = Math.min(...values), valueMax = Math.max(...values);
  const pad = Math.max((valueMax - valueMin) * 0.08, Math.max(Math.abs(valueMax), 1) * 0.008);
  valueMin -= pad;
  valueMax += pad;
  const count = Math.max(...series.map(item => item.points.length));
  const xAt = index => x0 + index * (x1 - x0) / Math.max(count - 1, 1);
  const yAt = value => y0 + (valueMax - number(value)) * (y1 - y0) / (valueMax - valueMin);
  const primary = series[0];
  const first = primary.points[0], latest = primary.points[primary.points.length - 1];
  const change = number(first.value) === 0 ? null : (number(latest.value) / number(first.value) - 1) * 100;
  const unit = short(payload.evidence?.unit ?? payload.options?.unit ?? '', 8);

  text(x0, 21, short(payload.title ?? '行情趋势图', chartWidth >= 960 ? 30 : 18), { 'font-size':15, 'font-weight':500 });
  text(chartWidth - 44, 21, `${format(latest.value)}${unit ? ` ${unit}` : ''}${change === null ? '' : `  ${change > 0 ? '+' : ''}${change.toFixed(2)}%`}`, { 'text-anchor':'end', 'font-size':12, 'font-weight':500, fill:change === null ? colors.text : change > 0 ? colors.up : change < 0 ? colors.down : colors.neutral });
  text(x0, 42, `${String(first.time ?? '')} - ${String(latest.time ?? '')}`, { fill:colors.muted });
  const legendStart = Math.max(x0 + 230, chartWidth - 320);
  [colors.primary, colors.secondary].forEach((color, index) => {
    const item = series[index];
    if (item) text(legendStart + index * 135, 42, `● ${short(item.name || `序列${index + 1}`, 12)}`, { fill:color, 'font-weight':500 });
  });

  for (let index = 0; index < 5; index += 1) {
    const value = valueMin + (valueMax - valueMin) * index / 4;
    const y = yAt(value);
    line(x0, y, x1, y);
    text(x1 + 8, y + 4, format(value), { fill:colors.muted });
  }

  series.forEach((item, seriesIndex) => {
    const color = seriesIndex === 0 ? colors.primary : colors.secondary;
    const coordinates = item.points.map((point, index) => [xAt(index), yAt(point.value)]);
    if (seriesIndex === 0) {
      const areaPath = `M ${coordinates[0][0].toFixed(1)} ${y1} ` + coordinates.map(([x, y]) => `L ${x.toFixed(1)} ${y.toFixed(1)}`).join(' ') + ` L ${coordinates[coordinates.length - 1][0].toFixed(1)} ${y1} Z`;
      create('path', { d:areaPath, fill:color, 'fill-opacity':0.07, stroke:'none' });
    }
    create('polyline', { points:coordinates.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '), fill:'none', stroke:color, 'stroke-width':seriesIndex === 0 ? 2.2 : 1.7, 'stroke-linecap':'round', 'stroke-linejoin':'round' });
    const end = coordinates[coordinates.length - 1];
    create('circle', { cx:end[0], cy:end[1], r:3, fill:colors.panel, stroke:color, 'stroke-width':2 });
  });

  const labelCount = Math.min(5, primary.points.length);
  const used = new Set();
  for (let slotIndex = 0; slotIndex < labelCount; slotIndex += 1) {
    const index = Math.round(slotIndex * (primary.points.length - 1) / Math.max(labelCount - 1, 1));
    if (used.has(index)) continue;
    used.add(index);
    const raw = String(primary.points[index].time ?? '');
    text(xAt(index), 312, raw.length >= 10 ? raw.slice(5, 10) : raw, { 'text-anchor':'middle', fill:colors.muted });
  }

  const hover = create('g', { display:'none', 'pointer-events':'none' });
  const hoverLine = line(x0, y0, x0, y1, { stroke:colors.neutral, 'stroke-width':0.9, 'stroke-dasharray':'3 3' }, hover);
  const hoverBox = rect(52, 74, 260, series.length === 2 ? 55 : 42, { rx:3, fill:colors.panel, 'fill-opacity':0.96, stroke:colors.grid }, hover);
  const hoverDate = text(62, 91, '', { 'font-weight':500 }, hover);
  const hoverPrimary = text(62, 108, '', { fill:colors.primary }, hover);
  const hoverSecondary = text(62, 125, '', { fill:colors.secondary }, hover);
  const overlay = rect(x0, y0, x1 - x0, y1 - y0, { fill:'transparent', 'pointer-events':'all' });
  const showPoint = event => {
    const bounds = svg.getBoundingClientRect();
    const pointerX = (event.clientX - bounds.left) * chartWidth / Math.max(bounds.width, 1);
    const index = clamp(Math.round((pointerX - x0) * (primary.points.length - 1) / (x1 - x0)), 0, primary.points.length - 1);
    const x = xAt(index);
    const boxX = x > chartWidth * 0.58 ? 52 : Math.max(chartWidth - 312, 52);
    hover.setAttribute('display', 'block');
    hoverLine.setAttribute('x1', x);
    hoverLine.setAttribute('x2', x);
    hoverBox.setAttribute('x', boxX);
    [hoverDate, hoverPrimary, hoverSecondary].forEach(item => item.setAttribute('x', boxX + 10));
    hoverDate.textContent = String(primary.points[index]?.time ?? '');
    hoverPrimary.textContent = `${primary.name || '序列1'}  ${primary.points[index] ? format(primary.points[index].value) : '—'}${unit ? ` ${unit}` : ''}`;
    hoverSecondary.textContent = series[1] && series[1].points[index] ? `${series[1].name || '序列2'}  ${format(series[1].points[index].value)}${unit ? ` ${unit}` : ''}` : '';
  };
  overlay.addEventListener('pointermove', showPoint);
  overlay.addEventListener('pointerdown', showPoint);
  overlay.addEventListener('pointerleave', () => hover.setAttribute('display', 'none'));
})();
</script>
```

If the two series do not share a meaningful unit or aligned time basis, render one primary series or use the fallback table instead of forcing them onto this template.
