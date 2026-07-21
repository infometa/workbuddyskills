# 智投项目周期达成 (Period Completion)

> 来源：腾讯广告 MKT API `adgroups/add` 接口
> 适用：`tencentads-delivery-smart-create` 创建智投项目时使用

---

## 概述

周期达成是一种固定周期投放模式，系统学习多天累计数据以进行更充分的探索，帮助广告主以更稳定的成本获得更高转化。

**仅在用户明确提出"周期达成"/"周期稳投"需求时才开启，不要自行添加。**

> ⚠️ 周期达成仅部分智投场景支持，目前已支持的场景包括：**线索智投**（`SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_LEADS`）。如果账号未开通周期达成功能，创建时会报错提示不支持。

---

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `smart_delivery_period_switch` | enum | **是** | 周期达成开关：`PERIOD_SWITCH_ON` / `PERIOD_SWITCH_OFF` |
| `smart_delivery_period_days` | enum | 开启时**必填** | 周期天数：`PERIOD_DAYS_THREE`(3天) / `PERIOD_DAYS_SEVEN`(7天) |
| `smart_delivery_period_budget` | integer | 开启时**必填** | 周期总预算（单位：**分**） |
| `smart_delivery_period_continue` | enum | 开启时**必填** | 续投开关：`PERIOD_CONTINUE_SWITCH_ON`(长期自动续投) / `PERIOD_CONTINUE_SWITCH_OFF`(单周期结束即停) |

---

## 约束规则

开启周期达成时，必须满足以下规则：

### 1. 必填字段组合

四个字段必须同时设置：
- `smart_delivery_period_switch` = `PERIOD_SWITCH_ON`
- `smart_delivery_period_days`（选择 3 天或 7 天）
- `smart_delivery_period_budget`（周期总预算）
- `smart_delivery_period_continue`（续投模式）

### 2. 预算约束

`smart_delivery_period_budget` ≥ 3 × `bid_amount` × 周期天数

例如：出价 100 分、7 天周期 → 预算 ≥ 2100 分

### 3. 禁止字段与自动覆盖字段

开启周期达成时，以下字段**不允许** Agent 传入：
- `daily_budget`（日预算）
- `total_budget`（总预算）

以下字段由脚本**自动覆盖**，Agent 不应手动构造：
- `end_date` — 脚本统一设为空字符串 `""`，无论续投还是不续投，后端根据 `begin_date` + 周期天数自动计算实际结束日期

### 4. 出价限制

不允许使用自动出价：`smart_bid_type` 不能为 `SMART_BID_TYPE_SYSTEMATIC`

### 5. 投放时段

支持多时段投放，可设置 `delivery_time_ranges` 和 `first_day_begin_time`（不传则默认全时段）

### 6. 续投模式

- `PERIOD_CONTINUE_SWITCH_ON`：系统长期自动续投（`end_date` 设为空）
- `PERIOD_CONTINUE_SWITCH_OFF`：单周期结束即停（`end_date` = `begin_date` + 周期天数 - 1）

---

## 示例

### 7天周期、续投、出价 50 元、周期预算 2000 元

```json
{
  "smart_delivery_period_switch": "PERIOD_SWITCH_ON",
  "smart_delivery_period_days": "PERIOD_DAYS_SEVEN",
  "smart_delivery_period_budget": 200000,
  "smart_delivery_period_continue": "PERIOD_CONTINUE_SWITCH_ON",
  "bid_amount": 5000,
  "begin_date": "2026-06-10",
  "delivery_time_ranges": ["all"]
}
```

### 3天周期、不续投

```json
{
  "smart_delivery_period_switch": "PERIOD_SWITCH_ON",
  "smart_delivery_period_days": "PERIOD_DAYS_THREE",
  "smart_delivery_period_budget": 60000,
  "smart_delivery_period_continue": "PERIOD_CONTINUE_SWITCH_OFF",
  "bid_amount": 5000,
  "begin_date": "2026-06-10",
  "delivery_time_ranges": ["all"]
}
```
