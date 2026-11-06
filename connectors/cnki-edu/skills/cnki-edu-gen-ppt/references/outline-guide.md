# 两级大纲规范（步骤 2）

本文件定义大纲的结构、二级摘要写法与表格格式。大纲仅支持**两级**，不得出现三级。

## 一、结构规则

- **一级标题**：模块/篇章，数量建议 5–9 个（含末尾固定的"总结"一章）。**须先合并内容相同或高度重合的一级标题**（如多个"知识讲解""原理分析"归并为一章），杜绝章节碎片化与同名重复。
- **二级标题**：每个一级下的具体页面，每章 1–4 个二级标题；全篇二级标题总数约等于目标页数（扣除封面/目录）。**相邻或跨章语义重复的二级标题须先合并为一条**，避免同一内容出现两次。
- **字数硬约束**：一级标题、二级标题**均不超过 20 个汉字**（标点、阿拉伯数字、英文单词不计入汉字计数，但整体仍须精炼）；超长须压缩或拆分，不得用"……"等截断占位。
- **标题优化扩展**：一级/二级标题应经**优化与适度扩展**，表述完整、有信息量（避免"讲授""说明"等干瘪短语），但仍受 20 字上限约束。
- 末尾固定一章：
  1. `总结` → 二级标题：`本PPT核心结论与要点回顾`（内容步骤 3 填充）

## 二、二级内容摘要写法

为每个二级标题写**一句话摘要**（15–40 字），说明该页"讲什么、放什么"，例如：
- 差："讲授知识点。"（空泛）
- 好："用生活案例解释光合作用原理，配示意图与 1 道思考题。"

## 三、大纲输出格式（三字段表 · 相同内容只写一次、延续行留空）

- **表格列固定为三字段**：`一级标题 | 二级标题 | 内容摘要`，**不得包含"建议页数 / 配图建议 / 文献推荐"等额外列**。
- **顶部 PPT 名称 = 横跨三列的名称行**：PPT 名称占**一整行、横跨三列**（渲染环境执行内联 HTML 时用 `colspan="3"`；不支持时在表格正上方**单独一行、全宽**呈现）。**不得把名称塞进「一级标题」列**。

### 1. 合并只在内容层（**内容合并 · 单元格不合并 · 延续行留空**）

- **① 内容先去重**——内容相同或高度重合的**一级标题归并为同一章**（如多个"知识讲解""原理分析"合成一章）；相邻重复的**二级标题合并为一条**；相邻**摘要若讲同一件事先合并**。**相同内容只保留一处、绝不重复填写**。
- **② 单元格不做合并，延续行留空即可**——同一章节**首行正常填写一级标题**，其**后续行该列保持为空白单元格**（空白即表示"同上"、与上一行相同）。**不使用 `rowspan` 做纵向合并单元格，也不要求填写「〃」等占位符号。**
  - ⚠️ **留空 ≠ 漏填**：此处的空白是**有意的延续标记**（该列值与上一行相同），属**预期形态**；但如果确实有新的一级标题却故意不写，才算漏填。
  - ⚠️ **禁止"为了填满表格而重复填写"**：不得把相同内容在每一行再抄一遍。

### 2. 大纲**强制表格化**的写法（表格 · 相同内容只写一次 · 延续行留空 · 不做单元格合并）

- ⚠️ **大纲只能以表格形式呈现**：**禁止**改用非表格形态（层级分组式、缩进列表、要点清单等）。
- ⚠️ **单元格一律不做合并**：**不使用 `rowspan` 做相同内容的跨行合并**（仅"PPT 名称行"横跨三列的 `colspan` 除外，那是在表达"整行标题"，不是合并相同内容）。
- ⚠️ **相同内容的延续行：留空即可**——一级标题**仅在该章首行填写**，其**后续行该列保持空白单元格**（表示"同上"）；**不需要「〃」等占位符号，也不需要合并单元格**。
- ⚠️ **唯一禁止的是"重复填写"**：不得把相同内容在每一行再抄一遍；留空是**预期形态**，不算漏填。

- **写法（Markdown 表格 · 通用）**：

  ```
  《光合作用（初中生物教学课件）》

  | 一级标题 | 二级标题 | 内容摘要 |
  |---|---|---|
  | 课标导入 | 情境激趣 | 用"植物如何长大"提问引出本课主题 |
  |  | 目标锚定 | 出示本课 3 条学习目标 |
  | 知识讲解 | 概念界定 | 光合作用定义与反应物/产物辨析 |
  |  | 过程剖析 | 光反应与暗反应两阶段流程说明 |
  |  | 影响因素 | 光照/CO₂/温度对速率的影响 |
  | 例题活动 | 巩固练习 | 2 道典型题 + 小组讨论任务 |
  | 总结 | 核心结论回顾 | 回顾 3 个关键结论与易错点 |
  ```

- **写法（渲染环境执行内联 HTML 时 · 规则完全相同）**——仅名称行跨列，相同内容延续行同样**留空**（不 `rowspan`）：

  ```html
  <table style="border-collapse:collapse;width:100%">
    <tr><td colspan="3" style="text-align:center;border:0.5px solid #D3D1C7;padding:6px 10px">《光合作用（初中生物教学课件）》</td></tr>
    <tr><th style="border:0.5px solid #D3D1C7;padding:6px 10px">一级标题</th><th style="border:0.5px solid #D3D1C7;padding:6px 10px">二级标题</th><th style="border:0.5px solid #D3D1C7;padding:6px 10px">内容摘要</th></tr>
    <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px">知识讲解</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">概念界定</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光合作用定义与反应物/产物辨析</td></tr>
    <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">过程剖析</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光反应与暗反应两阶段流程说明</td></tr>
    <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">影响因素</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光照/CO₂/温度对速率的影响</td></tr>
  </table>
  ```

  ① 名称行用 `colspan="3"` 横跨整行；② 同一章节首行正常填写一级标题，后续行该列**留空**（延续"同上"语义）；③ 下一章节首行重新填写一级标题；④ **整表为一个 `<table>`**，不得拆成多张。

- **判定**：**两种渲染环境写法一致**——表格 + 相同内容只写一次 + 延续行留空；**均不做单元格合并**。

- **可选版式标注**：为保证"内容丰富、形式多样化"，可在「内容摘要」句末用括号轻量标注该页建议版式（如（图文）/（卡片）/（时间轴）/（对比）/（数据大字）/（表格）/（引言）/（双栏）），仅供步骤 3 生成时参考，不向用户强调内部名词。全篇版式应在多种类型间轮换，避免同质化。
- **版式标注的下游用途**：这些括号标注直接进入步骤 3 的 `STORY.md`（叙事逻辑）与 `DESIGN.md`（版式映射表），并最终映射为 `PPT 渲染工作流` 的 SlideDSL 版式（见 `generate-pptx-tencent.md` 第五节）。

## 四、示例（教学课件·光合作用·14 页）

**两种渲染环境的写法一致**：表格 + 相同内容只写一次 + **同一章节延续行的对应单元格留空**；**不做单元格合并**（仅名称行横跨三列）。**不得改用非表格的层级分组/缩进列表形态。**

```html
<table style="border-collapse:collapse;width:100%">
  <tr><td colspan="3" style="text-align:center;border:0.5px solid #D3D1C7;padding:6px 10px">《光合作用（初中生物教学课件）》</td></tr>
  <tr><th style="border:0.5px solid #D3D1C7;padding:6px 10px">一级标题</th><th style="border:0.5px solid #D3D1C7;padding:6px 10px">二级标题</th><th style="border:0.5px solid #D3D1C7;padding:6px 10px">内容摘要</th></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px">课标导入</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">情境激趣</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">用"植物如何长大"提问引出主题</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">目标锚定</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">出示本课 3 条学习目标</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px">知识讲解</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">概念界定</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光合作用定义与反应物/产物辨析</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">过程剖析</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光反应与暗反应两阶段流程图</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">影响因素</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">光照/CO₂/温度对速率的影响曲线</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px">例题活动</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">巩固练习</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">2 道典型题 + 小组讨论任务</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px"></td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">拓展迁移</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">举一个生活中的光合作用实例</td></tr>
  <tr><td style="border:0.5px solid #D3D1C7;padding:6px 10px">总结</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">核心结论回顾</td><td style="border:0.5px solid #D3D1C7;padding:6px 10px">回顾 3 个关键结论与易错点</td></tr>
</table>
```

Markdown 表格（渲染环境不执行内联 HTML 时 · 规则完全相同 · 仍是表格）：

```
《光合作用（初中生物教学课件）》

| 一级标题 | 二级标题 | 内容摘要 |
|---|---|---|
| 课标导入 | 情境激趣 | 用"植物如何长大"提问引出主题 |
|  | 目标锚定 | 出示本课 3 条学习目标 |
| 知识讲解 | 概念界定 | 光合作用定义与反应物/产物辨析 |
|  | 过程剖析 | 光反应与暗反应两阶段流程图 |
|  | 影响因素 | 光照/CO₂/温度对速率的影响曲线 |
| 例题活动 | 巩固练习 | 2 道典型题 + 小组讨论任务 |
|  | 拓展迁移 | 举一个生活中的光合作用实例 |
| 总结 | 核心结论回顾 | 回顾 3 个关键结论与易错点 |
```

> 注意：封面/目录/过渡页由生成流程按规范产出，**大纲只列内容章节（不列"封面"行）**，但须显式包含"总结"一章。知网推荐不进入大纲与 PPT，于最终交付时**紧接 PPT 卡片下方**作「知网推荐」呈现（**仅展示文献名/作者/来源三项**，**严禁在可见文案中暴露任何元数据**，仅文献名可点击且**带跳转链接**、**一次直达知网研学平台的研读页面**，**不附带悬停提示**）。
