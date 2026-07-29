# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "maxLength": 1000,
      "description": "ASIN码"
    },
    "desc": {
      "type": "boolean",
      "default": true,
      "description": "是否降序，默认传 true "
    },
    "sortBy": {
      "type": "string",
      "pattern": "lastRank|adLastRank|updateTime|searchesRank|estSearchesNum",
      "examples": [
        {
          "value": "",
          "summary": "默认系统排序"
        },
        {
          "value": "lastRank",
          "summary": "自然排名"
        },
        {
          "value": "adLastRank",
          "summary": "广告排名"
        },
        {
          "value": "updateTime",
          "summary": "关键词抓取时间"
        },
        {
          "value": "searchesRank",
          "summary": "搜索排名"
        },
        {
          "value": "estSearchesNum",
          "summary": "月搜索量"
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
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "关键词，尽量翻译成对应国家站点的语言"
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
      "description": "每页数量,最小10，最大100，默认也是100"
    },
    "conditions": {
      "type": "string",
      "pattern": "^(nfPosition|isSpAd|isBrandAd|isVedioAd|isAC|isAccurateKw|isAccurateTailKw|isPurchaseKw|isQualityKw|isStableKw|isLossKw|isInvalidKw|isMultiVariantKw|isSearchVolUpKw|isSearchVolDownKw|totalPeriod\\.in|nfKeywordCnt\\.(total|in)|adKeywordCnt\\.(total|in)|allSpKeywordCnt\\.(total|in)|spKeywordCnt\\.(total|in)|recSpKeywordCnt\\.(total|in)|allSbKeywordCnt\\.(total|in)|sbKeywordCnt\\.(total|in)|sbvKeywordCnt\\.(total|in))(,(nfPosition|isSpAd|isBrandAd|isVedioAd|isAC|isAccurateKw|isAccurateTailKw|isPurchaseKw|isQualityKw|isStableKw|isLossKw|isInvalidKw|isMultiVariantKw|isSearchVolUpKw|isSearchVolDownKw|totalPeriod\\.in|nfKeywordCnt\\.(total|in)|adKeywordCnt\\.(total|in)|allSpKeywordCnt\\.(total|in)|spKeywordCnt\\.(total|in)|recSpKeywordCnt\\.(total|in)|allSbKeywordCnt\\.(total|in)|sbKeywordCnt\\.(total|in)|sbvKeywordCnt\\.(total|in)))*$",
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
          "value": "isBrandAd",
          "summary": "品牌广告词"
        },
        {
          "value": "isVedioAd",
          "summary": "视频广告词"
        },
        {
          "value": "isAC",
          "summary": "ac推荐词"
        },
        {
          "value": "isAccurateKw",
          "summary": "精准流量词"
        },
        {
          "value": "isAccurateTailKw",
          "summary": "精准长尾词"
        },
        {
          "value": "isPurchaseKw",
          "summary": "出单词"
        },
        {
          "value": "isQualityKw",
          "summary": "转化优质词"
        },
        {
          "value": "isStableKw",
          "summary": "转化平稳词"
        },
        {
          "value": "isLossKw",
          "summary": "转化流失词"
        },
        {
          "value": "isInvalidKw",
          "summary": "无效曝光词"
        },
        {
          "value": "isMultiVariantKw",
          "summary": "多变体自然位词"
        },
        {
          "value": "isSearchVolUpKw",
          "summary": "搜索量同比增长词"
        },
        {
          "value": "isSearchVolDownKw",
          "summary": "搜索量同比下降词"
        },
        {
          "value": "totalPeriod.in",
          "summary": "新进全部流量词"
        },
        {
          "value": "nfKeywordCnt.total",
          "summary": "有自然曝光的流量词"
        },
        {
          "value": "nfKeywordCnt.in",
          "summary": "新进自然流量词"
        },
        {
          "value": "adKeywordCnt.total",
          "summary": "有广告曝光的流量词"
        },
        {
          "value": "adKeywordCnt.in",
          "summary": "新进广告流量词"
        },
        {
          "value": "allSpKeywordCnt.total",
          "summary": "SP广告流量词"
        },
        {
          "value": "allSpKeywordCnt.in",
          "summary": "新进SP广告流量词"
        },
        {
          "value": "spKeywordCnt.total",
          "summary": "SP常规流量词"
        },
        {
          "value": "spKeywordCnt.in",
          "summary": "新进SP常规流量词"
        },
        {
          "value": "recSpKeywordCnt.total",
          "summary": "SP推荐流量词"
        },
        {
          "value": "recSpKeywordCnt.in",
          "summary": "新进SP推荐流量词"
        },
        {
          "value": "allSbKeywordCnt.total",
          "summary": "SB广告流量词"
        },
        {
          "value": "allSbKeywordCnt.in",
          "summary": "新进SB广告流量词"
        },
        {
          "value": "sbKeywordCnt.total",
          "summary": "SB常规流量词"
        },
        {
          "value": "sbKeywordCnt.in",
          "summary": "新进SB常规流量词"
        },
        {
          "value": "sbvKeywordCnt.total",
          "summary": "SBV流量词"
        },
        {
          "value": "sbvKeywordCnt.in",
          "summary": "新进SBV流量词"
        }
      ],
      "description": "条件筛选,多个条件以英文逗号隔开"
    },
    "timePieceType": {
      "type": "string",
      "default": "latelyDay",
      "pattern": "latelyDay|month|week",
      "examples": [
        {
          "value": "latelyDay",
          "summary": "最近N天"
        },
        {
          "value": "month",
          "summary": "某月"
        },
        {
          "value": "week",
          "summary": "某周"
        }
      ],
      "description": "时间片段类型：latelyDay=最近N天/month=某月/week=某周"
    },
    "timePieceValue": {
      "type": "string",
      "default": "7",
      "examples": [
        {
          "value": "7",
          "summary": "最近 7 天"
        },
        {
          "value": "30",
          "summary": "最近 30 天"
        },
        {
          "value": "2026-04",
          "summary": "2026 年 4 月"
        },
        {
          "value": "2026-04-13",
          "summary": "2026-04-13 开始的一周"
        }
      ],
      "maxLength": 1000,
      "description": "时间片段值：latelyDay 时仅支持 7 或 30；month 时为 YYYY-MM；week 时为周开始日期 YYYY-MM-DD"
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
            "description": "商品asin"
          },
          "keyword": {
            "type": "string",
            "description": "关键词"
          },
          "updateTime": {
            "type": "string",
            "description": "关键词数据更新时间"
          },
          "brandAdScore": {
            "type": "number",
            "description": "SB 品牌广告得分.该关键词下 Sponsored Brands 品牌广告的流量得分（含常规 + 视频，总和）"
          },
          "trafficShare": {
            "type": "number",
            "description": "流量占比.该关键词为商品带来的流量占所有关键词总流量的比例，其中1表示100%"
          },
          "videoAdScore": {
            "type": "number",
            "description": "SBV 视频广告得分.该关键词下 Sponsored Brands Video 视频广告的流量得分"
          },
          "adRankDisplay": {
            "type": "string",
            "description": "广告排名显示文本.SP广告排名的字符串表示形式"
          },
          "periodEndDate": {
            "type": "string",
            "description": "本周期结束日期.本周期（周粒度）的最大时间（站点时间），= 开始周 + 7 天"
          },
          "productAdRank": {
            "type": "integer",
            "description": "商品SP广告排名.该商品在此关键词下的Sponsored Products广告位中的排名位置，如3表示排在广告位第3位"
          },
          "lastAdRankTime": {
            "type": "string",
            "description": "最近有效SP广告排名的时间.商品在此关键词下最近一次Sponsored Products广告排名的记录时间"
          },
          "paidTrafficShare": {
            "type": "number",
            "description": "付费广告流量得分占比.广告流量得分 / 总得分；广告合计 = sp + sb + sbv + recAd"
          },
          "translateKeyword": {
            "type": "string",
            "description": "关键词翻译.关键词的站点本地化译文（如中文），v2 新增"
          },
          "naturalRankDisplay": {
            "type": "string",
            "description": "自然排名显示文本.自然搜索排名的字符串表示形式"
          },
          "productNaturalRank": {
            "type": "integer",
            "description": "商品自然搜索排名.该商品在此关键词下的自然搜索结果中的位置排名，如1表示排在搜索结果第1位（首位）"
          },
          "weeklySearchVolume": {
            "type": "integer",
            "description": "周搜索量.该关键词在亚马逊平台每周的预估搜索次数"
          },
          "lastNaturalRankTime": {
            "type": "string",
            "description": "最近有效自然排名的时间.商品在此关键词下最近一次有效自然搜索排名的记录时间"
          },
          "naturalTrafficScore": {
            "type": "number",
            "description": "自然流量得分.该关键词为该 ASIN 带来的自然搜索曝光得分，0 = 无自然流量曝光"
          },
          "naturalTrafficShare": {
            "type": "number",
            "description": "自然流量得分占比.自然搜索流量得分 / 总得分"
          },
          "displayPositionTypes": {
            "type": "array",
            "items": {},
            "description": "商品展示位置类型数组.该关键词下商品的展示位置，可能包含以下值：natural=自然搜索结果位；ac=Amazon's Choice推荐位；sp=Sponsored Products赞助商品广告位；top=页面顶部品牌广告位；bottom=页面底部品牌广告位；er=Editorial Recommendations编辑推荐位；vedio=视频广告位；tr=Top Rated高评分推荐位；trfob=Top Rated Frequently Bought高频购买推荐位。示例：[\"natural\"]表示仅在自然搜索结果中展示，[\"natural\",\"sp\"]表示同时在自然搜索和广告位展示"
          },
          "keywordPopularityRank": {
            "type": "integer",
            "description": "关键词搜索热度排名.该关键词的月搜索量在亚马逊所有关键词中的排名，数值越小表示搜索量越大，如203表示该词搜索热度排第203名"
          },
          "sponsoredProductsScore": {
            "type": "number",
            "description": "SP 广告常规得分.该关键词下 Sponsored Products 常规位的流量得分（不含 SP 推荐位）"
          },
          "clickConcentrationShare": {
            "type": "number",
            "description": "ABA TOP3 点击集中度.衡量该关键词下点击是否集中在头部几款 ASIN 上的指标；注意：不是转化率"
          },
          "conversionPerformanceMarkers": {
            "type": "array",
            "items": {},
            "description": "转化效果标记数组.标记该关键词的转化表现，可能包含以下值：isPurchaseKw=出单词（通过该词产生过订单）；isQualityKw=转化优质词（转化率高的优质关键词）；isStableKw=转化平稳词（转化表现稳定的关键词）；isLossKw=转化流失词（曾经转化好但现在流失的关键词）；isInvalidKw=无效曝光词（有曝光但无转化的无效词）。示例：[\"isPurchaseKw\",\"isStableKw\"]"
          },
          "sponsoredRecommendationScore": {
            "type": "number",
            "description": "SP 推荐位得分.该关键词下 SP 推荐位（Trending now / Seen on social media / Customers frequently viewed 等）合计得分"
          },
          "trafficCharacteristicMarkers": {
            "type": "array",
            "items": {},
            "description": "关键词流量特征标记数组.标记该关键词的流量特征，可能包含以下值：isMainKw=主要流量词（为该商品带来主要流量的核心词）；isAccurateKw=精准流量词（与商品高度相关的精准词）；isAccurateAboveKw=精准大词（搜索量大且精准的关键词）；isAccurateTailKw=精准长尾词（搜索量较小但精准的长尾关键词）。示例：[\"isMainKw\",\"isAccurateKw\"]"
          },
          "clickToPurchaseConversionRate": {
            "type": "number",
            "description": "点击到购买的转化率（purchaseQty / clickQty）"
          },
          "totalSearchResultProductCount": {
            "type": "integer",
            "description": "该关键词下搜索结果商品总数（在售产品数）"
          },
          "sponsoredRecommendationBreakdown": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "SP 推荐位得分明细.数组，每项 {title, score, scoreRatio}；title 示例：Trending now / Seen on social media / 4 stars and above / Customers frequently viewed"
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
    "hasVaiants": {
      "type": "boolean",
      "description": "是否有变体"
    },
    "isParentAsin": {
      "type": "boolean",
      "description": "是否是父体"
    },
    "abaCreateDateWeek": {
      "type": "string",
      "description": "最新周aba时间"
    }
  }
}
```

</details>
