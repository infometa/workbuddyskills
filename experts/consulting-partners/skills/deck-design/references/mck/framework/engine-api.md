# Engine API Reference — MckEngine

> 框架级规范。67个高级方法速查表，每个方法对应一张幻灯片。
> 详细代码模板见 `references/layouts/` 对应文件。

## Setup

```python
import sys, os
sys.path.insert(0, os.path.expanduser('~/.workbuddy/skills/mck-ppt-design'))
from mck_ppt import MckEngine
from mck_ppt.constants import *  # NAVY, ACCENT_BLUE, BG_GRAY, etc.

eng = MckEngine(total_slides=N)  # N = 计划总页数（用于页码）
eng.save('output/deck.pptx')     # 自动 full_cleanup，无需手动清理
```

## Dependencies

```bash
pip install python-pptx lxml
# 封面图生成额外需要：
pip install tencentcloud-sdk-python rembg pillow numpy
```

---

## Methods by Category

### A. Structure（结构导航）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.cover(title, subtitle='', author='', date='', cover_image=None)` | #1 | 封面页。cover_image: None/`'auto'`/文件路径 |
| `eng.toc(title='目录', items=None, source='')` | #6 | 目录页。items: [(num, title, desc)] |
| `eng.section_divider(section_label, title, subtitle='')` | #5 | 章节分隔页 |
| `eng.appendix_title(title, subtitle='')` | #7 | 附录标题页 |
| `eng.closing(title, message='', source_text='')` | #36 | 结束页 |

### B. Data & Stats（数据统计）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.big_number(title, number, unit='', description='', detail_items=None, source='', bottom_bar=None)` | #8 | 大数字页 |
| `eng.two_stat(title, stats, detail_items=None, source='')` | #9 | 双数据对比 |
| `eng.three_stat(title, stats, detail_items=None, source='')` | #10 | 三指标仪表盘 |
| `eng.data_table(title, headers, rows, col_widths=None, source='', bottom_bar=None)` | #11 | 数据表格 |
| `eng.metric_cards(title, cards, source='')` | #12 | 指标卡片行 |
| `eng.metric_comparison(title, metrics, source='')` | #62 | 指标前后对比 |

### C. Frameworks & Matrices（框架矩阵）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.matrix_2x2(title, quadrants, axis_labels=None, source='', bottom_bar=None)` | #13 | 四象限矩阵 |
| `eng.table_insight(title, headers, rows, insights, col_widths=None, insight_title='启示：', source='', bottom_bar=None)` | #71 | 表格+洞见（推荐开篇用） |
| `eng.pyramid(title, levels, source='', bottom_bar=None)` | #15 | 金字塔 |
| `eng.process_chevron(title, steps, source='', bottom_bar=None)` | #16 | 流程箭头 |
| `eng.venn(title, circles, overlap_label='', right_text=None, source='')` | #17 | 维恩图 |
| `eng.temple(title, roof_text, pillar_names, foundation_text, pillar_colors=None, source='')` | #18 | 殿堂框架 |
| `eng.staircase(title, steps, source='', bottom_bar=None)` | #15b | 阶梯进化图 |

### D. Comparison & Evaluation（对比评估）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.side_by_side(title, options, source='')` | #19 | 左右对比 |
| `eng.before_after(title, before_title, before_points, after_title, after_points, source='')` | #20 | 前后对比 |
| `eng.pros_cons(title, pros_title, pros, cons_title, cons, conclusion=None, source='')` | #21 | 优劣分析 |
| `eng.rag_status(title, headers, rows, source='')` | #22 | 红绿灯状态 |
| `eng.scorecard(title, items, source='')` | #23 | 计分卡 |
| `eng.checklist(title, columns, col_widths, rows, status_map=None, source='', bottom_bar=None)` | #61 | 检查清单 |
| `eng.swot(title, quadrants, source='')` | #65 | SWOT 分析 |

### E. Narrative（内容叙事）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.executive_summary(title, headline, items, source='')` | #24 | 执行摘要 |
| `eng.key_takeaway(title, left_text, takeaways, source='')` | #25 | 核心洞见 |
| `eng.quote(quote_text, attribution='')` | #26 | 引言页 |
| `eng.two_column_text(title, columns, source='')` | #27 | 双栏文本（⚠️全局≤1张） |
| `eng.four_column(title, items, source='')` | #28 | 四栏概览 |
| `eng.numbered_list_panel(title, items, panel=None, source='')` | #69 | 编号列表+侧边栏 |

### F. Timeline & Process（时间流程）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.timeline(title, milestones, source='', bottom_bar=None)` | #29 | 时间轴/路线图 |
| `eng.vertical_steps(title, steps, source='', bottom_bar=None)` | #30 | 垂直步骤 |
| `eng.cycle(title, phases, right_panel=None, source='')` | #31 | 循环图 |
| `eng.funnel(title, stages, source='')` | #32 | 漏斗图 |
| `eng.value_chain(title, stages, source='', bottom_bar=None)` | #67 | 价值链/水平流程 |

### G. Team & Cases（团队专题）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.meet_the_team(title, members, source='')` | #33 | 团队介绍 |
| `eng.case_study(title, sections, result_box=None, source='')` | #34 | 案例研究 |
| `eng.action_items(title, actions, source='')` | #35 | 行动计划 |
| `eng.case_study_image(title, sections, image_label, kpis=None, source='')` | #45 | 带图案例 |

### H. Charts — BLOCK_ARC（圆形图表）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.donut(title, segments, center_label='', center_sub='', source='')` | #48 | 环形图（最多6段）|
| `eng.pie(title, segments, source='')` | #64 | 饼图（最多6段）|
| `eng.gauge(title, pct, label='', source='')` | #55 | 仪表盘 |

### I. Charts — Bar/Line（柱线图）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.grouped_bar(title, categories, series, data, max_val, source='', bottom_bar=None)` | #37 | 分组柱状图（最多6类×3系列）|
| `eng.stacked_bar(title, categories, series, data, source='', bottom_bar=None)` | #38 | 堆叠柱状图 |
| `eng.horizontal_bar(title, items, source='', bottom_bar=None)` | #39 | 水平柱状图/排名 |
| `eng.line_chart(title, categories, series, data, source='', bottom_bar=None)` | #50 | 折线图/趋势 |
| `eng.stacked_area(title, categories, series, data, source='')` | #70 | 堆叠面积图 |

### J. Charts — Advanced（高级图表）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.waterfall(title, items, source='')` | #49 | 瀑布图 |
| `eng.pareto(title, items, source='')` | #51 | 帕累托图 |
| `eng.progress_bars(title, items, source='')` | #52 | KPI 进度条 |
| `eng.bubble(title, points, x_label='', y_label='', source='')` | #53 | 气泡图 |
| `eng.risk_matrix(title, items, source='')` | #54 | 风险矩阵 |
| `eng.harvey_ball(title, headers, rows, source='')` | #56 | Harvey Ball 状态表 |

### K. Dashboards（仪表盘）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.dashboard_kpi(title, kpis, chart_data, takeaways, source='')` | #57 | KPI+图表仪表盘 |
| `eng.dashboard_table(title, table_data, chart_data, factoids, source='')` | #58 | 表格+图表仪表盘 |

### L. Image Layouts（图文版式）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.content_right_image(title, content, image_path=None, source='')` | #40 | 内容+右侧图 |
| `eng.left_image_content(title, content, image_path=None, source='')` | #41 | 左图+内容 |
| `eng.three_images(title, images, source='')` | #42 | 三图 |
| `eng.image_four_points(title, points, image_path=None, source='')` | #43 | 图+四要点 |
| `eng.hero_image(title, text, image_path=None, source='')` | #44 | 全宽背景图 |
| `eng.two_col_image_text(title, items, source='')` | #68 | 双栏图文 |

### M. Special（特殊版式）

| Method | Pattern# | Description |
|--------|----------|-------------|
| `eng.stakeholder_map(title, stakeholders, source='')` | #59 | 利益相关方地图 |
| `eng.decision_tree(title, nodes, source='')` | #60 | 决策树 |
| `eng.icon_grid(title, items, source='')` | #63 | 图标网格（4×2或3×3）|
| `eng.agenda(title, items, source='')` | #66 | 议程/会议大纲 |

---

## Content-to-Layout Quick Match

| 内容类型 | 推荐版式 |
|---------|---------|
| 单个关键数据 | `big_number` |
| 2个选项对比 | `side_by_side`, `before_after` |
| 3–4个并列概念 | `table_insight`(⭐推荐), `metric_cards`, `four_column` |
| 流程/步骤 | `process_chevron`, `vertical_steps`, `value_chain` |
| 时间线 | `timeline` |
| 数据表格 | `data_table`, `scorecard` |
| 案例研究 | `case_study` |
| 摘要/结论 | `executive_summary`, `key_takeaway` |
| 多 KPI | `three_stat`, `dashboard_kpi` |
| 时间序列数据 | `grouped_bar`, `line_chart`, `stacked_bar` |
| 占比/构成 | `donut`, `pie` |
| 风险/评估矩阵 | `risk_matrix`, `swot`, `matrix_2x2` |
| 开篇高影响力 | `table_insight`(#1), `big_number`(#2), `key_takeaway`(#3) |
