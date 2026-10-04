# HTML 可视化报告 · 样式规范 + 三模式产出规范

> 本文件定义 `药箱药企数据洞察` 的 HTML 报告样式与组装规则。**唯一权威模板 = `assets/html_template.html`**（即「<药品名>洞察报告.html」的完整黄金模板，1239 行）。每次生成报告时，**只替换数据，不改 CSS / 骨架 / JS 引擎**。

---

## 0. 黄金模板定位（写死）

`assets/html_template.html` 是唯一权威黄金模板，已完整包含：

| 模块 | 内容 | 是否可改 |
|---|---|---|
| `<style>` 段 | 完整 CSS 设计系统（240 行） | ❌ 原样保留 |
| `hero` / `navbar` / `main` / `footer` / `back-top` | 页面骨架 | ❌ 结构不变，仅换文本 |
| `SECTIONS` 对象 | 三段完整 HTML（s-summary / s-market / s-func） | ✅ 只换数据 |
| JS 渲染引擎 | `renderSection` / `ensureChartsReady` / `bindMiniTabs` / `mk` / `initCharts` | ❌ 原样保留 |
| 配色常量 `C` + `baseGrid` + `axisStyle` | 图表风格 | ❌ 原样保留，只改图表 data |

**样式统一三原则（写死）**：
1. CSS（`<style>` 段）原样保留，不改配色变量、字号、圆角、间距。
2. 页面骨架（hero / navbar / main / footer / back-top）结构不变，仅替换药品名、统计周期、hero 指标数值等文本。
3. JS 渲染引擎与配色常量 `C` 原样保留，只改图表数据。

---

## 1. 设计系统（CSS 变量，医疗蓝绿）

统一医疗蓝绿主题。所有颜色集中在 `:root` 变量里，与黄金模板一致：

| 变量 | 值 | 用途 |
|---|---|---|
| `--brand` | `#0F6FB5` | 主品牌蓝（导航 / 图表主色 / 企业侧） |
| `--brand-2` | `#1E88C7` | 品牌蓝浅一档 |
| `--brand-deep` | `#0B4E80` | 品牌深蓝（hero 渐变起点） |
| `--brand-soft` | `#EAF4FB` | 品牌浅蓝底（表头 / 角标底） |
| `--teal` | `#16A085` | 青绿（药箱侧 / 洞察框左边线） |
| `--teal-2` | `#2FB8A0` | 青绿浅一档 |
| `--gold` | `#16A085` | 金色（历史遗留，实际同 teal） |
| `--ink` `--ink-2` `--ink-3` | `#1B2733` `#5A6B7B` `#8A99A8` | 正文三档灰（标题 / 正文 / 弱化） |
| `--line` | `#E4EBF1` | 分隔线 |
| `--bg` | `#F4F7FA` | 页面背景 |
| `--card` | `#FFFFFF` | 卡片底 |
| `--insight-bg` `--plan-bg` | `#F6FAFD` `#EDF6FC` | 洞察框 / 策略框底 |
| `--ent` `--box` | `#0F6FB5` `#16A085` | 企业侧 / 药箱侧标识色 |
| `--up` `--down` | `#D64545` `#2E9E6B` | **涨=红 / 跌=绿**（中国约定） |
| `--up-bg` `--down-bg` | `#FCECEC` `#E7F5EE` | 涨跌底 |
| `--radius` | `16px` | 卡片圆角 |

字体栈：`-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif`。

---

## 2. 页面骨架（与黄金模板一致）

```
<head>  → title + <!--__ECHARTS__--> 占位符 + <style>（完整 CSS）
<body>
  <header class="hero">    药品名 + 时间范围 + 4 个 hero 指标
  <nav class="navbar">     3 段导航：结论汇总(A) / 整体市场规模(1) / 药箱功能使用(2)
                           每段 subnav 含对应维度锚点
  <main id="main">         空容器，由 JS 按 SECTIONS 动态填充
  <footer>                 药品名 + 统计周期 + 数据来源说明
  <button id="backTop">    返回顶部
  <script>                 SECTIONS + renderSection + initCharts + 配色常量 C
```

**hero 4 指标固定顺序**（用户原始数据必须能提供）：
1. 销售额（亿元）/ 时间范围规模（公开数据）
2. 月均扫码人数
3. 月均访问次数
4. 新用户占比

> 月均数据根据原始数据时间范围实际计算（如半年数据 → 月均 = 总数/6）。

---

## 3. 三大 section + 9 维度 block 结构

| section key | 导航编号 | 标题 | 包含维度 |
|---|---|---|---|
| `s-summary` | A | 结论汇总 | 一句话结论 + 4 信号卡 + 核心洞察表 + 策略引导总览（flow + 双策略速览） |
| `s-market` | 1 | 整体市场规模和药箱用户分析 | 1.1 / 1.2 / 1.3 / 1.4 / 1.5 |
| `s-func` | 2 | 药箱功能使用分析 | 2.1 / 2.2 / 2.3 / 2.4 |

### 每个维度 block 统一组件顺序（对齐黄金模板）

```html
<div class="block" id="sX-Y">
  <div class="block-title"><span class="bar"></span>X.Y · 维度名</div>

  <!-- 数据部分：一个或多个 viz-insight 卡片 -->
  <div class="viz-insight">
    <div class="viz-head"><span class="ic">◱</span><h4>子标题</h4></div>
    <div class="viz-body">
      <div class="kpi-row">…（可选）</div>
      <div id="chart-xxx" class="chart">…（可选）</div>
      <table class="dtable">…（可选）</table>
      <div class="insight"><div class="lbl">洞察分析</div><p>…</p></div>
    </div>
  </div>

  <!-- 双侧策略 -->
  <div class="plan">
    <div class="plan-head"><span class="pic">➜</span><h4>策略建议</h4><span class="hint">…</span></div>
    <div class="plan-cols">
      <div class="plan-col ent"><span class="who">◈ 企业侧 …</span><p>/<ul><li>…</li></ul></p></div>
      <div class="plan-col box"><span class="who">◉ 药箱侧 …</span><p>/<ul><li>…</li></ul></p></div>
    </div>
  </div>

  <!-- 可选：口径 / 缺失说明 -->
  <div class="src-note">…</div>
</div>
```

> **结论（20~40 字）的呈现位置**：黄金模板不设每个维度独立的「结论块」，而是统一收口在 `s-summary` 的「核心洞察表」（`dtable`，一维度一行核心结论）+「策略引导总览」（`flow` + `plan-cols`）。生成时**保持此结构**，不要给每个维度额外新增结论块。

### 组件速查（class → 用途）

| class | 用途 |
|---|---|
| `.viz-insight` | 数据卡片容器（`.viz-head` 子标题 + `.viz-body` 内容） |
| `.kpi-row` + `.kpi` | 大数字指标卡（`.v` 数值 / `.k` 标签 / `.trend` 趋势说明） |
| `.dtable` | 数据表格（`.num` 数字 / `.rank` 排名 / `.dtable-nowrap1` 首列不换行 / `td.cat` 维度名单元格） |
| `.chart` / `.chart.tall` / `.chart.short` / `.chart.mini` | 图表容器（高 320 / 360 / 260 / 240 px） |
| `.insight` | 洞察框（青绿左边线 + ◆ 标签 `.lbl`） |
| `.plan` + `.plan-cols` + `.plan-col.ent/.box` | 双策略卡（蓝顶边 / 绿顶边，`.who` 主体标签） |
| `.summary-hero` | 结论汇总首屏卡（一句话结论 + `.signal-row` 信号卡） |
| `.flow` + `.flow-step` | 策略引导流程条（4 步） |
| `.concl-grid` + `.concl` | 结论卡（备用，黄金模板主要用 dtable 收口） |
| `.mini-tabs` + `.mini-tab` + `.mini-pane` | 维度内迷你 Tab 切换（如关联用药「所有药品 / 同类竞品」） |
| `.src-list` | 信源清单（`.badge-src` 编号 + URL） |
| `.src-note` | 口径 / 缺失说明条 |
| `sup.src` | 表内数据点信源角标 |

---

## 4. JS 配色常量 C + 图表对照表（对齐黄金模板）

ECharts 配色常量 `C`（黄金模板 `initCharts` 前的定义，**原样保留**）：

```js
const C = {
  brand:'#0F6FB5', brand2:'#1E88C7', brandDeep:'#0B4E80',
  teal:'#16A085', teal2:'#2FB8A0', blue:'#5A9BD4', green:'#2E9E6B',
  up:'#D64545', warn:'#E8873A', purple:'#7B4FC9',
  ink:'#5A6B7B', ink3:'#8A99A8', line:'#E4EBF1', soft:'#9DC3E0'
};
```

> ⚠️ 注意：涨红实际是 `C.up = '#D64545'`，跌绿是 `C.green = '#2E9E6B'`（**不是** `C.down`）；次浅蓝是 `C.soft = '#9DC3E0'` 与 `C.blue = '#5A9BD4'`（**不是** `C.brand3`）。务必以黄金模板实际代码为准。

### 9 维度图表 id 对照表（黄金模板实际 id）

| 维度 | chart id | 类型 | 所属 section |
|---|---|---|---|
| 1.1 市场规模 / 用户规模 | 无图表（KPI + 表格） | kpi-row + dtable | s-market |
| 1.2 月度销量 / 扫码走势 | `chart-scale-trend` | 双柱（访问+扫码，涨红跌绿） | s-market |
| 1.3 SKU 销量 / 扫码分布 | `chart-sku` | 环形图 | s-market |
| 1.4 地域扫码分布 | `chart-geo` | 横向条形 Top6 | s-market |
| 1.5 竞品规模 | `chart-competitor` | 横向条形（电商份额） | s-market |
| 1.5 关联用药疾病领域 | `chart-disease` | 横向条形 Top10 | s-market |
| 2.1 人群画像 | `chart-prof-gender` / `-age` / `-edu` / `-industry` / `-life` / `-hometown` | 6 个迷你图（环形/横向） | s-func |
| 2.2 功能使用 | `chart-func` | 环形图 | s-func |
| 2.3 科普访问 | `chart-article` | 柱 + 折线（访问人数 + 平均时长） | s-func |
| 2.4 用药打卡 | `chart-funnel` + `chart-checkin-days` | 漏斗 + 横向条形（持续天数分桶） | s-func |

共 **15 个图表容器**，`initCharts` 里的 `mk(id)` 必须与之**一一对应**（无死链、无孤儿）。

---

## 5. 数据缺失降级规则（写死）

**总原则**：数据缺失 = **直接不展示该部分**。不编造、不留空、不占位。

| 级别 | 缺失情况 | 处理 |
|---|---|---|
| **L1 — 整维度缺失** | 原始数据无该字段（如无 Sku 表 / 无打卡表） | 整个 `.block` 不渲染；navbar 锚点同步删除；s-summary 核心洞察表删该行；`initCharts` 删对应 `mk()` |
| **L2 — 维度内子部分缺失** | 维度有数据，但部分子字段为空或网络子节查不到 | 保留 block；缺失子部分不渲染；补 `.src-note`：暂未在公开渠道查询到 xxx 数据 |
| **L3 — 单图 / 单表数据缺失** | 某 chart 数据集为空 | 不渲染该 chart（删对应 `<div id>` + `mk()` 块）；表格保留则保留表格 |
| **L4 — 字段存在但全为 0** | 数据全 0 | 仍展示（0 是数据），但不单独写洞察 |

### 综合洞察里必须备注

> s-summary 必须包含一行：本期报告内「xxx 数据」未在公开渠道查询到，已基于药箱侧数据完成分析。

---

## 6. 三模式产出规范

### 6.1 模式 1 · 完整报告

按黄金模板替换全部数据点，产出单文件 HTML。流程见 SKILL.md 第 5 步（模式 1）。

### 6.2 模式 2 · 单维度洞察

从黄金模板摘取**单一维度章节**，生成独立 HTML：

1. **定位 section**：`1.x` → `s-market`；`2.x` → `s-func`。
2. **摘取 block**：从 `SECTIONS` 对应 section 中取该维度的 `<div class="block" id="sX-Y">…</div>` 整块。
3. **组装结构（固定）**：
   - `<head>`：`<title>` = 「药品名 · 维度名」+ `<!--__ECHARTS__-->` + **完整 CSS（原样）**
   - `<body>`：`hero` 简化（药品名 + 该维度核心指标）+ `<main id="main">` + 简化 `footer` + `back-top`
   - `<script>`：`SECTIONS` 仅含该 section（且只含该 block）；`initCharts` 仅保留该维度 `mk()`；渲染引擎 / 配色常量 `C` 原样保留
4. **缺失处理**：该维度本身无数据 → 直接返回「该维度本期无数据」提示，**不生成空 HTML**。
5. **命名**：`<药品名>_<维度>洞察报告_单文件版.html`。
6. **交付后固定引导话术（写死，逐字输出）**：
   ```
   已为您生成「<药品名>」<时间范围>的<维度名>数据报告。是否需要帮您补齐其他维度，生成完整版的报告？
   ```

> 摘取原则：**只删内容不删样式**。CSS、渲染引擎、`C` 常量一律原样保留，避免样式漂移。

### 6.3 模式 3 · 数据查询

**不生成 HTML 报告**，直接从药箱数据平台实时拉取对应指标返回（对照 `references/data_gateway_mapping.md`）：

1. 定位指标 → 对应业务指标（参考 `references/dimension_field_spec.md` 字段映射 + `references/data_gateway_mapping.md` 取数方式）。
2. 通过药箱数据平台只读查询接口拉取（**不再读离线 Excel / CSV**）。
3. 返回格式（结构化，用业务语言标注来源，**禁止出现平台名 / 表名 / 字段名**）：

```
【查询结果】<指标名>
- 数值：<结果>
- 统计周期：<YYYY-MM ~ YYYY-MM>
- 数据来源：药箱数据平台（按统计周期聚合）
```

4. **只返回数据事实**，不写洞察 / 策略 / 结论，不生成报告。
5. 数据不存在 → 明确回复「药箱数据平台未查询到 xxx」，不编造。
6. **交付后固定引导话术（写死，逐字输出）**：
   ```
   已为您查询到「<药品名>」<时间范围>的<指标名>数据为 <数值>。是否需要帮您进一步生成可视化图表或完整的数据洞察分析？
   ```

---

## 7. 单文件版生成（内联 ECharts，**写死**）

黄金模板含 `<!--__ECHARTS__-->` 占位符（head 内**独立成行**）。发布前把 `echarts.min.js` 内联进占位符：

```bash
python3 - <<'PY'
import pathlib, re
tpl = pathlib.Path('<html_path>').read_text(encoding='utf-8')
ech = pathlib.Path('<echarts_path>').read_text(encoding='utf-8')
# ⚠️ 必须用 re.subn 只替换独立成行的占位符；不能用 .replace()
# 原因：模板注释里也出现「<!--__ECHARTS__-->」描述，.replace 会把两处都换掉
out, n = re.subn(r'\n<!--__ECHARTS__-->\n', lambda m: '\n<script>'+ech+'</script>\n', tpl)
assert n == 1, f'占位符替换次数异常，应为 1，实际 {n}'
pathlib.Path('<单文件版路径>').write_text(out, encoding='utf-8')
print('✅ 单文件版完成:', round(len(out)/1024), 'KB')
PY
```

> `echarts.min.js` 已内置在本 skill 的 `assets/echarts.min.js`（自包含，直接引用即可）。

### 发布前必检清单

- [ ] **无** `<!--__ECHARTS__-->` 残留（已替换为 `<script>`）
- [ ] section 切换正常、图表渲染无空白、无 JS 报错
- [ ] 数据缺失维度按第 5 节降级（**无空 block / 空图表 / 死锚点**）
- [ ] 图表容器 id 集合 == `mk()` 集合（一一对应）
- [ ] 网络数据点全部带 `sup.src` 角标 + `src-list` URL
- [ ] 涨红跌绿配色、港澳台「中国」前缀、医疗免责声明已核对
- [ ] JS `node --check` 通过（提取 `<script>` 块送检）

---

## 8. 输出文件建议命名

| 场景 | 文件名 |
|---|---|
| 模式 1 调试版 | `<药品名>洞察报告.html` |
| 模式 1 交付版 | `<药品名>洞察报告_单文件版.html` |
| 模式 2 交付版 | `<药品名>_<维度>洞察报告_单文件版.html` |
| 模式 3 数据查询 | 不生成文件，直接返回结果 |
| 示例参考 | `<药品名>洞察报告_单文件版.html` |

---

## 9. 不要做的事

- ❌ 不要在 style 段自行加颜色（必须用 CSS 变量）
- ❌ 不要换黄金模板骨架 / 引擎 / 配色常量 `C`
- ❌ 不要在 navbar 留死锚点（缺失维度去掉）
- ❌ 不要 `.replace()` 内联 ECharts（必须 `re.subn`）
- ❌ 不要把洞察 / 策略 / 结论写到 block 之外（必须严格嵌套）
- ❌ 不要让维度排序错乱（先 1.x 后 2.x；段内序号按提取结果顺延）
- ❌ 不要给单维度摘取时删 CSS / 引擎（只删内容不删样式）
- ❌ 不要混淆三种模式（查询就别生成报告，单维度就别做整套）
