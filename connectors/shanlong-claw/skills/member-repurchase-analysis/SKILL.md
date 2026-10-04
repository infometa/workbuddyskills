---
name: member-repurchase-analysis
description: 仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据。会员业务 Skill：使用固定复购分析接口 CLI 输出复购核心指标、增长趋势、群体结构、次数分布和排行。适用于用户问“复购表现怎么样”“复购率趋势如何”“消费 2 次及以上会员占比多少”“复购会员排行如何”。只使用本文固定命令和固定门店编码获取 CLI；不使用近似指标或其它业务概念替代。当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
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

# 复购分析业务 Skill

## 关键执行规范

1. 本 Skill 只能使用下方列出的固定 `<sl-sea-absolute> general` CLI 和固定门店编码获取 CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试其它接口路径，不得临场改写接口口径。
3. 5 个复购接口必须统一使用 `--params '<完整 JSON 对象>' --format json` 调用，不得把 JSON 字段拆成多个 `--字段名` flags。
4. `shopFilterTypeValue` 必须保持 JSON 数组类型；未指定筛选时传 `[]`，指定筛选时传 `["<筛选值>"]`。
5. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
6. 不主动执行新增、修改、发券、触达、导出敏感名单等操作。
7. 不输出 token、session、cookie、密钥、认证参数；会员姓名、手机号、会员编号、订单号等敏感信息默认脱敏。

## 用途

用于分析指定统计周期和筛选范围内的复购表现，回答消费会员数、消费 1 次会员数、消费 2 次及以上会员数、复购率走势、新老会员结构、复购次数分布和复购排行。

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

示例：当前周期为 `2026-05-12 00:00:00` 到 `2026-05-18 23:59:59` 时，`rangeDays=7`，上一周期为 `2026-05-05 00:00:00` 到 `2026-05-11 23:59:59`。

| 参数 | 规则 |
|---|---|
| `beginDate` | 用户指定开始日转成 `yyyy-MM-dd 00:00:00`。 |
| `endDate` | 用户指定结束日按自然日包含，转成 `yyyy-MM-dd 23:59:59`。 |
| 自然语言时间 | 如“近一周”“本月”“上周”先解析为当前统计周期，再统一生成 `beginDate/endDate`。 |
| 默认时间 | 用户未指定时，默认最近 7 个完整自然日。 |
| `preBeginDate/preEndDate` | 不要求用户填写，按当前周期自动计算。 |
| `dateType` | 默认 `1` 按天；用户问月趋势或按月时用 `2`。 |
| `repurchaseMode` | 默认 `1` 按实际消费次数；用户明确说按市别汇总消费次数时用 `2`。 |
| `shopFilterType` | 默认 `1` 门店筛选。 |
| `shopFilterTypeValue` | 未指定门店时传 `[]`；指定门店时使用门店查询 CLI 返回的 `omShopCode`。 |
| `dimensionType` | 复购排行默认 `2` 城市；用户问门店/品牌时分别用 `1`/`3`。 |
| `page/size` | 默认 `page=1,size=10`；用户要求更多时再提高，不要无边界拉全量。 |

通用 `--params` 基础形态：

```json
{
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>",
  "dateType": 1,
  "shopFilterType": 1,
  "shopFilterTypeValue": [],
  "repurchaseMode": 1
}
```

## 固定接口模块

### 1. 复购核心指标固定查询

用途：查询消费会员数、消费 1 次会员数、消费 2 次及以上会员数及其较上一周期变化。

```text
<sl-sea-absolute> general get-data-indicators --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `consumeMemberCount` | 当前周期消费会员数，单位人。 |
| `consumeMemberCountFloatRangeValue` / `consumeMemberCountFloatRangeType` | 消费会员数较上一周期变化比例和方向。 |
| `onceConsumeMemberCount` | 当前周期消费 1 次会员数，单位人。 |
| `onceConsumeMemberRatio` | 消费 1 次会员占消费会员数比例。 |
| `onceConsumeMemberCountFloatRangeValue` / `onceConsumeMemberCountFloatRangeType` | 消费 1 次会员数较上一周期变化比例和方向。 |
| `twiceConsumeMemberCount` | 当前周期消费 2 次及以上会员数，单位人。 |
| `twiceConsumeMemberRatio` | 消费 2 次及以上会员占消费会员数比例。 |
| `twiceConsumeMemberCountFloatRangeValue` / `twiceConsumeMemberCountFloatRangeType` | 消费 2 次及以上会员数较上一周期变化比例和方向。 |

### 2. 复购增长趋势固定查询

用途：查询周期内消费 1 次会员、消费 2 次及以上会员和复购率趋势。

```text
<sl-sea-absolute> general get-re-purchase-growth-trend --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList[]` | 趋势时间点列表。 |
| `onceConsumeMemberCountList[]` | 各时间点消费 1 次会员数。 |
| `twiceConsumeMemberCountList[]` | 各时间点消费 2 次及以上会员数。 |
| `repurchaseRatioList[]` | 各时间点复购率。 |

### 3. 复购群体趋势固定查询

用途：查询复购相关会员中新会员、老会员和总人数结构。

```text
<sl-sea-absolute> general get-re-purchase-group-trend --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `dateList[]` | 趋势时间点列表。 |
| `totalMemberCount[]` | 各时间点复购相关会员总人数。 |
| `newMemberCount[]` | 各时间点新会员人数。 |
| `oldMemberCount[]` | 各时间点老会员人数。 |

### 4. 复购次数分布固定查询

用途：查询不同复购次数区间的会员数分布。

```text
<sl-sea-absolute> general get-repurchase-frequency-data --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `frequencyList[]` | 复购次数区间标签。 |
| `countList[]` | 各复购次数区间对应会员数。 |

### 5. 复购会员排行固定查询

用途：按城市、门店或品牌维度查询复购会员排行。

```text
<sl-sea-absolute> general get-ranking-repurchase-members --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1,"dimensionType":2,"page":1,"size":10}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `total` | 排行总条数。 |
| `list[]` | 排行明细列表。 |
| `list[].repurchaseRatio` | 对应维度的复购率。 |
| `list[].consumeMemberCount` | 对应维度的消费会员数。 |
| `list[].twiceConsumeMemberCount` | 对应维度消费 2 次及以上会员数。 |

排行维度说明：`dimensionType=1` 门店，`dimensionType=2` 城市，`dimensionType=3` 品牌。不同排行维度不能直接混排比较。

## 执行顺序

1. 标准化时间、时间粒度、门店筛选、复购模式、排行维度和分页参数，计算上一周期。
2. 执行复购核心指标固定查询。
3. 执行复购增长趋势固定查询。
4. 执行复购群体趋势固定查询。
5. 执行复购次数分布固定查询。
6. 执行复购会员排行固定查询，默认城市维度、第一页 10 条。

用户只问单个模块时，只执行对应固定查询，不为了补全报告追加其它查询。

## 合并与解释规则

| 指标 | 规则 |
|---|---|
| 消费会员数 | 使用核心指标接口 `consumeMemberCount`。 |
| 消费 1 次会员数 | 使用 `onceConsumeMemberCount`；占比用 `onceConsumeMemberRatio`。 |
| 消费 2 次及以上会员数 | 使用 `twiceConsumeMemberCount`；占比用 `twiceConsumeMemberRatio`。 |
| 较上一周期 | 使用对应 `*FloatRangeValue` 与 `*FloatRangeType`；变化方向按接口返回解释。 |
| 复购率 | 优先使用增长趋势接口的 `repurchaseRatioList` 或排行接口的 `repurchaseRatio`。 |
| 复购群体 | 使用 `totalMemberCount/newMemberCount/oldMemberCount`，不要把新老会员相加不等于总数时强行修正。 |
| 复购次数分布 | 使用 `frequencyList/countList`，两个数组长度不一致时停止解释该图。 |
| 复购排行 | 城市、门店、品牌只能在同一维度内比较。 |
| 本地计算 | 只允许做展示层百分比格式化、Top 项筛选、简单差值和异常提示；不得发明接口未返回的复购周期、RFM 分层或营销建议。 |

## 输出报告结构

1. 筛选条件：时间、上一周期、时间粒度、复购模式、门店筛选、排行维度、分页。
2. 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
3. 核心指标：消费会员数、消费 1 次会员数、消费 2 次及以上会员数、占比和较上一周期变化。
4. 复购趋势：按天/月的消费 1 次会员、消费 2 次及以上会员、复购率高低点和异常波动。
5. 群体结构：新会员、老会员、总人数占比关系。
6. 次数分布：主要复购次数区间和人数集中情况。
7. 复购排行：城市/门店/品牌 Top 项、复购率、消费会员数和消费 2 次及以上会员数。
8. 口径提示：合法 0 值、样本少、分母为 0、排行维度切换和接口缺失字段。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 核心指标失败 | 可以继续输出趋势和排行，但必须标注缺少核心汇总。 |
| 返回空对象/空列表 | 说明当前条件无数据，提示检查时间、复购模式、门店筛选或权限。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
