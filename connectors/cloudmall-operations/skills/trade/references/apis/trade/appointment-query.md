# 交易域 — 预约查询契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；预约处置与全局配置写操作见 `appointment-action.md`；运营流程：`references/flows/trade-appointment.md`
> 所有 ID 均为十进制字符串；手机号已脱敏，不可反推。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 appointment.search · appointment.tab-count · appointment.calendar · appointment.dashboard.metrics · appointment.config.get · appointment.export · appointment.reminder-log.search · appointment.reminder-log.detail

---

## ✅ 预约搜索 — ops.trade.appointment.search

用途：定位待确认、待到访或异常的预约。可用 `keyword`、`date`、`status`、`storeId`、`serviceId`、`memberName`、`memberPhone`、`startDate`、`endDate`、`appointmentNo`；日期必须严格为 `yyyy-MM-dd`；写操作前从结果取得 id 和现态。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| pageNum | integer | 可选，默认 1，最小 1 | 页码 |
| pageSize | integer | 可选，默认 20，1～100 | 每页条数 |
| keyword | string | 可选 | 姓名或手机号模糊匹配，两者为或 |
| date | string | 可选，yyyy-MM-dd | 单日预约日期 |
| status | string | 可选，见 `trade-enums.md` 预约状态表（小写枚举） | 预约现态 |
| storeId | string | 可选，十进制 ID | 门店精确匹配 |
| serviceId | string | 可选，十进制 ID | 到店服务精确匹配 |
| memberName | string | 可选 | 姓名模糊匹配 |
| memberPhone | string | 可选 | 手机号模糊匹配 |
| startDate | string | 可选，yyyy-MM-dd | 预约日期下界，含当天 |
| endDate | string | 可选，yyyy-MM-dd | 预约日期上界，含当天 |
| appointmentNo | string | 可选 | 预约编号模糊匹配，写前须逐字比对 |

所有筛选叠加为且；`date` 与区间同时给出时取交集，不会覆盖。状态严格小写（见 `trade-enums.md` 预约状态）。`AppointmentRecordVO` 记录含 `id/appointmentNo/memberName/memberPhone/serviceName/serviceItemName/storeName/appointmentDate/timeSlot/status/statusDesc/confirmMode/remark/autoCompleted/createdTime`。写动作使用 `id`，确认时用服务、门店、日期及时段区分同名客户。来源：`AppointmentPageQuery`、`AppointmentRecordServiceImpl.page`、`AppointmentStatus.canTransit`。

```json
{
  "capability": "ops.trade.appointment.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20,
    "date": "2026-09-09"
  },
  "summary": "查询预约单"
}
```

---

## ✅ 预约阶段计数 — ops.trade.appointment.tab-count

用途：统计一天内指定门店/服务的预约阶段数量，只作工作量统计。`date`、`storeId`、`serviceId` 都可选；未给 `date` 时不要把默认统计误说成特定日期。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| date | string | 可选，yyyy-MM-dd；省略不限定日期 | 预约日期 |
| storeId | string | 可选，十进制 ID | 门店 |
| serviceId | string | 可选，十进制 ID | 到店服务 |

`AppointmentTabCountVO`：`all/pendingConfirm/pendingVisit/visited/completed/cancelled/rejected/noShow` 为数量。此能力仅承接日期、门店和服务，不接受列表姓名、手机号、状态等筛选；不得声称它与任意列表完全同口径。来源：`AppointmentRecordServiceImpl.tabCount` 及聚合实现。

```json
{
  "capability": "ops.trade.appointment.tab-count",
  "input": { "date": "2026-09-09" },
  "summary": "统计预约状态"
}
```

---

## ✅ 预约日历 — ops.trade.appointment.calendar

用途：查看日期区间的预约汇总，用于排班或容量判断。它没有单笔操作状态。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| startDate | string | 可选，yyyy-MM-dd；默认系统当天 | 区间首日 |
| endDate | string | 可选，yyyy-MM-dd；默认首日加 6 天 | 区间末日；Agent 保证不早于首日 |
| storeId | string | 可选，十进制 ID | 门店 |
| serviceId | string | 可选，十进制 ID | 到店服务 |

返回 `AppointmentCalendarDayVO[]`；每项 `date/totalCount/pendingConfirmCount/pendingVisitCount/visitedCount/completedCount/cancelledCount/rejectedCount/noShowCount`。这是预约数量，未提供容量或剩余名额，不能仅凭数量断言时段已满；日历不是单笔处置依据。来源：`AppointmentRecordServiceImpl.calendarAggregate`、`AppointmentCalendarDayVO`。

```json
{
  "capability": "ops.trade.appointment.calendar",
  "input": {
    "startDate": "2026-09-01",
    "endDate": "2026-09-30"
  },
  "summary": "查询预约日历"
}
```

---

## ✅ 预约看板 — ops.trade.appointment.dashboard.metrics

用途：读取指定近 7 天或近 30 天的预约运营聚合指标；只读看板，不能据此直接确认、拒绝或标记到访，也不产生单笔操作依据。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| timeDimension | string | 必填；LAST_7_DAYS / LAST_30_DAYS，大小写严格 | 最近 7 天或 30 天，含系统当天 |

`AppointmentDashboardMetricsVO`：`totalCount` 总数，`arrivalRate/cancelRate` 为已经乘 100 的百分比数值（如 25 表示 25%，不再乘 100），`todayPendingVisit` 今日待到店；`topStores[]` 含 `storeId/storeName/count`，`topTimeSlots[]` 含 `startTime/count`，时段格式 HH:mm。到店率分子含 visited 与 completed，不能解释为逐人实际签到率。门店名称获取失败会退回门店 ID，不编造名称。这些是固定对象，不接受任意附加字段。来源：`AppointmentDashboardMetricsQuery` 的必填与正则、`AppointmentDashboardServiceImpl.aggregateMetrics/computeArrivalRate/computeCancelRate`、运营预约看板类型。无单笔 ID，不能据此写预约；看板必须提供 `timeDimension`。

```json
{
  "capability": "ops.trade.appointment.dashboard.metrics",
  "input": { "timeDimension": "LAST_7_DAYS" },
  "summary": "查询预约看板"
}
```

---

## ✅ 预约全局配置查询 — ops.trade.appointment.config.get

用途：查询预约全局配置（防重复预约、取消限次、并发控制、提醒等规则现值）。

入参：无，传 `{}`。结果来源 `AppointmentGlobalConfigVO`：`enableDuplicateCheck`（防重复预约开关）、`cancelLimitPerMonth`（每月取消次数上限）、`maxActivePerUser`（单用户活跃预约上限）、`autoCompleteTimeoutHours`（超时自动完成小时数）、`reminderHoursBefore`（提醒提前小时数）、`enableConcurrencyControl`（并发控制开关）。

```json
{
  "capability": "ops.trade.appointment.config.get",
  "input": {},
  "summary": "查询预约全局配置"
}
```

---

## ✅ 预约导出 — ops.trade.appointment.export

用途：按筛选条件导出预约数据（🟢 URL 型）。入参为预约检索筛选（日期/状态/门店等，同 search 的可选字段）。结果 `ExportResultVO`：`downloadUrl`（预签名，约 60 分钟时效）；链接转告用户，不代下载。

```json
{
  "capability": "ops.trade.appointment.export",
  "input": {},
  "summary": "导出预约数据"
}
```

---

## ✅ 提醒记录搜索 — ops.trade.appointment.reminder-log.search

用途：分页查询预约提醒的发送记录（核对提醒是否实际发出）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| pageNum / pageSize | 整数 | 否（公共分页默认） | 页码/每页 |
| appointmentNo | 字符串 | 否，≤64 字符 | 预约编号精确匹配 |
| reminderType | 字符串 | 否，`user_before` / `staff_before` | 提醒类型（客户前/服务人员前） |
| channel | 字符串 | 否，`sms` / `wechat_template` / `site_inbox` | 发送渠道 |
| sendStatus | 字符串 | 否，`mocked` / `sent` / `failed` | 发送状态 |
| timeStart / timeEnd | 时间字符串 | 否，`yyyy-MM-dd HH:mm:ss` | 计划发送时间范围 |

来源：`AppointmentReminderLogPageQuery`。结果为 `PageResult<AppointmentReminderLogVO>` 分页，每条含：`id`（详情定位）、`appointmentNo`、`reminderType`、`channel`、`receiverDisplay`（接收方展示：会员提醒=脱敏手机号；服务人员提醒=admin 账号信息 **JSON 文本字符串**，冻结场景为空字符串）、`templateCode`（模板编码）、`sendStatus`、`plannedSendTime` / `mockedAt`（`yyyy-MM-dd HH:mm:ss`，计划/实际发送时间）、`errorMsg`（异常信息）。

```json
{
  "capability": "ops.trade.appointment.reminder-log.search",
  "input": { "pageNum": 1, "pageSize": 20, "sendStatus": "failed" },
  "summary": "查询失败的预约提醒"
}
```

---

## ✅ 提醒记录详情 — ops.trade.appointment.reminder-log.detail

用途：查询单条提醒记录详情（**`contentJson` 已二次脱敏**，敏感内容不回显明文）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | reminder-log.search 返回的记录 ID |

结果来源 `AppointmentReminderLogDetailVO`：列表字段 + `mockFlag`（整数，1=Mock 发送）+ `contentJson`（**消息体 JSON 文本字符串**：模板变量对象，如预约日期/时段/门店/会员称呼等键，已脱敏；键集随模板变化，无统一 schema，转述键值即可、不补造字段）。

```json
{
  "capability": "ops.trade.appointment.reminder-log.detail",
  "input": { "id": "8150000000000000001" },
  "summary": "查询提醒记录详情"
}
```
