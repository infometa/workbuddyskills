---
name: member-coupon-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：使用固定卡券接口 CLI 分析发券、用券、作废、收益、抵扣、撬动、响应时间、券模板和门店表现。适用于用户问“卡券分析”“最近发券用券效果怎么样”“哪些券核销表现好”。只使用本文固定命令和固定门店编码获取 CLI；不使用近似指标或其它业务概念替代。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

# 卡券分析业务 Skill

## 关键执行规范（最高优先级）

1. 本 Skill 只能使用下方列出的固定 `<sl-sea-absolute> coupon` CLI 和固定门店编码获取 CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试其它接口路径，不得临场改写接口口径。
3. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
4. 默认业务查询模块是 5 个：核心指标、发券趋势、用券趋势、响应时间、券模板表现。只有用户要求门店维度，或整体分析明确需要门店表现时，才执行门店券列表和门店表现 2 个模块。
5. 不主动执行发券、作废券、导出明细、触达会员等写操作或敏感操作。
6. 不输出 token、session、cookie、密钥、认证参数；会员姓名、手机号、会员编号、订单号等敏感信息默认脱敏。
7. 结论只能来自本轮固定接口返回；不能把空数据推断成“券没配置”“门店没使用”“权限错误”等未被结果直接证明的原因。

## 用途

用于分析指定发券时间、核销时间、券类型、券名称/别名/ID、发券门店、核销门店和回收站口径下的卡券表现，输出整体指标、趋势、响应时间、券模板表现和可选门店表现。

本 Skill 不处理券模板配置、发券操作、作废操作、券明细穿透、营销活动效果或会员消费大盘。如果用户只问这些内容，说明本 Skill 只能输出卡券分析统计结果。

## 时间范围

用户可以分别指定发券时间和核销时间；如果只给一个时间范围，默认同时作为发券时间和核销时间。

- 用户给自然日时，开始时间展开为 `00:00:00`，结束时间展开为 `23:59:59`。
- 用户未指定时间时，默认最近 7 个完整自然日。
- `preBeginDate/preEndDate` 是发券时间上一周期，按当前发券周期等长前移。
- `usePreBeginDate/usePreEndDate` 是核销时间上一周期，按当前核销周期等长前移。

上一周期计算：

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

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

## 通用参数

固定接口模块共用以下参数。执行时把占位符替换成实际值，不要省略必填时间字段。

```json
{
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>",
  "useBeginDate": "<useBeginDate>",
  "useEndDate": "<useEndDate>",
  "usePreBeginDate": "<usePreBeginDate>",
  "usePreEndDate": "<usePreEndDate>",
  "couponTypeIds": [],
  "searchType": 1,
  "searchTypeValue": "",
  "shopFilterType": 1,
  "shopFilterTypeValue": [],
  "useShopFilterType": 1,
  "useShopFilterTypeValue": [],
  "includeRecycle": 0
}
```

| 参数 | 说明 |
|---|---|
| `couponTypeIds` | 券类型 ID 数组，未指定时传 `[]`。 |
| `searchType` | `1` 券名称，`2` 券别名，`3` 券模板 ID；默认 `1`。 |
| `searchTypeValue` | 券名称、别名或券模板 ID；未指定时传空字符串。 |
| `includeRecycle` | 默认 `0` 不统计回收站券；用户明确要求包含回收站时传 `1`。 |
| `page/size` | 表格模块默认 `page=1,size=10`；用户要求更多时再提高，不要无边界拉全量。 |

## 固定接口模块

### 1. 卡券核心指标固定查询

用途：查询发券、可用、核销、作废、收益、抵扣、撬动和累计口径。

```text
<sl-sea-absolute> coupon get-coupon-data-indicators --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0}' --format json
```

### 2. 发券趋势固定查询

用途：查询卡券发券数量的时间趋势。

```text
<sl-sea-absolute> coupon coupon-send-analysis --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0}' --format json
```

### 3. 用券趋势固定查询

用途：查询卡券用券数量的时间趋势。

```text
<sl-sea-absolute> coupon coupon-used-analysis --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0}' --format json
```

### 4. 响应时间固定查询

用途：查询从发券到用券的响应时间人数分布。

```text
<sl-sea-absolute> coupon coupon-response-time-analysis --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0}' --format json
```

### 5. 券模板表现固定查询

用途：按券模板维度统计发券、用券、作废、核销率、抵扣和拉动账单数据。

```text
<sl-sea-absolute> coupon get-coupon-analysis --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0,"couponIds":[],"dimensionType":1,"sortField":null,"order":null,"page":1,"size":10}' --format json
```

### 6. 门店分析券列表固定查询

用途：查询按门店分析可筛选的券模板列表。只有需要门店表现时执行。

```text
<sl-sea-absolute> coupon get-coupon-shop-analysis-coupon-list --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0}' --format json
```

### 7. 门店券表现固定查询

用途：按门店和券模板交叉统计发券、用券、抵扣和拉动账单数据。执行前必须已有至少 1 个 `couponId`。

```text
<sl-sea-absolute> coupon get-store-coupon-analysis-list --params '{"beginDate":"<beginDate>","endDate":"<endDate>","useBeginDate":"<useBeginDate>","useEndDate":"<useEndDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","usePreBeginDate":"<usePreBeginDate>","usePreEndDate":"<usePreEndDate>","couponTypeIds":[],"searchType":1,"searchTypeValue":"","shopFilterType":1,"shopFilterTypeValue":[],"useShopFilterType":1,"useShopFilterTypeValue":[],"includeRecycle":0,"couponIds":["<couponId>"],"dimensionType":2,"sortField":null,"order":null,"page":1,"size":10}' --format json
```

## 输出字段说明

### 卡券核心指标固定查询

| 字段 | 说明 |
|---|---|
| `sendCouponCount` | 券发放张数。 |
| `availableCouponCount` | 券可用张数。 |
| `useCouponCount` | 券核销张数。 |
| `invalidCouponCount` | 券作废张数。 |
| `incomeCouponMoney` | 券收益金额。 |
| `deductionCouponMoney` | 券抵扣金额。 |
| `consumeCouponMoney` | 券撬动金额。 |
| `availableCouponCountProportion` | 可用张数占发放张数比例。 |
| `useCouponCountProportion` | 核销张数占发放张数比例。 |
| `invalidCouponCountProportion` | 作废张数占发放张数比例。 |
| `deductionCouponMoneyProportion` | 抵扣金额占券收益金额比例。 |
| `consumeCouponMoneyProportion` | 撬动金额占券收益金额比例。 |
| `totalIncomeCouponMoney` | 累计收益。 |
| `totalSendCouponCount` | 发券累计数。 |
| `totalUseCouponCount` | 用券累计数。 |
| `totalInvalidCouponCount` | 作废券累计数。 |
| `totalUseCouponCountProportion` | 券核销比例。 |
| `totalDeductionCouponMoney` | 累计抵扣金额。 |
| `*FloatRangeValue` / `*FloatRangeType` | 较上一区间变化比例和方向，直接使用接口返回。 |

### 趋势与响应时间固定查询

| 模块 | 字段 | 说明 |
|---|---|---|
| 发券趋势 | `sendChart.date` | 发券趋势日期序列。 |
| 发券趋势 | `sendChart.grossNum` | 每个日期对应的发券张数。 |
| 用券趋势 | `usedChart.date` | 用券趋势日期序列。 |
| 用券趋势 | `usedChart.usedNum` | 每个日期对应的用券张数。 |
| 响应时间 | `bar.label` | 响应时间分桶标签。 |
| 响应时间 | `bar.labelValue` | 每个分桶对应人数。 |

### 券模板表现固定查询

| 字段 | 说明 |
|---|---|
| `total` | 总条数。 |
| `list[].couponName` | 券名称。 |
| `list[].couponId` | 券模板 ID。 |
| `list[].couponAlias` | 券别名。 |
| `list[].couponMoney` | 购买金额。 |
| `list[].sendCouponCount` | 发券数。 |
| `list[].useCouponCount` | 用券数。 |
| `list[].invalidCouponCount` | 作废数。 |
| `list[].useCouponPercent` | 核销率。 |
| `list[].deductionMoney` | 抵扣金额。 |
| `list[].couponConsumeCount` | 拉动账单笔数。 |
| `list[].couponConsumeMoney` | 拉动账单金额。 |

### 门店表现固定查询

| 模块 | 字段 | 说明 |
|---|---|---|
| 门店分析券列表 | `data[].couponName` | 券名称。 |
| 门店分析券列表 | `data[].couponId` | 券模板 ID。 |
| 门店券表现 | `total` | 门店总条数。 |
| 门店券表现 | `list[].shopName` | 门店名称。 |
| 门店券表现 | `list[].shopId` | 门店 ID。 |
| 门店券表现 | `list[].couponList[].couponId` | 券模板 ID。 |
| 门店券表现 | `list[].couponList[].couponName` | 券名称。 |
| 门店券表现 | `list[].couponList[].sendCouponCount` | 发券数量。 |
| 门店券表现 | `list[].couponList[].useCouponCount` | 用券数量。 |
| 门店券表现 | `list[].couponList[].deductionMoney` | 抵扣金额。 |
| 门店券表现 | `list[].couponList[].couponConsumeCount` | 拉动账单笔数。 |
| 门店券表现 | `list[].couponList[].couponConsumeMoney` | 拉动账单金额。 |

## 合并与解释规则

| 指标 | 规则 |
|---|---|
| 总体概况 | 使用卡券核心指标固定查询的 `total*` 字段。 |
| 数据指标 | 使用卡券核心指标固定查询的非 `total*` 字段。 |
| 累计收益 vs 券收益金额 | 不能混同。累计收益只按核销时间统计；券收益金额同时受发券时间和核销时间约束。 |
| 用券累计数 vs 券核销张数 | 不能混同。用券累计数只按核销时间统计；券核销张数要求券也在发券时间内发放。 |
| 券核销比例 | 使用 `totalUseCouponCountProportion`，不要自行改分母。 |
| 可用/核销/作废占比 | 优先使用接口返回比例；字段缺失时可按 `sendCouponCount` 计算并注明本地计算。 |
| 抵扣/撬动占比 | 优先使用接口返回比例；字段缺失时可按 `incomeCouponMoney` 计算并注明本地计算。 |
| 发券趋势 | 使用 `sendChart.date` 和 `sendChart.grossNum` 按下标对应。 |
| 用券趋势 | 使用 `usedChart.date` 和 `usedChart.usedNum` 按下标对应。 |
| 响应时间 | 使用 `bar.label` 和 `bar.labelValue`。 |
| 券模板表现 | 默认展示当前页前 10 条，按发券、核销、抵扣、拉动账单识别表现突出券。 |
| 门店表现 | 必须先取得 `couponId`；门店分析券列表为空时，不执行门店券表现固定查询。 |

## 输出要求

默认输出结构：

- 筛选条件：发券时间、核销时间、券类型、券搜索、发券门店、核销门店、回收站口径、分页。
- 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
- 总体概况：累计收益、发券累计数、用券累计数、作废券累计数、券核销比例、累计抵扣金额。
- 数据指标：发放、可用、核销、作废、收益、抵扣、撬动及较上一区间变化。
- 趋势判断：发券趋势、用券趋势高低点、连续为 0、异常波动。
- 响应时间：主要响应时间分桶及人数集中情况。
- 券模板表现：高发券、高核销、高抵扣、高拉动券。
- 门店表现：如执行门店券表现固定查询，输出门店维度亮点；未执行则说明原因。
- 口径提示：说明累计指标与数据指标的时间约束差异。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 核心指标失败 | 可以继续输出趋势和表格，但必须标注缺少核心汇总。 |
| 返回空对象或空列表 | 说明当前条件无数据，并列出筛选条件。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| CRM 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
