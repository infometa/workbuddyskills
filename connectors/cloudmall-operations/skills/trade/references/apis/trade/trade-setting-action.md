# 交易域 — 交易设置契约（写操作）

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-appointment.md`
> **先读现值**：保存前用 `trade-setting-query.md` 的对应 get 读现值、复述新旧值，确认后提交并回读核对。售后侧规则（自动退款/运费/时效/退库存）在 `aftersale-config-action.md`，与交易侧设置相互独立。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 setting.timeout-config.save 🔴 · setting.gift-warehouse-config.save 🔴

---

## ✅ 保存交易超时设置 — ops.trade.setting.timeout-config.save

用途：保存交易订单超时配置（🔴）。全量覆盖；影响后续新订单的超时取消/自动收货任务，存量订单不重算。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| paymentCancelMinutes | 整数 | 是，1~43200 | 待支付取消时间（分钟） |
| autoReceiveMinutes | 整数 | 是，1~43200 | 自动确认收货时间（分钟） |
| seckillPaymentCancelMinutes | 整数 | 否，1~60 | 秒杀订单超时取消（分钟） |
| addressEditEnabled | 布尔值 | 否 | C 端下单后可修改地址开关 |
| addressEditWindowMinutes | 整数 | 否，0~120 | 可修改地址时间窗口（分钟，基准=支付成功时间） |

来源：`TradeTimeoutSettingSaveRequest`。先 timeout-config 读现值，复述新旧值后提交；回读核对。

```json
{
  "capability": "ops.trade.setting.timeout-config.save",
  "input": {
    "paymentCancelMinutes": 30,
    "autoReceiveMinutes": 10080,
    "seckillPaymentCancelMinutes": 5,
    "addressEditEnabled": false,
    "addressEditWindowMinutes": 60
  },
  "summary": "保存交易超时配置"
}
```

---

## ✅ 保存赠品仓库规则 — ops.trade.setting.gift-warehouse-config.save

用途：保存赠品仓库发货规则（🔴）。影响后续赠品订单的履约仓选择。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| forceSameWarehouse | 布尔值 | 是 | true=赠品强制与主商品同仓发货；false=可拆仓 |

```json
{
  "capability": "ops.trade.setting.gift-warehouse-config.save",
  "input": { "forceSameWarehouse": true },
  "summary": "保存赠品仓库规则"
}
```
