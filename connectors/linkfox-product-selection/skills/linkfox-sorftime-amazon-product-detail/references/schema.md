# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin",
    "marketplace"
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
          "value": "B0088PUEPK,B00U26V4VQ",
          "summary": "多个ASIN，用英文逗号分隔，最多10个"
        }
      ],
      "maxLength": 1000,
      "description": "亚马逊标准识别号(ASIN).支持多个ASIN查询（最多10个），以英文逗号隔开"
    },
    "marketplace": {
      "type": "string",
      "pattern": "us|gb|de|fr|in|ca|jp|es|it|mx|ae|au|br|sa",
      "examples": [
        {
          "value": "us",
          "summary": "美国站"
        },
        {
          "value": "gb",
          "summary": "英国站"
        },
        {
          "value": "de",
          "summary": "德国站"
        },
        {
          "value": "fr",
          "summary": "法国站"
        },
        {
          "value": "in",
          "summary": "印度站"
        },
        {
          "value": "ca",
          "summary": "加拿大站"
        },
        {
          "value": "jp",
          "summary": "日本站"
        },
        {
          "value": "es",
          "summary": "西班牙站"
        },
        {
          "value": "it",
          "summary": "意大利站"
        },
        {
          "value": "mx",
          "summary": "墨西哥站"
        },
        {
          "value": "ae",
          "summary": "阿联酋站"
        },
        {
          "value": "au",
          "summary": "澳大利亚站"
        },
        {
          "value": "br",
          "summary": "巴西站"
        },
        {
          "value": "sa",
          "summary": "沙特站"
        }
      ],
      "description": "亚马逊站点代码"
    },
    "includeTrend": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "包含趋势数据（默认）"
        },
        {
          "value": "2",
          "summary": "不包含趋势数据"
        }
      ],
      "description": "是否包含趋势数据.1：包含（默认）；2：不包含"
    },
    "queryTrendEndDate": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "examples": [
        {
          "value": "2025-03-01",
          "summary": "查询到2025年3月1日的趋势"
        }
      ],
      "description": "趋势截止日期(yyyy-MM-dd)"
    },
    "queryTrendStartDate": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "examples": [
        {
          "value": "2025-01-01",
          "summary": "从2025年1月1日开始查询趋势"
        }
      ],
      "description": "趋势开始日期(yyyy-MM-dd).默认仅返回近15天，查询天数>15天时扣费加倍"
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
    "msg": {
      "type": "string",
      "description": "响应消息"
    },
    "code": {
      "type": "integer",
      "description": "响应码（200表示成功）"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "总数"
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
    "costTime": {
      "type": "integer",
      "description": "接口耗时(毫秒)"
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
          "size": {
            "type": "array",
            "items": {},
            "description": "尺寸.外包装[最长边,第二长边,最短边]，单位cm"
          },
          "aPlus": {
            "type": "boolean",
            "description": "有A+"
          },
          "brand": {
            "type": "string",
            "description": "品牌"
          },
          "isFBA": {
            "type": "boolean",
            "description": "是否FBA.Buybox卖家是否使用FBA物流"
          },
          "price": {
            "type": "number",
            "description": "销售价.扣除Coupon后的实际售价，单位为当地货币(如美元)"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "coupon": {
            "type": "integer",
            "description": "Coupon政策.值>0为抵扣金额(如500=$5)，值<0为折扣百分比(如-10=10%折扣)"
          },
          "rating": {
            "type": "number",
            "description": "当前评分（0.0-5.0，如4.70）"
          },
          "weight": {
            "type": "string",
            "description": "重量.单位g"
          },
          "asinUrl": {
            "type": "string",
            "description": "商品链接.亚马逊Listing详情页URL"
          },
          "fbaFees": {
            "type": "number",
            "description": "FBA费用.单位为当地货币(如美元)"
          },
          "feature": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "offSale": {
            "type": "integer",
            "description": "是否下架.1=不可售，0=可售"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数量"
          },
          "category": {
            "type": "array",
            "items": {},
            "description": "大类.[大类名称, NodeId]"
          },
          "dealType": {
            "type": "string",
            "description": "Deal标签"
          },
          "ebcPhoto": {
            "type": "array",
            "items": {},
            "description": "A+图片"
          },
          "hasVideo": {
            "type": "boolean",
            "description": "有视频"
          },
          "imageUrl": {
            "type": "string",
            "description": "主图"
          },
          "property": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "shipCost": {
            "type": "number",
            "description": "FBM配送费.单位为当地货币(如美元)"
          },
          "attribute": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "asin": {
                  "type": "string",
                  "description": "子体ASIN"
                },
                "name": {
                  "type": "string",
                  "description": "属性名"
                },
                "value": {
                  "type": "string",
                  "description": "属性值"
                }
              }
            },
            "description": "产品属性.有子体时表示子体属性"
          },
          "dealTrend": {
            "type": "array",
            "items": {},
            "description": "Deal趋势.下标%2=0为日期，下标%2=1为状态(1:有Deal，0:无Deal)"
          },
          "fbaDetail": {
            "type": "array",
            "items": {},
            "description": "FBA明细.首项为配送费，后续为月份:仓储费，如[475,1-9:5,10-12:15]"
          },
          "rankTrend": {
            "type": "array",
            "items": {},
            "description": "BSR趋势.大类排名变化历史"
          },
          "salesRank": {
            "type": "integer",
            "description": "BSR排名"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数"
          },
          "shipsFrom": {
            "type": "string",
            "description": "发货方"
          },
          "storeName": {
            "type": "string",
            "description": "店铺名称"
          },
          "lastUpdate": {
            "type": "string",
            "description": "更新时间.ASIN数据最近采集时间（格式yyyy-MM-dd）"
          },
          "onlineDays": {
            "type": "integer",
            "description": "上架天数"
          },
          "parentAsin": {
            "type": "string",
            "description": "父ASIN.有子体时为父级ASIN，无子体时为null"
          },
          "priceTrend": {
            "type": "array",
            "items": {},
            "description": "售价趋势.未扣Coupon，单位为当地货币最小单位，-1表示该日无可用价格"
          },
          "profitRate": {
            "type": "number",
            "description": "利润率.例25.83表示25.83%"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型"
          },
          "bsrCategory": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "date": {
                  "type": "string",
                  "description": "日期.格式yyyyMMdd"
                },
                "name": {
                  "type": "string",
                  "description": "类目名称"
                },
                "rank": {
                  "type": "string",
                  "description": "排名"
                },
                "nodeId": {
                  "type": "string",
                  "description": "节点ID"
                }
              }
            },
            "description": "小类排名列表"
          },
          "description": {
            "type": "string",
            "description": "五点描述"
          },
          "platformFee": {
            "type": "number",
            "description": "平台佣金.单位为当地货币(如美元)"
          },
          "productInfo": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "productType": {
            "type": "string",
            "description": "分类.亚马逊产品类目节点名称"
          },
          "bsrRankTrend": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "小类排名趋势.JSON格式，示例: [{NodeId:xxx, Rank:[日期,排名,...]}]"
          },
          "buyboxSeller": {
            "type": "string",
            "description": "Buybox卖家"
          },
          "extraSavings": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "关联促销.如[{Asin:xxx, Text:Save 5%...}]"
          },
          "productBadge": {
            "type": "array",
            "items": {},
            "description": "产品标志.如Amazon Choice、Best Seller、New Release等"
          },
          "profitAmount": {
            "type": "number",
            "description": "利润.到手价-FBA费-佣金，单位为当地货币(如美元)"
          },
          "variationNum": {
            "type": "integer",
            "description": "变体数"
          },
          "availableDate": {
            "type": "string",
            "description": "上架时间.格式yyyy-MM-dd"
          },
          "hasBrandStore": {
            "type": "boolean",
            "description": "有品牌店"
          },
          "variationASIN": {
            "type": "array",
            "items": {},
            "description": "子体ASIN列表.无子体时为null"
          },
          "brandPromotion": {
            "type": "string",
            "description": "品牌促销"
          },
          "buyBoxSellerId": {
            "type": "string",
            "description": "Buybox卖家ID"
          },
          "listPriceTrend": {
            "type": "array",
            "items": {},
            "description": "原价趋势.划线价历史，单位为当地货币最小单位，-1表示该日无可用价格"
          },
          "oneStarRatings": {
            "type": "number",
            "description": "1星占比.例15.5表示15.5%"
          },
          "twoStarRatings": {
            "type": "number",
            "description": "2星占比.例8.0表示8.0%"
          },
          "fiveStarRatings": {
            "type": "number",
            "description": "5星占比.例57.7表示57.7%"
          },
          "fourStarRatings": {
            "type": "number",
            "description": "4星占比.例12.3表示12.3%"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "主图列表"
          },
          "threeStarRatings": {
            "type": "number",
            "description": "3星占比.例6.5表示6.5%"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "官方月销量.亚马逊公布的ASIN月销量，取近7个自然日最新值，无则为0"
          },
          "buyboxSellerAddress": {
            "type": "string",
            "description": "卖家所在地.Buybox卖家国籍(二字码如CN、US)，亚马逊自营时为null"
          },
          "listingSalesOfDailyTrend": {
            "type": "array",
            "items": {},
            "description": "日销售额趋势.单位为当地货币最小单位(如美分)，下标%2=0为日期，下标%2=1为预计日销售额"
          },
          "listingSalesOfMonthTrend": {
            "type": "array",
            "items": {},
            "description": "月销售额趋势.单位为当地货币最小单位，下标%2=0为日期，下标%2=1为预计月销售额"
          },
          "listingSalesVolumeOfDailyTrend": {
            "type": "array",
            "items": {},
            "description": "日销量趋势.下标%2=0为日期，下标%2=1为预计日销量，值为-1表示无法预估"
          },
          "listingSalesVolumeOfMonthTrend": {
            "type": "array",
            "items": {},
            "description": "月销量趋势.近30日销量，下标%2=0为日期，下标%2=1为月销量，值为-1表示无法预估"
          }
        }
      },
      "description": "产品详情列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗的Token数量"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型"
    },
    "requestConsumed": {
      "type": "integer",
      "description": "消耗的请求数"
    }
  }
}
```

</details>
