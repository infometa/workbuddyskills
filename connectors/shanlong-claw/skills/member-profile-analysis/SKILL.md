---
name: member-profile-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：使用固定用户画像接口 CLI 分析一批会员的基础指标、生日、年龄、性别、入会来源、消费频次、入会时长和星座分布。适用于用户问“分析本月新增会员的用户画像分布”“用户画像结构怎么样”。仅用于群体画像；不用于手机号、会员号、卡号等单个会员查询。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

# 用户画像分析业务 Skill

## 关键执行规范

1. 本 Skill 只能使用下方列出的 4 条固定 `<sl-sea-absolute> general` CLI 和固定门店编码获取 CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试未列出的接口路径，不得临场改写接口口径。
3. 四个用户画像模块必须使用同一组 `beginDate`、`endDate`、`preBeginDate`、`preEndDate`、`accountTypeIds`、`shopFilterType`、`shopFilterTypeValue`。
4. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
5. 本 Skill 只做群体画像分析。用户要查某一个会员、手机号、会员号、卡号或会员编号时，停止执行并说明本 Skill 不处理单会员查询。
6. 不主动执行新增、修改、删除、发券、触达、导出敏感名单等操作。
7. 不输出 token、session、cookie、密钥、认证参数；涉及会员标识时默认脱敏。

## 用途

用于分析指定加入时间、会员来源、门店筛选范围内的一批会员画像，输出基础指标、人口属性、入会来源、消费频次、入会时长和星座分布，并给出可运营分群建议。

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
| `beginDate` | 加入时间开始；用户只给日期时转成 `yyyy-MM-dd 00:00:00`。 |
| `endDate` | 加入时间结束；用户只给日期时转成 `yyyy-MM-dd 23:59:59`。 |
| 自然语言时间 | 如“近一个月”“本月”“上周”先解析为当前统计周期，再统一生成 `beginDate/endDate`。 |
| 默认时间 | 用户未指定时，默认最近 7 个完整自然日。 |
| `preBeginDate/preEndDate` | 不要求用户填写；按上述公式自动计算。 |
| `dateType` | 默认 `1`。 |
| `accountTypeIds` | 会员来源 ID 数组；未指定会员来源时传 `[]`。 |
| `shopFilterType` | 默认 `1`。 |
| `shopFilterTypeValue` | 未指定门店时传 `[]`；指定门店时使用门店查询 CLI 返回的 `omShopCode`。 |

通用 `--params` 基础形态：

```json
{
  "shopFilterType": 1,
  "shopFilterTypeValue": [],
  "accountTypeIds": [],
  "dateType": 1,
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>"
}
```

## 固定接口模块

### 1. 基础指标与基础分布固定查询

用途：查询会员总数、新增会员数量、平均消费次数、平均客单价、生日月份、年龄和性别分布。

```text
<sl-sea-absolute> general get-member-base-info --params '{"shopFilterType":1,"shopFilterTypeValue":[],"accountTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `memberTotalCount` | 会员总数。 |
| `memberCount` | 当前筛选区间新增会员数量。 |
| `avgConsumeTimes` | 平均消费次数。 |
| `avgConsumeMoney` | 平均客单价。 |
| `avgConsumeTimesFloatRangeType` / `avgConsumeTimesFloatRangeValue` | 平均消费次数较上一区间变化方向和变化值。 |
| `avgConsumeMoneyFloatRangeType` / `avgConsumeMoneyFloatRangeValue` | 平均客单价较上一区间变化方向和变化值。 |
| `birthdayInfo.monthList` | 生日月份列表。 |
| `birthdayInfo.memberCountList` | 与 `birthdayInfo.monthList` 按下标对齐的会员人数列表。 |
| `ageInfo.memberCount` | 年龄分布总人数。 |
| `ageInfo.dataList` | 年龄分布明细；按接口返回的分段、人数和占比解释。 |
| `sexInfo.dataList` | 性别分布明细；按接口返回的性别、人数和占比解释。 |

结果粒度：基础指标为当前筛选范围汇总值；生日、年龄、性别为分布粒度。返回 0 是合法结果，不代表接口失败。

### 2. 入会来源分布固定查询

用途：查询会员入会来源分布、来源人数和来源 ID。

```text
<sl-sea-absolute> general get-sources-membership-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"accountTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `memberCount` | 入会来源分布总人数。 |
| `dataList[].name` | 来源名称。 |
| `dataList[].value` | 来源人数。 |
| `dataList[].id` | 来源 ID，可作为 `accountTypeIds` 的过滤值。 |

结果粒度：来源维度。`dataList=[]` 表示当前筛选范围无来源分布数据；不要改用其它接口补造来源。

### 3. 消费频次分布固定查询

用途：查询会员消费频次分段人数，用于识别未消费、低频消费和高频消费会员结构。

```text
<sl-sea-absolute> general get-consumption-frequency-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"accountTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `memberCount` | 消费频次分布总人数。 |
| `dataList[].name` | 消费频次分段；常见分段包括 `0次`、`1-3次`、`4-6次`、`7-10次`、`11-20次`、`21-30次`、`30次以上`，实际以接口返回为准。 |
| `dataList[].value` | 对应分段人数。 |

结果粒度：消费频次分段。若接口只返回人数，占比可按 `dataList[].value / memberCount` 计算并注明；分母为 0 时不计算。

### 4. 入会时长与星座分布固定查询

用途：查询入会时长分段、分段占比和星座分布。

```text
<sl-sea-absolute> general get-regular-membership-data --params '{"shopFilterType":1,"shopFilterTypeValue":[],"accountTypeIds":[],"dateType":1,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `durationInfo.durationList` | 入会时长分段；常见分段包括 `0-7天`、`8-30天`、`31-90天`、`91-180天`、`181-365天`、`365天以上`，实际以接口返回为准。 |
| `durationInfo.memberCountList` | 与 `durationInfo.durationList` 按下标对齐的各分段人数。 |
| `durationInfo.memberProportionList` | 与 `durationInfo.durationList` 按下标对齐的各分段占比。 |
| `constellationInfo.constellationList` | 星座列表。 |
| `constellationInfo.memberCountList` | 与 `constellationInfo.constellationList` 按下标对齐的各星座人数。 |

结果粒度：入会时长分段和星座分布。数组长度不一致时必须说明接口字段异常，不自行补齐。

## 执行顺序

1. 标准化时间、会员来源、门店参数，计算上一周期。
2. 执行基础指标与基础分布固定查询。
3. 执行入会来源分布固定查询。
4. 执行消费频次分布固定查询。
5. 执行入会时长与星座分布固定查询。
6. 合并输出时先给数据概览，再给画像结构，最后给运营建议。

用户只问单个模块时，只执行对应固定查询，不为了补全报告追加其它查询。

## 合并与计算规则

| 指标 | 规则 |
|---|---|
| 会员总数、新增会员数量、平均消费次数、平均客单价 | 只使用基础指标与基础分布固定查询返回值。 |
| 较上一周期 | 使用基础指标接口返回的 `FloatRangeType` 和 `FloatRangeValue`；不自行重算覆盖。 |
| 生日月份分布 | 按 `birthdayInfo.monthList` 与 `birthdayInfo.memberCountList` 下标对齐解释。 |
| 年龄、性别分布 | 使用 `ageInfo.dataList`、`sexInfo.dataList`；字段缺失时不补造分段。 |
| 入会来源占比 | 优先使用接口返回占比；缺失时可按 `dataList[].value / memberCount` 计算，分母为 0 时不计算。 |
| 消费频次占比 | 优先使用接口返回占比；缺失时可按 `dataList[].value / memberCount` 计算，分母为 0 时不计算。 |
| 入会时长 | 按 `durationList`、`memberCountList`、`memberProportionList` 下标对齐解释。 |
| 星座 | 按 `constellationList`、`memberCountList` 下标对齐解释；不根据生日自行推导。 |
| 分布数组 | 只有标签数组和数值数组长度一致时才按下标解释；不一致时标注字段异常。 |

## 输出报告结构

1. 筛选条件：加入时间、上一周期、会员来源、门店范围。
2. 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
3. 数据概览：会员总数、新增会员数量、平均消费次数、平均客单价及较上一区间变化。
4. 画像分布：生日、年龄、性别、入会来源、消费频次、入会时长、星座。
5. 重点人群：未消费会员、资料未知会员、新入会短周期会员、来源占比较高或异常的人群。
6. 风险与建议：样本少、未知占比高、未消费占比高、来源过于集中、入会短周期会员运营建议等。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 基础指标失败 | 可以继续输出来源、消费频次、入会时长和星座，但必须标注缺少核心汇总。 |
| 返回空对象或空列表 | 说明当前条件无数据，提示检查时间、会员来源、门店或权限。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
