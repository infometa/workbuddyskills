---
name: deck-design
description: |
  交付物生成工具：以假设驱动、证据分级和 Title Storyboard 为上游，使用统一 DeckSpec 与双引擎 Fusion 管线生成可审计的专业咨询 PPT；同时支持 Excel 测算底稿排版。
  触发词：把这份分析做成PPT、出一份能直接汇报的演示文稿、产出ppt、帮我把测算结果整理成Excel、生成幻灯片。
allowed-tools: Read,Write,Bash
---

# 专业咨询 PPT 与 Excel 交付

目标是生成可直接用于高层决策的顶级咨询风演示：标题连读构成完整论证，每页只证明一个主张，正文证据能够证明标题，视觉节奏服务于内容。

## 品牌边界

- 只复制顶级咨询的结构化表达、克制视觉和质量标准。
- 不使用麦肯锡 Logo、品牌模板、专有定制字体或其他受保护品牌资产。
- 不声称、暗示或标注“麦肯锡出品”“McKinsey produced”。
- 默认使用本包统一主题与可用系统字体；品牌要求以用户合法提供的品牌规范为准。

## 视觉完成度硬标准

- “咨询风”不等于白底文字堆叠。无图片时封面也必须使用深海军蓝 Hero 构图、明确焦点和克制几何元素；章节页使用深色转场，内容页保持高留白与强对齐。
- 全篇必须形成封面 / Hero 关键结论 / Supporting 证据 / Transition 转场的层级变化，不允许连续三页使用同构等宽卡片。
- 每页只设置一个视觉锚点和一个主强调色；数据比较优先使用可编辑图表、矩阵、时间线、瀑布或表格，不用大段项目符号冒充分析。
- 禁止楷体、书法体、表情符号、彩虹配色、厚阴影、伪 3D、随机渐变和无意义装饰图标。中文默认使用现代无衬线 Office 兼容字体。
- 精美必须建立在信息层级、证据关系和精确网格上；不得以整页图片栅格化换取“好看”，文本、图表、表格和基础图形必须可编辑。

## 强制输入链路

PPT 请求不得从主题或原始材料直接跳到版式生成：

- 有完整材料：材料诊断 -> Deck Brief -> Governing Thought -> Title Storyboard。
- 只有主题：先用 hypothesis-framing，必要时用 evidence-analysis，形成 Day-1 假设、证据缺口和默认商务假设，再进入 Deck Brief。
- 信息不足时使用标记为 [A]/[E] 的专业默认假设推进，不得纯反问。
- 默认同一轮从骨架自动推进到成品。只有用户明确要求“先审大纲/故事线”时，才在 D2 Gate 后暂停。

## D0-D7 端到端流程

### D0 意图对齐与材料诊断

明确受众、决策、场景、页数、时限、已有材料、数据口径和敏感边界。识别事实、推断、假设、估算及证据缺口。输出 `deck_brief.md`。

### D1 Governing Thought 与故事线

用金字塔原理组织唯一顶层结论；按 SCQA/SCR 或 Situation-Problem-Resolution 展开；分支必须 MECE。输出 `storyline.md`，包含 Executive Summary 草案与 Appendix 边界。

### D2 Title Storyboard Gate

先只写行动标题，不写正文。标题连读必须让决策者理解完整论证；每个内容页标题是可被证据验证的完整主张，不是主题标签。未通过以下门禁不得选版式：

1. 顶层结论回答 Deck Brief 中的决策问题。
2. 标题链条呈现“背景/张力 -> 发现 -> 含义 -> 建议/行动”。
3. 相邻标题无跳步、重复或互相矛盾。
4. 每页只承载一个主张；Executive Summary 与正文标题一一对齐。
5. 事实与推断已映射到 claim_id，证据缺口显式标 [A]/[E]。

详见 `references/storyline-system.md`。

### D3 Page Brief、Evidence Map 与视觉节奏

为每页确定：`role`、`rhythm`、`visual_role`、`anti_pattern`、`density`、`objective`、`one_message`、证据和来源。

- `role`：Hero / Supporting / Transition。Hero 建议占 20%-30%。
- `rhythm`：Peak / Valley / Transition，避免连续高密或连续过空。
- 非对称版式建议不少于 40%；相邻页面不重复同一版式，除非比较任务要求刻意一致。
- 版式由内容关系决定；图表由比较关系决定，并只突出一个信息。

### D4 统一 DeckSpec 与 S3 内容门禁

把 Page Brief 写入唯一机器输入 `deck_spec.json`。禁止同时维护多套输入协议，禁止 Agent 手写 `FusionDeck` 调用代码。

统一字段和示例见 `references/deck-spec.md`。运行：

```bash
python3 scripts/gate_check_s3.py <project_dir>/deck_spec.json <project_dir>
```

`gate_s3.json.passed` 必须为 `true`。空 slides、页码不连续、未知版式、标签式标题、缺少页面语义字段、占位符、错误 evidence/source 结构均须失败。

### D5 统一 Build CLI 生成

只允许使用统一 CLI：

```bash
python3 scripts/build_fusion_deck.py \
  --spec <project_dir>/deck_spec.json \
  --output <project_dir>/<name>.pptx \
  --result <project_dir>/build_result.json
```

CLI 同时支持 `mck_ppt` 主引擎和 `mckinsey_pptx` 补充引擎。任何一页失败、未知引擎/版式、实际页数不等于声明页数，整次构建必须失败，不得跳页或交付部分文件。

### D6 S4 机读门禁、真实渲染与视觉 QC

先运行机读门禁，再执行渲染探测：

```bash
python3 scripts/gate_check.py <project_dir>/<name>.pptx <project_dir>
python3 scripts/render_preview.py <project_dir>/<name>.pptx <project_dir>
```

`render_preview.py` 优先使用 LibreOffice + pdftoppm 全量渲染；不可用时显式降级为 macOS Quick Look 首屏预览；若 Quick Look 也不可用，则只输出逐页结构报告并标记 `mode=structure_only`。所有模式都会写出 `render_result.json`。随后逐页执行 `references/visual-qc.md`：三秒测试、标题/正文证据、网格、字体、颜色、图表、Source、页码、占位符、数字一致性和可编辑性。

- 有 LibreOffice/PowerPoint 等真实渲染能力：必须全量逐页预览并记录视觉结论。
- 真实渲染不可用：允许用 macOS `qlmanage` 生成首屏预览，并按逐页结构报告审阅内容；Quick Look 也不可用时只能标记为 `structure_only`。两种情况都必须在交付说明中写明“视觉门禁已降级，未完成全量真实渲染”，不得声称全量渲染通过。
- `gate_result.json.passed != true` 或视觉 QC 有阻断项时，返回 D3-D5 修复。

### D7 正式交付与质量审计

正式交付前必须加载 `quality-audit`，覆盖 Storyline、标题、证据、视觉和完整性。交付：最终 `.pptx`、门禁结果摘要、渲染状态、关键假设和待补证据。未经质量审计不得称为正式版。

## 统一项目产物

每个 PPT 项目目录必须保持以下契约：

```text
<project_dir>/
  deck_brief.md
  storyline.md
  deck_spec.json
  gate_s3.json
  build_result.json
  gate_result.json
  render_result.json
  preview/
  <final-name>.pptx
```

不得用 `content.json`、`outline.json` 或 Agent 临时 Python 代码替代 `deck_spec.json`。最终文件默认落到 `deliverables/consulting/` 下的独立项目目录。

## 双引擎选型

- 主引擎 `mck_ppt`：结构页、摘要、KPI、表格、流程、对比、矩阵、常规图表等。
- 补充引擎 `mckinsey_pptx`：甘特图、增长-份额矩阵、增强气泡图、历史/预测柱图等。
- 主引擎完整签名见 `references/mck/framework/engine-api.md`；补充版式见 `mckinsey_pptx/agent/CATALOG.md`。
- `process_chevron` 统一为 2-5 步，超过 5 步必须合并或拆页。

## 图表纪律

1. 时间趋势 -> 折线图；类别比较 -> 条形/柱形；构成 -> 堆叠或环形；增量归因 -> 瀑布图；双变量定位 -> 散点/气泡/矩阵。
2. 每张图只强调一个信息，用标题和单一强调色指出结论。
3. 图表必须由真实数据驱动；缺数据时用 [A]/[E] 明示，不得伪造。
4. Source 是结构化数组，在生成时统一渲染为页脚来源；Footnote 解释口径，不替代来源。

## ⚠️ deck_spec.json 数据格式（最高频失败点，必读）

**铁律：`data` 字段中所有复合数据一律使用数组/元组格式，绝不传字典/对象。**

引擎内部通过 Python 解包获取值。传入 `{"key": "value"}` 格式会导致页面显示 key 名称而非实际数据。

**核心规则：**
1. 所有复合字段用数组 `[[a, b, c]]`，不用 `[{key: val}]`
2. label/编号 ≤3 字符（推荐 "01"-"05"）
3. `detail_items` 是单个 `\n` 拼接的字符串，不是数组
4. `col_widths` 永远不传（传数字=列宽为零=文字竖排）
5. `grouped_bar` / `horizontal_bar` / `swot` 需要 RGBColor，JSON 无法用，改用替代版式
6. `desc` ≤50 字符

**完整版式数据格式参考：** 详见 `references/layout-data-format.md`（生成 `deck_spec.json` 前必须查阅）。

**速查对照（最高频错误）：**

| 版式 | 关键字段 | ✅ 正确 | ❌ 错误 |
|------|---------|--------|--------|
| `two_stat`/`three_stat` | stats | `[["449亿", "标签", true]]` | `[{value, label}]` |
| `side_by_side` | options | `[["标题", "内容\n内容"]]` | `[{heading, points}]` |
| `process_chevron` | steps | `[["01", "标题", "描述≤50字"]]` | `[{label, detail}]` |
| `executive_summary` | items | `[["01", "标题", "描述"]]` | `["纯字符串"]` |
| `data_table` | col_widths | **不传** | `[8, 15, 22]` |

## Excel 测算底稿

数据区与结论区物理分离：Sheet1 假设参数与来源；Sheet2 计算过程，公式引用 Sheet1；Sheet3 结果汇总。关键数字与 PPT 使用同一口径和 claim_id。
