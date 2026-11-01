---
name: member-campaign-analysis
description: >-
  全面分析会员营销活动效果，支持按时间、活动名称和活动创建人，查询发券量、用券量、收益等活动明细和核销情况。
  适用于用户问“最近营销活动效果怎么样”“活动收益和用券情况如何”“有哪些活动值得关注”。
  只使用本文固定命令；不使用近似指标或其它业务概念替代。
  当用户的本业务问题提到“整个集团”“集团视角”“不区分门店”或未指定门店时，仍按当前账号/当前上下文默认权限范围执行，不得仅因未指定门店而拒绝或改用其它 Skill。
version: "1.0.174"
author: shanglong-skill-creator
---

# 活动分析业务 Skill

## Skill 路由（WorkBuddy）

本连接器当前 **仅** 提供本 Skill：营销活动效果 / ROI / 发券用券核销 / 活动列表与状态数量。

- Agent 元数据见 [`agents/claw.yaml`](agents/claw.yaml)、[`agents/openai.yaml`](agents/openai.yaml)。
- WorkBuddy 按本 Skill 的 `description` + `agents/*` 选择；包内无其它业务 Skill。
- 仓库 OpenClaw Agent（`generated/agents/agent-group|agent-store`）挂的是 L1 `marketing_crm`，与本 WorkBuddy Skill **不是同一加载链路**，不会自动互跳。

---

## ⚠️ WorkBuddy 运行兼容（强制）

> 完整细则：[rules/workbuddy-runtime.md](rules/workbuddy-runtime.md)

### CLI 可执行路径

所有查询通过连接器安装的 `sl-sea` 二进制和当前 AI Gateway 执行。先读取
[`rules/workbuddy-runtime.md`](rules/workbuddy-runtime.md) 定位绝对路径；正文中的
`<sl-sea-absolute>` 是占位符，执行前替换为实际路径，不使用 PATH 或开发版入口。

### 执行边界与隐私

- 禁止 `--verbose` / `-v`、`--header`、`--envPath`、`--body-file`，也不要使用旧的 token 查看命令。
- 禁止动态 DataCube、可变任务 ID、`title/where`、直连 MCP/数据库。
- 不输出 token / session / cookie / 密钥 / 认证参数；错误业务化，不贴原始堆栈。
- 不主动执行发券、触达、导出明细、修改活动。

### 积分优先路径

WorkBuddy 按轮次/工具调用计费。槽位齐全时：解析时间参数 → 执行核心指标（1 次）→ 列表（1 次）；类型选项按需。禁止探索性找 path、扫无关文档。

---

## 关键执行规范

1. 本 Skill 只能使用下方列出的固定 `<sl-sea-absolute> marketing_crm` CLI。
2. 不得搜索命令列表、不得执行 help、不得尝试其它接口路径，不得临场改写接口口径。
3. 固定接口模块失败、返回空对象/空列表、指标为 0 必须分开说明；失败不能写成 0。
4. 认证业务查询模块只有 3 个：活动核心指标、活动分析列表、按需查询的活动类型选项。
5. 不主动执行发券、触达、导出明细、修改活动等操作。
6. 不输出 token、session、cookie、密钥、认证参数；涉及活动 ID、创建人等明细时只展示分析必要字段。
7. 本组固定接口没有门店筛选入参；用户问门店范围时，只能说明按当前 Gateway 账号授权范围执行，不能自行添加门店参数。

## 用途

用于分析指定用券时间、发券时间、活动时间、创建时间、活动名称、活动状态、活动类型和创建人筛选条件下的营销活动表现，输出活动数量、发券数量、收益、用券数量、券核销率和活动列表观察。

## 时间与参数

用户只需要提供当前统计周期。不要向用户额外索要上一周期；`preBeginDate/preEndDate` 按当前周期等长前移。

```text
rangeDays = (Date.parse(endDate) - Date.parse(beginDate) + 1000) / 1000 / 60 / 60 / 24
preBeginDate = beginDate - rangeDays days
preEndDate = endDate - rangeDays days
```

默认时间：最近 7 个完整自然日，结束于昨天。

| 参数 | 规则 |
|---|---|
| `beginDate` | 用户给自然日时展开为 `yyyy-MM-dd 00:00:00`。 |
| `endDate` | 用户给自然日时展开为 `yyyy-MM-dd 23:59:59`。 |
| `preBeginDate/preEndDate` | 不要求用户填写；按上述公式自动计算。 |
| `campaignName` | 活动名称模糊查询；未指定传 `null`。 |
| `creatorName` | 创建人；未指定传 `null`。 |
| `campaignStates` | 活动状态 ID 数组；未指定传 `[]`。 |
| `campaignTypes` | 活动类型 ID 数组；未指定传 `[]`。 |
| `sendBeginDate/sendEndDate` | 发券时间；自然日展开为整天，未指定传空字符串。 |
| `createBeginDate/createEndDate` | 创建时间；自然日展开为整天，未指定传空字符串。 |
| `campaignBeginDate/campaignEndDate` | 活动时间；自然日展开为整天，未指定传空字符串。 |
| `page/size` | 列表默认 `page=1,size=10`；用户要求更多时再提高，不要无边界拉全量。 |

活动状态中文到 ID 的固定映射：

| 中文状态 | ID |
|---|---|
| 未开始 | `0` |
| 进行中 | `1` |
| 系统结束 | `2` |
| 人工结束 | `3` |
| 审核中 | `4` |
| 已驳回 | `5` |
| 第三方审核中 | `6` |
| 第三方已驳回 | `7` |

通用 `--params` 基础形态：

```json
{
  "beginDate": "<beginDate>",
  "endDate": "<endDate>",
  "preBeginDate": "<preBeginDate>",
  "preEndDate": "<preEndDate>",
  "campaignName": null,
  "creatorName": null,
  "campaignStates": [],
  "campaignTypes": [],
  "sendBeginDate": "",
  "sendEndDate": "",
  "createBeginDate": "",
  "createEndDate": "",
  "campaignBeginDate": "",
  "campaignEndDate": ""
}
```

## 固定接口模块

> 每条命令都必须通过 `<sl-sea-absolute>` 绝对路径执行；不读取认证文件或产品凭据。

### 1. 活动核心指标固定查询

用途：查询活动未开始、进行中、已结束数量，以及发券数量、活动收益、用券数量和券核销率。

```text
<sl-sea-absolute> marketing_crm get-campaign-data --skill-ref member-campaign-analysis@1.0.174 --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","campaignName":null,"creatorName":null,"campaignStates":[],"campaignTypes":[],"sendBeginDate":"","sendEndDate":"","createBeginDate":"","createEndDate":"","campaignBeginDate":"","campaignEndDate":""}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `notStartCount` | 活动未开始数量。 |
| `proceedingCount` | 活动进行数量。 |
| `systemEndCount` | 活动已结束数量。 |
| `sendCouponCount` | 发券数量。 |
| `incomeMoney` | 活动收益金额。 |
| `useCouponCount` | 用券数量。 |
| `useCouponRate` | 券核销率。 |
| `*FloatRangeValue` | 较上一周期变化值。 |
| `*FloatRangeType` | 较上一周期变化方向，`2` 代表下降，其它按接口原义解释。 |

结果粒度：当前筛选条件下的汇总指标。返回 0 是合法结果，不代表接口失败。空对象表示当前条件无匹配数据或当前权限范围无数据，需要如实说明。

### 2. 活动分析列表固定查询

用途：分页查询活动列表，返回活动名称、状态、收益、用券金额、发券数、用券数和核销率。

```text
<sl-sea-absolute> marketing_crm get-campaign-analysis --skill-ref member-campaign-analysis@1.0.174 --params '{"beginDate":"<beginDate>","endDate":"<endDate>","page":1,"size":10}' --format json
```

输出字段：

| 字段 | 说明 |
|---|---|
| `total` | 总条数。 |
| `list[].campaignName` | 活动名称。 |
| `list[].campaignStatus` | 活动状态。 |
| `list[].incomeMoney` | 收益金额。 |
| `list[].useCouponMoney` | 用券金额。 |
| `list[].sendCouponCount` | 发券数。 |
| `list[].useCouponCount` | 用券数。 |
| `list[].useCouponRate` | 核销率。 |

结果粒度：活动列表分页。`total=0,list=[]` 表示当前筛选条件下无匹配活动，是合法空结果。当前页数据不能当作全量排行；需要更深分页时必须说明。

### 3. 活动类型选项固定查询

只有用户要求查看可选活动类型，或用户给了活动类型 ID 需要校验时执行。

```text
<sl-sea-absolute> marketing_crm get-marketing-type-list --skill-ref member-campaign-analysis@1.0.174 --format json
```

固定过滤规则：

1. 遍历接口返回的全部顶层分类；顶层分类 ID 不作为筛选条件。
2. 保留子活动类型 `id in [2, 17, 19, 20, 21, 42, 43, 44, 45, 47]`。
3. 将保留项按子活动类型 ID 去重，整理为可用的 `campaignTypeId` 列表；只使用接口实际返回的选项。

输出字段为顶层分类的 `id`、`name`，以及子活动类型的 `id`、`name`、`permissionCode`、`status`。如果用户只给了模糊中文活动类型名，而当前上下文无法和返回 key 做确定映射，应明确说明无法稳定解析，不要硬猜。

## 执行顺序

1. 标准化用券时间、发券时间、活动时间、创建时间、活动名称、活动状态、活动类型、创建人和分页参数。
2. 计算上一周期 `preBeginDate/preEndDate`。
3. 如果用户要求查看可选活动类型，或给了活动类型 ID 需要校验，执行活动类型选项固定查询。
4. 执行活动核心指标固定查询。
5. 执行活动分析列表固定查询，默认 `page=1,size=10`。

用户只问单个模块时，只执行对应固定查询，不为了补全报告追加其它查询。

## 合并与解释规则

| 指标 | 规则 |
|---|---|
| 数据指标 | 使用活动核心指标固定查询返回的 7 个核心字段。 |
| 较上一周期 | 使用 `*FloatRangeValue` 和 `*FloatRangeType`；当 `FloatRangeType=2` 时按下降解释。 |
| 活动列表总数 | 使用活动分析列表固定查询的 `total`。 |
| 活动排行/亮点 | 只从当前返回页中提取，不伪装成全量排行。 |
| 活动状态解释 | 列表中 `campaignStatus` 以接口返回 ID 为准，不自行发明新展示文案。 |
| 核销率 | 直接使用接口返回的 `useCouponRate`，不重复本地计算。 |
| 本地计算 | 只允许做 Top 项筛选、百分比格式化、变化方向解释和简单摘要，不得补造收益、发券或用券口径。 |

## 输出报告结构

1. 筛选条件：用券时间、上一周期、发券时间、活动时间、创建时间、活动名称、活动状态、活动类型、创建人、分页。
2. 执行摘要：执行了哪些固定接口模块，哪些成功、失败或为空。
3. 数据指标：未开始、进行中、已结束、发券数量、活动收益、用券数量、券核销率，以及较上一周期变化。
4. 活动列表观察：总条数、当前页条数、活动状态分布、收益/用券/发券为 0 或非 0 的代表活动。
5. 口径提示：当前页样本不等于全量排行；活动类型只能按固定 ID/key 规则稳定过滤。

## 失败策略

| 情况 | 处理 |
|---|---|
| 单个固定接口模块失败 | 说明失败模块和受影响指标，继续分析其它已成功模块，不补造该模块数字；只有用户明确要求排查执行问题时才展示底层命令和错误摘要。 |
| 核心指标失败 | 可以继续输出列表观察，但必须标注缺少汇总指标。 |
| 返回空对象或空列表 | 说明当前条件无数据，提示检查时间、活动状态、活动类型、创建人或权限范围。 |
| 字段缺失 | 标注缺失字段，不用近似字段替代。 |
| 活动类型无法稳定映射 | 明确说明当前 CLI 只稳定支持活动类型 ID 和原始 key，不猜中文类型名。 |
| 登录或解密失败 | 说明认证或解密失败导致查询不可用，不输出认证信息；只有用户明确要求排查执行问题时，才展示 CLI 错误摘要。 |
