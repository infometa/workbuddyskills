# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "asins"
  ],
  "properties": {
    "sort": {
      "type": "string",
      "examples": [
        {
          "value": "name",
          "summary": "名称升序"
        },
        {
          "value": "-name",
          "summary": "名称降序"
        },
        {
          "value": "dominant_category",
          "summary": "主导分类升序"
        },
        {
          "value": "-dominant_category",
          "summary": "主导分类降序"
        },
        {
          "value": "monthly_trend",
          "summary": "月度趋势升序"
        },
        {
          "value": "-monthly_trend",
          "summary": "月度趋势降序"
        },
        {
          "value": "quarterly_trend",
          "summary": "季度趋势升序"
        },
        {
          "value": "-quarterly_trend",
          "summary": "季度趋势降序"
        },
        {
          "value": "monthly_search_volume_exact",
          "summary": "精确月搜索量升序"
        },
        {
          "value": "-monthly_search_volume_exact",
          "summary": "精确月搜索量降序(默认)"
        },
        {
          "value": "monthly_search_volume_broad",
          "summary": "广泛月搜索量升序"
        },
        {
          "value": "-monthly_search_volume_broad",
          "summary": "广泛月搜索量降序"
        },
        {
          "value": "recommended_promotions",
          "summary": "推荐推广次数升序"
        },
        {
          "value": "-recommended_promotions",
          "summary": "推荐推广次数降序"
        },
        {
          "value": "sp_brand_ad_bid",
          "summary": "品牌广告竞价升序"
        },
        {
          "value": "-sp_brand_ad_bid",
          "summary": "品牌广告竞价降序"
        },
        {
          "value": "ppc_bid_broad",
          "summary": "广泛PPC竞价升序"
        },
        {
          "value": "-ppc_bid_broad",
          "summary": "广泛PPC竞价降序"
        },
        {
          "value": "ppc_bid_exact",
          "summary": "精确PPC竞价升序"
        },
        {
          "value": "-ppc_bid_exact",
          "summary": "精确PPC竞价降序"
        },
        {
          "value": "ease_of_ranking_score",
          "summary": "排名难度分升序"
        },
        {
          "value": "-ease_of_ranking_score",
          "summary": "排名难度分降序"
        },
        {
          "value": "relevancy_score",
          "summary": "相关性评分升序"
        },
        {
          "value": "-relevancy_score",
          "summary": "相关性评分降序"
        },
        {
          "value": "organic_product_count",
          "summary": "自然产品数升序"
        },
        {
          "value": "-organic_product_count",
          "summary": "自然产品数降序"
        }
      ],
      "maxLength": 1000,
      "description": "排序字段。可选值: name, -name, dominant_category, -dominant_category, monthly_trend, -monthly_trend, quarterly_trend, -quarterly_trend, monthly_search_volume_exact, -monthly_search_volume_exact, monthly_search_volume_broad, -monthly_search_volume_broad, recommended_promotions, -recommended_promotions, sp_brand_ad_bid, -sp_brand_ad_bid, ppc_bid_broad, -ppc_bid_broad, ppc_bid_exact, -ppc_bid_exact, ease_of_ranking_score, -ease_of_ranking_score, relevancy_score, -relevancy_score, organic_product_count, -organic_product_count。默认: -monthly_search_volume_exact"
    },
    "asins": {
      "type": "string",
      "maxLength": 1000,
      "description": "要分析的ASIN列表(1-10个有效ASIN), 多个asin使用逗号分隔"
    },
    "needCount": {
      "type": "integer",
      "description": "需要返回的总条数(系统内部自动分页拉取)"
    },
    "marketplace": {
      "type": "string",
      "examples": [
        {
          "value": "us",
          "summary": "美国"
        },
        {
          "value": "uk",
          "summary": "英国"
        },
        {
          "value": "de",
          "summary": "德国"
        },
        {
          "value": "in",
          "summary": "印度"
        },
        {
          "value": "ca",
          "summary": "加拿大"
        },
        {
          "value": "fr",
          "summary": "法国"
        },
        {
          "value": "it",
          "summary": "意大利"
        },
        {
          "value": "es",
          "summary": "西班牙"
        },
        {
          "value": "mx",
          "summary": "墨西哥"
        },
        {
          "value": "jp",
          "summary": "日本"
        }
      ],
      "maxLength": 1000,
      "description": "目标市场代码"
    },
    "maxWordCount": {
      "type": "integer",
      "description": "关键词最多词数(1-99999)"
    },
    "minWordCount": {
      "type": "integer",
      "description": "关键词最少词数(1-99999)"
    },
    "includeVariants": {
      "type": "boolean",
      "examples": [
        {
          "value": "false",
          "summary": "默认不含变体"
        },
        {
          "value": "true",
          "summary": "包含变体"
        }
      ],
      "description": "是否包含变体产品关键词"
    },
    "maxOrganicProductCount": {
      "type": "integer",
      "description": "最大自然搜索结果数(1-99999)"
    },
    "minOrganicProductCount": {
      "type": "integer",
      "description": "最小自然搜索结果数(1-99999)"
    },
    "maxMonthlySearchVolumeBroad": {
      "type": "integer",
      "description": "最大广泛月搜索量(1-999999)"
    },
    "maxMonthlySearchVolumeExact": {
      "type": "integer",
      "description": "最大精确月搜索量(1-999999)"
    },
    "minMonthlySearchVolumeBroad": {
      "type": "integer",
      "description": "最小广泛月搜索量(1-999999)"
    },
    "minMonthlySearchVolumeExact": {
      "type": "integer",
      "description": "最小精确月搜索量(1-999999)"
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
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "keywordInfoList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "name": {
            "type": "string",
            "description": "关键词名称"
          },
          "country": {
            "type": "string",
            "description": "国家市场代码"
          },
          "updatedAt": {
            "type": "string",
            "description": "数据更新时间(UTC)"
          },
          "organicRank": {
            "type": "integer",
            "description": "自然排名位置"
          },
          "overallRank": {
            "type": "integer",
            "description": "综合排名"
          },
          "ppcBidBroad": {
            "type": "number",
            "description": "广泛匹配PPC竞价(USD)"
          },
          "ppcBidExact": {
            "type": "number",
            "description": "精确匹配PPC竞价(USD)"
          },
          "primaryAsin": {
            "type": "string",
            "description": "主要ASIN"
          },
          "monthlyTrend": {
            "type": "number",
            "description": "月度搜索趋势(%)"
          },
          "spBrandAdBid": {
            "type": "number",
            "description": "品牌广告建议竞价(USD)"
          },
          "sponsoredRank": {
            "type": "integer",
            "description": "赞助排名位置"
          },
          "quarterlyTrend": {
            "type": "number",
            "description": "季度搜索趋势(%)"
          },
          "relevancyScore": {
            "type": "integer",
            "description": "相关性评分(0-100)"
          },
          "dominantCategory": {
            "type": "string",
            "description": "主导产品类别"
          },
          "easeOfRankingScore": {
            "type": "integer",
            "description": "排名难度评分(0-100)"
          },
          "organicProductCount": {
            "type": "integer",
            "description": "自然搜索结果数"
          },
          "competitorOrganicRank": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "asin": {
                  "type": "string",
                  "description": "ASIN"
                },
                "organicRank": {
                  "type": "integer",
                  "description": "自然排名"
                }
              }
            },
            "description": "竞品自然排名列表"
          },
          "recommendedPromotions": {
            "type": "integer",
            "description": "推荐推广次数"
          },
          "sponsoredProductCount": {
            "type": "integer",
            "description": "赞助产品数量"
          },
          "competitorSponsoredRank": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "asin": {
                  "type": "string",
                  "description": "ASIN"
                },
                "sponsoredRank": {
                  "type": "integer",
                  "description": "赞助排名"
                }
              }
            },
            "description": "竞品赞助排名列表"
          },
          "relativeOrganicPosition": {
            "type": "integer",
            "description": "相对自然位次"
          },
          "avgCompetitorOrganicRank": {
            "type": "number",
            "description": "平均竞品自然排名"
          },
          "monthlySearchVolumeBroad": {
            "type": "integer",
            "description": "广泛匹配月搜索量"
          },
          "monthlySearchVolumeExact": {
            "type": "integer",
            "description": "精确匹配月搜索量"
          },
          "organicRankingAsinsCount": {
            "type": "integer",
            "description": "自然排名ASIN数"
          },
          "relativeSponsoredPosition": {
            "type": "integer",
            "description": "相对赞助位次"
          },
          "avgCompetitorSponsoredRank": {
            "type": "number",
            "description": "平均竞品赞助排名"
          },
          "sponsoredRankingAsinsCount": {
            "type": "integer",
            "description": "赞助排名ASIN数"
          },
          "variationLowestOrganicRank": {
            "type": "integer",
            "description": "变体最低自然排名"
          },
          "variationLowestSponsoredRank": {
            "type": "integer",
            "description": "变体最低赞助排名"
          }
        }
      },
      "description": "按ASIN扩展的关键词信息列表"
    }
  }
}
```

</details>
