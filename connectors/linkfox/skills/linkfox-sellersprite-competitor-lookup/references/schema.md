# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "uid": {
      "type": "string",
      "maxLength": 1000,
      "description": "用户id"
    },
    "page": {
      "type": "integer",
      "default": 1,
      "description": "页码，从1开始"
    },
    "size": {
      "type": "integer",
      "default": 50,
      "minimum": 10,
      "description": "每页条数,返回10-100条数据"
    },
    "brand": {
      "type": "string",
      "maxLength": 1000,
      "description": "品牌"
    },
    "order": {
      "type": "object",
      "required": [
        "field",
        "desc"
      ],
      "properties": {
        "desc": {
          "type": "string",
          "default": "true",
          "maxLength": 1000,
          "description": "true为降序 false为升序"
        },
        "field": {
          "type": "string",
          "default": "total_units",
          "examples": [
            {
              "value": "total_units",
              "summary": "月销量"
            },
            {
              "value": "total_amount",
              "summary": "月销售额"
            },
            {
              "value": "bsr_rank",
              "summary": "bsr排名"
            },
            {
              "value": "price",
              "summary": "价格"
            },
            {
              "value": "rating",
              "summary": "评分"
            },
            {
              "value": "reviews",
              "summary": "评分数"
            },
            {
              "value": "profit",
              "summary": "毛利率"
            },
            {
              "value": "reviews_rate",
              "summary": "留评率"
            },
            {
              "value": "available_date",
              "summary": "上架时间"
            },
            {
              "value": "questions",
              "summary": "Q & A"
            },
            {
              "value": "total_units_growth",
              "summary": "月销量增长率"
            },
            {
              "value": "total_amount_growth",
              "summary": "月销售额增长率"
            },
            {
              "value": "reviews_increasement",
              "summary": "月新增评分数"
            },
            {
              "value": "bsr_rank_cv",
              "summary": "近7天BSR增长数"
            },
            {
              "value": "bsr_rank_cr",
              "summary": "近7天BSR增长率"
            },
            {
              "value": "amz_unit",
              "summary": "子体销量"
            },
            {
              "value": "",
              "summary": "不传，查询全部数据"
            }
          ],
          "maxLength": 1000,
          "description": "排序字段"
        }
      }
    },
    "chatId": {
      "type": "string",
      "maxLength": 1000,
      "description": "对话id"
    },
    "teamId": {
      "type": "string",
      "maxLength": 1000,
      "description": "团队id"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "关键字；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等"
    },
    "asinList": {
      "type": "string",
      "pattern": "^[A-Z0-9]+(,[A-Z0-9]+){0,39}$",
      "examples": [
        {
          "value": "B072MQ5BRX,B08N5WRWNW",
          "summary": "多个ASIN示例,最多40个"
        }
      ],
      "description": "asin,多个asin使用英文逗号分隔,最多40个"
    },
    "matchType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "词组匹配"
        },
        {
          "value": "2",
          "summary": "模糊匹配"
        },
        {
          "value": "3",
          "summary": "精准匹配"
        }
      ],
      "description": "匹配方式，1词组匹配 2模糊匹配 3精准匹配；默认1"
    },
    "nodeLabel": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊类目名称"
    },
    "requestId": {
      "type": "string",
      "maxLength": 1000,
      "description": "推送id"
    },
    "nodeIdPath": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊类目id"
    },
    "sellerName": {
      "type": "string",
      "maxLength": 1000,
      "description": "卖家名称"
    },
    "marketplace": {
      "type": "string",
      "default": "US",
      "examples": [
        {
          "value": "US",
          "summary": "亚马逊-美国站"
        },
        {
          "value": "UK",
          "summary": "亚马逊-英国站"
        },
        {
          "value": "DE",
          "summary": "亚马逊-德国站"
        },
        {
          "value": "FR",
          "summary": "亚马逊-法国站"
        },
        {
          "value": "JP",
          "summary": "亚马逊-日本站"
        },
        {
          "value": "CA",
          "summary": "亚马逊-加拿大站"
        },
        {
          "value": "IT",
          "summary": "亚马逊-意大利站"
        },
        {
          "value": "ES",
          "summary": "亚马逊-西班牙站"
        },
        {
          "value": "MX",
          "summary": "亚马逊-墨西哥站"
        },
        {
          "value": "AU",
          "summary": "亚马逊-澳大利亚站"
        },
        {
          "value": "TR",
          "summary": "亚马逊-土耳其站"
        },
        {
          "value": "IN",
          "summary": "亚马逊-印度站"
        }
      ],
      "maxLength": 1000,
      "description": "市场"
    },
    "showVariation": {
      "type": "string",
      "default": "N",
      "examples": [
        {
          "value": "Y",
          "summary": "是"
        },
        {
          "value": "N",
          "summary": "否"
        }
      ],
      "maxLength": 1000,
      "description": "是否查询变体"
    },
    "dataSnapshotMonth": {
      "type": "string",
      "default": "nearly",
      "examples": [
        {
          "value": "nearly",
          "summary": "查询最近30天的亚马逊商品实时数据（非快照数据）"
        },
        {
          "value": "202412",
          "summary": "查询2024年12月亚马逊所有在售商品的历史快照数据"
        },
        {
          "value": "202501",
          "summary": "查询2025年01月亚马逊所有在售商品的历史快照数据"
        }
      ],
      "maxLength": 1000,
      "description": "亚马逊商品数据快照年月。指定查询特定历史时间点的商品数据快照，每个快照包含该月份所有在售商品的完整数据。格式：yyyyMM（如202412表示2024年12月所有在售商品的数据快照）。默认值 'nearly' 表示查询最近30天的实时数据。注意：数据快照是对特定月份亚马逊市场上所有在售商品的完整记录，用于历史分析和同期对比。仅支持查询已存在的历史快照，不支持未来日期。建议季节性分析时查询去年同期快照进行对比"
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
    "message": {
      "type": "string",
      "description": "执行消息"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "bsr": {
            "type": "integer",
            "description": "BSR 排名"
          },
          "fba": {
            "type": "number",
            "description": "fba运费"
          },
          "sku": {
            "type": "string",
            "description": "sku"
          },
          "asin": {
            "type": "string",
            "description": "asin"
          },
          "badge": {
            "type": "object",
            "required": [],
            "properties": {
              "ebc": {
                "type": "string",
                "description": "A+页面(Y/N)"
              },
              "video": {
                "type": "string",
                "description": "视频介绍(Y/N)"
              },
              "bestSeller": {
                "type": "string",
                "description": "Best Seller标识(Y/N)"
              },
              "newRelease": {
                "type": "string",
                "description": "release标识(Y/N)"
              },
              "amazonChoice": {
                "type": "string",
                "description": "amazon choice标识(Y/N)"
              }
            }
          },
          "brand": {
            "type": "string",
            "description": "品牌"
          },
          "bsrId": {
            "type": "string",
            "description": "BSR id"
          },
          "price": {
            "type": "number",
            "description": "价格"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "nodeId": {
            "type": "integer",
            "description": "节点id"
          },
          "parent": {
            "type": "string",
            "description": "父体ASIN"
          },
          "profit": {
            "type": "number",
            "description": "利润率"
          },
          "rating": {
            "type": "number",
            "description": "评分"
          },
          "weight": {
            "type": "string",
            "description": "重量"
          },
          "keyword": {
            "type": "string",
            "description": "对应筛选的关键词，如果有值，则表示这批数据是通过 这个关键词 keyword 搜索出来的"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数"
          },
          "badgeEbc": {
            "type": "string",
            "description": "A+页面(Y/N)"
          },
          "brandUrl": {
            "type": "string",
            "description": "品牌URL"
          },
          "currency": {
            "type": "string",
            "description": "币种"
          },
          "imageUrl": {
            "type": "string",
            "description": "图片URL"
          },
          "sellerId": {
            "type": "string",
            "description": "BuyBox卖家id"
          },
          "dimension": {
            "type": "string",
            "description": "尺寸"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数"
          },
          "badgeVideo": {
            "type": "string",
            "description": "视频介绍(Y/N)"
          },
          "nodeIdPath": {
            "type": "string",
            "description": "节点id路径字符串"
          },
          "primePrice": {
            "type": "number",
            "description": "prime价格"
          },
          "sellerName": {
            "type": "string",
            "description": "BuyBox卖家"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型：amazon"
          },
          "fulfillment": {
            "type": "string",
            "description": "配送方式(AMZ,FBA,FBM)"
          },
          "ratingsRate": {
            "type": "number",
            "description": "留评率"
          },
          "averagePrice": {
            "type": "number",
            "description": "平均价格"
          },
          "sellerNation": {
            "type": "string",
            "description": "BuyBox卖家国籍"
          },
          "variationNum": {
            "type": "integer",
            "description": "变体数"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "上架时间(日期)"
          },
          "bsrGrowthRate": {
            "type": "number",
            "description": "BSR 增长率"
          },
          "deliveryPrice": {
            "type": "number",
            "description": "卖家运费"
          },
          "nodeLabelPath": {
            "type": "string",
            "description": "类目路径"
          },
          "packageWeight": {
            "type": "string",
            "description": "包装重量"
          },
          "ratingsGrowth": {
            "type": "integer",
            "description": "月度增长数"
          },
          "subcategories": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "code": {
                  "type": "string",
                  "description": "类目code"
                },
                "rank": {
                  "type": "integer",
                  "description": "排名"
                },
                "label": {
                  "type": "string",
                  "description": "名称"
                }
              }
            },
            "description": "子类目"
          },
          "bsrGrowthCount": {
            "type": "integer",
            "description": "BSR 增长数"
          },
          "dimensionsType": {
            "type": "string",
            "description": "尺寸类型"
          },
          "badgeBestSeller": {
            "type": "string",
            "description": "Best Seller标识(Y/N)"
          },
          "badgeNewRelease": {
            "type": "string",
            "description": "release标识(Y/N)"
          },
          "amzUnitDateString": {
            "type": "string",
            "description": "子体销量更新日期(时间戳)"
          },
          "badgeAmazonChoice": {
            "type": "string",
            "description": "amazon choice标识(Y/N)"
          },
          "dataSnapshotMonth": {
            "type": "string",
            "description": "数据查询月份"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量"
          },
          "packageDimensions": {
            "type": "string",
            "description": "包装尺寸"
          },
          "variant30DayUnits": {
            "type": "integer",
            "description": "子体月销量(件数)"
          },
          "availableDateString": {
            "type": "string",
            "description": "上架日期(日期字符串)"
          },
          "listingQualityScore": {
            "type": "number",
            "description": "listing质量得分"
          },
          "monthlySalesRevenue": {
            "type": "number",
            "description": "月销售额"
          },
          "variant30DayRevenue": {
            "type": "number",
            "description": "子体月销售额(金额)"
          },
          "packageDimensionType": {
            "type": "string",
            "description": "包装尺寸类型"
          },
          "variant30DayUpdatedAt": {
            "type": "string",
            "description": "子体数据更新时间(时间戳)"
          },
          "monthlySalesUnitsGrowthRate": {
            "type": "number",
            "description": "月销量增长率"
          }
        }
      },
      "description": "竞品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "nodeLabel": {
      "type": "string",
      "description": "nodeLabel"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型：amazon"
    }
  }
}
```

</details>
