# 门店经营 KPI 细则

> 本文件是 `jumper-kpi-analysis` 的**门店维度**细则。共用规则（只读边界、ID 别名、分页、消歧、量纲与时点对照）在 `SKILL.md` 里，本文件只写门店维度特有的部分，不再重复。

## 目标与边界

使用 `search_hospitals`、`query_hospital_kpi`、`query_hospital_channel_kpi`、`compare_hospital_kpi`、`rank_kpi` 五个只读工具，回答门店整体经营的问题。

- 只使用本文件列出的字段和指标，不虚构收入、利润、成本、净额、渠道金额或真实转化率。
- 门店维度只到「门店」这一层。问到门店内具体人员/顾问的 KPI 目标、完成率、职级、档级、达标情况，或某个人某天/某段时间的业绩时，改读 `references/staff-kpi.md`（`search_staff` / `query_staff_kpi` / `query_staff_daily_kpi` / `query_hospital_staff_summary`）。人员维度按月按天都能查，不要因为「要按天」就改用门店工具——那查的是整店，不是人。
- 两边口径与量纲都不同：人员完成金额只统计配置了 KPI 的人、**单位为万元**，而门店金额**单位为元**，差 1 万倍，禁止相互印证、比较或相减。两张底表的时点语义也不同：门店表是**按日增量**（一行=一家店的一天），人员表是**每日快照**（一行=截至那天的当月累计），不能套用彼此的口径。
- 当前工具名或参数结构若与本文件不同，以调用时实际暴露的工具 Schema 为准；不要把旧参数硬塞给新工具。
- 每次只调用回答问题所必需的工具。排名优先用 `rank_kpi`，服务端可直接完成的单院完整周期对比优先用 `compare_hospital_kpi`。

## 调用前先形成查询卡

在内部确定以下信息；不要把查询卡原样输出给用户：

- 医院范围：单院、多院、全部医院明细、所选范围整体汇总。
- 指标：准确映射到指标编码。
- 时间：明确的开始日期、结束日期、业务时区。
- 任务：查数、趋势、同比/环比、医院排名、渠道排名或渠道趋势。
- 粒度：`day`、`month` 或 `year`。
- 完整性：是否包含今天、是否需要检查覆盖天数、是否可能分页。

只有下列歧义会改变结果时才追问：医院搜索出现多个同样合理的院区；用户没有给任何时间范围；用户只说“转化”但无法判断客资还是商机；用户问“增长了吗”但没有说明同比还是环比。其他情况按下文默认映射执行。

## 门店维度的传参规则

先遵守 `SKILL.md` 的共用硬规则（ID 别名、字符串/整数类型、可选参数省略、`Asia/Shanghai`），本节只列门店维度特有的：

1. 日期使用字符串：`startDate`、`endDate` 为 `yyyy-MM-dd`；`period` 按粒度分别为 `yyyy-MM-dd`、`yyyy-MM`、`yyyy`。
2. 枚举统一使用小写英文（`day`/`month`/`year`、`hospital`/`channel`、`asc`/`desc`），不发送中文别名。
3. `startDate` 不得晚于 `endDate`，不得查询未来经营结果。「最近 7 天」包含今天时，范围为今天及之前 6 天。
4. `summary` 传 JSON 布尔值，`page`、`pageSize`、`topN` 传 JSON 整数；不要给这些值加引号。
5. 单家医院查询始终传 `summary=false`。只有用户要把多家或全部医院合并成一个整体时才传 `summary=true`；「单院某月总业绩」不属于整体汇总。

## 医院消歧

按以下顺序执行：

1. 用户直接给出医院 ID：只有形如 `H_3F7A2B9C41` 的别名才能直接按字符串传给 `hospitalId`；给的是数字ID时不要转发（会被拒绝），改用 `search_hospitals` 按名称重新确认。
2. 用户询问全部医院、医院排名或整体数据且没有点名医院：不搜索，不加医院过滤。
3. 用户给出医院名称、简称或院区名：先调用 `search_hospitals`。
4. 搜索结果中只有一个明确匹配，或正式名称/简称存在唯一完全匹配：使用该项的 `hospitalId`。
5. 多个结果都可能匹配：列出正式名称、简称和可用数据日期，让用户选择；未确认前不得调用 KPI 工具。
6. 没有匹配：说明当前账号可见范围内未找到医院，不把空结果当成经营数据为 0。
7. 多个点名医院：逐个消歧，再把 ID 用英文逗号拼成一个字符串。
8. 用户提到人名（如李兵、刘乐）或地区/城市（如重庆、北京）：这类词往往是医院正式名称或简称的一部分（如「李兵妇产医院」「重庆安琪儿」），**不要当成「没点名医院」而按全部医院查**。先用该词作 `keyword` 调 `search_hospitals`：命中唯一按第 4 条取 `hospitalId`，命中多家按第 5 条让用户选，没有命中按第 6 条说明未找到。拿到 ID 后，本文件的其余医院类工具照常按 ID 使用。

`search_hospitals` 返回的 `earliestStatDate` 和 `latestStatDate` 只表示该院最早/最新出现数据的日期，不证明中间每天都有数据。

- 请求区间完全落在该院已知日期范围之外：说明没有已知数据覆盖，不回答为 0。
- 请求区间只有一部分落在已知日期范围内：不要悄悄修改用户日期；查询原范围，并在结果中明确未覆盖的日期段。

## 指标映射

| 用户说法 | 指标编码 | 含义 |
|---|---|---|
| 业绩、销售额、总销售额 | `totalSalesAmount` | VIP 与居家销售额之和，单位元；用户笼统说“业绩”时默认用此项 |
| VIP 业绩、VIP 销售额 | `vipSalesAmount` | VIP 销售额（成交金额-退款金额），单位元 |
| 居家业绩、居家销售额 | `homeSalesAmount` | 居家销售额，单位元 |
| VIP 有效金额 | `vipValidAmount` | VIP 有效金额，与 VIP 销售额是两个不同口径的字段，单位元 |
| 有效金额、总有效金额 | `totalValidAmount` | VIP 有效金额 + 居家销售额的合计，两项口径不同，属**混合口径**；只有用户明确说“有效金额”时才用，问“业绩”一律用 `totalSalesAmount` |
| 退款、总退款 | `totalRefundAmount` | VIP 与居家退款成功金额之和，正数，单位元 |
| VIP 退款 | `vipRefundAmount` | VIP 退款成功金额，正数，单位元 |
| 居家退款 | `homeRefundAmount` | 居家退款成功金额，正数，单位元 |
| 成交、成交量、总成交数 | `totalPayCount` | VIP 与居家成交数量之和 |
| VIP 成交 | `vipPayCount` | VIP 成交数量 |
| 居家成交 | `homePayCount` | 居家成交数量 |
| 线索、新增线索 | `newLeadCount` | 新增有效线索数 |
| 客资、线索转客资 | `leadToCustomerCount` | 首次从线索转为客资的对象数 |
| 商机、客资转商机 | `customerToOpportunityCount` | 首次从客资转为商机的对象数 |
| 企微客户、企微客户数、CRM 客户数、加了多少客户 | `wecomCustomerCount` | 新增企微客户数，该院**全部科室合计**；口径见下节 |

“销售额”与“有效金额”是两套口径，居家侧只有销售额、没有有效金额：`totalSalesAmount` 是 VIP 与居家销售额的干净合计，`totalValidAmount` 则把 VIP 有效金额与居家销售额相加，仅为兼容历史口径保留。两者不可混用、不可相减，同一段结论里同时出现时必须分别写明是哪一个口径。

漏斗顺序是 `newLeadCount → leadToCustomerCount → customerToOpportunityCount`。这些是各阶段发生量，不是同一批对象的实时存量。工具没有真实转化率字段；若用户明确要求阶段比率，只能计算“后阶段计数 ÷ 前阶段计数”，并明确它不是同一批对象的真实转化率。分母为 0 时不计算。

**`wecomCustomerCount` 不在这条漏斗里**：不要把它当成漏斗的某一级，也不要拿它与线索/客资/商机相除算转化率。

## 企微客户数（`wecomCustomerCount`）

**含义**：企业微信客户数，对齐 CRM「客户」页签 `stage=0`（全部）统计出的 `total`。它和线索数、商机数是并列的绩效指标，**主要用途是算绩效**；目前 KPI 指标尚未覆盖全部维度，它补上的是「加了多少客户」这一维。

**统计口径是「医院 → 该院全部科室」的合计**：

- 问某家医院时，返回的是该院**所有科室**的合计数，不是某一个科室的数。
- 问某个日期时，统计的是**该日期内所有科室对应的 CRM 客户数**。
- 工具不提供科室级拆分，也没有科室字段。用户追问「哪个科室加得多」时，说明当前数据只到医院层，不要编造科室数字。

**时点语义与门店其他指标一致**：它是**按日增量**（当天新增），不是存量总数。跨日、跨月相加就是区间合计，和 `newLeadCount` 一样，`granularity="month"/"year"` 直接给区间值。

**「未归属医院」**：企微客户没有关联到任何医院时，服务端把它们单独归成一行，医院名称与简称都是 `未归属医院`。它**不是一家真实医院**：

- 不出现在 `search_hospitals` 的结果里，也不计入「共有多少家医院」。
- 不参与 `rank_kpi` 的医院排名，也不进 `share` 的分母。
- 不出现在 `query_hospital_channel_kpi` 里（它没有渠道数据）。
- 但 `query_hospital_kpi` 的明细里有它单独一行，`summary=true` 的合计**包含**它；`matchedHospitalCount` 只数真实医院，不含它。

因此「各**真实**医院的企微客户数相加」可能小于「`summary=true` 的全国合计」，差额就是未归属客户（`query_hospital_kpi` 的明细里能看到它单独那一行）。要把这部分**单列说明**，不要悄悄抹掉、平摊到各院，也不要说成某家医院的数据。

## 工具选择决策

| 用户意图 | 使用工具 | 关键规则 |
|---|---|---|
| 确认医院 | `search_hospitals` | 名称不唯一时必须先消歧 |
| 金额、退款、成交、漏斗总量或趋势 | `query_hospital_kpi` | 单院 `summary=false`；多院或全部医院合并成整体才设 `summary=true` |
| 渠道随日/月/年变化 | `query_hospital_channel_kpi` | 返回每院每周期的三个渠道列表，不提供整体汇总 |
| 哪些渠道最多、主要来源、渠道占比 | `rank_kpi`，`dimension="channel"` | 按对应漏斗指标排名；金额指标禁止用于渠道排名 |
| 单院或各医院的完整周期同比/环比 | `compare_hospital_kpi` | 无 `summary` 参数，返回每家医院一行 |
| 所选多院合计或全部医院整体同比/环比 | 两次 `query_hospital_kpi`，均 `summary=true` | 分别查本期和基期，再按公式计算；不要把各院变化率相加 |
| 单院或各医院当前未结束月/年的同进度对比 | `compare_hospital_kpi` | 服务端自动对齐；按实际起止日期、`comparable` 与 `comparabilityNote` 解释结果 |
| 医院排名 | `rank_kpi`，`dimension="hospital"` | 不要查询全部医院后自行排序 |
| 企微客户数总量或趋势 | `query_hospital_kpi` | 与其他指标同一次调用即可返回，不需要额外工具 |
| 哪家医院企微客户加得最多 | `rank_kpi`，`dimension="hospital"`、`metric="wecomCustomerCount"` | 排名不含「未归属医院」，需要全国合计时另用 `summary=true` 核对 |
| 门店里某个人/顾问的业绩，按月或按天 | 改读 `references/staff-kpi.md` | 门店维度的工具都只到门店层，没有人员维度；「某天」也一样，用 `query_staff_daily_kpi` 而不是门店工具的 `granularity="day"` |

## 5 个工具的精确合同

### `search_hospitals`

用途：按正式名称或简称模糊搜索医院；不传关键字时最多返回 100 家。

- 可选参数：`keyword` 字符串。
- 关键返回字段：`hospitalId`、`hospitalName`、`hospitalShortName`、`earliestStatDate`、`latestStatDate`。

### `query_hospital_kpi`

用途：查询 KPI 聚合结果。

- 必填：`startDate`、`endDate`。
- 可选：
  - `granularity`：`day|month|year`，默认 `day`。
  - `hospitalKeyword`：医院名称/简称模糊过滤；仅在无需消歧的特殊情况下使用。
  - `hospitalId`：一个或多个医院 ID 的字符串。
  - `summary`：布尔值，默认 `false`。`true` 表示所选范围整体汇总，每周期一行；`false` 表示每院每周期一行。
  - `page`：从 1 开始，默认 1。
  - `pageSize`：默认 100，最大 500。
- 返回 `items` 字段：
  - 范围：`period`、`hospitalId`、`hospitalName`、`hospitalShortName`。
  - 金额：`vipSalesAmount`、`homeSalesAmount`、`totalSalesAmount`、`vipValidAmount`、`totalValidAmount`（混合口径）、`vipRefundAmount`、`homeRefundAmount`、`totalRefundAmount`。
  - 数量：`vipPayCount`、`homePayCount`、`totalPayCount`、`newLeadCount`、`leadToCustomerCount`、`customerToOpportunityCount`、`wecomCustomerCount`（企微客户数）。
  - 完整性：`dayCount`、`containsPartialDay`、`containsIncompleteSource`、`dataAsOf`；范围汇总另看 `matchedHospitalCount`。
- `summary=false` 时可能出现医院名为「未归属医院」的一行（企微客户未关联医院的兜底行，其余指标恒为 0）；`summary=true` 的合计含这部分，`matchedHospitalCount` 不含。详见上文「企微客户数」。

单院查询始终使用 `summary=false`。用户明确要把多家或全部医院合并为一个整体时使用 `summary=true`；用户问各医院明细时使用 `summary=false`。任意日期范围若只要总计而不看趋势，可用 `year` 减少返回行，再把同一范围内的年度行相加。

### `query_hospital_channel_kpi`

用途：查询渠道明细随周期的变化。

- 必填：`startDate`、`endDate`。
- 可选：`granularity`（`day|month|year`，默认 `day`）、`hospitalKeyword`、`hospitalId`、`page`、`pageSize`。
- 分页默认每页 50，最大 500。
- 每个 `items` 元素包含医院、周期以及：
  - `newLeadByChannel`：新增有效线索渠道列表。
  - `leadToCustomerByChannel`：线索转客资渠道列表。
  - `customerToOpportunityByChannel`：客资转商机渠道列表。
- 每个渠道元素包含 `channelId`、`channelName`、`count`；未知渠道的 ID 或名称可能为空。
- 本工具不返回「未归属医院」那一行（它没有渠道数据），也不返回 `wecomCustomerCount`。
- 完整性字段：`containsPartialDay`、`containsIncompleteSource`。本工具没有 `summary`、`dayCount` 或 `dataAsOf`。需要整体渠道趋势时，必须取全各院结果后按同周期、同渠道、同指标相加，并说明这是客户端汇总。

### `compare_hospital_kpi`

用途：由服务端计算每家医院全部 KPI 的同比或环比。

- 必填：
  - `granularity`：只传 `day|month|year`。
  - `period`：`day` 传 `yyyy-MM-dd`，`month` 传 `yyyy-MM`，`year` 传 `yyyy`。
  - `compareType`：环比传 `period_over_period`；同比传 `year_over_year`。
- 可选：`hospitalKeyword`、`hospitalId`、`page`、`pageSize`；分页默认 50，最大 500。
- 返回每院一行：`currentPeriod`、`basePeriod`、`currentContainsPartialDay` 和 `metrics`；实际范围见 `currentStartDate`、`currentEndDate`、`baseStartDate`、`baseEndDate`，日历天数见 `currentDayCount`、`baseDayCount`，可比性见 `comparable`、`comparabilityNote`。
- 每个 `metrics` 元素包含 `metric`、`label`、`current`、`base`、`change`、`changeRate`。
- 基期规则：日环比前一天，日同比去年同一天；月环比上月，月同比去年同月；年环比与年同比都为上一年。
- 服务端公式：`change = current - base`；`changeRate = change / base`，保留为小数；基期为 0 时 `changeRate=null`。

本期周期结束日晚于数据截止日时，服务端会截取本期并同步对齐基期，得到“本期至今 vs 基期同期”。两期天数是实际查询区间的自然日数，不是逐院有数据天数，不能证明数据完整；某一期完全没有行时仍按 0 参与计算。因此：

- `currentContainsPartialDay=true` 时，不直接下“上升/下降”的确定结论。
- `comparable=false` 时先读 `comparabilityNote`；天数不等时说明日历因素，本期晚于数据截止日时说明对比不可用。即使为 `true`，也不代表逐院上游数据完整。
- 某一期值全为 0 且“无数据还是实际为 0”会影响结论时，补查该期 `query_hospital_kpi`：`items=[]` 是无数据；存在行且值为 0 才是指标为 0。

### `rank_kpi`

用途：对医院或渠道按指定日期范围的一个指标排序，并返回占比。

- 必填：`startDate`、`endDate`。
- 可选：
  - `dimension`：`hospital|channel`，默认 `hospital`。
  - `metric`：医院维度默认 `totalSalesAmount`；渠道维度默认 `newLeadCount`。
  - `order`：`desc|asc`，默认 `desc`。
  - `topN`：默认 10，范围 1 到 100。
  - `hospitalKeyword`、`hospitalId`：渠道排名时可限制到指定医院范围。
- 医院维度可用全部 15 个指标编码（含 `totalSalesAmount`、`vipSalesAmount`、`homeSalesAmount`、`wecomCustomerCount`）。
- 医院维度的排名对象只有真实医院，「未归属医院」既不占名次也不进 `share` 的分母；因此排名各行的 `wecomCustomerCount` 之和可能小于 `summary=true` 的全国合计。
- 渠道维度只允许 `newLeadCount`、`leadToCustomerCount`、`customerToOpportunityCount`。
- 返回：`rank`、`targetId`、`targetName`、`targetShortName`、`metric`、`metricLabel`、`metricValue`、`share`、`containsPartialDay`。
- `share` 是 0 到 1 的小数，按参与排名的全部对象合计计算；合计为 0 时为 `null`。
- 同值使用并列名次，例如 `1,1,3`。渠道排名的 `containsPartialDay` 表示整个查询范围是否包含暂累计，不是逐渠道的完成状态。

处理“前 N 名”并列：首次把 `topN` 设为 `min(max(N+10,20),100)`，最终保留所有 `rank <= N` 的行。如果返回行数等于 `topN` 且最后一行 `rank <= N`，用 `topN=100` 重查；若 100 行最后仍是 `rank <= N`，说明服务端上限可能截断同名次对象。

## 门店维度的分页补充

分页通则见 `SKILL.md`。门店维度特有：`search_hospitals` 和 `rank_kpi` **不分页**，`page`/`pageSize` 为 `null`，`total` 是符合条件的真实总数。`truncated=true` 时搜索需收窄关键字，排名可增大 `topN`（最大100）；只返回前 N 名也可回答前 N 名，但不能声称已取全或自行据此计算整体合计。

## 渠道分析与缺失核对

渠道只对应三个漏斗指标：

- 问线索来源：使用 `newLeadCount` / `newLeadByChannel`。
- 问客资来源：使用 `leadToCustomerCount` / `leadToCustomerByChannel`。
- 问商机来源：使用 `customerToOpportunityCount` / `customerToOpportunityByChannel`。

问主要来源或占比时：

1. 调用 `rank_kpi`，`dimension="channel"`，选择对应指标，通常设 `topN=100`。
2. 再调用 `query_hospital_kpi` 查询同一医院范围和日期范围的对应漏斗总数；整体范围设 `summary=true`。
3. 将返回的全部渠道 `metricValue` 相加，与漏斗总数比较。
4. 渠道合计小于漏斗总数时，把差额单列为“未归因/渠道明细缺失”，不要悄悄排除；若正好返回 100 个渠道，同时说明还可能包含未返回渠道。
5. 渠道合计大于漏斗总数时，说明数据口径不一致，不强行给出占比结论。
6. `targetId`、`channelId` 或名称为空的渠道保留并显示为“未知渠道”。

不得用金额给渠道排名。`rank_kpi` 返回的渠道 `share` 是已解析渠道之间的占比；在未与漏斗总数核对前，不得称为“占全部线索/客资/商机的比例”。

## 时间、粒度与数据完整性

- 单日或逐日趋势：`day`。
- 月度结果或跨月趋势：`month`。
- 年度结果或跨年趋势：`year`。
- “本月”是本月 1 日至今天；“上月”是上月完整自然月；“本年”是 1 月 1 日至今天；“去年”是去年完整自然年。
- 查询指定完整周期时，日期边界必须覆盖该自然周期。查询部分周期时，明确写“截至某日累计”。
- 对齐月度或年度截止日时，若基期没有相同日序（例如本期到 31 日而基期月份只有 30 日），基期截止到该月月末，并明确说明。

处理 `query_hospital_kpi` 完整性：

1. `containsPartialDay=true`：标记“暂累计，数值仍可能变化”。
2. 用 `dayCount` 与查询区间在该 `period` 内应覆盖的自然日数比较。少于应有天数时，说明实际覆盖天数，不把它描述成完整周期。
3. `summary=true` 的 `dayCount` 是范围内有任意数据的去重日期数，不能证明每家医院都完整；需要逐院完整性时改查 `summary=false`。
4. `containsIncompleteSource=true`：说明上游同步尚不完整、数值可能偏低；渠道查询也检查此字段和 `containsPartialDay`。渠道排名只提供查询范围级别的 `containsPartialDay`，不提供上游完整性字段。
5. `query_hospital_kpi` 返回 `dataAsOf` 时按原值说明统计截止时间；为空时不编造。未返回标志或标志为 `null`，不能据此声称“上游已完整同步”。

## 对比计算

手工对比用于整体汇总、所选多院合计或用户指定的自定义区间：

- 本期值：`current`
- 基期值：`base`
- 变化额：`change = current - base`
- 基期不为 0：`changeRate = change / base`
- 基期为 0：变化率写“基期为 0，无法计算”，不得写成 `0%`、`100%` 或“无限增长”。

变化率和 `share` 都是小数，展示时乘以 100 并加 `%`，例如 `0.15` 显示为增长 `15%`，`-0.15` 显示为下降 `15%`。

## 结果判定

- `total=0` 且 `items=[]`：没有返回数据。
- 存在结果行且指标字段为 0：指标值为 0。
- 字段为 `null`：说明该字段未提供或无法计算，不擅自改成 0。
- 金额单位统一为元；退款金额按正数展示。
- 只描述数据支持的事实，不从相关变化直接推断原因。

## 输出格式

先给结论，再给证据，最后集中说明限制：

1. **结论**：用一到三句话直接回答用户问题；暂累计或不可比时在结论里同时说明。
2. **统计口径**：医院范围、明确起止日期、粒度、指标名称和单位。
3. **关键数据**：
   - 普通查询给核心值和必要拆分。
   - 对比给本期、基期、变化额、可计算的变化率。
   - 渠道按对应漏斗数量降序，给数量和经核对后的占比；未知和缺失单列。
   - 排名写清指标、周期、医院范围，并保留并列名次。
4. **数据限制**：统一列出暂累计、覆盖天数不足、分页上限、渠道缺失、无法证明同步完整或口径不可比。

## 常见请求的固定路径

- “上个月安琪儿的业绩怎么样”：`search_hospitals` 消歧 → `query_hospital_kpi`，上月首日至末日，`granularity="month"`，唯一 `hospitalId`，`summary=false`。
- “这个月线索主要来自哪些渠道”：本月首日至今天，`rank_kpi` 使用 `dimension="channel",metric="newLeadCount",order="desc",topN=100` → `query_hospital_kpi` 使用同范围、`summary=true` 核对线索总数 → 标记含今天暂累计。
- “哪三家医院业绩/销售额最高”：`rank_kpi` 使用 `dimension="hospital",metric="totalSalesAmount",order="desc"`，按并列规则扩大 `topN` 后输出所有 `rank<=3` 的医院；用户明确问“有效金额”时才换成 `metric="totalValidAmount"` 并在结论里写明是混合口径。
- “这个月各院加了多少企微客户”：本月首日至今天，`query_hospital_kpi` 使用 `granularity="month"`、`summary=false` 取各院明细。明细里若有「未归属医院」那一行，把它与真实医院分开列，不要并进某家医院，也不要当成一家院。
- “本月整体业绩环比”：本月未结束时不用服务端完整基期直接判断方向；分别查询本月 1 日至今天、上月 1 日至相同日序的 `query_hospital_kpi`，两次均 `summary=true`，再计算变化额和变化率。

## 禁止事项

- 禁止把医院 ID 当数字或数组传递，或使用未经 `search_hospitals` 返回的自造别名。
- 禁止在医院未消歧时用模糊关键字混查多个院区。
- 禁止把“所有医院明细”和“整体汇总”混为一谈。
- 禁止用渠道漏斗计数解释渠道金额贡献。
- 禁止把「未归属医院」当成一家真实医院、某家分院，或把它的企微客户数摊到各医院头上。
- 禁止把企微客户数当作漏斗的一级，或与线索/客资/商机相除算转化率。
- 禁止把阶段计数比包装成真实转化率。
- 禁止把当前暂累计与完整基期直接描述为确定上升或下降。
- 禁止把 `compare_hospital_kpi` 的合成 0 未经核对就认定为实际 0。
- 禁止只看 `truncated` 决定是否继续翻页。
- 禁止把空变化率解释成没有变化。
- 禁止用门店维度的数据推断某个人的业绩（如把门店金额按人数摊到人头上，或说「这家店业绩差所以某某顾问业绩差」）——人员业绩按 `references/staff-kpi.md` 实查。
- 禁止把门店金额（元）与人员完成金额（万元）相互印证、相减或算占比。
