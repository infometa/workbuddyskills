# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "keyword"
  ],
  "properties": {
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "golf",
          "summary": "示例关键词"
        }
      ],
      "maxLength": 1000,
      "description": "要分析的亚马逊搜索关键词"
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
    "shareOfVoice": {
      "type": "object",
      "required": [],
      "properties": {
        "id": {
          "type": "string",
          "description": "数据标识(市场/关键词)"
        },
        "type": {
          "type": "string",
          "description": "响应资源类型(固定 share_of_voice)"
        },
        "brands": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [],
            "properties": {
              "brand": {
                "type": "string",
                "description": "品牌名称"
              },
              "organicBasicSov": {
                "type": "number",
                "description": "自然基础声量份额；可为空"
              },
              "organicProducts": {
                "type": "integer",
                "description": "自然搜索结果中该品牌产品数；可为空"
              },
              "combinedBasicSov": {
                "type": "number",
                "description": "综合基础声量份额(出现次数/总结果)"
              },
              "combinedProducts": {
                "type": "integer",
                "description": "综合(自然+赞助)前三页内该品牌产品数"
              },
              "sponsoredBasicSov": {
                "type": "number",
                "description": "赞助基础声量份额；可为空"
              },
              "sponsoredProducts": {
                "type": "integer",
                "description": "赞助位中该品牌产品数；可为空"
              },
              "organicWeightedSov": {
                "type": "number",
                "description": "自然加权声量份额；可为空"
              },
              "combinedWeightedSov": {
                "type": "number",
                "description": "综合加权声量份额(0–1，含Amazon Choice徽标与位次权重)"
              },
              "organicAveragePrice": {
                "type": "number",
                "description": "自然结果平均价格；可为空"
              },
              "combinedAveragePrice": {
                "type": "number",
                "description": "综合平均价格(市场货币)"
              },
              "sponsoredWeightedSov": {
                "type": "number",
                "description": "赞助加权声量份额；可为空"
              },
              "sponsoredAveragePrice": {
                "type": "number",
                "description": "赞助结果平均价格；可为空"
              },
              "organicAveragePosition": {
                "type": "number",
                "description": "自然结果平均排名；可为空"
              },
              "combinedAveragePosition": {
                "type": "number",
                "description": "综合平均排名位置"
              },
              "sponsoredAveragePosition": {
                "type": "number",
                "description": "赞助结果平均排名；可为空"
              }
            }
          },
          "description": "各品牌在前三页的声量与排名、价格等指标"
        },
        "topAsins": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [],
            "properties": {
              "asin": {
                "type": "string",
                "description": "ASIN"
              },
              "name": {
                "type": "string",
                "description": "商品标题/描述；可为空"
              },
              "brand": {
                "type": "string",
                "description": "品牌；可为空"
              },
              "clicks": {
                "type": "integer",
                "description": "统计区间内点击次数"
              },
              "conversions": {
                "type": "integer",
                "description": "统计区间内购买次数"
              },
              "conversionRate": {
                "type": "number",
                "description": "转化率(购买/点击)；可为空"
              }
            }
          },
          "description": "TOP3 ASIN的点击、购买与转化率；可为空"
        },
        "updatedAt": {
          "type": "string",
          "description": "数据刷新时间(ISO 8601)"
        },
        "productCount": {
          "type": "integer",
          "description": "返回数据中包含的ASIN数量(搜索结果产品总数)"
        },
        "topAsinsModelEndDate": {
          "type": "string",
          "description": "TOP3 ASIN点击与转化统计区间终点(YYYY-MM-DD)；可为空"
        },
        "topAsinsModelStartDate": {
          "type": "string",
          "description": "TOP3 ASIN点击与转化统计区间起点(YYYY-MM-DD)；可为空"
        },
        "exactSuggestedBidMedian": {
          "type": "number",
          "description": "所选市场货币下，赢得竞价的中位估算成本(PPC)"
        },
        "estimated30DaySearchVolume": {
          "type": "integer",
          "description": "该关键词精确匹配30天搜索量估算(次)"
        }
      }
    }
  }
}
```

</details>
