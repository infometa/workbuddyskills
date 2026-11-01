# 交易域 — 售后配置契约（查询侧）

> 概念知识：`references/domains/trade-concepts.md`；保存/重置写操作见 `aftersale-config-action.md`；运营流程：`references/flows/trade-aftersale-config.md`
> 本页是租户级售后规则配置的读取面：四组配置（自动退款/退运费规则/售后时效/退库存）相互独立，保存均为全量覆盖（不是增量合并），写入前先读现值。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 aftersale.auto-refund.get · aftersale.freight-rule.list · aftersale.timeout-config.get · aftersale.inventory-config.get

---

## ✅ 自动退款配置查询 — ops.trade.aftersale.auto-refund.get

用途：读取自动退款开关与阈值配置。未配置过时返回默认值（enabled=false）。

入参：无，传 `{}`。结果来源 `AfterSaleAutoRefundSettingVO`：

| 字段 | 类型 | 含义 |
|---|---|---|
| enabled | 布尔值 | 自动退款是否启用 |
| amountThreshold | 整数 | 金额阈值，单位**分**（前端类型注释同口径） |
| userLimitCount | 整数 | 单用户近 N 天售后次数限制 |
| userLimitDays | 整数 | 统计天数窗口 |
| skuBlacklistCount | 整数 | SKU 黑名单阈值（同 SKU 售后达到该次数进黑名单） |
| userBlacklistCount | 整数 | 用户黑名单阈值 |

未保存过配置时返回默认值：`enabled=false、amountThreshold=0、userLimitCount=0、userLimitDays=30、skuBlacklistCount=0、userBlacklistCount=0`。配置读取走 Redis 缓存 + DB，保存后即时生效于读取面。

注意（实现缺口，如实报告）：当前 trade-center 内该配置只有存储与 Feign 读取接口，未发现自动退款执行消费方；开关与阈值描述的是规则意图，不能据此向用户承诺“配置后即自动退款”。

```json
{
  "capability": "ops.trade.aftersale.auto-refund.get",
  "input": {},
  "summary": "查询自动退款配置"
}
```

---

## ✅ 退运费规则查询 — ops.trade.aftersale.freight-rule.list

用途：读取退换货运费规则矩阵。售后场景下“谁承担运费”由该矩阵判定；首次读取自动初始化默认规则。

入参：无，传 `{}`。结果来源 `AfterSaleFreightRuleVO` 数组，固定 11 条规则（售后类型 × 发货状态组合维度）：

| 字段 | 类型 | 含义 |
|---|---|---|
| ruleId | 字符串 | 规则标识（如 `RULE_01`），保存时原样回传 |
| afterSaleType / shippingStatus / refundScope / responsibility | 字符串 | 规则维度组合（售后类型、发货状态、退款范围、责任归属），只读 |
| originalFreight | 字符串 | 原发货运费处理方式：`全退` / `不退` / `人工判定` / `0` / `-`（枚举文本，非数值） |
| returnFreight | 字符串 | 退回运费处理方式：`商家承担` / `用户自付` / `人工判定` / `-` |
| newShipmentFreight | 字符串 | 寄新货运费处理方式：`商家出` / `-` |
| refundAmount | 字符串 | 退款范围描述（只读） |
| editable | 布尔值 | 该规则是否可编辑；不可编辑项保存时保留原值 |

首次读取时系统用分布式锁初始化默认规则并落库。运费字段值是中文枚举文本，不是金额数字；修改时从 list 结果原样取合法值，不自造新枚举。

```json
{
  "capability": "ops.trade.aftersale.freight-rule.list",
  "input": {},
  "summary": "查询退运费规则"
}
```

---

## ✅ 售后时效配置查询 — ops.trade.aftersale.timeout-config.get

用途：读取售后时效配置（各阶段超时阈值与自动流转开关）。

入参：无，传 `{}`。结果来源 `AfterSaleTimeoutSettingVO`：

| 字段 | 类型 | 含义 |
|---|---|---|
| afterSaleWindow | 整数（天） | 售后发起时间窗（确认收货后 N 天内可发起） |
| auditTimeoutEnabled | 布尔值 | 审核超时自动处理开关 |
| auditTimeoutHours | 整数（小时） | 审核超时时间，超时自动通过 |
| returnTimeout | 整数（天） | 用户寄回超时，超时自动关闭 |
| merchantReceiveTimeout | 整数（天） | 商家自动收货超时，超时自动确认收货 |
| selfPickupTimeoutEnabled | 布尔值 | 自提超时未核销检测开关 |
| selfPickupTimeoutAction | 字符串 | 自提超时处理：`AUTO_CANCEL`（自动取消订单）/ `AUTO_AFTER_SALE`（自动发起售后） |
| selfPickupTimeoutDays | 整数（天） | 备货完成后 N 天未核销触发 |

```json
{
  "capability": "ops.trade.aftersale.timeout-config.get",
  "input": {},
  "summary": "查询售后时效配置"
}
```

---

## ✅ 退库存配置查询 — ops.trade.aftersale.inventory-config.get

用途：读取售后退库存配置（售后完成后是否自动回补商品库存）。

入参：无，传 `{}`。结果来源 `AfterSaleInventorySettingVO`：`enabled`（布尔值，是否启用退库存）与 `applicableTypes`（字符串数组，适用售后类型，元素为 `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE`）。

```json
{
  "capability": "ops.trade.aftersale.inventory-config.get",
  "input": {},
  "summary": "查询售后退库存配置"
}
```
