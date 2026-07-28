# PPT Design System

本规范统一双引擎 Fusion 交付的主题、网格、字体和图表语言。生成统一由 `scripts/build_fusion_deck.py` 读取 `deck_spec.json` 完成；不得调用已废弃的四版式 `scripts/build_deck.py`。

## 品牌边界

仅采用顶级咨询风的结构化表达和克制视觉。不得使用麦肯锡 Logo、品牌模板、定制字体或声称麦肯锡出品。

## 专业精美的完成度标准

“咨询风”不等于白底加文字。默认成品必须同时满足以下视觉完成度：

- 封面采用暖色深底全幅 Hero 构图（暖炭灰 + 铜色强调）、明确的标题焦点与克制几何视觉；即使无外部图片也不得退化成纯白标题页。
- 章节页采用暖深色转场（底部铜色条带），与暖白底内容页形成 Peak / Valley 节奏；全篇至少包含封面、关键结论 Hero、章节转场三类视觉层级。
- 内容页遵循“一个行动标题 + 一个主要视觉关系 + 一个结论锚点”，禁止连续堆叠等宽文字卡片。
- 数据页优先用可编辑图表、矩阵、瀑布、时间线和对比结构，不用大段项目符号模拟分析。
- 图标只用于辅助扫描，保持同一线性风格；禁止表情符号、彩虹色、厚阴影、伪 3D、随机渐变和装饰性素材堆砌。
- 图片必须有证据或叙事作用，并与标题主张相关；低清截图、无来源图库图和整页栅格化均为阻断项。

## 主题与配色

双引擎统一使用 `MCK_ALIGNED_THEME`：

| 名称 | 色值 | 用途 |
|---|---|---|
| NAVY | #2C2C34 暖炭灰 | 行动标题、封面、关键结构 |
| WHITE | #FFFFFF | 留白和深色背景文字 |
| DARK_GRAY | #3D3D42 暖深灰 | 正文 |
| MED_GRAY | #7A7772 暖灰褐 | 次要信息、Source、Footnote |
| ACCENT_BLUE | #C47A2B 暖铜 | 唯一重点、关键数字或选中状态（实为暖色强调） |
| BG_GRAY | #FAF8F5 暖白 | 卡片和分区背景 |
| ACCENT_GREEN | #5E8C6A 鼠尾草绿 | 正面状态 |
| ACCENT_ORANGE | #D97B2D 赤陶 | 警示/次要强调 |
| ACCENT_RED | #B54C4C 玫瑰红 | 负面状态 |

整体色调偏暖（charcoal + copper + cream），一页以暖中性色为主，只用一个主强调色；状态色不可装饰性滥用。深色背景必须搭配高对比文字。

## 字体与字号

默认采用现代无衬线体系：西文 Arial，中文 Microsoft YaHei（由 Office 在不可用环境中自动回退到兼容系统字体）。标题与正文保持同一字体家族，通过字号、字重与留白建立层级；不使用书法体、楷体或品牌专有字体。

| 用途 | 建议字号 |
|---|---|
| 封面标题 | 38-44pt |
| 行动标题 | 22pt |
| 章节标题 | 30-36pt |
| 分组标题 | 14-18pt |
| 正文 | 12-14pt |
| Source / Footnote | 9pt |

不得通过将正文缩到 8pt 以下解决溢出；应缩短文案、拆页或换承载力更合适的版式。

## 网格

- 画布：13.333 x 7.5 英寸，16:9。
- 左右边距：0.8 英寸。
- 行动标题区：顶部 0.15-1.05 英寸。
- 主内容区：约 1.3-7.05 英寸。
- Source、Footnote、页码位于统一页脚区。
- 非对称版式建议不少于全篇 40%；相邻页面不重复同一版式，除非需要严格比较。

## 页面角色与节奏

- Hero：关键结论、关键数字、核心选择；建议占 20%-30%。
- Supporting：证据、机制、比较、案例。
- Transition：章节切换和论证转向。
- 用 Peak / Valley / Transition 控制密度，避免连续高密或连续空页。

版式由内容关系决定，不为“多样”而随机换版式。

## 版式选型

| 内容关系 | 推荐版式 |
|---|---|
| 顶层结论 | executive_summary / key_takeaway / dark_navy_summary |
| 单一关键数字 | big_number / stat_hero |
| 多指标 | metric_cards / three_stat / dashboard_kpi_chart |
| 分类比较 | horizontal_bar / grouped_bar / column_comparison |
| 时间趋势 | line_chart / column_historic_forecast |
| 构成 | stacked_bar / donut / pie |
| 增量归因 | waterfall |
| 取舍与选项 | side_by_side / pros_cons / comparison_table |
| 二维定位 | matrix_2x2 / bubble / growth_share |
| 流程与价值链 | process_chevron / value_chain / process_flow_horizontal |
| 路线图 | timeline / waves_timeline_4 / gantt_timeline |
| 详细数据 | data_table / scorecard / assessment_table |

`process_chevron` 统一支持 2-5 步；超过 5 步必须合并阶段或拆页。其他流程/矩阵类页面也以最多 5 个主要步骤或维度为默认上限，避免密度冲突。

## 图表纪律

- 时间趋势用折线或历史/预测柱图；类别规模用条形/柱形；构成用堆叠或环形；增量用瀑布；双变量用散点/气泡/矩阵。
- 每张图只突出一个信息，行动标题直接说出该信息。
- 图表由真实数据驱动；[A]/[E] 必须显式标注。
- Source 为结构化数组，构建时统一渲染；Footnote 解释口径。

## 信息密度与页面自检

- 每页只证明一个主张，正文必须证明标题。
- 每页通常不超过 6 个主要要点；复杂内容拆页而非压字。
- 三秒内能识别行动标题、视觉锚点和唯一结论。
- 检查溢出、重叠、无意留白、占位符、数字一致性、可编辑性和页码 `N/total`。
- 机读门禁不能替代真实渲染；渲染降级规则见 `visual-qc.md`。