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
    "page": {
      "type": "integer",
      "default": 1,
      "description": "页码（从1开始）"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "关键词（必填，并根据所选国家，翻译关键词为对应国家的语言）"
    },
    "pageSize": {
      "type": "integer",
      "default": 50,
      "maximum": 100,
      "minimum": 10,
      "description": "每页返回数量（10-100）"
    },
    "sortType": {
      "type": "string",
      "default": "desc",
      "pattern": "^(desc|asc)$",
      "examples": [
        {
          "value": "desc",
          "summary": "降序"
        },
        {
          "value": "asc",
          "summary": "升序"
        }
      ],
      "description": "排序方式"
    },
    "sortField": {
      "type": "string",
      "default": "unitsSoldT7",
      "pattern": "^(clickConversionRateT7|demand|avgPrice|maximumPrice|minimumPrice|productCount|searchConversionRateT7|searchVolumeT7|unitsSoldT7|searchVolumeGrowthT7|clickCountT90|clickCountT7|brandCount|top5BrandsClickShare|newProductsLaunchedT180|successfulLaunchesT180|launchRateT180|top5ProductsClickShare|returnRateT360|clickConversionRateT90|searchConversionRateT90|searchVolumeT90|unitsSoldT90|unitsSoldGrowthT90|searchVolumeGrowthT90|acos|profitRate50)$",
      "examples": [
        {
          "value": "clickConversionRateT7",
          "summary": "7天点击转化率"
        },
        {
          "value": "demand",
          "summary": "需求得分"
        },
        {
          "value": "avgPrice",
          "summary": "商品均价"
        },
        {
          "value": "maximumPrice",
          "summary": "商品最高价"
        },
        {
          "value": "minimumPrice",
          "summary": "商品最低价"
        },
        {
          "value": "productCount",
          "summary": "商品数量"
        },
        {
          "value": "searchConversionRateT7",
          "summary": "7天搜索转化率"
        },
        {
          "value": "searchVolumeT7",
          "summary": "7天搜索量"
        },
        {
          "value": "unitsSoldT7",
          "summary": "7天销量"
        },
        {
          "value": "searchVolumeGrowthT7",
          "summary": "搜索增长率"
        },
        {
          "value": "clickCountT90",
          "summary": "90天点击量"
        },
        {
          "value": "clickCountT7",
          "summary": "周点击量"
        },
        {
          "value": "brandCount",
          "summary": "品牌数量"
        },
        {
          "value": "top5BrandsClickShare",
          "summary": "TOP5品牌份额"
        },
        {
          "value": "newProductsLaunchedT180",
          "summary": "180d新品成功率-发布数"
        },
        {
          "value": "successfulLaunchesT180",
          "summary": "180d新品成功率-新品数"
        },
        {
          "value": "launchRateT180",
          "summary": "180d新品成功率-发布率"
        },
        {
          "value": "top5ProductsClickShare",
          "summary": "top5商品点击份额"
        },
        {
          "value": "returnRateT360",
          "summary": "退货率"
        },
        {
          "value": "clickConversionRateT90",
          "summary": "90天点击转化率"
        },
        {
          "value": "searchConversionRateT90",
          "summary": "90天搜索转化率"
        },
        {
          "value": "searchVolumeT90",
          "summary": "90天搜索量"
        },
        {
          "value": "unitsSoldT90",
          "summary": "90天销量"
        },
        {
          "value": "unitsSoldGrowthT90",
          "summary": "90天销量增长率"
        },
        {
          "value": "searchVolumeGrowthT90",
          "summary": "90天搜索增长率"
        },
        {
          "value": "acos",
          "summary": "No comments found."
        },
        {
          "value": "profitRate50",
          "summary": "50%自然单的利润率"
        }
      ],
      "description": "排序字段"
    },
    "avgPriceMax": {
      "type": "number",
      "description": "平均价格（当前）最大值"
    },
    "avgPriceMin": {
      "type": "number",
      "description": "平均价格（当前）最小值"
    },
    "countryCode": {
      "type": "string",
      "default": "US",
      "pattern": "^(US|JP|DE)$",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "DE",
          "summary": "德国"
        }
      ],
      "description": "国家编码"
    },
    "cpcMediumMax": {
      "type": "number",
      "description": "CPC（当前）最大值"
    },
    "cpcMediumMin": {
      "type": "number",
      "description": "CPC（当前）最小值"
    },
    "brandCountMax": {
      "type": "integer",
      "description": "品牌数量最大值"
    },
    "brandCountMin": {
      "type": "integer",
      "description": "品牌数量最小值"
    },
    "avgBrandAgeMax": {
      "type": "number",
      "description": "平均品牌年龄（当前）最大值"
    },
    "avgBrandAgeMin": {
      "type": "number",
      "description": "平均品牌年龄（当前）最小值"
    },
    "unitsSoldT7Max": {
      "type": "integer",
      "description": "销售量（7天统计）最大值"
    },
    "unitsSoldT7Min": {
      "type": "integer",
      "description": "销售量（7天统计）最小值"
    },
    "clickCountT7Max": {
      "type": "integer",
      "description": "点击量（7天统计）最大值"
    },
    "clickCountT7Min": {
      "type": "integer",
      "description": "点击量（7天统计）最小值"
    },
    "productCountMax": {
      "type": "integer",
      "description": "商品数量（当前）最大值"
    },
    "productCountMin": {
      "type": "integer",
      "description": "商品数量（当前）最小值"
    },
    "avgBrandAgeQoqMax": {
      "type": "number",
      "description": "平均品牌年龄（90天统计）最大值"
    },
    "avgBrandAgeQoqMin": {
      "type": "number",
      "description": "平均品牌年龄（90天统计）最小值"
    },
    "avgBrandAgeYoyMax": {
      "type": "number",
      "description": "平均品牌年龄（360天统计）最大值"
    },
    "avgBrandAgeYoyMin": {
      "type": "number",
      "description": "平均品牌年龄（360天统计）最小值"
    },
    "launchRateT180Max": {
      "type": "number",
      "description": "发布商品的成功率（180天统计）最大值，数值范围为0-1,代表0%-100%"
    },
    "launchRateT180Min": {
      "type": "number",
      "description": "发布商品的成功率（180天统计）最小值，数值范围为0-1,代表0%-100%"
    },
    "returnRateT360Max": {
      "type": "number",
      "description": "退货率（360天统计）最大值，数值范围为0-1,代表0%-100%"
    },
    "returnRateT360Min": {
      "type": "number",
      "description": "退货率（360天统计）最小值，数值范围为0-1,代表0%-100%"
    },
    "searchVolumeT7Max": {
      "type": "integer",
      "description": "搜索量（7天统计）最大值"
    },
    "searchVolumeT7Min": {
      "type": "integer",
      "description": "搜索量（7天统计）最小值"
    },
    "newProductRateT180": {
      "type": "number",
      "description": "新商品占比（180天统计）最小值，数值范围为0-1,代表0%-100%"
    },
    "avgSellingPartnerAgeMax": {
      "type": "number",
      "description": "平均销售伙伴年龄最大值"
    },
    "avgSellingPartnerAgeMin": {
      "type": "number",
      "description": "平均销售伙伴年龄最小值"
    },
    "top5BrandsClickShareMax": {
      "type": "number",
      "description": "前5个品牌所占细分市场的点击量份额最大值，数值范围为0-1,代表0%-100%"
    },
    "top5BrandsClickShareMin": {
      "type": "number",
      "description": "前5个品牌所占细分市场的点击量份额最小值，数值范围为0-1,代表0%-100%"
    },
    "clickConversionRateT7Max": {
      "type": "number",
      "description": "点击转换率（7天统计）最大值，数值范围为0-1,代表0%-100%"
    },
    "clickConversionRateT7Min": {
      "type": "number",
      "description": "点击转换率（7天统计）最小值，数值范围为0-1,代表0%-100%"
    },
    "top5ProductsClickShareMax": {
      "type": "number",
      "description": "排名前 5 位的商品点击份额（当前）最大值，数值范围为0-1,代表0%-100%"
    },
    "top5ProductsClickShareMin": {
      "type": "number",
      "description": "排名前 5 位的商品点击份额（当前）最小值，数值范围为0-1,代表0%-100%"
    },
    "avgSellingPartnerAgeQoqMax": {
      "type": "number",
      "description": "平均销售伙伴年龄（90天统计）最大值"
    },
    "avgSellingPartnerAgeQoqMin": {
      "type": "number",
      "description": "平均销售伙伴年龄（90天统计）最小值"
    },
    "avgSellingPartnerAgeYoyMax": {
      "type": "number",
      "description": "平均销售伙伴年龄（360天统计）最大值"
    },
    "avgSellingPartnerAgeYoyMin": {
      "type": "number",
      "description": "平均销售伙伴年龄（360天统计）最小值"
    },
    "sponsoredProductsPercentageMax": {
      "type": "number",
      "description": "SP广告占比最大值，数值范围为0-1,代表0%-100%"
    },
    "sponsoredProductsPercentageMin": {
      "type": "number",
      "description": "SP广告占比最小值，数值范围为0-1,代表0%-100%"
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
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "cpc": {
            "type": "object",
            "required": [],
            "properties": {
              "low": {
                "type": "number",
                "description": "最低价"
              },
              "high": {
                "type": "number",
                "description": "最高价"
              },
              "medium": {
                "type": "number",
                "description": "中间价"
              }
            }
          },
          "acos": {
            "type": "number",
            "description": "（ACOS）广告销售成本比"
          },
          "demand": {
            "type": "integer",
            "description": "细分市场得分"
          },
          "nicheId": {
            "type": "string",
            "description": "细分市场ID"
          },
          "avgPrice": {
            "type": "number",
            "description": "产品均价"
          },
          "brandCount": {
            "type": "integer",
            "description": "品牌数量"
          },
          "nicheTitle": {
            "type": "string",
            "description": "细分市场标题"
          },
          "maximumPrice": {
            "type": "number",
            "description": "产品最高价"
          },
          "minimumPrice": {
            "type": "number",
            "description": "产品最低价"
          },
          "productCount": {
            "type": "integer",
            "description": "商品数量"
          },
          "categorieList": {
            "type": "array",
            "items": {},
            "description": "商品品类列表"
          },
          "translationZh": {
            "type": "string",
            "description": "细分市场标题(中文)"
          },
          "avgBrandAgeNow": {
            "type": "number",
            "description": "平均品牌年龄(当前)"
          },
          "breakEvenRatio": {
            "type": "number",
            "description": "盈亏平衡比率"
          },
          "unitsSoldWeekly": {
            "type": "integer",
            "description": "销售数量（周数据）"
          },
          "clickCountWeekly": {
            "type": "integer",
            "description": "点击量（周数据）"
          },
          "returnRateAnnual": {
            "type": "number",
            "description": "退货率（全年数据）"
          },
          "searchVolumeWeekly": {
            "type": "integer",
            "description": "搜索量（周数据）"
          },
          "unitsSoldQuarterly": {
            "type": "integer",
            "description": "销售数量（季度数据）"
          },
          "clickCountQuarterly": {
            "type": "integer",
            "description": "点击量（季度数据）"
          },
          "avgBrandAgeQuarterly": {
            "type": "number",
            "description": "平均品牌年龄(季度数据)"
          },
          "launchRateSemiannual": {
            "type": "number",
            "description": "发布商品的成功率（半年数据）"
          },
          "top5BrandsClickShare": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额"
          },
          "referenceAsinImageUrl": {
            "type": "string",
            "description": "细分市场参考图片地址"
          },
          "searchVolumeQuarterly": {
            "type": "integer",
            "description": "搜索量（季度数据）"
          },
          "top5ProductsClickShare": {
            "type": "number",
            "description": "排名前 5 位的商品点击份额"
          },
          "searchVolumeGrowthWeekly": {
            "type": "number",
            "description": "搜索量增长率（周数据）"
          },
          "searchConversionRateWeekly": {
            "type": "number",
            "description": "搜索转换率（周数据）"
          },
          "clickToSaleConversionWeekly": {
            "type": "number",
            "description": "点击转换率（周数据）"
          },
          "profitMarginGt50PctSkuRatio": {
            "type": "number",
            "description": "利润率大于50%的商品比例"
          },
          "searchVolumeGrowthQuarterly": {
            "type": "number",
            "description": "搜索量增长率（季度数据）"
          },
          "clickConversionRateQuarterly": {
            "type": "number",
            "description": "点击转换率（季度数据）"
          },
          "successfulLaunchedSemiannual": {
            "type": "integer",
            "description": "成功发布商品的数量（半年数据）"
          },
          "newProductsLaunchedSemiannual": {
            "type": "integer",
            "description": "已发布新产品的数量（半年数据）"
          },
          "searchConversionRateQuarterly": {
            "type": "number",
            "description": "搜索转换率（季度数据）"
          }
        }
      },
      "description": "细分市场信息列表"
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
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
