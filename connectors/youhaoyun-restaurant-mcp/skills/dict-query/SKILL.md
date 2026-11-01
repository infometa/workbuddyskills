---
name: yh-dict-query
display_name: 基础数据字典查询
display_name_en: Master Data Dictionary Lookup
description: 当需要将品牌/门店/餐段等中文名称转换为 ID，或搜索菜品库获取菜品 ID 时使用。
description_zh: 通过 query_dict 查询品牌、门店、餐段、菜品分类等基础字典（支持 ID/名称/编码），通过 search_dish 按关键词搜索菜品库获取菜品 ID。
description_en: Look up master data dictionaries (brand, branch, meal period, dish category) via query_dict by ID, name or code; search the dish library by keyword via search_dish to get dish IDs.
version: 1.0.0
author: 有好云
---

# 基础数据字典查询

## 工具：query_dict

基础数据字典统一查询入口。将用户输入的中文名称转换为对应 ID，再作为其他工具（如 `query_sale_income`）的过滤入参。

### 支持的字典类型

| dict_type | 说明 | 典型用途 |
|---|---|---|
| `Brand` | 品牌 | 查品牌ID → 传入 query_sale_income 的 brand_id |
| `Branch` | 门店 | 查门店ID → 传入 query_sale_income 的 branch_id |
| `Market` | 餐段 | 查餐段ID → 理解 market_flag 返回结果 |
| `PayWay` | 支付方式 | 查支付方式名称 |
| `FDept` | 财务核算部门 | 对应 item_group=FDept |
| `DishType` | 菜品类型 | 对应 item_group=DishType |
| `DishCategory` | 菜品大类 | 对应 item_group=DishCategory |
| `Account` | 收入科目 | 对应 item_group=Account |

### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `dict_type` | string | ✅ | 字典类型，见上表枚举 |
| `id` | string | — | 按ID精确查询，多个用逗号隔开，如 `"30000001,30000002"` |
| `name` | string | — | 按名称模糊查询（不区分大小写），兼容拼音码 |
| `code` | string | — | 按编码模糊查询（不区分大小写） |

> 三种查询条件可选、可组合，同时传时取交集。

### 返回结构

统一返回数组，每项包含：

| 字段 | 说明 |
|---|---|
| `id` | 记录ID |
| `code` | 编码 |
| `name` | 名称 |
| `spell` | 拼音码 |
| `pId` | 父级ID（Branch 为所属品牌ID，其他类型可能为空） |
| `pName` | 父级名称 |

### 调用示例

**示例 1**：查询所有门店
```json
{
  "dict_type": "Branch"
}
```

**示例 2**：按名称模糊查找门店（支持拼音码）
```json
{
  "dict_type": "Branch",
  "name": "朝阳"
}
```

**示例 3**：精确查询指定品牌
```json
{
  "dict_type": "Brand",
  "id": "66400620"
}
```

**示例 4**：查询菜品大类
```json
{
  "dict_type": "DishCategory"
}
```

### 典型两步调用流程

用户问："查询**海底捞朝阳店**本月的营业收入"

1. **第一步**：调用 `query_dict(dict_type="Branch", name="朝阳")` → 得到 branch_id
2. **第二步**：调用 `query_sale_income(begin_date="2026-09-01", end_date="2026-09-22", branch_id="30000001", date_flag="1")`

### 认证说明

- 首次调用需要完成 SSO 登录授权
- 未授权时调用会返回包含登录链接的错误信息

## 工具：search_dish

菜品搜索。按关键词模糊搜索商户菜品库，返回匹配菜品的 ID/编码/名称/拼音码，用于为报表工具获取 `dish_id` 入参。

> 与 `query_dict` 的区别：菜品数据量大（数百至数千条），不适合全量下拉查询，因此采用关键词搜索，最多返回 50 条。

### 参数说明

| 参数名 | 类型 | 必填 | 枚举值 | 说明 |
|---|---|---|---|---|
| `keyword` | string | ✅ | — | 搜索关键词，支持菜品名称/编码/拼音码模糊匹配，如 `"番茄"`、`"D001"`、`"fq"`（不区分大小写） |
| `dish_mode` | string | — | `0`(默认), `1`, `2` | 菜品范围：0=全部，1=仅单品，2=仅套餐 |
| `category_id` | string | — | — | 菜品大类ID，可通过 `query_dict(dict_type="DishCategory")` 获取 |

### 返回结构

返回数组，每项包含：

| 字段 | 说明 |
|---|---|
| `dishId` | 菜品ID（作为报表工具 dish_id 入参） |
| `dishCode` | 菜品编码 |
| `dishName` | 菜品名称 |
| `spellCode` | 拼音简码 |
| `categoryId` / `typeId` | 菜品大类/类型 ID |
| `isCombo` | 是否套餐：0=单品，1=套餐 |

### 调用示例

**示例 1**：搜索“番茄”相关菜品
```json
{
  "keyword": "番茄"
}
```

**示例 2**：搜索套餐类菜品
```json
{
  "keyword": "龙虾",
  "dish_mode": "2"
}
```

### 典型两步调用流程

用户问：“查一下**香辣小龙虾**上周的销量”

1. **第一步**：`search_dish(keyword="香辣小龙虾")` → 得到 dishId
2. **第二步**：`query_dish_sum(begin_date=..., end_date=..., dish_id=<dishId>)`
