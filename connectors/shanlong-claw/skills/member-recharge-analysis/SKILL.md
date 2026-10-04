---
name: member-recharge-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：组合固定储值分析接口，输出储值基础指标、扣减、趋势、规则、渠道、会员明细和档位分析。适用于用户问“分析近一个月储值整体情况”“储值金额、扣减、趋势和结构怎么样”。用于储值发生额与结构分析；不要替代储值余额、储值转化率或余额预警分析。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

1. 本业务 Skill 必须只依赖本文件及附带运行规则明确写出的固定 CLI、固定接口和参数规则执行。
2. 执行时不得搜索、读取或要求用户安装其它统计模块文档；本文已经内置储值分析所需的固定接口、入参、出参和边界。
3. 只有固定 CLI 不存在、命令失败、鉴权失败、参数缺失，或本文没有提供可执行命令时，才按失败处理；面向业务用户只说明失败模块、业务影响和可核对范围，只有用户明确要求排查执行问题时，才展示底层命令、参数或错误摘要。

## 标准安全与边界（最高优先级）

1. 只使用本 Skill 明确写出的固定 CLI 或固定接口；不得搜索其它命令、不得执行 help 探测、不得猜测或替换固定命令。
2. 本业务 Skill 只执行本文明确列出的固定接口；不用近似指标或其它业务 Skill 替代。
3. 用户问题不属于本 Skill 名称、description 或正文边界时，停止并说明不属于储值发生额与结构分析口径；无法确定时先列出候选方向让用户确认，不自行猜测。
4. 本 Skill 默认只读安全：不主动执行新增、修改、删除、发券、触达、导出敏感名单等动作。
5. 不输出 token、session、cookie、密钥、内部网关认证参数；会员姓名、手机号、会员编号、订单号等敏感信息默认脱敏。
6. 命令失败、接口异常、查询超时、空数组和指标为 0 必须区分；失败不能写成 0，空数据不能编造结论。
7. 输出必须说明统计时间、门店/集团视角和关键口径；涉及占比、转化率、环比或同比时说明分子、分母或对比基准。

# 储值分析

本 Skill 是业务 Skill，按固定直接接口 CLI 模块生成储值分析报告。它使用固定储值分析接口口径。

## 边界规则

- 用户问储值整体情况、储值金额、扣减、趋势、规则、渠道、明细或档位表现时使用本 Skill。
- 用户只问其中单个储值模块时，直接执行本文对应固定 CLI。
- 用户问会员数据概览类储值趋势时，不属于本 Skill，停止并提示该问题属于数据概览口径。
- 用户问储值余额健康、余额分层、余额预警客户时，不属于本 Skill，停止并提示该问题属于储值余额口径。
- 用户问新会员储值转化、首充/续充、转化率时，不属于本 Skill，停止并提示该问题属于储值转化率口径。
- 不允许把示例值当作实时结果；实时结果必须来自本文固定接口 CLI。

## 固定接口模块

| 模块 | 固定 CLI | 用途 | 默认执行 |
|---|---|---|---|
| 储值基础指标 | `<sl-sea-absolute> general get-accumulated-amount-info` | 储值金额、笔数、平均储值额以及新老会员拆分。 | 是 |
| 储值扣减指标 | `<sl-sea-absolute> general get-deductions-amount-info` | 储值扣减金额、本期沉淀本金、累计沉淀本金。 | 是 |
| 储值趋势 | `<sl-sea-absolute> general get-new-trend-chart` | 按天或按月返回储值金额、笔数、平均储值额趋势。 | 是 |
| 储值规则分布 | `<sl-sea-absolute> general get-distribution-rule-data` | 各储值规则的金额、本金、赠送、笔数和人数。 | 是 |
| 储值渠道分布 | `<sl-sea-absolute> channel get-distribution-channel-data` | 各渠道的储值金额、本金、赠送、笔数和人数。 | 是 |
| 储值会员明细 | `<sl-sea-absolute> general get-detail-data` | 分页返回储值会员累计明细。 | 用户需要名单、样例或明细时执行 |
| 储值档位 | `<sl-sea-absolute> general get-gear-data` | 分页返回储值档位、笔数、本金、赠送和日期。 | 用户问档位或整体分析时执行 |

## 执行顺序

1. 标准化时间、卡型、门店参数，计算上一周期。
2. 执行储值基础指标。
3. 执行储值扣减指标。
4. 执行储值趋势。
5. 执行储值规则分布。
6. 执行储值渠道分布。
7. 如用户需要名单、样例或明细，执行储值会员明细；默认只取第一页。
8. 如用户问档位或整体分析，执行储值档位；默认只取第一页。

## 参数规范

用户只需要提供当前统计周期。不要向用户额外索要上一区间；`preBeginDate/preEndDate` 按当前周期整体前移同样天数自动计算：

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

也就是把当前周期整体向前平移同样天数。示例：当前周期为 `2026-05-11 00:00:00` 到 `2026-05-17 23:59:59` 时，`rangeDays=7`，上一区间为 `2026-05-04 00:00:00` 到 `2026-05-10 23:59:59`。

| 参数 | 规则 |
|---|---|
| `beginDate` | 用户指定开始日转成 `yyyy-MM-dd 00:00:00` |
| `endDate` | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59` |
| 自然语言时间 | 如“近一个月”“本月”“上周”先解析为当前统计周期，再统一生成 `beginDate/endDate` |
| 默认时间 | 用户未指定时，默认最近 7 个完整自然日 |
| `preBeginDate/preEndDate` | 不要求用户填写；按上述前端平移公式从当前周期自动计算 |
| `dateType` | 默认 `1` 按天；用户问月趋势/按月时用 `2` |
| `cardTypeIds` | 未指定卡型时传 `[]` |
| `shopFilterType` | 默认 `1` |
| `shopFilterTypeValue` | 未指定门店时传 `[]`；指定门店时先按“门店编码获取 CLI”得到唯一 `omShopCode`，再传 `['<omShopCode>']` |
| 明细分页 | 默认 `page=1,size=10`；用户要求更多时再提高，但不要无边界拉全量 |

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

## 统一参数模板

未指定门店、未指定卡型时，各固定接口使用以下 `--params` 基础形态。指定门店或卡型时，只替换对应数组。

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

## 固定接口 CLI 详情

### 储值基础指标

```text
<sl-sea-absolute> general get-accumulated-amount-info --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`rechargeTotal` 储值金额，`newMemberRecharge` 新会员储值金额，`oldMemberRecharge` 老会员储值金额，`rechargeAmount` 储值笔数，`newMemberRechargeAmount` 新会员储值笔数，`oldMemberRechargeAmount` 老会员储值笔数，`rechargeAverage` 平均储值额，`newMemberRechargeAverage` 新会员平均储值额，`oldMemberRechargeAverage` 老会员平均储值额。字段对象通常包含 `value`、`floatRangeType`、`floatRange`、`principalMoney`、`donateMoney`、`proportion`。

### 储值扣减指标

```text
<sl-sea-absolute> general get-deductions-amount-info --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`rechargeReduce` 储值扣减金额，`rechargePrecipitate` 本期沉淀本金，`rechargePrecipitateTotal` 累计沉淀本金。字段对象通常包含 `value`、`floatRangeType`、`floatRange`。

### 储值趋势

```text
<sl-sea-absolute> general get-new-trend-chart --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`dateList` 日期或月份列表，`rechargeMoneyList` 储值金额序列，`rechargeAmountList` 储值笔数序列，`rechargeAverageList` 平均储值额序列。只有 `dateList` 与所有序列长度一致时才能按下标横向解释。

### 储值规则分布

```text
<sl-sea-absolute> general get-distribution-rule-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`rechargeTotal` 规则分布总储值金额，`ruleList[].ruleName` 规则名称，`ruleList[].rechargeMoney` 储值金额，`ruleList[].principalMoney` 本金金额，`ruleList[].donateMoney` 赠送金额，`ruleList[].rechargeAmount` 储值笔数，`ruleList[].rechargeMemberCount` 储值人数。规则金额占比可按 `rechargeMoney / rechargeTotal` 计算；总额为 0 时不输出占比。

### 储值渠道分布

```text
<sl-sea-absolute> channel get-distribution-channel-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：`rechargeTotal` 渠道分布总储值金额，`channelList[].channelName` 渠道名称，`channelList[].rechargeMoney` 储值金额，`channelList[].principalMoney` 本金金额，`channelList[].donateMoney` 赠送金额，`channelList[].rechargeAmount` 储值笔数，`channelList[].rechargeMemberCount` 储值人数。渠道金额占比可按 `rechargeMoney / rechargeTotal` 计算；总额为 0 时不输出占比。

### 储值会员明细

```text
<sl-sea-absolute> general get-detail-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输出字段：`list[].memberName` 姓名，`list[].shopName` 所属门店，`list[].saledShopName` 售卡门店，`list[].memberMobile` 手机号，`list[].cardNo` 卡号，`list[].memberSex` 性别，`list[].memberBirthday` 生日，`list[].rechargeMoney` 累计储值金额，`list[].rechargeRealMoney` 累计储值本金，`list[].rechargeDonateMoney` 累计储值赠送，`list[].rechargeAmount` 累计储值次数，`list[].lastOptTime` 最后一次操作时间，`total` 总条数。手机号、卡号属于明细数据，默认只输出条数和必要脱敏样例。

### 储值档位

```text
<sl-sea-absolute> general get-gear-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' --format json
```

输出字段：`list[].shopName` 门店名称，`list[].rechargeMoney` 储值档位，`list[].rechargeAmount` 储值笔数，`list[].totalPrincipalMoney` 储值本金，`list[].totalDonateMoney` 储值赠送，`list[].rechargeDate` 日期或月份，`total` 总条数。档位是分布维度，不应与规则分布或渠道分布直接按行合并。

## 合并与计算规则

| 指标 | 规则 |
|---|---|
| 新会员储值占比 | 优先使用基础指标接口的 `proportion` |
| 老会员储值占比 | 优先使用基础指标接口的 `proportion` |
| 赠送占比 | `donateMoney / value`，仅在接口未直接给出且分母大于 0 时计算 |
| 平均储值额 | 优先使用基础指标接口，不用金额/笔数重算覆盖 |
| 规则/渠道占比 | `rechargeMoney / rechargeTotal`，总额为 0 时不计算 |
| 趋势比较 | 只有 `dateList` 和序列长度一致时才按下标解释 |
| 明细样例 | 默认最多展示 3 条脱敏样例；手机号、卡号不要完整展开 |
| 档位分析 | 与规则、渠道是不同维度，不能按行直接关联 |

## 输出报告结构

1. 筛选条件：时间、上一区间、卡型、门店、趋势粒度。
2. 执行摘要：执行了哪些固定接口，哪些成功、失败或为空。
3. 核心指标：储值金额、本金、赠送、笔数、平均储值额、新老会员拆分。
4. 扣减与沉淀：储值扣减金额、本期沉淀本金、累计沉淀本金。
5. 趋势判断：金额、笔数、均额的高低点和异常波动。
6. 结构分布：规则分布、渠道分布、档位分布的 Top 项。
7. 明细提示：总条数、样例或不展示原因。
8. 风险与建议：样本少、分母为 0、渠道集中、规则集中、扣减偏高等。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要 |
| 基础指标失败 | 可以继续输出分布和趋势，但必须标注缺少核心汇总 |
| 返回空对象/空列表 | 说明当前条件无数据，提示检查时间、卡型、门店、权限 |
| 字段缺失 | 标注缺失字段，不用近似字段替代 |
| CRM 登录/解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要 |
