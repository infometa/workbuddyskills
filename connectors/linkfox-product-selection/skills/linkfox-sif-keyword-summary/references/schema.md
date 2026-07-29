# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "searchKeyword"
  ],
  "properties": {
    "desc": {
      "type": "boolean",
      "default": true,
      "description": "是否降序，默认传 true "
    },
    "asins": {
      "type": "string",
      "examples": [
        {
          "value": "B01NBNDC1T",
          "summary": "单 ASIN 过滤"
        },
        {
          "value": "B01NBNDC1T,B09VLJJPL6",
          "summary": "多 ASIN 过滤"
        }
      ],
      "maxLength": 1000,
      "description": "ASIN 过滤列表，多个用英文逗号分隔；不传则返回该关键词下所有 ASIN"
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
          "value": "2026-04-11",
          "summary": "2026-04-11"
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
      "default": 100,
      "maximum": 100,
      "minimum": 10,
      "description": "每页数量，最小10，最大100，默认也是100"
    },
    "condition": {
      "type": "string",
      "pattern": "nfPosition|isSpAd|isVedioAd|isBrandAd|isPPCAd|isSearchRecommend|acAd|totalPeriod\\.in|nfKeywordCnt\\.(total|in)|adKeywordCnt\\.(total|in)|allSpKeywordCnt\\.(total|in)|spKeywordCnt\\.(total|in)|recSpKeywordCnt\\.(total|in)|allSbKeywordCnt\\.(total|in)|sbKeywordCnt\\.(total|in)|sbvKeywordCnt\\.(total|in)",
      "examples": [
        {
          "value": "nfPosition",
          "summary": "自然流量词"
        },
        {
          "value": "isSpAd",
          "summary": "sp广告词"
        },
        {
          "value": "isVedioAd",
          "summary": "视频广告词"
        },
        {
          "value": "isBrandAd",
          "summary": "品牌广告词"
        },
        {
          "value": "isPPCAd",
          "summary": "ppc广告词"
        },
        {
          "value": "isSearchRecommend",
          "summary": "搜索推荐词"
        },
        {
          "value": "acAd",
          "summary": "SP推荐"
        },
        {
          "value": "totalPeriod.in",
          "summary": "新进全部流量词"
        },
        {
          "value": "nfKeywordCnt.total",
          "summary": "自然流量词数"
        },
        {
          "value": "nfKeywordCnt.in",
          "summary": "新进自然流量词数"
        },
        {
          "value": "adKeywordCnt.total",
          "summary": "广告流量词数"
        },
        {
          "value": "adKeywordCnt.in",
          "summary": "新进广告流量词数"
        },
        {
          "value": "allSpKeywordCnt.total",
          "summary": "SP广告流量词数"
        },
        {
          "value": "allSpKeywordCnt.in",
          "summary": "新进SP广告流量词数"
        },
        {
          "value": "spKeywordCnt.total",
          "summary": "SP常规流量词数"
        },
        {
          "value": "spKeywordCnt.in",
          "summary": "新进SP常规流量词数"
        },
        {
          "value": "recSpKeywordCnt.total",
          "summary": "SP推荐流量词数"
        },
        {
          "value": "recSpKeywordCnt.in",
          "summary": "新进SP推荐流量词数"
        },
        {
          "value": "allSbKeywordCnt.total",
          "summary": "SB广告流量词数"
        },
        {
          "value": "allSbKeywordCnt.in",
          "summary": "新进SB广告流量词数"
        },
        {
          "value": "sbKeywordCnt.total",
          "summary": "SB常规流量词数"
        },
        {
          "value": "sbKeywordCnt.in",
          "summary": "新进SB常规流量词数"
        },
        {
          "value": "sbvKeywordCnt.total",
          "summary": "SBV流量词数"
        },
        {
          "value": "sbvKeywordCnt.in",
          "summary": "新进SBV流量词数"
        }
      ],
      "description": "条件筛选,每次只能传一个"
    },
    "startDate": {
      "type": "string",
      "examples": [
        {
          "value": "2026-04-05",
          "summary": "2026-04-05"
        }
      ],
      "maxLength": 1000,
      "description": "开始日期 yyyy-MM-dd（last7d=false 时生效，不填取系统最新整周）"
    },
    "searchKeyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "搜索关键词，尽量翻译成对应国家站点的语言"
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
          "keyword": {
            "type": "string",
            "description": "关键词"
          },
          "productPrice": {
            "type": "number",
            "description": "商品售价.当前亚马逊页面显示的商品价格"
          },
          "productTitle": {
            "type": "string",
            "description": "商品标题.亚马逊页面显示的完整商品标题"
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
          "productUpdateTime": {
            "type": "string",
            "description": "产品更新时间.格式 yyyy-MM-dd HH:mm:ss"
          },
          "productRatingScore": {
            "type": "number",
            "description": "商品评分"
          },
          "totalExposureRatio": {
            "type": "number",
            "description": "总流量份额"
          },
          "totalExposureScore": {
            "type": "number",
            "description": "总曝光分数.该商品在所有关键词下的曝光量综合评分，分数越高表示整体曝光量越大"
          },
          "customerRatingCount": {
            "type": "integer",
            "description": "客户评分总数.该商品在亚马逊上获得的客户评分总数"
          },
          "dataPeriodStartDate": {
            "type": "string",
            "description": "数据周期起始日期 (yyyy-MM-dd)"
          },
          "brandAdExposureRatio": {
            "type": "number",
            "description": "品牌广告曝光占比.品牌广告曝光分数占总曝光分数的百分比"
          },
          "brandAdExposureScore": {
            "type": "number",
            "description": "品牌广告曝光总分.该商品在品牌广告位的曝光量综合评分"
          },
          "videoAdExposureRatio": {
            "type": "number",
            "description": "视频广告曝光占比.视频广告曝光分数占总曝光分数的百分比"
          },
          "videoAdExposureScore": {
            "type": "number",
            "description": "视频广告曝光总分.该商品在视频广告位的曝光量综合评分"
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
          "recommendAdExposureRatio": {
            "type": "number",
            "description": "推荐位广告流量份额"
          },
          "recommendAdExposureScore": {
            "type": "number",
            "description": "推荐位广告曝光分数"
          },
          "keywordTotalExposureScore": {
            "type": "number",
            "description": "关键词总得分"
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
          "amazonRecommendationSources": {
            "type": "array",
            "items": {},
            "description": "亚马逊推荐流量来源标记.包含：Best Seller榜单、Amazon's Choice推荐、编辑推荐（ER）、高评分推荐（TR）、高频购买推荐（TRFOB）等"
          },
          "keywordBrandAdExposureScore": {
            "type": "number",
            "description": "关键词品牌广告得分"
          },
          "keywordNaturalExposureScore": {
            "type": "number",
            "description": "关键词自然得分"
          },
          "keywordVideoAdExposureScore": {
            "type": "number",
            "description": "关键词视频广告得分"
          },
          "naturalSearchTrafficSources": {
            "type": "array",
            "items": {},
            "description": "自然搜索流量来源标记.如果该数组不为空，表示商品有自然搜索流量。数组内容标记具体的自然搜索类型"
          },
          "recommendNonadExposureRatio": {
            "type": "number",
            "description": "推荐位非广告流量份额"
          },
          "recommendNonadExposureScore": {
            "type": "number",
            "description": "推荐位非广告曝光分数"
          },
          "keywordRecommendExposureScore": {
            "type": "number",
            "description": "关键词推荐位得分"
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
          "keywordRecommendAdExposureScore": {
            "type": "number",
            "description": "关键词推荐位广告得分"
          },
          "comprehensiveNaturalExposureRatio": {
            "type": "number",
            "description": "综合自然流量份额"
          },
          "comprehensiveNaturalExposureScore": {
            "type": "number",
            "description": "综合自然流量得分.自然搜索 + 推荐位非广告"
          },
          "keywordAmazonsChoiceExposureScore": {
            "type": "number",
            "description": "关键词Amazon's Choice得分"
          },
          "keywordRecommendNonadExposureScore": {
            "type": "number",
            "description": "关键词推荐位非广告得分"
          },
          "editorialRecommendationsExposureRatio": {
            "type": "number",
            "description": "Editorial Recommendations曝光占比.ER推荐曝光分数占总曝光分数的百分比"
          },
          "editorialRecommendationsExposureScore": {
            "type": "number",
            "description": "Editorial Recommendations曝光总分.该商品在编辑推荐位的曝光量综合评分"
          },
          "keywordSponsoredProductsExposureScore": {
            "type": "number",
            "description": "关键词SP广告得分"
          },
          "keywordComprehensiveNaturalExposureScore": {
            "type": "number",
            "description": "关键词综合自然得分.自然 + 推荐位非广告"
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
    }
  }
}
```

</details>
