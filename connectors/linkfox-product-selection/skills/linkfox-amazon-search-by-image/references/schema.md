# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "amazonDomain",
    "imageUrl"
  ],
  "properties": {
    "sort": {
      "type": "string",
      "pattern": "default|price-asc-rank|price-desc-rank|rating-asc-rank|rating-desc-rank|ratings-asc-rank|ratings-desc-rank",
      "examples": [
        {
          "value": "default",
          "summary": "默认"
        },
        {
          "value": "price-asc-rank",
          "summary": "价格：从低到高"
        },
        {
          "value": "price-desc-rank",
          "summary": "价格：从高到低"
        },
        {
          "value": "rating-asc-rank",
          "summary": "评分：从低到高"
        },
        {
          "value": "rating-desc-rank",
          "summary": "评分：从高到低"
        },
        {
          "value": "ratings-asc-rank",
          "summary": "评论数：从低到高"
        },
        {
          "value": "ratings-desc-rank",
          "summary": "评论数：从高到低"
        }
      ],
      "description": "排序, 支持价格，评分，评论数排序"
    },
    "imageUrl": {
      "type": "string",
      "examples": [
        {
          "value": "https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg",
          "summary": "图片URL"
        }
      ],
      "maxLength": 1000,
      "description": "图片URL地址,请确保图片URL地址有效"
    },
    "deliveryZip": {
      "type": "string",
      "examples": [
        {
          "value": "10001",
          "summary": "美国站默认邮编"
        },
        {
          "value": "EC1A 1BB",
          "summary": "英国站默认邮编"
        },
        {
          "value": "10115",
          "summary": "德国站默认邮编"
        },
        {
          "value": "75001",
          "summary": "法国站默认邮编"
        },
        {
          "value": "00100",
          "summary": "意大利站默认邮编"
        },
        {
          "value": "28001",
          "summary": "西班牙站默认邮编"
        },
        {
          "value": "100-0001",
          "summary": "日本站默认邮编"
        },
        {
          "value": "110034",
          "summary": "印度站默认邮编"
        }
      ],
      "maxLength": 1000,
      "description": "站内收货地址邮编或城市，如果用户未指定，则取站点（国家）的默认邮编。例如：亚马逊美国站取邮编10001。"
    },
    "amazonDomain": {
      "type": "string",
      "pattern": "amazon.com|amazon.co.uk|amazon.de|amazon.fr|amazon.it|amazon.es|amazon.co.jp|amazon.in",
      "examples": [
        {
          "value": "amazon.com",
          "summary": "亚马逊美国站"
        },
        {
          "value": "amazon.co.uk",
          "summary": "亚马逊英国站"
        },
        {
          "value": "amazon.de",
          "summary": "亚马逊德国站"
        },
        {
          "value": "amazon.fr",
          "summary": "亚马逊法国站"
        },
        {
          "value": "amazon.it",
          "summary": "亚马逊意大利站"
        },
        {
          "value": "amazon.es",
          "summary": "亚马逊西班牙站"
        },
        {
          "value": "amazon.co.jp",
          "summary": "亚马逊日本站"
        },
        {
          "value": "amazon.in",
          "summary": "亚马逊印度站"
        }
      ],
      "description": "亚马逊站点，仅支持以下站点：美国，英国，德国，法国，意大利，西班牙，日本，印度。默认 amazon.com"
    },
    "countryOrAreaCode": {
      "type": "string",
      "examples": [
        {
          "value": "CN",
          "summary": "中国"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "KR",
          "summary": "韩国"
        },
        {
          "value": "TW",
          "summary": "台湾"
        },
        {
          "value": "HK",
          "summary": "香港"
        },
        {
          "value": "MO",
          "summary": "澳门"
        },
        {
          "value": "SG",
          "summary": "新加坡"
        },
        {
          "value": "TH",
          "summary": "泰国"
        },
        {
          "value": "VN",
          "summary": "越南"
        },
        {
          "value": "PH",
          "summary": "菲律宾"
        },
        {
          "value": "MY",
          "summary": "马来西亚"
        }
      ],
      "maxLength": 1000,
      "description": "站外收货的国家代码，站内邮编地址和站外国家地区代码不能同时指定。注意：印度站不支持设置站外国家或地区收货"
    },
    "aggregateByKeepaData": {
      "type": "boolean",
      "description": "是否聚合Keepa数据"
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
            "description": "颜色(keepa)"
          },
          "model": {
            "type": "string",
            "description": "型号(keepa)"
          },
          "price": {
            "type": "number",
            "description": "当前价格.（单位：元，如美元/欧元等）"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "profit": {
            "type": "number",
            "description": "利润率(keepa).（利润率百分比，如25.5表示25.5%）"
          },
          "rating": {
            "type": "number",
            "description": "当前评分.（0.0-5.0，如4.5星）"
          },
          "weight": {
            "type": "string",
            "description": "重量（克）(keepa)"
          },
          "asinUrl": {
            "type": "string",
            "description": "亚马逊asin的详情网址"
          },
          "fbaFees": {
            "type": "number",
            "description": "FBA配送费(keepa).（单位：元）"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数量"
          },
          "urlSlug": {
            "type": "string",
            "description": "URL Slug(keepa)"
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
            "description": "是否为危险品(keepa)"
          },
          "material": {
            "type": "string",
            "description": "产品的材质(keepa).指其构造中使用的主要材料"
          },
          "oldPrice": {
            "type": "number",
            "description": "划线价格"
          },
          "dimension": {
            "type": "string",
            "description": "尺寸(keepa)"
          },
          "itemWidth": {
            "type": "integer",
            "description": "商品宽度(keepa).单位为毫米，不可用时为0或-1。示例: 100"
          },
          "salesRank": {
            "type": "integer",
            "description": "销售排名(keepa)"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数(keepa)"
          },
          "itemHeight": {
            "type": "integer",
            "description": "商品高度(keepa).单位为毫米，不可用时为0或-1。示例: 100"
          },
          "itemLength": {
            "type": "integer",
            "description": "商品长度(keepa).单位为毫米，不可用时为0或-1。示例: 100"
          },
          "lastUpdate": {
            "type": "string",
            "description": "最后更新时间(keepa).（yyyy-MM-dd HH:mm:ss）"
          },
          "parentAsin": {
            "type": "string",
            "description": "父ASIN(keepa)"
          },
          "primePrice": {
            "type": "number",
            "description": "prime价格(keepa)"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型"
          },
          "fulfillment": {
            "type": "string",
            "description": "配送方式(AMZ,FBA,FBM)(keepa)"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论数量(keepa)"
          },
          "salesRank30": {
            "type": "integer",
            "description": "近30天平均销售排名(keepa)"
          },
          "salesRank90": {
            "type": "integer",
            "description": "近90天平均销售排名(keepa)"
          },
          "categoryTree": {
            "type": "string",
            "description": "类目树(keepa)"
          },
          "manufacturer": {
            "type": "string",
            "description": "制造商(keepa)"
          },
          "packageWidth": {
            "type": "integer",
            "description": "包装宽度（毫米）(keepa)"
          },
          "rootCategory": {
            "type": "integer",
            "description": "根类目ID(keepa)"
          },
          "salesRank180": {
            "type": "integer",
            "description": "近180天平均销售排名(keepa)"
          },
          "variationNum": {
            "type": "integer",
            "description": "变体数量(keepa)"
          },
          "availableDate": {
            "type": "string",
            "description": "上架时间(keepa).（yyyy-MM-dd HH:mm:ss）"
          },
          "packageHeight": {
            "type": "integer",
            "description": "包装高度（毫米）(keepa)"
          },
          "packageLength": {
            "type": "integer",
            "description": "包装长度（毫米）(keepa)"
          },
          "packageWeight": {
            "type": "string",
            "description": "包装重量（克）(keepa)"
          },
          "buyBoxSellerId": {
            "type": "string",
            "description": "购买按钮卖家ID(keepa)"
          },
          "categoryTreeId": {
            "type": "string",
            "description": "类目树Id(keepa)"
          },
          "dimensionsType": {
            "type": "string",
            "description": "尺寸类型(keepa)"
          },
          "isAdultProduct": {
            "type": "boolean",
            "description": "是否为成人产品(keepa)"
          },
          "packageQuantity": {
            "type": "integer",
            "description": "包装中商品的数量(keepa).不可用时为0或-1。示例: 3"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "商品图片列表(keepa)"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量(keepa)"
          },
          "packageDimensions": {
            "type": "string",
            "description": "包装尺寸(keepa)"
          },
          "monthlySalesRevenue": {
            "type": "number",
            "description": "月销售额(keepa)"
          },
          "referralFeePercentage": {
            "type": "number",
            "description": "推荐费百分比(keepa)"
          },
          "monthlySalesUnits1MonthAgo": {
            "type": "integer",
            "description": "1月前月销量(keepa)"
          },
          "monthlySalesUnits2MonthsAgo": {
            "type": "integer",
            "description": "2月前月销量(keepa)"
          },
          "monthlySalesUnits3MonthsAgo": {
            "type": "integer",
            "description": "3月前月销量(keepa)"
          },
          "monthlySalesUnits4MonthsAgo": {
            "type": "integer",
            "description": "4月前月销量(keepa)"
          },
          "monthlySalesUnits5MonthsAgo": {
            "type": "integer",
            "description": "5月前月销量(keepa)"
          },
          "monthlySalesUnits6MonthsAgo": {
            "type": "integer",
            "description": "6月前月销量(keepa)"
          },
          "monthlySalesUnits7MonthsAgo": {
            "type": "integer",
            "description": "7月前月销量(keepa)"
          },
          "monthlySalesUnits8MonthsAgo": {
            "type": "integer",
            "description": "8月前月销量(keepa)"
          },
          "monthlySalesUnits9MonthsAgo": {
            "type": "integer",
            "description": "9月前月销量(keepa)"
          },
          "monthlySalesUnits10MonthsAgo": {
            "type": "integer",
            "description": "10月前月销量(keepa)"
          },
          "monthlySalesUnits11MonthsAgo": {
            "type": "integer",
            "description": "11月前月销量(keepa)"
          },
          "monthlySalesUnits12MonthsAgo": {
            "type": "integer",
            "description": "12月前月销量(keepa)"
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
      "description": "来源类型"
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
