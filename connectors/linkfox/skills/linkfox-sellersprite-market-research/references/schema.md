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
      "description": "页码，从1开始"
    },
    "size": {
      "type": "integer",
      "default": 50,
      "maximum": 200,
      "minimum": 1,
      "description": "每页条数，默认50，最大200"
    },
    "month": {
      "type": "string",
      "pattern": "^(nearly|(19|20)\\d{2}(0[1-9]|1[0-2]))$",
      "examples": [
        {
          "value": "nearly",
          "summary": "最近30天"
        },
        {
          "value": "202507",
          "summary": "具体月份 yyyyMM"
        }
      ],
      "description": "筛选日期。支持两种写法：① nearly — 最近30天；② yyyyMM — 查询具体月份（如 202507），最多支持当前月往前共24个月内的月份"
    },
    "topNum": {
      "type": "integer",
      "default": 10,
      "description": "头部Listing数量"
    },
    "maxAvgBsr": {
      "type": "integer",
      "description": "最高平均BSR排名"
    },
    "maxBrands": {
      "type": "integer",
      "description": "最大品牌数量"
    },
    "maxVolume": {
      "type": "number",
      "description": "最高体积"
    },
    "maxWeight": {
      "type": "number",
      "description": "最高重量"
    },
    "minAvgBsr": {
      "type": "integer",
      "description": "最低平均BSR排名"
    },
    "minBrands": {
      "type": "integer",
      "description": "最小品牌数量"
    },
    "minVolume": {
      "type": "number",
      "description": "最低体积"
    },
    "minWeight": {
      "type": "number",
      "description": "最低重量"
    },
    "orderDesc": {
      "type": "boolean",
      "default": true,
      "description": "排序是否降序，true降序 false升序，默认true"
    },
    "maxSellers": {
      "type": "integer",
      "description": "最大卖家数量"
    },
    "minSellers": {
      "type": "integer",
      "description": "最小卖家数量"
    },
    "newProduct": {
      "type": "integer",
      "default": 3,
      "description": "新品定义(月)"
    },
    "nodeIdPath": {
      "type": "string",
      "maxLength": 1000,
      "description": "类目节点ID路径，如 172282:281407"
    },
    "orderField": {
      "type": "string",
      "examples": [
        {
          "value": "total_units",
          "summary": "月销量"
        },
        {
          "value": "total_amount",
          "summary": "月销售额"
        },
        {
          "value": "bsr_rank",
          "summary": "bsr排名"
        },
        {
          "value": "price",
          "summary": "价格"
        },
        {
          "value": "rating",
          "summary": "评分"
        },
        {
          "value": "reviews",
          "summary": "评分数"
        },
        {
          "value": "profit",
          "summary": "毛利率"
        },
        {
          "value": "reviews_rate",
          "summary": "留评率"
        },
        {
          "value": "available_date",
          "summary": "上架时间"
        },
        {
          "value": "questions",
          "summary": "Q&A"
        },
        {
          "value": "total_units_growth",
          "summary": "月销量增长率"
        },
        {
          "value": "total_amount_growth",
          "summary": "月销售额增长率"
        },
        {
          "value": "reviews_increasement",
          "summary": "月新增评分数"
        },
        {
          "value": "bsr_rank_cv",
          "summary": "近7天BSR增长数"
        },
        {
          "value": "bsr_rank_cr",
          "summary": "近7天BSR增长率"
        },
        {
          "value": "amz_unit",
          "summary": "子体销量"
        }
      ],
      "maxLength": 1000,
      "description": "排序字段(order.field)，对应表1.6。可选：total_units-月销量；total_amount-月销售额；bsr_rank-bsr排名；price-价格；rating-评分；reviews-评分数；profit-毛利率；reviews_rate-留评率；available_date-上架时间；questions-Q&A；total_units_growth-月销量增长率；total_amount_growth-月销售额增长率；reviews_increasement-月新增评分数；bsr_rank_cv-近7天BSR增长数；bsr_rank_cr-近7天BSR增长率；amz_unit-子体销量"
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
      "description": "站点编码(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹)"
    },
    "maxAvgPrice": {
      "type": "number",
      "description": "最高平均价格"
    },
    "maxAvgUnits": {
      "type": "integer",
      "description": "最高月均销量"
    },
    "maxBrandCrn": {
      "type": "number",
      "description": "最大品牌集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxGoodsCrn": {
      "type": "number",
      "description": "最大商品集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxNewCount": {
      "type": "integer",
      "description": "最大新品数量"
    },
    "minAvgPrice": {
      "type": "number",
      "description": "最低平均价格"
    },
    "minAvgUnits": {
      "type": "integer",
      "description": "最低月均销量"
    },
    "minBrandCrn": {
      "type": "number",
      "description": "最小品牌集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "minGoodsCrn": {
      "type": "number",
      "description": "最小商品集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "minNewCount": {
      "type": "integer",
      "description": "最小新品数量"
    },
    "maxAvgProfit": {
      "type": "number",
      "description": "最高平均毛利率（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxAvgRating": {
      "type": "number",
      "description": "最高平均评分值"
    },
    "maxSellerCrn": {
      "type": "number",
      "description": "最大卖家集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxTopAvgBsr": {
      "type": "integer",
      "description": "最高头部平均BSR"
    },
    "minAvgProfit": {
      "type": "number",
      "description": "最低平均毛利率（输入 N 表示 N%，取值范围 0–100）"
    },
    "minAvgRating": {
      "type": "number",
      "description": "最低平均评分值"
    },
    "minSellerCrn": {
      "type": "number",
      "description": "最小卖家集中度（输入 N 表示 N%，取值范围 0–100）"
    },
    "minTopAvgBsr": {
      "type": "integer",
      "description": "最低头部平均BSR"
    },
    "maxAvgRatings": {
      "type": "integer",
      "description": "最高平均评分数"
    },
    "maxAvgRevenue": {
      "type": "number",
      "description": "最高月均销售额"
    },
    "maxAvgSellers": {
      "type": "number",
      "description": "最大平均卖家数量"
    },
    "maxGoodsCount": {
      "type": "integer",
      "description": "最高商品数量"
    },
    "minAvgRatings": {
      "type": "integer",
      "description": "最低平均评分数"
    },
    "minAvgRevenue": {
      "type": "number",
      "description": "最低月均销售额"
    },
    "minAvgSellers": {
      "type": "number",
      "description": "最小平均卖家数量"
    },
    "minGoodsCount": {
      "type": "integer",
      "description": "最低商品数量"
    },
    "maxNewAvgPrice": {
      "type": "number",
      "description": "最大新品平均价格"
    },
    "maxNewAvgUnits": {
      "type": "number",
      "description": "最高新品月均销量"
    },
    "maxTopAvgUnits": {
      "type": "integer",
      "description": "最高头部月均销量"
    },
    "minNewAvgPrice": {
      "type": "number",
      "description": "最小新品平均价格"
    },
    "minNewAvgUnits": {
      "type": "number",
      "description": "最低新品月均销量"
    },
    "minTopAvgUnits": {
      "type": "integer",
      "description": "最低头部月均销量"
    },
    "sellerLocation": {
      "type": "string",
      "examples": [
        {
          "value": "US,GB",
          "summary": "示例"
        }
      ],
      "maxLength": 1000,
      "description": "卖家所属地，多个用英文逗号分隔，见卖家精灵表1.3"
    },
    "maxNewAvgRating": {
      "type": "number",
      "description": "最大新品平均星级"
    },
    "minNewAvgRating": {
      "type": "number",
      "description": "最小新品平均星级"
    },
    "maxEbcProportion": {
      "type": "number",
      "description": "最大A+数量占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxFbaProportion": {
      "type": "number",
      "description": "最大FBA占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxFbmProportion": {
      "type": "number",
      "description": "最大FBM占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxNewAvgRatings": {
      "type": "integer",
      "description": "最大新品平均评分数"
    },
    "maxNewAvgRevenue": {
      "type": "number",
      "description": "最高新品月均销售额"
    },
    "maxNewProportion": {
      "type": "number",
      "description": "最大新品数量占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "maxTopAvgRevenue": {
      "type": "number",
      "description": "最高头部月均销售额"
    },
    "minEbcProportion": {
      "type": "number",
      "description": "最小A+数量占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "minFbaProportion": {
      "type": "number",
      "description": "最小FBA占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "minFbmProportion": {
      "type": "number",
      "description": "最小FBM占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "minNewAvgRatings": {
      "type": "integer",
      "description": "最小新品平均评分数"
    },
    "minNewAvgRevenue": {
      "type": "number",
      "description": "最低新品月均销售额"
    },
    "minNewProportion": {
      "type": "number",
      "description": "最小新品数量占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "minTopAvgRevenue": {
      "type": "number",
      "description": "最低头部月均销售额"
    },
    "departmentKeyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "类目关键字路径，如 Electronics:Accessories & Supplies"
    },
    "maxAmazonSelfProportion": {
      "type": "number",
      "description": "最大Amazon自营占比（输入 N 表示 N%，取值范围 0–100）"
    },
    "minAmazonSelfProportion": {
      "type": "number",
      "description": "最小Amazon自营占比（输入 N 表示 N%，取值范围 0–100）"
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
          "avgBsr": {
            "type": "integer",
            "description": "平均BSR"
          },
          "brands": {
            "type": "integer",
            "description": "品牌数量"
          },
          "nodeId": {
            "type": "string",
            "description": "节点ID"
          },
          "ranking": {
            "type": "integer",
            "description": "排名"
          },
          "sellers": {
            "type": "integer",
            "description": "卖家数量"
          },
          "avgPrice": {
            "type": "number",
            "description": "平均价格"
          },
          "avgUnits": {
            "type": "integer",
            "description": "月均销量"
          },
          "currency": {
            "type": "string",
            "description": "该市场的货币类型"
          },
          "avgProfit": {
            "type": "number",
            "description": "平均利润率(%)"
          },
          "avgRating": {
            "type": "number",
            "description": "平均评分值"
          },
          "avgVolume": {
            "type": "number",
            "description": "平均体积(in³)"
          },
          "avgWeight": {
            "type": "number",
            "description": "平均重量(pound)"
          },
          "avgRatings": {
            "type": "integer",
            "description": "平均评分数"
          },
          "avgRevenue": {
            "type": "number",
            "description": "月均销售额"
          },
          "avgSellers": {
            "type": "number",
            "description": "平均卖家数"
          },
          "nodeIdPath": {
            "type": "string",
            "description": "节点ID路径"
          },
          "totalUnits": {
            "type": "integer",
            "description": "月总销量"
          },
          "marketplace": {
            "type": "string",
            "description": "市场标志"
          },
          "returnRatio": {
            "type": "number",
            "description": "退货率(%)"
          },
          "top10Images": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "asin": {
                  "type": "string",
                  "description": "ASIN"
                },
                "image": {
                  "type": "string",
                  "description": "图片链接"
                }
              }
            },
            "description": "前10商品图片"
          },
          "topProducts": {
            "type": "integer",
            "description": "样本数量"
          },
          "sellerNation": {
            "type": "string",
            "description": "最多卖家归属地 code"
          },
          "totalRevenue": {
            "type": "number",
            "description": "月总销售额"
          },
          "baseAvgVolume": {
            "type": "number",
            "description": "平均体积(cm³)"
          },
          "baseAvgWeight": {
            "type": "number",
            "description": "平均重量(g)"
          },
          "ebcProportion": {
            "type": "number",
            "description": "A+商品占比(%)"
          },
          "fbaProportion": {
            "type": "number",
            "description": "FBA占比(%)"
          },
          "fbmProportion": {
            "type": "number",
            "description": "FBM占比(%)"
          },
          "nodeLabelName": {
            "type": "string",
            "description": "节点名称"
          },
          "nodeLabelPath": {
            "type": "string",
            "description": "节点名称路径"
          },
          "totalProducts": {
            "type": "integer",
            "description": "商品总数"
          },
          "avgReturnRatio": {
            "type": "number",
            "description": "退货率类目平均值(%)"
          },
          "nodeLabelLocale": {
            "type": "string",
            "description": "节点名称翻译"
          },
          "sellerProportion": {
            "type": "number",
            "description": "最多卖家归属地占比(%)"
          },
          "sellerNationLabel": {
            "type": "string",
            "description": "最多卖家归属地 label"
          },
          "nodeLabelPathLocale": {
            "type": "string",
            "description": "节点名称路径翻译"
          },
          "amazonSelfProportion": {
            "type": "number",
            "description": "Amazon自营占比(%)"
          },
          "searchToPurchaseRatio": {
            "type": "number",
            "description": "搜索购买比(千分比)"
          }
        }
      },
      "description": "类目市场列表(对应第三方 data.items)"
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
      "description": "站点编码"
    }
  }
}
```

</details>
