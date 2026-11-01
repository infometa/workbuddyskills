---
name: yh-dish-report
display_name: 菜品销售报表
display_name_en: Dish Sales Reports
description: 当用户需要查询菜品销量排行、菜品销售汇总或菜品时段销售分布时使用。
description_zh: 通过 query_dish_sum 查询菜品销售汇总（销量/金额/退菜），通过 query_dish_period_sum 查询菜品时段销售汇总（按时段或餐段看菜品销量分布）。
description_en: Query dish sales summaries (quantity, amount, refunds) via query_dish_sum and dish sales by time period via query_dish_period_sum.
version: 1.0.0
author: 有好云
---

# 菜品销售报表

## 工具：query_dish_sum

菜品销售汇总报表查询。按日期/门店/市场/运营区/督导区/商圈/城市/用餐方式/订单渠道等维度，查询指定时间区间内菜品的销量、金额、退菜等数据汇总。

### 参数说明

| 参数名 | 类型 | 必填 | 枚举值 | 说明 |
|---|---|---|---|---|
| `begin_date` | string | ✅ | — | 统计开始日期，格式 YYYY-MM-DD；与 end_date 间隔最长 31 天（门店数≤10 家放宽至 366 天，仅查单店放宽至 92 天；午/晚市高峰时段收紧为 7~31 天） |
| `end_date` | string | ✅ | — | 统计结束日期，格式 YYYY-MM-DD，不能早于 begin_date |
| `sku_union` | string | — | `1` | 菜品规格合并统计（不拆分规格），默认不合并 |
| `combo_flag` | string | — | `1`~`5` | 菜单属性：1=单点+套餐子菜，2=单点+主套餐，3=仅单点，4=仅主套餐，5=仅套餐子菜 |
| `begin_period` / `end_period` | string | — | — | 时段范围（0-23），可选 |
| `date_flag` | string | — | `1` | 开启【日期】拆分维度 |
| `branch_flag` | string | — | `1` | 开启【门店】拆分维度 |
| `sheet_type_flag` | string | — | `1` | 开启【用餐方式】拆分维度 |
| `f_area_flag` / `s_area_flag` / `t_area_flag` / `trading_flag` / `city_flag` | string | — | `1` | 开启【市场/运营区/督导区/商圈/城市】拆分维度 |
| `channel_flag` | string | — | `1` | 开启【订单渠道】拆分维度 |
| `include_give_flag` | string | — | `1` | 销量包含赠送，默认不包含 |
| `brand_id` / `branch_id` | string | — | — | 品牌/门店过滤，多个用逗号隔开 |
| `dish_id` | string | — | — | 菜品ID过滤，可先调用 `search_dish` 按名称获取 |
| `type_id` / `category_id` / `category_ids` | string | — | — | 菜品类型/大类/小类ID过滤 |
| `f_dept_id` / `account_id` | string | — | — | 财务部门/收入科目ID过滤 |
| `sheet_type` / `channel_id` | string | — | — | 用餐方式/订单渠道ID过滤 |

### 调用示例

**示例 1**：查询上周各门店销量前十菜品
```json
{
  "begin_date": "2026-09-14",
  "end_date": "2026-09-20",
  "branch_flag": "1"
}
```
> 结果按 `qty` 降序取前 10 行即为销量前十（注意跳过合计行 dishId=99999）。

**示例 2**：查询指定菜品的销售汇总
```json
{
  "begin_date": "2026-09-01",
  "end_date": "2026-09-22",
  "dish_id": "1001",
  "date_flag": "1"
}
```

### 返回值说明

返回 `{meta: {fields: [...]}, data: [...]}`，关键字段：

| 关键字段 | 说明 |
|---|---|
| `qty` | 菜品销量 |
| `oriAmt` / `realAmt` / `sheetAmt` | 原价金额 / 实收金额 / 单据金额（元） |
| `oriPrice` / `oriAvgPrice` / `realPrice` | 菜品原价 / 原价均价 / 实收均价 |
| `refundQty` / `refundAmt` | 退菜数量 / 退菜金额 |
| `eatInQty` / `takeOutQty` / `toGoQty` | 堂食 / 外卖 / 自取销量 |
| `dishId` / `dishName` | 菜品 ID / 名称（合计行 dishId=99999） |

所有 ID 列均已附 `*_Desc` 中文描述，无需再查字典。

## 工具：query_dish_period_sum

菜品时段销售汇总报表查询。按日期/门店/渠道/时段(餐段)维度，查询指定时间区间内菜品的时段销量、金额、退菜数据，用于分析"某个时段哪些菜品卖得好"。

### 参数说明

| 参数名 | 类型 | 必填 | 枚举值 | 说明 |
|---|---|---|---|---|
| `begin_date` | string | ✅ | — | 统计开始日期，格式 YYYY-MM-DD；跨度限制同 query_dish_sum |
| `end_date` | string | ✅ | — | 统计结束日期，格式 YYYY-MM-DD，不能早于 begin_date |
| `dimension` | string | — | `Period`(默认), `Market` | 分组维度：Period=按时段（配合 period_div），Market=按餐段 |
| `period_div` | string | — | `60`(默认), `30`, `15` | 时段间隔（分钟），仅 dimension=Period 时有效 |
| `sku_union` | string | — | `1` | 菜品规格合并统计，默认不合并 |
| `combo_flag` | string | — | `1`~`5` | 菜单属性（同 query_dish_sum） |
| `begin_period` / `end_period` | string | — | — | 时段范围（0-23），可选 |
| `date_flag` | string | — | `1` | 开启【日期】拆分维度 |
| `branch_flag` | string | — | `1` | 开启【门店】拆分维度 |
| `channel_flag` | string | — | `1` | 开启【渠道】拆分维度 |
| `brand_id` / `branch_id` | string | — | — | 品牌/门店过滤，多个用逗号隔开 |
| `dish_id` | string | — | — | 菜品ID过滤，可先调用 `search_dish` 获取 |
| `type_id` / `category_id` | string | — | — | 菜品类型/大类ID过滤 |
| `sheet_type` / `channel_id` | string | — | — | 用餐方式/订单渠道ID过滤 |
| `f_dept_id` / `account_id` | string | — | — | 财务部门/收入科目ID过滤 |

> **重要**：`date_flag`、`branch_flag`、`channel_flag` 至少一项为 `"1"`。

### 调用示例

**示例 1**：查询昨天午餐时段各菜品的销售情况
```json
{
  "begin_date": "2026-09-22",
  "end_date": "2026-09-22",
  "dimension": "Market",
  "date_flag": "1"
}
```

**示例 2**：查询上周某门店菜品按小时的销售分布
```json
{
  "begin_date": "2026-09-14",
  "end_date": "2026-09-20",
  "branch_id": "30000001",
  "dimension": "Period",
  "period_div": "60"
}
```

### 返回值说明

返回 `{meta: {fields: [...]}, data: [...]}`，除与 query_dish_sum 相同的销量/金额/退菜字段外，含：

| 关键字段 | 说明 |
|---|---|
| `dynamicData` | 动态时段数据对象，key 为时段中文名称（如 08:00~09:00），value 为该时段销量 |
| `id` / `name` | 时段/餐段 ID 与名称（如 08:00 - 09:00、午餐） |

## 通用错误场景

| 场景 | 错误信息 | 处理方式 |
|---|---|---|
| 未登录 | 返回登录 URL | 引导用户完成 SSO 登录 |
| 日期跨度超限 | 返回跨度限制说明 | 拆分日期区间分批查询 |
| 无权限 | 工具未在 allowed_tools 或缺少菜单权限 | 联系管理员开通权限 |
| 菜品不存在 | 菜品ID无效 | 先用 search_dish 确认菜品ID |
