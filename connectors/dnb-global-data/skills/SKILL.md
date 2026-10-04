---
name: D&B Global Search
description: 使用邓白氏查全球 D&B Global Search 查询企业商业数据，可进行邓白氏编码 (DUNS) 匹配查询目标企业主体，查询工商/注册信息、财务数据、股权与最终受益人 (UBO/CBO)、企业家族树与关联关系、 风险评分、付款记录、ESG、新闻、行业概况、高管与联系人、多元化指标、营销评分、 海运数据与溯源数据。适用于企业尽调、工商信息查询、股东与实控人穿透、财务概览、 供应链风险排查、销售线索评估等场景。当用户要求"查询某公司的工商/商业信息"、 提到 D&B / 邓白氏 / 邓白氏编码 / DUNS、或需要股东穿透、家族树、财报、风险评分、 ESG、Paydex 付款评分、企业新闻时使用。
version: "1.0.0"
author: Dun & Bradstreet
agent_created: true
---

# 邓白氏查全球

本 Skill 提供邓白氏查全球商业数据的完整操作能力。 数据端点 `https://plus.dnb.com/v2/mcp` (MCP 协议 2025-11-25)  全套工具共 17 个: 2 个核心工具 (匹配、公司概况) + 15 个专项工具 (股权家族树、风险、付款、 ESG、新闻、高管、行业概况等)，每个工具均以邓白氏编码为主入参，先匹配目标主体再查询信息。

## 使用流程概览

1. **先匹配**：用户给公司名、地址、所在国家/地区等信息时，先调 `MatchTool` 得到邓白氏编码；
  知名公司名称可自行推断国家代码，不需要反问用户。
2. **再查核心**：`DataTool` 查企业概况与营收
3. **按需深挖**：股权与关联关系/风险评分/付款信息/ESG洞察/新闻/高管等维度，用对应专项工具按邓白氏编码查询。

## 核心工具

### MatchTool - 匹配目标企业邓白氏编码 (DUNS)

将用户提供的公司信息匹配为邓白氏编码，是查询一切公司数据的第一步。 仅国家代码为必填；用户给出知名公司名称时，**系统自行推断国家代码，不需反问用户** （如 Apple → US、腾讯 → CN）。

**参数**：


| 参数                   | 类型     | 必填  | 说明                                                                 |
| -------------------- | ------ | --- | ------------------------------------------------------------------ |
| countryISOAlpha2Code | string | ✅   | 公司所在国家 ISO2 代码（如 US、CN、JP）                                         |
| name                 | string | -   | 公司名称（英文名匹配效果最佳，不能包含特殊字符，非英文地区原语言名称若无法匹配可尝试用其英文名称匹配，如 腾讯 → Tencent） |
| addressLocality      | string | -   | 城市/城镇                                                              |
| addressRegion        | string | -   | 州/省/地区；US/CA 必须为 2 字符（如 FL、NY），其他国家最长 64 字符                        |
| streetAddressLine    | string | -   | 街道地址                                                               |
| registrationNumber   | string | -   | 官方注册号（如 VAT 税号）                                                    |


**使用示例**：

- 查苹果公司：调用 MatchTool，`countryISOAlpha2Code="US"`，`name="Apple Inc."` → 命中 DUNS 060704780（Global Ultimate / Domestic Ultimate / Parent-HQ，Hierarchy Level 1）。
- 查腾讯：调用 MatchTool，`countryISOAlpha2Code="CN"`，`name="Tencent"`。

```json
{
  "countryISOAlpha2Code": "US",
  "name": "Apple Inc."
}
```

**提示**：命中后向用户展示匹配结果（DUNS、官方名称、地址、电话、家族树角色），确认无误再进入后续查询。

### DataTool - 公司概况与财务数据

获取单一公司的工商概况（firmographic）与标准财务数据：公司描述、官方名称、曾用名、经营状态、注册号、成立/注册日期、行业分类、地址、主邮箱/电话、官网、雇员数，以及年度营收与历史财务数据。可对多家公司多次调用。

**参数**（4 项全为必填）：


| 参数                             | 类型      | 必填  | 说明                                  |
| ------------------------------ | ------- | --- | ----------------------------------- |
| duns                           | string  | ✅   | 邓白氏编码                               |
| show_historical_data           | boolean | ✅   | 是否返回历史财务数据，默认 false                 |
| include_partial_financial_year | boolean | ✅   | 是否包含非完整会计年度的报表（如中期报表），默认 false      |
| block_extended_mode            | boolean | ✅   | 是否解锁扩展财务块；首次调用设 false，确需扩展块时再设 true |


**使用示例**：

- 查 Apple 概况与财务（含历史）：调用 DataTool，
`duns="060704780"`，`show_historical_data=true`，`include_partial_financial_year=false`，
`block_extended_mode=false`。

```json
{
  "duns": "060704780",
  "show_historical_data": true,
  "include_partial_financial_year": false,
  "block_extended_mode": false
}
```

**提示**：

- 返回历史财务时，**必须向用户说明数据的起止期间**（Start + Ending period）；
- 历史财务不可用时，必须明确说明"无历史数据"；
- 首次调用保持 `block_extended_mode=false`；如后续需要扩展财务块，再以 true 重调。

## 专项工具

### OwnershipTool - 股权、实控人与家族树

获取公司层级（hierarchy）、股权结构、最终受益人（UBO）、企业家族树（family tree）、 分支/子公司/母公司、全球/本国终极母公司（GU/DU）、股票类型。 **凡是需要统计分支、子公司、总部数量，必须使用本工具**。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 查 Apple 股权与家族树：调用 OwnershipTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```

**提示**：用户要求"整个家族树"时，先确认是否指全球/本国终极母公司 Global Ultimate 的完整家族树； 家族树 Level 1 为根节点，Global Ultimate 表示向上无父节点。

### BusinessEventsTool - 公共记录

获取公司在公开披露信息渠道显示的商业事件与法律事件及文件备案，包含业务活动信号、变更事件、数据补全事件、冲突/排除/验证事件；以及本地机构注册、诉讼（suits）、留置权（liens）、判决（judgments）、 破产、财务困境、暂停付款、资不抵债、清算、取消资格（debarments）、追偿索赔、奖项、 贷款、公开合同数量与金额、责任函、管控与违规（含政府管控清单 GCL）； 另含融资声明、公开通告、美国政府奖励（合同/贷款/债务/拨款）及特殊事件 （灾难事件、盗窃、CEO 变更、名称变更、合伙人变更、控制权变更、曾用名与曾用地址）等信息。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 尽调某供应商是否有诉讼/破产记录：调用 BusinessEventsTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```



### ContactTool - 联系人与高管

获取公司高级管理人员（senior executives）名单及可用联系方式。
**被问及 CEO 时**：给出职级最高（most senior）的 principal 数据；
若该人实际职称不是 CEO，必须如实说明其真实职称，不得声称其为 CEO/Chief Executive Officer。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 查 Apple 高管：调用 ContactTool，`duns="060704780"`，汇报最高职级人员及其真实职称。

```json
{
  "duns": "060704780"
}
```



### DiversityTool - 多元化指标（美国）

仅限调查美国企业，获取公司多元化洞察数据，判断该组织是否被认可或自我认定为以下类型之一： 8(a) 认证、弱势企业（DBE）、机场特许 DBE、阿拉斯加原住民公司、认证小企业、 残障退伍军人企业、联邦/州 HUBZone 认证、少数族裔企业（MBE）、退伍军人企业、 女性所有企业、女性所有小企业、少数族裔服务机构、小弱势企业、女性所有、 少数族裔所有、退伍军人所有、越战退伍军人所有、弱势退伍军人企业、服务残障退伍军人所有、 LGBTQ 所有、本地弱势企业、残障人士所有等。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 政府采购供应商资格审查：调用 DiversityTool，`duns="<目标公司D-U-N-S>"`。

```json
{
  "duns": "123456789"
}
```



### ESGTool - ESG 数据

获取公司 ESG 评分与明细，覆盖三大主题：

- **环境（Environment）**：温室气体排放（含范围明细）、水资源管理、能源使用、碳中和/净零计划、 气候风险、废弃物管理、环境认证；
- **社会（Social）**：多元与包容、劳工关系、社区参与、培训与发展、慈善活动、员工福祉、 健康与安全、客户参与、产品与服务质效评分等；
- **治理（Governance）**：董事会问责、业务韧性、商业伦理、商业透明度、股东权利、治理相关认证、 高管薪酬、公司行为、合规。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 评估 Apple 的 ESG 表现：调用 ESGTool，`duns="060704780"`，分主题汇报评分与细节。

```json
{
  "duns": "060704780"
}
```



### IndustryProfileTool - 行业概况

获取公司所属行业的多档案（multi-profile）行业报告，每个档案包含： 行业概览（Industry Overview）、季度/前次更新（Quarterly/Previous Updates）、 行业指标（Industry Indicators）、业务挑战（Business Challenges）、 趋势与机会（Trends and Opportunities）、高管洞察（Executive Insight）、 电话访谈准备问题（Call Preparation Questions）、财务信息（Financial Information）、 估值倍数（Valuation Multiples）、预测（Forecast）、行业网站（Industry Websites）、 缩略语（Acronyms）等章节。适合销售/行研/尽调前了解行业背景。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 分析 Apple 所处消费电子行业：调用 IndustryProfileTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```



### InquiryTool - 查询记录

获取公司的被查询（inquiry）数据，反映市场对该公司的征信/商业查询活跃度。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 了解某公司近期被查询频度：调用 InquiryTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```



### NewsTool - 新闻与媒体报道

获取公司近期的标准新闻与媒体内容。支持可选日期范围过滤与新闻类别过滤。
**用户寻找特定类型新闻时，必须把需求映射到 newsCategories 枚举值**。
新闻可用性限于最近 6 个月；若请求范围超过 30 天，API 会从 endDate 起截断为最近 30 天。

**参数**：


| 参数             | 类型          | 必填  | 说明                        |
| -------------- | ----------- | --- | ------------------------- |
| duns           | string      | ✅   | 邓白氏编码                     |
| startDate      | string      | -   | 开始日期 YYYY-MM-DD，最多回溯 6 个月 |
| endDate        | string      | -   | 结束日期 YYYY-MM-DD，缺省为今天     |
| newsCategories | arraystring | -   | 新闻类别枚举，见下方常用值             |
| maxNewsItems   | integer     | -   | 最多返回的文章条数                 |


**常用 newsCategories 枚举**（完整枚举以工具 schema 为准）： Mergers and Acquisitions、Executive Changes、Earnings Announcement、Product Launch、Bankruptcy、Layoffs、Legal、Joint Ventures and Partnerships、Contract Win、 Regulatory Activity、Dividend Announcement、Public Offering、Security Breach、 Corporate Name Change、Corporate Relocations、Hiring Initiatives、 Supply Chain Initiatives、Venture and Other Funding 等。

**使用示例**：

- 查 Apple 近 30 天并购与高管变更新闻：调用 NewsTool，
`duns="060704780"`，`newsCategories=["Mergers and Acquisitions", "Executive Changes"]`。

```json
{
  "duns": "060704780",
  "newsCategories": ["Mergers and Acquisitions", "Executive Changes"],
  "maxNewsItems": 10
}
```



### PaymentTool - 付款信息

获取公司付款历史与画像：主要展示Paydex 评分（当前与历史）、付款历史、所在行业商业交易规范、 建议信用额度、商业无担保贸易额度明细（trade lines）。 可与 DataTool 组合使用，提供更全面的财务上下文。 **若某日期 Paydex 历史评分不可用，必须说明**。

**参数**：


| 参数                   | 类型      | 必填  | 说明                        |
| -------------------- | ------- | --- | ------------------------- |
| duns                 | string  | ✅   | 邓白氏编码                     |
| show_historical_data | boolean | ✅   | 是否返回历史数据                  |
| order_reason         | string  | -   | 仅德国上市公司必填，取值 6332–6339 之一 |


**使用示例**：

- 查 Apple 付款表现（含历史 Paydex）：调用 PaymentTool，
`duns="060704780"`，`show_historical_data=true`。

```json
{
  "duns": "060704780",
  "show_historical_data": true
}
```



### ProvenanceTool - 数据溯源

基于当前数据覆盖（截止2026年7月）仅适用于部分市场：美国、英国、德国、瑞典，其它市场持续扩展中。获取公司注册备案数据（registry filing data）的提供情况，用于合规场景下确认企业数据的准确溯源：包含当前与历史的注册与所有权信息，提供市场级摘要，说明官方注册数据 来源何处、更新频率如何。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 合规审查某公司注册数据来源：调用 ProvenanceTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```



### RiskTool - 财务风险评分

获取公司财务风险指标：标准风险评级（standard risk rating）、生存能力评级
（viability rating）、失败分数（failure score）、逾期分数（delinquency score）、
裁员概率（layoff score）、供应商评估 SER（是否出现债权人法律救济或未偿债停业）、
供应商稳定性 SSI（是否存在重大财务或运营不稳定），及其他风险指标，
并附细节、统计、原因与评注。可与 DataTool 组合使用。
**用户引用任何过去时间段（包括"以前怎么样"等表述）时，必须设 show_historical_data=true**。

**参数**：


| 参数                   | 类型      | 必填  | 说明                        |
| -------------------- | ------- | --- | ------------------------- |
| duns                 | string  | ✅   | 邓白氏编码                     |
| show_historical_data | boolean | ✅   | 是否返回历史数据                  |
| order_reason         | string  | -   | 仅德国上市公司必填，取值 6332–6339 之一 |


**使用示例**：

- 评估 Apple 当前风险：调用 RiskTool，`duns="060704780"`，`show_historical_data=false`；
若要历史风险走势则设为 true。

```json
{
  "duns": "060704780",
  "show_historical_data": true
}
```



### RumSpendTool - 用量统计

查询当前用户的 RUM（Record Under Management）用量花费，用于监控本账号的
数据消耗情况。**无需任何参数**。
**必须提醒用户：RUM 花费更新可能有最长 24 小时的延迟**。

**参数**：无（`required: []`，直接调用即可）

**使用示例**：

- 用户询问"本月 D&B 用量还剩多少"时，直接调用 RumSpendTool，无参数。

```json
{}
```



### SBRITool - 小微企业风险洞察（美国）

仅适用于美国主体。获取公司的小企业风险洞察（SBRI，Small Business Risk Insight）： 参与放贷机构发放的贷款、租赁、信用卡与授信额度数据，包括距上次任何放贷机构 债务核销的时间、过去一年信用卡逾期严重度、被核销的租赁账户数、未偿余额合计、 企业账户总敞口、信用利用率；并按账户类型细分逾期金额与逾期周期。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 评估小型供应商的信贷风险：调用 SBRITool，`duns="<目标公司D-U-N-S>"`。

```json
{
  "duns": "123456789"
}
```



### SalesAndMarketingTool - 营销评分

获取公司销售与营销相关评分：营销活动响应可能性（Prospector Model Ratings，含
总余额、信用卡响应、贷款倾向、授信额度倾向分段）、营销风险分（Marketing risk score）、
基于支出的公司分类（Buydex 评分）、公司在家族树内的决策权（决策总部 DHQ，
Decision Headquarter）、三重奏评分（triple play score，销售定向复合风险分，
勿与 RiskTool 中的 TSR 东京商工评级混淆）、以及 Material Change 评分
（预测风险/组织规模/雇员/销售/借款/支出增长或衰退的模型）。
**用户询问 DHQ / Decision Headquarter 时，必须使用本工具**。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 判断 Apple 家族树中的决策总部：调用 SalesAndMarketingTool，`duns="060704780"`。

```json
{
  "duns": "060704780"
}
```



### ShippingTool - 海运数据

获取公司的船运洞察数据：该公司在货运中的角色（发货人 shipper / 收货人 consignee /
通知人 notifier）以及该公司的货运量（volume of shipments）。
适合供应链与贸易流分析。

**参数**：


| 参数   | 类型     | 必填  | 说明    |
| ---- | ------ | --- | ----- |
| duns | string | ✅   | 邓白氏编码 |


**使用示例**：

- 分析某贸易公司的货运角色与货量：调用 ShippingTool，`duns="<目标公司D-U-N-S>"`。

```json
{
  "duns": "123456789"
}
```



## 认证说明

- 登陆凭证为 D&B Global Search 的 Access Token，在 `~/.workbuddy/mcp.json` 的 mcpServers headers 中
以 `"Authorization": "Bearer ${DNB_ACCESS_TOKEN}"` 动态更新配置。        
- `Bearer`  前缀不可省略，否则 D&B 返回 HTTP 401（`www-authenticate: Bearer error="invalid_token"`），连接器界面会持续显示"需要认证"。
- Token 有效期 24 小时（D&B 错误码 00040），过期后须获取新 token 更新配置并重新信任连接器；
可以使用 Consumer API Key/API Secret 走 OAuth client credentials 流程换取 token。
- 错误码 00004：账户未获得当前产品授权，须联系 D&B 客户代表开通，代码层无法修复。



## 注意事项

- D&B 返回均为英文/ASCII 原文，不翻译，LLM会基于英文内容翻译。
- 字段值为 NOTAVAILABLE 时如实报告"无数据"，不得编造。
- 财务块中 `<<EXTENSION_CANDIDATE|May trigger globalfinancials_L1_v1>>` 表示可扩展但未授权的
数据块，保持未扩展并如实说明（部分财务比率/历史年份为空）。
- 数据块范围示例：`companyinfo_L4` / `companyfinancials_L4`（DataTool）、
`hierarchyconnections_L1` / `ownershipinsight_L1` / UBO / familyTree（OwnershipTool）。
- 大响应处理：单次响应超过上下文上限时，结果自动落盘到
`~/.workbuddy/projects/<project>/tool-results/mcp-connector-proxy-*.txt`
（单行 JSON，需用 python 转为带换行文本后按 ≤700 行分块读取，务必读完全部再汇总）。
- 家族树：Level 1 为根节点；Global Ultimate 表示向上无父节点。
- NewsTool 新闻仅覆盖最近 6 个月，且单次查询范围超过 30 天会被截断为最近 30 天。
- 德国上市公司使用 PaymentTool / RiskTool 时需提供 order_reason（6332–6339）。
- RumSpendTool 用量更新可能有最长 24 小时延迟，汇报时须提醒用户。

