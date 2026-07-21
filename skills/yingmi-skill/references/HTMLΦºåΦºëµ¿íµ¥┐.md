# HTML 报告视觉模板（全场景共用）

## HTML 交付铁律（强制，写死）

凡生成**完整 HTML 报告页**（自包含 `<!DOCTYPE html>…`）时，执行模型**必须**遵守以下顺序与边界，**禁止跳过、颠倒或凭记忆臆造**。

1. **必读 ① — 当前场景技能的完整规范**  
   **完整阅读**本次生效的**场景技能**目录下 **`SKILL.md` 全文**，以及该文件指向且与本任务相关的 **`references/*`**（如 playbook、report-templates、板块表、工具链、输出顺序、字段与免责口径）。**正文结构、板块顺序、表格列、图表语义、工具调用顺序与结论边界**均以该 **`SKILL.md` 体系为准**。

2. **必读 ② — 统一视觉壳**  
   **完整阅读**本目录 [`demo-report.html`](demo-report.html)（路径：`skills/yingmi-skill/references/demo-report.html`）。生成物须**原样嵌入**其中的 **整段 `<style>`**（含水印 `body::before`、`qieman-icon.png` 等）、与 demo 一致的 **壳层 DOM 与 class**（如 **`report-header`**、`theme-btn`、`hero-card`、`card`、`section-title`、`disclaimer`、`footer`），以及 demo 中与主题切换一致的 **`<script>`**；有图表时再按需追加 ECharts 初始化。**禁止**自写大段 CSS 替代、**禁止**自造一套与 demo 不一致的版式或 class 体系。

3. **demo 与 SKILL 的权责划分（写死）**  
   - **`demo-report.html` 仅为 UI 壳与视觉示例**：其中的标题、KPI 文案、示例表格/图表、占位说明**不得**作为真实报告内容照抄输出。  
   - **真实报告的内容与模块**：必须来自 **① MCP/用户数据** + **② 当前场景 `SKILL.md` 规定的章节与规则**。若 demo 的示例板块与当前 `SKILL.md` 的板块表不一致，**以 `SKILL.md` 为准**组织内容，**以 demo 为准**套用样式与壳层。

4. **禁止事项**  
   未读 **`SKILL.md` + `demo-report.html` 就输出 HTML**；仅用 demo 想象业务结构；省略当前技能要求的板块；把 demo 占位数字/结论写入交付物。

**历史表述**：部分技能正文仍写「Topbar」— 实施时**等价于** demo 中的 **`report-header`**（且慢图标 + 标题区 + 深浅色切换），与 [`demo-report.html`](demo-report.html) 保持一致即可。

---

视觉基调与 **`qieman-design-pdf`**（`template-preview.html` / `SKILL.md`）对齐：**品牌蓝 `#1B88EE`、报告型浅蓝白渐变页底、白底半透明卡片 + 轻边框 + 低干扰阴影**，区别于营销 H5。涨跌色、深浅色主题切换仍按 `demo-report.html` 实现。

## 文件

- **样式与组件基准**（本 skill 内路径）：[`demo-report.html`](demo-report.html)
- 其他场景 skill 从各自目录引用：`../yingmi-skill/references/demo-report.html`

## 定位

`demo-report.html` 为全库统一 **UI 壳**（布局、CSS 变量、class、主题切换、水印）。**权责与必读顺序**见上文「HTML 交付铁律」；示例正文与数字禁止写入交付物。

## 品牌与背景

1. **顶栏图标（清晰）**：`report-header` 内继续使用 **`<img class="brand-icon" src="qieman-icon.png" …>`**（与 `demo-report.html` 同目录，生成物需带上该文件或等价 URL）。
2. **全页水印（淡化）**：由 **`body::before`** 实现，同一 `qieman-icon.png` **`background-size: contain`**、**低透明度**（浅色约 `0.055`，深色略降），固定在视口右上区域，**`pointer-events: none`**，与浅色渐变底自然融合；**勿删除**该规则，否则与规范不一致。
3. **字体**：中文优先 **Noto Sans SC / 思源黑体族**（与 PDF 技能一致），见 demo 中 `font-family` 栈。

## 生成 HTML 时（操作清单）

> **与各场景 `SKILL.md` 中的「第零步：加载视觉模板」同义**：技能内不必再重复粘贴长段「如何读取 demo」说明，**以本节 + 铁律为准**即可。

1. **已执行**上文「HTML 交付铁律」中的 **必读 ① + 必读 ②**，再开始拼 DOM。  
2. 将 `demo-report.html` 的 `<style>` **完整**放入输出 `<head>`（含 **`body::before` 水印**、`:root` 中 **`--chart-1`～`--chart-6`** 等；可与业务页一并保留 ECharts `<script>` 外链）。  
3. **壳层结构**：**`report-header`**（`qieman-icon.png` + `brand-heading` / `brand-sub` + `theme-btn`）、`hero-card`、`kpi-grid`、`card` / `ai-card`、`section-title`、`disclaimer`、`footer` 等 **class 与 demo 保持一致**；**各板块是否出现、顺序与内部字段**以**当前场景 `SKILL.md`** 为准。  
4. **脚本**：有图表则引入 ECharts；系列色建议按 `--chart-1`～`--chart-6` 与 **`qieman-design-pdf` §6.1** 一致。**主题切换**与 demo 一致。  
5. **禁止**：自写大段 CSS、自造 class、拼「类似」但不同的 DOM；照抄 demo 里的任何示例数据或结论；去掉水印或顶栏图标。

**再次强调**：本文件 + `demo-report.html` 只管「长什么样、用什么壳」；**「写什么、写几段、哪些表图」完全服从各场景 `SKILL.md`**。

**数据真实性**：各场景共用的 MCP 零容忍条款见 [MCP数据真实性零容忍.md](MCP数据真实性零容忍.md)（各 `SKILL.md` 内已引用 §1/§2/§3）。
