---
name: yh-sales-query
display_name: 营业收入分析
display_name_en: Sales Revenue Analysis
description: 当用户需要查询餐饮门店营业收入、实收金额、时段餐段汇总等经营数据时使用。
description_zh: 通过 query_sale_income 查询门店营业收入报表（按日期/门店/餐段/收入口径），通过 query_sale_period 查询时段餐段汇总（按时段或餐段看订单、营收、来客数）。
description_en: Query branch revenue reports via query_sale_income (date/branch/meal-period dimensions) and meal-period summaries via query_sale_period (orders, revenue and guest counts by time period).
version: 1.0.0
author: 有好云
---

# 营业收入分析

## 工具：query_sale_income

营业收入分析报表查询。按日期/门店/餐段维度，查询指定时间区间内门店营收数据，支持原价/实收口径及多种收入分类，可按品牌/门店过滤。

### 参数说明

| 参数名 | 类型 | 必填 | 枚举值 | 说明 |
|---|---|---|---|---|
| `begin_date` | string | ✅ | — | 统计开始日期，格式 YYYY-MM-DD |
| `end_date` | string | ✅ | — | 统计结束日期，格式 YYYY-MM-DD，不能早于 begin_date |
| `brand_id` | string | — | — | 品牌过滤，多个ID用逗号隔开，如 `"66400620,10000001"`；需传ID而非名称 |
| `branch_id` | string | — | — | 门店过滤，多个ID用逗号隔开，如 `"30000001,30000002"`；需传ID而非名称 |
| `cycle` | string | — | `day`(默认), `month` | 日期聚合维度；day=按自然日，month=按月 |
| `data_mode` | string | — | `ori`(默认), `real` | 收入口径；ori=菜品原价（未扣优惠），real=实际收款 |
| `date_flag` | string | — | `1` | 开启【日期】拆分维度 |
| `branch_flag` | string | — | `1` | 开启【门店】拆分维度 |
| `market_flag` | string | — | `1` | 开启【餐段】拆分维度 |
| `item_group` | string | — | `FDept`(默认), `DishType`, `DishCategory`, `Account` | 收入分类维度；FDept=财务核算部门，DishType=菜品类型，DishCategory=菜品大类，Account=收入科目 |

> **重要**：`date_flag`、`branch_flag`、`market_flag` 至少一项为 `"1"`。

### 使用流程

1. **先查 ID**：如果用户给出的是品牌名/门店名，先调用 `query_dict` 获取对应 ID，再传入本工具。
2. **选择维度**：根据用户问题选择合适的 flag 和 item_group。
3. **选择口径**：用户说"实收"用 `data_mode=real`，否则默认 `ori`。

### 调用示例

**示例 1**：查询本月各门店营业收入（原价口径）
```json
{
  "begin_date": "2026-09-01",
  "end_date": "2026-09-22",
  "date_flag": "1",
  "branch_flag": "1"
}
```

**示例 2**：按菜品大类汇总上周实收金额
```json
{
  "begin_date": "2026-09-14",
  "end_date": "2026-09-20",
  "data_mode": "real",
  "date_flag": "1",
  "item_group": "DishCategory"
}
```

**示例 3**：指定品牌按月汇总
```json
{
  "begin_date": "2026-01-01",
  "end_date": "2026-09-22",
  "brand_id": "66400620",
  "cycle": "month",
  "date_flag": "1"
}
```

### 返回值说明

返回已转码的 grid 行数组（所有 ID 均已附中文描述，无需再查字典）。

### 认证说明

- 首次调用需要完成 SSO 登录授权（网关会返回登录 URL）
- 未授权时调用会返回包含登录链接的错误信息

### 错误场景

| 场景 | 错误信息 | 处理方式 |
|---|---|---|
| 未登录 | 返回登录 URL | 引导用户完成 SSO 登录 |
| 日期范围无效 | end_date 早于 begin_date | 修正日期参数 |
| 无维度标志 | 三个 flag 全为空 | 至少设置一个 flag 为 "1" |
| 无权限 | 工具未在 allowed_tools 中 | 联系管理员开通权限 |

## 工具：query_sale_period

时段餐段汇总报表查询。按日期/门店/市场/运营区/督导区/商圈/城市/用餐方式/订单渠道/时段(餐段)等维度，查询指定时间区间的营业数据汇总，含订单数、原价/实收/优惠金额、来客数及占比分析。

### 参数说明

| 参数名 | 类型 | 必填 | 枚举值 | 说明 |
|---|---|---|---|---|
| `begin_date` | string | ✅ | — | 统计开始日期，格式 YYYY-MM-DD；与 end_date 间隔最长 366 天（午/晚市高峰时段最长 31 天） |
| `end_date` | string | ✅ | — | 统计结束日期，格式 YYYY-MM-DD，不能早于 begin_date |
| `dimension` | string | — | `Period`(默认), `Market` | 主维度：Period=按时段（配合 period_div），Market=按餐段 |
| `period_div` | string | — | `60`(默认), `30`, `15` | 时段间隔（分钟），仅 dimension=Period 时有效 |
| `branch_flag` | string | — | `1` | 开启【门店】拆分维度 |
| `date_flag` | string | — | `1` | 开启【日期】拆分维度 |
| `f_area_flag` / `s_area_flag` / `t_area_flag` / `trading_flag` / `city_flag` | string | — | `1` | 开启【市场/运营区/督导区/商圈/城市】拆分维度 |
| `sheet_type_flag` | string | — | `1` | 开启【用餐方式】拆分维度 |
| `channel_flag` | string | — | `1` | 开启【订单渠道】拆分维度 |
| `brand_id` / `branch_id` | string | — | — | 品牌/门店过滤，多个用逗号隔开；需传ID而非名称 |
| `f_area_id` / `s_area_id` / `t_area_id` / `trading_id` | string | — | — | 市场/运营区/督导区/商圈ID过滤 |
| `sheet_type` / `channel_id` | string | — | — | 用餐方式/订单渠道ID过滤，多个用逗号隔开 |
| `city` | string | — | — | 城市名称过滤，多个用逗号隔开 |

> **重要**：各 `*_flag` 至少一项为 `"1"`。

### 使用流程

1. **先查 ID**：名称类过滤条件先用 `query_dict` 换 ID，再传本工具。
2. **选主维度**：用户问“哪个时段/餐段卖得好”→ `dimension=Period`（默认）或 `Market`。
3. **选拆分维度**：按用户问题设置对应 `*_flag`。

### 调用示例

**示例 1**：查询昨天各时段营业额（60分钟间隔）
```json
{
  "begin_date": "2026-09-22",
  "end_date": "2026-09-22",
  "dimension": "Period",
  "period_div": "60",
  "date_flag": "1"
}
```

**示例 2**：按餐段汇总本月各门店实收
```json
{
  "begin_date": "2026-09-01",
  "end_date": "2026-09-22",
  "dimension": "Market",
  "branch_flag": "1"
}
```

### 返回值说明

返回已转码的 `{meta: {fields: [...]}, data: [...]}`，data 每行为一个时段/餐段汇总：

| 关键字段 | 说明 |
|---|---|
| `validCnt` | 有效订单数 |
| `oriAmt` / `realAmt` / `sheetAmt` | 原价金额 / 实收金额 / 单据金额（元） |
| `yhAmt` | 优惠金额 = 原价-实收（元） |
| `persons` | 来客数 |
| `*_Per` | 对应指标占比（小数，展示时转%） |
| `*_Avg` | 对应单均/人均指标 |
| `id` / `name` | 时段/餐段 ID 与名称（如 08:00 - 09:00、午餐） |

所有 ID 列均已附 `*_Desc` 中文描述，无需再查字典。
