# 交易域 — 售后配置契约（写操作）

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-aftersale-config.md`
> **先读现值**：四组配置保存均为**全量覆盖**（不是增量合并）——先用 `aftersale-config-query.md` 的对应 get/list 读取现值，向用户复述当前值与目标变更，确认后构造完整提交，回读核对。保存带分布式锁防重复提交。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 aftersale.auto-refund.save 🟡 · aftersale.freight-rule.save 🔴 · aftersale.freight-rule.reset 🔴 · aftersale.timeout-config.save 🔴 · aftersale.inventory-config.save 🔴

---

## ✅ 保存自动退款配置 — ops.trade.aftersale.auto-refund.save

用途：保存自动退款配置（🟡）。全量覆盖：6 个字段全部必填，省略任意字段会校验失败；不能只提交变化项。`amountThreshold` 单位是**分**。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| enabled | 布尔值 | 是 | 是否启用 |
| amountThreshold | 整数 | 是，≥0 | 金额阈值，单位**分** |
| userLimitCount | 整数 | 是，≥0 | 单用户限制次数 |
| userLimitDays | 整数 | 是，≥1 | 统计天数 |
| skuBlacklistCount | 整数 | 是，≥0 | SKU 黑名单阈值 |
| userBlacklistCount | 整数 | 是，≥0 | 用户黑名单阈值 |

来源：`AfterSaleAutoRefundSettingSaveRequest`。保存带租户级分布式锁与配置操作日志（模块 `AFTER_SALE_CONFIG`，可在交易运营日志中追溯变更前后值）。提交后用 auto-refund.get 回读。自动退款配置当前无执行消费方（实现缺口），如实说明配置是规则意图而非执行承诺。

```json
{
  "capability": "ops.trade.aftersale.auto-refund.save",
  "input": {
    "enabled": true,
    "amountThreshold": 1000,
    "userLimitCount": 3,
    "userLimitDays": 30,
    "skuBlacklistCount": 5,
    "userBlacklistCount": 10
  },
  "summary": "保存自动退款配置"
}
```

---

## ✅ 保存退运费规则 — ops.trade.aftersale.freight-rule.save

用途：全量保存运费规则矩阵（🔴 影响全部售后运费判定）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| rules | 对象数组 | 是，**恰好 11 条** | 完整规则列表，从 freight-rule.list 取得后修改目标项 |

| rules[] 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| ruleId | 字符串 | 是 | 规则 ID，与 list 返回一致 |
| originalFreight | 字符串 | 否 | 原发货运费处理方式，合法值见查询侧 list 节 |
| returnFreight | 字符串 | 否 | 退回运费处理方式 |
| newShipmentFreight | 字符串 | 否 | 寄新货运费处理方式 |

来源：`AfterSaleFreightRuleSaveRequest`（`@Size(min=11, max=11)`）。流程：先 freight-rule.list 取全部 11 条 → 只修改用户确认的目标项 → 完整提交 11 条 → 回读 list 核对。不可编辑（editable=false）的项原样回传。保存有分布式锁与操作日志。

```json
{
  "capability": "ops.trade.aftersale.freight-rule.save",
  "input": {
    "rules": [
      { "ruleId": "RULE_01", "originalFreight": "全退", "returnFreight": "商家承担", "newShipmentFreight": "-" }
    ]
  },
  "summary": "保存退运费规则（示例仅 1 条，实际必须提交全部 11 条）"
}
```

---

## ✅ 重置退运费规则 — ops.trade.aftersale.freight-rule.reset

用途：将运费规则矩阵重置为系统默认（🔴 覆盖当前全部自定义运费规则）。无请求体。

执行前向用户明确“当前全部自定义规则将被默认规则覆盖”；执行后返回重置后的 11 条规则，逐项核对并报告关键变化。重置同样有分布式锁与操作日志。

```json
{
  "capability": "ops.trade.aftersale.freight-rule.reset",
  "input": {},
  "summary": "重置退运费规则"
}
```

---

## ✅ 保存售后时效配置 — ops.trade.aftersale.timeout-config.save

用途：保存售后时效配置（🔴 影响超时自动流转任务的全租户行为）。全量覆盖，8 字段全部必填。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| afterSaleWindow | 整数 | 是，1~365 | 售后发起时间窗（天） |
| auditTimeoutEnabled | 布尔值 | 是 | 审核超时开关 |
| auditTimeoutHours | 整数 | 是，1~720 | 审核超时时间（小时），超时自动通过 |
| returnTimeout | 整数 | 是，1~90 | 用户寄回超时（天），超时自动关闭售后 |
| merchantReceiveTimeout | 整数 | 是，1~90 | 商家自动收货超时（天） |
| selfPickupTimeoutEnabled | 布尔值 | 是 | 自提超时检测开关 |
| selfPickupTimeoutAction | 字符串 | 是，仅 `AUTO_CANCEL` / `AUTO_AFTER_SALE` | 自提超时处理路径 |
| selfPickupTimeoutDays | 整数 | 是，1~90 | 自提超时天数 |

来源：`AfterSaleTimeoutSettingSaveRequest`（含范围校验与 `selfPickupTimeoutAction` 枚举校验）。先 timeout-config.get 读现值，复述变更项与新旧值，确认后全量提交并回读。

```json
{
  "capability": "ops.trade.aftersale.timeout-config.save",
  "input": {
    "afterSaleWindow": 15,
    "auditTimeoutEnabled": true,
    "auditTimeoutHours": 48,
    "returnTimeout": 7,
    "merchantReceiveTimeout": 15,
    "selfPickupTimeoutEnabled": false,
    "selfPickupTimeoutAction": "AUTO_CANCEL",
    "selfPickupTimeoutDays": 7
  },
  "summary": "保存售后时效配置"
}
```

---

## ✅ 保存退库存配置 — ops.trade.aftersale.inventory-config.save

用途：保存售后退库存配置（🔴 决定售后完成后库存回补行为）。全量覆盖。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| enabled | 布尔值 | 是 | 是否启用售后退库存 |
| applicableTypes | 字符串数组 | 是，非空 | 适用售后类型，元素限 `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE` |

来源：`AfterSaleInventorySettingSaveRequest`。提交后 inventory-config.get 回读。

```json
{
  "capability": "ops.trade.aftersale.inventory-config.save",
  "input": {
    "enabled": true,
    "applicableTypes": ["RETURN_REFUND", "EXCHANGE"]
  },
  "summary": "保存售后退库存配置"
}
```

---

## 配置纪律

四组配置相互独立，保存互不影响；每次保存写配置操作日志（模块 `AFTER_SALE_CONFIG`），可在交易运营日志查询中追溯。金额阈值单位是分（不是元）；运费规则字段是中文枚举文本（不是金额）；时效字段单位混合（天/小时）以各参数表为准。所有保存接口都是全量覆盖，先读现值再构造完整提交。
