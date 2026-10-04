---
name: member-consumption-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：组合 SCRM 消费分析页面接口，输出营业额、消费笔数、客单价、趋势、会员明细、商品排行和来源分布。适用于用户问“分析消费分析页面近一周表现”。用于 SCRM 消费分析页面；不要替代 DataCube 会员消费占比或完整会员营业汇总。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
version: "1.0.168"
author: shanglong-skill-creator
---

## 适用客户（CRM8）

仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。

- 开始分析时明确提示上述适用范围。当前用户或连接器上下文已明确为非 CRM8 时，说明没有数据并停止业务查询，不输出零值报告。
- 客户版本未知时，不凭空认定其为 CRM8 或非 CRM8；按当前已认证连接器权限执行本文固定查询，并保留适用范围提示。
- 空结果不能用来判定客户版本。区分非 CRM8 不适用、CRM8 当前筛选无数据、查询失败和真实指标为 0；查询失败不解释为零。

## WorkBuddy 运行兼容（强制）

所有业务查询直接执行连接器安装的 **`sl-sea` 二进制**：Windows 为 `sl-sea.exe`，macOS/Linux 为 `sl-sea`。`<sl-sea-absolute>` 表示按附带运行规则解析出的二进制绝对路径，不能原样执行占位符。禁止调用旧版裸命令 `sl`、`sl.cmd`、`sl.ps1` 或 Node CLI 入口。正文命令模板按当前操作系统使用 PowerShell 或 Bash 直接执行；查询不依赖 Node.js。

先读取本技能附带的 [rules/workbuddy-runtime.md](rules/workbuddy-runtime.md)，按其中系统对应的定位与调用规则执行二进制。下文直接命令模板按运行规则转换为当前系统的参数数组执行；Windows 不照搬 Bash 引号写法。所有时间占位符必须替换为实际时间，筛选数组、分页和维度按用户条件调整；示例中的默认空数组不覆盖用户已经确认的筛选。正文表格里的 `<sl-sea-absolute> 域 命令` 仅标识固定接口，实际执行使用绝对程序路径与参数数组。

Agent 元数据见 [agents/claw.yaml](agents/claw.yaml) 与 [agents/openai.yaml](agents/openai.yaml)。本技能独立加载，不依赖专家团 Agent 或外部统计技能。

## 业务 Skill 自包含执行规则（最高优先级）

1. 本业务 Skill 必须只依赖本文件及附带运行规则中明确写出的固定 CLI、固定接口、参数规则、字段口径和失败策略执行。
2. 执行时不得搜索、读取或要求用户安装其它模块文档；不得因为外部文档不存在而停止执行。
3. 只有固定 CLI 不存在、命令失败、鉴权失败、参数缺失，或本文没有提供可执行命令时，才按失败处理；面向业务用户只说明失败模块、业务影响和可核对范围，只有用户明确要求排查执行问题时，才展示底层命令、参数或错误摘要。

## 标准安全与边界（最高优先级）

1. 只使用本 Skill 明确写出的固定 CLI、SQL、接口或脚本；不得搜索 task 列表、不得执行 help 探测、不得猜测或替换 taskId/exeTaskId。
2. 本业务 Skill 只执行本文明确列出的固定 CLI、固定脚本或固定接口；不用近似页面、近似指标或其它业务 Skill 替代。
3. 用户问题不属于本 Skill 名称、description 或正文边界时，停止并转交更匹配的 Skill；无法确定时先列出候选让用户确认，不自行猜测。
4. 本 Skill 默认只读安全：不主动执行新增、修改、删除、发券、触达、导出敏感名单等动作，除非正文明确支持且用户明确要求。
5. 不输出 token、session、cookie、密钥、内部网关认证参数；会员姓名、手机号、会员编号、订单号等敏感信息默认脱敏。
6. 命令失败、接口异常、SQL 超时、空数组和指标为 0 必须区分；失败不能写成 0，空数据不能编造结论。
7. 输出必须说明统计时间、门店/集团视角和关键口径；涉及占比、转化率、环比或同比时说明分子、分母或对比基准。


# 消费分析

本 Skill 是业务 Skill，按固定直接接口 CLI 模块生成消费分析报告。它复现 SCRM 页面“数据 > 消费分析”的接口口径，不使用 DataCube SQL、`<sl-sea-absolute> datacube`、`taskId` 或 `exeTaskId`。

## 边界规则

- 用户问 SCRM 页面“数据 > 消费分析”的整体分析时使用本 Skill。
- 用户只问单个模块时，直接执行本文对应固定 CLI。
- 用户问“数据概览”页面里的账单金额、消费笔数、会员客单价时，使用数据概览相关 Skill。
- 用户问储值、积分、卡券、RFM、复购或活动分析页面时，使用对应页面 Skill，不用本 Skill 代答。
- 不允许把浏览器页面样例值当作实时结果；实时结果必须来自固定接口 CLI。

## 内置固定接口模块

本业务 Skill 已把消费分析页面所需的固定接口模块写入本文。执行时只读取本文及附带运行规则，不要搜索其它模块文档。

| 问题 | 模块 | 固定 CLI |
|---|---|---|
| 当前营业额、消费笔数、消费人数、客单价表现如何 | 消费分析基础指标 | `<sl-sea-absolute> general get-consume-base-info` |
| 会员/非会员消费金额趋势如何 | 消费金额趋势 | `<sl-sea-absolute> general get-comsume-amount-analysis` |
| 会员/非会员消费笔数趋势如何 | 消费笔数趋势 | `<sl-sea-absolute> general get-comsume-nums-analysis` |
| 会员/非会员客单价趋势如何 | 消费客单价趋势 | `<sl-sea-absolute> general get-unit-price-analysis` |
| 哪些会员消费贡献高，是否需要明细样例 | 会员消费明细 | `<sl-sea-absolute> general get-member-consume` |
| 哪些商品或类别更受会员偏好 | 会员消费商品排行 | `<sl-sea-absolute> general get-product-rank` |
| 城市、门店或品牌维度会员消费占比如何 | 会员消费占比统计 | `<sl-sea-absolute> general get-consume-proportion-rank` |
| 消费会员来源是否集中 | 消费会员来源分布 | `<sl-sea-absolute> general get-consume-member-source-distribution` |

注意：金额趋势和笔数趋势命令名沿用平台生成产物里的拼写 `comsume`，不要自行改成 `consume`。

## 执行顺序

1. 标准化时间、卡型、门店、新会员定义、外卖参与计算、分页和维度参数，计算上一周期。
2. 执行内置模块“消费分析基础指标”。
3. 执行内置模块“消费金额趋势”。
4. 执行内置模块“消费笔数趋势”。
5. 执行内置模块“消费客单价趋势”。
6. 如用户需要会员名单、样例或页面整体分析，执行内置模块“会员消费明细”；默认只取第一页。
7. 如用户问商品、类别、偏好或页面整体分析，执行内置模块“会员消费商品排行”；默认按商品取第一页。
8. 如用户问占比、城市、门店、品牌或页面整体分析，执行内置模块“会员消费占比统计”；默认按城市取第一页。
9. 如用户问来源结构或页面整体分析，执行内置模块“消费会员来源分布”。

## 门店编码获取 CLI

用户指定门店名称、简称、别名或门店 ID 时，先按运行规则定位二进制，执行固定 CRM 门店查询；未指定门店时按本文默认权限范围执行。

```text
<sl-sea-absolute> store find --type crm --name '<门店关键词>' --format json
```

用户给门店 ID，或名称查询无结果而需要关键词查询时，最多补查一次：

```text
<sl-sea-absolute> store find --type crm --keyword '<门店关键词或门店ID>' --format json
```

先检查进程退出码和业务状态，再读取业务结果。候选为空时停止并提示未找到门店；只有一个候选时使用其 `omShopCode`；多个候选时展示候选名称供用户确认，不静默选择第一条，不展示完整内部编码。用户确认多个门店后使用对应编码数组。

门店清单缺失或认证失败时，引导用户在连接器重新认证，再重试原门店查询一次；不读取认证文件、不手工刷新或填写认证参数。

数据概览把选定编码放入 `shopIds`，未指定门店时省略该字段；其它会员分析放入 `shopFilterTypeValue`，并设 `shopFilterType=1`。卡券分析分别设置发券门店 `shopFilterTypeValue` 和核销门店 `useShopFilterTypeValue`。相同筛选必须应用到本轮所有相关查询。

## 参数规范

用户只需要提供当前统计周期。不要向用户额外索要上一区间；`preBeginDate/preEndDate` 按前端页面逻辑自动计算：

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

示例：当前周期为 `2026-05-11 00:00:00` 到 `2026-05-17 23:59:59` 时，`rangeDays=7`，上一区间为 `2026-05-04 00:00:00` 到 `2026-05-10 23:59:59`。

| 参数 | 规则 |
|---|---|
| `beginDate` | 用户指定开始日转成 `yyyy-MM-dd 00:00:00` |
| `endDate` | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59` |
| 自然语言时间 | 如“近一个月”“本月”“上周”先解析为当前统计周期，再统一生成 `beginDate/endDate` |
| 默认时间 | 用户未指定时，默认最近 7 个完整自然日 |
| `preBeginDate/preEndDate` | 不要求用户填写；按上述前端平移公式从当前周期自动计算 |
| `dateType` | 默认 `1` 按天；用户问月趋势/按月时用 `2` |
| `newMemberType` | 默认 `0` 按注册时间；用户明确说按首次消费时用 `1` |
| `hasTakeOut` | 默认 `0`，只有用户明确要求外卖数据参与计算时传 `1` |
| `cardTypeIds` | 未指定卡型时传 `[]` |
| `shopFilterType` | 默认 `1` |
| `shopFilterTypeValue` | 未指定门店时传 `[]`；指定门店时使用已解析出的门店筛选值 |
| `dimensionType` | 会员消费占比统计默认 `1` 城市；用户问门店/品牌时分别用 `2`/`3` |
| 明细分页 | 默认 `page=1,size=10`；用户要求更多时再提高，但不要无边界拉全量 |

统一 `--params` 形态：

```json
{
  "shopFilterType": 1,
  "shopFilterTypeValue": [],
  "cardTypeIds": [],
  "dateType": 1,
  "newMemberType": 0,
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>"
}
```

## 合并与计算规则

| 指标 | 规则 |
|---|---|
| 会员/非会员占比 | 优先使用基础指标和占比统计接口返回的占比字段 |
| 新老会员拆分 | 只使用基础指标接口的 `newMemberValue`、`oldMemberValue` |
| 趋势比较 | 只有 `dateList` 和序列长度一致时才按下标解释 |
| 会员消费金额趋势 | 使用 `memberConsumeAmountList` 与 `notMemberConsumeAmountList` |
| 会员消费笔数趋势 | 使用 `memberConsumeNumsList` 与 `notMemberConsumeNumsList` |
| 客单价趋势 | 优先使用 `memberUnitPriceList` 与 `notMemberUnitPriceList`，不重算覆盖 |
| 商品偏好 | 使用商品排行接口的 `memberPreferencePercent`，不自行定义偏好指数 |
| 来源占比 | 可用 `resourceList[].count / totalCount` 计算；总人数为 0 时不计算 |
| 明细样例 | 默认最多展示 3 条脱敏样例；手机号、卡号不要完整展开 |

## 输出报告结构

1. 筛选条件：时间、上一区间、卡型、门店、新会员定义、外卖口径、趋势粒度。
2. 执行摘要：执行了哪些内置接口模块，哪些成功、失败或为空。
3. 核心指标：营业额、消费笔数、消费人数、客单价，含会员/非会员/新老会员拆分。
4. 趋势判断：金额、笔数、客单价的高低点和异常波动。
5. 结构分布：商品排行、会员消费占比、消费会员来源的 Top 项。
6. 明细提示：会员消费明细总条数、脱敏样例或不展示原因。
7. 风险与建议：样本少、分母为 0、会员消费占比异常、来源集中、商品偏好集中等。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个内置接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要 |
| 基础指标失败 | 可以继续输出趋势和分布，但必须标注缺少核心汇总 |
| 返回空对象/空列表 | 说明当前条件无数据，提示检查时间、卡型、门店、权限 |
| 字段缺失 | 标注缺失字段，不用近似字段替代 |
| CRM 登录/解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要 |

## 固定接口模块详情

以下模块详情已合并到本业务 Skill。执行单个模块或整体分析时，直接使用本节固定 CLI、参数和字段说明。

### 通用入参字段

以下字段在多个固定 CLI 的 `--params` JSON 中复用；生成命令前必须先按用户问题和上方“参数规范”确定这些值。

| 参数 | 含义 | 默认/规则 |
|---|---|---|
| `shopFilterType` | 门店筛选类型 | 默认 `1`，沿用消费分析页面默认门店筛选口径。 |
| `shopFilterTypeValue` | 门店筛选值数组 | 用户未指定门店时传 `[]`；用户指定门店时填入已解析出的门店筛选值。 |
| `cardTypeIds` | 会员卡型 ID 数组 | 用户未指定卡型时传 `[]`；指定卡型时只放对应卡型 ID。 |
| `dateType` | 趋势粒度 | 默认 `1` 按天；用户明确问月趋势或按月时用 `2`。 |
| `newMemberType` | 新会员定义 | 默认 `0` 按注册时间；用户明确说按首次消费时用 `1`。 |
| `beginDate` | 当前统计周期开始时间 | 用户指定开始日转成 `yyyy-MM-dd 00:00:00`。 |
| `endDate` | 当前统计周期结束时间 | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59`。 |
| `preBeginDate` | 上一统计周期开始时间 | 不向用户索要，按本文前端平移公式从当前周期自动计算。 |
| `preEndDate` | 上一统计周期结束时间 | 不向用户索要，按本文前端平移公式从当前周期自动计算。 |
| `hasTakeOut` | 外卖是否参与计算 | 默认 `0` 不参与；只有用户明确要求外卖参与时传 `1`。 |
| `page` / `size` | 分页参数 | 默认 `page=1,size=10`；业务分析默认不超过 `20`，不要无边界拉全量。 |
| `itemType` | 商品排行维度 | `0` 商品名称，`1` 类别名称；默认 `0`。 |
| `sortField` / `order` | 商品排行排序 | `sortField=1` 会员点单笔数，`sortField=2` 会员消费笔数；`order=1` 正序，`order=2` 倒序。 |
| `dimensionType` | 消费占比统计维度 | `1` 城市，`2` 门店，`3` 品牌；默认 `1`。 |

### 消费分析基础指标

固定 CLI：

```text
<sl-sea-absolute> general get-consume-base-info --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`turnoverInfo` 营业额卡片、`consumeAmountInfo` 消费笔数卡片、`consumeMemberInfo` 消费人数卡片、`customerPriceInfo` 客单价卡片。各卡片的 `totalValue` 是汇总值，`totalFloatRangeType/totalFloatRange` 是较上一区间变化方向和比例，`nonMemberValue/nonMemberProportion` 与 `memberValue/memberProportion` 是非会员/会员拆分，`newMemberValue/oldMemberValue` 是新老会员拆分。结果粒度为当前筛选范围的汇总卡片；`0` 是合法值，接口失败、字段缺失、空对象不能解释为 0。

### 消费金额趋势

固定 CLI：

```text
<sl-sea-absolute> general get-comsume-amount-analysis --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`dateList[]` 时间点列表、`memberConsumeAmountList[]` 会员消费金额、`notMemberConsumeAmountList[]` 非会员消费金额。结果粒度为时间序列，只有 `dateList` 与两个序列长度一致时，才按下标合并解读。

### 消费笔数趋势

固定 CLI：

```text
<sl-sea-absolute> general get-comsume-nums-analysis --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`dateList[]` 时间点列表、`memberConsumeNumsList[]` 会员消费笔数、`notMemberConsumeNumsList[]` 非会员消费笔数。结果粒度为时间序列；空数组表示当前筛选条件没有可展示趋势点，不得补造趋势。

### 消费客单价趋势

固定 CLI：

```text
<sl-sea-absolute> general get-unit-price-analysis --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`dateList[]` 时间点列表、`memberUnitPriceList[]` 会员客单价、`notMemberUnitPriceList[]` 非会员客单价。结果粒度为时间序列；客单价优先使用接口返回值，不用金额除以笔数覆盖接口口径。

### 会员消费明细

固定 CLI：

```text
<sl-sea-absolute> general get-member-consume --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输入补充：`page` 默认 `1`，`size` 默认 `10`，业务分析默认不超过 `20`。输出字段：`list[].memberName`、`shopName`、`saledShopName`、`cardSoldTime`、`mobile`、`cardNo`、`cardTypeName`、`sex`、`birthday`、`totalConsumeBill`、`totalConsumeBalance`、`totalConsumeTimes`、`lastOpTime` 和 `total`。结果粒度为会员；手机号、卡号属于明细数据，默认只输出汇总条数和必要脱敏样例。

### 会员消费商品排行

固定 CLI：

```text
<sl-sea-absolute> general get-product-rank --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"itemType":0,"sortField":null,"order":null,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输入补充：`itemType=0` 表示商品名称，`itemType=1` 表示类别名称；`sortField=1` 表示会员点单笔数，`sortField=2` 表示会员消费笔数；`order=1` 正序，`order=2` 倒序。输出字段：`list[].itemName`、`saleAmount`、`memberBillCount`、`memberConsumeCount`、`memberPreferencePercent` 和 `total`。结果粒度为商品或类别，取决于 `itemType`；喜好指数按接口返回，不自行重新定义。

### 会员消费占比统计

固定 CLI：

```text
<sl-sea-absolute> general get-consume-proportion-rank --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"dimensionType":1,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输入补充：`dimensionType=1` 城市、`dimensionType=2` 门店、`dimensionType=3` 品牌；`hasTakeOut=0` 表示外卖不参与计算，`hasTakeOut=1` 表示外卖参与计算。输出字段：`list[].dimension`、`turnover`、`memberConsumeAmount`、`memberConsumeAmountProportion`、`nonMemberConsumeAmount`、`nonMemberConsumeAmountProportion`、`consumeCount`、`memberConsumeCount`、`memberConsumeCountProportion`、`nonMemberConsumeCount`、`nonMemberConsumeCountProportion` 和 `total`。结果粒度由 `dimensionType` 决定；城市、门店、品牌是不同维度，不能按行直接互相比。

### 消费会员来源分布

固定 CLI：

```text
<sl-sea-absolute> general get-consume-member-source-distribution --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`totalCount` 消费会员总人数、`resourceList[].resourceName` 来源名称、`resourceList[].count` 来源消费会员人数、`resourcePieList[].resourceName` 饼图来源名称、`resourcePieList[].count` 饼图来源消费会员人数。结果粒度为消费会员注册来源分布；占比可用 `count / totalCount` 计算，总人数为 0 时不输出占比。
