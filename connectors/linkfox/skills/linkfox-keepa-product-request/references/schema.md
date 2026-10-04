# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin",
    "domain"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "examples": [
        {
          "value": "B0088PUEPK",
          "summary": "单个ASIN"
        },
        {
          "value": "B0088PUEPK,B00U26V4VQ,B07M68S376",
          "summary": "多个ASIN，用英文逗号分隔，最多100个"
        }
      ],
      "maxLength": 3000,
      "description": "亚马逊标准识别号(ASIN)，多个ASIN，用英文逗号分隔，最多100个"
    },
    "domain": {
      "type": "string",
      "pattern": "1|2|3|4|5|6|8|9|10|11|12",
      "examples": [
        {
          "value": "1",
          "summary": "Amazon.com (美国)"
        },
        {
          "value": "2",
          "summary": "Amazon.co.uk (英国)"
        },
        {
          "value": "3",
          "summary": "Amazon.de (德国)"
        },
        {
          "value": "4",
          "summary": "Amazon.fr (法国)"
        },
        {
          "value": "5",
          "summary": "Amazon.co.jp (日本)"
        },
        {
          "value": "6",
          "summary": "Amazon.ca (加拿大)"
        },
        {
          "value": "8",
          "summary": "Amazon.it (意大利)"
        },
        {
          "value": "9",
          "summary": "Amazon.es (西班牙)"
        },
        {
          "value": "10",
          "summary": "Amazon.in (印度)"
        },
        {
          "value": "11",
          "summary": "Amazon.com.mx (墨西哥)"
        },
        {
          "value": "12",
          "summary": "Amazon.com.br (巴西)"
        }
      ],
      "description": "亚马逊域名ID"
    },
    "history": {
      "type": "integer",
      "default": 0,
      "examples": [
        {
          "value": "1",
          "summary": "包含价格历史、销售排名、历史销量等时间序列数据（前几个月的销量）"
        },
        {
          "value": "0",
          "summary": "仅返回基本商品信息"
        }
      ],
      "description": "返回值是否包含历史数据,历史销量"
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
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "总行数"
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
    "perPage": {
      "type": "integer",
      "description": "每页数量"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "asin": {
            "type": "string",
            "description": "ASIN"
          },
          "brand": {
            "type": "string",
            "description": "品牌"
          },
          "color": {
            "type": "string",
            "description": "颜色"
          },
          "model": {
            "type": "string",
            "description": "型号"
          },
          "price": {
            "type": "number",
            "description": "当前价格（单位：元，如美元/欧元等）"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "profit": {
            "type": "number",
            "description": "利润率（百分比，如25.5表示25.5%）"
          },
          "rating": {
            "type": "number",
            "description": "当前评分（0.0-5.0，如4.5星）"
          },
          "weight": {
            "type": "string",
            "description": "重量（克）"
          },
          "asinUrl": {
            "type": "string",
            "description": "亚马逊asin的详情网址"
          },
          "fbaFees": {
            "type": "number",
            "description": "FBA配送费（单位：元）"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数量"
          },
          "urlSlug": {
            "type": "string",
            "description": "URL Slug"
          },
          "currency": {
            "type": "string",
            "description": "币种"
          },
          "imageUrl": {
            "type": "string",
            "description": "图片URL（完整URL）"
          },
          "isHazmat": {
            "type": "boolean",
            "description": "是否为危险品"
          },
          "material": {
            "type": "string",
            "description": "产品的材质，指其构造中使用的主要材料"
          },
          "dimension": {
            "type": "string",
            "description": "尺寸"
          },
          "itemWidth": {
            "type": "integer",
            "description": "商品宽度，单位为毫米，不可用时为0或-1。示例: 100"
          },
          "salesRank": {
            "type": "integer",
            "description": "销售排名"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数"
          },
          "itemHeight": {
            "type": "integer",
            "description": "商品高度，单位为毫米，不可用时为0或-1。示例: 100"
          },
          "itemLength": {
            "type": "integer",
            "description": "商品长度，单位为毫米，不可用时为0或-1。示例: 100"
          },
          "lastUpdate": {
            "type": "string",
            "description": "最后更新时间（yyyy-MM-dd HH:mm:ss）"
          },
          "parentAsin": {
            "type": "string",
            "description": "父ASIN"
          },
          "primePrice": {
            "type": "number",
            "description": "prime价格"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型：keepa"
          },
          "fulfillment": {
            "type": "string",
            "description": "配送方式(AMZ,FBA,FBM)"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论数量"
          },
          "salesRank30": {
            "type": "integer",
            "description": "近30天平均销售排名"
          },
          "salesRank90": {
            "type": "integer",
            "description": "近90天平均销售排名"
          },
          "categoryTree": {
            "type": "string",
            "description": "类目树"
          },
          "manufacturer": {
            "type": "string",
            "description": "制造商"
          },
          "packageWidth": {
            "type": "integer",
            "description": "包装宽度（毫米）"
          },
          "rootCategory": {
            "type": "integer",
            "description": "根类目ID"
          },
          "salesRank180": {
            "type": "integer",
            "description": "近180天平均销售排名"
          },
          "variationNum": {
            "type": "integer",
            "description": "变体数量"
          },
          "availableDate": {
            "type": "string",
            "description": "上架时间（yyyy-MM-dd HH:mm:ss）"
          },
          "packageHeight": {
            "type": "integer",
            "description": "包装高度（毫米）"
          },
          "packageLength": {
            "type": "integer",
            "description": "包装长度（毫米）"
          },
          "packageWeight": {
            "type": "string",
            "description": "包装重量（克）"
          },
          "subcategories": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "code": {
                  "type": "string",
                  "description": "类目ID"
                },
                "rank": {
                  "type": "integer",
                  "description": "排名"
                },
                "label": {
                  "type": "string",
                  "description": "类目名称"
                }
              }
            },
            "description": "子类目列表"
          },
          "buyBoxSellerId": {
            "type": "string",
            "description": "购买按钮卖家ID"
          },
          "categoryTreeId": {
            "type": "string",
            "description": "类目树Id"
          },
          "dimensionsType": {
            "type": "string",
            "description": "尺寸类型"
          },
          "isAdultProduct": {
            "type": "boolean",
            "description": "是否为成人产品"
          },
          "packageQuantity": {
            "type": "integer",
            "description": "包装中商品的数量，不可用时为0或-1。示例: 3"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "商品图片列表"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量"
          },
          "packageDimensions": {
            "type": "string",
            "description": "包装尺寸"
          },
          "monthlySalesRevenue": {
            "type": "number",
            "description": "月销售额"
          },
          "referralFeePercentage": {
            "type": "number",
            "description": "推荐费百分比"
          },
          "monthlySalesUnits1MonthAgo": {
            "type": "integer",
            "description": "1月前月销量"
          },
          "monthlySalesUnits2MonthsAgo": {
            "type": "integer",
            "description": "2月前月销量"
          },
          "monthlySalesUnits3MonthsAgo": {
            "type": "integer",
            "description": "3月前月销量"
          },
          "monthlySalesUnits4MonthsAgo": {
            "type": "integer",
            "description": "4月前月销量"
          },
          "monthlySalesUnits5MonthsAgo": {
            "type": "integer",
            "description": "5月前月销量"
          },
          "monthlySalesUnits6MonthsAgo": {
            "type": "integer",
            "description": "6月前月销量"
          },
          "monthlySalesUnits7MonthsAgo": {
            "type": "integer",
            "description": "7月前月销量"
          },
          "monthlySalesUnits8MonthsAgo": {
            "type": "integer",
            "description": "8月前月销量"
          },
          "monthlySalesUnits9MonthsAgo": {
            "type": "integer",
            "description": "9月前月销量"
          },
          "monthlySalesUnits10MonthsAgo": {
            "type": "integer",
            "description": "10月前月销量"
          },
          "monthlySalesUnits11MonthsAgo": {
            "type": "integer",
            "description": "11月前月销量"
          },
          "monthlySalesUnits12MonthsAgo": {
            "type": "integer",
            "description": "12月前月销量"
          }
        }
      },
      "description": "商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型：keepa"
    },
    "totalCount": {
      "type": "integer",
      "description": "总数量"
    },
    "currentPage": {
      "type": "integer",
      "description": "当前页码"
    }
  }
}
```

</details>
