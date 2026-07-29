# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "nodeIdPath"
  ],
  "properties": {
    "topN": {
      "type": "integer",
      "default": 10,
      "description": "头部Listing数量"
    },
    "month": {
      "type": "string",
      "pattern": "^(nearly|(19|20)\\d{2}(0[1-9]|1[0-2]))$",
      "examples": [
        {
          "value": "nearly",
          "summary": "最近30天"
        },
        {
          "value": "202507",
          "summary": "具体月份 yyyyMM"
        }
      ],
      "description": "筛选日期。支持两种写法：① nearly — 最近30天；② yyyyMM — 查询具体月份（如 202507），最多支持当前月往前共24个月内的月份"
    },
    "newProduct": {
      "type": "integer",
      "default": 6,
      "description": "新品定义(月)"
    },
    "nodeIdPath": {
      "type": "string",
      "maxLength": 1000,
      "description": "节点ID路径字符串，如 1064954:1069242:1069784:1069820:1069838:1069828"
    },
    "marketplace": {
      "type": "string",
      "default": "US",
      "examples": [
        {
          "value": "US",
          "summary": "美国站 USD($)"
        },
        {
          "value": "JP",
          "summary": "日本站 JPY(￥)"
        },
        {
          "value": "UK",
          "summary": "英国站 GBP(£)"
        },
        {
          "value": "DE",
          "summary": "德国站 EUR(€)"
        },
        {
          "value": "FR",
          "summary": "法国站 EUR(€)"
        },
        {
          "value": "IT",
          "summary": "意大利站 EUR(€)"
        },
        {
          "value": "ES",
          "summary": "西班牙站 EUR(€)"
        },
        {
          "value": "CA",
          "summary": "加拿大站 C$($)"
        },
        {
          "value": "IN",
          "summary": "印度站 INR(₹)"
        }
      ],
      "maxLength": 1000,
      "description": "站点编码(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹)"
    }
  }
}
```

</details>

## 原始 Output Schema

<details>
<summary>展开查看完整 Output Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "avgBsr": {
            "type": "integer",
            "description": "平均BSR"
          },
          "brands": {
            "type": "integer",
            "description": "品牌数"
          },
          "sellers": {
            "type": "integer",
            "description": "卖家数"
          },
          "avgPrice": {
            "type": "number",
            "description": "平均价格"
          },
          "avgUnits": {
            "type": "integer",
            "description": "月均销量"
          },
          "currency": {
            "type": "string",
            "description": "该市场的货币类型"
          },
          "hlAvgBsr": {
            "type": "integer",
            "description": "头部Listing前N名商品平均BSR"
          },
          "products": {
            "type": "integer",
            "description": "样品商品数"
          },
          "avgProfit": {
            "type": "number",
            "description": "平均利润率"
          },
          "avgRating": {
            "type": "number",
            "description": "平均星级"
          },
          "avgVolume": {
            "type": "number",
            "description": "平均体积(in³)"
          },
          "avgWeight": {
            "type": "number",
            "description": "平均重量(pound)"
          },
          "avgRatings": {
            "type": "integer",
            "description": "平均评分数"
          },
          "avgRevenue": {
            "type": "number",
            "description": "月均销售额"
          },
          "avgSellers": {
            "type": "number",
            "description": "平均卖家数"
          },
          "hlAvgPrice": {
            "type": "number",
            "description": "头部Listing前N名商品平均价格"
          },
          "hlAvgUnits": {
            "type": "integer",
            "description": "头部Listing前N名商品月均销量"
          },
          "hlProducts": {
            "type": "integer",
            "description": "头部Listing前N名商品样本数"
          },
          "nodeIdPath": {
            "type": "string",
            "description": "节点ID路径"
          },
          "countryCode": {
            "type": "string",
            "description": "国家二简码"
          },
          "hlAvgRating": {
            "type": "number",
            "description": "头部Listing前N名商品平均星级"
          },
          "marketplace": {
            "type": "string",
            "description": "市场标志"
          },
          "newAvgPrice": {
            "type": "number",
            "description": "新品平均价格"
          },
          "newAvgUnits": {
            "type": "integer",
            "description": "新品月均销量"
          },
          "newProducts": {
            "type": "integer",
            "description": "新品数量"
          },
          "avgRatingsCv": {
            "type": "integer",
            "description": "月评论平均增长数"
          },
          "hlAvgRatings": {
            "type": "integer",
            "description": "头部Listing前N名商品平均评论数"
          },
          "hlAvgRevenue": {
            "type": "number",
            "description": "头部Listing前N名商品月均销售额"
          },
          "newAvgRating": {
            "type": "number",
            "description": "新品平均星级"
          },
          "baseAvgVolume": {
            "type": "number",
            "description": "平均体积(cm³)"
          },
          "baseAvgWeight": {
            "type": "number",
            "description": "平均重量(g)"
          },
          "lastShelfDate": {
            "type": "string",
            "description": "商品最新上架日期"
          },
          "maxNewRatings": {
            "type": "integer",
            "description": "最高新品评分数"
          },
          "minNewRatings": {
            "type": "integer",
            "description": "最低新品评分数"
          },
          "newAvgRatings": {
            "type": "integer",
            "description": "新品平均评分数"
          },
          "newAvgRevenue": {
            "type": "number",
            "description": "新品月均销售额"
          },
          "nodeLabelPath": {
            "type": "string",
            "description": "节点名称路径"
          },
          "totalProducts": {
            "type": "integer",
            "description": "商品总数"
          },
          "firstShelfDate": {
            "type": "string",
            "description": "商品首次上架日期"
          },
          "hlAvgRatingsCv": {
            "type": "integer",
            "description": "头部Listing前N名商品月评论平均增长数"
          },
          "nodeLabelLocale": {
            "type": "string",
            "description": "节点名称翻译"
          },
          "nodeLabelPathLocale": {
            "type": "string",
            "description": "节点名称路径翻译"
          },
          "newProductProportion": {
            "type": "number",
            "description": "新品数量占比"
          }
        }
      },
      "description": "统计结果列表(对应第三方 data)"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "总条数"
    },
    "columns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "渲染的列"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "marketplace": {
      "type": "string",
      "description": "站点编码"
    }
  }
}
```

</details>
