# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "asin"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "examples": [
        {
          "value": "B07Z82895W",
          "summary": "示例 ASIN"
        }
      ],
      "maxLength": 1000,
      "description": "ASIN"
    },
    "page": {
      "type": "integer",
      "default": 1,
      "description": "当前页，默认1"
    },
    "size": {
      "type": "integer",
      "default": 50,
      "maximum": 100,
      "minimum": 1,
      "description": "每页条数，默认50，最大100，最多查2000条"
    },
    "month": {
      "type": "string",
      "pattern": "^(19|20)\\d{2}(0[1-9]|1[0-2])$",
      "examples": [
        {
          "value": "202308",
          "summary": "2023年8月"
        }
      ],
      "description": "历史月份，不传默认最近30天，格式 yyyyMM"
    },
    "badges": {
      "type": "string",
      "examples": [
        {
          "value": "naturalSearching",
          "summary": "自然搜索词"
        },
        {
          "value": "amazonChoice",
          "summary": "AC推荐词"
        },
        {
          "value": "editorialRecommendations",
          "summary": "ER推荐词"
        },
        {
          "value": "fourStar",
          "summary": "四星推荐词"
        },
        {
          "value": "highlyRated",
          "summary": "HR推荐词"
        },
        {
          "value": "sponsorBrand",
          "summary": "品牌推荐词"
        },
        {
          "value": "sponsorVideo",
          "summary": "视频推荐词"
        },
        {
          "value": "ads",
          "summary": "SP广告词"
        }
      ],
      "maxLength": 1000,
      "description": "流量词类型(badges)，多个值用英文逗号分隔。可选枚举：naturalSearching-自然搜索词；amazonChoice-AC推荐词；editorialRecommendations-ER推荐词；fourStar-四星推荐词；highlyRated-HR推荐词；sponsorBrand-品牌推荐词；sponsorVideo-视频推荐词；ads-SP广告词"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "关键词筛选"
    },
    "orderDesc": {
      "type": "boolean",
      "default": false,
      "description": "排序是否倒序，默认 false"
    },
    "orderField": {
      "type": "string",
      "default": "rankPosition",
      "examples": [
        {
          "value": "rankPosition",
          "summary": "自然排名"
        },
        {
          "value": "adPosition",
          "summary": "广告排名"
        },
        {
          "value": "createdTime",
          "summary": "创建时间"
        },
        {
          "value": "searchesRank",
          "summary": "搜索量周排名"
        },
        {
          "value": "searches",
          "summary": "月搜索量"
        },
        {
          "value": "purchases",
          "summary": "月购买量"
        },
        {
          "value": "purchaseRate",
          "summary": "购买率"
        },
        {
          "value": "products",
          "summary": "商品数"
        },
        {
          "value": "supplyDemandRatio",
          "summary": "供需比"
        },
        {
          "value": "latest1daysAds",
          "summary": "广告竞品数"
        },
        {
          "value": "bid",
          "summary": "PPC竞价"
        },
        {
          "value": "trafficPercentage",
          "summary": "流量占比"
        }
      ],
      "maxLength": 1000,
      "description": "排序字段(order.field)，默认 rankPosition。可选：rankPosition-自然排名；adPosition-广告排名；createdTime-创建时间；searchesRank-搜索量周排名；searches-月搜索量；purchases-月购买量；purchaseRate-购买率；products-商品数；supplyDemandRatio-供需比；latest1daysAds-广告竞品数；bid-PPC竞价；trafficPercentage-流量占比"
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
      "description": "市场(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹)"
    },
    "trafficKeywordTypes": {
      "type": "string",
      "examples": [
        {
          "value": "primary",
          "summary": "主要流量词"
        },
        {
          "value": "precise",
          "summary": "精准流量词"
        },
        {
          "value": "preciseLongTail",
          "summary": "转化流失词"
        }
      ],
      "maxLength": 1000,
      "description": "流量占比类型(trafficKeywordTypes)，多个值用英文逗号分隔。可选枚举：primary-主要流量词；precise-精准流量词；preciseLongTail-转化流失词"
    },
    "conversionKeywordTypes": {
      "type": "string",
      "examples": [
        {
          "value": "excellent",
          "summary": "转化优质词"
        },
        {
          "value": "stable",
          "summary": "转化平稳词"
        },
        {
          "value": "lost",
          "summary": "转化流失词"
        },
        {
          "value": "invalid",
          "summary": "无效曝光词"
        }
      ],
      "maxLength": 1000,
      "description": "流量转化类型(conversionKeywordTypes)，多个值用英文逗号分隔。可选枚举：excellent-转化优质词；stable-转化平稳词；lost-转化流失词；invalid-无效曝光词"
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
    "asin": {
      "type": "string",
      "description": "ASIN"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "bid": {
            "type": "number",
            "description": "PPC竞价"
          },
          "sprt": {
            "type": "number",
            "description": "SP相关比率"
          },
          "stats": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "total": {
                  "type": "integer",
                  "description": "总条数"
                },
                "keywords": {
                  "type": "string",
                  "description": "词"
                },
                "adPosition": {
                  "type": "object",
                  "required": [],
                  "properties": {
                    "page": {
                      "type": "integer",
                      "description": "第几页"
                    },
                    "index": {
                      "type": "integer",
                      "description": "当前页排第几"
                    },
                    "pageSize": {
                      "type": "integer",
                      "description": "每页多少条数据"
                    },
                    "position": {
                      "type": "integer",
                      "description": "总结果中排第几"
                    },
                    "updatedTime": {
                      "type": "integer",
                      "description": "排名时间"
                    }
                  }
                },
                "rankPosition": {
                  "type": "object",
                  "required": [],
                  "properties": {
                    "page": {
                      "type": "integer",
                      "description": "第几页"
                    },
                    "index": {
                      "type": "integer",
                      "description": "当前页排第几"
                    },
                    "pageSize": {
                      "type": "integer",
                      "description": "每页多少条数据"
                    },
                    "position": {
                      "type": "integer",
                      "description": "总结果中排第几"
                    },
                    "updatedTime": {
                      "type": "integer",
                      "description": "排名时间"
                    }
                  }
                }
              }
            },
            "description": "高频词"
          },
          "badges": {
            "type": "array",
            "items": {},
            "description": "曝光位置(流量词类型)"
          },
          "bidMax": {
            "type": "number",
            "description": "PPC竞价上限"
          },
          "bidMin": {
            "type": "number",
            "description": "PPC竞价下限"
          },
          "clicks": {
            "type": "integer",
            "description": "点击量"
          },
          "adRatio": {
            "type": "number",
            "description": "流量分布-广告占比"
          },
          "keyword": {
            "type": "string",
            "description": "关键词"
          },
          "products": {
            "type": "integer",
            "description": "商品数"
          },
          "searches": {
            "type": "integer",
            "description": "月搜索量"
          },
          "keywordCn": {
            "type": "string",
            "description": "关键词中文翻译"
          },
          "purchases": {
            "type": "integer",
            "description": "月购买量"
          },
          "adPosition": {
            "type": "object",
            "required": [],
            "properties": {
              "page": {
                "type": "integer",
                "description": "第几页"
              },
              "index": {
                "type": "integer",
                "description": "当前页排第几"
              },
              "pageSize": {
                "type": "integer",
                "description": "每页多少条数据"
              },
              "position": {
                "type": "integer",
                "description": "总结果中排第几"
              },
              "updatedTime": {
                "type": "integer",
                "description": "排名时间"
              }
            }
          },
          "impressions": {
            "type": "integer",
            "description": "展示量"
          },
          "updatedTime": {
            "type": "integer",
            "description": "更新时间"
          },
          "naturalRatio": {
            "type": "number",
            "description": "流量分布-自然占比"
          },
          "purchaseRate": {
            "type": "number",
            "description": "购买率"
          },
          "rankPosition": {
            "type": "object",
            "required": [],
            "properties": {
              "page": {
                "type": "integer",
                "description": "第几页"
              },
              "index": {
                "type": "integer",
                "description": "当前页排第几"
              },
              "pageSize": {
                "type": "integer",
                "description": "每页多少条数据"
              },
              "position": {
                "type": "integer",
                "description": "总结果中排第几"
              },
              "updatedTime": {
                "type": "integer",
                "description": "排名时间"
              }
            }
          },
          "searchesRank": {
            "type": "integer",
            "description": "周搜索量排名"
          },
          "titleDensity": {
            "type": "number",
            "description": "标题密度"
          },
          "latest1daysAds": {
            "type": "integer",
            "description": "最近1天广告竞品数"
          },
          "latest7daysAds": {
            "type": "integer",
            "description": "最近7天广告竞品数"
          },
          "latest30daysAds": {
            "type": "integer",
            "description": "最近30天广告竞品数"
          },
          "top3ClickingRate": {
            "type": "number",
            "description": "Top3点击率"
          },
          "monopolyClickRate": {
            "type": "number",
            "description": "垄断点击率"
          },
          "supplyDemandRatio": {
            "type": "number",
            "description": "供需比"
          },
          "trafficPercentage": {
            "type": "number",
            "description": "流量占比"
          },
          "searchesRankTimeTo": {
            "type": "integer",
            "description": "周搜索量排名时间范围止"
          },
          "top3ConversionRate": {
            "type": "number",
            "description": "Top3转化率"
          },
          "trafficKeywordType": {
            "type": "string",
            "description": "流量占比类型"
          },
          "searchesRankTimeFrom": {
            "type": "integer",
            "description": "周搜索量排名时间范围起"
          },
          "conversionKeywordType": {
            "type": "string",
            "description": "流量转化类型"
          },
          "calculatedWeeklySearches": {
            "type": "number",
            "description": "预估周曝光量"
          }
        }
      },
      "description": "流量词列表(对应第三方 data.items)"
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
      "description": "市场编码"
    },
    "summaryList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "total": {
            "type": "integer",
            "description": "总次数"
          },
          "keywords": {
            "type": "string",
            "description": "词"
          }
        }
      },
      "description": "高频词总结列表"
    }
  }
}
```

</details>
