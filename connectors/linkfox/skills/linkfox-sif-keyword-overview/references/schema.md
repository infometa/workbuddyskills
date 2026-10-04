# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "keyword"
  ],
  "properties": {
    "last7d": {
      "type": "boolean",
      "default": true,
      "description": "是否取最近7天数据，默认 true；传 false 时使用 startDate/endDate 区间"
    },
    "country": {
      "type": "string",
      "default": "US",
      "pattern": "US|UK|DE|CA|JP|FR|ES|IT|MX|AU|AE|BR|SA",
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
          "value": "CA",
          "summary": "亚马逊-加拿大站"
        },
        {
          "value": "JP",
          "summary": "亚马逊-日本站"
        },
        {
          "value": "FR",
          "summary": "亚马逊-法国站"
        },
        {
          "value": "ES",
          "summary": "亚马逊-西班牙站"
        },
        {
          "value": "IT",
          "summary": "亚马逊-意大利站"
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
          "value": "AE",
          "summary": "亚马逊-阿联酋站"
        },
        {
          "value": "BR",
          "summary": "亚马逊-巴西站"
        },
        {
          "value": "SA",
          "summary": "亚马逊-沙特阿拉伯站"
        }
      ],
      "description": "国家站点"
    },
    "endDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-11-15",
          "summary": "2025-11-15"
        }
      ],
      "maxLength": 1000,
      "description": "结束日期 yyyy-MM-dd（与 startDate 配套）"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "关键词，尽量翻译成对应国家站点的语言"
    },
    "startDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-11-13",
          "summary": "2025-11-13"
        }
      ],
      "maxLength": 1000,
      "description": "开始日期 yyyy-MM-dd（last7d=false 时生效）"
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
      "description": "消息"
    },
    "code": {
      "type": "string",
      "description": "返回码"
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "keyword": {
            "type": "string",
            "description": "关键词.搜索查询的关键词文本"
          },
          "dataPeriodEndDate": {
            "type": "string",
            "description": "数据周期结束日期.本次返回数据对应的 ABA 周结束日期 (yyyy-MM-dd)"
          },
          "recAdProductCount": {
            "type": "integer",
            "description": "推荐位广告商品数量.在该关键词下推荐位中属于广告的商品数量"
          },
          "supplyDemandRatio": {
            "type": "number",
            "description": "供需比率.供应与需求的比率，计算公式：搜索结果商品数 / 月搜索量，数值越小表示竞争越小、机会越大"
          },
          "brandAdProductCount": {
            "type": "integer",
            "description": "品牌广告商品数量.在该关键词下投放品牌广告（Brand Ads）的商品数量"
          },
          "dataPeriodStartDate": {
            "type": "string",
            "description": "数据周期起始日期.本次返回数据对应的 ABA 周起始日期 (yyyy-MM-dd)"
          },
          "videoAdProductCount": {
            "type": "integer",
            "description": "视频广告商品数量.在该关键词下投放视频广告（Video Ads）的商品数量"
          },
          "recNonadProductCount": {
            "type": "integer",
            "description": "推荐位非广告商品数量.在该关键词下推荐位中属于非广告（自然）的商品数量"
          },
          "topRatedProductCount": {
            "type": "integer",
            "description": "Top Rated推荐商品数量.在该关键词下出现在Top Rated（高评分）推荐位的商品数量"
          },
          "keywordDataUpdateTime": {
            "type": "string",
            "description": "关键词数据更新时间.该关键词相关数据的最后更新时间"
          },
          "keywordPopularityRank": {
            "type": "integer",
            "description": "关键词热度排名.该关键词的月搜索量在亚马逊所有关键词中的排名，数值越小表示搜索量越大"
          },
          "trackedAsinTotalCount": {
            "type": "integer",
            "description": "SIF 跟踪的有曝光 ASIN 去重总数.该关键词下所有位置（自然/广告/推荐）中，SIF 系统追踪到有曝光得分的 ASIN 去重数量。上游字段：totalAsinNum"
          },
          "sponsoredProductsCount": {
            "type": "integer",
            "description": "SP广告商品数量.在该关键词下投放Sponsored Products（赞助商品）广告的商品数量"
          },
          "amazonChoiceProductCount": {
            "type": "integer",
            "description": "Amazon's Choice商品数量.在该关键词下获得Amazon's Choice推荐标志的商品数量"
          },
          "naturalSearchProductCount": {
            "type": "integer",
            "description": "自然搜索商品数量.在该关键词的自然搜索结果中展示的商品数量（不包括广告位）"
          },
          "estimatedWeeklySearchVolume": {
            "type": "integer",
            "description": "周预估搜索量.该关键词在亚马逊上每周的预估搜索次数，反映该词的搜索热度"
          },
          "paidAdvertisingProductCount": {
            "type": "integer",
            "description": "PPC广告商品总数.在该关键词下所有PPC付费广告（包括SP、品牌广告、视频广告等）的商品总数"
          },
          "totalMarketplaceKeywordCount": {
            "type": "integer",
            "description": "站点关键词总量.该站点（如美国站）所有关键词的总数量，用于了解市场整体规模"
          },
          "totalSearchResultProductCount": {
            "type": "integer",
            "description": "搜索结果商品总数.在该关键词下显示的所有商品总数（包括自然搜索、广告位、推荐位等）"
          },
          "searchRecommendationProductCount": {
            "type": "integer",
            "description": "搜索推荐商品数量.在该关键词搜索时亚马逊推荐的商品数量"
          },
          "editorialRecommendationsProductCount": {
            "type": "integer",
            "description": "Editorial Recommendations商品数量.在该关键词下出现在编辑推荐位的商品数量"
          }
        }
      },
      "description": "返回数据"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "title": {
      "type": "string",
      "description": "标题"
    },
    "total": {
      "type": "integer",
      "description": "数据总量。注意：本接口通常只返回单条数据，total 通常为1"
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
      "description": "耗时"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
