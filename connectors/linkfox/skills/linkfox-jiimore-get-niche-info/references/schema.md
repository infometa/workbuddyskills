# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "nicheId"
  ],
  "properties": {
    "nicheId": {
      "type": "string",
      "maxLength": 1000,
      "description": "细分市场ID"
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
      "description": "国家编码，仅支持US，JP，DE"
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
            "properties": {}
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
          "avgOOSRateNow": {
            "type": "number",
            "description": "平均缺货率(当前)"
          },
          "brandCountNow": {
            "type": "integer",
            "description": "品牌数量(当前)"
          },
          "categorieList": {
            "type": "array",
            "items": {},
            "description": "商品品类列表"
          },
          "marketplaceId": {
            "type": "string",
            "description": "市场ID"
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
          "productCountNow": {
            "type": "integer",
            "description": "商品数量(当前)"
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
          "avgOOSRateT360Now": {
            "type": "number",
            "description": "平均缺货率(360天统计)(当前)"
          },
          "avgReviewCountNow": {
            "type": "number",
            "description": "平均评论数(当前)"
          },
          "brandCountT360Now": {
            "type": "integer",
            "description": "品牌数量(360天统计)(当前)"
          },
          "avgBrandAgeT360Now": {
            "type": "number",
            "description": "平均品牌年龄(360 天统计)(当前)"
          },
          "avgProductPriceNow": {
            "type": "number",
            "description": "产品均价(当前)"
          },
          "avgReviewRatingNow": {
            "type": "number",
            "description": "平均评论评分(当前)"
          },
          "searchVolumeWeekly": {
            "type": "integer",
            "description": "搜索量（周数据）"
          },
          "unitsSoldQuarterly": {
            "type": "integer",
            "description": "销售数量（季度数据）"
          },
          "avgOOSRateT90Before": {
            "type": "number",
            "description": "平均缺货率(90天前)"
          },
          "brandCountT90Before": {
            "type": "integer",
            "description": "品牌数量(90天前)"
          },
          "clickCountQuarterly": {
            "type": "integer",
            "description": "点击量（季度数据）"
          },
          "avgBestSellerRankNow": {
            "type": "number",
            "description": "平均BestSeller排名(当前)"
          },
          "avgBrandAgeQuarterly": {
            "type": "number",
            "description": "平均品牌年龄(季度数据)"
          },
          "avgBrandAgeT90Before": {
            "type": "number",
            "description": "平均品牌年龄(90天前)"
          },
          "avgOOSRateT360Before": {
            "type": "number",
            "description": "平均缺货率(360天前)"
          },
          "brandCountT360Before": {
            "type": "integer",
            "description": "品牌数量(360天前)"
          },
          "launchRateSemiannual": {
            "type": "number",
            "description": "发布商品的成功率（半年数据）"
          },
          "top5BrandsClickShare": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额"
          },
          "avgBrandAgeT360Before": {
            "type": "number",
            "description": "平均品牌年龄(360天前)"
          },
          "productCountT90Before": {
            "type": "integer",
            "description": "商品数量(90天前)"
          },
          "referenceAsinImageUrl": {
            "type": "string",
            "description": "细分市场参考图片地址"
          },
          "searchVolumeQuarterly": {
            "type": "integer",
            "description": "搜索量（季度数据）"
          },
          "productCountT360Before": {
            "type": "integer",
            "description": "商品数量(360天前)"
          },
          "sellingPartnerCountNow": {
            "type": "integer",
            "description": "销售伙伴数量(当前)"
          },
          "top5ProductsClickShare": {
            "type": "number",
            "description": "排名前 5 位的商品点击份额"
          },
          "avgOOSRateT360T90Before": {
            "type": "number",
            "description": "平均缺货率(360天统计)(90天前)"
          },
          "avgReviewCountT90Before": {
            "type": "number",
            "description": "平均评论数(90天前)"
          },
          "avgSellingPartnerAgeNow": {
            "type": "number",
            "description": "平均销售伙伴年龄(当前)"
          },
          "brandCountT360T90Before": {
            "type": "integer",
            "description": "品牌数量(360天统计)(90天前)"
          },
          "productStarRatingImpact": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "产品星级影响力信息"
          },
          "top5BrandsClickShareNow": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(当前)"
          },
          "avgBrandAgeT360T90Before": {
            "type": "number",
            "description": "平均品牌年龄(360 天统计)(90天前)"
          },
          "avgOOSRateT360T360Before": {
            "type": "number",
            "description": "平均缺货率(360天统计)(360天前)"
          },
          "avgProductPriceT90Before": {
            "type": "number",
            "description": "产品均价(90天前)"
          },
          "avgReviewCountT360Before": {
            "type": "number",
            "description": "平均评论数(360天前)"
          },
          "avgReviewRatingT90Before": {
            "type": "number",
            "description": "平均评论评分(90天前)"
          },
          "brandCountT360T360Before": {
            "type": "integer",
            "description": "品牌数量(360天统计)(360天前)"
          },
          "searchVolumeGrowthWeekly": {
            "type": "number",
            "description": "搜索量增长率（周数据）"
          },
          "successfulLaunchesT90Now": {
            "type": "integer",
            "description": "成功上架数(90天统计)(当前）"
          },
          "top20BrandsClickShareNow": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(当前)"
          },
          "avgBrandAgeT360T360Before": {
            "type": "number",
            "description": "平均品牌年龄(360 天统计)(360天前)"
          },
          "avgProductPriceT360Before": {
            "type": "number",
            "description": "产品均价(360天前)"
          },
          "avgReviewRatingT360Before": {
            "type": "number",
            "description": "平均评论评分(360天前)"
          },
          "successfulLaunchesT180Now": {
            "type": "integer",
            "description": "成功发布商品的数量（180 天统计）(当前)"
          },
          "successfulLaunchesT360Now": {
            "type": "integer",
            "description": "成功发布商品的数量（360 天统计）(当前)"
          },
          "top5ProductsClickShareNow": {
            "type": "number",
            "description": "前5个商品所占细分市场的点击量份额(当前)"
          },
          "avgBestSellerRankT90Before": {
            "type": "number",
            "description": "平均BestSeller排名(90天前)"
          },
          "newProductsLaunchedT180Now": {
            "type": "integer",
            "description": "已发布新产品的数量(180天统计)(当前)"
          },
          "newProductsLaunchedT360Now": {
            "type": "integer",
            "description": "新上架商品数(360天统计)(当前)"
          },
          "primeProductsPercentageNow": {
            "type": "number",
            "description": "prime商品的百分比(当前)"
          },
          "searchConversionRateWeekly": {
            "type": "number",
            "description": "搜索转换率（周数据）"
          },
          "sellingPartnerCountT360Now": {
            "type": "integer",
            "description": "销售伙伴数量(360 天统计)(当前)"
          },
          "top20ProductsClickShareNow": {
            "type": "number",
            "description": "前20个商品所占细分市场的点击量份额（当前)"
          },
          "avgBestSellerRankT360Before": {
            "type": "number",
            "description": "平均BestSeller排名(360天前)"
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
          "top5BrandsClickShareT360Now": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(360 天统计)(当前)"
          },
          "clickConversionRateQuarterly": {
            "type": "number",
            "description": "点击转换率（季度数据）"
          },
          "sellingPartnerCountT90Before": {
            "type": "integer",
            "description": "销售伙伴数量(90天前)"
          },
          "successfulLaunchedSemiannual": {
            "type": "integer",
            "description": "成功发布商品的数量（半年数据）"
          },
          "top20BrandsClickShareT360Now": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(360天统计)（当前)"
          },
          "avgSellingPartnerAgeT90Before": {
            "type": "number",
            "description": "平均销售伙伴年龄(90天前)"
          },
          "newProductsLaunchedSemiannual": {
            "type": "integer",
            "description": "已发布新产品的数量（半年数据）"
          },
          "searchConversionRateQuarterly": {
            "type": "number",
            "description": "搜索转换率（季度数据）"
          },
          "sellingPartnerCountT360Before": {
            "type": "integer",
            "description": "销售伙伴数量(360天前)"
          },
          "top5BrandsClickShareT90Before": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(90天前)"
          },
          "top5ProductsClickShareT360Now": {
            "type": "number",
            "description": "排名前 5 位的商品点击份额（360天统计）(当前)"
          },
          "avgSellingPartnerAgeT360Before": {
            "type": "number",
            "description": "平均销售伙伴年龄(360天前)"
          },
          "negativeCustomerReviewInsights": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "负面客户评论见解信息"
          },
          "positiveCustomerReviewInsights": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "正面客户评论见解信息"
          },
          "primeProductsPercentageT360Now": {
            "type": "number",
            "description": "prime商品的百分比(360 天统计）(当前)"
          },
          "sponsoredProductsPercentageNow": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(当前)"
          },
          "successfulLaunchesT90T90Before": {
            "type": "integer",
            "description": "成功上架数(90天统计)(90天前)"
          },
          "top20BrandsClickShareT90Before": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(90天前)"
          },
          "top20ProductsClickShareT360Now": {
            "type": "number",
            "description": "排名前20位的商品点击份额(360 天统计)(当前)"
          },
          "top5BrandsClickShareT360Before": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(360天前)"
          },
          "successfulLaunchesT180T90Before": {
            "type": "integer",
            "description": "成功发布商品的数量（180 天统计）(90天前)"
          },
          "successfulLaunchesT360T90Before": {
            "type": "integer",
            "description": "成功发布商品的数量（360 天统计）(90天前)"
          },
          "successfulLaunchesT90T360Before": {
            "type": "integer",
            "description": "成功上架数(90天统计)(360天前)"
          },
          "top20BrandsClickShareT360Before": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(360天前)"
          },
          "top5ProductsClickShareT90Before": {
            "type": "number",
            "description": "前5个商品所占细分市场的点击量份额(90天前)"
          },
          "newProductsLaunchedT180T90Before": {
            "type": "integer",
            "description": "已发布新产品的数量(180天统计)(90天前)"
          },
          "newProductsLaunchedT360T90Before": {
            "type": "integer",
            "description": "新上架商品数(360天统计)(90天前)"
          },
          "primeProductsPercentageT90Before": {
            "type": "number",
            "description": "prime商品的百分比(90天前)"
          },
          "sellingPartnerCountT360T90Before": {
            "type": "integer",
            "description": "销售伙伴数量(360 天统计)(90天前)"
          },
          "successfulLaunchesT180T360Before": {
            "type": "integer",
            "description": "成功发布商品的数量（180 天统计）(360天前)"
          },
          "successfulLaunchesT360T360Before": {
            "type": "integer",
            "description": "成功发布商品的数量（360 天统计）(360天前)"
          },
          "top20ProductsClickShareT90Before": {
            "type": "number",
            "description": "前20个商品所占细分市场的点击量份额（90天前)"
          },
          "top5ProductsClickShareT360Before": {
            "type": "number",
            "description": "前5个商品所占细分市场的点击量份额(360天前)"
          },
          "newProductsLaunchedT180T360Before": {
            "type": "integer",
            "description": "已发布新产品的数量(180天统计)(360天前)"
          },
          "newProductsLaunchedT360T360Before": {
            "type": "integer",
            "description": "新上架商品数(360天统计)(360天前)"
          },
          "primeProductsPercentageT360Before": {
            "type": "number",
            "description": "prime商品的百分比(360天前)"
          },
          "sellingPartnerCountT360T360Before": {
            "type": "integer",
            "description": "销售伙伴数量(360 天统计)(360天前)"
          },
          "top20ProductsClickShareT360Before": {
            "type": "number",
            "description": "前20个商品所占细分市场的点击量份额（360天前)"
          },
          "top5BrandsClickShareT360T90Before": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(360 天统计)(90天前)"
          },
          "sponsoredProductsPercentageT360Now": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(360 天统计)(当前)"
          },
          "top20BrandsClickShareT360T90Before": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(360天统计)（90天前)"
          },
          "top5BrandsClickShareT360T360Before": {
            "type": "number",
            "description": "前5个品牌所占细分市场的点击量份额(360 天统计)(360天前)"
          },
          "top20BrandsClickShareT360T360Before": {
            "type": "number",
            "description": "前20个品牌所占细分市场的点击量份额(360天统计)（360天前)"
          },
          "top5ProductsClickShareT360T90Before": {
            "type": "number",
            "description": "排名前 5 位的商品点击份额（360天统计）(90天前)"
          },
          "primeProductsPercentageT360T90Before": {
            "type": "number",
            "description": "prime商品的百分比(360 天统计）(90天前)"
          },
          "sponsoredProductsPercentageT90Before": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(90天前)"
          },
          "top20ProductsClickShareT360T90Before": {
            "type": "number",
            "description": "排名前20位的商品点击份额(360 天统计)(90天前)"
          },
          "top5ProductsClickShareT360T360Before": {
            "type": "number",
            "description": "排名前 5 位的商品点击份额（360天统计）(360天前)"
          },
          "primeProductsPercentageT360T360Before": {
            "type": "number",
            "description": "prime商品的百分比(360 天统计）(360天前)"
          },
          "sponsoredProductsPercentageT360Before": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(360天前)"
          },
          "top20ProductsClickShareT360T360Before": {
            "type": "number",
            "description": "排名前20位的商品点击份额(360 天统计)(360天前)"
          },
          "sponsoredProductsPercentageT360T90Before": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(360 天统计)(90天前)"
          },
          "sponsoredProductsPercentageT360T360Before": {
            "type": "number",
            "description": "已进行商品推广的商品的百分比(360 天统计)(360天前)"
          }
        }
      },
      "description": "细分市场信息列表"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "记录数"
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
