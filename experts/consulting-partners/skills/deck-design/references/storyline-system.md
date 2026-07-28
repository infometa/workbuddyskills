# Storyline System

## 1. Deck Brief

生成前先定义决策契约：

| 字段 | 含义 |
|---|---|
| audience | 最终决策者及其知识水平 |
| decision | 本次汇报必须推动的决策 |
| context | 场景、时限、组织背景 |
| governing_question | 演示必须回答的唯一主问题 |
| scope / out_of_scope | 分析边界 |
| governing_thought | 结论先行的顶层判断 |
| success_criteria | 汇报成功的可观察标准 |
| evidence_constraints | 数据可得性、口径、敏感性 |
| assumptions | 缺失信息下的默认 [A]/[E] 假设 |
| delivery | 页数、语言、日期、文件要求 |

信息不全时先写可证伪默认假设并继续，禁止只返回问题清单。

## 2. Governing Thought 与金字塔

Governing Thought 必须用一句话同时表达方向、理由和边界。正文按“结论 -> 2-4 个 MECE 支柱 -> 证据”展开：

- 同层论点回答同一个问题，粒度一致。
- 分支之间互斥，合计覆盖决策所需范围。
- 每个支柱可被一组 claim_id 证明或证伪。
- 不能证明顶层结论的材料移入 Appendix 或删除。

## 3. SCQA / SPR

根据问题选用以下等价结构：

- SCQA：Situation -> Complication -> Question -> Answer。
- SCR/SPR：Situation -> Complication/Problem -> Resolution。

默认标题节奏：背景共识 -> 张力/问题 -> 关键发现 -> 决策含义 -> 建议 -> 行动与风险。不要把框架名称直接当页面标题。

## 4. Title Storyboard

Title Storyboard 先于正文和版式，只保留页序、页面角色和行动标题。内容页标题必须是完整、具体、可验证的主张；“市场概览”“竞争格局”“下一步”属于标签，不合格。

### 标题连读门禁

1. 只读标题即可复述完整论证和最终建议。
2. 相邻标题存在明确因果、并列或递进关系。
3. 每页只证明一个主张，标题不使用“以及/同时/多维”等把多个结论硬塞一页。
4. 标题中的数字、比较和因果均有 Evidence Map 支撑。
5. 标题不夸大证据等级；[I]/[A]/[E] 不得写成已证实事实。
6. Executive Summary 的 2-4 条结论与正文关键标题一一对应。
7. 最终行动页回应 Governing Thought，风险页给出 Kill Conditions。

## 5. Page Brief Schema

每页 Page Brief 至少包含：

```yaml
idx: 3
layout: grouped_bar
engine: main
title: "头部两家已占据六成高价值客户，进入策略应避开正面价格战"
role: Supporting
rhythm: Peak
visual_role: Evidence chart
anti_pattern: "不使用无差异多色柱，不重复标题中的所有数字"
density: medium
objective: "证明市场集中在高价值客群而非总客户数"
one_message: "应从垂直细分切入，而非复制头部的广覆盖模式"
evidence:
  - claim_id: C-03
    grade: "[F]"
source:
  - label: "公司年报与客户访谈汇总"
    url: ""
```

`objective` 描述本页要完成的证明任务；`one_message` 是观众离开页面后应记住的唯一信息；两者不能互相替代。

## 6. Evidence Map

Evidence Map 连接标题、正文和来源：

| claim_id | claim | grade | evidence | source | used_on | gap / kill_condition |
|---|---|---|---|---|---|---|
| C-03 | 高价值客户集中度超过总客户集中度 | [F] | 分层客户收入 | 年报/访谈 | 3, 4 | 若分层口径不可比则降级为 [I] |

证据等级仅允许 `[F]` 事实、`[I]` 推断、`[A]` 假设、`[E]` 估算。每个内容页至少关联一个 claim_id；同一数字跨页必须复用同一口径。

## 7. 角色、节奏与视觉锚点

- Hero：决定性结论、关键数字或核心选择；建议占全篇 20%-30%。
- Supporting：证明 Hero 的分析、数据、机制和案例。
- Transition：章节切换、问题重置、从发现转向行动。
- Peak：高对比、高聚焦、强结论。
- Valley：降低密度，用于解释、呼吸或吸收复杂信息。
- Transition：显式切换论证阶段。

`visual_role` 应写明页面的视觉证明方式，如 Evidence chart、Decision matrix、Process、Comparison、Narrative bridge。非对称布局建议不少于 40%，相邻布局不重复，除非需要严格可比。

## 8. Executive Summary 与正文对齐

Executive Summary 不是摘要堆砌，而是 Governing Thought 的最短证明：

- 每条结论映射到至少一个正文页和 claim_id。
- 摘要措辞不得比正文证据更强。
- 正文结论变化时必须同步更新摘要。
- 建议、价值、风险、下一步应形成闭环。

## 9. Appendix

Appendix 用于承载方法、详细数据表、敏感性、定义和补充案例，不用于隐藏关键结论。正文中的重要数字必须能追溯到 Appendix 或结构化 Source；Appendix 延续统一页码、来源、脚注和证据等级。