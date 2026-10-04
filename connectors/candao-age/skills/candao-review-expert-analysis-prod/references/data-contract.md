# 数据口径（适配连接器 2026-09 改版后的新版 schema）

仅使用 `get_review_expert_analysis_data` 返回的数据，不自行补充网络、天气、促销、节假日、餐品或门店背景。

> 2026-09 连接器再次改版，**返回结构整体更换**。旧 v2 字段（`period` / `dailyTrends` / `scores` /
> `reviewDetails` / `reviewMetrics` / `businessMetrics` / `negativeReasons` / `negativeSamples`）
> **已全部不存在**，本文件与生成脚本已按新版重写。新版顶层 9 字段：
> `logId` / `hasData` / `commentDetails` / `reviewMetricSummary` / `orderAndReceiptSummary` /
> `badCommentReasonDistribution` / `commentScoreDistribution` / `dailyCommentTrends` / `badCommentSamples`。

## 一、返回结构（`hasData=true` 时）

| 顶层字段 | 类型 | 粒度 | 关键子字段 |
|---|---|---|---|
| `logId` | string | — | 本次查询日志编号（用于排查） |
| `hasData` | boolean | — | 所选范围是否有评价数据；`false` 则停止分析、不编造报告 |
| `commentDetails[]` | list | 单条评论（全部评价，含好评/中评/差评） | `commentDate` `platformTypeDesc` `brandId` `brandName` `storeId` `storeName` `commentContent` `commentTime` `replyContent` `replyTime` `commentScore` `commentLevel` `commentTags` `badCommentTags` |
| `reviewMetricSummary[]` | list | 门店 × 渠道 | `commentCount` `preCommentCount` `goodCommentCount` `preGoodCommentCount` `badCommentCount` `preBadCommentCount` `replyWithin24Hours` `preReplyWithin24Hours` `goodCommentCountPer` `preGoodCommentCountPer` `replyWithin24HoursPer` `preReplyWithin24HoursPer`（**扁平 `preXxx` 即上期**，无嵌套 current/previous） |
| `orderAndReceiptSummary[]` | list | 门店 × 渠道 | `orderNum` `preOrderNum` `totalActualReceipt` `preTotalActualReceipt`（**无 date 维度**；无订单的门店×渠道组合可能返回 null，生成脚本 `num()` 已兜成 0.0） |
| `badCommentReasonDistribution[]` | list | 单条差评 + 标签 | `commentDate` `storeId` `storeName` `platformTypeDesc` `commentContent` `badCommentTags`（细粒度差评归因，可直接聚合 `badCommentTags`） |
| `commentScoreDistribution[]` | list | 门店 × 渠道 × 分值（**无 date 维度，整周期汇总**） | `commentScore`(字符串 `'1'~'5'`) `commentScoreCount` |
| `dailyCommentTrends[]` | list | 日期 × 门店 × 渠道 | `commentDate` `storeId` `storeName` `platformTypeDesc` `commentCount` `goodCommentCount` `badCommentCount` `goodCommentPer` `badCommentPer`（**⚠️ 不含任何 reply/回复字段**） |
| `badCommentSamples[]` | list | 抽样差评（举证用） | `commentDate` `commentId` `replyContent` `replyTime` `brandId` `brandName` `storeId` `storeName` `badCommentTags` `commentContent` |

**差评明细来源**：`commentDetails` 中 `commentLevel=='差评'` 的条目（全量，新接口无 200 条上限封装）。
`badCommentSamples` 仅 19 条抽样，用于举证，不代表全部差评；报告应以 `commentDetails` 过滤结果为准。

**一级原因 vs 二级标签（两套独立体系）**：
- `commentTags` = **一级原因**（与 v2 `tags` 完全一致）：`菜品口味 / 菜品份量 / 门店出品 / 餐品包装 / 服务态度 / 菜品异物 / 餐具漏送 / 配送超时 / 其他原因`，**仅作差评明细卡片并列展示**；报告的差评原因分布、命中门店、改进建议现已统一改用二级 `badCommentTags`。
- `badCommentTags` = **细粒度标签（按「-」拆一级/二级两层）**：形如 `口味问题-味道异常` / `制作/错漏送-漏做少给` / `异物问题-毛发人体异物`，其中「-」前为**一级大类**（口味问题/分量问题/制作·错漏送/异物问题/服务态度/缺餐具/配送超时/包装·撒漏/其他原因/笼统差评）、「-」后为**二级细项**。**是报告「差评原因分布」的唯一维度**：一级条形图按「-」前大类汇总、点一级名下钻二级条形图、点二级名联动命中门店/每日趋势/改进建议/食安红线（食安红线 = 一级命中「异物问题」前缀）。两级同色按一级大类前缀（`TAGCOLOR`）。差评明细中一级 chip 与「一级-二级」整串 chip 并列展示。

## 二、评分与比例口径

- 5 分 = 好评；3～4 分 = 中评；0～2 分 = 差评（由 `commentLevel` 直接判定，`commentLevel=='差评'` 即纳入差评明细）。
- `commentScoreDistribution.commentScore` 为字符串 `'1'~'5'`，须转 int；**无 0 分桶**（新接口不返回评分缺失档，故评分分布环形图无「评分缺失」段）。平均分只使用 1～5 分加权自算（工具不再返回 `averageScore`）。
- 好评率 / 中评率 / 差评率分母均为评价总数，三者合计 100%（注意 `goodCommentCount + badCommentCount` 可能 < `commentCount`，差值即中评）。
- **所有比例字段均为 0～1 的小数**（`goodCommentCountPer` / `replyWithin24HoursPer` 等，`0.01` 展示为 `1%`）。
- **率指标（好评率 / 差评率 / 24h差评回复率）的环比统一用「百分点变化（pp）」**：`(cur − prev) × 100`；**不写相对变化 %**（如 67.1%→73.5% 记 −6.3pp，而非 −8.6%）。计数类指标（总评论数 / 好评数 / 差评数）环比仍用**相对变化 %**。
- **比例一律「分子分母分别汇总后再相除」，绝不可对各行比例取平均**（分行平均会在每天样本量不等时严重失真）。
- 变化率的对比基数为 0 时只说明绝对数量变化，不计算或猜测百分比。

## 三、标签口径

- 一条评价可命中多个标签（跨大类），故「各一级原因占差评比例」**横向相加合计**可能 >100%（如一条差评同时含口味问题+分量问题，会分别计入两类）。但**单类占比恒 ≤100%**：分子须为该大类命中的「去重差评条数」（一条差评即使带多个同大类二级标签，也只计 1 次），分母为同口径差评总条数；**不得用标签出现次数作分子**，否则单类会算出 >100%（如曾出现的 164%），属错误。
- `commentTags`（旧一级体系）与 `badCommentTags`（按「-」拆一级/二级）是**两套独立体系**：`badCommentTags` 自身已含「一级大类-二级细项」两层；报告原因分布统一用 `badCommentTags` 的两层下钻，一级 `commentTags` 仅作差评明细卡片并列展示、不再驱动原因分布。
- 「其他原因」为兜底标签、无可落地归因：在差评原因分布中**强制置底**，在改进建议中**直接剔除**（不占编号、不渲染弱化框）。
- 「占差评比例」的分母必须与分子同源：分子、分母均来自同一份差评明细（`commentDetails` 过滤结果）——分子=该原因命中的**去重差评条数**（`aggTag1Count` 已按评论去重，一条差评带多个同大类二级标签只计 1 次），分母=该过滤结果的长度（`fq.length`）；**不得用标签出现次数作分子**（会 >100%）、**不得**混用 `dailyCommentTrends` 汇总出的差评数（后者不含「原因」维度）。
- `commentTags` / `badCommentTags` 为**字符串化的 Python 列表**（如 `"['其他原因']"`、`"['口味问题-味道异常', '分量问题-份量偏少']"`），`gen_report.py` 的 `clean_tags()` 用 `ast.literal_eval` 还原，失败时退化为按 `|`/`,`/`[` 拆分并二次清洗标签内 `[]` 残留（数仓偶发 `]` 拼接两条标签或尾随空格，已兜底还原为多条干净标签）。

## 四、已知数据缺陷 / 调用坑（生成脚本已打补丁）

1. **日期窗口左移（MCP 服务端 bug，仍在新版存在）**：实测请求 `startDate=2026-08-24` / `endDate=2026-08-30` 时，`dailyCommentTrends` 实际只返回 `2026-08-23 ~ 2026-08-29`（左移一天、缺失 0830、多出 0823）；但 `badCommentSamples` 返回 `2026-08-24 ~ 2026-08-30` 正常。属同一响应内窗口不一致，确认是 MCP 工具侧 bug，**非 skill 问题**。统计周期从 `dailyCommentTrends.commentDate` 推导，缺尾日时如实标注（如报告副标题显示 0823~0829），不要虚构 0830。
2. **接口无 `period` 字段**：旧 v2 的 `period`（含 startDate/endDate/previous/through）已移除。统计周期（`PERIOD.start/end/through`）从 `dailyCommentTrends.commentDate` 去重排序推导；无上期日期区间、无 `dataAvailableThrough`，相关文案降级处理。
3. **`dailyCommentTrends[]` 实际不含 reply 字段**：仅含 comment/good/bad 计数 + 率；回复率必须从 `reviewMetricSummary` 聚合（周期级），日趋势图改画周期级参考虚线。
4. **`commentScoreDistribution[]` 实际不含 `date` 字段**：是门店×渠道×评分的整周期汇总；评分分布图**不按日期过滤**，只随门店/渠道联动。
5. **`commentTags` / `badCommentTags` 为字符串化列表**：见第三节，`clean_tags()` 已兜底。
6. **`commentContent` 可能为空字符串**（用户只打分未写文字），渲染须兜底，不显示空引号。
7. **回复时效窗口因平台而异（已内置于 `replyWithin24HoursPer`）**：美团 1–48h、其他平台 1–24h。生成脚本按 `reviewMetricSummary` 聚合（`replyWithin24Hours / badCommentCount`），与工具口径一致，**无需按平台重算**。
8. **`orderAndReceiptSummary` 字段可空（连接器层硬阻塞，非脚本可解）**：无订单的门店×渠道组合可能把 `orderNum` / `preOrderNum` / `totalActualReceipt` / `preTotalActualReceipt` 返回 **null**；如果目标环境的 output schema 要求这些字段为非 null number，MCP 传输层会整体 `Validation failed`，响应无法到达本脚本（`gen_report.py` 的 `num()` 兜底只在数据已经到达时生效）。正式取数前必须以 WorkBuddy 实测确认；如复现，数据团队需对无订单组合补 0 或将 schema 放宽为可空。

## 五、能力边界（必须在报告中如实标注，不得编造）

- **上期数据无逐日明细**（`reviewMetricSummary.preXxx` 只到门店×渠道粒度）→ **按日期子集筛选时环比不可得**；门店/渠道筛选已支持环比。
- **`orderAndReceiptSummary` 无日期维度** → 订单量/实收金额只随门店/渠道联动，**不随日期联动**；「差评密度（条/万单）」为跨口径换算，仅作量级参考，不等于逐单归因。
- **差评明细无 200 条上限**：`commentDetails` 过滤 `commentLevel=='差评'` 即全量差评（本次 180 条）；指标卡与趋势走 `dailyCommentTrends` 全量汇总，不受影响。
- **无标签级的评分 / 订单 / 回复数据** → 「差评原因」维度只作用于明细类模块（原因分布、命中门店、每日命中趋势、差评明细、总结），**不**影响指标卡、评分分布、每日整体趋势。
- 24h 差评回复率为**周期级指标**（分子 `replyWithin24Hours`、分母 `badCommentCount`，来自 `reviewMetricSummary`，与服务端 `replyWithin24HoursPer` 口径一致）；`dailyCommentTrends` 无 reply 字段，故**无逐日折线**；**分母为 0（无差评）时回复率须显示「—（不适用）」而非 0%**。
- **「未回复」有且仅有两套口径，报告须显式区分、不得混写（曾因混写被误判为算错）**：
  ① **24h 内未回复（周期级，store/channel 跟随筛选、不带日期）** = `reviewMetricSummary` 聚合 `badCommentCount − replyWithin24Hours`，用于**指标卡 / 重点问题② / 每日趋势参考线**的「24h差评回复率」；
  ② **至今未回复（逐条，任意时间，跟随全四维筛选）** = `commentDetails` 中 `replyTime` 与 `replyContent` 均为空的差评条数，用于**重点问题② 举例列表 / 改进建议 SLA**的「至今未回复」。
  两者定义不同（24h 窗口 vs 任意时间），数值天然不等（本期 24h 未回复 54 条、至今未回复 17 条）；`commentTime` 被接口截到 `00:00:00`（仅日期），**无法从逐条时间戳反推 24h 内回复**，故 24h 口径只能信工具聚合值、不得自行用时间戳折算。重点问题② 须桥接说明：`至今未回复(17) + 已回复但超24h(37) = 未达24h SLA(54)`。
