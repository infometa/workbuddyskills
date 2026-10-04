# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin",
    "domain"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊标准识别号(ASIN)，只支持单个ASIN"
    },
    "days": {
      "type": "integer",
      "default": 90,
      "maximum": 1096,
      "examples": [
        {
          "value": "30",
          "summary": "最近30天数据"
        },
        {
          "value": "90",
          "summary": "最近90天数据"
        }
      ],
      "description": "限制历史数据天数，默认90天"
    },
    "domain": {
      "type": "string",
      "pattern": "1|2|3|4|5|6|8|9|10|11|12",
      "examples": [
        {
          "value": "1",
          "summary": "Amazon.com (美国)"
        },
        {
          "value": "2",
          "summary": "Amazon.co.uk (英国)"
        },
        {
          "value": "3",
          "summary": "Amazon.de (德国)"
        },
        {
          "value": "4",
          "summary": "Amazon.fr (法国)"
        },
        {
          "value": "5",
          "summary": "Amazon.co.jp (日本)"
        },
        {
          "value": "6",
          "summary": "Amazon.ca (加拿大)"
        },
        {
          "value": "8",
          "summary": "Amazon.it (意大利)"
        },
        {
          "value": "9",
          "summary": "Amazon.es (西班牙)"
        },
        {
          "value": "10",
          "summary": "Amazon.in (印度)"
        },
        {
          "value": "11",
          "summary": "Amazon.com.mx (墨西哥)"
        },
        {
          "value": "12",
          "summary": "Amazon.com.br (巴西)"
        }
      ],
      "description": "亚马逊域名ID"
    },
    "showPrice": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回价格"
        }
      ],
      "description": "是否返回市场最低新品价曲线"
    },
    "showBsrMain": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回大类BSR"
        }
      ],
      "description": "是否返回大类BSR曲线"
    },
    "showPriceFba": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回FBA价格"
        }
      ],
      "description": "是否返回第三方FBA新品价曲线"
    },
    "showPriceFbm": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回FBM价格"
        }
      ],
      "description": "是否返回第三方FBM新品价曲线"
    },
    "showPriceDeal": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回Deal价格"
        }
      ],
      "description": "是否返回闪促价格曲线"
    },
    "showPriceList": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回划线价"
        }
      ],
      "description": "是否返回划线价/标价曲线"
    },
    "showPricePrime": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回Prime价格"
        }
      ],
      "description": "是否返回Prime专属新品价曲线"
    },
    "showPriceCoupon": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回coupon价格"
        }
      ],
      "description": "是否返回优惠券后买盒价曲线"
    },
    "showSellerCount": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "返回卖家数"
        }
      ],
      "description": "是否返回卖家数曲线"
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
    "price": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "价格,(time=时间,value=价格)"
    },
    "bsrSub": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "points": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "time=时间,value=排名"
          },
          "categoryName": {
            "type": "string",
            "description": "类目名称"
          }
        }
      },
      "description": "小类BSR"
    },
    "rating": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "评分(time=时间,value=评分)"
    },
    "bsrMain": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "points": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "time=时间,value=排名"
          },
          "categoryName": {
            "type": "string",
            "description": "类目名称"
          }
        }
      },
      "description": "大类BSR"
    },
    "priceFba": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "FBA价格,(time=时间,value=FBA价格)"
    },
    "priceFbm": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "FBM价格,(time=时间,value=FBM价格)"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "priceDeal": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "Deal价格,(time=时间,value=Deal价格)"
    },
    "priceList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "划线价,(time=时间,value=划线价格)"
    },
    "pricePrime": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "Prime价格,(time=时间,value=Prime价格)"
    },
    "buyboxPrice": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "Buybox价格,(time=时间,value=Buybox价格)"
    },
    "monthlySold": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "子体销量(time=时间,value=销量)"
    },
    "priceCoupon": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "coupon价格(time=时间,value=coupon价格)"
    },
    "ratingCount": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "评分数(time=时间,value=评分数)"
    },
    "sellerCount": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "卖家数(time=时间,value=卖家数)"
    }
  }
}
```

</details>
