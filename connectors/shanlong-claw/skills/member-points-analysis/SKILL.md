---
name: member-points-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：使用固定积分分析接口 CLI 输出积分笔数、积分额、兑换笔数、兑换额、积分/兑换趋势、规则分布、渠道分布和会员明细。适用于用户问“积分分析”“积分获得和兑换情况怎么样”“哪些规则或渠道贡献积分多”。只使用本文固定命令和固定门店编码获取 CLI；不使用近似指标或其它业务概念替代。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

# 积分分析业务 Skill

## 关键执行规范

1. 本 Skill 只能使用下方列出的固定 `<sl-sea-absolute> general`、`<sl-sea-absolute> channel` CLI 和固定门店编码获取 CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试其它接口路径，不得临场改写接口口径。
3. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
4. 默认业务查询模块是 3 个：基础指标与趋势、积分规则分布、积分渠道分布。会员明细只在用户要求名单、样例、会员明细或整体分析需要样例时执行。
5. 不主动执行积分调整、规则启停、导出敏感名单、触达会员等操作。
6. 不输出 token、session、cookie、密钥、认证参数；手机号、卡号等明细默认脱敏。

## 用途

用于分析指定时间、卡型和门店筛选范围内的积分表现，输出积分获得、积分兑换、趋势、规则贡献、渠道贡献和必要的会员明细样例。

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

## 时间与参数

用户只需要提供当前统计周期。不要向用户额外索要上一周期；`preBeginDate/preEndDate` 按当前周期等长前移。

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

| 参数 | 规则 |
|---|---|
| `beginDate` | 用户指定开始日转成 `yyyy-MM-dd 00:00:00`。 |
| `endDate` | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59`。 |
| 自然语言时间 | 如“近一个月”“本月”“上周”先解析为当前统计周期，再统一生成 `beginDate/endDate`。 |
| 默认时间 | 用户未指定时，默认最近 7 个完整自然日。 |
| `preBeginDate/preEndDate` | 不要求用户填写；按上述公式自动计算。 |
| `dateType` | 默认 `1` 按天；用户问月趋势或按月时用 `2`。 |
| `cardTypeIds` | 未指定卡型时传 `[]`。 |
| `shopFilterType` | 默认 `1`。 |
| `shopFilterTypeValue` | 未指定门店时传 `[]`；指定门店时使用门店查询 CLI 返回的 `omShopCode`。 |
| `dimensionType` | 会员明细默认 `1` 按积分；用户明确问兑换明细时用 `2`。 |
| `page/size` | 默认 `page=1,size=10`；用户要求更多时再提高，不要无边界拉全量。 |

通用 `--params` 基础形态：

```json
{
  "shopFilterType": 1,
  "shopFilterTypeValue": [],
  "cardTypeIds": [],
  "dateType": 1,
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>"
}
```

## 固定接口模块

### 1. 积分基础指标与趋势固定查询

用途：查询积分笔数、积分额、兑换笔数、兑换额、较上一周期变化以及积分/兑换趋势。

```text
<sl-sea-absolute> general get-score-base-info --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `scoreCount` | 积分笔数。 |
| `scoreCountFloatRangeValue` / `scoreCountFloatRangeType` | 积分笔数较上一周期变化比例和方向，`0` 无变化、`1` 上浮、`2` 下浮。 |
| `scoreAmount` | 积分额。 |
| `scoreAmountFloatRangeValue` / `scoreAmountFloatRangeType` | 积分额较上一周期变化比例和方向。 |
| `exchangeCount` | 兑换笔数。 |
| `exchangeCountFloatRangeValue` / `exchangeCountFloatRangeType` | 兑换笔数较上一周期变化比例和方向。 |
| `exchangeAmount` | 兑换额。 |
| `exchangeAmountFloatRangeValue` / `exchangeAmountFloatRangeType` | 兑换额较上一周期变化比例和方向。 |
| `scoreTrend.dateList` | 积分趋势日期。 |
| `scoreTrend.scoreAmountList` | 积分额趋势。 |
| `scoreTrend.scoreCountList` | 积分笔数趋势。 |
| `exchangeTrend.dateList` | 兑换趋势日期。 |
| `exchangeTrend.exchangeAmountList` | 兑换额趋势。 |
| `exchangeTrend.exchangeCountList` | 兑换笔数趋势。 |

结果粒度：当前筛选范围的汇总卡片和按天/按月趋势序列。返回 0 是合法结果，不代表接口失败。趋势数组为空或长度不一致时，只报告原始字段，不自行补齐或重算。

### 2. 积分规则分布固定查询

用途：查询各积分规则的积分额、积分笔数、积分会员数和饼图数据。

```text
<sl-sea-absolute> general get-score-rule-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `scoreTotal` | 规则分布积分额总计。 |
| `ruleList[].ruleName` | 规则名称。 |
| `ruleList[].scoreAmount` | 积分额。 |
| `ruleList[].scoreCount` | 积分笔数。 |
| `ruleList[].scorePersonCount` | 积分会员数。 |
| `ruleList[].proportion` | 占比；若接口未返回或为空，可按 `scoreAmount / scoreTotal` 辅助计算。 |
| `rulePieList[].ruleName` | 饼图规则名称。 |
| `rulePieList[].scoreAmount` | 饼图积分额。 |

结果粒度：积分规则。`ruleList=[]` 且 `scoreTotal=0` 表示当前筛选范围无规则分布数据；不要改用其它接口补造规则。

### 3. 积分渠道分布固定查询

用途：查询各渠道的积分额、积分笔数、积分会员数和饼图数据。

```text
<sl-sea-absolute> channel get-score-channel-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `scoreTotal` | 渠道分布积分额总计。 |
| `channelList[].channelName` | 渠道名称。 |
| `channelList[].scoreAmount` | 积分额。 |
| `channelList[].scoreCount` | 积分笔数。 |
| `channelList[].scorePersonCount` | 积分会员数。 |
| `channelList[].proportion` | 占比；若接口未返回或为空，可按 `scoreAmount / scoreTotal` 辅助计算。 |
| `channelPieList[].channelName` | 饼图渠道名称。 |
| `channelPieList[].scoreAmount` | 饼图积分额。 |

结果粒度：积分渠道。`channelList=[]` 且 `scoreTotal=0` 表示当前筛选范围无渠道分布数据；不要改用其它接口补造渠道。

### 4. 会员积分明细固定查询

用途：分页查询会员积分或兑换明细，返回积分额、兑换额、次数和最后一次操作时间。

```text
<sl-sea-absolute> general get-member-score --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"dimensionType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输入补充：`dimensionType=1` 按积分，`dimensionType=2` 按兑换；默认 `page=1,size=10`。

输出字段：

| 字段 | 说明 |
|---|---|
| `total` | 会员明细总条数。 |
| `list[].memberName` | 姓名。 |
| `list[].shopName` | 所属门店。 |
| `list[].saledShopName` | 售卡门店。 |
| `list[].memberMobile` | 手机号，输出报告中需脱敏。 |
| `list[].cardNo` | 卡号，输出报告中需脱敏。 |
| `list[].cardTypeName` | 卡型。 |
| `list[].memberSex` | 性别。 |
| `list[].memberBirthday` | 生日。 |
| `list[].amount` | 当 `dimensionType=1` 时为积分额；当 `dimensionType=2` 时为兑换额。 |
| `list[].count` | 当 `dimensionType=1` 时为积分次数；当 `dimensionType=2` 时为兑换次数。 |
| `list[].lastOptTime` | 最后一次操作时间。 |

结果粒度：会员卡维度的分页明细。`total=0` 且 `list=[]` 表示当前筛选范围没有会员积分/兑换明细。

## 执行顺序

1. 标准化时间、卡型、门店、趋势粒度和分页参数，计算上一周期。
2. 执行积分基础指标与趋势固定查询。
3. 执行积分规则分布固定查询。
4. 执行积分渠道分布固定查询。
5. 如用户需要名单、样例、会员明细或整体分析需要少量样例，执行会员积分明细固定查询；默认 `dimensionType=1` 按积分、`page=1,size=10`。
6. 如用户明确问兑换会员明细，再执行一次会员积分明细固定查询，把 `dimensionType` 改为 `2`。

用户只问单个模块时，只执行对应固定查询，不为了补全报告追加其它查询。

## 合并与计算规则

| 指标 | 规则 |
|---|---|
| 积分笔数、积分额、兑换笔数、兑换额 | 只使用积分基础指标与趋势固定查询返回值。 |
| 较上一周期 | 使用基础指标接口返回的 `FloatRangeValue` 和 `FloatRangeType`；不自行重算覆盖。 |
| 积分趋势 | 使用 `scoreTrend.dateList`、`scoreAmountList`、`scoreCountList`。 |
| 兑换趋势 | 使用 `exchangeTrend.dateList`、`exchangeAmountList`、`exchangeCountList`。 |
| 趋势解释 | 只有日期数组和数值序列长度一致时才按下标解释高低点。 |
| 规则占比 | 优先使用 `ruleList[].proportion`；缺失时可用 `scoreAmount / scoreTotal` 计算，分母为 0 时不计算。 |
| 渠道占比 | 优先使用 `channelList[].proportion`；缺失时可用 `scoreAmount / scoreTotal` 计算，分母为 0 时不计算。 |
| 规则和渠道 | 是不同维度，不能按行直接关联，也不能把规则贡献归因到某个渠道。 |
| 会员明细 | 默认最多展示 3 条脱敏样例；手机号、卡号不要完整展开。 |
| 兑换明细 | 只有执行 `dimensionType=2` 后才能输出兑换额/兑换次数会员排行。 |

## 输出报告结构

1. 筛选条件：时间、上一周期、卡型、门店、趋势粒度、会员明细口径。
2. 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
3. 核心指标：积分笔数、积分额、兑换笔数、兑换额，含较上一周期变化。
4. 趋势判断：积分获得和积分兑换的高低点、连续为 0、异常波动。
5. 结构分布：积分规则 Top 项、积分渠道 Top 项，并注明分布口径。
6. 明细提示：会员积分/兑换明细总条数、脱敏样例或不展示原因。
7. 风险与建议：样本少、分母为 0、规则过于集中、渠道过于集中、兑换活跃度异常等。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 基础指标失败 | 可以继续输出规则、渠道和明细，但必须标注缺少核心汇总。 |
| 返回空对象或空列表 | 说明当前条件无数据，提示检查时间、卡型、门店或权限。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
