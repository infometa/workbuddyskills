# 物流域 — 轨迹查询契约

> 概念知识：`references/domains/logistics.md`（统一轨迹状态字典）；运营流程：`references/flows/logistics.md`
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.logistics.`）：查询 track.query

---

## ✅ 物流轨迹查询 — ops.logistics.track.query

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| expressCompanyCode | String | 是 | 来自启用快递公司列表或交易/售后记录 |
| trackingNumber | String | 是 | 运单号 |
| phone | String | 否 | 收件人手机号后四位；服务提示需要时传，执行前必须严格校验 `^\d{4}$`，Java 当前不校验格式 |

返回 `expressCompanyName/trackingNumber/currentStatus/tracks[]`。`currentStatus` 按领域字典解释；`tracks[]` 含 `time/content/areaCode/areaName/status`，但当前查询实现未赋值明细 `status`，不得据此判断节点状态。时间由平台透传，不强制统一格式。

平台故障可能返回 `currentStatus=null` 且空 `tracks`，这不是“尚未揽收”的确定证据；空轨迹可能是平台异常降级，不能向用户断言尚未揽收。

```json
{"capability":"ops.logistics.track.query","input":{"expressCompanyCode":"shunfeng","trackingNumber":"SF1234567890","phone":"1234"},"summary":"查询订单物流轨迹"}
```
