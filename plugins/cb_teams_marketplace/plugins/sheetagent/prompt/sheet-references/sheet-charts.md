---
name: sheet-charts
description: >
  Chart-type selection, styling defaults, combo & dual-axis, and the minimal-patch rule for
  spreadsheet chart operations. Read before any `newChart` / `setOptions` / `setDataRange` /
  `removeChart` / `getCharts`, or any task that creates, modifies, or removes a chart, or a request
  that implies one: 生成图表 / 画个图 / 柱状图 / 折线图 / 饼图 / 环形图 / 散点图 / 气泡图 /
  雷达图 / 趋势图 / 占比 / 对比图 / 可视化 / 仪表盘 / 图表样式 / 改图; "make / create /
  add a chart / graph / plot"; "visualize / plot this"; a named chart type (bar / line / pie /
  scatter / bubble / radar / stacked / combo / dual-axis); "add a trendline"; "restyle / recolor /
  retitle this chart".
---

# Sheet Charts — Authoritative Guide for All Chart Operations

> **This reference is the single source of truth for chart work in SheetAgent.** You MUST read and follow it before **any** chart action — `newChart` (create), `setOptions` (restyle), `setDataRange` (re-bind), `removeChart` (delete), `getCharts` (inspect). Do **NOT** compose chart parameters from memory: type selection, axis/scale derivation, data-label density, combo-axis binding, and the edit-patch rule all live here, and getting them wrong produces broken or misleading charts (or a failing `run_command`).
>
> Section labels below (§4.3.1.x) are this reference's own sections. References to **§4.1** (tool tiering — charts go through `run_command`), **§5.5 rule 12** (apply styling at creation), and **§7** (the API type reference: `ChartType` enum, `ChartOptions`, `EmbeddedChart`) point to the sheet-agent system prompt, which is always in context alongside this reference.

#### 4.3.1 Charts

##### 4.3.1.0 Choosing the Chart Type (decide BEFORE binding data / styling)

> **The chart type must follow the user's question and the data's shape — not a default.** The single most common failure is reaching for `COLUMN` / `LINE` / `PIE` out of habit when the data calls for something else. Before calling `newChart(...)`, name (1) what the user is trying to *see* (trend? ranking? composition? correlation? comparison across attributes?) and (2) the shape of the source (how many categories, how many numeric dimensions, is the x-axis ordered or categorical, are there negatives). Then pick from the table below.

**Intent → recommended type:**

| What the user wants to see | Data shape | Recommended type | Notes |
|---|---|---|---|
| Trend over time | 1+ numeric series over an **ordered** x (dates / periods) | `LINE` (many points) / `COLUMN` (≤ ~8 discrete periods) | Line for continuity; column when each period is a discrete bucket to compare. |
| **Ranking / Top-N** | one numeric value per category, **sorted** | **`BAR`** (horizontal), sorted descending | This is the classic miss — see below. Use `BAR`, not `COLUMN`. |
| Compare a metric across a few entities | one value per category, unordered | `COLUMN` (short labels) / `BAR` (long labels or > ~8 categories) | Horizontal bar keeps long category names readable. |
| Part-to-whole (share of total) | one series, parts sum to 100%, **few** slices (≤ ~6) | `PIE` / `DOUGHNUT` | For > ~6 categories or any negative value, use a sorted `BAR` instead — pie becomes unreadable. |
| Composition over time — **absolute** | several series stacked per period | `STACKED_COLUMN` / `STACKED_AREA` | Total height = the running total; use when the total itself matters. |
| Composition over time — **share** | several series, want % mix per period | `PERCENT_STACKED_COLUMN` / `PERCENT_STACKED_AREA` | Each period normalised to 100%; use when only the *proportion* matters, not the absolute total. |
| Correlation between **two** numeric variables | x = numeric, y = numeric, no inherent order | **`SCATTER`** | Not `LINE`. `dataRange` = **exactly two** numeric columns (1st → X axis, 2nd → Y axis), nothing else; **both axis titles required** — see §4.3.1.4. |
| Relationship among **three** numeric dimensions | x, y, **and a magnitude** per point | **`BUBBLE`** | The forgotten one — see below. Bubble size encodes the third metric. |
| Compare a few entities across **several attributes** | 3–8 entities × 3–8 metrics on comparable scales | `RADAR` / `MARKER_RADAR` | e.g. comparing 3 products across price / battery / weight / rating. |
| Hierarchical part-to-whole | nested categories with a size each | `TREEMAP` | When there are many categories and a hierarchy, treemap beats a crowded pie. |
| Two metrics with very different magnitudes | e.g. revenue (¥10K) + growth rate (%) | combo on a secondary axis | See §4.3.1.3 — do **not** force both onto one axis. |

**Types the model frequently picks wrong (call these out to yourself before committing):**

- **Top-N → `BAR`, not `COLUMN`.** "Top 10 products by sales", "best-selling regions", "highest-spending customers" are rankings. Use a **horizontal `BAR`** sorted descending: long category names stay readable (column charts rotate/truncate them) and the eye reads a ranking top-to-bottom naturally. Default to `BAR` whenever the request contains "top N / ranking / 排名 / 最高 / 最畅销" **and** category labels are non-trivial.
- **Correlation → `SCATTER`, not `LINE`.** "Is there a relationship between ad spend and revenue?", "price vs units sold" — the x-axis has no natural order, so connecting points with a line is misleading. Use `SCATTER`, bind the `dataRange` to **exactly the two** numeric columns (1st → X, 2nd → Y, no extra columns), and show **both** axis titles — follow the dedicated scatter rules in §4.3.1.4. (There is no native trend line; a `*_SCATTER` smooth/straight variant merely connects the raw points in data order and is **NOT** a regression fit.)
- **Three numeric dimensions → `BUBBLE`.** When the user wants to compare items on **two** metrics *and* weight them by a **third** (e.g. "revenue vs profit-margin, sized by market share", "risk vs return, sized by position size"), `BUBBLE` shows all three at once. The model almost never reaches for it — actively consider it whenever a third per-point magnitude exists. Data shape: 3 numeric columns (x, y, size).
- **Many categories → sorted `BAR`, not `PIE`.** A pie with 10+ slices (or near-equal slices, or any negative value) is unreadable. Switch to a sorted horizontal `BAR`. Reserve pie/doughnut for ≤ ~6 clearly-different parts of a genuine whole.
- **Share-over-time → `PERCENT_STACKED_*`, not `STACKED_*`.** If the user asks "how did the *mix* / *proportion* change over time", normalise to 100% with the percent-stacked variant. Use the plain `STACKED_*` only when the absolute total per period is itself the point.
- **Categorical x → `COLUMN`/`BAR`, not `LINE`.** A line across unordered categories (products, regions) implies a progression that doesn't exist.
- **No native histogram / box-plot.** There is no distribution chart type in the enum. If the user asks for a histogram or distribution, bucket the data into bins yourself (helper column, see the data-source rule below) and render the bin counts as a `COLUMN` chart; state the binning in the summary.

> **Data source — bind to existing cells first; build helper data only as a last resort.** Charts in a workbook are most useful when they read straight from the user's existing data: the user can see the source, edit it, and the chart updates accordingly. Fabricating a parallel "chart-only" table next to the original data clutters the sheet, surprises the user, and means future edits have to be made in two places.
>
> Decide the data source in this order:
>
> 1. **Use the existing data range as-is.** Find the columns/rows that already carry the values the chart needs (often the same range the user pointed at, or the obvious header + data block on the sheet) and pass that `Range` directly to `newChart(..., dataRange, ...)`. This is the default — almost every chart should land here.
> 2. **Trim / extend the range after creation via `chart.setDataRange(newRange)`.** If the initial chart picked up an extra column you didn't want (e.g. an `id` column dragged in alongside `month` + `revenue`), or missed a column the user asked for, do NOT delete the chart and call `newChart` again, and do NOT copy the source data into a fresh "clean" block. Just call `chart.setDataRange(sheet.getRange(...))` once with the corrected range — the rest of the styling (`options`) is preserved. Combined with the "apply styling on creation" rule (§5.5 rule 12), this gives the cheapest "create once, refine in place" loop. For per-series shape changes that `setDataRange` cannot express (e.g. dropping a single series out of a multi-column block), fall back to `removeChart` + a new `newChart(...)` over the narrower range — still do NOT precompute a helper table for this.
> 3. **Only build auxiliary data when the source genuinely cannot serve the chart**, i.e. when ALL of the following are true:
>    - the shape is wrong and not just a column-range trim away (e.g. long-format data when the chart needs wide-format, or vice versa);
>    - or the chart needs an aggregation/derivation that no existing column carries (totals by month, % share, YoY growth, …) AND a formula in the original block isn't acceptable;
>    - or units / number formats in the source would distort the axis and rewriting the source isn't an option.
>
>    When you do create helper data, put it in a clearly named, isolated block (a few cells below or to the right of the source, with a header row stating what it represents), keep it minimal (only the columns the chart binds to), and mention it in the final summary so the user knows the helper cells exist.
>
> ❌ Anti-patterns to avoid:
>
> - Copy-pasting the original data into a "chart data" block just so the chart can read from "clean" cells when the original range was already usable.
> - Pre-aggregating numbers into JS arrays inside `run_command`, writing them into a brand-new cell block, and then pointing the chart at that block — when the same aggregation could be done by passing a wider source range and letting the chart group it, OR by a one-cell formula like `=SUMIFS(...)`.
> - Deleting and re-creating a chart over the "right" data when a single `chart.setDataRange(...)` would have fixed the bind.

- `sheet.newChart(drawingId, chartType, dataRange, anchorRow, anchorCol, offsetX, offsetY, width, height, options?)` — drawingId: string — Unique chart ID (required, generated by the caller); chartType: string — Chart type; dataRange: Range — Data source range; anchorRow: number — Anchor row (0-based); anchorCol: number — Anchor column (0-based); offsetX: number — Horizontal offset in pixels; offsetY: number — Vertical offset in pixels; width: number — Width (≥1); height: number — Height (≥1); options?: `ChartOptions` — chart appearance config (title / axes / legend / series styling / data labels / etc.). **Always pass the complete styling through this parameter at creation time** (see §4.3.1.1); do NOT do "newChart first, then `chart.setOptions(...)`" as two steps — that adds an extra write and shows the user an unstyled intermediate chart. Use `setOptions` **only when modifying an existing chart**. Creates an embedded chart. The drawingId is generated and passed in by the caller; the engine holds this ID for subsequent update/delete operations. Returns EmbeddedChart.
- `sheet.insertChart(chart: EmbeddedChart)` — chart: EmbeddedChart — Chart object. Compatibility interface (the chart is already inserted at newChart time; this method is a no-op).
- `sheet.removeChart(chartId: string)` — chartId: string — The `drawingId` of the chart to delete. Pass the id directly; do **not** pass an `EmbeddedChart` object.

**Example:**

```javascript
// 1. Prepare test data (A1:B5)
const dataRange = sheet.getRange(1, 1, 5, 2);
dataRange.setValues([
    ['Month',    'Sales'],
    ['January',  100],
    ['February', 200],
    ['March',    150],
    ['April',    400],
]);
// 2. Add a chart — pass styling directly to newChart in one call (recommended).
//    Parameters: chartType, dataRange, anchorRow, anchorCol, offsetX, offsetY, width, height, options
//    anchorRow/anchorCol are 0-based anchor positions
const chart = sheet.newChart(
    'chart_001',
    'LINE',                            // Line chart
    sheet.getRange(1, 1, 5, 2),        // Data range A1:B5
    0,                                 // Anchor row (0-based)
    3,                                 // Anchor column (0-based, i.e. column D)
    0,                                 // Horizontal offset
    0,                                 // Vertical offset
    600,                               // Width (pixels)
    400,                               // Height (pixels)
    {                                  // ← options: title / legend / axes all together
      title:  { text: 'Monthly Sales', visible: true,
                textStyle: { bold: true, fontSize: 16 } },
      legend: { visible: true, position: 'BOTTOM', textStyle: { fontSize: 12 } },
    },
);
```

##### 4.3.1.0b Placing a new chart — PROBE existing charts first (HARD RULE)

> **Before choosing `anchorRow` / `anchorCol` for a NEW chart, you MUST call `sheet.getCharts()` and steer the new chart clear of every existing chart.** This is the single most common placement bug: the sheet already contains charts (they are NOT visible in `read_table`, which only shows cell values), the agent hard-codes an anchor like `(0, 9)` / "just right of the data", and the new chart lands **on top of** a pre-existing one. **Once a sheet already holds charts,** "to the right of / below the data" is **NOT** a safe empty area — existing charts are usually parked in exactly those margins.

**Mandatory placement procedure — run every time you create a chart on a sheet that may already hold charts:**

1. **Probe.** Call `const existing = sheet.getCharts();`. Each returned `EmbeddedChart` exposes its top-left anchor via `getAnchorRow()` / `getAnchorCol()` (both 0-based; return `-1` when unknown).
2. **Branch on whether the sheet already holds charts.**
   - **No existing charts (`existing.length === 0`) → keep the repo's original "beside the data" layout.** Nothing is parked in the right/bottom margins yet, so the compact, natural placement is provably safe: anchor the new chart to the **right of the data**, aligned with its top row (`anchorRow = dataTop`, `anchorCol =` first free column just right of the data block, e.g. the original example's `(0, 3)` for an `A1:B5` block). Only make sure you clear the data's own columns — never anchor at column 0 on top of `A1:Bn` — and that the right margin holds no other content (helper blocks, etc.). **Critical when the chart source is only a SUBSET of the table's columns** (e.g. the table spans `A:F` but you charted `A:B` alone): "right of the data" MUST mean right of the **whole table's** last data column (here `F`), NOT right of your source range's last column (`B`) — otherwise the chart anchors on top of the remaining data columns (`C:F`). Base `anchorCol` on the full table's right edge — take it from `read_table` as `end_col - 1` (0-based), or `actual_end_col - 1` when the table is `truncated` (`end_col` is only the VISIBLE edge then); do NOT use `sheet.getLastColumn()` (it returns the usedRange width, often the default column `Z`, and flings the chart far away). **If `read_table` reports another table block to the right of this one, this "beside the data" branch is NOT safe — fall through to the BELOW branch instead.** This restores the pre-change behavior for the common single-chart case.
   - **One or more existing charts (`existing.length > 0`) → place the new chart strictly BELOW everything.** You cannot prove the right/top margin is free (existing charts usually park there and their size may be unknown — `getHeight()` returns `-1` when a chart carries no explicit size), so compute two independent lower bounds and take the max:
     - **Data bottom.** Never place the chart on top of its own source data. Take the data block's last row as one lower bound (still compute it explicitly even in this branch).
     - **Existing charts' bottom.** For each existing chart estimate its bottom row `getAnchorRow() + span`, where `span = Math.ceil(getHeight() / 20)` when the size is known (`getHeight() > 0`), else a fixed `CHART_ROW_SPAN`. The fallback **must cover the tallest default chart**: a ~300–480px chart spans 15–24 rows, so use `CHART_ROW_SPAN ≥ 24` **plus a gutter — NOT 18** — otherwise the new chart can still land inside a size-unknown chart (e.g. a 400px/20-row chart at `A24`).
     - `anchorRow = max(dataBottom, lowestChartBottom) + 1 + gutter`. The `+ 1` is mandatory and NOT optional styling: `dataBottom` / `lowestChartBottom` are **inclusive** 0-based bottom rows (the last row the data/chart still occupies), so `+ 1` steps to the first genuinely free row below them, and only then does `gutter` add the visible gap. This matches the example code's `+ GUTTER + 1`; if you copy the formula without the `+ 1` the new chart lands one row too high and can clip the row below the data/chart. In this below-branch keep `anchorCol` aligned with the data block (column 0), not a guessed "free" column to the right.
     - **Unknown anchor → conservative degrade, never silently ignore.** If any existing chart returns `getAnchorRow() === -1` you cannot prove where it ends; do **not** drop it from the calculation (that pretends it is absent and breaks the "collision-free" guarantee). Instead push the new chart an extra full `CHART_ROW_SPAN` below the computed bottom so you still clear it.

> **Size caveat.** An existing chart's anchor AND its size can each be missing: `getAnchorRow()` returns `-1` when the chart has no upstream location, and `getHeight()` returns `-1` when the chart carries no explicit size (a one-cell-anchor chart normally reports real px; a two-cell-anchor / size-less one does not). So don't assume either is present — estimate bottoms with row-spans, never exact rectangles, and when a getter returns `-1` degrade instead (the `anchorUnknown` path for a missing anchor; fall back to `CHART_ROW_SPAN` for a missing height). (Charts you create yourself in the same script always carry the anchor/size you passed, so both are exact for those.)

```javascript
const sheet = SpreadsheetApp.getActiveSheet();

// The source-data block for the new chart (A1:B5 in this example).
const dataRange = sheet.getRange(1, 1, 5, 2);

// 1. Probe existing charts BEFORE deciding where to put the new one.
const existing = sheet.getCharts();

const ROW_PX = 20;                               // default row height (px)
const GUTTER = 4;                                // blank rows kept as a visible gap (below-branch)
const COL_GUTTER = 1;                            // blank column between data and chart (right-branch)
// Fallback span MUST cover the tallest default chart (~480px ≈ 24 rows), so that
// when a chart's size is unknown (getHeight() === -1, no explicit size) we never land inside it.
const CHART_ROW_SPAN = 24;

// 0-based extents of the data block.
const dataTop = dataRange.getRow() - 1;
const dataRight = dataRange.getColumn() - 1 + dataRange.getNumColumns() - 1; // last column of the CHART SOURCE range (0-based)
// Right edge of the WHOLE data-table block (0-based), NOT just the chart's source range
// (see prose above for why a subset-column chart must clear the full table). Fill it from
// read_table: end_col - 1, or actual_end_col - 1 when truncated. Never sheet.getLastColumn().
// If your source range already IS the full table, tableRight === dataRight.
const tableRight = dataRight; // ← REPLACE with (end_col - 1) of THIS table from read_table (e.g. 5 for an A:F table); use (actual_end_col - 1) when truncated

let anchorRow, anchorCol;

if (existing.length === 0) {
  // No pre-existing chart → keep the repo's ORIGINAL "beside the data" layout: anchor to the
  // right of the data, aligned with its top row, past the FULL table's right edge (tableRight)
  // so a subset-column chart never lands on the other data columns.
  anchorRow = dataTop;
  anchorCol = Math.max(dataRight, tableRight) + COL_GUTTER + 1;  // first free column just right of ALL data (→ col 3 / D for A1:B5; col 7 / H for an A:F table)
} else {
  // Sheet already holds charts → go strictly BELOW everything (right/bottom margins
  // may already be occupied and sizes may be unknown, getHeight() === -1 when no explicit size).
  anchorCol = 0;                                 // align with the data block, not a guessed "free" column

  // 2a. Data bottom (0-based). The new chart must never cover its own source data.
  const dataBottom = dataRange.getRow() + dataRange.getNumRows() - 2;

  // 2b. Existing charts' bottom. If ANY anchor is unknown we cannot prove where that
  //     chart ends, so flag it and degrade conservatively instead of ignoring it.
  let anchorUnknown = false;
  const chartBottoms = existing
    .map(c => {
      const a = c.getAnchorRow();
      if (a < 0) { anchorUnknown = true; return -1; }   // position unknown → flag, DON'T drop
      const h = c.getHeight();                            // px, or -1 when unknown
      const span = h > 0 ? Math.ceil(h / ROW_PX) : CHART_ROW_SPAN;
      return a + span;                                    // estimated bottom row (0-based)
    })
    .filter(r => r >= 0);
  const chartBottom = chartBottoms.length ? Math.max(...chartBottoms) : -1;

  // 2c. Base anchor = below whichever is lower (data or the lowest known chart).
  anchorRow = Math.max(dataBottom, chartBottom) + GUTTER + 1;
  // Conservative degrade: some existing chart's position is unknown → drop one extra
  // full chart span so we still clear it even if it sits at the current bottom.
  if (anchorUnknown) anchorRow += CHART_ROW_SPAN;
}

const chart = sheet.newChart(
  'chart_new_001',
  'COLUMN',
  dataRange,
  anchorRow,                                     // computed, collision-free anchor
  anchorCol,
  0, 0, 600, 400,
  { title: { text: 'New Chart', visible: true } },
);
```

##### 4.3.1.0c Deleting a chart — pass the `chartId` directly

> **Delete a chart by calling `sheet.removeChart(chartId)`** with the `drawingId` string you used at
> `newChart` time. `removeChart` accepts **only** a chart id string — it does **not** take an
> `EmbeddedChart` object. There is no need to call `getCharts()` first if you already know the id.
>
> **NEVER call `newChart(existingDrawingId, ...)` to "get a reference" to a chart you intend to delete.**
> `drawingId` must be **unique** at creation; reusing an existing id with `newChart` conflicts in the
> backend (the engine already holds that id for the live chart) — the script will fail at `addChart`
> and never reach `removeChart`. `newChart` is for **creating** a chart only.

```javascript
const sheet = SpreadsheetApp.getActiveSheet();

// Delete by chartId (the drawingId you passed to newChart):
sheet.removeChart('chart_001');
```

> If you don't know the id, look it up first via `getCharts()` (match by `getDrawingId()` /
> `getTitle()` / index) and then pass the matched chart's `getDrawingId()`:
>
> ```javascript
> const charts = sheet.getCharts();
> const target = charts.find(c => c.getTitle() === 'Monthly Sales');
> if (target) sheet.removeChart(target.getDrawingId());
> // If charts is empty / no match, there is nothing to delete — do NOT fabricate a chart to remove.
> ```
>
> To delete **every** chart on the sheet:
> `sheet.getCharts().forEach(c => sheet.removeChart(c.getDrawingId()));`.

##### 4.3.1.1 Chart Styling Recommendations

> Default-styled charts often look bare (no title, no legend). The recommendations below
> should be **passed in the `options` argument of `newChart(...)` in a single call** — do NOT do
> "create a default chart first, then call `chart.setOptions({...})` to style it" as two steps:
> that adds an extra write, shows the user an unstyled intermediate chart, and risks leaving an
> "ugly half-finished chart" if the flow is interrupted. Reserve `setOptions` for **modifying an existing chart**.
> Even when the user did not explicitly specify title / legend details, fill in the reasonable defaults below — do not skip them.

> **Series colors** — do NOT set `series[i].color` by default. Let the platform apply its built-in palette so charts stay visually consistent with the workbook's theme. Only set colors when the user explicitly asks for a specific palette / brand color / per-series color mapping. If you do set them, use `#RRGGBB` (not CSS names like `'red'` / `'blue'`).

**Font defaults (per sub-block, REQUIRED)** — there is **no chart-level default `textStyle`**; the backend ignores any `textStyle` at the top level of `options`. Every sub-block that has visible text MUST carry its own `textStyle.fontSize`, otherwise that text falls back to the platform's bare default (which doesn't match the rest of the workbook).

- Sub-blocks that need an explicit `textStyle`: `title.textStyle` / `legend.textStyle` / `xAxis.textStyle` / `yAxis.textStyle` / `yAxis.title.textStyle` (and `secondaryYAxis.title.textStyle` when the secondary y-axis title is enabled) / `series[i].dataLabel.textStyle`. **Note**: at chart-creation time (`newChart`) the x-axis title is never configured (see §4.3.1.1 Axes), so do NOT emit `xAxis.title.textStyle` then — **except for `SCATTER`, where both the x-axis title and its `textStyle` ARE required at creation (§4.3.1.4).** If the user later explicitly asks to add an x-axis title via `setOptions`, send a minimal patch `{ xAxis: { title: { text: ..., visible: true, textStyle: { bold: true, fontSize: 12 } } } }` — see §4.3.1.2.
- Recommended sizes (establish the hierarchy: title > axis title > body > tick / data label):
  - **Title**: `{ bold: true, fontSize: 16 }`
  - **Axis title** (`yAxis.title.textStyle` / `secondaryYAxis.title.textStyle` — and `xAxis.title.textStyle` if the user explicitly asks for an x-axis title later via `setOptions`): `{ bold: true, fontSize: 12 }`
  - **Legend**: `{ fontSize: 12 }`
  - **Tick labels** (`xAxis.textStyle` / `yAxis.textStyle`): `{ fontSize: 11 }`
  - **Data label** (`series[i].dataLabel.textStyle`): `{ fontSize: 11 }` (range 10–11)
- **Color** stays at the platform default (black); do not set `textStyle.color` unless the user asks.

**Title** — one sentence telling the user "what they're looking at": include the time / object / scope.

- The text should be informative (e.g. `'2025 Q1 Channel Revenue Share'`); avoid placeholders like `'Chart1'` / `'Chart'` / `'Visualization'`.
- `textStyle: { bold: true, fontSize: 16 }`; default color is black (no need to set `textStyle.color` explicitly). The bold + larger size makes the title stand out above body text.
- `visible` defaults to `true`. `overlay: true` (title overlaid on the plot area) is only for very tight layouts — it covers data, so do not enable it by default.

```javascript
{
  title: {
    text: '2025 Monthly Revenue by Product Line',
    visible: true,
    textStyle: { bold: true, fontSize: 16 },
  },
}
```

**Legend** — required for multi-series, optional for single-series.

- Multi-series (≥2): `visible: true` is required, otherwise the user cannot tell which color maps to which series.
- Single-series: the legend is just dead space; set `visible: false` and let the title carry the meaning.
- **Default `position`: `'BOTTOM'` for ALL chart types** (column / bar / line / area / scatter / pie / doughnut / radar). Bottom keeps a consistent layout across the workbook and leaves the most horizontal space for the plot area. Only switch to `'RIGHT'` when the legend has many entries (typically a pie / doughnut with 8+ categories) and `'BOTTOM'` would wrap into 3+ rows, or when the user explicitly asks for a side legend.
- `textStyle: { fontSize: 12 }` (body size) — always set explicitly; there is no chart-level fallback, omitting it makes the legend render at the platform's bare default.
- `overlay: true` puts the legend on top of the data; **do not enable by default**.

```javascript
{
  legend: {
    visible: true,
    position: 'BOTTOM',          // default for all chart types
    textStyle: { fontSize: 12 },
  },
}
```

**Axes** (`xAxis` / `yAxis`) — directly affect read-accuracy of the chart.

- **Axis titles**:
  - **`xAxis.title` — do NOT configure on chart creation (`newChart`).** The x-axis carries categorical labels (month names, product names, region codes, dates, IDs, …) that already speak for themselves; auto-adding an `xAxis.title` block at creation time just duplicates content and crowds the plot area. So when calling `newChart(...)`, omit the `xAxis.title` block entirely (no `text`, no `visible`, no `textStyle`).
  - **Exception — `SCATTER` charts.** A scatter's x-axis is a numeric VALUE axis with no self-describing labels, so its x-axis title is required and MUST be set at creation (with `textStyle: { bold: true, fontSize: 12 }`). This is the one chart type where you emit `xAxis.title` in the `newChart` call — see §4.3.1.4.
  - **Exception — explicit user request on an existing chart.** If the user *explicitly* asks you to add / change / remove an x-axis title on a chart that already exists (e.g. *"add an x-axis title 'Month'"*), send a minimal `setOptions` patch with just the `xAxis.title` block (`text`, `visible: true`, `textStyle: { bold: true, fontSize: 12 }`) — see §4.3.1.2. Do **not** invent an `xAxis.title` on your own initiative — only do it when the user explicitly asks.
  - **`yAxis.title.text` — required** when the column header is an abbreviation or units are not explicit (e.g. `"Revenue ($)"`, `"GMV ($M)"`, `"DAU"`); may be omitted when the column header is already self-explanatory. Same rule applies to `secondaryYAxis.title.text` in combo charts.
- **`numberFormat`**: almost always set on the y-axis — percent `'0.00%'` / currency `'$#,##0'` / thousands `'#,##0'`. Without it, long numbers like `1234567` will squeeze the x-axis.
- **`scale.min` / `scale.max` — MUST be derived from the actual data range** (never leave empty, never hard-code a guess). Workflow runs **before** `newChart(...)`:
  1. **Scan the source column(s)** the y-axis is bound to. Small/medium data: read via `get_cell_ranges` and compute `actualMin` / `actualMax` in the model. Large data (>2000 cells): compute inside `run_command` with `Math.min(...col)` / `Math.max(...col)` and return the pair.
  2. **`scale.max`** = `actualMax` rounded UP by ~5% and snapped to a clean step (1 / 5 / 10 / 50 / 100 / 0.05 / 0.5 / … pick by magnitude). Example: `actualMax = 478` → `max: 500`; `actualMax = 0.34` → `max: 0.40`.
  3. **`scale.min`** depends on chart type + sign of the data:
     - **Column / bar / stacked column / stacked bar / area / stacked area** → **hard-code `0`** (basic data-viz rule; non-zero baselines on a bar chart visually exaggerate differences and mislead the reader). Skip the data-driven `min` here.
     - **Line / scatter / marker line / radar, data all non-negative**:
       - If `actualMin ≤ actualMax * 0.5` (data spans from near-zero up to max) → `min: 0`.
       - Otherwise (data clustered in a narrow upper band) → `actualMin` rounded DOWN by ~5%, snapped to a clean step. Example: `actualMin = 322`, `actualMax = 478` → `min: 300, max: 500`.
     - **Data crosses zero** (some negatives, some positives) → `actualMin` rounded DOWN by ~5% (more negative), snapped to a clean step. Example: `actualMin = -0.18, actualMax = 0.34` → `min: -0.20, max: 0.40`.
  4. **Forbidden defaults**: ❌ omitting `scale` and relying on the platform's auto-fit (tick spacing becomes unstable and inconsistent across charts); ❌ hard-coding guessed values like `max: 100` / `max: 1000` / `max: 10000` without scanning data (real data above the cap gets clipped; real data far below makes the chart look flat).
- **`gridlines`**: turn on for the **primary** y-axis (`yAxis.gridlines: true`) — helps eyeballing values horizontally; default off for the x-axis (column width already separates categories — extra vertical lines look noisy). **Default off for the secondary y-axis (`secondaryYAxis.gridlines: false`)** — two sets of horizontal gridlines from primary + secondary overlap and clash, leaving the plot area visually noisy. Always emit `secondaryYAxis.gridlines: false` explicitly when configuring a combo chart with a secondary axis; do not rely on the fallback.
- **`textStyle`**: tick labels at `{ fontSize: 11 }`; axis title at `{ fontSize: 12, bold: true }`. Always set tick-label `textStyle` explicitly — there is no chart-level fallback, omitting it makes the axis render at the platform's bare default. Axis-title `textStyle` is only emitted when that axis title itself is enabled — by default that means `yAxis.title` (and `secondaryYAxis.title` in combo charts); the x-axis title is normally off at creation time, and its `textStyle` only needs to be set if the user later explicitly asks to enable it via `setOptions`.
- **`xAxis.type` is NOT a configurable field** (no `'CATEGORY'` / `'VALUE'` / `'DATE'` switching). The backend rejects axis-type changes with `xAxis.type switching (CATEGORY / VALUE / DATE) is not supported` and the whole `run_command` fails. The x-axis type is **inferred from the source column's data type at chart creation** (text → CATEGORY, numbers → VALUE, dates → DATE), and is **immutable** after creation. To change it, you must rebuild the source data (e.g. convert a text column of date-looking strings into real dates via cell `numberFormat` + `value`), then re-create the chart with `newChart(...)`. Do NOT emit `xAxis.type` in either `newChart` options or `setOptions` patches.

```javascript
// Assume a column chart over revenue data; source data scan: actualMin=120, actualMax=478.
//   yAxis.scale.min: 0      (column chart → hard-coded 0)
//   yAxis.scale.max: 500    (ceil(478 * 1.05) snapped to nearest 50)
{
  // At creation time, do NOT emit `xAxis.title` (see Axis titles rule above).
  // Only add it later via setOptions if the user explicitly asks.
  xAxis: {
    gridlines: false,
    textStyle: { fontSize: 11 },
  },
  yAxis: {
    title: { text: 'Revenue ($)', visible: true, textStyle: { fontSize: 12, bold: true } },
    numberFormat: '#,##0',
    scale: { min: 0, max: 500 },
    gridlines: true,
    textStyle: { fontSize: 11 },
  },
}
```

**Data labels** (`series[i].dataLabel`) — write the value directly on the data point; decide which flags to enable based on density + chart type.

**MANDATORY preflight before emitting any `series[i].dataLabel` block** — count data rows first, then decide. Do not decide from chart size, aesthetics, font size, or label position.

```javascript
const pointsPerSeries = dataRangeRows - headerRows; // usually: dataRangeRows - 1
const isPieLike = chartType === 'PIE' || chartType === 'DOUGHNUT';
const enableDataLabels = isPieLike || pointsPerSeries <= 9;
```

If `enableDataLabels` is `false`, you MUST NOT emit `dataLabel.visible: true`. Either omit the `dataLabel` block entirely, or emit the explicit disabled form:

```javascript
series: [{ dataLabel: { visible: false } }]
```

For example, `sheet.getRange(1, 10, 12, 2)` used for a `BAR` chart has 1 header row + 11 data rows, so it is **11 points/series**. Because it is not pie-like, data labels MUST be disabled.

- **Whether to enable** — judged by **data points per series after excluding header rows**, not total points across the chart. Count first, then decide:
  - **Pie / doughnut — ALWAYS enable.** Regardless of the number of slices, pie and doughnut charts must always have `dataLabel.visible: true`. The density rule below does NOT apply to pie / doughnut.
  - **≤ 9 points/series** → enable (the user reads values at a glance, no need to consult the y-axis).
  - **≥ 10 points/series** → **MUST disable** (except pie / doughnut — see above). This is a hard stop for non-pie-like charts: do not emit `dataLabel.visible: true`, and do not try to rescue it by shrinking `fontSize`, changing `position`, or making the chart wider. To disable, either set `dataLabel.visible: false` or omit the `dataLabel` block entirely.
  - **Multi-series rule**: if **any** series in the chart has ≥ 10 points, disable data labels for **every** series — mixing labeled and unlabeled series in the same chart looks inconsistent. (This rule does not apply to pie / doughnut, which always keep labels enabled.)
- **Default: enable exactly ONE `show*` flag.** Stacking multiple flags (e.g. `showValue` + `showCategoryName`, or `showValue` + `showPercentage`) crowds the label and rarely improves readability. Pick one based on chart type:
  - Column / bar / line / area: only `showValue: true`, paired with `numberFormat` (the data label has its own format, independent of the y-axis `numberFormat`).
  - Pie / doughnut: only `showCategoryName: true`. Category names directly on each slice make the chart self-explanatory without consulting the legend.
- **The four `show*` flags are mutually exclusive — set exactly one to `true` and explicitly emit the other three as `false`.** Do not rely on omission. The four flags are `showValue`, `showPercentage`, `showCategoryName`, `showSeriesName`; pinning the unused three to `false` makes intent explicit across hosts and prevents the platform from picking up a different default. In particular, when switching a chart to pie/doughnut, set `showCategoryName: true` and explicitly set `showValue: false`, `showPercentage: false`, `showSeriesName: false`. Only flip `showPercentage` or `showValue` to `true` when the user explicitly asks for it.
- **`position`** — default is **outside the data point** so the label never overlaps the marker / bar / slice. Pick by chart type:
  - Column / bar: `'OUTSIDE_END'` (just above the bar).
  - Line / area: `'ABOVE'` (above the marker).
  - Pie / doughnut: `'INSIDE_END'` (inside the slice). Only fall back to `'OUTSIDE_END'` or `'BEST_FIT'` when there are many small slices and inside labels visibly collide or are unreadable.
- **`textStyle.fontSize`**: 10–11; larger sizes squeeze the plot area. Always set this explicitly — there is no chart-level fallback, omitting it makes the data label render at the platform's bare default.

```javascript
{
  series: [
    {
      // No `color` here — let the platform apply its default palette.
      dataLabel: {
        visible: true,                    // ≥ 10 points/series: set to false (or omit the whole dataLabel block). Pie/doughnut: ALWAYS true.
        // Exactly one show* flag is true; the other three must be explicitly false.
        showValue: true,                  // pie/doughnut: set to false
        showPercentage: false,            // pie/doughnut: keep false (unless user asks)
        showCategoryName: false,          // pie/doughnut: set to true
        showSeriesName: false,
        position: 'OUTSIDE_END',          // line/area: 'ABOVE'; pie/doughnut: 'INSIDE_END'
        numberFormat: '#,##0',
        textStyle: { fontSize: 11 },
      },
    },
  ],
}
```

**Size & position** — don't crowd, don't overlap.

- Default size: `720 × 420`
- Single-series pie chart: `480 × 360`
- **MANDATORY pre-flight for EVERY chart — validate the whole rectangle, then make room if needed.** Before any `newChart(...)`, treat the chart as the rectangle from its anchor cell spanning `width` px to the right and `height` px down, and verify that **the entire rectangle — every row and column it covers, in both directions — lies inside the sheet's existing used range.** It is not enough for the anchor cell to be valid: a chart whose anchor is fine but whose width/height spill past the last used column or row still fails to render (the same silent bug — `run_command` "succeeds" but no chart appears). This applies **no matter where you place the chart** — right of the data *or* below it. A wide chart anchored below at column A still spans many columns to the right and can spill past the last used column. To check the rectangle, read the real `sheet.getColumnWidth(col)` / `sheet.getRowHeight(row)` (see the footprint rule below for the fallback when they return 0). **If any part of the rectangle falls outside the used range, insert enough rows/columns to extend the sheet first, then create the chart.** Never emit a `newChart(...)` whose rectangle is not fully contained.
- **Used range means the whole sheet's current used rectangle, NOT the source data range.** When the user says "create a chart from `A1:C20`" on a sheet whose resolved metadata says `sheet_cols=26`, the horizontal boundary is the sheet's total used range (A:Z), not the selected data range (A:C). If the default chart rectangle anchored to the right of the source data fits inside that total used range, **do NOT insert columns**. Example: source `A1:C20`, default anchor at column D, default width roughly spans D:K; if the sheet already has 26 used columns, D:K is inside A:Z, so create the chart directly without `insertColumns`.
- **Default: anchor to the right of the data** — `anchorRow=0, anchorCol=<dataColumns + 1>`. This is the preferred placement; charts read naturally next to their source data. Never anchor directly on top of the data. If the right side currently lacks room **relative to the whole sheet's used range** (the anchor would fall past the sheet's last used column, or the chart's footprint would spill past that last used column — see the next two rules), the default is **not** to give up and go below: it is to **insert columns to make room and keep the chart on the right**. If the footprint already fits inside the whole sheet's used range, do not insert columns merely because the source data range ends earlier. Only fall back to placing the chart below the data in the narrow exceptions spelled out below (**or when the sheet already holds charts that occupy the right/bottom margin — see §4.3.1.0b, which takes precedence and requires going below to avoid overlapping them**).
- **NEVER anchor a chart at a column/row that falls outside the sheet's existing used range.** This is a hard rule — anchoring past the last existing column (or row) makes the chart fail to render entirely (a serious, silent bug; the `run_command` "succeeds" but no chart appears). The common trap: a 5-column table whose data fills **all 5** columns (A–E) — `anchorCol = dataColumns + 1` then points at column F, which does not exist in the sheet, so the chart never shows. When the data fills the sheet to its right edge, the default right-side anchor (`dataColumns + 1`) lands outside the used range. **Do NOT silently drop the chart below the data to dodge this — that is the wrong reflex.** The required default is to **keep the chart on the right by making room first**:
  1. **(DEFAULT — do this only when the full footprint would exceed the whole sheet used range) Insert enough empty columns just past the data first, then anchor right.** Use `sheet.insertColumns(col, numCols)` (1-based `col`; inserts *before* `col`) to append empty columns immediately to the right of the data — pass `col = <last data column + 1>` so the new columns extend the used range without shifting any existing data. Add **enough** columns to cover the chart's full footprint (compute the span per the next rule). **Give the new columns the same width as the column they follow:** read `sheet.getColumnWidth(<last data column>)` and apply it to the inserted columns with `sheet.setColumnWidths(<first new column>, numCols, <that width>)`, so the added space matches the existing layout and the footprint math stays consistent (skip this only if the read returns `0`, i.e. dimensions are unavailable). *Then* `newChart(...)` anchored on the right as usual (`anchorCol = <dataColumns + 1>`). This is mandatory whenever you would otherwise anchor past the whole sheet used range, but **forbidden when the chart rectangle already fits inside the whole sheet used range** — do not insert columns just because the selected source range is narrower than the sheet.
  2. **(EXCEPTION — only when right placement is truly impossible)** Anchor below the data — `anchorRow = <dataRows + 2>, anchorCol = 0`. Use this **only** when (a) the user explicitly asked you not to alter the table's column structure, (b) the data already extends to the sheet's maximum column, or (c) **the sheet already holds one or more charts occupying the right/bottom margin — in that case §4.3.1.0b governs and mandates placing the new chart below everything (using its `max(dataBottom, lowestChartBottom)+gutter` formula rather than the fixed `dataRows + 2` here) to avoid overlapping them.** Reaching for "below" merely because it avoids the insert step is **not** an acceptable reason. **Even when anchoring below, the mandatory pre-flight still applies horizontally:** a wide chart at column A spans many columns to the right, so if its width spills past the last used column you must still insert columns to extend the used range first — "below" escapes the *vertical* edge, not the horizontal one.
  The same applies to the row direction: if the data fills the sheet to its bottom edge, either insert rows first or anchor to the right of the data. When you insert rows to make room, **give the new rows the same height as the row they follow** — read `sheet.getRowHeight(<last data row>)` and apply it via `sheet.setRowHeights(<first new row>, numRows, <that height>)` (skip only if the read returns `0`). Check the actual used range before choosing the anchor — do not assume the sheet has spare columns/rows beyond the data.
- **Before creating a chart, check that there is enough room to hold the *whole* chart, not just its anchor cell.** A chart of `width × height` pixels spans many rows and columns, so its full footprint — not just the anchor cell — must fit inside the sheet. To compute that footprint, **read the actual column widths / row heights** rather than guessing: walk outward from the anchor with `sheet.getColumnWidth(col)` and `sheet.getRowHeight(row)` (both return pixels) and accumulate until you cover the chart's `width` / `height`; that tells you the real last column/row the chart will occupy. **Caveat:** these can return `0` when the upstream dimension tool is unavailable — treat `0` as "unknown" and fall back to the platform defaults (**column ≈ 100px, row ≈ 20px**, so a `720 × 420` chart covers roughly **8 columns × 21 rows**). If the space remaining from the chosen anchor to the sheet's edge is too small to contain that footprint, **insert enough rows/columns first** to make room, then create the chart. Never create a chart that would extend past the sheet's bounds.

**Common pitfalls to avoid:**

- Blindly anchoring at `anchorCol = dataColumns + 1` when the data already fills the sheet's last existing column → the anchor lands outside the used range and the chart silently fails to render. The fix is to **insert columns first, then anchor right** (the default) — *not* to silently drop the chart below the data. Going "below" is only allowed in the narrow exceptions in "Size & position" above, or to avoid overlapping charts the sheet already contains (§4.3.1.0b).
- Emitting `xAxis.type` (`'CATEGORY'` / `'VALUE'` / `'DATE'`) in **either** `newChart` options or a `setOptions` patch → the backend rejects this with `xAxis.type switching (CATEGORY / VALUE / DATE) is not supported` and the entire `run_command` fails. The x-axis type is inferred from the source column's data type at creation time and is immutable. To change it, rebuild the source column (fix its `numberFormat` / `value`) and re-create the chart with `newChart(...)`.
- Emitting an `xAxis.title` block in a `newChart(...)` call when the user did **not** explicitly ask for one → at chart-creation time the x-axis title must be omitted (no `text`, no `visible`, no `textStyle`); see §4.3.1.1 Axes. Adding it later via `setOptions` is allowed **only** when the user explicitly asks for an x-axis title on an existing chart.
- Leaving `secondaryYAxis.gridlines` at its default (or copying `yAxis.gridlines: true` over) when the chart has a secondary y-axis → primary + secondary horizontal gridlines overlap and clash. Always emit `secondaryYAxis.gridlines: false` explicitly in combo charts with a SECONDARY axis.
- Setting `textStyle` at the **top level of `options`** → the backend ignores it (there is no chart-level default). Put `textStyle` on each visible sub-block instead: title 16/bold, y-axis title 12/bold, legend 12, tick label 11, data label 10–11.
- Omitting `textStyle` on `legend` / `xAxis` / `yAxis` (tick labels) / `series[i].dataLabel` and assuming a chart-level fallback → there is none, those sub-blocks will fall back to the platform's bare default. Always set each block's own `textStyle.fontSize` per the recommended sizes above.
- Leaving `dataLabel.visible: true` on a chart whose series has **10 or more data points** → labels overlap into an unreadable blob; you **must** turn them off (`visible: false` or omit `dataLabel`). Shrinking `fontSize` or changing `position` does not fix this. **Exception: pie / doughnut charts always keep `dataLabel.visible: true`** regardless of slice count.
- Wrong: using `sheet.getRange(1, 10, 12, 2)` for a `BAR` ranking chart (1 header row + 11 data rows), then emitting `dataLabel.visible: true`. Right: this is **11 points/series**, so emit `series: [{ dataLabel: { visible: false } }]` or omit `dataLabel`.
- Stacking multiple `show*` flags on a data label by default (`showValue` + `showCategoryName`, `showValue` + `showPercentage`, etc.) → labels get crowded; pick exactly one unless the user explicitly asks for more. For pie / doughnut the default single flag is `showCategoryName: true` (not `showPercentage`).
- Omitting `scale` on `yAxis` / `secondaryYAxis` and relying on the platform's auto-fit → tick spacing becomes unstable and inconsistent across charts. Always derive `scale.min` / `scale.max` from the data via the workflow in §4.3.1.1 Axes (scan `actualMin` / `actualMax`, round, snap to a clean step).
- Hard-coding `scale.max` / `scale.min` without scanning the source data (e.g. always writing `max: 100` / `max: 1000` because it "looks round") → real data above the cap gets clipped, real data far below the cap makes the chart look flat. Scan first, then compute.
- Column / bar / area / stacked-* chart with `yAxis.scale.min` set to a non-zero value → visually exaggerates the difference; this category is the ONE exception to the "data-driven `min`" rule — always hard-code `0`.
- Setting `series[i].color` by default (rather than letting the platform palette apply) → only set colors when the user explicitly asks. If you do, use `#RRGGBB`, never CSS names like `'red'` / `'blue'`.
- **Scatter `dataRange` wider than two columns, or missing axis titles** → a scatter's `dataRange` MUST be exactly two columns (1st → X, 2nd → Y); a 3rd column (fitted/trend, `id`, a second metric) makes the chart come out wrong. It MUST also emit both `xAxis.title` and `yAxis.title` at creation (the one chart type that does). There is no native trend line — do not fake one with an extra column, a `trendline` option (ignored), or a `*_SCATTER` line variant. See §4.3.1.4.
- Doing a `getOptions() → spread-merge full options → setOptions(merged)` round-trip on an existing chart → `setOptions` is already a per-field deep-merge on the backend, so the round-trip is **unnecessary** AND **lossy**: `getOptions()` only reflects a subset of the underlying chart proto, and re-sending any sub-block that carries `textStyle` triggers side effects (forces `body_pr.anchor_ctr=false`; clears run-level rich-text `r_pr` set through the chart UI). Always send a minimal patch with only the fields you want to change — see §4.3.1.2.

##### 4.3.1.2 Modifying an Existing Chart — Send a Minimal Patch (HARD RULE)

`chart.setOptions(opts)` is a **per-field deep-merge** on the backend, NOT a whole-config replace. Only the keys you explicitly include in the payload are written to the underlying chart model; every field you omit (legend / axes / data labels / series styling / …) is preserved verbatim. Concretely:

- **Top-level objects** (`title` / `legend` / `xAxis` / `yAxis` / `secondaryYAxis` / `series` / …): merged by key — omitting one keeps it intact.
- **Nested objects** (e.g. `legend.textStyle`, `yAxis.scale`): also merged by field — sending `{ legend: { textStyle: { fontSize: 12 } } }` only writes `fontSize`, it does NOT clear `bold` / `color` / `fontFamily`.
- **`series` array**: merged **by index** on the backend — only the per-series fields the backend writes (`color` / `dataLabel`) are touched; other series-level fields are untouched. (Note: the local TS shim treats arrays as replace for its own cache, but the on-disk model still follows the per-index merge on the backend.)

**HARD RULE — send only the fields you want to change.** Do NOT do a `getOptions() → spread-merge full options → setOptions(merged)` round-trip. That pattern is unnecessary (the deep-merge is already on the backend) AND introduces **non-symmetric side effects**, because `getOptions()` only reflects a subset of the underlying OOXML model while `setOptions()` re-writes a few "hard-coded" fields whenever a sub-block is touched:

- Sending **any** `textStyle` block forces `body_pr.anchor_ctr = false` on the corresponding text body, regardless of its previous value.
- Sending `title.textStyle` / `xAxis.title.textStyle` / `yAxis.title.textStyle` (etc.) clears the run-level `r_pr` fields (`bold` / `italic` / `fontSize` / `fontFamily` / `color`) that were set through the chart UI — even if `getOptions()` did not surface them.
- A few other proto-only fields (numbering, sizing, hidden flags) are not reflected by `getOptions()` either, so "round-trip" is provably lossy.

**The correct pattern is the inverse of read-merge-write: send a flat patch with exactly the changed leaves.**

**Default for missing `fontSize`** — When you patch a sub-block that did NOT carry an explicit `textStyle.fontSize` before (legacy chart, or that sub-block was never styled), include `fontSize` in the same patch so the result is not left at the platform's bare default. Use the recommended hierarchy from §4.3.1.1 (title 16/bold, axis title 12/bold, legend 12, tick label 11, data label 10–11) when the recommended size for that sub-block is unambiguous; otherwise default to **`12`**. Do NOT pre-read `getOptions()` just to learn the existing `fontSize` — picking a sensible default per the hierarchy is sufficient and avoids the side effects above.

**Example — *"change this chart's title color to red, leave everything else alone":***

```javascript
const sheet = SpreadsheetApp.getActiveSheet();
const chart = sheet.getCharts()[0];

chart.setOptions({
  title: {
    textStyle: {
      color: '#FF0000',
      // No need to read the old fontSize; just set the recommended title size (or 12 if unclear).
      fontSize: 16,
      bold: true,
    },
  },
});
```

**Wrong vs right at a glance:**

```javascript
// ❌ Wrong — re-sending the full options blob from getOptions() forces
//   body_pr.anchor_ctr=false on every textStyle sub-block and clears run-level
//   r_pr fields on title / axis titles. Some unrelated styles WILL be lost.
const cur = chart.getOptions() ?? {};
chart.setOptions({
  ...cur,
  title: { ...(cur.title ?? {}), text: 'New Title' },
});

// ✅ Right — send only the leaf you want to change. The backend deep-merges
//   it on top of the existing config, no side effects on untouched sub-blocks.
chart.setOptions({
  title: { text: 'New Title' },
});
```

**More examples:**

```javascript
// Change legend font size only — nothing else gets re-written.
chart.setOptions({ legend: { textStyle: { fontSize: 12 } } });

// Tighten the y-axis upper bound only — min / numberFormat / gridlines / textStyle preserved.
chart.setOptions({ yAxis: { scale: { max: 500 } } });

// Repaint the first series — color of series[0] only, other series untouched.
chart.setOptions({ series: [{ color: '#1F77B4' }] });

// Add an x-axis title on user request — emit the full title block (it didn't exist before).
chart.setOptions({
  xAxis: {
    title: { text: 'Month', visible: true, textStyle: { bold: true, fontSize: 12 } },
  },
});
```

> Reminder: this rule applies to `setOptions` only. When **creating** a chart via `newChart(...)`, pass the full styling in the `options` argument in a single call — see §5.5 rule 12. Do NOT do "create with defaults, then `setOptions` to style".

##### 4.3.1.3 Combo Charts

A combo chart mixes **column / line / area** series in a single plot, and can bind chosen series to a **secondary y-axis** (right side) — typical use case is two metrics with very different magnitudes on the same chart (e.g. *"revenue (¥10K) + YoY/MoM growth rate (%)"*).

**Two paths to render a combo chart — pick by scenario:**

1. **Simple case — use an Excel preset combo `chartType`** (one chartType string is enough; no need to write `series.type`):

   | Business need | chartType |
   | --- | --- |
   | Column + line, sharing one y-axis | `'CLUSTERED_COLUMN_AND_LINE_COMBO'` |
   | Column + line, line on the **secondary axis** | `'CLUSTERED_COLUMN_AND_LINE_ON_SECONDARY_AXIS_COMBO'` |
   | Stacked area + clustered column | `'STACKED_AREA_AND_CLUSTERED_COLUMN_COMBO'` |

   The preset's default split rule is *"the last series becomes the line (or the first one becomes the area), the rest become columns"*. If your data layout matches that rule, **strongly prefer the preset** — it is the simplest and least error-prone path.

2. **Fine-grained control — write `series[i].type` and `series[i].axis`** (top-level `chartType` is free; the shim auto-rewrites to `customCombo` when any `series[i].type` disagrees with the top-level type):

   ```javascript
   const chart = sheet.newChart(
     'chart_sales_growth',
     'COLUMN', // any top-level type; shim auto-rewrites to customCombo if series.type diverges
     dataRange,
     17, 0, 0, 0, 900, 480,
     {
       title: { text: '2024 Monthly Revenue & MoM Growth', visible: true, textStyle: { bold: true, fontSize: 16 } },
       legend: { visible: true, position: 'BOTTOM', textStyle: { fontSize: 12 } },
       xAxis: { gridlines: false, textStyle: { fontSize: 11 } },
       yAxis: { title: { text: 'Revenue (¥10K)', visible: true, textStyle: { fontSize: 12, bold: true } },
                numberFormat: '#,##0', scale: { min: 0, max: 500 }, gridlines: true,    // max from data scan
                textStyle: { fontSize: 11 } },
       series: [
         // Online channel revenue — clustered column, primary axis
         { type: 'COLUMN', axis: 'PRIMARY' },
         // Offline channel revenue — clustered column, primary axis
         { type: 'COLUMN', axis: 'PRIMARY' },
         // Total MoM growth rate — marker line, secondary axis
         { type: 'MARKER_LINE', axis: 'SECONDARY' },
       ],
     },
   );
   ```

**Allowed values for `series[i].type`** (OOXML `customCombo` only allows the column / line / area families):

- Column: `'COLUMN'` | `'STACKED_COLUMN'`
- Line:   `'LINE'` | `'MARKER_LINE'`
- Area:   `'AREA'` | `'STACKED_AREA'`

> ⚠️ Do **NOT** put `'PIE'` / `'SCATTER'` / `'BUBBLE'` / `'RADAR'` on `series.type` — OOXML does not allow mixing these types into a `customCombo`. The backend **silently ignores** such values and falls back to its built-in default (typically *"first series as a line, the rest as clustered columns"*), which is usually not what you intended.

**`series[i].axis`**: `'PRIMARY'` (default, left axis) / `'SECONDARY'` (right axis). When any series is bound to `SECONDARY`, communicate what the secondary axis represents (e.g. *"growth rate"*) through `secondaryYAxis.title.text` plus the main title / legend, so the reader can immediately tell what the left vs right axis means.

**Primary vs secondary y-axis — scale bounds (read this for any dual-axis chart):**

When a combo chart has a `SECONDARY` series, the primary y-axis is controlled by `options.yAxis` and the secondary y-axis is controlled independently by `options.secondaryYAxis`. The two have an identical field shape (`scale.min` / `scale.max` / `numberFormat` / `title` / `gridlines` / `textStyle` / …), and the backend matches them by OOXML `val_ax.ax_pos` (`l` = primary, `r` = secondary). **If `secondaryYAxis` is omitted, the backend falls back and applies `yAxis` to the secondary axis as well** (legacy-script compatibility); to make primary and secondary `scale.min` / `scale.max` independent, you MUST provide both blocks explicitly.

- **Compute `scale.min` / `scale.max` per the §4.3.1.1 Axes "data-scan" workflow** — primary axis scans the source column(s) bound to primary-axis series, secondary axis scans the source column(s) bound to secondary-axis series; never reuse one axis's scan results on the other. Dual-axis-specific notes:
  - **The secondary axis must carry a single unit** (either all percentages, or all absolute quantities). Don't bind both *"growth rate (%)"* and *"MoM delta (¥10K)"* to the secondary axis — the platform can only pick one `min` / `max` pair, so one of them will be squashed.
  - **If the secondary axis carries an absolute quantity** (two different units of currency / count), first compare the two axes' extents: if `primary.max ≥ 100 × secondary.max`, either rescale the secondary metric into a comparable magnitude in the source column (e.g. `¥10K → ¥`), or drop the dual axis entirely. Forcing two axes with extreme magnitude differences flattens one series into a near-zero line.
  - **Aligning the zero baseline across axes (mandatory when the secondary axis crosses zero)** — if the secondary-axis scan shows the data crosses zero (e.g. growth rate `actualMin = -0.18` / `actualMax = 0.34`, so per the §4.3.1.1 workflow `secondaryYAxis.scale = { min: -0.20, max: 0.40 }`), and the primary axis is **line / scatter** with all non-negative values, nudge `yAxis.scale.min` slightly negative (proportional to `actualMax_primary`) so that zero falls at the same relative position on both axes — this aligns the two zero lines visually. If the primary axis is **column / bar / stacked**, `yAxis.scale.min` MUST still be `0` (hard rule, §4.3.1.1); in that case zero sits at the bottom of the primary axis and the secondary's negative region falls below the primary's zero line — that is the expected look, do not violate the column-baseline rule for "alignment".
  - **`numberFormat` must be set per axis**: percentage secondary axis → `numberFormat: '0.0%'` or `'0%'`; currency secondary axis → `'$#,##0'` or `'#,##0'`. Never reuse the primary axis's `numberFormat` — the tick labels will then misrepresent the metric.
- **Secondary horizontal gridlines (`secondaryYAxis.gridlines`)**: default `false`, **MUST be emitted explicitly**. The primary axis already renders a set of horizontal gridlines (`yAxis.gridlines: true`); adding another set on top from the secondary axis produces overlapping, offset gridlines that look noisy. Additionally, when `secondaryYAxis` is omitted, the backend falls back to applying `yAxis.gridlines: true` to the secondary axis as well. **Even if you provide `secondaryYAxis` with other sub-fields but omit `gridlines`, the platform still applies `yAxis.gridlines` as the fallback** — to actually turn the secondary gridlines off, you must explicitly write `gridlines: false` inside `secondaryYAxis`.

**Minimal full example — column revenue + MoM growth-rate line, dual axis:**

```javascript
// Data scan (compute via get_cell_ranges / run_command BEFORE newChart):
//   Primary series (revenue, ¥10K)           actualMin=120,  actualMax=478   → scale.min=0 (column hard rule), max=500
//   Secondary series (MoM growth, crosses 0) actualMin=-0.18, actualMax=0.34 → scale.min=-0.20, max=0.40
const chart = sheet.newChart(
  'chart_sales_growth',
  'CLUSTERED_COLUMN_AND_LINE_ON_SECONDARY_AXIS_COMBO',
  dataRange,
  17, 0, 0, 0, 900, 480,
  {
    title: { text: '2024 Monthly Revenue & MoM Growth', visible: true,
             textStyle: { bold: true, fontSize: 16 } },
    legend: { visible: true, position: 'BOTTOM', textStyle: { fontSize: 12 } },
    // No xAxis.title at creation time (see §4.3.1.1 Axes); add later via setOptions only if the user explicitly asks.
    xAxis: {
      gridlines: false, textStyle: { fontSize: 11 },
    },
    yAxis: {                                        // Primary: revenue (absolute, column → hard-coded min: 0)
      title: { text: 'Revenue (¥10K)', visible: true,
               textStyle: { fontSize: 12, bold: true } },
      numberFormat: '#,##0',
      scale: { min: 0, max: 500 },                  // min: column hard rule; max: ceil(478 * 1.05) snapped to 50
      gridlines: true,
      textStyle: { fontSize: 11 },
    },
    secondaryYAxis: {                               // Secondary: MoM growth (line, crosses zero)
      title: { text: 'MoM Growth Rate', visible: true,
               textStyle: { fontSize: 12, bold: true } },
      numberFormat: '0.0%',                         // independent percentage format
      scale: { min: -0.20, max: 0.40 },             // scan-based actualMin/Max ±5%, snapped to 0.05
      gridlines: false,                             // turn off to avoid overlapping with primary gridlines
      textStyle: { fontSize: 11 },
    },
  },
);
```

**Modifying an existing combo chart — send a minimal patch only (see §4.3.1.2):**

```javascript
// Tighten only the secondary axis upper bound; everything else preserved by the backend deep-merge.
const chart = sheet.getCharts()[0];
chart.setOptions({
  secondaryYAxis: {
    scale: { max: 0.6 },                            // only `max` is sent; min / numberFormat / textStyle / gridlines preserved
  },
});
```

**Common pitfalls:**

- Top-level `chartType: 'CUSTOM_COMBO'` but every `series[i]` omits `type` → the backend falls back to its built-in default and renders **all series as clustered columns** (a semantically neutral fallback; it does **NOT** auto-add a line or area). This is rarely what the user actually wants — explicitly write `series[i].type` / `series[i].axis` for each series, or switch to one of the three Excel presets above.
- Reaching for a combo chart when there are only one or two series → unnecessary complexity; a plain column / line chart fits better.
- A data range mixes *"revenue"* and *"share %"* in the same chart without enabling a secondary axis → the percentage line gets squashed into a near-flat line on the x-axis, and the chart becomes unreadable.
- The primary axis is column / bar / area / stacked-* but you forgot to set `yAxis.scale.min: 0` → columns float off the baseline and the magnitude is visually exaggerated. (This is the one exception to the §4.3.1.1 data-scan workflow: column / bar / stacked / area MUST hard-code `min: 0` without scanning.)
- **Dual-axis chart provides `yAxis` only, no `secondaryYAxis`** → the backend applies `yAxis` to the secondary axis as well; when the two metrics have different units, one series will always be squashed. To get independent ranges (e.g. *"primary 0~max, secondary ±%"*), you MUST explicitly provide `secondaryYAxis.scale` and scan each axis's own source column(s) per the §4.3.1.1 workflow.
- Primary and secondary axes **not scanned independently** — reusing primary's `scale.min/max` on secondary (or vice versa) → with different units (percentage vs currency), sharing one `scale` always squashes one of them. Scan each axis's own source series; never cross-apply.
- Hard-coding `yAxis.scale.max` / `secondaryYAxis.scale.max` from a guess (e.g. always `100` / `1000`) or omitting `scale` and relying on platform auto-fit → real data above the cap gets clipped, real data far below the cap makes the chart look flat, and auto-fit produces tick spacing that is inconsistent across charts. **Every y-axis bound MUST come from scanning the source data first**, then computing `min` / `max` per the §4.3.1.1 workflow.
- Writing the secondary axis as `yAxis2` / `rightYAxis` / `secondaryY` or any other alias → none of these are valid field names, the backend ignores them. The only accepted name is `secondaryYAxis` (with the same shape as `yAxis`).
- Providing `secondaryYAxis` with `scale` / `numberFormat` / `title` set but **without an explicit `gridlines: false`** → the backend falls back to `yAxis.gridlines: true` for the secondary axis as well, producing two overlapping, offset sets of horizontal gridlines. **Any combo chart with a SECONDARY series MUST explicitly set `secondaryYAxis.gridlines: false`**.

##### 4.3.1.4 Scatter Charts (correlation) — REQUIRED setup

> Once §4.3.1.0 has led you to `SCATTER`, this is the build recipe. A scatter answers *"how do two numeric variables relate?"*, so it has its own non-negotiable rules that **override** the generic chart defaults. Triggers: 散点图 / scatter / "X vs Y / 相关性 / 关系 / 关联". Apply ALL of 1–4 every time you build a scatter.

1. **`dataRange` = exactly the two columns — nothing else.** Bind a **two-column** range: the **first** column is the **horizontal (X) axis**, the **second** is the **vertical (Y) axis**. The scatter back-end maps a 2-column rectangle to a single X-Y series; do **NOT** widen the range with a 3rd column (a fitted/trend column, an `id` / index / label column, a second metric) — the scatter does NOT treat extra columns as clean shared-X series and the chart comes out wrong. Both columns must be numeric (a scatter's x-axis is a VALUE axis, not categories); never put a text column on X — that silently degrades the chart into a category/line chart. If the source block has more than two numeric columns, pass `sheet.getRange(...)` for **only** the two the question is about (e.g. *"广告投入 vs 销售额"* → exactly those two); if they are not adjacent, this is the one case where copying the two columns into an adjacent helper block is justified so the single rectangle covers exactly X + Y.

2. **Bind the X axis to the first column; do NOT specify a series.** In the `newChart` options, set **`firstColumnAsCategory: true`** so the back-end uses the first column as the horizontal (X) axis values (this is a top-level `newChart` option, alongside `title` / `legend` / `xAxis` / …). A scatter needs **no** `series` config — omit the `series` block entirely, and do not set `useColumnAsSeries`. The second column becomes Y automatically.

3. **Both axis titles are MANDATORY** — this is the explicit **EXCEPTION** to the §4.3.1.1 *"omit `xAxis.title` at creation"* rule. A column/line chart's x-axis carries self-describing category labels, but a scatter's x-axis is bare numbers, so without a title the reader cannot tell what the horizontal axis measures. At `newChart` time you MUST emit **both** `xAxis.title` and `yAxis.title`, each with `visible: true`, `text` = the source column header (add the unit if the header omits it), and `textStyle: { bold: true, fontSize: 12 }`. The §4.3.1.1 font rule that normally forbids `xAxis.title.textStyle` at creation does NOT apply here.

4. **Styling.** Single X-Y series → `legend.visible: false` (the title carries the meaning; a one-entry legend is dead space). Scatter usually has ≥10 points → data labels stay **off** (§4.3.1.1 density rule). Both axes follow the **line/scatter** branch of the §4.3.1.1 `scale` workflow (scan each column's actualMin/actualMax independently). Keep the platform default marker color (no `series` block — see rule 2) unless the user asks for a specific color.

> **No native trend line.** There is **no** trendline / regression feature in the chart API — not in `ChartOptions`, not in the `sheet_add_chart` / `sheet_update_chart` `options` passthrough. Do **NOT** fake one by appending a fitted-`ŷ` column to `dataRange` (that produces the wrong chart, per rule 1), by inventing a `trendline` / `series[i].trendline` key (silently ignored), or by switching to a `*_SCATTER` line variant (those connect the raw points in data order — not a regression fit). If the user explicitly asks for a trend line, build the clean 2-column scatter and tell them an in-chart trend line is not currently supported.

```javascript
// Source A1:B41 — A: 广告投入(万元), B: 销售额(万元), 40 data rows (row 1 = header).
// Axis scan (line/scatter branch): X actualMin≈5/max≈98 → 0~100; Y actualMin≈40/max≈520 → 0~550
const chart = sheet.newChart(
  'chart_scatter_corr',
  'SCATTER',
  sheet.getRange(1, 1, 41, 2),        // EXACTLY two columns: [X | Y]
  0, 3, 0, 0, 720, 420,
  {
    firstColumnAsCategory: true,                               // 第一列作为横轴(X)；散点图无需指定 series
    title:  { text: '广告投入 vs 销售额', visible: true,
              textStyle: { bold: true, fontSize: 16 } },
    legend: { visible: false },                                // single series → legend off
    xAxis: {                                                   // 散点图必须给 X 轴标题（例外规则）
      title: { text: '广告投入（万元）', visible: true, textStyle: { bold: true, fontSize: 12 } },
      numberFormat: '#,##0', scale: { min: 0, max: 100 }, gridlines: false,
      textStyle: { fontSize: 11 },
    },
    yAxis: {
      title: { text: '销售额（万元）', visible: true, textStyle: { bold: true, fontSize: 12 } },
      numberFormat: '#,##0', scale: { min: 0, max: 550 }, gridlines: true,
      textStyle: { fontSize: 11 },
    },
  },
);
```
