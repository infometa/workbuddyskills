## Reference files (read on demand)

You have detailed reference files bundled with the plugin. They are **not** in your context by
default. Before acting on a task that matches a topic below, you **MUST** `Read` that topic's
reference file first, then follow it. Do **NOT** compose parameters from memory — each file is the
single source of truth for its area, and guessing instead of reading produces broken output or a
failing `run_command`.

| Topic | Read this file FIRST | When |
| --- | --- | --- |
| **sheet-charts** | `${CODEBUDDY_PLUGIN_ROOT}/prompt/sheet-references/sheet-charts.md` | Chart-type selection, styling defaults, combo & dual-axis, and the minimal-patch rule for spreadsheet chart operations. Read before any `newChart` / `setOptions` / `setDataRange` / `removeChart` / `getCharts`, or any task that creates, modifies, or removes a chart, or a request that implies one: 生成图表 / 画个图 / 柱状图 / 折线图 / 饼图 / 环形图 / 散点图 / 气泡图 / 雷达图 / 趋势图 / 占比 / 对比图 / 可视化 / 仪表盘 / 图表样式 / 改图; "make / create / add a chart / graph / plot"; "visualize / plot this"; a named chart type (bar / line / pie / scatter / bubble / radar / stacked / combo / dual-axis); "add a trendline"; "restyle / recolor / retitle this chart". |
| **audit-spreadsheet** | `${CODEBUDDY_PLUGIN_ROOT}/prompt/sheet-references/audit-spreadsheet.md` | Audit a spreadsheet for formula accuracy, errors, and common mistakes. Scopes to a selected range, a single sheet, or the entire workbook. Triggers on "audit this sheet", "check my formulas", "find formula errors", "QA this spreadsheet", "sanity check this", "something's off in this sheet", "review this spreadsheet". |
| **sheet-replicate-template-layout** | `${CODEBUDDY_PLUGIN_ROOT}/prompt/sheet-references/sheet-replicate-template-layout.md` | MANDATORY when the user asks to "reference / copy / replicate / follow the format of" an existing sheet (template) to modify another sheet. Triggers on "参考、模版、模板、template、copy format、 replicate layout、follow the style of、按照…格式、照着…做、复制格式、格式一样、样式一样、 跟…一样的格式", or any intent implying "make sheet B look like sheet A". Covers P0 properties: row heights, column widths, merged cells, background colors, font sizes, font colors, font weights, font styles, font families, font lines, number formats, text wrap, horizontal/vertical alignment, borders. |
| **featured-formulas** | `${CODEBUDDY_PLUGIN_ROOT}/prompt/sheet-references/featured-formulas.md` | Authoritative guide to the two external-data formulas STOCK (stock quotes) and IMPORTRANGE (cross-sheet range import) — syntax, required params, spill/return shape, limits, the `#GETTING_DATA` loading state, and error codes. Read BEFORE writing any STOCK or IMPORTRANGE formula into a cell. Triggers on: 查股价 / 拉行情 / 股票报价 / 涨跌幅 / 实时价 / STOCK; 从另一个表导入 / 跨表引用 / 引用某个链接的数据 / IMPORTRANGE; "stock price / quote / ticker", "import a range from another sheet / doc", any formula string containing `STOCK(` or `IMPORTRANGE(`. |

`${CODEBUDDY_PLUGIN_ROOT}` is the plugin root; the paths above resolve to real files on disk. If a
task spans two topics (e.g. an audit that also rebuilds a chart), read both files.
