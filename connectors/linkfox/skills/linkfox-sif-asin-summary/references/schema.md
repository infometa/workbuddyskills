# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "searchValue"
  ],
  "properties": {
    "desc": {
      "type": "boolean",
      "default": true,
      "description": "是否降序，默认传 true "
    },
    "last7d": {
      "type": "boolean",
      "default": true,
      "description": "是否取最近7天数据，默认 true；传 false 时使用 startDate/endDate 区间"
    },
    "sortBy": {
      "type": "string",
      "pattern": "totalKeywordNum|naturalKeywordNum|brandKeywordNum|vedioKeywordNum|acKeywordNum|erKeywordNum|trKeywordNum|sumScore|totalNfScore|totalSpSocre|totalBrandScore|totalVedioScore|totalAcScore|totalTrScore|totalErScore",
      "examples": [
        {
          "value": "",
          "summary": "系统默认排序"
        },
        {
          "value": "totalKeywordNum",
          "summary": "全部流量词"
        },
        {
          "value": "naturalKeywordNum",
          "summary": "自然流量词"
        },
        {
          "value": "brandKeywordNum",
          "summary": "品牌广告词"
        },
        {
          "value": "vedioKeywordNum",
          "summary": "视频广告词"
        },
        {
          "value": "acKeywordNum",
          "summary": "ac推荐词"
        },
        {
          "value": "erKeywordNum",
          "summary": "er推荐词"
        },
        {
          "value": "trKeywordNum",
          "summary": "tr推荐词"
        },
        {
          "value": "sumScore",
          "summary": "所有关键词下曝光总得分"
        },
        {
          "value": "totalNfScore",
          "summary": "所有自然排名曝光总得分"
        },
        {
          "value": "totalSpSocre",
          "summary": "所有sp广告曝光总得分"
        },
        {
          "value": "totalBrandScore",
          "summary": "所有品牌广告曝光总得分"
        },
        {
          "value": "totalVedioScore",
          "summary": "所有视频广告曝光总得分"
        },
        {
          "value": "totalAcScore",
          "summary": "所有ac推荐曝光总得分"
        },
        {
          "value": "totalTrScore",
          "summary": "所有tr推荐曝光总得分"
        },
        {
          "value": "totalErScore",
          "summary": "所有er推荐曝光总得分"
        }
      ],
      "description": "排序字段"
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
          "value": "2026-03-14",
          "summary": "2026-03-14"
        }
      ],
      "maxLength": 1000,
      "description": "结束日期 yyyy-MM-dd（与 startDate 配套）"
    },
    "pageNum": {
      "type": "integer",
      "default": 1,
      "description": "页码"
    },
    "pageSize": {
      "type": "integer",
      "default": 10000,
      "maximum": 10000,
      "minimum": 10,
      "description": "每页数量，最小10，最大10000，默认10000"
    },
    "startDate": {
      "type": "string",
      "examples": [
        {
          "value": "2026-03-08",
          "summary": "2026-03-08"
        }
      ],
      "maxLength": 1000,
      "description": "开始日期 yyyy-MM-dd（last7d=false 时生效，不填取系统最新周）"
    },
    "conditions": {
      "type": "string",
      "pattern": "^(nf|sp|sb|sbv|ad|acAd|totalPeriod\\.in)(,(nf|sp|sb|sbv|ad|acAd|totalPeriod\\.in))*$",
      "examples": [
        {
          "value": "nf",
          "summary": "自然流量"
        },
        {
          "value": "sp",
          "summary": "SP广告"
        },
        {
          "value": "sb",
          "summary": "SB常规"
        },
        {
          "value": "sbv",
          "summary": "视频广告"
        },
        {
          "value": "ad",
          "summary": "广告流量"
        },
        {
          "value": "acAd",
          "summary": "SP推荐"
        },
        {
          "value": "totalPeriod.in",
          "summary": "新进全部流量词"
        }
      ],
      "description": "条件筛选,多个条件以英文逗号隔开（v2 新增）"
    },
    "searchValue": {
      "type": "string",
      "maxLength": 1000,
      "description": "搜索值，ASIN码，多个用逗号分隔，最多10个ASIN"
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
          "asin": {
            "type": "string",
            "description": "ASIN编码.亚马逊商品标准识别码（Amazon Standard Identification Number）"
          },
          "isMonitored": {
            "type": "boolean",
            "description": "是否已监控.true=该商品在监控列表中，false=未监控"
          },
          "productPrice": {
            "type": "number",
            "description": "商品售价.当前亚马逊页面显示的商品价格"
          },
          "productTitle": {
            "type": "string",
            "description": "商品标题.亚马逊页面显示的完整商品标题"
          },
          "productCategory": {
            "type": "string",
            "description": "商品类目.该商品在亚马逊上所属的行业类目"
          },
          "productFeatures": {
            "type": "array",
            "items": {},
            "description": "商品特征列表.商品在亚马逊页面上列出的主要特性和卖点"
          },
          "productImageUrl": {
            "type": "string",
            "description": "商品主图URL.商品在亚马逊页面上的主要展示图片链接"
          },
          "isVariantProduct": {
            "type": "boolean",
            "description": "是否为变体.true=该ASIN是父ASIN下的变体（如不同颜色、尺寸），false=独立ASIN或父ASIN"
          },
          "ppcTrafficSources": {
            "type": "array",
            "items": {},
            "description": "PPC付费广告流量来源标记.包含：sp广告（Sponsored Products）、头部品牌广告（Top Brand Ad）、底部品牌广告（Bottom Brand Ad）、视频广告（Video Ad）"
          },
          "productStarRating": {
            "type": "number",
            "description": "商品星级（0-5 星）"
          },
          "productRatingScore": {
            "type": "number",
            "description": "商品评分数值（0-5，亚马逊页面显示数值）"
          },
          "totalExposureScore": {
            "type": "number",
            "description": "总曝光分数.该商品在所有关键词下的曝光量综合评分，分数越高表示整体曝光量越大"
          },
          "brandAdKeywordCount": {
            "type": "integer",
            "description": "品牌广告关键词总数.该商品在品牌广告位（包括页面顶部和底部）展示的关键词总数"
          },
          "customerRatingCount": {
            "type": "integer",
            "description": "客户评分总数.该商品在亚马逊上获得的客户评分总数"
          },
          "dataPeriodStartDate": {
            "type": "string",
            "description": "数据周期起始日期 (yyyy-MM-dd)"
          },
          "monitoringStartTime": {
            "type": "string",
            "description": "商品关注时间.该商品被添加到监控系统的时间"
          },
          "videoAdKeywordCount": {
            "type": "integer",
            "description": "视频广告关键词数量.该商品在视频广告位展示的关键词总数"
          },
          "brandAdExposureRatio": {
            "type": "number",
            "description": "品牌广告曝光占比.品牌广告曝光分数占总曝光分数的百分比"
          },
          "brandAdExposureScore": {
            "type": "number",
            "description": "品牌广告曝光总分.该商品在品牌广告位的曝光量综合评分"
          },
          "topRatedKeywordCount": {
            "type": "integer",
            "description": "Top Rated推荐关键词数量.该商品在高评分推荐位展示的关键词总数"
          },
          "videoAdExposureRatio": {
            "type": "number",
            "description": "视频广告曝光占比.视频广告曝光分数占总曝光分数的百分比"
          },
          "videoAdExposureScore": {
            "type": "number",
            "description": "视频广告曝光总分.该商品在视频广告位的曝光量综合评分"
          },
          "recommendKeywordCount": {
            "type": "integer",
            "description": "推荐位关键词总数"
          },
          "topRatedExposureRatio": {
            "type": "number",
            "description": "Top Rated推荐曝光占比.TR推荐曝光分数占总曝光分数的百分比"
          },
          "topRatedExposureScore": {
            "type": "number",
            "description": "Top Rated推荐曝光总分.该商品在TR推荐位的曝光量综合评分"
          },
          "promotionalDealSources": {
            "type": "array",
            "items": {},
            "description": "促销活动流量来源标记.包含：优惠券（Coupon）、限时优惠（Limited Time Deal）、30天内最低价（Lowest Price in 30 Days）等"
          },
          "topBrandAdKeywordCount": {
            "type": "integer",
            "description": "页面顶部品牌广告关键词数量.该商品在搜索结果页面顶部品牌广告位展示的关键词总数"
          },
          "totalExposureScorePrev": {
            "type": "number",
            "description": "上周期总曝光分数"
          },
          "recommendAdKeywordCount": {
            "type": "integer",
            "description": "推荐位广告关键词数量"
          },
          "brandAdExposureScorePrev": {
            "type": "number",
            "description": "上周期品牌广告曝光分数"
          },
          "recentMonthlySalesBucket": {
            "type": "string",
            "description": "近一月销量桶（仅 keywordSummary 路径有值，形如 \"300+\" 或 \"1,000+\"）"
          },
          "recommendAdExposureScore": {
            "type": "number",
            "description": "推荐位广告曝光分数"
          },
          "totalTrafficKeywordCount": {
            "type": "integer",
            "description": "流量关键词总数.该商品在所有渠道（自然搜索+各类广告位+推荐位）被发现的关键词总数"
          },
          "videoAdExposureScorePrev": {
            "type": "number",
            "description": "上周期视频广告曝光分数"
          },
          "amazonsChoiceKeywordCount": {
            "type": "integer",
            "description": "Amazon's Choice关键词数量.该商品获得Amazon's Choice（亚马逊精选）推荐标志的关键词总数"
          },
          "bottomBrandAdKeywordCount": {
            "type": "integer",
            "description": "页面底部品牌广告关键词数量.该商品在搜索结果页面底部品牌广告位展示的关键词总数"
          },
          "naturalSearchKeywordCount": {
            "type": "integer",
            "description": "自然搜索关键词数量.该商品在自然搜索结果中被发现的关键词总数（不包括广告位）"
          },
          "amazonsChoiceExposureRatio": {
            "type": "number",
            "description": "Amazon's Choice曝光占比.AC推荐曝光分数占总曝光分数的百分比"
          },
          "amazonsChoiceExposureScore": {
            "type": "number",
            "description": "Amazon's Choice曝光总分.该商品作为AC推荐商品的曝光量综合评分"
          },
          "naturalSearchExposureRatio": {
            "type": "number",
            "description": "自然搜索曝光占比.自然搜索曝光分数占总曝光分数的百分比，反映自然流量的比重"
          },
          "naturalSearchExposureScore": {
            "type": "number",
            "description": "自然搜索曝光总分.该商品在自然搜索结果位置的曝光量综合评分"
          },
          "recommendNonadKeywordCount": {
            "type": "integer",
            "description": "推荐位非广告关键词数量"
          },
          "totalTrafficKeywordCountIn": {
            "type": "integer",
            "description": "本周期新进流量关键词数量"
          },
          "amazonRecommendationSources": {
            "type": "array",
            "items": {},
            "description": "亚马逊推荐流量来源标记.包含：Best Seller榜单、Amazon's Choice推荐、编辑推荐（ER）、高评分推荐（TR）、高频购买推荐（TRFOB）等"
          },
          "amazonsChoiceKeywordCountIn": {
            "type": "integer",
            "description": "本周期新进Amazon's Choice关键词数量"
          },
          "naturalSearchKeywordCountIn": {
            "type": "integer",
            "description": "本周期新进自然搜索关键词数量"
          },
          "naturalSearchTrafficSources": {
            "type": "array",
            "items": {},
            "description": "自然搜索流量来源标记.如果该数组不为空，表示商品有自然搜索流量。数组内容标记具体的自然搜索类型"
          },
          "nonAcRecommendExposureScore": {
            "type": "number",
            "description": "非AC推荐位曝光分数"
          },
          "recommendNonadExposureScore": {
            "type": "number",
            "description": "推荐位非广告曝光分数"
          },
          "totalTrafficKeywordCountOut": {
            "type": "integer",
            "description": "本周期退出流量关键词数量"
          },
          "amazonsChoiceKeywordCountOut": {
            "type": "integer",
            "description": "本周期退出Amazon's Choice关键词数量"
          },
          "frequentlyBoughtKeywordCount": {
            "type": "integer",
            "description": "高频购买推荐关键词数量.该商品在Top Rated Frequently Bought（高评分高频购买）推荐位展示的关键词总数"
          },
          "naturalSearchKeywordCountOut": {
            "type": "integer",
            "description": "本周期退出自然搜索关键词数量"
          },
          "totalTrafficKeywordCountPrev": {
            "type": "integer",
            "description": "上周期流量关键词总数"
          },
          "naturalSearchKeywordCountPrev": {
            "type": "integer",
            "description": "上周期自然搜索关键词数量"
          },
          "sponsoredProductsKeywordCount": {
            "type": "integer",
            "description": "SP广告关键词数量.该商品在Sponsored Products（赞助商品）广告位展示的关键词总数"
          },
          "amazonsChoiceExposureScorePrev": {
            "type": "number",
            "description": "上周期Amazon's Choice曝光分数"
          },
          "naturalSearchExposureScorePrev": {
            "type": "number",
            "description": "上周期自然搜索曝光分数"
          },
          "recommendPositionExposureScore": {
            "type": "number",
            "description": "推荐位曝光总分"
          },
          "sponsoredProductsExposureRatio": {
            "type": "number",
            "description": "SP广告曝光占比.SP广告曝光分数占总曝光分数的百分比，反映付费广告流量的比重"
          },
          "sponsoredProductsExposureScore": {
            "type": "number",
            "description": "SP广告曝光总分.该商品在SP广告位的曝光量综合评分"
          },
          "sponsoredProductsExposureScorePrev": {
            "type": "number",
            "description": "上周期SP广告曝光分数"
          },
          "editorialRecommendationsKeywordCount": {
            "type": "integer",
            "description": "Editorial Recommendations关键词数量.该商品在编辑推荐位展示的关键词总数"
          },
          "editorialRecommendationsExposureRatio": {
            "type": "number",
            "description": "Editorial Recommendations曝光占比.ER推荐曝光分数占总曝光分数的百分比"
          },
          "editorialRecommendationsExposureScore": {
            "type": "number",
            "description": "Editorial Recommendations曝光总分.该商品在编辑推荐位的曝光量综合评分"
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
      "description": "本次实际返回的数据数量"
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
    },
    "variantsNum": {
      "type": "integer",
      "description": "有关键词的变体商品数量"
    },
    "isParentAsin": {
      "type": "boolean",
      "description": "搜索的是否是pasin"
    },
    "noKeywordVariantsNum": {
      "type": "integer",
      "description": "无关键词的变体商品数量"
    }
  }
}
```

</details>
