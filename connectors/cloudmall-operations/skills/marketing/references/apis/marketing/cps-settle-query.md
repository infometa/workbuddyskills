# 营销域 — CPS 结算明细查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-settle-flow.md`
> **结算状态（明细维度，整数，与活动维度的字符串结算状态是两套体系）**：`settleStatus` 0=待结算 / 1=已结算；`awardStatus` 0=未发奖 / 1=已发奖。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-settle.search 活动结算明细分页（分销员×活动汇总） · cps-settle.global-search 全局结算明细分页（不限活动） · cps.settlement.export-by-activity 按活动结算明细异步导出（返回任务 ID） · cps.settlement.export 全局结算明细异步导出（返回任务 ID）
> 写操作见 `cps-settle-action.md`。

---

## ⛔ 未开放

- **活动数据明细（订单维度）**：服务端未提供该查询端点（前端存在调用但后端无对应实现，调用必然失败）。订单维度数据请走交易域订单查询能力。

---

## ✅ 活动结算明细分页 — `ops.marketing.cps-settle.search`

- **说明**：查询指定活动的预估结算明细（每行=一个分销员在该活动下的结算汇总）。排序：已结算(settleStatus=1)按结算时间倒序，否则按活动 ID 倒序。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID（16 位数字串，路径参数） |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| cpsUid | String | 否 | 分销员 UID（精确） |
| cpsType | String | 否 | 分销员类型（数字字符串）：`'1'` 员工 / `'2'` 普通用户 |
| settleStatus | Integer | 否 | 结算状态：0 待结算 / 1 已结算 |
| settleStartTime | String | 否 | 结算时间下限（yyyy-MM-dd HH:mm:ss，语义上仅已结算数据有结算时间） |
| settleEndTime | String | 否 | 结算时间上限（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].activityId`（→ 活动详情/手动结算）、`records[].cpsUid`（分销员维度追踪）
- **枚举字段**：`settleStatus`（0/1）、`awardStatus`（0/1）、`cpsType`（'1' 员工 / '2' 普通用户）
- **格式敏感字段**：`commissionAmount`（预估佣金，**元**）、`settledAmount`（已结算金额，**元**）、`settleTime`/`createTime`（yyyy-MM-dd HH:mm:ss）、`id`/`cpsGroupId`（Long→string）、`cpsGroupInfo`（分组信息 JSON 字符串，内部结构：`{"id": <分组ID>, "name": <分组名称>}`——`id` 为 Long→string；取分组名称直接用已解析的 `groupName` 字段即可）
- **脱敏字段**：`phone`（分销员手机号，**未脱敏明文**，来自用户中心；展示给用户时自行打码）

### 调用示例

```json
{"capability":"ops.marketing.cps-settle.search","input":{"activityId":"7017890752010234","pageNum":1,"pageSize":20,"settleStatus":0},"summary":"查看该活动的待结算明细"}
```

---

## ✅ 全局结算明细分页 — `ops.marketing.cps-settle.global-search`

- **说明**：不限定活动的全局结算明细查询（数据统计场景），筛选条件与活动维度查询共用一套结构，`activityId` 变为可选。手机号/分组名/活动名均先反查再过滤——反查无命中直接返回空页。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| activityId | String | 否 | 活动业务 ID（精确，可选） |
| activityName | String | 否 | 活动名称（模糊，≤100 字） |
| cpsUid | String | 否 | 分销员 UID（精确） |
| phone | String | 否 | 分销员手机号（精确，反查会员后过滤） |
| cpsType | String | 否 | 分销员类型（数字字符串）：`'1'` 员工 / `'2'` 普通用户 |
| groupName | String | 否 | 分销员分组名称（模糊，≤100 字，反查分组后过滤） |
| cpsGroupId | Long | 否 | 分销员分组 ID（精确） |
| settleStatus | Integer | 否 | 结算状态：0 待结算 / 1 已结算 |
| settleStartTime | String | 否 | 结算时间下限（yyyy-MM-dd HH:mm:ss） |
| settleEndTime | String | 否 | 结算时间上限（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

与「活动结算明细分页」完全一致（含 `phone` 明文警示）。

### 调用示例

```json
{"capability":"ops.marketing.cps-settle.global-search","input":{"pageNum":1,"pageSize":20,"activityName":"推新","settleStatus":1,"settleStartTime":"2026-08-01 00:00:00","settleEndTime":"2026-08-31 23:59:59"},"summary":"查询8月已结算的分销佣金明细"}
```

---

## ✅ 按活动导出结算明细 — `ops.marketing.cps.settlement.export-by-activity`

- **说明**：导出**指定活动**的预估结算明细（异步）。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选条件结构同 `ops.marketing.cps-settle.search`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动 ID（路径参数） |
| （筛选条件） | object | 否 | body 可选，结构同活动结算明细分页查询 |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.cps.settlement.export-by-activity","input":{"activityId":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"导出该活动的结算明细"}
```

---

## ✅ 全局导出结算明细 — `ops.marketing.cps.settlement.export`

- **说明**：**不限定活动**的全局结算明细导出（异步）。返回**导出任务 ID**，轮询与下载方式同上。筛选条件结构同 `ops.marketing.cps-settle.global-search`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | body 可选，结构同全局结算明细分页查询 |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID

### 调用示例

```json
{"capability":"ops.marketing.cps.settlement.export","input":{"pageNum":1,"pageSize":20},"summary":"全局导出本期结算明细"}
```

---
