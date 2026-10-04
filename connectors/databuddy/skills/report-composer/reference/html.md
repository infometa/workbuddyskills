# reference/html.md —— CSS 定义 + wedata-chart 组件定义（单一来源）

> 🛑 **阅读本文前必看 · CSS 存放红线**
>
> 本文「一、CSS 定义」下的 §1.1~§1.7 代码块**全部只是"参考说明"**，用于让你了解公共样式长什么样——**它们已经打包在 CDN `wedata-chart@1.0.1.css` 里**。
>
> - ✅ **要写进产物**：`<head>` 里一行 `<link>` 引用 CDN CSS；仅当需要自定义主题色时，`<style>` 里写 `:root` 变量覆盖（≤ 20 行）。
> - ❌ **禁止写进产物**：**不得**把 §1.1~§1.7 的任何 CSS 规则复制进 HTML 的 `<style>` 块。
> - ❌ 不要因为"担心 CDN 不可用"而内联全量 CSS——CDN 白名单是强制约束，内联全量反而违规。

## html整体结构介绍

### 引用资源说明
DataBuddy 启用严格 CSP，非白名单资源会被浏览器拦截（图表空白 / 样式丢失）；To B 客户内网也会屏蔽外网 CDN。因此**只允许** `wedata.cdn.tencent.com/w3_workspace/` 域下的资源。
**默认(仅渲染交互 HTML)——1 个公共 CSS + 2 个 JS**：

```
https://wedata.cdn.tencent.com/w3_workspace/wedata-chart@1.0.1.css?{系统时间}             ← 公共样式（放 <head>，<link> 引用）
https://wedata.cdn.tencent.com/w3_workspace/echarts@6.0.0.min.js   ← 图表内核
https://wedata.cdn.tencent.com/w3_workspace/wedata-chart@1.0.1.min.js?{系统时间}  ← 图表组件（紧随 echarts）,每次生成时带上最新时间,防止缓存
```

**`export_docx=true` 时——额外放 2 个 JS**(仅此场景才引,见 `html-docx.md` §L)：

```
https://wedata.cdn.tencent.com/w3_workspace/html2canvas.min.js
https://wedata.cdn.tencent.com/w3_workspace/html-docx.min.js
```


### html大纲规范


> 🛑 **CSS 存放规则（红线）**：使用 `<head>` 里的 `<link>` 引用 CDN CSS，**不得**在 `<style>` 中复制「一、CSS 定义」§1.1~§1.7 的全量 CSS。仅当 `design_brief` 明确要求自定义主题色时，才在 `<style>` 中写 `:root` 变量覆盖（≤ 20 行）。

**✅ 正确写法示例（简版 `<head>`）**：

```html
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>...</title>
  <!-- 公共样式：全量 CSS 都在这里，不要往下面 <style> 里复制 -->
  <link rel="stylesheet" href="https://wedata.cdn.tencent.com/w3_workspace/wedata-chart@1.0.1.css?t=20260827">
  <script src="https://wedata.cdn.tencent.com/w3_workspace/echarts@6.0.0.min.js"></script>
  <script src="https://wedata.cdn.tencent.com/w3_workspace/wedata-chart@1.0.1.min.js?t=20260827"></script>
  <!-- 仅当需要自定义主题色时才写；不需要则整块删除 -->
  <style>
    :root {
      --color-primary: #1e3a5f;
      --color-secondary: #2d8a4e;
      /* 最多 5 个变量覆盖，不要加 .kpi-card / .section / table 等任何其他规则 */
    }
  </style>
</head>
<body>
内容
</body>

</html>
```

### html内容规范
当用户无明确内容规范,默认使用此内容格式规范
1.title +subtitle(报告书写时间、数据时间范围等)+ KPI 网格（3-col
2.摘要 ：3~5 条要点，结论先行
3.主体内容:共 N 个 section（与规划的分析角度数对齐）,每一个section包含：title + 一句话结论 + 图表 + narrative
4.综合洞察&建议：针对问题的综合洞察 以及具体行动建议
5.数据来源：简单总结依赖来源表即可,不需要显示来自什么工具


## 引用CSS以及组件信息参考

### CSS定义
> ⚠️ **本节所有 CSS 均为"参考说明"，不是"要写进产物的模板"。**
> 以下 §1.1~§1.7 的样式**已全部打包在 `wedata-chart@1.0.1.css`** 中——生成 HTML 时只需 `<link>` 引用该公共 CSS 即可，**不要**把这些代码块复制到 `<style>` 里。列在这里只是为了让你了解公共样式的类名与视觉规范（如 `.kpi-card`、`.section`、z-index 规则等），便于正确书写 HTML 结构。
#### 1.1 主题变量 + 基础样式

```css
:root {
  --color-primary: #636efa; /* 主色：KPI 数值、标题左边框 */
  --color-secondary: #00cc96; /* 辅色：正向指标、toast、建议区块边框 */
  --color-warning: #d4880f; /* 警示色：需关注的指标 */
  --color-danger: #ef553b; /* 危险色：负向指标、差评 */
  --bg-page: #f0f2f5; /* 页面背景 */
  --bg-card: #ffffff; /* 卡片/区块背景 */
  --bg-hover: #f8f9fa; /* 行 hover 背景 */
  --bg-header: #f0f2f5; /* 表头背景 */
  --bg-insight: #f0f7ff; /* 分析洞察区块背景 */
  --bg-suggest: #e8f5e9; /* 建议区块背景 */
  --text-primary: #333333; /* 正文文字 */
  --text-secondary: #666666; /* 次要文字 */
  --text-muted: #888888; /* 辅助文字（标签、注释） */
  --border-light: #e8e8e8; /* 浅色边框 */
  --border-medium: #d0d5dd; /* 中等边框 */
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06); /* 卡片投影 */
  --radius-card: 12px; /* 卡片圆角 */
  --radius-btn: 6px; /* 按钮圆角 */
  --font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: var(--font-family);
  background: var(--bg-page);
  color: var(--text-primary);
  line-height: 1.6;
  padding: 20px;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
}
h1 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 8px;
  color: var(--text-primary);
  overflow-wrap: break-word;
}
.subtitle {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 24px;
  font-size: 14px;
  overflow-wrap: break-word;
  word-break: break-word;
}
```

#### 1.2 移动端断点（768 / 480 两档）

```css
/* 默认样式 = 桌面排版（≥ 768px），无前缀 */

@media (max-width: 768px) {
  /* 平板 / 窄 sidebar：KPI 2 列、图表降高、表格仍保持完整列 */
}
@media (max-width: 480px) {
  /* 手机：KPI 1 列、字号下调 */
  body { padding: 12px; }
  .container { max-width: 100%; }
  .section { padding: 16px; }
}
```

> viewport meta（HTML 结构项，CSS 管不到，必须自己写）：
>
> ```html
> <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
> ```

#### 1.3 KPI 指标卡片

> ⚠️ **仅供参考**：以下 CSS 已在 CDN `wedata-chart@1.0.1.css` 中，**不要**复制到 HTML 的 `<style>` 中。

```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.kpi-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 20px 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-light);
}
.kpi-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}
.kpi-value.green {
  color: var(--color-secondary);
}
.kpi-value.warning {
  color: var(--color-warning);
}
.kpi-value.danger {
  color: var(--color-danger);
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .kpi-value {
    font-size: 22px;
  }
}
@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .kpi-card {
    padding: 14px 12px;
    min-height: 80px;
  }
  .kpi-value {
    font-size: 20px;
  }
  .kpi-label {
    font-size: 12px;
  }
}
```

#### 1.4 Section 区块 / 洞察 / 建议 / 表格

> ⚠️ **仅供参考**：以下 CSS 已在 CDN `wedata-chart@1.0.1.css` 中，**不要**复制到 HTML 的 `<style>` 中。

```css
.section {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-light);
}
.section h2 {
  font-size: 18px;
  margin-bottom: 16px;
  color: var(--text-primary);
  padding-left: 12px;
  border-left: 4px solid var(--color-primary);
}
.section h3 {
  font-size: 15px;
  margin: 12px 0 8px;
  color: var(--text-primary);
}

.insight {
  background: var(--bg-insight);
  border-left: 3px solid var(--color-primary);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}
.suggest {
  background: var(--bg-suggest);
  border-left: 3px solid var(--color-secondary);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

/* 表格外层 wrapper 强制横滚（移动端列多必备）*/
.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 12px 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}
th {
  background: var(--bg-header);
  padding: 10px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-medium);
  white-space: nowrap;
}
td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-secondary);
}
tr:hover td {
  background: var(--bg-hover);
}
@media (max-width: 480px) {
  table {
    font-size: 12px;
  }
  th, td {
    padding: 6px 8px;
  }
}
```

#### 1.5 Toast 通知

> ⚠️ **仅供参考**：以下 CSS 已在 CDN `wedata-chart@1.0.1.css` 中，**不要**复制到 HTML 的 `<style>` 中。

```css
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: var(--color-secondary);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  z-index: 9999;
  opacity: 0;
  transition: opacity 0.3s;
}
.toast.show {
  opacity: 1;
}
```

#### 1.6 打印样式（`@media print`）

> ⚠️ **仅供参考**：以下 CSS 已在 CDN `wedata-chart@1.0.1.css` 中，**不要**复制到 HTML 的 `<style>` 中。

```css
@media print {
  .sql-toggle,
  .sql-block,
  .toast {
    display: none !important;
  }
  body {
    background: white !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .container {
    max-width: 100%;
    padding: 0;
  }
  .card,
  .section,
  .kpi-card {
    box-shadow: none;
    border: 1px solid #eee;
    break-inside: avoid;
  }
  /* ECharts 渲染为 canvas，避免跨页被截断 */
  .chart-container {
    break-inside: avoid;
  }
}
```

---

### 二、wedata-chart 组件定义参考

图表统一用 `wedata-chart` 组件渲染：**只写「卡片容器 + 一段 draw_spec」，不写任何 ECharts option / JS**。


#### 2.1 容器骨架（每个图表原样套）

```html
<div class="section">
  <h2>各城市月度 GMV 趋势</h2>
  <div class="wedata-chart chart-container" data-height="380px">
    <script type="application/json" class="wedata-chart-spec">
    { ...draw_spec（widget_type / title / encode / chart_option / dataset）... }
    </script>
  </div>
</div>
```

- 容器**必须同时**带 `wedata-chart`（组件识别）和 `chart-container`（响应式高度）两个 class，并给 `data-height`（普通图 `380px`，多系列/趋势图 `420~480px`）。
- `.chart-container` 的窄屏高度断点（`≤768→320px` / `≤480→260px`）已在 `wedata-chart@1.0.1.css`，带上 class 即自动生效。
- resize 由内核 `ResizeObserver` 自动处理，无需监听 window。

#### 2.2 容器可选属性（`data-*`）

| 属性 | 说明 | 默认 |
|---|---|---|
| `data-height` | 图表区高度 | `300px` |
| `data-legend-limit` | legend 默认可见的颜色维度上限，`0` 关闭 | `5` |
| `data-default-view` | 初始视图 `chart` / `detail` | `chart` |
| `data-collapsed` | `true` 则初始折叠 | `false` |
| `data-show-header` | `false` 则不渲染卡片头部（Tab/下载） | `true` |
| `data-show-footer` | `false` 则不渲染行数提示 | `true` |

#### 2.3 三条硬性要求（漏一条图就空白/报错）

1. **spec 用 `<script type="application/json" class="wedata-chart-spec">` 承载，不要拼进 JS**。
2. **ECharts 族（line/bar/pie/scatter/…）的 `chart_option` 必须存在且含 `series`**。内核在已有 `series` 之上做增强，不会凭空造 series。`indexCard` / `table` 走 DOM 渲染，本来无 `series`。除非有特定要求,否则chart_option不需要设置
3. **数据走 `dataset` COS 直链**：`dataset.Data` 填 `wedatacli query-data` 返回的 **COS 直链 URL** 原样透传，不要把二维数组内联写进 spec。
4. 组件是基于Echart组件,针对一些特定用户要求,可基于Echart的chart_option进行丰富扩展

> **明细数据不重复展示**：wedata-chart 组件本身自带「图表 / 明细」切换交互（卡片头部胶囊 Tab，`data-default-view` 控制默认视图），用户可直接在同一张卡片里切到明细表查看原始二维数据。因此**一份数据只出一个 wedata-chart 卡片即可**——如果某份数据已经用某个 chart widget（line/bar/pie/…）展示，就**不要**再在 HTML 里为同一份数据额外加一个明细表格（`<table>` 或另开 `table` widget），避免同一数据两处维护、页面冗余。
>
> **明细/表格也用 wedata-chart 组件承载**：确实需要展示明细数据时（如兜底表、纯明细场景），同样用 `table` widget（`.wedata-chart` 容器 + draw_spec，见 §2.5 `table`），数据直接走 `dataset.Data` 的 COS 直链，**不要**手写原生 `<table>` + `<div class="table-wrap">` 去铺数据。原生表格样式（§1.4）仅用于承载少量静态内容（如结论要点、非数据集的说明性表格），不用于展示 `wedatacli query-data` 返回的数据集。

#### 2.4 dataset 结构（COS 直链 + 列元信息）

```json
"dataset": {
  "Key": "ask_result",
  "Data": "https://wedata3-knowledge-sh-1257305158.cos.ap-shanghai.myqcloud.com/dataclaw-tool/sql-query/.../xxxx.csv?q-sign-algorithm=sha1&q-ak=...&q-signature=...",
  "Sql":"select * from catelog.table",
  "Columns": [
    {"ColumnName": "dm_trade_stat_date__month", "DisplayName": "月份", "ColumnType": "date_type"},
    {"ColumnName": "dm_trade_gmv",              "DisplayName": "GMV",  "ColumnType": "decimal_type"}
  ]
}
```

> - `Data`：**COS 直链 URL 原样透传**，含签名参数，不要改写、截断或重新签名。
> - `Columns`：CSV 的列元信息，`ColumnName` 与 CSV 表头一致、并与 `encode` 里引用的字段名对应；`DisplayName` 供展示、`ColumnType` 供格式化。
> - `Sql`：产出该数据集的查询语句。
> - `Key`：数据集标识（如 `ask_result`），多图表时用于区分不同 `dataset`。

#### 2.5 draw_spec 各 widget 规范

每个 spec 是一个对象，核心字段：`widget_type`（组件类型）、`title`（图表标题）、`encode`（字段映射契约）、`chart_option`（**JSON 对象**）、`dataset`（§2.4）。

> ⚠️ `chart_option` 是**JSON 对象**（直接写对象字面量，无需字符串化、无需转义内层引号）。下方示例为聚焦配置省略了 `dataset`，实际生成时**每个 widget 都要带对应 `dataset`**。

#### `indexCard`（指标卡）

```json
{
  "widget_type": "indexCard",
  "title": "2024年GMV",
  "encode": {
    "valueField": "dm_trade_gmv",
    "compareField": null
  },
  "chart_option": {"indexCard": {"valueFormat": "0,0.00", "valueFontSize": 28, "showTrend": false}}
}
```

> **单位处理**：单位**不要写进 `valueFormat`**——`numeral` 见到 `%` 会把值 ×100。用 `valuePrefix` / `valueSuffix` 做字面量拼接：`{"indexCard": {"valueFormat": "0.00", "valueSuffix": "%"}}`。

##### `line`（时间趋势）

```json
{
  "widget_type": "line",
  "title": "2018年月度GMV趋势",
  "encode": {
    "x": "dm_trade_stat_date__month",
    "y": ["dm_trade_gmv"],
    "seriesNames": ["GMV"]
  },
  "chart_option": {
    "line": {
      "xAxis": {"type": "category"},
      "yAxis": {"type": "value"},
      "tooltip": {"trigger": "axis", "order": "valueDesc"},
      "legend": {"type": "scroll"},
      "series": [{"type": "line", "encode": {"x": "dm_trade_stat_date__month", "y": "dm_trade_gmv"}, "smooth": true, "symbol": "none", "lineStyle": {"width": 1.2}, "emphasis": {"focus": "series"}}]
    }
  }
}
```

> **line 视觉规范（必须遵守）**：无论单/多系列，`series[]` 的每个 line item **必须**包含：
> 1. `"smooth": true`
> 2. `"symbol": "none"`
> 3. `"lineStyle": {"width": 1.2}`
> 4. `"emphasis": {"focus": "series"}`
>
> 同时 `tooltip` 加 `"order": "valueDesc"`、`legend` 为 `{"type": "scroll"}`。**禁止**在 `chart_option` 里写 `grid` / `legend.top` / `legend.left` 等布局定位。
>
> **20 色调色板（顶层 `color`，必须原样使用）**：
> ```
> ["#5470c6","#91cc75","#fac858","#ee6666","#73c0de","#3ba272","#fc8452","#9a60b4","#ea7ccc","#5b8ff9","#f6bd16","#6dc8ec","#945fb9","#ff9d4d","#269a99","#ff99c3","#7262fd","#78d3f8","#9661bc","#f08bb4"]
> ```

**`line` 多维/多指标（1 time + 1 category + 1 metric，按城市分组）**：

```json
{
  "widget_type": "line",
  "title": "各城市月度销售额趋势",
  "encode": {
    "x": "stat_month",
    "y": ["sum_sales"],
    "seriesField": "city"
  },
  "chart_option": {
    "line": {
      "xAxis": {"type": "category"},
      "yAxis": {"type": "value"},
      "tooltip": {"trigger": "axis", "order": "valueDesc"},
      "legend": {"type": "scroll"},
      "series": [{"type": "line", "encode": {"x": "stat_month", "y": "sum_sales"}, "smooth": true, "symbol": "none", "lineStyle": {"width": 1.2}, "emphasis": {"focus": "series"}}]
    }
  }
}
```

> 1. **`series[]` 只写一个模板 item**（type/smooth/symbol/lineStyle/emphasis/encode 五件套），不要替 city 每个取值复制 N 份。前端会拿 `seriesField` 展开。
> 2. **`encode.seriesField` 只写在顶层 `encode`**，不要重复塞进 `series[0].encode`（后者只需 `{x, y}`）。
> 3. **不要**在 chart_option 里写 `series[0].seriesField` / `series[0].color` / `series[0].stack` 等自造字段。

##### `bar`（类目对比）

```json
{
  "widget_type": "bar",
  "title": "各产品类目销售额",
  "encode": {
    "x": "product_category",
    "y": ["total_gmv"]
  },
  "chart_option": {
    "bar": {
      "xAxis": {"type": "category"},
      "yAxis": {"type": "value"},
      "tooltip": {"trigger": "axis"},
      "legend": {"type": "scroll"},
      "series": [{"type": "bar", "encode": {"x": "product_category", "y": "total_gmv"}, "emphasis": {"focus": "series"}}]
    }
  }
}
```

> **bar 视觉规范（必须遵守）**：
> 1. **20 色调色板**：顶层 `color` 数组与 line 图相同。
> 2. **`series[].emphasis.focus: "series"`**。
> 3. **`legend.type: "scroll"`**。
> 4. **`tooltip.trigger: "axis"`**。
> 5. **禁止**写 `grid` / `legend.top` / `legend.left` 等布局定位。

**`bar` 多维（2 category + 1 metric，按城市分组）**：

```json
{
  "widget_type": "bar",
  "title": "各城市各品类销售额",
  "encode": {
    "x": "product_category",
    "y": ["sum_sales"],
    "seriesField": "city"
  },
  "chart_option": {
    "bar": {
      "xAxis": {"type": "category"},
      "yAxis": {"type": "value"},
      "tooltip": {"trigger": "axis"},
      "legend": {"type": "scroll"},
      "series": [{"type": "bar", "emphasis": {"focus": "series"}}]
    }
  }
}
```

> 与 line 相同：`series[]` 只写一个模板 item；`seriesField` 只写在顶层 `encode`。

#### `pie`（少类目占比）

```json
{
  "widget_type": "pie",
  "title": "地区销售额占比",
  "encode": {
    "itemName": "region",
    "value": "total_gmv"
  },
  "chart_option": {
    "pie": {
      "tooltip": {"trigger": "item"},
      "series": [{"type": "pie", "radius": "55%", "encode": {"itemName": "region", "value": "total_gmv"}}]
    }
  }
}
```

#### `table`（明细/兜底）

```json
{
  "widget_type": "table",
  "title": "订单明细",
  "encode": {
    "columns": [
      {"physicalFieldName": "order_id",   "displayName": "订单号"},
      {"physicalFieldName": "sum_amount", "displayName": "金额", "displayAs": "number"}
    ]
  },
  "chart_option": {
    "table": {
      "gridSettings": {"itemsPerPage": 25, "freezeFirstNColumns": 1}
    }
  }
}
```

#### 2.6 widget 选型速查

| 数据形态 | 选 widget |
|---|---|
| 单个核心数值（KPI） | `indexCard` |
| 时间趋势（1 time + N metric，可选 category 分组） | `line` |
| 类目对比 / 排行（1~2 category + N metric） | `bar` |
| 少类目占比（≤ ~8 类，1 category + 1 metric） | `pie` |
| 明细 / 多列 / 兜底（画不成图时） | `table` |

---

## §i 落盘前门禁检查清单（强制 · 漏一条即回炉）

`Write` HTML 前逐条确认：

- [ ] 1. `<head>` 有 `viewport` meta，且 `<link>` 引 `wedata-chart@1.0.1.css` + `echarts@6.0.0.min.js` + `wedata-chart@1.0.1.min.js`（echarts 在 chart 前）。
- [ ] 2. **每个**图表是 `.wedata-chart` 容器 + `<script class="wedata-chart-spec">`；ECharts 族 `chart_option` 含 `series`；无手写 `setOption` / `resize`。
- [ ] 3. **每个**容器带 `data-height` + `class="wedata-chart chart-container"`（高度断点由 CDN CSS 自动生效，勿内联组件 CSS）。
- [ ] 4. **每个**图表带 `dataset`（走 COS 直链，`Columns` 与 CSV 表头一致，空值 `null`、时间维为字符串）。
- [ ] 5. `<style>` 块仅含 `:root` 变量覆盖（≤ 20 行），**无** §1.1~§1.7 的全量 CSS 复制（`.kpi-card` / `.section` / `table` / `@media` 等均不得出现在 `<style>` 里）。

> 任一条没做到 → **回到 Step 3 重写**，不许直接返回。
