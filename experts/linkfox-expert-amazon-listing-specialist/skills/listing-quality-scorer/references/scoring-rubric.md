# Listing Quality Scoring Rubric v1

## Scoring Philosophy

评分对象是「Listing 转化准备度」，不是承诺真实 CVR。分数必须回答：

1. 卖家能不能安全使用？
2. 搜索系统能不能理解并匹配？
3. 买家能不能快速理解价值并降低购买疑虑？

每个维度都必须有证据、扣分原因和动作建议。

## Dimensions

| 维度 | weight | 可评分证据 | 主要扣分项 |
|---|---:|---|---|
| 平台合规与风险 | 20 | compliance_report、旧版 scorePanel 合规项、researchReport.riskTerms、平台规则、品类规则、商标/禁用词扫描 | 高危违禁词、医疗/功效夸大、竞品品牌泄漏、绝对化宣称、品类必填缺失 |
| 商品事实与声明可信度 | 15 | product_facts、ASIN 详情、用户规格、图片/OCR 事实 | 编造材质/尺寸/认证/适配型号，超出证据范围，描述与商品事实冲突 |
| 搜索匹配与语义可发现性 | 15 | keyword_matrix.scored_table、结构化属性、标题/五点/描述/后台词覆盖 | 核心词缺失，实体/属性关系不清，高价值词未前置，堆词，后台词重复前台词，长尾场景词不足 |
| 标题点击与首屏识别质量 | 10 | title、itemHighlights、title_char_count、类目标题规则 | 非 Media 类目 Title >75c，Item Highlights >125c，拆分后信息丢失，核心品类词不清晰，品牌/型号/规格混乱，促销语、重复堆词 |
| 五点转化与购买决策支持 | 15 | bullets、评论痛点、竞品卖点、BAF/STAR 结构 | 只列功能不讲收益，缺场景/人群/痛点，五点重复，缺证据，购买疑虑未覆盖 |
| 信息完整度与 AI 导购可回答性 | 10 | listing 全字段、buyer_questions、question_coverage、产品规格、包装/使用/护理/兼容/边界信息 | 买家问题无明确答案，关键规格/适用范围/包装/限制缺失，答案缺事实证据，产品实体与使用边界不清 |
| 语言质量与站点本地化 | 8 | listing 全文、目标 marketplace | 机器翻译感、语法错误、表达不自然、站点语言风格不匹配、重复空话 |
| 差异化与竞争安全 | 7 | diff_report、competitor_context、竞品文本 | 与竞品高度相似，卖点无差异，复刻痕迹强，定位不清 |

总权重 100。N/A 维度不参与 overall，剩余权重归一化。

## Hard Gates

| 条件 | cap | 处理 |
|---|---:|---|
| 高危合规命中、商标侵权、竞品品牌泄漏 | 59 | pass=false，requires_human_review=true |
| 商品事实明显编造，尤其认证、材质、医疗/安全宣称 | 69 | pass=false，要求重写相关字段 |
| 非 Media 类目 Title >75 字符 | none | 标题维度最高 59；若无 Item Highlights 承接迁出信息，overall_cap=79。字符数由 `normalize_listing_input.py` 按来源字段实测，**不接受把一条标题拆成 Title + Item Highlights 后再评** |
| 非 Media 类目 Item Highlights >125 字符 | none | 标题维度最高 69；Item Highlights 必须来自来源的独立字段，来源没有该字段时按 `unavailable` 处理 |
| 任一五点 >255 字符或五点合计 >1275 字符 | none | 五点转化与购买决策支持最高 69；201-255 仅为可读性提醒，不封顶 |
| 长描述 >1000 字符 | none | 信息完整度与 AI 导购可回答性最高 79；描述维度建议重写 |
| 标题缺失、五点缺失、核心字段不可读 | 70 | pass=false |
| 无任何合规机检产物（`compliance_report` / `compliance_scan` / `check-report` 全缺） | 79 | 由 `score_quality.py` 自动触发，评估者删不掉：合规维度同时封顶 79，note 固定「合规待终检」。评估者自己通读文案数极限词**不构成合规证据**，`data_confidence` 里写 `verified` 也不算 |
| 有合规机检产物，但其结论标注检测范围受限 | none | 可给合规数字分；用户可见 note 必须写成「基于当前合规检测数据」，不得出现「旧版/legacy/scorePanel」；同时标明「基于当前检测，不构成法律意见或平台最终审核保证」 |
| product_facts unavailable | 79 | 忠实度维度 N/A，不能标注「事实已验证」 |
| keyword_matrix unavailable | none | 搜索匹配维度 N/A，不得编关键词覆盖率或流量分 |

| 字段级安检（`check-report.json`）任一字段 status=fail | 79 | pass=false；失败字段列入 `scorePanel.mechanicalFieldFailures` |

cap 在加权分计算之后应用：`overall = min(weighted_overall, cap)`。

合规维度权重 20，是全表最高的一项，因此它的证据来源由脚本强制而不是靠评估者自觉：
`_has_compliance_machine_evidence()` 只认真实机检产物，缺产物就落 `compliance_unavailable`
门禁 + 维度封顶 79，overall 一定进不了 80 的「可直接使用」档。堵的是「合规扫描没跑，
手工 grep 几个极限词就给 92 分，再按 20% 权重把总分抬到 B+」这条路径。

最后一条是机检总闸：只压维度不够——「标题点击与首屏识别质量」权重仅 10，Item Highlights
超 125c 把该维度压到 69 之后总分仍能算出 97 分 A 级，与 `pass=false` 自相矛盾。字段安检没过
的 Listing 一律落到「需要优化后使用」档。机检结论由 `score_quality.py --check-report` 自动并入，
只压不抬，映射表见 [scoring-input-contract.md](scoring-input-contract.md)。

## Compliance Copy Constraints

- 合规分项必须标明检测范围：`基于当前合规检测数据` 或 `基于已提供的合规检测结果`。
- 用户可见文案不得出现内部实现词：`旧版`、`legacy`、`scorePanel`。
- 合规分项的具体结论必须由输入证据触发；不得固定写 `未发现高风险词`、`无极限词`、`无竞品品牌词`。
- 如果 `riskTerms`、validator violations、内部兼容合规项备注中出现风险命中，note 必须改写为命中结论，并展示命中类型、数量或样例。
- 如果合规说明明确表示风险命中均为误报、无真实品牌词/商标侵权、无禁用词或未发现高风险词，合规分项不得标记为 `bad` 或展示「高风险」；只能按证据范围标记为 `ok` / `warn` / `na`。
- 合规分项不得使用法律承诺式表述：`保证合规`、`完全无风险`、`平台一定通过`、`无需复核`。
- 面向用户展示的 note/recommendation 必须包含边界提示：`不构成法律意见或平台最终审核保证`。
- 医疗/安全/认证/商标/功效宣称相关产品，即使自动检测通过，也应建议卖家按 Amazon 规则、当地法规和品牌授权资料做最终复核。

## Dimension Scoring Anchors

## Search Match & Semantic Discoverability Rule

「搜索匹配与语义可发现性」不能只因为 keyword_matrix 存在就给高分。评分必须同时看关键词覆盖率、字段布局、后台词承接，以及产品—属性—场景关系是否清楚。

### Required Checks

| 检查项 | 通过标准 | 扣分/限制 |
|---|---|---|
| Frontend exact coverage | 研究词在 Title、Item Highlights、Bullets、Description 中自然出现 | `<20%` 最高 69；`20%-39%` 最高 79；`40%-59%` 最高 89；`>=60%` 才可进入 90+ |
| P0/P1 placement | P0/P1 词或清晰等价表达进入 Title / Highlights / 前两条 Bullets | P0 大量缺失最高 79；Title 无核心品类词最高 69 |
| Backend coverage | 后台词承接未放入前台的高相关长尾，不重复前台，不超字节 | 后台未承接研究词或过短扣 8-20 |
| Naturalness | 关键词自然嵌入，不牺牲可读性 | 堆词、重复、语义不通扣 8-25 |
| Data confidence | 有 scored_table / search rank / priority / field mapping | 只有摘要无明细时 state 至少为 warn，不能显示 verified 高分 |

### Scoring Anchor For This Dimension

- **90-100**：前台精确/自然覆盖 >=60%，P0/P1 核心词布局合理，后台词补充有效长尾，且无明显堆词。
- **80-89**：覆盖率 40%-59%，核心词基本到位，后台词有少量缺口。
- **70-79**：覆盖率 20%-39%，部分核心词缺失或后台承接不足，需要补词。
- **60-69**：覆盖率 <20%，或后台几乎未承接研究词；即使文案语义相关，也只能算待优化。
- **<60**：关键词矩阵不可验证、核心品类词缺失、关键词堆砌严重或搜索意图明显错配。

## Title 75c + Item Highlights 125c Rule

标题评分必须按新版拆分模型评价，不按旧 200 字符标题模型给高分。Media 类目除外。

### Required Checks

| 检查项 | 通过标准 | 扣分/限制 |
|---|---|---|
| Title length | 非 Media 类目 `len(title) <= 75` | 超出则「标题点击与首屏识别质量」最高 59 |
| Item Highlights length | 非 Media 类目 `len(itemHighlights) <= 125` | 超出则该维度最高 69 |
| Title role clarity | Title 只回答「产品是什么」，保留核心品类词、关键规格/材质/兼容锚点 | 场景、多个卖点、促销语堆在 Title 内扣 10-30 |
| Highlights migration | 从 Title 迁出的功能收益、场景、量化卖点进入 Item Highlights | 迁出信息丢失扣 10-25；无 Highlights 承接时 overall_cap=79 |
| Search continuity | Top 核心词仍在 Title 前 40 字符；次级词自然进入 Highlights/五点/后台词 | 核心词后置或丢失扣 8-20 |
| Duplication control | Highlights 不重复 Title 核心词堆砌，不复制五点全文 | 重复堆词扣 5-15 |

### Scoring Anchor For This Dimension

- **90-100**：Title <=75c，核心品类词前置，Title 清楚回答产品是什么；Item Highlights <=125c，自然承接场景/收益/次级规格；无明显信息丢失。
- **80-89**：长度合规，拆分基本合理；有轻微信息迁移不足或 Highlights 表达一般。
- **70-79**：长度合规但点击价值弱，核心词不够前置，或 Highlights 重复/空泛。
- **60-69**：Item Highlights 超长、缺失关键迁移信息，或标题仍有明显堆词。
- **<60**：非 Media 标题超过 75c，或标题不可读/促销化/规则明显违规。

## AI Shopping Assistant Answerability

维度 6 评价 Listing 是否能让购物助手从可追溯信息中回答买家问题，而不是评价平台是否一定推荐。

| 检查项 | 通过标准 | 扣分/限制 |
|---|---|---|
| Product identity | Title/Highlights 能明确说明产品是什么 | 实体不清或型号混乱扣 10-25 |
| Audience and scene | 明确适用人群、对象与真实场景 | 只有泛化场景扣 5-15 |
| Pain to solution | 高频顾虑有具体方案与事实证据 | 空洞收益或无证据功效扣 10-30 |
| Specs and compatibility | 关键规格、适配、包装、使用方法可定位 | 影响购买的问题缺答案扣 5-20/项 |
| Trust and boundary | 认证/材质/效果可追溯，不适用边界清楚 | 缺边界或过度承诺扣 10-25 |
| Question coverage | buyer_questions 有明确字段承接 | 覆盖不足 40% 最高 69；40%-69% 最高 79；≥70% 才可进入 90+ |

Alexa 问答实测(计费)不是该维度的必要输入；未执行时只表示 `external_probe.probed=false`，不得因此扣文案分。`recommendation_readiness` 由合规、事实、语义可发现性、购买决策支持和可回答性派生，不作为第九维重复计权。

### 90-100

- 证据充分，字段完整，表达自然。
- 没有高/中风险扣分。
- 搜索、合规、购买说服力都强。
- 这个区间应当少见，不能作为默认分。

### 80-89

- 可上架，但有明确优化点。
- 无硬性风险；允许少量表达、完整度或差异化不足。
- 推荐展示为「可上架 · 建议优化」。

### 70-79

- 能用但不建议直接投放。
- 存在关键词、转化表达、信息完整度或合规待验证问题。
- 需要 writer retry 或人工修订。

### 60-69

- 关键字段需要重写。
- 有事实忠实度风险、结构问题或明显转化弱点。

### <60

- 不可直接使用。
- 通常由 hard gate、严重合规风险、字段缺失或高度雷同触发。

## Recommended Item Names

`scorePanel.items` 面向用户展示时建议使用：

1. 平台合规与风险
2. 商品事实与声明可信度
3. 搜索匹配与语义可发现性
4. 标题点击与首屏识别质量
5. 五点转化与购买决策支持
6. 信息完整度与 AI 导购可回答性
7. 语言质量与本地化
8. 差异化与竞争安全

若需要兼容旧 UI，可在渲染层映射旧名称，但评分源必须保留新维度。

## Output Rules

- 每个分项必须有 `evidence[]`，证据应引用字段、命中词、覆盖数量、检查结果或数据路径。
- 每个扣分项必须有 `deductions[]`，包含 `points`、`reason`、`field`、`action`。
- 每个 N/A 维度必须说明缺少什么数据，以及如何补齐。
- `topIssues` 只列真正影响上架或转化的事项，不列装饰性建议。
- `quickFixes` 应可直接传给 writer 作为 retry 约束。
- 模型只输出扣分项；最终维度分、N/A 权重归一、hard gate、overall、grade 和 AI readiness 必须由 `scripts/score_quality.py` 计算。
