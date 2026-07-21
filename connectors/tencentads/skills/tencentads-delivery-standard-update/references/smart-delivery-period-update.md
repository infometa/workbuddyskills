# 周期达成编辑参考 (Period Completion Update)

> 来源：腾讯广告 MKT API `adgroups/update` 接口
> 适用：`tencentads-delivery-standard-update` 更新周期达成项目时使用

---

## 概述

周期达成项目的编辑操作与普通项目不同，存在以下特殊约束：
- 周期达成开关（`smart_delivery_period_switch`）**不可修改**——创建时确定后无法通过编辑接口开启或关闭
- 部分金额字段**只允许提升**，不允许降低
- `daily_budget`（日预算）**不允许**传入

---

## 可编辑字段

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| `smart_delivery_period_budget` | number | 周期总预算（单位：**分**） | 只允许提升，不允许降低。约束：≥ 3 × 出价 × 周期天数 |
| `smart_delivery_period_continue` | string | 续投开关 | `PERIOD_CONTINUE_SWITCH_ON` / `PERIOD_CONTINUE_SWITCH_OFF` |

---

## 编辑规则

### 1. 周期达成开关不可修改

`smart_delivery_period_switch` 在创建时确定后**无法通过编辑接口开启或关闭**。非周期达成项目不能变成周期达成项目，反之亦然。

### 2. 周期达成项目的特殊限制

如果目标项目是周期达成项目，以下限制自动生效：

- **只允许提升**的字段：
  - `bid_amount`（出价）——只能往上调，不能降低
  - `smart_delivery_period_budget`（周期预算）——只能往上调，不能降低
  - `deep_conversion_behavior_bid`（深层出价）——只能往上调，不能降低
- **只允许降低**的字段：
  - `deep_conversion_worth_rate`（ROI 系数）——只能降低（ROI 低=目标放宽）
- **禁止传入**的字段：
  - `daily_budget`（日预算）
- **预算约束**：修改后的 `smart_delivery_period_budget` 仍须满足 ≥ 3 × 出价 × 周期天数

### 3. 修改续投开关

| 操作 | 说明 |
|------|------|
| 从"不续投"→"续投"（`PERIOD_CONTINUE_SWITCH_ON`） | 项目需未过期，切换后 `end_date` 自动清空（变为长期投放） |
| 从"续投"→"不续投"（`PERIOD_CONTINUE_SWITCH_OFF`） | 系统自动计算当前周期的 `end_date` |

### 4. 修改周期预算

- 只允许提升，不允许降低

---

## 用户意图映射

| 用户输入 | 对应字段 |
|----------|----------|
| "把项目X的周期预算提高到3000元" | `smart_delivery_period_budget: 300000`（3000元=300000分） |
| "项目X改为续投" / "开启续投" | `smart_delivery_period_continue: "PERIOD_CONTINUE_SWITCH_ON"` |
| "项目X关闭续投" / "不续投了" | `smart_delivery_period_continue: "PERIOD_CONTINUE_SWITCH_OFF"` |

---

## 示例

### 周期达成项目提高周期预算

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"smart_delivery_period_budget":300000}'
```

### 周期达成项目开启续投

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"smart_delivery_period_continue":"PERIOD_CONTINUE_SWITCH_ON"}'
```

### 周期达成项目关闭续投

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"smart_delivery_period_continue":"PERIOD_CONTINUE_SWITCH_OFF"}'
```

### 周期达成项目同时提高出价和周期预算

> 周期达成项目出价只允许提升不允许降低。提高出价时需确保周期预算仍满足 ≥ 3 × 出价 × 周期天数。

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"bid_amount":6000,"smart_delivery_period_budget":200000}'
```
