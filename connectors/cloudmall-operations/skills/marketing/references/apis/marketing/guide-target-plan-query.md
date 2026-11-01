# 营销域 — 导购目标计划查询契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 目标计划 = 考核周期容器（仅周期信息），导购目标行独立管理（新增空白行 → 填值/导入/按上期填充）。
> 周期模型：`periodType` 月度（`period` = 1..12 月份）/ 季度（`period` = 1..4 季度）；起止日期由周期自动计算，创建/编辑时按当前日期快照初始状态，每日定时任务自动流转。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：guide-target-plan.search 目标计划分页（周期/状态筛选） · guide-target-plan.detail 目标计划详情（不含目标行） · guide-target-plan.targets 导购目标分页（门店/导购筛选） · guide-target-plan.store-groups 目标门店分组汇总 · guide-target-plan.periods 可选周期列表（上期参照） · guide-target-plan.target-summary 导购目标汇总（目标合计/人数）
> 写操作见 `guide-target-plan-action.md`。

---

## ⛔ 未开放端点

| 端点能力 | 不开放原因 |
|---------|-----------|
| 下载导入模板（按计划生成 Excel 模板，二进制流响应） | 二进制文件下载，超出工具返回契约；模板列结构以运营端页面下载为准 |

---

## ✅ 目标计划分页 — `ops.marketing.guide-target-plan.search`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| periodType | String | 否 | 周期类型筛选：`monthly` 月度 / `quarterly` 季度 |
| year | Integer | 否 | 年度筛选，如 2026 |
| status | String | 否 | 状态筛选：`not_started` 未开始 / `in_progress` 进行中 / `ended` 已结束 |

### 出参（分页，原始数据）

- **枚举字段**：`periodType`（monthly/quarterly）、`status`（not_started/in_progress/ended）
- **格式敏感字段**：`startDate`/`endDate`（考核起止日期，yyyy-MM-dd）；`totalSalesTarget`（销售额目标合计，元）；`totalCustomerTarget`（客户目标合计，整数）；`year`/`period`（整数）
- 其余展示字段：`periodLabel`（如「2026年4月」「2026年Q2」）、`guideCount`、`storeCount`。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.search","input":{"pageNum":1,"pageSize":20,"periodType":"monthly","year":2026,"status":"in_progress"},"summary":"查看2026年进行中的月度目标计划"}
```

---

## ✅ 目标计划详情 — `ops.marketing.guide-target-plan.detail`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 目标计划 ID（本文各能力中的 planId 同义） |

### 出参（原始数据）

- 仅计划基本信息（**不含**导购目标行——用 targets 能力查询）
- **枚举字段**：`periodType`、`status`
- **格式敏感字段**：`startDate`/`endDate`（yyyy-MM-dd）

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.detail","input":{"id":"5100000000000000001"},"summary":"查看目标计划基本信息"}
```

---

## ✅ 导购目标分页 — `ops.marketing.guide-target-plan.targets`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| storeIds | String[] | 否 | 门店 ID 批量筛选 |
| guideIds | String[] | 否 | 导购 ID 批量筛选 |

### 出参（分页，原始数据）

- **关键字段来源**：`guideId`（→ 更新/删除单条导购目标）、`storeId`
- **格式敏感字段**：`salesTarget`/`salesActual`/`lastSales`（销售额，元；`lastSales` 为上期实际）、`customerTarget`/`customerActual`/`lastCustomers`（客户数，整数）
- 每行含 `storeName`/`guideName`；目标值为空表示尚未设定（null 字段不出现在响应中）。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.targets","input":{"planId":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"分页查看计划下导购目标明细"}
```

---

## ✅ 门店分组分页 — `ops.marketing.guide-target-plan.store-groups`

- **说明**：按门店维度聚合该计划的导购目标与实际达成。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| storeIds | String[] | 否 | 门店 ID 批量筛选 |
| guideIds | String[] | 否 | 导购 ID 批量筛选 |

### 出参（分页，原始数据）

- **关键字段来源**：`storeId`
- **格式敏感字段**：`salesTargetSum`/`salesActualSum`/`lastPeriodSalesActualSum`（销售额合计，元）；`customerTargetSum`/`customerActualSum`/`lastPeriodCustomerActualSum`（客户数合计，整数）
- 其余展示字段：`storeName`、`guideCount`。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.store-groups","input":{"planId":"5100000000000000001","pageNum":1,"pageSize":20},"summary":"按门店查看目标与达成汇总"}
```

---

## ✅ 可选周期列表 — `ops.marketing.guide-target-plan.periods`

- **说明**：返回当前租户全部目标计划的周期选项（年/期倒序），供筛选器与「上期」参照。

### 入参

- 无（分页/筛选参数均不需要）。

### 出参（数组，原始数据）

- **关键字段来源**：`planId`（→ 各计划内能力）
- **枚举字段**：`periodType`、`status`
- 其余展示字段：`periodLabel`。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.periods","input":{},"summary":"获取目标计划周期选项列表"}
```

---

## ✅ 导购目标汇总 — `ops.marketing.guide-target-plan.target-summary`

- **说明**：对当前筛选条件下的目标行做汇总（与 targets 列表同一数据口径）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| storeId | String | 否 | 门店 ID 筛选 |
| keyword | String | 否 | 导购姓名关键词（模糊匹配） |

### 出参（原始数据）

- **格式敏感字段**：`totalSalesTarget`（销售额目标合计，元）；`guideCount`/`storeCount`/`totalCustomerTarget`（整数）

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.target-summary","input":{"planId":"5100000000000000001"},"summary":"汇总查看计划下目标设定情况"}
```

---
