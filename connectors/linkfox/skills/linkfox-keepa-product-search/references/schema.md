# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "domain"
  ],
  "properties": {
    "page": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "第一页"
        },
        {
          "value": "2",
          "summary": "第二页"
        }
      ],
      "description": "页码（从1开始）"
    },
    "size": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"large\", \"XL\"]",
          "summary": "大号或特大号尺码的产品"
        }
      ],
      "maxItems": 1000,
      "description": "尺码(OR匹配)，筛选指定尺码的产品"
    },
    "sort": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "fieldName",
          "sortDirection"
        ],
        "properties": {
          "fieldName": {
            "type": "string",
            "pattern": "availableDate|currentSales|monthlySold|currentRating|currentCountReviews|currentBuyBoxShipping|currentNew",
            "examples": [
              {
                "value": "currentSales",
                "summary": "当前销售排名"
              },
              {
                "value": "monthlySold",
                "summary": "销量/月销量"
              },
              {
                "value": "availableDate",
                "summary": "上架时间"
              },
              {
                "value": "currentRating",
                "summary": "当前评分"
              },
              {
                "value": "currentCountReviews",
                "summary": "当前评论数"
              },
              {
                "value": "currentBuyBoxShipping",
                "summary": "当前购买按钮含运费价格"
              },
              {
                "value": "currentNew",
                "summary": "当前新品价格"
              }
            ],
            "description": "排序字段名（驼峰格式），只允许以下值：listedSince(上架时间)、currentSales(当前销售排名)、monthlySold(销量/月销量)、currentRating(当前评分)、currentCountReviews(当前评论数)、currentBuyBoxShipping(当前购买按钮含运费价格)、currentAmazon(当前亚马逊自营价格)、currentNew(当前新品价格)"
          },
          "sortDirection": {
            "type": "string",
            "pattern": "asc|desc",
            "examples": [
              {
                "value": "asc",
                "summary": "升序"
              },
              {
                "value": "desc",
                "summary": "降序"
              }
            ],
            "description": "排序方向：asc=升序，desc=降序"
          }
        }
      },
      "maxItems": 1000,
      "description": "排序(最多3)：对象数组；每项包含 fieldName 与 sortDirection"
    },
    "brand": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"Canon\"]",
          "summary": "Canon"
        },
        {
          "value": "[\"Apple\", \"Samsung\"]",
          "summary": "Apple或Samsung"
        }
      ],
      "maxItems": 1000,
      "description": "品牌(OR匹配)"
    },
    "color": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"black\", \"red\"]",
          "summary": "黑色或红色产品"
        }
      ],
      "maxItems": 1000,
      "description": "颜色(OR匹配)，筛选指定颜色的产品"
    },
    "domain": {
      "type": "string",
      "pattern": "1|2|3|4|5|6|8|9|10|11",
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
        }
      ],
      "description": "Amazon域名ID"
    },
    "rating": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "0",
          "summary": "不获取评分信息"
        },
        {
          "value": "1",
          "summary": "获取评分信息"
        }
      ],
      "description": "是否获取评分信息（默认 1 获取，0 不获取）"
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
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "Digital Camera Canon",
          "summary": "包含Digital、Camera和Canon三个关键词，顺序不限"
        },
        {
          "value": "\"Digital Camera\" Canon",
          "summary": "包含完整短语\"Digital Camera\"和关键词Canon，注意短语用双引号包裹"
        },
        {
          "value": "-digital camera",
          "summary": "不包含digital但包含camera"
        }
      ],
      "maxLength": 1000,
      "description": "标题关键词(大小写不敏感；空格表示分词AND；关键词本身包含空格时用双引号包裹；支持前缀-排除；如果含有 & 符号会被替换为空格；最多50个关键词)"
    },
    "perPage": {
      "type": "integer",
      "default": 50,
      "maximum": 100,
      "minimum": 50,
      "examples": [
        {
          "value": "50",
          "summary": "每页50条"
        },
        {
          "value": "100",
          "summary": "每页100条"
        }
      ],
      "description": "每页返回的最大结果数（默认50，最小50，最大100）"
    },
    "isHazMat": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "危险品"
        },
        {
          "value": "false",
          "summary": "非危险品"
        }
      ],
      "description": "是否为危险品"
    },
    "srAvgGte": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "排名从第1名开始"
        },
        {
          "value": "100",
          "summary": "排名从第100名开始"
        }
      ],
      "description": "历史销售排名-最低值（from，正整数，数值越小排名越好）"
    },
    "srAvgLte": {
      "type": "integer",
      "examples": [
        {
          "value": "1000",
          "summary": "排名到第1000名"
        },
        {
          "value": "10000",
          "summary": "排名到第10000名"
        }
      ],
      "description": "历史销售排名-最高值（to，正整数，数值越小排名越好）"
    },
    "srAvgMonth": {
      "type": "string",
      "pattern": "^\\d{6}$",
      "examples": [
        {
          "value": "202511",
          "summary": "2025年11月"
        },
        {
          "value": "202401",
          "summary": "2024年1月"
        },
        {
          "value": "202312",
          "summary": "2023年12月"
        }
      ],
      "description": "历史销售排名-选择月份（格式：YYYYMM，如202511表示2025年11月，最近36个月内）"
    },
    "buyBoxIsFBA": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "FBA配送"
        },
        {
          "value": "false",
          "summary": "非FBA配送"
        }
      ],
      "description": "购买按钮是否为FBA"
    },
    "productType": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "examples": [
        {
          "value": "[0,1,2]",
          "summary": "标准产品、可下载产品、电子书"
        },
        {
          "value": "[0]",
          "summary": "仅标准产品"
        },
        {
          "value": "[0,5]",
          "summary": "标准产品和变体父ASIN"
        }
      ],
      "maxItems": 1000,
      "description": "产品类型筛选（默认[0,1,2]）：0=标准产品(所有数据可用)，1=可下载产品(无市场/第三方价格数据)，2=电子书(无市场报价数据)，5=变体父ASIN(仅销售排名和变体CSV)"
    },
    "rootCategory": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "examples": [
        {
          "value": "[3167641]",
          "summary": "限定在某根类目"
        },
        {
          "value": "[562066, 493964]",
          "summary": "限定在多个根类目"
        }
      ],
      "maxItems": 1000,
      "description": "根类目ID(最多50)，仅包含列在这些根类别中的产品"
    },
    "avg90SalesGte": {
      "type": "integer",
      "description": "90天平均销售排名-最低"
    },
    "avg90SalesLte": {
      "type": "integer",
      "description": "90天平均销售排名-最高"
    },
    "currentNewGte": {
      "type": "integer",
      "examples": [
        {
          "value": "500",
          "summary": "至少$5.00"
        }
      ],
      "description": "当前新品价格-最低（最小货币单位）"
    },
    "currentNewLte": {
      "type": "integer",
      "examples": [
        {
          "value": "10000",
          "summary": "不超过$100.00"
        }
      ],
      "description": "当前新品价格-最高（最小货币单位）"
    },
    "buyBoxIsAmazon": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "亚马逊自营"
        },
        {
          "value": "false",
          "summary": "非亚马逊自营"
        }
      ],
      "description": "购买按钮卖家是否为亚马逊"
    },
    "monthlySoldGte": {
      "type": "integer",
      "examples": [
        {
          "value": "1000",
          "summary": "至少1000件"
        }
      ],
      "description": "销量/月销量-最低"
    },
    "monthlySoldLte": {
      "type": "integer",
      "examples": [
        {
          "value": "10000",
          "summary": "不超过10000件"
        }
      ],
      "description": "销量/月销量-最高"
    },
    "currentSalesGte": {
      "type": "integer",
      "examples": [
        {
          "value": "100",
          "summary": "排名100以后"
        }
      ],
      "description": "当前销售排名-最低（数值越小排名越好）"
    },
    "currentSalesLte": {
      "type": "integer",
      "examples": [
        {
          "value": "1000",
          "summary": "排名前1000"
        }
      ],
      "description": "当前销售排名-最高（数值越小排名越好）"
    },
    "packageWidthGte": {
      "type": "integer",
      "examples": [
        {
          "value": "50",
          "summary": "至少50毫米"
        }
      ],
      "description": "包装宽度-最小（毫米）"
    },
    "packageWidthLte": {
      "type": "integer",
      "examples": [
        {
          "value": "200",
          "summary": "不超过200毫米"
        }
      ],
      "description": "包装宽度-最大（毫米）"
    },
    "singleVariation": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "多变体仅取一个"
        }
      ],
      "description": "仅返回一个变体，当设为true时，多变体产品只返回一个变体"
    },
    "availableDateGte": {
      "type": "string",
      "examples": [
        {
          "value": "2024-01-01",
          "summary": "日期格式"
        }
      ],
      "maxLength": 1000,
      "description": "产品上架时间-最早（日期格式：yyyy-MM-dd）"
    },
    "availableDateLte": {
      "type": "string",
      "examples": [
        {
          "value": "2024-01-01",
          "summary": "日期格式"
        }
      ],
      "maxLength": 1000,
      "description": "产品上架时间-最晚（日期格式：yyyy-MM-dd）"
    },
    "currentRatingGte": {
      "type": "number",
      "examples": [
        {
          "value": "4.0",
          "summary": "至少4星"
        },
        {
          "value": "4.5",
          "summary": "至少4.5星"
        }
      ],
      "description": "当前评分-最低（0.0-5.0，如4.0星）"
    },
    "currentRatingLte": {
      "type": "number",
      "examples": [
        {
          "value": "5.0",
          "summary": "5星以下"
        },
        {
          "value": "4.5",
          "summary": "4.5星以下"
        }
      ],
      "description": "当前评分-最高（0.0-5.0，如4.5星）"
    },
    "packageHeightGte": {
      "type": "integer",
      "examples": [
        {
          "value": "30",
          "summary": "至少30毫米"
        }
      ],
      "description": "包装高度-最小（毫米）"
    },
    "packageHeightLte": {
      "type": "integer",
      "examples": [
        {
          "value": "150",
          "summary": "不超过150毫米"
        }
      ],
      "description": "包装高度-最大（毫米）"
    },
    "packageLengthGte": {
      "type": "integer",
      "examples": [
        {
          "value": "100",
          "summary": "至少100毫米"
        }
      ],
      "description": "包装长度-最小（毫米）"
    },
    "packageLengthLte": {
      "type": "integer",
      "examples": [
        {
          "value": "300",
          "summary": "不超过300毫米"
        }
      ],
      "description": "包装长度-最大（毫米）"
    },
    "packageWeightGte": {
      "type": "integer",
      "examples": [
        {
          "value": "100",
          "summary": "至少100克"
        }
      ],
      "description": "包装重量-最小（克）"
    },
    "packageWeightLte": {
      "type": "integer",
      "examples": [
        {
          "value": "1500",
          "summary": "不超过1500克"
        }
      ],
      "description": "包装重量-最大（克）"
    },
    "categoriesExclude": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "examples": [
        {
          "value": "[77028031,186606]",
          "summary": "排除这些子类目"
        }
      ],
      "maxItems": 1000,
      "description": "排除的子类目ID(最多50)"
    },
    "categoriesInclude": {
      "type": "array",
      "items": {
        "type": "integer"
      },
      "examples": [
        {
          "value": "[3010075031,12950651,355007011]",
          "summary": "限定在这些子类目"
        }
      ],
      "maxItems": 1000,
      "description": "仅包含的子类目ID(最多50)，仅包含直接列在这些子类别中的产品"
    },
    "rootCategoryNames": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"Electronics\"]",
          "summary": "限定在电子产品类目"
        },
        {
          "value": "[\"Home & Kitchen\", \"Sports & Outdoors\"]",
          "summary": "限定在多个类目"
        }
      ],
      "maxItems": 1000,
      "description": "根类目名称(最多50)，当rootCategory为空时使用，系统会自动查找对应的类目ID"
    },
    "variationCountGte": {
      "type": "integer",
      "examples": [
        {
          "value": "2",
          "summary": "至少2个变体"
        }
      ],
      "description": "变体数量-最低"
    },
    "variationCountLte": {
      "type": "integer",
      "examples": [
        {
          "value": "10",
          "summary": "不超过10个变体"
        }
      ],
      "description": "变体数量-最高"
    },
    "currentCountNewGte": {
      "type": "integer",
      "examples": [
        {
          "value": "5",
          "summary": "至少5个报价"
        }
      ],
      "description": "当前新品报价数量-最低"
    },
    "currentCountNewLte": {
      "type": "integer",
      "examples": [
        {
          "value": "50",
          "summary": "不超过50个报价"
        }
      ],
      "description": "当前新品报价数量-最高"
    },
    "categoriesExcludeNames": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"Books\"]",
          "summary": "排除图书类目"
        },
        {
          "value": "[\"Clothing, Shoes & Jewelry›Novelty & More›Clothing›Novelty›Women›Tops & Tees›T-Shirts\"]",
          "summary": "排除T-Shirts类目(带路径)"
        }
      ],
      "maxItems": 1000,
      "description": "排除的子类目名称(最多50)，当categoriesExclude为空时使用，系统会自动查找对应的类目ID。支持传入完整类目路径（如 'Clothing, Shoes & Jewelry›Novelty & More...' 或 'Clothing, Shoes & Jewelry:Novelty & More...'），此时将包含根类目在内进行转换，结果更准确。"
    },
    "categoriesIncludeNames": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"Camera & Photo\"]",
          "summary": "限定在相机摄影类目"
        },
        {
          "value": "[\"Clothing, Shoes & Jewelry›Novelty & More›Clothing›Novelty›Women›Tops & Tees›T-Shirts\"]",
          "summary": "限定在T-Shirts类目(带路径)"
        }
      ],
      "maxItems": 1000,
      "description": "包含的子类目名称(最多50)，当categoriesInclude为空时使用，系统会自动查找对应的类目ID。支持传入完整类目路径（如 'Clothing, Shoes & Jewelry›Novelty & More...' 或 'Clothing, Shoes & Jewelry:Novelty & More...'），此时将包含根类目在内进行转换，结果更准确。"
    },
    "currentCountReviewsGte": {
      "type": "integer",
      "examples": [
        {
          "value": "100",
          "summary": "至少100条评论"
        }
      ],
      "description": "当前评论数量-最低"
    },
    "currentCountReviewsLte": {
      "type": "integer",
      "examples": [
        {
          "value": "10000",
          "summary": "不超过10000条评论"
        }
      ],
      "description": "当前评论数量-最高"
    },
    "deltaPercent90SalesGte": {
      "type": "integer",
      "description": "90天销售排名变化百分比-最低"
    },
    "deltaPercent90SalesLte": {
      "type": "integer",
      "description": "90天销售排名变化百分比-最高"
    },
    "currentBuyBoxShippingGte": {
      "type": "integer",
      "examples": [
        {
          "value": "1000",
          "summary": "至少$10.00"
        }
      ],
      "description": "当前购买按钮含运费价格-最低（最小货币单位）"
    },
    "currentBuyBoxShippingLte": {
      "type": "integer",
      "examples": [
        {
          "value": "5000",
          "summary": "不超过$50.00"
        }
      ],
      "description": "当前购买按钮含运费价格-最高（最小货币单位）"
    },
    "outOfStockPercentage90Gte": {
      "type": "integer",
      "examples": [
        {
          "value": "10",
          "summary": "至少10%时间缺货"
        }
      ],
      "description": "90天缺货百分比-最低"
    },
    "outOfStockPercentage90Lte": {
      "type": "integer",
      "examples": [
        {
          "value": "25",
          "summary": "缺货不超过25%的时间"
        }
      ],
      "description": "90天缺货百分比-最高"
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
