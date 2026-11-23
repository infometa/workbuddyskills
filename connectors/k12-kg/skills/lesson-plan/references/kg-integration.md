# k12-kg 图谱集成说明（lesson-plan 数据底座）

> 连接器：k12-kg MCP（kservice 外网实例，只读）。本文件是 SKILL.md「第零步」的展开：
> 工具用法、板块数据映射、降级规则、校验与留痕。**原则：图谱给确定性事实，模型只做教学设计判断。**

## 1. 覆盖范围与降级决策树

图谱当前覆盖 8 学科、111 册，版本：**统编（语文/历史）、人教（数学/英语/物理/化学/生物）、湘少+译林（英语）、湘教（地理）**。

```
kg_health 失败
  → 降级：走原路径（追问 + 不编造 + 标注「待核对」），告知用户连接器不可用
locate_lesson 无命中
  → 先重试一次：keyword 去书名号《》/序号/首尾空白后再查（服务端有归一化兜底，
    但纯课文名最稳；exact 命中=图谱确有此课的凭据，match_type 字段可判别）
  → 仍无命中（学科/版本/册不在库，如苏教版、北师大版、音体美）
    → 降级：同上，但照常追问
locate_lesson 多命中（同名课文跨册，如「短诗」命中四下与九下）
  → 列出候选（课文名 + 册 + 单元路径）让用户选——这就是「不要猜年级」的图谱化实现
唯一命中
  → 进入数据注入流程（§2）
```

降级是**全有或全无**以外的第三种状态要避免：档案拿不到就全部走原路径，**不要**把模型印象和图谱数据混着写（学生分不清哪句是事实）。

## 2. 数据注入映射表

预检通过后按序调用（一次备课的典型调用量：5～7 次）：

| 序 | 工具 | 用途 |
|---|---|---|
| 1 | `kg_health` | 连接器预检（每次开工第一步） |
| 2 | `locate_lesson(keyword, subject, grade_term)` | 课文名→Lesson 节点 + 挂载树路径（顺带拿到册、单元锚） |
| 3 | `lesson_context(lesson_id)` | 课时档案全量（一次返回，别拆成多次查询） |
| 4 | `kg_ability_profile(knowledge_ids)` | 知识点→能力/素养上溯（目标维度标签的依据） |
| 5 | `kg_anchor_exercises(unit_id)` | 单元习题 + 难度/题型 stats（作业分层素材） |
| 6 | `kg_std_items(subject, codes=[…])` | 需要课标条目原文时按 code **精取**（知识点 std_items → 原文回查；勿拉全量清单）；浏览清单/找 code 才用全量，高中场景带 stage=senior |
| 7 | `check_lesson_plan(lesson_id, plan)` | 出稿校验（§4） |
| 8 | `report_gap(...)` | 发现图谱缺漏时登记（可选） |

教案板块 ← 档案字段：

| 教案板块 | 数据来源（lesson_context 为主） |
|---|---|
| **教材分析**（meta.info） | `lesson.properties`（lesson_type 课型、printed_page 印刷页码、characters 生字表会认/会写）+ `path`（单元归属）+ `knowledge[].properties`（definition 摘要、importance、std_items 课标锚）+ `sibling_lessons`（单元语境/语文要素） |
| **学情分析**（meta.info） | `prerequisites.nodes`（前序链，**跨册节点标所属册 book**，dist 层深=距本课几步）——「学生已学基础」只写图谱里有的；**空链时按返回体 fallback_hint 降级**（sibling_lessons 同单元前课/单元语文要素），不自行猜策略 |
| **教学目标四维** | `kg_ability_profile` 返回的 Ability/Competency **真实名称**作维度依据；知识点 `std_items` code 作课标锚（原文从 `kg_std_items` 查） |
| **重难点** | `knowledge[].properties.importance`（5=最重要）+ knowledge_type（方法/概念类常为难） |
| **作业设计（三层）** | `kg_anchor_exercises` 的 `exercises`（stem/answer/difficulty/type/analysis）：**基础←难度1-2、提升←3、拓展←4-5**；`stats` 分布决定各层题量 |
| **课时数建议** | knowledge 数量与性质 + lesson_type（精读/略读/习作…）：小学课文一般 2–3 课时，略读/识字 1–2——建议值给用户确认，不硬定 |
| **板书设计** | 生字板书用 `characters.会写` 清单（没有会写字段的课型用会认） |

**ID 使用纪律**：node_id / 课标 code 在工作过程与留痕块中原样保留、**不进教案正文表格**（教师誊用场景，正文保持干净；这点与备课技能的追溯文档定位不同）。附录（一/二/三）与留痕块同属教研留痕域，原文照录含 ID 不算违纪——「不进正文」只约束教学过程正文与教师誊用板块（phases/info/rubric 量规等）；承接模式的附录三「目标↔知识点映射表」全表含 node_id 转录（见 from-lesson-prep.md §3）。

## 3. 生字表与页码

- 生字表（会认/会写）从 `lesson.properties.characters` **逐字直取**，这是全技能最容易凭印象写错的地方——图谱有就必须用图谱的。
- 印刷页码用 `printed_page`；`pages` 字段注意口径：`print`=纸面页码、`pdf`=源文件页序。

## 4. 出稿前校验：check_lesson_plan

教学设计写完、渲染文档之前，把课时切分翻译成 plan 结构过一遍校验：

```json
{"hours": [{"no": 1, "duration": 40,
            "blocks": [{"name": "情境导入", "minutes": 3}, ...],
            "knowledge_ids": ["chinese_1a_tbb_cptX", ...],
            "exercise_ids": ["chinese_1a_tbb_exeY", ...],
            "goals": ["认读 6 个生字…"]}]}
```

校验报告盯四项：
1. **duration_mismatch**（warn）：板块时长和 ≠ 课时长度——必须修（等同于原技能「时间必须加得起来」的机器化）；
2. **foreign_knowledge / foreign_exercise**（warn）：引用了别课的节点——必须修或说明理由；
3. **goal_without_knowledge**（warn）：目标无图谱支撑——检查目标写法或补挂知识点；
4. **knowledge_unassigned / exercise_unassigned**（info）：**提示不是闸门**——标注「属第 N 课时/留白」即可继续。

## 5. 留痕块（sections 末尾 text 块，默认带）

留痕块是一个 `text` section，**`title` / `text` 都必填**（title 固定「数据来源与 AI 辅助」；缺 title 会被 `render_lesson` 预检拒绝）：

```json
{ "type": "text", "title": "数据来源与 AI 辅助", "text": "数据来源与 AI 辅助：本教案经 k12-kg 知识图谱取数——……<br />……【待教师核对】……" }
```

`text` 正文按下式组织（换行用 `<br />`）：

```
数据来源与 AI 辅助：本教案经 k12-kg 知识图谱取数——课时档案（N 个知识点 /
M 条学情前序 / K 道单元习题）、能力上溯 P 项、check_lesson_plan 校验结论
（X 错误/Y 警告/Z 提示）；教学设计（目标、活动、话术、板书）由 AI 起草，
课标锚/生字表/习题编号来自图谱未改动。【待教师核对】课时数与分层作业
是否符合本班学情。
```

图谱降级（未用图谱）时此块改写为：「未连接知识图谱，教材分析/学情分析
为通用经验撰写，课标原文与页码请核对纸质教材。」

## 6. 图谱缺漏

备课中发现图谱问题（生字表缺字、知识点缺失、页码不对）→ `report_gap(gap_type, description, related_nodes)` 登记（返回 **gap_id 回执**，向用户如实说明「已登记待建图」；同条目重复登记自动去重），告知用户走建图流程；历史登记与处置状态可用 `list_gaps(gap_type=…, related_node=…)` 回查。**绝不**为了出教案绕过图谱编造，也不建议用户改图。
