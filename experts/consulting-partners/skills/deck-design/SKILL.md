---
name: deck-design
description: |
  交付物生成工具：PPT专业化生成(双引擎:mck_ppt 67版式 + mckinsey_pptx 补充版式,统一麦肯锡深蓝皮肤)、Excel测算底稿排版。
  触发词：把这份分析做成PPT、出一份能直接汇报的演示文稿、产出ppt、帮我把测算结果整理成Excel、生成幻灯片。
allowed-tools: Read,Write,Bash
---

# 交付：专业级 PPT 与 Excel 生成

把分析和文字变成**能直接进董事会的成品 PPT**——不是"标题+一列小字+大片留白"的骨架，
而是版式丰富、图表克制、信息密度饱满、经得起挑剔视觉审美检验的麦肯锡风演示。

> ⚠️ 本 skill 已于 2026-07 重构：废弃旧的 `build_deck.py`(仅4版式,产出过于简陋),
> 改用双引擎 `mck_fusion.FusionDeck`。**禁止再调用 `build_deck.py`(见文末已废弃说明)。**

## 引擎与依赖

**双引擎融合**(统一麦肯锡深蓝皮肤 MCK_ALIGNED_THEME,两套引擎同色同网格同字号):
- 主引擎 `mck_ppt`(Apache-2.0, 源自 likaku/Mck-ppt-design-skill)：67 种专业版式 + 中文楷体注入 + 机读门禁。
- 补充版式 `mckinsey_pptx`(MIT, 源自 seulee26/mckinsey-pptx)：甘特图/BCG矩阵/气泡图等主引擎相对弱或缺的版式。

**依赖**(见 requirements.txt)：核心仅 `python-pptx>=1.0.0` + `lxml>=4.9.0`。
首次使用先装：`pip install python-pptx lxml`。
(可选：`Pillow numpy rembg tencentcloud-sdk-python` 仅用于 AI 自动生成封面图,不装则用纯色封面,不影响主流程。)

## 五阶段流程(S1→S5,禁止跳步)

**S1 需求** — 明确：给谁看(董事会/内部评审)、要几页、核心结论是什么、有哪些真实数据。
**S2 骨架** — 给出每页的"标题 + 核心论点 + 选用版式"清单(用下方统一版式目录选型),确认骨架后再填充。
**S3 内容填充** — 逐页把**真实血肉**填进每个版式的入参(不是一句话结论,要带论据/数据/展开)。
   ⚠️ 严格按每种版式的入参 schema(见下方速查),入参结构错会直接报错。
**S4 渲染 + 门禁** — 用 FusionDeck 生成 pptx,然后**必须跑 `scripts/gate_check.py` 机读门禁**。
   门禁不过(留白超标/文字溢出/图例溢出/内容太空)**不得交付**,回 S3 修。
   **禁止口头声称"已通过校验"** —— 必须实际跑门禁脚本、贴出 gate_result.json 的 passed=true。
**S5 交付** — 产出文件路径 + 一句话说明每页用了什么版式,落到 `deliverables/consulting/`。

## 生成方式(代码模板)

```python
import sys
sys.path.insert(0, '<本skill目录绝对路径>')  # 含 mck_ppt / mckinsey_pptx / mck_fusion.py
from mck_fusion import FusionDeck

d = FusionDeck(total_slides=8)             # total_slides 用于页码
# —— 主引擎 67 版式：d.eng.<方法>(...) ——
d.eng.cover(title="...", subtitle="...", date="2026-07")
d.eng.executive_summary(title="...", headline="...", items=[(1,"标题","说明"), ...])
d.eng.big_number(title="...", number="24", unit="个月", description="...", detail_items=["...","..."])
# —— 补充版式：d.mck("<类型>", ...) 自动套统一皮肤 ——
d.mck("column_historic_forecast", title="...", categories=[...], values=[...], forecast_from_index=2, ...)
d.mck("growth_share", title="...", bus=[{"name":..,"x":..,"y":..,"size":..}, ...])
d.save("deliverables/consulting/xxx-deck.pptx")
```

主引擎完整 67 方法签名见 `references/mck/framework/engine-api.md`；补充版式见 `d.available_fusion_layouts()`
与 `mckinsey_pptx` 的 CATALOG。

## 统一版式目录(按内容选型)

| 内容类型 | 推荐版式 | 引擎 |
|---------|---------|------|
| 封面/章节/结束 | `cover` `section_divider` `closing` | mck |
| 摘要/核心结论 | `executive_summary` `key_takeaway` | mck |
| 单个关键数字 | `big_number` | mck |
| 多 KPI/指标 | `three_stat` `metric_cards` `dashboard_kpi` | mck |
| 3-4 并列概念 | `table_insight`⭐ `four_column` `metric_cards` | mck |
| 流程/步骤 | `process_chevron` `vertical_steps` `value_chain` | mck |
| 时间线/路线图 | `timeline` | mck / `waves_timeline_4` `gantt_timeline`(补充) |
| 优劣/取舍对比 | `pros_cons` `side_by_side` `before_after` | mck |
| 四象限/矩阵 | `matrix_2x2` `swot` `risk_matrix` | mck / `growth_share`(BCG,补充) |
| 时间序列数据 | `grouped_bar` `line_chart` | mck / `column_historic_forecast`(历史vs预测,补充) |
| 占比构成 | `donut` `pie` | mck |
| 增量归因 | `waterfall` | mck |
| 二维定位分布 | `bubble`(mck) / `bubble_chart`(补充) | 两者 |
| 主题趋势(恰好3个) | `three_trends_numbered/table/icons`(补充) | 补充 |
| 行动计划 | `action_items` | mck |
| 数据表 | `data_table` `scorecard` | mck |

## 版式入参 schema 速查(常踩的坑,务必按此)

- `executive_summary(title, headline, items, source='')` — **items 是 `(编号, 标题, 说明)` 三元组**,如 `[(1,"护城河","...")]`。
- `pros_cons(title, pros_title, pros, cons_title, cons, conclusion=None)` — **conclusion 是 `(标签, 文字)` 元组**,不是字符串。
- `action_items(title, actions)` — **actions 是 `(动作标题, 时间, 说明, 责任人)` 四元组**,顺序固定。
- `big_number(title, number, unit='', description='', detail_items=None)` — detail_items 是 `list[str]`。
- `process_chevron(title, steps)` — steps 是 `(标签, 步骤标题, 说明)` 三元组,支持 2-7 步。
- `d.mck("column_historic_forecast", categories=[...], values=[...], forecast_from_index=N, ...)` — forecast_from_index 指第几个起为预测。
- `d.mck("growth_share", bus=[{"name","x","y","size","quadrant"?}])` — x=市场份额, y=增长率, size=气泡大小。
- 拿不准就先读 `references/mck/framework/engine-api.md` 对应方法签名,不要猜。

## 图表选型纪律(红线)

只选能被**真实数据**驱动的图表。找不到真实数据支撑的图表,宁可换成对比表格或文字论述,
**绝不编造数据凑一张"看起来专业"的图**。数据来源用 `[E]`(估算)/`[A]`(假设) 标注。

## 中文注意(见 references/mck/experiences/cjk-issues.md)

- 中文默认注入楷体东亚字体(引擎已内置),无需手动设置。
- 长标题/长 bullet 易 overflow：标题控制在 ~30 字内,bullet 单行 ~40 字内,超长拆分或换承载力更强的版式。
- 门禁 `gate_check.py` 会检测溢出,不过则缩短文案。

## 反"骨架化"硬纪律(针对历史事故)

1. **禁止大面积用纯 bullet 页**。同样的内容,`executive_summary`/`metric_cards`/`process_chevron`
   比"标题+一列 bullet"信息密度高一个量级。纯文字列表页占比要低。
2. **每页形状数应远大于 2**(旧骨架每页仅 2 个形状)。生成后可用 python-pptx 体检:
   `len(slide.shapes)` 普遍应 ≥ 8。过空的页回 S3 换富版式。
3. **S4 门禁必跑、必贴结果**。不许跳过、不许口头声称通过。

## Excel 测算底稿(不变)

数据区(原始输入+来源)与结论区(计算结果)物理分离；假设参数单列一个 Sheet 便于复核；
Sheet1 假设参数 / Sheet2 计算过程(公式引用 Sheet1,不硬编码) / Sheet3 结果汇总(面向决策者)。

## 页面自检清单(每页完成后过一遍)

- [ ] 版式与骨架一致,且不是"能用富版式却用了光秃 bullet"
- [ ] 图表类型匹配真实数据结构,无编造
- [ ] 中文无溢出、无乱码
- [ ] 配色/字号统一(两套引擎都走 MCK_ALIGNED_THEME)
- [ ] 信息密度饱满,无大片留白
- [ ] S4 门禁 passed=true

## 已废弃

`build_deck.py`(旧的 4 版式骨架生成器)**已废弃,禁止调用**。它是本次事故("产出 PPT 极其简单")的根源。
一切 PPT 生成走 `mck_fusion.FusionDeck`��旧文件保留仅作历史对照,已在文件头标注 DEPRECATED。
