# 交易域 — 服务订单写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-service-order.md`
> **先读现值**：全部写入先用 `service-order-query.md` 的 detail 读取履约子单与次数序号、time-slots 确认目标时段容量；三层标识（购买单/履约子单/次数序号）不能互换。
> 所有 ID 为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 service-order.assist-appointment 🔴 · service-order.reschedule 🔴 · service-order.dispatch 🔴 · service-order.redispatch 🔴 · service-order.verify 🔴

---

## ✅ 协助预约服务 — ops.trade.service-order.assist-appointment

用途：协助客户完成一次服务预约（🔴）。按次数序号预约到指定时间；重试保持同一序号；须先查时段容量。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| purchaseOrderNo | 字符串 | 是，路径参数 | 购买单号 |
| sequenceNo | 整数 | 是，>0 | 服务次数序号（从 1 开始） |
| appointmentAt | 时间字符串 | 是 | 预约时间（ISO-8601，如 `2026-09-25T10:00:00`） |
| operationReason | 字符串 | 是，非空 ≤200 字 | 操作原因（审计留痕，如客户确认记录） |

来源：`ServiceAdminAppointmentRequest`。先 `time-slots` 查该日期容量并向用户确认时段；执行后回读 detail 核对新预约。结果 `ServiceAppointmentResultVO`：`fulfillmentOrderNo`、`sequenceNo`、`appointmentAt`、`rescheduleCount`。

```json
{
  "capability": "ops.trade.service-order.assist-appointment",
  "input": {
    "purchaseOrderNo": "PO-SO20260905000001",
    "sequenceNo": 1,
    "appointmentAt": "2026-09-25T10:00:00",
    "operationReason": "客户电话确认周五上午上门"
  },
  "summary": "协助预约服务"
}
```

---

## ✅ 服务改约 — ops.trade.service-order.reschedule

用途：对已预约的履约子单改期（🔴）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| fulfillmentOrderNo | 字符串 | 是，路径参数 | 履约子单号（detail 的 fulfillments 取得） |
| appointmentAt | 时间字符串 | 是 | 新预约时间 |
| operationReason | 字符串 | 是，非空 ≤200 字 | 改约原因 |

来源：`ServiceAdminRescheduleRequest`。改约后 `rescheduleCount` 递增（展示计数，当前服务端不设改约上限，不以次数为拒绝依据）；先 time-slots 确认新时段可约。结果同 `ServiceAppointmentResultVO`（`rescheduleCount` 更新）。

```json
{
  "capability": "ops.trade.service-order.reschedule",
  "input": {
    "fulfillmentOrderNo": "FO20260905000001",
    "appointmentAt": "2026-09-26T14:00:00",
    "operationReason": "客户要求改期到周六下午"
  },
  "summary": "服务改约"
}
```

---

## ✅ 派单 — ops.trade.service-order.dispatch

用途：对履约子单首次派单给服务人员（🔴）。须真实人员信息。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| fulfillmentOrderNo | 字符串 | 是，路径参数 | 履约子单号 |
| staff | 对象 | 是 | `{ staffId, staffName }`——真实服务人员快照 |
| operationReason | 字符串 | 否，≤200 字 | 首次派单可不传 |

来源：`ServiceDispatchRequest` + `ServiceStaffSnapshot`（`staffId` 必填、`staffName` 非空 ≤64 字）。执行后回读 detail 核对服务人员；派单对象是真实人员（来自门店/导购域信息或用户指定），不猜测。

```json
{
  "capability": "ops.trade.service-order.dispatch",
  "input": {
    "fulfillmentOrderNo": "FO20260905000001",
    "staff": { "staffId": "8550000000000000001", "staffName": "王师傅" }
  },
  "summary": "派单服务人员"
}
```

---

## ✅ 改派 — ops.trade.service-order.redispatch

用途：改派服务人员（🔴）。与 dispatch 的区别：改派必须给原因。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| fulfillmentOrderNo | 字符串 | 是，路径参数 | 履约子单号 |
| staff | 对象 | 是 | 新服务人员 `{ staffId, staffName }` |
| operationReason | 字符串 | 否但强烈建议，≤200 字 | 改派原因（DTO 可选，改派留痕场景应提供） |

```json
{
  "capability": "ops.trade.service-order.redispatch",
  "input": {
    "fulfillmentOrderNo": "FO20260905000001",
    "staff": { "staffId": "8550000000000000002", "staffName": "李师傅" },
    "operationReason": "原服务人员临时请假"
  },
  "summary": "改派服务人员"
}
```

---

## ✅ 服务核销 — ops.trade.service-order.verify

用途：服务核销（🔴）。核销节点分**取件**（`PICKUP`）与**完成**（`COMPLETION`）；核销码是 4 位数字，来自客户，不猜测；码错不重试猜测。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| fulfillmentOrderNo | 字符串 | 是，路径参数 | 履约子单号 |
| verificationType | 字符串 | 是 | `PICKUP`（取件核销）/ `COMPLETION`（完成核销） |
| verificationCode | 字符串 | 是，正则 `\d{4}` | 4 位数字核销码（客户提供，不猜测） |
| operationReason | 字符串 | 是，非空 ≤200 字 | 核销说明 |

来源：`ServiceVerifyRequest`。核销码必须来自客户当面/消息提供；执行后回读 detail 核对状态推进。

```json
{
  "capability": "ops.trade.service-order.verify",
  "input": {
    "fulfillmentOrderNo": "FO20260905000001",
    "verificationType": "COMPLETION",
    "verificationCode": "1234",
    "operationReason": "服务已完成，客户确认"
  },
  "summary": "核销服务"
}
```

---

## 标识与体系边界

三层标识严格区分：`purchaseOrderNo` 购买单（预约入口）、`fulfillmentOrderNo` 履约子单（派单/改约/核销入口）、`sequenceNo` 次数序号（多次服务定位第几次）。服务预约与「到店预约」（appointment 契约）是两套体系：服务订单是商品履约链路，appointment 是独立预约台账。核销码 4 位数字（实物自提核销码是 6 位），两码不通用。
