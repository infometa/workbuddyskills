# reference/html.md —— 数据产出 HTML 产物工程约束（单一来源）

> 本文件是 `report-composer` 生成 **HTML 一体化产物**时的**全部工程约束单一来源**：适用范围、CDN 白名单、
> 浅色主题与 CSS 变量、移动端、组件样式、打印、图表（下钻 / 排版 / 序列化）、写盘前自检、内容组装骨架、design_brief。
> **产 html 时整份读本文**（组件 §d、图表 §f/g/h 已并入，不再拆分多文件）。可选的 `.docx` 导出在 `html-docx.md`（§L）。
>
> ## 自包含原则
>
> HTML 的全部工程约束都在本 skill 内（**不读取任何其它 skill 的 reference / scripts**）。配套图表工具在本 skill `scripts/chart_utils.py`。
> **形态 / 载体怎么定**（出单图还是满配报告、出 md/html/两者）见 `SKILL.md` §三；本文只管「决定要出 html 后，html 怎么工程化生成」。
>
> ⚠️ 本场景图表库**仅使用 ECharts**。基础语法底线：单文件直出（`<!DOCTYPE html>` → `</html>`，无 Markdown 代码块包裹 / HTML 注释）、JS **仅 ES5**、全 HTTPS、响应式。

## 目录

| 节 | 主题 | 何时读 |
|---|---|---|
| §a | 适用范围 | 确认场景 |
| §b | CDN 白名单（默认 1 / docx 3） | 写 `<head>` 前 |
| §c | 浅色主题 + CSS 变量 | 写 `<style>` |
| §c.5 | 移动端适配 | 写响应式（**强制**，另见开头「移动端红线速查」） |
| §d | 通用 UI 组件样式（KPI / section / SQL toggle / toast） | 组装 KPI/章节组件 |
| §e | 打印样式 | 收尾样式 |
| §f | 下钻交互骨架 | 有多维下钻 |
| §g | ECharts 排版规范 | 写图表 option |
| §h | `df_to_echarts_option` | 序列化图表 |
| §i | 生成前自检清单 | **写盘前必过** |
| §j | 内容组装（数据从上文识别） | 识别数据 + 搭骨架 |
| §k | `design_brief` 范例 | 按业务定制版面 |
| §L | DOCX 导出 | 见 `html-docx.md`，`export_docx` 时 |

> 与 md 版的一致性：html 与 md 由 report-composer 在**同一次调用**里组装，用**同一个语义化文件名** `<slug>.{md,html}`（共用同一 `<slug>`，仅扩展名不同）；两者的 KPI、核心发现、结论、行动建议、SQL 编号 **必须一一对应**，不允许 md 与 html 数据/结论打架（骨架对齐规则见 `SKILL.md` §三.4，文件名规则见 `SKILL.md` §五 Step 3）。

---

## 🛑 移动端红线速查（先看这块，再往下读）

报告在手机端打开是**高频场景**，而移动端约束**分散在 §c.5 / §d / §g / §i 四处**，历史上多次因"只读了图表段就开写"而漏掉，导致手机端图表标题与轴标签重叠、数据标签糊成一片（复盘见 `../../../docs/mobile-adaptation-regression.md`）。

下面 7 条是**全部**移动端强制项，先建立整体印象，细节回各节看：

| # | 红线 | 原文位置 | 漏了会怎样 |
|---|---|---|---|
| 1 | `<head>` 有 `viewport` meta | §c.5.1 | iframe 按 980px 缩放，**所有响应式 CSS 全废** |
| 2 | 断点只用 `768` / `480` 两道线 | §c.5.2 | 自创断点导致各组件降级不同步 |
| 3 | 长 token（表全名 / URL）能断行 | §c.5.4 | 撑破容器 → 整页横向溢出、标题被挤偏 |
| 4 | `.kpi-grid` 有 `≤768 → 2 列` / `≤480 → 1 列` | §d | KPI 卡在手机上挤成一条 |
| 5 | `<table>` 外层包 `.table-wrap` | §d | 宽表撑破页面 |
| 6 | 每个图表容器 `class="chart-container"` + `≤768 → 320px` / `≤480 → 260px` | §g | 图表按桌面高度渲染，内容被压扁重叠 |
| 7 | 每个 `setOption` 用 `{baseOption, media:[768,480]}` + 挂 `resize` 监听 | §g | **标题/轴标签/数据标签互相重叠**（最典型的手机端翻车现场） |

> ⚠️ 第 6、7 条是**最易漏**的两条——它们在 §g（本文中后段），且只在 §i 自检里被复述一次。走 `df_to_echarts_option()` 的图表自动带 `media`；**手写 option 的必须自己加**。
>
> 这 7 条对**所有 shape 一致强制**（含 `chart` 单图 / `dashboard` 看板），不因产物轻量而豁免（见 §j.4）。

---

## a. 适用范围

适用于一切**数据驱动**的单文件 HTML 产物（分析报告 / 问数 / 看板等）； §三、§j.4。**§b~§i 工程底线对所有形态一致强制**。

## b. WeData 可信 CDN 白名单（强制 · 默认 1 个 / 导出 docx 时 3 个）

WeData 启用严格 CSP，非白名单 `<script>` 会被浏览器拦截（图表空白）；To B 客户内网也会屏蔽外网 CDN。因此**只允许** `wedata.cdn.tencent.com/w3_workspace/` 域下的脚本，按是否导出 docx 分两档：

**默认(仅渲染交互 HTML)——只放 1 个**：

```
https://wedata.cdn.tencent.com/w3_workspace/echarts.min.js
```

**`export_docx=true` 时——额外放 2 个**(仅此场景才引,见 `html-docx.md` §L)：

```
https://wedata.cdn.tencent.com/w3_workspace/html2canvas.min.js
https://wedata.cdn.tencent.com/w3_workspace/html-docx.min.js
```

| JS 库 | 文件 | 用途 | 何时引 |
| --- | --- | --- | --- |
| ECharts | `echarts.min.js` | 图表渲染（主力 & 唯一图表库） | 总是 |
| html2canvas | `html2canvas.min.js` | DOCX 导出时截非图表区(KPI 卡 / 表格)为位图 | 仅 `export_docx` |
| html-docx | `html-docx.min.js` | 把组装好的 HTML 转为 `.docx` 二进制 | 仅 `export_docx` |

**禁止项**（写入 HTML 前自检必过）：

- ❌ `cdn.jsdelivr.net`、`unpkg.com`、`cdnjs.cloudflare.com`、`bootcdn.net`、`cdn.plot.ly` 等任何公共 CDN
- ❌ Bootstrap / Ant Design / Google Fonts / FontAwesome / jQuery / D3 / Chart.js / jsPDF / docxjs 等白名单外第三方库（导出 docx 用 `html-docx`，**不是** docxjs/jsPDF）
- ❌ `import` 从外部 URL 加载 ES Modules

> 自检动作：生成 HTML 后全文搜 `src="https://`，所有命中域名必须是 `wedata.cdn.tencent.com`；未开 docx 时**不应**出现 html2canvas / html-docx。

## c. 浅色主题 + 全局 CSS 变量（强制）

所有产物必须使用**浅色主题**，禁止深色 / 暗黑背景。本场景需兼顾屏幕阅读与打印，浅色主题天然满足。

`<style>` 开头必须包含以下完整 CSS 变量定义并通篇引用：

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
  /* 数据源常是表全名（catalog.schema.table，无空格长 token）→ 必须允许断行，
     否则窄屏下该 token 不折行会撑破容器、触发整页横向溢出（标题也被挤偏） */
  overflow-wrap: break-word;
  word-break: break-word;
}
```

> ⚠️ **禁止**将 `--bg-page` 改为深色（如 `#0f0c29`、`#1a1a2e`）。深色背景下 ECharts 默认文字颜色会不可读，同时不适合打印。
>
> 📌 **样式框架口径**：本场景使用**纯 CSS 变量 + 手写 class**（如上 `:root` + 下文 §d 各组件），**不引入** Tailwind / Bootstrap / Ant Design 等任何 CSS 框架（CDN 白名单只放 ECharts，框架 CSS 也会被 CSP 拦）。

## c.5 移动端适配硬约束（强制）

产物在前端 iframe 沙箱里渲染，可用宽度区间 ~300px ~ ~1920px。按**宽度**（不是 UA）判定排版。

### 1. viewport meta（必须，所有产物）

`<head>` 顶部第一行必须出现：

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

缺失会导致 iframe 在 srcdoc 模式（移动端降级）下按默认 980px 缩放渲染，所有响应式 CSS 失效。

### 2. 断点规范（统一三档）

```css
/* 默认样式 = 桌面排版（≥ 768px），无前缀 */

@media (max-width: 768px) {
  /* 平板 / 窄 sidebar：KPI 2 列、图表降高、表格仍保持完整列 */
}
@media (max-width: 480px) {
  /* 手机：KPI 1 列、字号下调 */
}
```

**只用** 768 / 480 两道线，**不要**自创 600 / 640 / 720 等中间断点。

### 3. 容器与字号

```css
@media (max-width: 480px) {
  body { padding: 12px; }
  .container { max-width: 100%; }
  .section { padding: 16px; }  /* 卡片内边距窄屏收窄，给图表/表格让出宽度 */
}
```

字号保留 px 硬编码（不引入 rem），每个组件在 ≤480px 下显式定义降级字号（见 §d 各组件）。

### 4. 长 token 强制断行（防整页横滚）

副标题/正文里出现 `catalog.schema.table` 表全名、长 URL、长 ID 等**无空格长 token** 时，承载它们的元素必须能断行，否则窄屏下该 token 不折行会撑破容器、触发**整页横向溢出**（标题也被一起挤偏）。

- 标题 `h1`、副标题 `.subtitle` 已在 §c 基础 CSS 内置 `overflow-wrap: break-word`（必须保留）。
- 任何**自定义**的 Hero / 页头 / 数据源行，凡可能放长表名的，都要带 `overflow-wrap: break-word;`（必要时再加 `word-break: break-word;`）。
- 数据源若特别长，优先只放表名（去掉 catalog 前缀），或用 `<code>` 包裹——`<code>` 在 §d 已带等宽样式但**也要确认**有 `overflow-wrap`。

## d. 通用 UI 组件样式（KPI / section / SQL toggle / toast）

与图表库无关，**所有数据产出 HTML 必须原样引用**（裸单图 `chart` 形态可只取用到的部分）：

### KPI 指标卡片

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

**KPI 布局规则**：

1. 固定列数 `repeat(3, 1fr)`，不要用 `auto-fit + minmax`（会导致卡片宽度不一致）。
2. HTML 结构必须是 `<div class="kpi-label">标签</div><div class="kpi-value">数值</div>`，顺序不能反。
3. `.kpi-value` 必须设置 `white-space: nowrap`，防止长数字（如 `R$ 13,541,512`）被挤压换行。
4. 窄屏降级遵循 §c.5 统一断点：`≤768px → 2 列`、`≤480px → 1 列`

### Section 区块 / 洞察 / 建议 / 表格

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

**表格使用规则**：所有 `<table>` 必须包一层 `<div class="table-wrap">`，否则窄屏下列多的表格会触发整页横滚（而非表格内局部横滚）。

```html
<div class="table-wrap">
  <table id="table-top10">
    <thead>...</thead>
    <tbody>...</tbody>
  </table>
</div>
```

### 查看 SQL 按钮（toggle）

```css
.sql-toggle {
  background: var(--bg-header);
  color: var(--color-primary);
  border: 1px solid var(--border-medium);
  padding: 6px 14px;
  border-radius: var(--radius-btn);
  cursor: pointer;
  font-size: 12px;
  margin: 8px 0;
  position: relative;
  z-index: 10;
}
.sql-toggle:hover {
  background: #e4e7ec;
}
.sql-block {
  display: none;
  background: var(--bg-hover);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  white-space: pre;
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
  position: relative;
  z-index: 10;
}
@media (max-width: 480px) {
  .sql-block {
    font-size: 11px;
    padding: 10px;
  }
  .sql-toggle {
    font-size: 11px;
    padding: 5px 12px;
  }
}
```

```html
<div class="chart-section">
  <div id="chart-1" style="height:450px;"></div>
  <button class="sql-toggle" onclick="toggleSQL('sql-1')">📋 查看 SQL</button>
  <pre class="sql-block" id="sql-1"><code>SELECT ...</code></pre>
</div>

<script>
  function toggleSQL(id) {
    var el = document.getElementById(id);
    el.style.display = el.style.display === "none" ? "block" : "none";
  }
</script>
```

> **z-index 规则**：`.sql-toggle` 和 `.sql-block` 必须 `position:relative; z-index:10`，否则会被 ECharts Canvas 遮挡导致点击无效。

### Toast 通知（异步反馈）

任何异步操作（如刷新数据）完成后必须给用户明确反馈：

```html
<div class="toast" id="toast"></div>
<style>
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
</style>
<script>
  function showToast(msg, d) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(function () {
      t.classList.remove("show");
    }, d || 3000);
  }
</script>
```

## e. 打印样式（`@media print`，强制）

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

## f. 下钻交互 HTML 骨架 + ECharts JS 模板（强制）

所有包含**多维度数据**的产物，当数据存在可下钻维度（品类 → 各州、州 → 各品类、月份 → 各品类等）时，**必须实现点击下钻交互**，而非静态图表。

### 下钻实现原理

1. **取数阶段**额外查询交叉维度数据（如 `品类 × 州` 的 GMV 交叉表）。
2. 将交叉数据以 **JSON 嵌入到 HTML 前端**（`var crossData = [...]`）。
3. 通过 **ECharts `chart.on('click', ...)`** 事件监听图表点击。
4. 前端 JS **过滤交叉数据** + `drilldownChart.setOption(newOption)` 动态渲染下钻图表。
5. **纯前端过滤+渲染，不发起额外后端请求**。

### 适用场景判断

| 场景                                   | 是否需要下钻 | 下钻方式                               |
| -------------------------------------- | ------------ | -------------------------------------- |
| 柱状图展示品类 / 地区 / 渠道等分类维度 | ✅ 必须      | 点击柱子 → 展示该分类的子维度分布      |
| 趋势图展示时间序列                     | ✅ 建议      | 点击某月/某天 → 展示该时段的分维度明细 |
| 散点图展示多指标交叉                   | ⚠️ 可选      | 点击数据点 → 展示该实体的详细指标      |
| 饼图展示占比                           | ✅ 建议      | 点击扇区 → 展示该分类的子维度          |
| KPI 卡片                               | ❌ 不需要    | —                                      |

### HTML 骨架

```html
<!-- 主图表（可点击） -->
<div class="section">
  <h2>
    品类 GMV 排行
    <span style="font-size:11px;color:var(--text-muted)">👆 点击柱子下钻</span>
  </h2>
  <div id="chart-category" style="height:450px;"></div>
</div>

<!-- 下钻面板（默认隐藏） -->
<div class="section" id="drilldown-panel" style="display:none;">
  <div
    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"
  >
    <h2 id="drilldown-title">下钻详情</h2>
    <button
      class="sql-toggle"
      onclick="closeDrilldown()"
      style="background:#999;color:#fff;font-size:12px;padding:4px 10px;border:none;"
    >
      ✕ 关闭
    </button>
  </div>
  <div id="drilldown-chart" style="height:400px;"></div>
</div>
```

### 关键规则（与图表库解耦的业务规则）

1. **提示用户可点击**：在可下钻图表的标题旁加 `👆 点击柱子下钻` 提示文字。
2. **下钻面板可关闭**：必须有 `✕ 关闭` 按钮，关闭时调用 `dispose()` 释放实例。
3. **平滑滚动**：下钻面板展开时 `scrollIntoView({ behavior: 'smooth' })`。
4. **交叉数据取数阶段获取**：SQL 侧 `GROUP BY state, category`，Python 侧通过 `df_to_echarts_option` 之外的独立序列化（`df.to_dict('records')` + NaN 转 None）嵌入到 HTML `<script>` 中。
5. **纯前端过滤渲染，不额外请求后端**。
6. **所有 JS 必须 ES5 语法**（`var`、`function`，不要箭头函数、`let` / `const`、模板字符串、解构、`class`）。

## g. 图表排版规范（ECharts option 表达）

解决双 Y 轴组合图 / 短时间序列 / 带数值标签柱图 / 饼图 / 折线图常见的标题-legend 重叠、X 轴时间插值错位、柱顶数值被压、容器坍塌等问题。

### 通用 option 规则

| 问题                       | 强制修复（ECharts option）                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 标题与 legend 重叠         | `title: { top: 8 }` + `legend: { top: 36, left: 'center', orient: 'horizontal' }` + `grid.top >= 80`                                                        |
| 柱顶数值被压               | `series[i].label = { show: true, position: 'top', color: '#333' }` + `grid.top` 预留空间                                                                    |
| 折线点标签遮柱值           | 折线 series 用 `label: { show: true, position: 'top' }`，柱状 series 用 `label.position: 'insideTop'` 或留白足够                                            |
| 同类 series 数值标签互相叠字   | 每个 series 加 `labelLayout: { hideOverlap: true }` + `label.minMargin: 4`（放大碰撞盒更早触发隐藏）；折线要"尽量都显示"改 `labelLayout: { moveOverlap: 'shiftY', hideOverlap: true }` |
| 柱顶数值压住 y 轴刻度          | `hideOverlap` **管不到跨组件冲突**，必须换手段：柱值改 `position:'insideTop'` / `yAxis.axisLabel.formatter` 缩短刻度（6000万→0.6亿）/ `yAxis.max` 上浮 15% |
| 轴 name 压住居中标题           | `yAxis: [{ nameLocation: 'end', nameGap: 8 }, ...]`；480 档 media 里直接 `name: ''`                                                                        |
| 月份/季度 X 轴出现日期插值 | `xAxis.type = 'category'`（离散枚举）；时间序列才用 `xAxis.type = 'time'`                                                                                   |
| 组合图柱子贴边             | `series[i].barGap = '20%'` + `series[i].barCategoryGap = '30%'`                                                                                             |
| 容器高度坍塌               | 容器 DOM 显式设 `style="height:450px"`（普通）/ `height:520px`（组合图、时间序列多系列）；**禁用 `height:100%` 或 `height:auto`**，ECharts 依赖容器初始高度；移动端按下文「图表容器移动端降级」规则覆盖 |
| 大数值展示                 | `yAxis.axisLabel.formatter` 自定义千分位；过大改单位 K/M                                                                                                    |
| 大数据量（> 1 万点）       | `series[i].progressive = 2000` + `series[i].large = true` + `largeThreshold = 2000`                                                                         |
| visualMap 误用于"区段染色"      | ❌ **禁止**在 option 顶层加 `visualMap` 调用以实现"预测期阴影 / 不同段颜色"。visualMap 是**会作用到所有 line series 的**：一旦 `pieces` 的范围与实际 y 轴值不重叠，所有曲线会被映射成默认透明色→"曲线全空"。区段背景染色统一走下面「区段阴影」模板的 `markArea` |
| `markArea` 写在 option 顶层        | `markArea` **必须挂载到某个 `series` 上**（推荐主线的 series），写在 option 顶层与 xAxis/series 同级会被**静默忽略**→ 阴影不出现                                                  |
| `stack` 误用于置信区间带          | ❌ **禁止**让 lower 和 upper 两条线同时 `stack: 'X'`——`stack` 是**值相加**，会得到 lower+upper 的总高度，y 轴被拉到 ~2×，其他曲线被压扁。正确写法 lower + (upper-lower) 差值两条 stack（下面「置信带」模板）                                                |

### 图表容器移动端降级（强制）

所有 ECharts 容器必须带 `chart-container` 类，按下面 CSS 在窄屏覆盖 inline `height`：

```html
<div class="chart-container" id="chart-1" style="height:450px;"></div>
```

```css
.chart-container { width: 100%; }
@media (max-width: 768px) { .chart-container { height: 320px !important; } }
@media (max-width: 480px) { .chart-container { height: 260px !important; } }
```

ECharts 不会自动响应 window resize，**必须挂监听**：

```javascript
window.addEventListener('resize', function () {
  for (var id in CHART_INSTANCES) {
    if (CHART_INSTANCES[id] && CHART_INSTANCES[id].resize) CHART_INSTANCES[id].resize();
  }
});
```

### ECharts 移动端 media query 规范（强制）

**所有 ECharts option 必须用 `{baseOption, media}` 结构**。走 `df_to_echarts_option()` 的图表已自动包含 `media`；手写 option 的按下面模板加：

```js
chart.setOption({
  baseOption: { /* title, legend, grid, xAxis, yAxis, series */ },
  media: [
    { query: { maxWidth: 768 }, option: {
      title: { textStyle: { fontSize: 14 } },
      legend: { top: 32, textStyle: { fontSize: 11 }, itemGap: 8 },
      grid: { top: 70, bottom: 50, left: 8, right: 12, containLabel: true },
      xAxis: { axisLabel: { fontSize: 11 } },
      yAxis: { axisLabel: { fontSize: 11 } }
    }},
    { query: { maxWidth: 480 }, option: {
      title: { textStyle: { fontSize: 13 } },
      legend: { bottom: 5, top: 'auto', left: 'center', textStyle: { fontSize: 10 }, itemGap: 6, itemWidth: 14, itemHeight: 8 },
      grid: { top: 50, bottom: 60, left: 8, right: 8, containLabel: true },
      xAxis: { axisLabel: { fontSize: 10, rotate: 30 } },
      yAxis: { axisLabel: { fontSize: 10 } }
    }}
  ]
});
```

**约束**：
- 768 写在 media 数组前、480 在后（ECharts 后写覆盖先写）
- media 里**不要改 series**，只改 title/legend/grid/axisLabel。**三个受控例外**：pie / heatmap（单 series），以及**双 Y 轴组合图**——组合图允许在 media 里改 `series[i].label`，但 `series` 数组**必须与 baseOption 下标一一对齐**（ECharts 按数组下标 merge，顺序错位会把 label 关到错误的系列上；不需要改的系列留空对象 `{}` 占位）
- **双 Y 轴组合图 480 档整体降级（对窄屏最有效）**：柱值 + 折线标签全关、轴 name 清空，数值靠 tooltip 与下方明细表读取：

```js
{ query: { maxWidth: 480 }, option: {
  // series 下标必须与 baseOption 严格对齐：[0]=bar, [1]=line
  series: [{ label: { show: false } }, { label: { show: false } }],
  yAxis: [{ name: '' }, { name: '' }]
}}
```
- pie 的 media 里**不要写** xAxis/yAxis（pie 无轴）
- **`grid.left/right` 取小值（8~16）**：`containLabel: true` 时 ECharts 已自动给轴标签留位，`left/right` 只是标签框外侧的留白，设 40-60 会在短轴标签左边硬塞一大段空白（移动端尤其明显）。短标签场景 `left: 8` 即可，ECharts 自动贴合
- pie 480：`series:[{radius:['28%','58%'], center:['50%','42%'], label:{show:false}}]`；768：`series:[{label:{formatter:'{d}%', fontSize:10}}]`
- **饼图图例统一放底部**（baseOption + 各档 media 的 `legend` 都用 `bottom`，`center` 上移到 `['50%','46%']` 留位），并给 series 加 `avoidLabelOverlap:true` + `labelLayout:{hideOverlap:true}`：外侧引导线标签集中在圆的上半圈，顶部图例会与标签打架（小扇区尤甚）
- heatmap 480：`xAxis.axisLabel.rotate:45` + `visualMap:{orient:'horizontal', bottom:0}`

### 双 Y 轴组合图最小 option 模板

```js
{
  title: { text: '销售额 & 订单数', left: 'center', top: 8, textStyle: { fontSize: 16 } },
  legend: { top: 36, left: 'center', orient: 'horizontal' },
  grid: { top: 90, bottom: 60, left: 8, right: 16, containLabel: true },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  xAxis: { type: 'category', data: ['Jan', 'Feb', 'Mar', 'Apr'], axisLabel: { hideOverlap: true } },
  yAxis: [
    // nameLocation:'end' + 小 nameGap：轴 name 贴住轴顶，不会顶到居中标题
    // axisLabel.formatter 缩短刻度文本（6000万 → 0.6亿），避免长刻度被柱顶数值压住
    { type: 'value', name: '销售额', position: 'left', nameLocation: 'end', nameGap: 8,
      axisLabel: { formatter: function (v) { return v >= 1e8 ? (v / 1e8) + '亿' : (v >= 1e4 ? (v / 1e4) + '万' : v); } } },
    { type: 'value', name: '订单数', position: 'right', nameLocation: 'end', nameGap: 8,
      splitLine: { show: false } }
  ],
  series: [
    {
      name: '销售额', type: 'bar', yAxisIndex: 0,
      data: [1200, 1500, 900, 2100],
      itemStyle: { color: '#636EFA' },
      // 柱值放柱内顶部：避免柱顶数值向上压住折线标签与 y 轴刻度（见规则表「折线点标签遮柱值」）
      label: { show: true, position: 'insideTop', color: '#fff', formatter: '{c}', minMargin: 4 },
      labelLayout: { hideOverlap: true }
    },
    {
      name: '订单数', type: 'line', yAxisIndex: 1,
      data: [30, 45, 28, 62],
      itemStyle: { color: '#00CC96' },
      label: { show: true, position: 'top', color: '#333', minMargin: 4 },
      // 折线希望"尽量都显示"：先竖向错位让位，实在放不下才隐藏
      labelLayout: { moveOverlap: 'shiftY', hideOverlap: true },
      lineStyle: { width: 2 }, symbolSize: 8
    }
  ]
}
```

**组合图 label 的三类冲突与对应解法**（`hideOverlap` 只能解第一类，另两类必须换手段）：

| 冲突类型 | 典型现象 | 解法 |
| --- | --- | --- |
| 同类 series label 互压（同一碰撞组） | 折线相邻点标签 `21.55%` / `31.47%` 叠字 | `labelLayout: { hideOverlap: true }` + `label.minMargin: 4` 放大碰撞盒 |
| series label 压 y 轴刻度（跨组件，`hideOverlap` 管不到） | 柱顶 `5411.5万` 压住刻度 `6000万` | 柱值改 `position: 'insideTop'`；或 `yAxis.axisLabel.formatter` 缩短刻度；或 `yAxis.max` 上浮 15% 留头部空间 |
| 轴 name 压居中标题 | `销售额（万元）` 顶到主标题 | `yAxis.nameLocation: 'end'` + `nameGap: 8`；480 档直接 `name: ''` |

> **组合图分类数 > 4 时**：柱值一律改 `insideTop`，或直接 `label.show: false` 靠 tooltip + 明细表补数值，不要硬挤在柱顶。

### 时间序列的两种选择

- **短时间序列（月份 / 季度 / 周）** → `xAxis.type: 'category'`，`data: ['2025-01', '2025-02', ...]`（字符串数组），避免 ECharts 自动做日期插值。
- **长时间序列 / 不等间隔** → `xAxis.type: 'time'`，`series.data: [[timestamp, value], ...]` 或 `[[isoString, value], ...]`。**绝不传 `datetime64[ns]`**，Python 侧必须转 ISO 字符串或毫秒时间戳（详见 §h）。

### 历史 + 预测 + 置信带 图表骨架要点（趋势预测场景）

历史线、预测线、置信区间三组数据共用一个 `xAxis.data`，常见踩坑已收录在上方通用规则表（visualMap / markArea / stack 三行）。除此之外的骨架要点：

- **数据对齐**：三组 series（历史、预测、置信带）都要按 `historyMonths.concat(forecastMonths)` 的全长数组构造，非本段填 `null`；预测线**首点 = 历史末点**（避免折线断裂）
- **X 轴**：用 `xAxis.type: 'category'` + 字符串数组（月/周枚举），**不要**用 `'time'` + 原始 `Timestamp`
- **置信带实现**：两条 `type: 'line'` 同 `stack: 'confidence-band'`——下边界 series 数据 = `lower`、`lineStyle.opacity: 0`、**不加** `areaStyle`；上边界 series 数据 = `upper - lower` 差值、`lineStyle.opacity: 0`、**加** `areaStyle` 填淡色。两条都 `silent: true` + `tooltip.show: false`
- **预测区背景阴影**：用 `markArea` 挂在主历史 series 上（顶层 markArea 会被忽略），范围 `[{xAxis: forecastMonths[0]}, {xAxis: forecastMonths.last}]`
- **图例**：补一个空 `data: []` 的 series 用于在 legend 里显示"80% 置信区间"色块（隐藏 series 不占图例位）
- **不要**给下边界加 `areaStyle: rgba(255,255,255,1)` 试图"擦除填充"，会盖住上面的置信带让视觉上消失

## h. `df_to_echarts_option()` 工具函数规范

Python 侧从 DataFrame 生成 ECharts option 的统一入口。完整可运行实现见本 skill `scripts/chart_utils.py`，生成取数/绘图脚本时**必须调用此函数**，不得手写 option dict（手写易漏 NaN 处理、日期转换、主题色注入）。

### 函数签名

```python
def df_to_echarts_option(
    df: pd.DataFrame,
    chart_type: Literal['line', 'bar', 'pie', 'scatter', 'heatmap'],
    x: str,
    y: str | list[str],
    color: str | None = None,
    **kwargs,
) -> dict:
    """从 DataFrame 生成 ECharts option（dict），内嵌到 HTML 后可直接 setOption()"""
```

### 覆盖的图表类型

| chart_type | 必传列                                | 可选列 / kwargs                       | 场景             |
| ---------- | ------------------------------------- | ------------------------------------- | ---------------- |
| `line`     | `x`、`y`（单列或多列列表）            | `color` 分组列、`smooth`、`stack`     | 时间序列、趋势图 |
| `bar`      | `x`、`y`（单列或多列列表）            | `color` 分组列、`horizontal`、`stack` | 分类对比、排行   |
| `pie`      | `x`（类别列）、`y`（单个数值列）      | `ring` 环形、`top_n`                  | 占比             |
| `scatter`  | `x`、`y`（数值列）                    | `size`、`color` 分组列                | 散点 / 气泡      |
| `heatmap`  | `x`、`y`、`value`（=kwargs['value']） | `x_order`、`y_order`                  | 二维热力图       |

### 必须处理的工程细节

1. **NaN 处理**：`df = df.where(pd.notna(df), None)`。ECharts 收到 `NaN` 字符串会显示为断点或异常，改为 `None` → JSON 输出 `null` → ECharts 天然支持。
2. **时间字段处理**：
  - 检测到列 dtype 为 `datetime64[ns]` / `datetime64[ns, tz]` → 转 **ISO 字符串** `'%Y-%m-%dT%H:%M:%S'` 或 **毫秒时间戳**（`int`）。
  - **绝不直接传 `pd.Timestamp` / `datetime.datetime`**，ECharts 侧 `JSON.parse` 会失败。
3. **主题色注入**：
  - 默认色序 = `['#636EFA', '#00CC96', '#EF553B', '#d4880f', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']`（与 §c CSS 变量对齐）。
  - 每个 series 注入 `itemStyle.color`，来自参数 `theme_colors: list[str] | None = None`（默认用上面的色序）。
4. **pie 数据结构**：`series[0].data = [{ 'name': cat, 'value': num }, ...]`。
5. **heatmap 数据结构**：`series[0].data = [[x_idx, y_idx, value], ...]`；`xAxis.data` / `yAxis.data` 取 unique + 可选排序。
6. **axis 类型推导**：
  - `chart_type == 'line'` 且 `x` 列为时间 dtype → `xAxis.type = 'time'`。
  - `chart_type in ('bar', 'line' with 类别 x)` → `xAxis.type = 'category'`。
  - `chart_type == 'scatter'` → 两轴均 `type = 'value'`。
7. **大数据量降噪**：当 `len(df) > 10000` 时，自动在 series 加 `progressive: 2000` + `large: true` + `largeThreshold: 2000`。

### 调用示例

```python
import pandas as pd
from chart_utils import df_to_echarts_option  # 由本 skill scripts/chart_utils.py 提供

df = pd.read_csv(csv_path)  # 假设列：date, category, revenue
# 趋势图
line_opt = df_to_echarts_option(df, 'line', x='date', y='revenue', color='category')
# 柱图
bar_opt  = df_to_echarts_option(df.groupby('category')['revenue'].sum().reset_index(),
                                'bar', x='category', y='revenue')

# 内嵌到 HTML 模板
import json
html = f"""
<div id="chart-1" style="height:450px;"></div>
<script>
var chart1 = echarts.init(document.getElementById('chart-1'));
var opt1 = {json.dumps(line_opt, ensure_ascii=False)};
chart1.setOption(opt1);
CHART_INSTANCES['chart1'] = chart1;
</script>
"""
```

> 注意：`json.dumps` 必须加 `ensure_ascii=False`，否则中文类目名会被转成 `\uXXXX` 转义，虽然不影响渲染但可读性差。

## i. 生成前自检清单（ECharts 版）

产物写入磁盘前必须逐条检查（全文搜或肉眼确认）：

### 主题与样式

- [ ] `body { background: var(--bg-page) }` 为 `#f0f2f5`，**未使用深色/暗黑背景**
- [ ] `<style>` 中包含完整 `:root { --color-primary: ... }` CSS 变量定义
- [ ] KPI 卡片使用 `grid-template-columns: repeat(3, 1fr)`；`.kpi-value` 有 `white-space: nowrap`

### CDN 与依赖

- [ ] `<head>` 中包含 `echarts.min.js` CDN
- [ ] 所有外部 JS 引用全部来自 `https://wedata.cdn.tencent.com/w3_workspace/`
- [ ] 全文搜 `jsdelivr` / `unpkg` / `cdn.plot.ly` / `cdnjs` **无命中**

### 打印

- [ ] `@media print` 中隐藏 `.sql-toggle / .sql-block / .toast`

### 图表容器与数据

- [ ] **每个 `<div id="chart-N">` 都有配套的 `echarts.init(...).setOption(...)` 脚本**（常见事故：多章节报告复制骨架时只复制了容器，漏写 init 脚本，该章节图表区一片空白）
- [ ] 每个 ECharts 实例初始化后写入 `CHART_INSTANCES[id] = chart`（供窄屏 resize 用，见 §c.5 / §g）
- [ ] 图表 id 编号**连续**（`chart-1/chart-2/chart-3`…），不出现跳号（跳号通常意味着有章节被漏写）
- [ ] 每个图表容器都有显式高度（≥ 380px 普通，≥ 480px 组合图），**未使用 `height:100%` 或 `height:auto`**
- [ ] 时间字段在 Python 侧已转为 ISO 字符串或毫秒时间戳，**JSON 中不出现** `datetime64` / `Timestamp` / `__str__` 字面量
- [ ] DataFrame 已经 `df.where(pd.notna(df), None)`，**JSON 中不出现裸 `NaN`**（只会是 `null`）
- [ ] 大数据量（单图 > 10000 点）series 中有 `progressive` + `large: true`

### SQL 与交互

- [ ] 每个图表/表格区域紧跟「查看 SQL」按钮，按钮文本包含 `SQL-N` 编号和查询用途
- [ ] `.sql-toggle` 和 `.sql-block` 设置了 `position: relative; z-index: 10`
- [ ] 多维度数据（品类/地区/渠道等）已实现下钻交互，事件用 `chart.on('click', function(params){...})`，参数解构使用 `params.name / params.data / params.dataIndex`

### 移动端适配（强制 · 见 §c.5）

- [ ] `<head>` 含 `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
- [ ] 媒体查询断点**只用** 768 / 480
- [ ] `.kpi-grid` 有 `≤768 → 2 列` + `≤480 → 1 列` 降级
- [ ] 所有 `<table>` 外层包 `<div class="table-wrap">`
- [ ] 所有 ECharts 容器有 `class="chart-container"` + `≤768 → 320px` / `≤480 → 260px` 高度覆盖
- [ ] 所有 `chart.setOption(...)` 用 `{baseOption, media:[...]}` 结构，media 含 `maxWidth:768` 和 `maxWidth:480` 两档
- [ ] `<script>` 含 `window.addEventListener('resize', ...)` 遍历 `CHART_INSTANCES.resize()`

### DOCX（仅 `export_docx=true` 时，详见 `html-docx.md` §L）

- [ ] `<head>` 含 `html2canvas.min.js` + `html-docx.min.js`，且均来自 `wedata.cdn.tencent.com`；未开 docx 时**不出现**这两个

## j. HTML 内容组装指引（数据从上文识别）

> report-composer 是 dispatcher-less（同一 LLM 在同一上下文继续干活）。调用方在取数/分析阶段累积的
> `wedatacli query-data` / `data-analyzer` 工具调用返回值**已经在上下文里**，组装 HTML 时**直接从上文识别**，
> **不要**要求调用方把数据复制成 `args.data` 字典（双倍 token 的无用功，且引入打包遗漏 / 字段名错误）。

### j.1 内容从上文哪里来（识别清单）

| HTML 组件 | 从上文识别来源 | 识别动作 |
|---|---|---|
| **顶部 Hero KPI** | 最近的 `Skill("data-analyzer", op="basic_summary")` 返回（或多次合并） | 取 `mean / sum / count / change_pct` 等核心指标作 KPI 卡 |
| **摘要（仅 full）** | 综合所有 section 结论 + 行动建议素材，浓缩成 3~5 条 | 结论先行（BLUF）：核心结论 + 首要建议，每条带 `[📊 SQL-N]`；置于 Hero KPI 下方第一屏 |
| **Section title + 一句话结论** | 上文每一对 `wedatacli query-data + Skill("data-analyzer")` 的语义意图 | 每对取数+分析对应一个 section，title 抽取规划文案 |
| **Section ECharts 图表** | `Skill("data-analyzer")` 返回里的 `echarts_opt`；或 `chart_utils.df_to_echarts_option()` 输出 | 直接消费 dict，按 §g 排版规范内嵌（`JSON.stringify(option)`） |
| **Section narrative** | `Skill("data-analyzer")` 返回里的 `trend / anomaly / attribution` 等字段 | 写成 markdown 段落，引用数据时标注 `[📊 SQL-N]` |
| **Section SQL 折叠块** | `wedatacli query-data` 返回里的 `sql` + 查询用途 | 按 §d 模板渲染 `.sql-toggle / .sql-block`，编号连续 |
| **多维下钻数据** | 上文显式查询了交叉维度的 `wedatacli query-data` | 按 §f 骨架渲染下钻；无交叉维度则跳过 |
| **底部综合洞察** | 跨 section 逻辑串联——综合所有 `data-analyzer` 返回生成 | markdown 列表（每条 1~2 句，含数据引用） |
| **底部行动建议（≥3 条）** | 综合上文给出短/中/长期建议 | 每条引用具体数据，按影响面排序 |

> 单图表 / 看板等轻量场景：按需取上表子集（如问数可能只有 1 个图表 + 一句结论，无需 KPI 网格与行动建议）。

### j.2 HTML 结构骨架（默认布局；按 `design_brief` 调整）

未传 `design_brief` 时：

```text
┌─────────────────────────────────────────────────┐
│ Hero 区：title + subtitle + KPI 网格（3-col）   │
├─────────────────────────────────────────────────┤
│ 摘要卡片（仅 full）：3~5 条要点，结论先行   │
├─────────────────────────────────────────────────┤
│ Section 1：title + 一句话结论 + 图表 + SQL + narrative │
├─────────────────────────────────────────────────┤
│ ... 共 N 个 section（与规划的分析角度数对齐）   │
├─────────────────────────────────────────────────┤
│ 综合洞察：跨 section 的 markdown 列表           │
├─────────────────────────────────────────────────┤
│ 行动建议：≥3 条，引用具体数据                    │
└─────────────────────────────────────────────────┘
```

> **摘要卡片**：仅 `full` 出，置于 Hero KPI 下方、第一个 Section 之前，是第一屏可见的"结论先行"区（BLUF）。用一个高亮卡片（沿用 §c/§d 既有卡片 class，不引入新版式标签）承载 3~5 条 `<li>` 要点，每条含数据引用 `[📊 SQL-N]`。它是底部"综合洞察 + 行动建议"的浓缩前置版，二者结论一致、不重复堆砌。`lite`/`chart`/`dashboard` 不出此卡片。

传了 `design_brief` 时：按 brief 调整 Hero / Section / 底部的版面节奏（双栏对照 / 4-col 网格 / 时间线 / 大数字 Hero 等），但**不可突破** §b~§i 的工程底线（CDN / 浅色主题 / chart_id 连续编号 / SQL 折叠 / 移动端 viewport + 断点等）。

#### HTML `<head>` 必含项（强制顺序）

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>{{ title }}</title>
    <script src="https://wedata.cdn.tencent.com/w3_workspace/echarts.min.js"></script>
    <style>
      /* §c 的 :root CSS 变量 + §c.5 移动端断点 + §d 各组件样式 + §e @media print */
    </style>
  </head>
  <body>
    <!-- §j.2 默认布局或 design_brief 定制布局 -->
  </body>
</html>
```

### j.3 写作 / 渲染规则

- **narrative / insights / actions** 等文字内容**直接写成基础 HTML 标签**（`<p>` / `<ul>` / `<strong>`），不要塞 `<div>` / `<button>` 等版式标签——版式由 §c/§d 的 CSS 变量 + UI 组件 class 统一控制
- **SQL** 单独走 `.sql-toggle` + `.sql-block` 折叠模板（§d），不要塞进 narrative 段落里
- **`chart_id` 必须连续编号** `chart-1 / chart-2 / chart-3 / ...`（跳号会被 §i 自检拦）
- **`echarts_opt`** 直接 `JSON.stringify(option)` 内嵌为 JS 字面量（`chart_utils.df_to_echarts_option()` 已处理 NaN / datetime / 主题色注入）
- **数据引用**：narrative 引用具体数据时标注 `[📊 SQL-N]`，与对应的 SQL 折叠块编号对齐

### j.4 轻量场景的裁剪

并非所有数据产出都要"满配报告"。按规划好的 shape（见 `SKILL.md` §三）取本节子集；无论裁剪到多轻，§b~§i 的工程底线（CDN / 浅色主题 / ES5 / 移动端 / 自检）对所有场景**一致强制**：

> 🛑 **"裁剪"只裁版面元素，不裁工程底线**。
> ✅ 可以裁：KPI 网格、摘要卡片、行动建议、综合洞察、section 数量——这些是**内容/版面**。
> ❌ 不可裁：`viewport` meta、768/480 断点、`.chart-container` 断点高度、`{baseOption, media}` 两档、`resize` 监听、CDN 白名单、§i 自检——这些是**工程底线**。
> 一张 `chart` 单图**同样要**完整的移动端 7 条红线：单图在手机上看崩了，和满配报告崩了一样是事故。

- **分析报告（full）**：满配（Hero KPI + 摘要 + 多 section + 图表 + SQL + 综合洞察 + 行动建议）。
- **问数单图（chart）**：单图表 + 一句话结论 + SQL 折叠，无需 KPI 网格 / 行动建议（`design_brief` 用「问数单图」范例）。
- **数据看板（dashboard）**：多卡片仪表盘网格，强调一屏概览（`design_brief` 用「数据看板」范例）。

## k. `design_brief` 范例（按业务场景）

`design_brief` 是 `args` 里的一句自然语言引导，用于在 §b~§i 工程底线之上做版面差异化。**不能突破** §b~§i 的强制约束（CDN / 主题等）。

| 业务场景 | 推荐 `design_brief` |
|---|---|
| 电商周报 | `"Hero 区放 GMV + 走势图 + 一句话洞察；中段品类用 4-col 网格替代柱状排行；浅色 + 蓝绿点缀；打印友好"` |
| 财务月报 | `"双栏对照核心指标的当期 vs 基准期；颜色冷淡；强调表格而非图表"` |
| 管理层汇报 | `"单页大数字 + 极少文字；Hero 区每个 KPI 占 1/3 屏幕；中段折线 + 重点高亮当月异动"` |
| 专题研究 | `"时间线视图叠加事件标注（产品上线、活动节点等）；强调因果链而非分段叙事"` |
| 异动洞察 | `"红色警示色为主导（指标恶化时）；问题 KPI 放最上方；归因路径用瀑布图或桑基图；建议区块加粗显示"` |
| 巡检报告 | `"check 列表打勾视图为主；每个 check 项左侧加状态色条；底部汇总分数 + 风险等级仪表盘"` |
| 问数单图 | `"无 KPI 网格与行动建议；单图表 + 一句话结论 + SQL 折叠；轻量自包含"` |
| 数据看板 | `"多卡片网格仪表盘；顶部筛选/时间范围；每卡一个核心指标 + 迷你图；强调一屏概览"` |

**缺省行为**：未传 `design_brief` → 按 §j.2 默认结构生成。

**注意**：`design_brief` 只是版面引导，最终产物由本 skill 按 §b~§i 工程约束 + design_brief + §j.1 上文识别结果综合决定。

## L. DOCX 导出（可选能力）

`export_docx=true` 时在已产出 html 基础上多导一份 `.docx`，实现细则见 `reference/html-docx.md`（§L）。需在 §b 第二档额外引入 `html2canvas` + `html-docx` 两个 wedata CDN。默认关，不引这两个库。