# 市场分析类工具 API 详情

## 目录
- [get_top_purchasers - Top采购单位](#get_top_purchasers)
- [get_top_suppliers - Top中标单位](#get_top_suppliers)
- [get_top_brands - Top中标品牌](#get_top_brands)
- [aggregate_bids_advanced - 多维度聚合统计](#aggregate_bids_advanced)
- [get_price_trends - 品牌型号价格查询](#get_price_trends)

---

## get_top_purchasers - Top采购单位 {#get_top_purchasers}

按关键词查询Top采购单位（精准获客、市场调研）。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `keywords` | list[str] | 必填，业务关键词 |
| `match_modes` | list[str] | 匹配模式，默认 `["all"]` |
| `begin_date` | str | 统计开始日期 |
| `end_date` | str | 统计结束日期 |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `exclude_keywords` | list[str] | 排除关键词 |
| `min_amount` | float | 最低金额（元，本类工具不做万元转换） |
| `max_amount` | float | 最高金额（元，本类工具不做万元转换） |
| `limit` | int | 返回数量，默认20，最大100 |
| `sort_field` | str | 排序字段：`count`/`amount`/`pub_time`，默认 `count` |

### 响应结构

```json
{
  "data": {
    "total": 100,
    "items": [
      {
        "company_name": "XX市人民政府",
        "company_id": 1234567890,
        "purchase_count": 50,
        "total_amount": 100000000,
        "total_amount_wan": 10000,
        "latest_purchase_time": "2025-01-10",
        "top_winners": [{"winner": "华为技术有限公司", "count": 10}],
        "company_url": "https://www.zhiliaobiaoxun.com/company/1234567890"
      }
    ]
  }
}
```

### 示例

**查找北京地区AI采购大户（按金额排序）**：
```json
{
  "keywords": ["人工智能", "AI"],
  "provinces": ["北京"],
  "min_amount": 1000000,
  "sort_field": "amount"
}
```

---

## get_top_suppliers - Top中标单位 {#get_top_suppliers}

按关键词查询Top中标单位（渠道扩展、竞对分析）。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `keywords` | list[str] | 必填，业务关键词 |
| `match_modes` | list[str] | 匹配模式，默认 `["all"]` |
| `begin_date` | str | 统计开始日期 |
| `end_date` | str | 统计结束日期 |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `exclude_keywords` | list[str] | 排除关键词 |
| `min_amount` | float | 最低金额（元，本类工具不做万元转换） |
| `max_amount` | float | 最高金额（元，本类工具不做万元转换） |
| `limit` | int | 返回数量，默认20，最大100 |
| `sort_field` | str | 排序字段：`count`/`amount`/`pub_time`，默认 `count` |

### 响应结构

```json
{
  "data": {
    "total": 100,
    "items": [
      {
        "company_name": "华为技术有限公司",
        "win_count": 100,
        "total_amount": 500000000,
        "total_amount_wan": 50000,
        "latest_win_time": "2025-01-10",
        "top_provinces": [{"province": "北京", "count": 30}],
        "top_callers": [{"caller": "中国移动", "count": 15}],
        "company_url": "https://www.zhiliaobiaoxun.com/company/1234567890"
      }
    ]
  }
}
```

### 示例

**查找服务器Top供应商（按中标金额排序，排除维保）**：
```json
{
  "keywords": ["服务器"],
  "exclude_keywords": ["维修", "维保"],
  "sort_field": "amount"
}
```

---

## get_top_brands - Top中标品牌 {#get_top_brands}

按产品/品类查询Top中标品牌及型号。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `product` | str | 必填，产品名称，如 `"呼吸机"` |
| `exclude_keywords` | list[str] | 排除关键词 |
| `min_price` | float | 最低价格（元） |
| `max_price` | float | 最高价格（元） |
| `begin_date` | str | 统计开始日期 |
| `end_date` | str | 统计结束日期 |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `counties` | list[str] | 区县列表 |
| `limit` | int | 返回品牌数量，默认10，最大50 |

### 响应结构

```json
{
  "data": {
    "product": "呼吸机",
    "total": 20,
    "brands": [
      {
        "brand": "迈瑞",
        "win_count": 500,
        "total_amount": 100000000,
        "avg_price": 50000,
        "avg_price_wan": 5,
        "top_models": ["SV300", "BeneVision T1"],
        "last_win_time": "2025-01-10"
      }
    ]
  }
}
```

### 示例

**查询服务器品牌市场占有率**：
```json
{
  "product": "服务器",
  "begin_date": "2024-01-01",
  "exclude_keywords": ["维修", "耗材"],
  "limit": 20
}
```

---

## aggregate_bids_advanced - 多维度聚合统计 {#aggregate_bids_advanced}

按月/季/年/省份/城市/行业/品牌等维度进行招中标数据统计分析。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `filters` | object | 筛选条件 |
| `filters.keywords` | list[str] | 关键词 |
| `filters.match_modes` | list[str] | 匹配模式 |
| `filters.keyword_groups` | list[dict] | 关键词组 |
| `filters.exclude_keywords` | list[str] | 排除关键词 |
| `filters.bid_type` | int | 1=招标 2=中标 |
| `filters.begin_date` | str | 开始日期 |
| `filters.end_date` | str | 结束日期 |
| `filters.provinces` | list[str] | 省份列表 |
| `filters.cities` | list[str] | 城市列表 |
| `filters.min_money` | float | 最低金额（元） |
| `filters.max_money` | float | 最高金额（元） |
| `group_by` | list[str] | **必填**，聚合维度 |
| `metrics` | list[str] | 统计指标，默认 `["count", "sum_amount"]` |
| `compare_with` | str | 对比类型：`yoy`=同比，`qoq`=环比 |

### group_by 可选值

| 值 | 说明 |
|---|------|
| `month` | 按月统计 |
| `quarter` | 按季度统计 |
| `year` | 按年统计 |
| `province` | 按省份统计 |
| `city` | 按城市统计 |
| `industry` | 按采购行业统计 |
| `brand` | 按品牌统计 |
| `company_type` | 按招标公司类型 |
| `bid_method` | 按采购方式 |

### 响应结构

```json
{
  "data": {
    "total_count": 1000,
    "total_amount": 5000000000,
    "total_amount_wan": 500000,
    "buckets": [
      {
        "key": "2025-01",
        "count": 100,
        "sum_amount": 500000000,
        "sum_amount_wan": 50000,
        "avg_amount": 5000000,
        "yoy_count": 10.5,
        "yoy_amount": 15.3
      }
    ],
    "group_by": ["month"]
  }
}
```

### 示例

**按月统计大语言模型中标趋势（同比分析）**：
```json
{
  "filters": {
    "keywords": ["大语言模型"],
    "bid_type": 2,
    "begin_date": "2024-01-01"
  },
  "group_by": ["month"],
  "compare_with": "yoy"
}
```

**按省份统计服务器市场**：
```json
{
  "filters": {
    "keywords": ["服务器"],
    "begin_date": "2024-01-01"
  },
  "group_by": ["province"]
}
```

**按品牌统计某产品市场份额**：
```json
{
  "filters": {
    "keywords": ["呼吸机"],
    "bid_type": 2
  },
  "group_by": ["brand"]
}
```

---

## get_price_trends - 品牌型号价格查询 {#get_price_trends}

查询品牌+型号的历史中标单价记录（采购寻源、价格参考）。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `brand` | str | **必填**，品牌名称，如 `"联想"` |
| `model` | str | 型号，如 `"SV300"` |
| `product` | str | 产品类别，如 `"呼吸机"` |
| `exclude_keywords` | list[str] | 排除关键词 |
| `min_price` | float | 最低价格（元） |
| `max_price` | float | 最高价格（元） |
| `begin_date` | str | 统计开始日期 |
| `end_date` | str | 统计结束日期 |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `counties` | list[str] | 区县列表 |
| `limit` | int | 返回记录数量，默认20，最大200 |

### 响应结构

```json
{
  "data": {
    "brand": "迈瑞",
    "model": "SV300",
    "total": 50,
    "price_stats": {
      "min": 30000,
      "max": 80000,
      "avg": 50000,
      "median": 48000
    },
    "records": [
      {
        "bid_id": 12345678,
        "sm_name": "呼吸机",
        "brand": "迈瑞",
        "model": "SV300",
        "sku_price": 50000,
        "sku_count": 5,
        "sku_total_money": 250000,
        "caller_name": "XX市人民医院",
        "pub_time": "2025-01-10",
        "province": "广东",
        "winner_names": ["XX医疗器械公司"],
        "url": "https://www.zhiliaobiaoxun.com/content/12345678/b1"
      }
    ]
  }
}
```

### 示例

**查询迈瑞SV300呼吸机历史中标价格**：
```json
{
  "brand": "迈瑞",
  "model": "SV300",
  "product": "呼吸机",
  "exclude_keywords": ["耗材", "维修", "维保"]
}
```

**查询某品牌服务器近一年价格区间**：
```json
{
  "brand": "联想",
  "product": "服务器",
  "begin_date": "2025-01-01",
  "limit": 50
}
```