---
name: member-data-overview-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：使用固定数据概览接口 CLI 输出活跃用户、消费转化、新增会员、会员来源、卡型、消费金额、消费笔数、客单价、营销活动状态和储值趋势。适用于用户问“分析 CRM 数据概览整体表现”“会员数据概览怎么样”。只使用本文固定命令和固定门店编码获取 CLI；不使用近似指标或其它业务概念替代。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

# 数据概览综合分析业务 Skill

## 关键执行规范

1. 本 Skill 只能使用下方列出的固定 `<sl-sea-absolute> crm_data_overview` CLI 和固定门店编码获取 CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试 DataCube task，不得临场改写接口口径。
3. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
4. 用户只问单个模块时，只执行对应固定查询；用户问整体概览时，按执行顺序尽量完整执行。
5. 本 Skill 只做查询、分析和建议，不执行修改、导出敏感名单、发券或触达动作。
6. 不输出 token、session、cookie、密钥、认证参数；用户只问汇总或结论时，不主动展开完整 JSON。

## 用途

用于分析指定时间和门店筛选范围内的会员经营概览，输出活跃、消费转化、新增会员、会员来源、卡型结构、会员/非会员消费、营销活动状态和储值表现。

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
| `shopIds` | 用户指定门店，且候选唯一或用户已确认所选门店时，传对应编码数组；未指定门店时省略。 |

带门店的命令示例：

```text
<sl-sea-absolute> crm_data_overview summary --params '{"shopIds":["<omShopCode>"],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

## 固定接口模块

### 1. 数据汇总固定查询

用途：查询活跃用户、券、营销收益、账单金额、会员消费、客单价、储值和新增会员的汇总指标。

```text
<sl-sea-absolute> crm_data_overview summary --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：每个指标通常为 `{ value, changeValue }`，`value` 是当前值，`changeValue` 是对比变化值。

| 字段 | 说明 |
|---|---|
| `activeUserNums` | 小程序活跃用户数。 |
| `sendCouponNums` | 发券数。 |
| `useCouponNums` | 用券数。 |
| `marketingRevenue` | 营销收益。 |
| `billAmount` | 账单金额。 |
| `memberBillAmount` | 会员账单金额。 |
| `notMemberBillAmount` | 非会员账单金额。 |
| `memberConsumptionNums` | 会员消费笔数。 |
| `customerUnitPrice` | 客单价。 |
| `rechargeAmount` | 储值金额。 |
| `rechargeNums` | 储值笔数。 |
| `newUserNums` | 新增会员数。 |

### 2. 用户消费转化固定查询

用途：查询活跃用户到消费、复购和会员消费的转化指标。

```text
<sl-sea-absolute> crm_data_overview consume-change --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `activeUsers` | 活跃用户数。 |
| `consumeUsers` | 消费用户数。 |
| `repurchaseUsers` | 复购用户数。 |
| `newMembers` | 新增会员数。 |
| `consumeMembers` | 消费会员数。 |
| `repurchaseMembers` | 复购会员数。 |

### 3. 新增会员趋势固定查询

用途：查询新增会员趋势。

```text
<sl-sea-absolute> crm_data_overview member-increase --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `userNumList` | 与 `dateList` 按下标对齐的新增会员数列表。 |

### 4. 小程序活跃趋势固定查询

用途：查询小程序活跃用户和消费用户趋势。

```text
<sl-sea-absolute> crm_data_overview user-activity --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `activeUserNumList` | 与 `dateList` 按下标对齐的小程序活跃用户数列表。 |
| `consumeUserNumList` | 与 `dateList` 按下标对齐的消费用户数列表。 |

### 5. 会员来源分布固定查询

用途：查询会员来源人数分布。

```text
<sl-sea-absolute> crm_data_overview member-resource --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `memberResourceTotal` | 会员来源总数。 |
| `list[].memberResourceName` | 来源名称。 |
| `list[].memberResourceCount` | 来源会员数。 |

### 6. 会员卡型分布固定查询

用途：查询会员卡型人数分布。

```text
<sl-sea-absolute> crm_data_overview member-card-type --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `total` | 会员卡型总数。 |
| `cardTypeList` | 卡型名称列表。 |
| `cardTypeMembers` | 与 `cardTypeList` 按下标对齐的卡型会员数列表。 |

### 7. 账单金额趋势固定查询

用途：查询会员与非会员账单金额趋势。

```text
<sl-sea-absolute> crm_data_overview consume-amount --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `memberBillAmountList` | 与 `dateList` 按下标对齐的会员账单金额列表。 |
| `notMemberBillAmountList` | 与 `dateList` 按下标对齐的非会员账单金额列表。 |

### 8. 消费笔数趋势固定查询

用途：查询会员与非会员消费笔数趋势。

```text
<sl-sea-absolute> crm_data_overview consume-count --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `memberConsumptionNum` | 与 `dateList` 按下标对齐的会员消费笔数列表。 |
| `notMemberConsumptionNum` | 与 `dateList` 按下标对齐的非会员消费笔数列表。 |

### 9. 会员客单价趋势固定查询

用途：查询会员与非会员客单价趋势。

```text
<sl-sea-absolute> crm_data_overview consume-billapc --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `memberCustomerUnitPrice` | 与 `dateList` 按下标对齐的会员客单价列表。 |
| `notMemberCustomerUnitPrice` | 与 `dateList` 按下标对齐的非会员客单价列表。 |

### 10. 营销活动状态数量固定查询

用途：查询营销活动总数以及各状态活动数量。

```text
<sl-sea-absolute> crm_data_overview marketing-campaign --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `marketingCampaignTotal` | 营销活动总数。 |
| `list[].marketingCampaignStatus` | 活动状态。 |
| `list[].marketingCampaignCount` | 该状态活动数量。 |

### 11. 会员储值趋势固定查询

用途：查询会员储值金额和储值笔数趋势。

```text
<sl-sea-absolute> crm_data_overview member-recharge --params '{"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList` | 日期或月份列表。 |
| `memberRecharge` | 与 `dateList` 按下标对齐的会员储值金额列表。 |
| `memberRechargeNum` | 与 `dateList` 按下标对齐的会员储值笔数列表。 |

## 执行顺序

1. 标准化时间、门店和趋势粒度，计算上一周期。
2. 执行数据汇总固定查询。
3. 执行用户消费转化固定查询。
4. 执行新增会员趋势、小程序活跃趋势、会员来源分布、会员卡型分布。
5. 执行账单金额趋势、消费笔数趋势、会员客单价趋势。
6. 执行营销活动状态数量和会员储值趋势。

用户只问单个模块时，只执行对应固定查询，不为了补全报告追加其它查询。

## 合并与计算规则

| 指标 | 规则 |
|---|---|
| 汇总卡片指标 | 只使用数据汇总固定查询返回值。 |
| 消费率 | `consumeUsers / activeUsers * 100%`，分母为 0 时不可计算。 |
| 用户复购率 | `repurchaseUsers / consumeUsers * 100%`，分母为 0 时不可计算。 |
| 消费会员占比 | `consumeMembers / consumeUsers * 100%`，分母为 0 时不可计算。 |
| 会员复购率 | `repurchaseMembers / consumeMembers * 100%`，分母为 0 时不可计算。 |
| 新增会员占活跃比 | `newMembers / activeUsers * 100%`，分母为 0 时不可计算。 |
| 小程序消费率趋势 | `consumeUserNumList[i] / activeUserNumList[i] * 100%`，分母为 0 时不可计算。 |
| 会员账单金额占比 | 优先使用汇总卡片字段；需要按趋势日计算时，用会员账单金额除以会员和非会员账单金额之和。 |
| 单笔储值均额 | `memberRecharge[i] / memberRechargeNum[i]`，分母为 0 时不可计算。 |
| 会员来源占比 | `list[].memberResourceCount / memberResourceTotal * 100%`，分母为 0 时不可计算。 |
| 卡型占比 | `cardTypeMembers[i] / total * 100%`，分母为 0 时不可计算。 |
| 趋势横向比较 | 只有不同模块的 `dateList` 完全一致时才做横向比较；不一致时分别描述。 |
| 数组下标解释 | 只有标签数组和数值数组长度一致时才按下标解释；不一致时标注字段异常。 |

## 输出报告结构

1. 筛选条件：时间、上一周期、门店范围、趋势粒度。
2. 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
3. 核心数据：活跃用户、券、营销收益、账单金额、会员消费、客单价、储值、新增会员。
4. 转化分析：活跃到消费、复购、会员消费和会员复购。
5. 趋势与结构：新增会员、小程序活跃、来源、卡型、金额、笔数、客单价、储值趋势。
6. 异常或风险：接口失败、空数据、分母为 0、趋势不一致、样本过少、金额或比例异常。
7. 可执行建议：围绕活跃转化、会员增长、消费质量、营销活动和储值运营给动作建议。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 数据汇总固定查询失败 | 可以继续执行单模块分析，但必须标注缺少汇总卡片指标。 |
| `dateList` 不一致 | 不做跨趋势合并，只分别描述。 |
| 返回空数组或空对象 | 说明当前条件下未查到数据，提示检查时间、门店或权限。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
