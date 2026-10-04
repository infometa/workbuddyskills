# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "page": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "第一页"
        }
      ],
      "description": "页码，默认1"
    },
    "region": {
      "type": "string",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "GB",
          "summary": "英国"
        },
        {
          "value": "ID",
          "summary": "印尼"
        },
        {
          "value": "VN",
          "summary": "越南"
        },
        {
          "value": "MY",
          "summary": "马来西亚"
        },
        {
          "value": "TH",
          "summary": "泰国"
        },
        {
          "value": "PH",
          "summary": "菲律宾"
        },
        {
          "value": "MX",
          "summary": "墨西哥"
        },
        {
          "value": "BR",
          "summary": "巴西"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "SG",
          "summary": "新加坡"
        }
      ],
      "maxLength": 1000,
      "description": "国家/地区代码,支持如下国家：['US','GB','MX','ES','DE','IT','FR','ID','VN','MY','TH','PH','BR','JP','SG']"
    },
    "isSshop": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "仅全托管商品"
        }
      ],
      "description": "是否全托管商品（TikTok S店=全托管商品）"
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "phone case",
          "summary": "手机壳"
        },
        {
          "value": "LED light",
          "summary": "LED灯"
        }
      ],
      "maxLength": 1000,
      "description": "搜索关键词（商品标题模糊匹配）"
    },
    "category": {
      "type": "string",
      "examples": [
        {
          "value": "Phone Cases",
          "summary": "手机壳（英文）"
        },
        {
          "value": "LED Light",
          "summary": "LED灯（英文）"
        }
      ],
      "maxLength": 1000,
      "description": "类目名称（文本，用于匹配 TikTok 英文类目并解析为类目 ID）。TikTok 类目为英文,若用户输入非英语，请先在对话侧译为英语再传入本参数。"
    },
    "pageSize": {
      "type": "integer",
      "maximum": 10,
      "examples": [
        {
          "value": "10",
          "summary": "每页10条"
        }
      ],
      "description": "每页条数，每页最多10条，默认10"
    },
    "shopType": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "本土"
        },
        {
          "value": "2",
          "summary": "跨境"
        }
      ],
      "description": "店铺类型：1-本土店铺，2-跨境店铺"
    },
    "orderField": {
      "type": "string",
      "pattern": "day7_units_sold|day7_gmv|commission_rate|total_units_sold|total_gmv|creator_count",
      "examples": [
        {
          "value": "day7_units_sold",
          "summary": "7日销量"
        },
        {
          "value": "day7_gmv",
          "summary": "7日销售额"
        },
        {
          "value": "commission_rate",
          "summary": "佣金率"
        },
        {
          "value": "total_units_sold",
          "summary": "总销量"
        },
        {
          "value": "total_gmv",
          "summary": "总销售额"
        },
        {
          "value": "creator_count",
          "summary": "关联达人数"
        }
      ],
      "description": "排序字段（默认降序排列）"
    },
    "isNewListed": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "仅新品"
        }
      ],
      "description": "是否新品"
    },
    "isTopSelling": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "仅热销商品"
        }
      ],
      "description": "是否热销商品"
    },
    "isFreeShipping": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "仅包邮商品"
        }
      ],
      "description": "是否包邮"
    },
    "unitsSoldRange": {
      "type": "object",
      "required": [],
      "properties": {
        "max": {
          "type": "integer",
          "description": "范围上限（最大值，含），不设置则不限上限"
        },
        "min": {
          "type": "integer",
          "description": "范围下限（最小值，含），不设置则不限下限"
        }
      }
    },
    "isLocalWarehouse": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "仅本地仓商品"
        }
      ],
      "description": "是否本地仓"
    },
    "creatorCountRange": {
      "type": "object",
      "required": [],
      "properties": {
        "max": {
          "type": "integer",
          "description": "范围上限（最大值，含），不设置则不限上限"
        },
        "min": {
          "type": "integer",
          "description": "范围下限（最小值，含），不设置则不限下限"
        }
      }
    },
    "commissionRateRange": {
      "type": "object",
      "required": [],
      "properties": {
        "max": {
          "type": "integer",
          "description": "范围上限（最大值，含），不设置则不限上限"
        },
        "min": {
          "type": "integer",
          "description": "范围下限（最小值，含），不设置则不限下限"
        }
      }
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
    "page": {
      "type": "integer",
      "description": "当前页码"
    },
    "type": {
      "type": "string",
      "description": "响应类型"
    },
    "total": {
      "type": "integer",
      "description": "结果总数"
    },
    "columns": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {}
      },
      "description": "列定义"
    },
    "costTime": {
      "type": "integer",
      "description": "接口耗时毫秒"
    },
    "pageSize": {
      "type": "integer",
      "description": "每页条数"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "price": {
            "type": "number",
            "description": "商品价格.数值类型，货币单位见currency字段"
          },
          "title": {
            "type": "string",
            "description": "商品名称"
          },
          "region": {
            "type": "string",
            "description": "区域代码.如US、GB、ID等"
          },
          "source": {
            "type": "string",
            "description": "商品来源标识"
          },
          "coverUrl": {
            "type": "array",
            "items": {},
            "description": "图片URL列表"
          },
          "currency": {
            "type": "string",
            "description": "货币符号"
          },
          "imageUrl": {
            "type": "string",
            "description": "商品图片URL"
          },
          "maxPrice": {
            "type": "number",
            "description": "最高价格.部分商品无此数据时为null，货币单位见currency字段"
          },
          "minPrice": {
            "type": "number",
            "description": "最低价格.部分商品无此数据时为null，货币单位见currency字段"
          },
          "shopName": {
            "type": "string",
            "description": "店铺名称"
          },
          "skuCount": {
            "type": "integer",
            "description": "SKU数量"
          },
          "productId": {
            "type": "string",
            "description": "TikTok产品ID.如1730759153212362829"
          },
          "tiktokUrl": {
            "type": "string",
            "description": "TikTok商品链接"
          },
          "shopAvatar": {
            "type": "string",
            "description": "店铺头像URL"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "商品来源"
          },
          "categoryIds": {
            "type": "array",
            "items": {},
            "description": "商品品类ID列表.一级到三级，如[\"16\",\"909064\",\"910728\"]"
          },
          "fastmossUrl": {
            "type": "string",
            "description": "FastMoss商品链接"
          },
          "isSShopText": {
            "type": "string",
            "description": "是否全托管商品.是/否，S店=TikTok全托管"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论总数.部分商品无此数据时为null"
          },
          "totalIflCnt": {
            "type": "integer",
            "description": "关联达人数.Influencer Count"
          },
          "categoryName": {
            "type": "string",
            "description": "商品品类名称路径.如Phones & Electronics -> Phone Accessories -> Power Banks"
          },
          "shopSellerId": {
            "type": "string",
            "description": "店铺ID"
          },
          "totalLiveCnt": {
            "type": "integer",
            "description": "关联直播数.部分商品无此数据时为null"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "总销量.累计历史总销量"
          },
          "availableDate": {
            "type": "string",
            "description": "上架时间.格式yyyy-MM-dd HH:mm:ss，如2025-10-26 18:09:29"
          },
          "isCrossBorder": {
            "type": "integer",
            "description": "是否跨境.1=跨境，0=本土"
          },
          "productRating": {
            "type": "number",
            "description": "商品评分.范围0.0-5.0，如4.4"
          },
          "totalVideoCnt": {
            "type": "integer",
            "description": "关联视频数"
          },
          "totalSale1dCnt": {
            "type": "integer",
            "description": "1天内总销量"
          },
          "totalSale7dCnt": {
            "type": "integer",
            "description": "7天内总销量"
          },
          "totalSale28dCnt": {
            "type": "integer",
            "description": "28天内总销量)"
          },
          "totalSale90dCnt": {
            "type": "integer",
            "description": "90天内总销量"
          },
          "totalSaleGmvAmt": {
            "type": "integer",
            "description": "总销售额.累计历史总销售额，货币单位见currency字段"
          },
          "freeShippingText": {
            "type": "string",
            "description": "是否包邮.是/否"
          },
          "totalSaleGmv7dAmt": {
            "type": "integer",
            "description": "7天内总销售额.货币单位见currency字段"
          },
          "salesTrendFlagText": {
            "type": "string",
            "description": "销售趋势标记"
          },
          "shopTotalUnitsSold": {
            "type": "integer",
            "description": "店铺总销量"
          },
          "totalSaleGmv28dAmt": {
            "type": "integer",
            "description": "28天内总销售额.货币单位见currency字段"
          },
          "productCommissionRate": {
            "type": "number",
            "description": "商品佣金比例.小数值，0.10表示10%，0.17表示17%"
          }
        }
      },
      "description": "商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗Token数量"
    },
    "matchedCategoryIdPath": {
      "type": "string",
      "description": "匹配类目ID路径"
    },
    "matchedCategoryNamePath": {
      "type": "string",
      "description": "匹配类目名称路径"
    }
  }
}
```

</details>
