# 会员域 — 积分兑换订单查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；兑换订单发货（写操作）见 `points-exchange-order-action.md`，积分商品见 `points-goods-query.md` / `points-goods-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。⚠️ 本模块分页参数为 **`pageNo` / `pageSize`**（不是 pageNum）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.points-exchange-order.search 兑换订单分页 · member.points-exchange-order.detail 兑换订单详情

---

## ✅ 兑换订单分页 — ops.member.points-exchange-order.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNo / pageSize | Integer | — | 分页（⚠️ 参数名是 pageNo，默认 1 / 10） |
| status | Integer | — | 1=待发货 / 2=已发货 / 3=已完成 / 4=已取消 |
| channel | Integer | — | 渠道：1=小程序 / 2=H5 / 3=APP |
| orderNo | String | — | 订单号（精确） |
| receiverName | String | — | 收货人姓名（模糊） |

### 出参（原始返回）

分页对象。**关键字段**：`records[].id`（→ 详情/发货路径参数）、`orderNo`；**枚举字段**：`status`（1/2/3/4，附 statusDesc）、`channel`（1/2/3，附 channelDesc）；**格式敏感字段**：`redeemPoints`（整数）、`redeemAmount`（元）、`createdTime`（yyyy-MM-dd HH:mm:ss）；**脱敏字段**：`receiverPhone`（脱敏）。

### 调用示例

```json
{"capability":"ops.member.points-exchange-order.search","input":{"pageNo":1,"pageSize":20,"status":1},"summary":"查询待发货的兑换订单"}
```

---

## ✅ 兑换订单详情 — ops.member.points-exchange-order.detail

- 发货前必读（收货信息与物流信息）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 订单 ID（来自 search 的 `records[].id`） |

### 出参（原始返回）

订单详情对象（列表字段 + `receiverAddress`、`logisticsCompany`、`logisticsNo`、`paymentNo`、`paymentStatus`）。

### 调用示例

```json
{"capability":"ops.member.points-exchange-order.detail","input":{"id":"1200012345678901234"},"summary":"查询兑换订单详情"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 兑换订单导出（export） | 后端首期返回空响应，未实现 |
