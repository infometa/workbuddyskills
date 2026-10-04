# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "region": {
      "type": "string",
      "default": "US",
      "pattern": "US|ID|TH|PH|MY|VN|GB|MX|SG|SA|BR|ES|JP|DE|IT|FR",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "ID",
          "summary": "印度尼西亚"
        },
        {
          "value": "TH",
          "summary": "泰国"
        },
        {
          "value": "PH",
          "summary": "菲律宾"
        },
        {
          "value": "MY",
          "summary": "马来西亚"
        },
        {
          "value": "VN",
          "summary": "越南"
        },
        {
          "value": "GB",
          "summary": "英国"
        },
        {
          "value": "MX",
          "summary": "墨西哥"
        },
        {
          "value": "SG",
          "summary": "新加坡"
        },
        {
          "value": "SA",
          "summary": "沙特阿拉伯"
        },
        {
          "value": "BR",
          "summary": "巴西"
        },
        {
          "value": "ES",
          "summary": "西班牙"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "DE",
          "summary": "德国"
        },
        {
          "value": "IT",
          "summary": "意大利"
        },
        {
          "value": "FR",
          "summary": "法国"
        }
      ],
      "description": "区域"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品关键词（请翻译为当地语言）"
    },
    "pageNum": {
      "type": "integer",
      "default": 1,
      "description": "分页页码"
    },
    "pageSize": {
      "type": "integer",
      "default": 50,
      "description": "每页条数"
    },
    "saleDays": {
      "type": "integer",
      "description": "商品上架销售天数,单位是天"
    },
    "sortType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "0",
          "summary": "asc"
        },
        {
          "value": "1",
          "summary": "desc"
        }
      ],
      "description": "排序方式"
    },
    "maxReviewCount": {
      "type": "integer",
      "description": "商品评价数（最大值）"
    },
    "maxSpuAvgPrice": {
      "type": "number",
      "description": "SPU平均价格（最大值）"
    },
    "maxTotalIflCnt": {
      "type": "integer",
      "description": "带货达人数（最大值）"
    },
    "minReviewCount": {
      "type": "integer",
      "description": "商品评价数（最小值）"
    },
    "minSpuAvgPrice": {
      "type": "number",
      "description": "SPU平均价格（最小值）"
    },
    "minTotalIflCnt": {
      "type": "integer",
      "description": "带货达人数（最小值）"
    },
    "maxFirstCrawlDt": {
      "type": "integer",
      "description": "商品上架时间（最大值）"
    },
    "maxTotalSaleCnt": {
      "type": "integer",
      "description": "总销量（最大值）"
    },
    "minFirstCrawlDt": {
      "type": "integer",
      "examples": [
        {
          "value": "20200101",
          "summary": "代表2020-01-01"
        }
      ],
      "description": "商品上架时间（最小值）"
    },
    "minTotalSaleCnt": {
      "type": "integer",
      "description": "总销量（最小值）"
    },
    "maxProductRating": {
      "type": "number",
      "description": "商品评分（最大值）"
    },
    "maxTotalVideoCnt": {
      "type": "integer",
      "description": "带货视频数（最大值）"
    },
    "maxTotalViewsCnt": {
      "type": "integer",
      "description": "带货播放数（最大值）"
    },
    "minProductRating": {
      "type": "number",
      "description": "商品评分（最小值）"
    },
    "minTotalVideoCnt": {
      "type": "integer",
      "description": "带货视频数（最小值）"
    },
    "minTotalViewsCnt": {
      "type": "integer",
      "description": "带货播放数（最小值）"
    },
    "productSortField": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "total_sale_cnt(总销量)"
        },
        {
          "value": "2",
          "summary": "total_sale_gmv_amt(商品交易总额)"
        },
        {
          "value": "3",
          "summary": "spu_avg_price(SPU平均价格)"
        },
        {
          "value": "4",
          "summary": "total_sale_7d_cnt(7天销量)"
        },
        {
          "value": "5",
          "summary": "total_sale_30d_cnt(30天销量)"
        },
        {
          "value": "6",
          "summary": "total_sale_gmv_7d_amt(7天商品交易额)"
        },
        {
          "value": "7",
          "summary": "total_sale_gmv_30d_amt(30天商品交易额)"
        }
      ],
      "description": "排序字段"
    },
    "categoryKeywordCN": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品分类（商品分类 请输入 中文）"
    },
    "maxTotalSale30dCnt": {
      "type": "integer",
      "description": "30天销量（最大值）"
    },
    "maxTotalSaleGmvAmt": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品交易总额（最大值）"
    },
    "minTotalSale30dCnt": {
      "type": "integer",
      "description": "30天销量（最小值）"
    },
    "minTotalSaleGmvAmt": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品交易总额（最小值）"
    },
    "maxTotalSaleGmv30dAmt": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品交易总额（30天）（最大值）"
    },
    "minTotalSaleGmv30dAmt": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品交易总额（30天）（最小值）"
    },
    "maxProductCommissionRate": {
      "type": "number",
      "description": "商品佣金比例（最大值）, 输入值为百分比时自动转成小数，例如：5%->0.05"
    },
    "minProductCommissionRate": {
      "type": "number",
      "description": "商品佣金比例（最小值）, 输入值为百分比时自动转成小数，例如：5%->0.05"
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
      "description": "记录数"
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
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "asin": {
            "type": "string",
            "description": "产品ID"
          },
          "price": {
            "type": "number",
            "description": "商品价格"
          },
          "title": {
            "type": "string",
            "description": "商品名称"
          },
          "region": {
            "type": "string",
            "description": "区域代码"
          },
          "ratings": {
            "type": "integer",
            "description": "评论数"
          },
          "coverUrl": {
            "type": "string",
            "description": "封面图URL列表"
          },
          "currency": {
            "type": "string",
            "description": "货币"
          },
          "discount": {
            "type": "string",
            "description": "折扣信息"
          },
          "imageUrl": {
            "type": "string",
            "description": "商品图片URL"
          },
          "maxPrice": {
            "type": "number",
            "description": "最高价格"
          },
          "minPrice": {
            "type": "number",
            "description": "最低价格"
          },
          "productId": {
            "type": "string",
            "description": "商品唯一标识ID"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "商品来源"
          },
          "categoryIds": {
            "type": "array",
            "items": {},
            "description": "商品品类ID列表"
          },
          "isSShopText": {
            "type": "string",
            "description": "是否S店"
          },
          "offMarkText": {
            "type": "string",
            "description": "是否有优惠标记"
          },
          "productName": {
            "type": "string",
            "description": "商品名称"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论数量"
          },
          "spuAvgPrice": {
            "type": "number",
            "description": "SPU平均价格"
          },
          "categoryName": {
            "type": "string",
            "description": "商品品类名称"
          },
          "firstCrawlDt": {
            "type": "integer",
            "description": "上架日期"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "总销量"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "上架时间(时间戳)"
          },
          "productRating": {
            "type": "number",
            "description": "商品评分"
          },
          "salePropsInfo": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "propId": {
                  "type": "string",
                  "description": "产品属性ID"
                },
                "hasImage": {
                  "type": "boolean",
                  "description": "产品属性是否包含图片"
                },
                "propName": {
                  "type": "string",
                  "description": "产品属性名称"
                },
                "salePropValues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": [],
                    "properties": {
                      "image": {
                        "type": "string",
                        "description": "属性值图片"
                      },
                      "propValue": {
                        "type": "string",
                        "description": "属性值名称"
                      },
                      "propValueId": {
                        "type": "string",
                        "description": "属性值ID"
                      }
                    }
                  },
                  "description": "产品属性值列表"
                }
              }
            },
            "description": "销售属性信息"
          },
          "salesFlagText": {
            "type": "string",
            "description": "带货方式"
          },
          "totalSale1dCnt": {
            "type": "integer",
            "description": "1天内总销量"
          },
          "totalSale7dCnt": {
            "type": "integer",
            "description": "7天内总销量"
          },
          "totalSale15dCnt": {
            "type": "integer",
            "description": "15天内总销量"
          },
          "totalSale30dCnt": {
            "type": "integer",
            "description": "30天内总销量"
          },
          "totalSale60dCnt": {
            "type": "integer",
            "description": "60天内总销量"
          },
          "totalSale90dCnt": {
            "type": "integer",
            "description": "90天内总销量"
          },
          "totalSaleGmvAmt": {
            "type": "number",
            "description": "总销售额"
          },
          "freeShippingText": {
            "type": "string",
            "description": "是否包邮"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "商品图片URL列表"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量"
          },
          "totalSaleGmv1dAmt": {
            "type": "number",
            "description": "1天内总销售额"
          },
          "totalSaleGmv7dAmt": {
            "type": "number",
            "description": "7天内总销售额"
          },
          "salesTrendFlagText": {
            "type": "string",
            "description": "销售趋势标记"
          },
          "totalSaleGmv15dAmt": {
            "type": "number",
            "description": "15天内总销售额"
          },
          "totalSaleGmv30dAmt": {
            "type": "number",
            "description": "30天内总销售额"
          },
          "totalSaleGmv60dAmt": {
            "type": "number",
            "description": "60天内总销售额"
          },
          "totalSaleGmv90dAmt": {
            "type": "number",
            "description": "90天内总销售额"
          },
          "productCommissionRate": {
            "type": "number",
            "description": "商品佣金比例"
          }
        }
      },
      "description": "产品信息列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
