# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace"
  ],
  "properties": {
    "page": {
      "type": "integer",
      "default": 1,
      "minimum": 1,
      "description": "分页页码.每页最多100个产品，默认1"
    },
    "queryMode": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "单条件查询（默认）"
        },
        {
          "value": "2",
          "summary": "多条件组合查询（且关系）"
        }
      ],
      "description": "查询方式.1：单条件查询（默认）；2：多条件组合查询（且关系）"
    },
    "queryType": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "基于ASIN查询同类产品"
        },
        {
          "value": "2",
          "summary": "基于类目(NodeId)查询"
        },
        {
          "value": "3",
          "summary": "查询品牌热销产品"
        },
        {
          "value": "4",
          "summary": "基于卖家名称查询热销产品"
        },
        {
          "value": "5",
          "summary": "基于卖家SellerId查询热销产品"
        },
        {
          "value": "6",
          "summary": "基于ABA关键词查热销产品"
        },
        {
          "value": "7",
          "summary": "基于标题/属性包含词查产品"
        },
        {
          "value": "8",
          "summary": "限定销售价范围(单位:当地货币最小单位如美分)"
        },
        {
          "value": "9",
          "summary": "限定月销量(近30日)范围"
        },
        {
          "value": "10",
          "summary": "限定季节性产品"
        },
        {
          "value": "11",
          "summary": "限定上架时间范围"
        },
        {
          "value": "12",
          "summary": "限定星级范围"
        },
        {
          "value": "13",
          "summary": "限定评论数量范围"
        },
        {
          "value": "14",
          "summary": "限定排名范围(大类+小类)"
        },
        {
          "value": "15",
          "summary": "限定发货方式"
        },
        {
          "value": "16",
          "summary": "限定子体数范围"
        }
      ],
      "description": "查询类型（仅当query=1时生效，query=2时此参数无效）。1:基于ASIN查询同类产品（注意：并非只查该ASIN，查单个产品请用productDetail接口）；2:基于类目(NodeId)查询；3:查询品牌热销产品；4:基于卖家名称查询热销产品；5:基于卖家SellerId查询热销产品；6:基于ABA关键词查热销产品（暂仅支持ABA关键词）；7:基于产品标题或产品属性包含词查产品；8:限定销售价范围查产品，单位为当地货币最小单位（如美分，1999表示$19.99）；9:限定月销量(近30日)范围查产品；10:限定季节性产品，仅返回所查月份的季节性产品；11:限定上架时间范围查产品，日期格式yyyy-MM-dd；12:限定星级范围查产品；13:限定评论数量范围查产品；14:限定排名范围查产品（需组合大小类排名）；15:限定发货方式查产品；16:限定子体数范围查产品"
    },
    "queryMonth": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "examples": [
        {
          "value": "2025-01",
          "summary": "查看2025年1月的历史数据"
        }
      ],
      "description": "回看历史月份产品数据，最长支持2024年1月起最多2年内数据, 选填，格式：yyyy-MM，不指定此参数时表示查实时数据，小于当月月份时为回看数据。AU BR IN暂不支持回看，US GB DE支持\"不限\"模式回看，其余站点支持Top100产品回看"
    },
    "queryValue": {
      "type": "string",
      "examples": [
        {
          "value": "B0CVM8TXHP",
          "summary": "queryType=1: 基于ASIN查同类产品"
        },
        {
          "value": "3743561",
          "summary": "queryType=2: 基于类目NodeId查询"
        },
        {
          "value": "Anker",
          "summary": "queryType=3: 查询品牌热销产品"
        },
        {
          "value": "AnkerDirect",
          "summary": "queryType=4: 基于卖家名称查询"
        },
        {
          "value": "A294P4X9EWVXLJ",
          "summary": "queryType=5: 基于卖家SellerId查询"
        },
        {
          "value": "Power Bank",
          "summary": "queryType=6: 基于ABA关键词查询"
        },
        {
          "value": "1,1000",
          "summary": "queryType=8: 价格范围1~1000美分"
        },
        {
          "value": "100,1000",
          "summary": "queryType=9: 月销量范围100~1000"
        },
        {
          "value": "1,2,3",
          "summary": "queryType=10: 查询1/2/3月旺季季节性产品"
        },
        {
          "value": "2024-06-01,2024-12-01",
          "summary": "queryType=11: 上架时间范围"
        },
        {
          "value": "3,5",
          "summary": "queryType=12: 星级3~5星"
        },
        {
          "value": "10,500",
          "summary": "queryType=13: 评论数10~500"
        },
        {
          "value": "500,5000;1,100",
          "summary": "queryType=14: 大类排名500~5000且小类排名1~100"
        },
        {
          "value": "FBA,FBM",
          "summary": "queryType=15: 限定发货方式"
        },
        {
          "value": "1,50",
          "summary": "queryType=16: 子体数1~50"
        },
        {
          "value": "[{\"QueryType\":1,\"Content\":\"B0CVM8TXHP\"},{\"QueryType\":8,\"Content\":\"100,500\"}]",
          "summary": "query=2: 多条件组合查询"
        }
      ],
      "maxLength": 1000,
      "description": "查询条件值，根据query和queryType不同而格式不同。\n【当query=1（单条件查询）时】根据queryType传入对应值：\nqueryType=1(ASIN同类): 传入ASIN，如 B0CVM8TXHP\nqueryType=2(类目): 传入NodeId，如 3743561\nqueryType=3(品牌): 传入品牌名，如 Anker\nqueryType=4(卖家名称): 传入卖家店铺名，如 AnkerDirect\nqueryType=5(卖家ID): 传入SellerId，如 A294P4X9EWVXLJ\nqueryType=6(ABA关键词): 传入关键词，如 Power Bank\nqueryType=7(标题/属性包含词): 传入匹配词，如 10,000mAh 30W\nqueryType=8(价格范围): 格式'最低,最高'(单位当地货币最小单位如美分)，如 1,1000 表示1~1000美分；省略一端表示不限，如 ,1000 表示不高于1000美分\nqueryType=9(月销量范围): 格式'最低,最高'，如 100,1000 表示月销量100~1000；,1000 表示不高于1000\nqueryType=10(季节性产品): 传入月份(逗号分隔)，如 1,2,3 表示查询1/2/3月为旺季的季节性产品\nqueryType=11(上架时间范围): 格式'开始日期,结束日期'(yyyy-MM-dd)，如 2024-06-01,2024-12-01；省略结束日期如 2024-06-01, 表示晚于该日期\nqueryType=12(星级范围): 格式'最低,最高'，如 3,5 表示3~5星；4, 表示>=4星\nqueryType=13(评论数范围): 格式'最低,最高'，如 10,500 表示10~500条；,500 表示少于500条\nqueryType=14(排名范围): 格式'大类最低,大类最高;小类最低,小类最高'，如 500,5000;1,100 表示大类排名500~5000且小类排名1~100\nqueryType=15(发货方式): 传入FBA或FBM(逗号分隔)，如 FBA,FBM\nqueryType=16(子体数范围): 格式'最低,最高'，如 1,50 表示子体数1~50\n【当query=2（多条件组合查询）时】传入JSON数组，每项包含QueryType和Content，如 [{\"QueryType\":1,\"Content\":\"B0CVM8TXHP\"},{\"QueryType\":8,\"Content\":\"100,500\"}]"
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
    "page": {
      "type": "integer",
      "description": "当前页码"
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
            "description": "当前价格.未扣Coupon，单位为当地货币(如美元)"
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
            "description": "当前评分（0.0-5.0，如4.8）"
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
          "ratings": {
            "type": "integer",
            "description": "评分数量"
          },
          "category": {
            "type": "array",
            "items": {},
            "description": "大类.[大类名称, NodeId]"
          },
          "hasVideo": {
            "type": "boolean",
            "description": "有视频"
          },
          "imageUrl": {
            "type": "string",
            "description": "主图"
          },
          "oldPrice": {
            "type": "number",
            "description": "划线价.单位为当地货币(如美元)"
          },
          "fbaDetail": {
            "type": "array",
            "items": {},
            "description": "FBA明细.首项为配送费，后续为月份:仓储费，如[475,1-9:5,10-12:15]"
          },
          "salesRank": {
            "type": "integer",
            "description": "BSR排名"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数"
          },
          "onlineDays": {
            "type": "integer",
            "description": "上架天数"
          },
          "parentAsin": {
            "type": "string",
            "description": "父ASIN.有子体时为父级ASIN，无子体时为null"
          },
          "profitRate": {
            "type": "number",
            "description": "利润率.例25.83表示25.83%"
          },
          "salesPrice": {
            "type": "number",
            "description": "到手价.扣除Coupon后的实际售价，单位为当地货币(如美元)"
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
          "platformFee": {
            "type": "number",
            "description": "平台佣金.单位为当地货币(如美元)"
          },
          "buyboxSeller": {
            "type": "string",
            "description": "Buybox卖家"
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
          "buyBoxSellerId": {
            "type": "string",
            "description": "Buybox卖家ID"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "主图列表"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量.近30日Listing维度不区分子体，推荐用于评估销量，值为-1表示无法预估"
          },
          "buyboxSellerAddress": {
            "type": "string",
            "description": "卖家所在地.Buybox卖家国籍(二字码如CN、US)，亚马逊自营时为null"
          },
          "listingSalesOfDaily": {
            "type": "number",
            "description": "日销售额.单位为当地货币(如美元)，值为-1表示无法预估"
          },
          "monthlySalesRevenue": {
            "type": "number",
            "description": "月销售额.预估值，单位为当地货币(如美元)，值为-1表示无法预估"
          },
          "listingSalesVolumeOfDaily": {
            "type": "integer",
            "description": "日销量.Listing维度不区分子体，值为-1表示无法预估"
          }
        }
      },
      "description": "产品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗的Token数量"
    },
    "pageCount": {
      "type": "integer",
      "description": "总页数(最多200页)"
    },
    "requestConsumed": {
      "type": "integer",
      "description": "消耗的请求数"
    }
  }
}
```

</details>
