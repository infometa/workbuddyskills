# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "station"
  ],
  "properties": {
    "page": {
      "type": "integer",
      "default": 1,
      "description": "当前页码"
    },
    "pids": {
      "type": "string",
      "maxLength": 10000,
      "description": "商品id列表(单次最多500个),多个商品id使用逗号隔开，如：aaa,bbb"
    },
    "pL1Id": {
      "type": "string",
      "maxLength": 1000,
      "description": "1级类目ID"
    },
    "pL2Id": {
      "type": "string",
      "maxLength": 1000,
      "description": "2级类目ID"
    },
    "pL3Id": {
      "type": "string",
      "maxLength": 1000,
      "description": "3级类目ID"
    },
    "cidList": {
      "type": "string",
      "maxLength": 1000,
      "description": "类目id列表，每组id必须指定完整路径，可指定多组id，多个组id使用｜隔开，如：AAA,BBB,CCC｜DDD,EEE"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "标题"
    },
    "orderBy": {
      "type": "string",
      "examples": [
        {
          "value": "rating",
          "summary": "评分"
        },
        {
          "value": "price",
          "summary": "价格"
        },
        {
          "value": "historical_sold",
          "summary": "商品总销售件数"
        },
        {
          "value": "sold",
          "summary": "前30天销售件数"
        },
        {
          "value": "payment",
          "summary": "前30天销售金额"
        },
        {
          "value": "favorite",
          "summary": "Favorite数"
        },
        {
          "value": "ratings",
          "summary": "Ratings数"
        },
        {
          "value": "gen_time",
          "summary": "商品上架时间"
        },
        {
          "value": "estimate_sold",
          "summary": "估算前30天销售件数"
        }
      ],
      "maxLength": 1000,
      "description": "排序方式: rating(评分), price(价格), historical_sold(商品总销售件数), sold(前30天销售件数), payment(前30天销售金额), favorite(Favorite数), ratings(Ratings数), gen_time(商品上架时间), estimate_sold(估算前30天销售件数)"
    },
    "soldMax": {
      "type": "integer",
      "description": "前30天销售件数结束值"
    },
    "soldMin": {
      "type": "integer",
      "description": "前30天销售件数起始值"
    },
    "station": {
      "type": "string",
      "examples": [
        {
          "value": "malaysia",
          "summary": "马来西亚"
        },
        {
          "value": "MY",
          "summary": "马来西亚(代码)"
        },
        {
          "value": "taiwan_china",
          "summary": "台湾"
        },
        {
          "value": "Taiwan_CHN",
          "summary": "台湾(代码)"
        },
        {
          "value": "indonesia",
          "summary": "印度尼西亚"
        },
        {
          "value": "ID",
          "summary": "印度尼西亚(代码)"
        },
        {
          "value": "thailand",
          "summary": "泰国"
        },
        {
          "value": "TH",
          "summary": "泰国(代码)"
        },
        {
          "value": "philippines",
          "summary": "菲律宾"
        },
        {
          "value": "PH",
          "summary": "菲律宾(代码)"
        },
        {
          "value": "singapore",
          "summary": "新加坡"
        },
        {
          "value": "SG",
          "summary": "新加坡(代码)"
        },
        {
          "value": "vietnam",
          "summary": "越南"
        },
        {
          "value": "VN",
          "summary": "越南(代码)"
        },
        {
          "value": "brazil",
          "summary": "巴西"
        },
        {
          "value": "BR",
          "summary": "巴西(代码)"
        },
        {
          "value": "mexico",
          "summary": "墨西哥"
        },
        {
          "value": "MX",
          "summary": "墨西哥(代码)"
        },
        {
          "value": "chile",
          "summary": "智利"
        },
        {
          "value": "CL",
          "summary": "智利(代码)"
        },
        {
          "value": "columbia",
          "summary": "哥伦比亚"
        },
        {
          "value": "CO",
          "summary": "哥伦比亚(代码)"
        }
      ],
      "maxLength": 1000,
      "description": "Shopee站点国家代码"
    },
    "cbOption": {
      "type": "integer",
      "description": "发货地点: 1-跨境, 0-本土, 不传的情况下为指定全部"
    },
    "merchant": {
      "type": "string",
      "maxLength": 1000,
      "description": "店铺名称或用户名称"
    },
    "pageSize": {
      "type": "integer",
      "default": 1000,
      "description": "每一页的商品数(范围1-1000)"
    },
    "priceMax": {
      "type": "number",
      "description": "商品总价结束值"
    },
    "priceMin": {
      "type": "number",
      "description": "商品总价起始值"
    },
    "ratingMax": {
      "type": "number",
      "description": "商品评分最大值"
    },
    "ratingMin": {
      "type": "number",
      "description": "商品评分最小值"
    },
    "isHotSales": {
      "type": "integer",
      "description": "商品是否热销: 0-非热销, 1-热销"
    },
    "paymentEnd": {
      "type": "number",
      "description": "前30天销售金额结束值"
    },
    "ratingsMax": {
      "type": "integer",
      "description": "ratings数结束值"
    },
    "ratingsMin": {
      "type": "integer",
      "description": "ratings数起始值"
    },
    "shopIdList": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品店铺id列表, 可指定多个id，多个id使用逗号隔开"
    },
    "favoriteMax": {
      "type": "integer",
      "description": "favorite数结束值"
    },
    "favoriteMin": {
      "type": "integer",
      "description": "favorite数起始值"
    },
    "keywordType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "整句语句(默认)"
        },
        {
          "value": "2",
          "summary": "多个搜索词\"与\"关系"
        },
        {
          "value": "3",
          "summary": "多个搜索词\"或\"关系"
        }
      ],
      "description": "商品标题查询类型: 1-整句语句(默认), 2-多个搜索词\"与\"关系, 3-多个搜索词\"或\"关系"
    },
    "orderByType": {
      "type": "string",
      "default": "DESC",
      "examples": [
        {
          "value": "ASC",
          "summary": "升序"
        },
        {
          "value": "DESC",
          "summary": "降序"
        }
      ],
      "maxLength": 1000,
      "description": "排序类型: ASC-升序, DESC-降序"
    },
    "statTimeEnd": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$",
      "description": "统计时间结束值(格式:YYYY-MM-DD HH:mm:ss,如 2024-01-01 12:12:12)"
    },
    "paymentStart": {
      "type": "number",
      "description": "前30天销售金额起始值"
    },
    "shopLocation": {
      "type": "string",
      "maxLength": 1000,
      "description": "店铺所在地"
    },
    "skuNumberEnd": {
      "type": "integer",
      "description": "Sku总数结束值"
    },
    "listingDateTo": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品上架时间结束值(格式:年-月-日)"
    },
    "statTimeStart": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$",
      "description": "统计时间起始值(格式:YYYY-MM-DD HH:mm:ss,如 2024-01-01 12:12:12)"
    },
    "isOfficialShop": {
      "type": "integer",
      "description": "商品所属店铺是否官方店铺: 0-否, 1-是"
    },
    "skuNumberStart": {
      "type": "integer",
      "description": "Sku总数起始值"
    },
    "approvedDateEnd": {
      "type": "string",
      "maxLength": 1000,
      "description": "店铺开张时间结束值(格式:年-月-日)"
    },
    "estimateSoldEnd": {
      "type": "integer",
      "description": "估算前30天销售件数结束值"
    },
    "lastModiTimeEnd": {
      "type": "string",
      "maxLength": 1000,
      "description": "最新抓取时间结束值(格式:年-月-日)"
    },
    "listingDateFrom": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品上架时间起始值(格式:年-月-日)"
    },
    "notExistKeyword": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品不包含标题"
    },
    "isShopeeVerified": {
      "type": "integer",
      "examples": [
        {
          "value": "0",
          "summary": "非优选"
        },
        {
          "value": "1",
          "summary": "优选"
        }
      ],
      "description": "虾皮优选: 0-非优选, 1-优选, 不传的情况下为指定全部"
    },
    "shippingIconType": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "海外"
        },
        {
          "value": "0",
          "summary": "本地"
        }
      ],
      "description": "店铺所在地: 1-海外, 0-本地, 不传的情况下为指定全部"
    },
    "approvedDateStart": {
      "type": "string",
      "maxLength": 1000,
      "description": "店铺开张时间起始值(格式:年-月-日)"
    },
    "estimateSoldStart": {
      "type": "integer",
      "description": "估算前30天销售件数起始值"
    },
    "historicalSoldEnd": {
      "type": "integer",
      "description": "商品总销售件数结束值"
    },
    "lastModiTimeStart": {
      "type": "string",
      "maxLength": 1000,
      "description": "最新抓取时间起始值(格式:年-月-日)"
    },
    "notExistShopIdList": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品不包含的店铺id列表, 可指定多个id，多个id使用逗号隔开"
    },
    "historicalSoldStart": {
      "type": "integer",
      "description": "商品总销售件数起始值"
    },
    "notExistKeywordType": {
      "type": "integer",
      "default": 1,
      "description": "商品不包含标题查询类型: 1-整句语句(默认), 2-多个搜索词\"与\"关系, 3-多个搜索词\"或\"关系"
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
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "cid": {
            "type": "string",
            "description": "商品归属的类目ID(由一级至子类，多个以逗号分隔)"
          },
          "pid": {
            "type": "string",
            "description": "商品唯一ID"
          },
          "sold": {
            "type": "integer",
            "description": "商品前30天销售件数"
          },
          "price": {
            "type": "number",
            "description": "商品默认价"
          },
          "stock": {
            "type": "integer",
            "description": "库存数"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "rating": {
            "type": "number",
            "description": "商品评分"
          },
          "shopId": {
            "type": "string",
            "description": "商品所属店铺id"
          },
          "status": {
            "type": "integer",
            "description": "商品状态: 1-正常, 0-下架, 8-列表中排除"
          },
          "genTime": {
            "type": "string",
            "description": "商品上架时间"
          },
          "payment": {
            "type": "number",
            "description": "商品前30天销售额"
          },
          "ratings": {
            "type": "integer",
            "description": "商品评分数"
          },
          "shopUrl": {
            "type": "string",
            "description": "shopee店铺链接"
          },
          "cbOption": {
            "type": "integer",
            "description": "发货地点: 1-跨境, 0-本土"
          },
          "currency": {
            "type": "string",
            "description": "货币单位"
          },
          "favorite": {
            "type": "integer",
            "description": "商品喜欢人数"
          },
          "imageUrl": {
            "type": "string",
            "description": "商品主图"
          },
          "maxPrice": {
            "type": "number",
            "description": "商品最高价"
          },
          "minPrice": {
            "type": "number",
            "description": "商品最低价"
          },
          "notExist": {
            "type": "integer",
            "description": "商品是否存在: 0-存在, 1-不存在"
          },
          "shopName": {
            "type": "string",
            "description": "店铺名称"
          },
          "statTime": {
            "type": "string",
            "description": "商品统计时间"
          },
          "userName": {
            "type": "string",
            "description": "店主名称"
          },
          "skuNumber": {
            "type": "integer",
            "description": "sku数量"
          },
          "viewCount": {
            "type": "integer",
            "description": "商品浏览数"
          },
          "isHotSales": {
            "type": "integer",
            "description": "商品是否热销(预留字段)"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型：shopee"
          },
          "description": {
            "type": "string",
            "description": "商品描述"
          },
          "approvedDate": {
            "type": "string",
            "description": "店铺开张时间"
          },
          "estimateSold": {
            "type": "integer",
            "description": "估算前30天销售件数"
          },
          "lastModiTime": {
            "type": "string",
            "description": "商品最新抓取时间"
          },
          "shopLocation": {
            "type": "string",
            "description": "店铺所在地"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "商品总销售件数"
          },
          "estimatedDays": {
            "type": "integer",
            "description": "商品预计到货时间"
          },
          "isOfficialShop": {
            "type": "integer",
            "description": "商品所属店铺是否官方店铺"
          },
          "productPageUrl": {
            "type": "string",
            "description": "shopee商品链接"
          },
          "isShopeeVerified": {
            "type": "integer",
            "description": "商品是否虾皮优选"
          },
          "shippingIconType": {
            "type": "integer",
            "description": "店铺所在地: 0-本地, 1-海外, 3或null-未知"
          },
          "categoryStructure": {
            "type": "string",
            "description": "商品所属的类目结构"
          },
          "shopProductsCount": {
            "type": "integer",
            "description": "店铺商品总数"
          }
        }
      },
      "description": "商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "totalSize": {
      "type": "integer",
      "description": "总结果数"
    },
    "sourceTool": {
      "type": "string",
      "description": "来源工具"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型：shopee"
    }
  }
}
```

</details>
