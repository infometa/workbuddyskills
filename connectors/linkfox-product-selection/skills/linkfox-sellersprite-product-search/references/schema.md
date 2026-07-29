# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "uid": {
      "type": "string",
      "maxLength": 1000,
      "description": "用户id"
    },
    "page": {
      "type": "integer",
      "default": 1,
      "description": "页码，从1开始"
    },
    "size": {
      "type": "integer",
      "default": 20,
      "maximum": 100,
      "minimum": 10,
      "description": "每页条数,返回10-100条数据"
    },
    "order": {
      "type": "object",
      "required": [
        "field",
        "desc"
      ],
      "properties": {
        "desc": {
          "type": "string",
          "default": "true",
          "maxLength": 1000,
          "description": "true为降序 false为升序"
        },
        "field": {
          "type": "string",
          "default": "total_units",
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
              "summary": "Q & A"
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
            },
            {
              "value": "",
              "summary": "不传，查询全部数据"
            }
          ],
          "maxLength": 1000,
          "description": "排序字段"
        }
      }
    },
    "chatId": {
      "type": "string",
      "maxLength": 1000,
      "description": "对话id"
    },
    "maxBsr": {
      "type": "integer",
      "description": "大类BSR最高排名"
    },
    "maxFba": {
      "type": "number",
      "minimum": 0,
      "description": "最高FBA运费"
    },
    "minBsr": {
      "type": "integer",
      "description": "大类BSR最低排名"
    },
    "minFba": {
      "type": "number",
      "minimum": 0,
      "description": "最低FBA运费"
    },
    "teamId": {
      "type": "string",
      "maxLength": 1000,
      "description": "团队id"
    },
    "keyword": {
      "type": "string",
      "maxLength": 10240,
      "description": "关键字；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等"
    },
    "maxPrice": {
      "type": "number",
      "minimum": 0,
      "description": "最高价格"
    },
    "maxUnits": {
      "type": "integer",
      "minimum": 0,
      "description": "最高月销量"
    },
    "minPrice": {
      "type": "number",
      "minimum": 0,
      "description": "最低价格"
    },
    "minUnits": {
      "type": "integer",
      "minimum": 0,
      "description": "最低月销量"
    },
    "matchType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "词组匹配"
        },
        {
          "value": "2",
          "summary": "模糊匹配"
        },
        {
          "value": "3",
          "summary": "精准匹配"
        }
      ],
      "description": "匹配方式，1词组匹配 2模糊匹配 3精准匹配；默认 1"
    },
    "maxProfit": {
      "type": "number",
      "maximum": 100,
      "minimum": 1,
      "description": "最大毛利率,单位 %，利润率最小为1 ，最大为100"
    },
    "maxRating": {
      "type": "number",
      "maximum": 5,
      "minimum": 0,
      "description": "最高评分值。评分最大为5分，最小0分，3.8-4.3为产品改良机会的产品"
    },
    "minProfit": {
      "type": "number",
      "maximum": 100,
      "minimum": 1,
      "description": "最小毛利率，单位 %。利润率最小为1 ，最大为100"
    },
    "minRating": {
      "type": "number",
      "maximum": 5,
      "minimum": 0,
      "description": "最低评分值。评分最大为5分，最小0分"
    },
    "nodeLabel": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊类目名称"
    },
    "requestId": {
      "type": "string",
      "maxLength": 1000,
      "description": "推送id"
    },
    "maxAmzUnit": {
      "type": "integer",
      "minimum": 0,
      "description": "最高子体近30日销量(仅近30日查询支持)"
    },
    "maxRatings": {
      "type": "integer",
      "maximum": 10000,
      "minimum": 0,
      "description": "最高评分数"
    },
    "maxRevenue": {
      "type": "number",
      "minimum": 0,
      "description": "最高月销售额"
    },
    "maxSellers": {
      "type": "integer",
      "description": "最大卖家数量，卖家数量小于等于"
    },
    "maxWeights": {
      "type": "number",
      "minimum": 0,
      "description": "最大重量"
    },
    "minAmzUnit": {
      "type": "integer",
      "minimum": 0,
      "description": "最低子体近30日销量(仅近30日查询支持)"
    },
    "minRatings": {
      "type": "integer",
      "maximum": 10000,
      "minimum": 0,
      "description": "最低评分数"
    },
    "minRevenue": {
      "type": "number",
      "minimum": 0,
      "description": "最低月销售额"
    },
    "minSellers": {
      "type": "integer",
      "description": "最小卖家数量,卖家数量大于等于"
    },
    "minWeights": {
      "type": "number",
      "minimum": 0,
      "description": "最小重量"
    },
    "nodeIdPath": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊类目节点id"
    },
    "weightUnit": {
      "type": "string",
      "pattern": "g|kg|oz|lb",
      "examples": [
        {
          "value": "g",
          "summary": "克"
        },
        {
          "value": "kg",
          "summary": "千克"
        },
        {
          "value": "oz",
          "summary": "盎司"
        },
        {
          "value": "lb",
          "summary": "磅"
        }
      ],
      "description": "重量单位。支持的有：g/kg/oz/lb 这几种，如果用户的参数里面有重量，则必须要求用户也输入重量的单位。"
    },
    "fulfillment": {
      "type": "string",
      "examples": [
        {
          "value": "AMZ",
          "summary": "AMZ"
        },
        {
          "value": "FBA",
          "summary": "FBA"
        },
        {
          "value": "FBM",
          "summary": "FBM"
        },
        {
          "value": "AMZ,FBA",
          "summary": "AMZ,FBA"
        },
        {
          "value": "AMZ,FBM",
          "summary": "AMZ,FBM"
        },
        {
          "value": "FBA,FBM",
          "summary": "FBA,FBM"
        },
        {
          "value": "AMZ,FBA,FBM",
          "summary": "AMZ,FBA,FBM"
        },
        {
          "value": "",
          "summary": "默认不限制"
        }
      ],
      "maxLength": 1000,
      "description": "配送方式，多条件查询用逗号隔开AMZ or FBA or FBM"
    },
    "marketplace": {
      "type": "string",
      "default": "US",
      "pattern": "US|UK|DE|FR|JP|CA|IT|ES|MX|IN",
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
          "value": "FR",
          "summary": "亚马逊-法国站"
        },
        {
          "value": "JP",
          "summary": "亚马逊-日本站"
        },
        {
          "value": "CA",
          "summary": "亚马逊-加拿大站"
        },
        {
          "value": "IT",
          "summary": "亚马逊-意大利站"
        },
        {
          "value": "ES",
          "summary": "亚马逊-西班牙站"
        },
        {
          "value": "MX",
          "summary": "亚马逊-墨西哥站"
        },
        {
          "value": "IN",
          "summary": "亚马逊-印度站"
        }
      ],
      "description": "市场"
    },
    "sellerNation": {
      "type": "string",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "DE",
          "summary": "德国"
        },
        {
          "value": "FR",
          "summary": "法国"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "CN",
          "summary": "中国"
        },
        {
          "value": "HK",
          "summary": "中国香港特区"
        },
        {
          "value": "",
          "summary": "默认不限制"
        }
      ],
      "maxLength": 1000,
      "description": "卖家所属地，默认不限制，多条件查询用逗号隔开"
    },
    "dimensionType": {
      "type": "string",
      "maxLength": 1000,
      "description": "包装尺寸类型, 参数信息如下  美国站点: SS-小号标准尺寸, LS-大号标准尺寸, SO-小号大件, MO-中号大件, LO/LB-大号大件, SP-特殊大件, O-其他尺寸, ELO-超大尺寸：0至50磅, EL5O-超大尺寸：50到70磅（不含50磅）, EL7O-超大尺寸：70至150磅（不含70磅）, EL15O-超大尺寸：150磅以上（不含150磅）; 日本站点: SM-小号, ST-标准, OV-大件, SS-超大尺寸, O-其他尺寸; 加拿大站点: EN-信封装, ST-标准, SO-小号大件, MO-中号大件, LO-大号大件, SP-特殊大件, O-其他尺寸; 英国/法国/德国/意大利/西班牙站点: SL-小号信封, NL-标准信封, LL-大号信封, ELL-超大号信封, SM-小包裹, SD-标准包裹, SB-小号大件, NB-标准大件, LB-大号大件, SPO-特殊大件, O-其他尺寸"
    },
    "excludeBrands": {
      "type": "string",
      "maxLength": 10240,
      "description": "排除品牌"
    },
    "filterSubNode": {
      "type": "boolean",
      "examples": [
        {
          "value": "true",
          "summary": "是"
        },
        {
          "value": "false",
          "summary": "否"
        }
      ],
      "description": "是否筛选子类目节点，true为筛选，false为不筛选，只有在nodeLabel 或 nodeIdPath 有值时才会生效"
    },
    "includeBrands": {
      "type": "string",
      "maxLength": 10240,
      "description": "包含品牌"
    },
    "maxVariations": {
      "type": "integer",
      "description": "最高变体数"
    },
    "minVariations": {
      "type": "integer",
      "description": "最低变体数"
    },
    "showVariation": {
      "type": "string",
      "default": "N",
      "examples": [
        {
          "value": "Y",
          "summary": "是"
        },
        {
          "value": "N",
          "summary": "否"
        }
      ],
      "maxLength": 1000,
      "description": "是否查询变体"
    },
    "excludeSellers": {
      "type": "string",
      "maxLength": 10240,
      "description": "排除卖家"
    },
    "includeSellers": {
      "type": "string",
      "maxLength": 10240,
      "description": "包含卖家"
    },
    "badgeBestSeller": {
      "type": "string",
      "examples": [
        {
          "value": "Y",
          "summary": "是"
        },
        {
          "value": "N",
          "summary": "否"
        },
        {
          "value": "",
          "summary": "不传，查询全部数据"
        }
      ],
      "maxLength": 1000,
      "description": "是否有热销标识 Best Seller(Y/N)"
    },
    "badgeNewRelease": {
      "type": "string",
      "examples": [
        {
          "value": "Y",
          "summary": "是"
        },
        {
          "value": "N",
          "summary": "否"
        },
        {
          "value": "",
          "summary": "不传，查询全部数据"
        }
      ],
      "maxLength": 1000,
      "description": "是否有新品标识 New Release(Y/N)"
    },
    "excludeKeywords": {
      "type": "string",
      "maxLength": 10240,
      "description": "排除关键词"
    },
    "maxBsrGrowthRate": {
      "type": "number",
      "description": "BSR最高增长率，单位 %"
    },
    "minBsrGrowthRate": {
      "type": "number",
      "description": "BSR最低增长率，单位 %"
    },
    "dataSnapshotMonth": {
      "type": "string",
      "default": "nearly",
      "examples": [
        {
          "value": "nearly",
          "summary": "查询最近30天的亚马逊商品实时数据（非快照数据）"
        },
        {
          "value": "202412",
          "summary": "查询2024年12月亚马逊所有在售商品的历史快照数据"
        },
        {
          "value": "202501",
          "summary": "查询2025年01月亚马逊所有在售商品的历史快照数据"
        }
      ],
      "maxLength": 1000,
      "description": "亚马逊商品数据快照年月。指定查询特定历史时间点的商品数据快照，每个快照包含该月份所有在售商品的完整数据。格式：yyyyMM（如202412表示2024年12月所有在售商品的数据快照）。默认值 'nearly' 表示查询最近30天的实时数据。注意：数据快照是对特定月份亚马逊市场上所有在售商品的完整记录，用于历史分析和同期对比。仅支持查询已存在的历史快照，不支持未来日期。建议季节性分析时查询去年同期快照进行对比"
    },
    "maxBsrGrowthCount": {
      "type": "integer",
      "description": "大类BSR最高增长数"
    },
    "maxSubNodeBsrRank": {
      "type": "integer",
      "description": "子类目BSR最大排名 ，只有在 filterSubNode 为 true 是生效"
    },
    "minBsrGrowthCount": {
      "type": "integer",
      "description": "BSR最低增长数"
    },
    "minSubNodeBsrRank": {
      "type": "integer",
      "description": "子类目BSR最低排名 ，只有在 filterSubNode 为 true 是生效"
    },
    "badgeAmazonsChoice": {
      "type": "string",
      "examples": [
        {
          "value": "Y",
          "summary": "是"
        },
        {
          "value": "N",
          "summary": "否"
        },
        {
          "value": "",
          "summary": "不传，查询全部数据"
        }
      ],
      "maxLength": 1000,
      "description": "是否有热销标识 Amazon's Choice(Y/N)"
    },
    "maxUnitsGrowthRate": {
      "type": "number",
      "description": "月销量最高增长率,单位 %"
    },
    "minUnitsGrowthRate": {
      "type": "number",
      "description": "月销量最低增长率,单位 %"
    },
    "hideUnlistedProduct": {
      "type": "boolean",
      "default": true,
      "examples": [
        {
          "value": "true",
          "summary": "隐藏,默认隐藏"
        },
        {
          "value": "false",
          "summary": "不隐藏"
        }
      ],
      "description": "是否隐藏已经下架的商品"
    },
    "maxRatingsGrowthCount": {
      "type": "integer",
      "minimum": 0,
      "description": "最高月新增评分数"
    },
    "minRatingsGrowthCount": {
      "type": "integer",
      "minimum": 0,
      "description": "最低月新增评分数"
    },
    "listedWithinLastMonths": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "近 1个 月"
        },
        {
          "value": "3",
          "summary": "近 3 个月"
        },
        {
          "value": "6",
          "summary": "近 6 个 月"
        },
        {
          "value": "12",
          "summary": "近 12 个月"
        },
        {
          "value": "24",
          "summary": "近 24 个月"
        }
      ],
      "description": "上架时间范围（月），商品上架日期距离当前日期的月份范围筛选，仅支持枚举值：1（近1个月内上架）、3（近3个月内上架）、6（近6个月内上架）、12（近12个月内上架）、24（近24个月内上架）。如果传入的是具体日期，应先计算该日期距离当前时间的月份差，并取不超过上述枚举值的最大值"
    },
    "maxListingQualityScore": {
      "type": "number",
      "minimum": 0,
      "description": "最高 Listing 页面质量分"
    },
    "minListingQualityScore": {
      "type": "number",
      "minimum": 0,
      "description": "最低 Listing 页面质量分，"
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
      "description": "总行数"
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
    "keyword": {
      "type": "string",
      "description": "对应筛选的关键词，如果有值，则表示这批数据是通过 这个关键词 keyword 搜索出来的"
    },
    "message": {
      "type": "string",
      "description": "消息"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "bsr": {
            "type": "integer",
            "description": "BSR 排名"
          },
          "fba": {
            "type": "number",
            "description": "fba运费"
          },
          "sku": {
            "type": "string",
            "description": "sku"
          },
          "asin": {
            "type": "string",
            "description": "asin"
          },
          "badge": {
            "type": "object",
            "required": [],
            "properties": {
              "ebc": {
                "type": "string",
                "description": "A+页面(Y/N)"
              },
              "video": {
                "type": "string",
                "description": "视频介绍(Y/N)"
              },
              "bestSeller": {
                "type": "string",
                "description": "Best Seller标识(Y/N)"
              },
              "newRelease": {
                "type": "string",
                "description": "release标识(Y/N)"
              },
              "amazonChoice": {
                "type": "string",
                "description": "amazon choice标识(Y/N)"
              }
            }
          },
          "brand": {
            "type": "string",
            "description": "品牌"
          },
          "price": {
            "type": "number",
            "description": "价格"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "nodeId": {
            "type": "integer",
            "description": "节点id"
          },
          "profit": {
            "type": "number",
            "description": "利润率"
          },
          "rating": {
            "type": "number",
            "description": "评分"
          },
          "weight": {
            "type": "string",
            "description": "重量"
          },
          "asinUrl": {
            "type": "string",
            "description": "亚马逊asin的详情网址"
          },
          "keyword": {
            "type": "string",
            "description": "对应筛选的关键词，如果有值，则表示这批数据是通过 这个关键词 keyword 搜索出来的"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数"
          },
          "badgeEbc": {
            "type": "string",
            "description": "A+页面(Y/N)"
          },
          "brandUrl": {
            "type": "string",
            "description": "品牌URL"
          },
          "currency": {
            "type": "string",
            "description": "币种"
          },
          "imageUrl": {
            "type": "string",
            "description": "图片URL"
          },
          "sellerId": {
            "type": "string",
            "description": "BuyBox卖家id"
          },
          "dimension": {
            "type": "string",
            "description": "尺寸"
          },
          "sellerNum": {
            "type": "integer",
            "description": "卖家数"
          },
          "badgeVideo": {
            "type": "string",
            "description": "视频介绍(Y/N)"
          },
          "nodeIdPath": {
            "type": "string",
            "description": "节点id路径字符串"
          },
          "primePrice": {
            "type": "number",
            "description": "prime价格"
          },
          "sellerName": {
            "type": "string",
            "description": "BuyBox卖家"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "来源类型：amazon"
          },
          "fulfillment": {
            "type": "string",
            "description": "配送方式(AMZ,FBA,FBM)"
          },
          "ratingsRate": {
            "type": "number",
            "description": "留评率"
          },
          "averagePrice": {
            "type": "number",
            "description": "平均价格"
          },
          "sellerNation": {
            "type": "string",
            "description": "BuyBox卖家国籍"
          },
          "variationNum": {
            "type": "integer",
            "description": "变体数"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "上架时间(时间戳)"
          },
          "bsrGrowthRate": {
            "type": "number",
            "description": "BSR 增长率"
          },
          "deliveryPrice": {
            "type": "number",
            "description": "卖家运费"
          },
          "nodeLabelPath": {
            "type": "string",
            "description": "类目路径"
          },
          "packageWeight": {
            "type": "string",
            "description": "包装重量"
          },
          "subcategories": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "code": {
                  "type": "string",
                  "description": "类目code"
                },
                "rank": {
                  "type": "integer",
                  "description": "排名"
                },
                "label": {
                  "type": "string",
                  "description": "名称"
                }
              }
            },
            "description": "子类目"
          },
          "dimensionsType": {
            "type": "string",
            "description": "尺寸类型"
          },
          "badgeBestSeller": {
            "type": "string",
            "description": "Best Seller标识(Y/N)"
          },
          "badgeNewRelease": {
            "type": "string",
            "description": "release标识(Y/N)"
          },
          "badgeAmazonChoice": {
            "type": "string",
            "description": "amazon choice标识(Y/N)"
          },
          "dataSnapshotMonth": {
            "type": "string",
            "description": "数据查询月份"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量"
          },
          "packageDimensions": {
            "type": "string",
            "description": "包装尺寸"
          },
          "variant30DayUnits": {
            "type": "integer",
            "description": "子体月销量(件数)"
          },
          "availableDateString": {
            "type": "string",
            "description": "上架日期(字符串)"
          },
          "listingQualityScore": {
            "type": "number",
            "description": "listing质量得分"
          },
          "monthlySalesRevenue": {
            "type": "number",
            "description": "月销售额"
          },
          "variant30DayRevenue": {
            "type": "number",
            "description": "子体月销售额(金额)"
          },
          "packageDimensionType": {
            "type": "string",
            "description": "包装尺寸类型"
          },
          "variant30DayUpdatedAt": {
            "type": "string",
            "description": "子体数据更新时间(日期)"
          },
          "monthlySalesUnitsGrowthRate": {
            "type": "number",
            "description": "月销量增长率"
          }
        }
      },
      "description": "搜索结果产品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "nodeLabel": {
      "type": "string",
      "description": "亚马逊类目"
    },
    "nodeIdPath": {
      "type": "string",
      "description": "搜索类目节点"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型：amazon"
    },
    "dataSnapshotMonth": {
      "type": "string",
      "description": "数据查询月份"
    }
  }
}
```

</details>
