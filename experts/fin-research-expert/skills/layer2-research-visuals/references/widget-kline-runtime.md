# K-line Widget Runtime

Renderer version: `workbuddy-kline-svg/1`

Use only for `chart_type: "candlestick_volume"`. The template accepts 2 to 60 ascending OHLC points, optional non-negative volume and up to three moving-average windows from 5, 10, 20, 30 or 60. `options.precision` is an integer from 0 to 4.

Copy the fragment unchanged, replace only `__TONGZHOU_CHART_PAYLOAD__`, and pass it directly to `show_widget`. The tool argument starts with `<svg` and ends with `</script>`; never add CDATA or Markdown wrappers.

```html
<svg data-tongzhou-kline="workbuddy-kline-svg-1" viewBox="0 0 680 340" role="img" style="display:block;width:100%;height:340px;font-family:var(--font-sans);background:transparent;touch-action:none">
  <title>行情 K 线图</title>
  <desc>基于当前已认证公开行情证据生成的日 K、均线与成交量图。</desc>
  <text data-runtime-placeholder="true" x="340" y="170" text-anchor="middle" font-size="12" fill="#888780">图表加载中，请同时参考数据表</text>
</svg>
<script>
(() => {
  const payload = __TONGZHOU_CHART_PAYLOAD__;
  const svg = Array.from(document.querySelectorAll('svg[data-tongzhou-kline="workbuddy-kline-svg-1"]')).find(item => item.dataset.rendered !== 'true');
  if (!svg) return;
  svg.dataset.rendered = 'true';
  const ns = 'http://www.w3.org/2000/svg';
  const colors = { up:'#d92d20', down:'#079455', neutral:'#888780', text:'#292927', muted:'#77766f', grid:'#deddd6', blue:'#185fa5', amber:'#ba7517', purple:'#534ab7', panel:'#ffffff' };
  const finite = value => Number.isFinite(Number(value));
  const number = value => Number(value);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
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
  const signed = value => `${value > 0 ? '+' : ''}${number(value).toFixed(2)}%`;
  const short = (value, limit = 24) => {
    const raw = String(value ?? '');
    return raw.length > limit ? `${raw.slice(0, limit - 1)}…` : raw;
  };
  const volumeLabel = value => {
    const current = number(value);
    if (current >= 100000000) return `${(current / 100000000).toFixed(1)}亿`;
    if (current >= 10000) return `${(current / 10000).toFixed(1)}万`;
    return `${Math.round(current)}`;
  };
  const empty = message => {
    svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
    text(340, 170, message, { 'text-anchor':'middle', fill:colors.muted, 'font-size':12 });
  };
  if (payload.renderer_version !== 'workbuddy-kline-svg/1' || payload.schema_version !== 'chart-evidence/1' || payload.chart_type !== 'candlestick_volume') {
    empty('当前 K 线模板或数据版本不匹配');
    return;
  }
  const points = (payload.evidence?.points ?? []).filter(point =>
    finite(point.open) && finite(point.high) && finite(point.low) && finite(point.close) &&
    number(point.open) > 0 && number(point.high) >= Math.max(number(point.open), number(point.close), number(point.low)) &&
    number(point.low) <= Math.min(number(point.open), number(point.close), number(point.high))
  ).slice(-60);
  if (points.length < 2) {
    empty('有效 OHLC 数据不足，已保留文字与表格说明');
    return;
  }
  svg.querySelectorAll('[data-runtime-placeholder]').forEach(item => item.remove());
  svg.querySelector('title').textContent = String(payload.title ?? '行情 K 线图');
  svg.querySelector('desc').textContent = String(payload.description ?? '基于当前已认证公开行情证据生成的日 K、均线与成交量图。');

  const x0 = 44, x1 = 622, priceTop = 70;
  const volumes = points.map(point => finite(point.volume) && number(point.volume) >= 0 ? number(point.volume) : 0);
  const hasVolume = Math.max(...volumes, 0) > 0;
  const priceBottom = hasVolume ? 222 : 278;
  const volumeTop = 246, volumeBottom = 282;
  const slot = (x1 - x0) / points.length;
  const xAt = index => x0 + (index + 0.5) * slot;
  const lows = points.map(point => number(point.low));
  const highs = points.map(point => number(point.high));
  let priceMin = Math.min(...lows), priceMax = Math.max(...highs);
  const pad = Math.max((priceMax - priceMin) * 0.07, Math.max(Math.abs(priceMax), 1) * 0.006);
  priceMin -= pad;
  priceMax += pad;
  const yPrice = value => priceTop + (priceMax - number(value)) * (priceBottom - priceTop) / (priceMax - priceMin);
  const first = points[0], latest = points[points.length - 1];
  const periodChange = (number(latest.close) / number(first.close) - 1) * 100;
  const unit = short(payload.evidence?.unit ?? payload.options?.unit ?? '', 8);

  text(x0, 20, short(payload.title ?? '行情 K 线图', 18), { 'font-size':15, 'font-weight':500 });
  text(x1, 20, `收 ${format(latest.close)}  区间 ${signed(periodChange)}`, { 'text-anchor':'end', 'font-size':12, 'font-weight':500, fill:periodChange > 0 ? colors.up : periodChange < 0 ? colors.down : colors.neutral });
  text(x0, 40, `${String(first.time ?? '')} - ${String(latest.time ?? '')}${unit ? ` · ${unit}` : ''}`, { fill:colors.muted });
  text(x1, 40, `高 ${format(Math.max(...highs))}  低 ${format(Math.min(...lows))}`, { 'text-anchor':'end', fill:colors.muted });

  const windows = (payload.options?.moving_average_windows ?? []).map(Number).filter(value => [5,10,20,30,60].includes(value)).slice(0, 3);
  const maColors = [colors.amber, colors.blue, colors.purple];
  const closes = points.map(point => number(point.close));
  windows.forEach((windowSize, seriesIndex) => {
    if (closes.length < windowSize) return;
    const latestAverage = closes.slice(-windowSize).reduce((sum, value) => sum + value, 0) / windowSize;
    text(x0 + seriesIndex * 126, 58, `MA${windowSize} ${format(latestAverage)}`, { fill:maColors[seriesIndex], 'font-weight':500 });
  });

  for (let index = 0; index < 5; index += 1) {
    const value = priceMin + (priceMax - priceMin) * index / 4;
    const y = yPrice(value);
    line(x0, y, x1, y);
    text(x1 + 8, y + 4, format(value), { fill:colors.muted });
  }

  const bodyWidth = clamp(slot * 0.58, 2.2, 9.5);
  points.forEach((point, index) => {
    const open = number(point.open), high = number(point.high), low = number(point.low), close = number(point.close);
    const direction = close > open ? colors.up : close < open ? colors.down : colors.neutral;
    const x = xAt(index);
    line(x, yPrice(high), x, yPrice(low), { stroke:direction, 'stroke-width':1.1 });
    const top = Math.min(yPrice(open), yPrice(close));
    const height = Math.max(1.5, Math.abs(yPrice(open) - yPrice(close)));
    rect(x - bodyWidth / 2, top, bodyWidth, height, { fill:direction, 'fill-opacity':close >= open ? 0.2 : 0.86, stroke:direction, 'stroke-width':1 });
  });

  windows.forEach((windowSize, seriesIndex) => {
    const coordinates = [];
    for (let index = windowSize - 1; index < closes.length; index += 1) {
      const average = closes.slice(index - windowSize + 1, index + 1).reduce((sum, value) => sum + value, 0) / windowSize;
      coordinates.push(`${xAt(index).toFixed(1)},${yPrice(average).toFixed(1)}`);
    }
    if (coordinates.length > 1) create('polyline', { points:coordinates.join(' '), fill:'none', stroke:maColors[seriesIndex], 'stroke-width':1.35, 'stroke-linecap':'round', 'stroke-linejoin':'round' });
  });

  if (hasVolume) {
    const volumeMax = Math.max(...volumes);
    line(x0, volumeBottom, x1, volumeBottom);
    text(x0, volumeTop - 7, '成交量', { fill:colors.muted, 'font-weight':500 });
    text(x1, volumeTop - 7, `峰值 ${volumeLabel(volumeMax)}`, { 'text-anchor':'end', fill:colors.muted });
    points.forEach((point, index) => {
      const height = volumes[index] / volumeMax * (volumeBottom - volumeTop);
      const direction = number(point.close) > number(point.open) ? colors.up : number(point.close) < number(point.open) ? colors.down : colors.neutral;
      rect(xAt(index) - bodyWidth / 2, volumeBottom - height, bodyWidth, Math.max(height, 0.7), { fill:direction, 'fill-opacity':0.62 });
    });
  }

  const labelCount = Math.min(5, points.length);
  const used = new Set();
  for (let slotIndex = 0; slotIndex < labelCount; slotIndex += 1) {
    const index = Math.round(slotIndex * (points.length - 1) / Math.max(labelCount - 1, 1));
    if (used.has(index)) continue;
    used.add(index);
    const raw = String(points[index].time ?? '');
    text(xAt(index), 312, raw.length >= 10 ? raw.slice(5, 10) : raw, { 'text-anchor':'middle', fill:colors.muted });
  }

  const hover = create('g', { display:'none', 'pointer-events':'none' });
  const hoverLine = line(x0, priceTop, x0, hasVolume ? volumeBottom : priceBottom, { stroke:colors.neutral, 'stroke-width':0.9, 'stroke-dasharray':'3 3' }, hover);
  const hoverBox = rect(52, 76, 330, 42, { rx:3, fill:colors.panel, 'fill-opacity':0.96, stroke:colors.grid }, hover);
  const hoverDate = text(62, 92, '', { 'font-weight':500 }, hover);
  const hoverValues = text(62, 109, '', { fill:colors.muted }, hover);
  const overlay = rect(x0, priceTop, x1 - x0, (hasVolume ? volumeBottom : priceBottom) - priceTop, { fill:'transparent', 'pointer-events':'all' });
  const showPoint = event => {
    const bounds = svg.getBoundingClientRect();
    const pointerX = (event.clientX - bounds.left) * 680 / Math.max(bounds.width, 1);
    const index = clamp(Math.floor((pointerX - x0) / slot), 0, points.length - 1);
    const point = points[index];
    const x = xAt(index);
    const boxX = x > 400 ? 52 : 300;
    hover.setAttribute('display', 'block');
    hoverLine.setAttribute('x1', x);
    hoverLine.setAttribute('x2', x);
    hoverBox.setAttribute('x', boxX);
    hoverDate.setAttribute('x', boxX + 10);
    hoverValues.setAttribute('x', boxX + 10);
    hoverDate.textContent = String(point.time ?? '');
    hoverValues.textContent = `开 ${format(point.open)}  高 ${format(point.high)}  低 ${format(point.low)}  收 ${format(point.close)}${finite(point.volume) ? `  量 ${volumeLabel(point.volume)}` : ''}`;
  };
  overlay.addEventListener('pointermove', showPoint);
  overlay.addEventListener('pointerdown', showPoint);
  overlay.addEventListener('pointerleave', () => hover.setAttribute('display', 'none'));
})();
</script>
```

If the template cannot render, use the prepared OHLCV table and text fallback. Do not switch to another chart type unless the evidence itself cannot support a valid K line.
