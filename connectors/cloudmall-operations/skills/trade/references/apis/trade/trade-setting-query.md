# 交易域 — 交易设置与运营日志契约（查询侧）

> 概念知识：`references/domains/trade-concepts.md`；超时/赠品仓保存写操作见 `trade-setting-action.md`；运营流程：`references/flows/trade-appointment.md`
> 交易设置（本组）与售后设置（`aftersale-config-*.md`）是两套独立配置：前者管订单超时/赠品仓，后者管售后时效/退库存/自动退款/运费规则。所有时间字段单位是分钟，不是小时。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 setting.timeout-config · setting.gift-warehouse-config.get · operation-log.search · operation-log.detail

---

## ✅ 交易超时设置查询 — ops.trade.setting.timeout-config

用途：读取交易订单的超时规则。无输入；只读，不能依据返回值推断或修改售后时效设置（售后时效在 `aftersale-config-query.md`，两套配置相互独立）。

`TradeTimeoutSettingVO`：`paymentCancelMinutes` 普通订单支付取消分钟数、`autoReceiveMinutes` 自动收货分钟数、`seckillPaymentCancelMinutes` 秒杀支付取消分钟数、`addressEditEnabled` 是否允许改地址、`addressEditWindowMinutes` 改地址窗口分钟数。仅反映当前设置，不能把分钟误报天数，不能假定已有订单一定按当前配置重算。

```json
{
  "capability": "ops.trade.setting.timeout-config",
  "input": {},
  "summary": "查询交易超时设置"
}
```

---

## ✅ 赠品仓库规则查询 — ops.trade.setting.gift-warehouse-config.get

用途：查询赠品仓库发货规则配置（订单含赠品时是否强制与主商品同仓发货）。

入参：无，传 `{}`。结果来源 `GiftWarehouseSettingVO`：`forceSameWarehouse`（布尔值，默认 false——不强制同仓，赠品可从其他仓发货）。

```json
{
  "capability": "ops.trade.setting.gift-warehouse-config.get",
  "input": {},
  "summary": "查询赠品仓库规则"
}
```

---

## ✅ 配置操作日志搜索 — ops.trade.operation-log.search

用途：分页查询交易配置操作日志（售后配置等写操作会自动记录，模块 `AFTER_SALE_CONFIG`；本能力是变更审计入口）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| firstModule | 字符串 | 是，非空 | 一级模块：`AFTER_SALE_CONFIG`（售后四类配置与订单/售后超时）或 `TRADE_CONFIG`（赠品仓库规则） |
| secondModule | 字符串 | 否 | 二级模块，实际值域：`AUTO_REFUND`（自动退款）、`FREIGHT_RULE`（运费规则）、`TIMELINESS`（订单超时与售后时效**共用**，按 `targetId` 配置键区分）、`INVENTORY`（售后退库存）、`GIFT_WAREHOUSE`（赠品仓库，firstModule=TRADE_CONFIG） |
| pageNo | 整数 | 是，≥1 | 页码 |
| pageSize | 整数 | 是，1~100 | 每页条数 |

结果来源 `PageResult<TradeConfigOperationLogVO>`：每条含 `id`、`firstModule` / `secondModule`、`action`、`targetId`、`summary`、`operatorName`、`createdTime`。

```json
{
  "capability": "ops.trade.operation-log.search",
  "input": { "firstModule": "AFTER_SALE_CONFIG", "pageNo": 1, "pageSize": 20 },
  "summary": "查询售后配置操作日志"
}
```

---

## ✅ 配置操作日志详情 — ops.trade.operation-log.detail

用途：查询单条配置操作日志详情（含变更前后完整 JSON）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | operation-log.search 返回的日志 ID |

结果来源 `TradeConfigOperationLogDetailVO`：列表字段（含 `operatorId`/`operatorName` 双操作人标识）+ `beforeValue` / `afterValue`（变更前后配置的 **JSON 文本字符串**，非对象；`targetId` 为配置键）。JSON 内部字段集按配置键区分：`AFTER_SALE_AUTO_REFUND_SETTING` 为自动退款 6 字段、`AFTER_SALE_FREIGHT_RULE_SETTING` 为 11 条规则数组、`TRADE_TIMEOUT_SETTING` 为订单超时 5 字段、`AFTER_SALE_TIMEOUT_SETTING` 为售后时效 8 字段、`AFTER_SALE_INVENTORY_SETTING` 为退库存 2 字段、`GIFT_WAREHOUSE_SETTING` 为赠品仓 1 字段。解析失败或为 `null`（首次保存无前值）时如实报告，不补造。用于精确核对某次配置变更内容；敏感值不向用户复述原文。

```json
{
  "capability": "ops.trade.operation-log.detail",
  "input": { "id": "8160000000000000001" },
  "summary": "查询配置变更详情"
}
```
