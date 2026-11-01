# 交易域 — 预约写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-appointment.md`
> **先读现值**：处置前用 `appointment-query.md` 的 search 取得唯一 id、状态与时间（没有预约详情能力，不编造 detail 调用）；全局配置保存前 config.get 读现值。
> 所有 ID 均为十进制字符串；实际到访和爽约须用户确认，不从当前时间自动推定；不得重复处置终态记录。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 appointment.confirm 🔴 · appointment.reject 🔴 · appointment.confirm-visit 🔴 · appointment.no-show 🔴 · appointment.config.update 🔴

---

## ✅ 确认预约 — ops.trade.appointment.confirm

用途：确认一张待处理预约（🔴）。仅输入十进制字符串 `id`；必须先查到真实服务时间、门店和当前阶段。

| 字段 | 类型 | 必填、默认与约束 | 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 预约检索中逐字核对编号后取得的 id |

必须明确确认；唯一允许的当前状态为 `pending_confirm`。事实条件：用户明确批准该门店、服务、日期和时段。返回无业务数据；执行后用原 `appointmentNo` 检索，逐字核对编号及 `id`，仅 `status=pending_visit` 可报告完成。其他现态或并发状态冲突先回读，不改调用对象、不重复提交。来源：`AppointmentStatus.canTransit`、`AppointmentRecordServiceImpl` 的状态比较更新。

```json
{
  "capability": "ops.trade.appointment.confirm",
  "input": {
    "id": "8000000000000000001"
  },
  "summary": "确认预约"
}
```

---

## ✅ 拒绝预约 — ops.trade.appointment.reject

用途：拒绝一张预约（🔴）。`id` 和非空 `reason` 均必填；拒绝原因只能来自用户明确说明，不能编造。

| 字段 | 类型 | 必填、默认与约束 | 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 预约检索中逐字核对编号后取得的 id |
| reason | string | 必填，非空白；未声明长度上限 | 用户给出的拒绝原因 |

必须明确确认；唯一允许的当前状态为 `pending_confirm`。事实条件：用户明确拒绝及真实原因。返回无业务数据；执行后用原 `appointmentNo` 检索，逐字核对编号及 `id`，仅 `status=rejected` 可报告完成。其他现态或并发状态冲突先回读，不改调用对象、不重复提交。来源：`AppointmentStatus.canTransit`、`AppointmentRecordServiceImpl` 的状态比较更新、`AppointmentRejectRequest`。

```json
{
  "capability": "ops.trade.appointment.reject",
  "input": {
    "id": "8000000000000000001",
    "reason": "预约时段已满"
  },
  "summary": "拒绝预约"
}
```

---

## ✅ 确认到访 — ops.trade.appointment.confirm-visit

用途：记录客户已实际到访（🔴）。仅输入 `id`；必须已有真实到访事实。

| 字段 | 类型 | 必填、默认与约束 | 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 预约检索中逐字核对编号后取得的 id |

必须明确确认；唯一允许的当前状态为 `pending_visit`。事实条件：客户已经实际到店。返回无业务数据；执行后用原 `appointmentNo` 检索，逐字核对编号及 `id`，仅 `status=visited` 可报告完成。其他现态或并发状态冲突先回读，不改调用对象、不重复提交。来源：`AppointmentStatus.canTransit`、`AppointmentRecordServiceImpl` 的状态比较更新。

```json
{
  "capability": "ops.trade.appointment.confirm-visit",
  "input": {
    "id": "8000000000000000001"
  },
  "summary": "确认到访"
}
```

---

## ✅ 标记爽约 — ops.trade.appointment.no-show

用途：记录客户未按约到访（🔴）。仅输入 `id`；必须已有真实未到访事实，不能因未联系上客户而推断爽约。

| 字段 | 类型 | 必填、默认与约束 | 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 预约检索中逐字核对编号后取得的 id |

必须明确确认；唯一允许的当前状态为 `pending_visit`。事实条件：客户确实未按约到店。返回无业务数据；执行后用原 `appointmentNo` 检索，逐字核对编号及 `id`，仅 `status=no_show` 可报告完成。其他现态或并发状态冲突先回读，不改调用对象、不重复提交。来源：`AppointmentStatus.canTransit`、`AppointmentRecordServiceImpl` 的状态比较更新。

```json
{
  "capability": "ops.trade.appointment.no-show",
  "input": {
    "id": "8000000000000000001"
  },
  "summary": "标记爽约"
}
```

---

## ✅ 保存预约全局配置 — ops.trade.appointment.config.update

用途：保存预约全局配置（🔴）。影响全租户预约行为（客户预约校验与提醒节奏）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| enableDuplicateCheck | 布尔值 | 否 | 防重复预约（同一用户同一服务同一时段） |
| cancelLimitPerMonth | 整数 | 否 | 每月取消次数限制 |
| maxActivePerUser | 整数 | 否 | 单用户活跃预约上限 |
| autoCompleteTimeoutHours | 整数 | 否 | 超时自动完成时长（小时） |
| reminderHoursBefore | 整数 | 否，1~48 | 提醒提前时长（小时） |
| enableConcurrencyControl | 布尔值 | 否 | 时段人数上限校验开关 |

来源：`AppointmentGlobalConfigSaveRequest`（仅 `reminderHoursBefore` 有范围校验，其余字段无 Bean Validation——传值靠语义正确性）。**保存为非 null 字段级合并**：未传字段保留旧值（与售后配置的全量覆盖语义不同，不能套错模式）；推荐先 config.get 读现值、复述变更后提交完整目标状态，回读核对。

```json
{
  "capability": "ops.trade.appointment.config.update",
  "input": {
    "enableDuplicateCheck": true,
    "cancelLimitPerMonth": 3,
    "maxActivePerUser": 5,
    "autoCompleteTimeoutHours": 72,
    "reminderHoursBefore": 2,
    "enableConcurrencyControl": true
  },
  "summary": "保存预约全局配置"
}
```
