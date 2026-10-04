# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "region",
    "dateInfo"
  ],
  "properties": {
    "page": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "第1页"
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
          "value": "MX",
          "summary": "墨西哥"
        },
        {
          "value": "ES",
          "summary": "西班牙"
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
          "value": "DE",
          "summary": "德国"
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
      "description": "国家/地区代码，与商品搜索相同白名单：['US','GB','MX','ES','DE','IT','FR','ID','VN','MY','TH','PH','BR','JP','SG']"
    },
    "orderby": {
      "type": "object",
      "required": [
        "field"
      ],
      "properties": {
        "field": {
          "type": "string",
          "examples": [
            {
              "value": "units_sold",
              "summary": "销量"
            },
            {
              "value": "gmv",
              "summary": "销售额"
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
              "value": "growth_rate",
              "summary": "增长率"
            }
          ],
          "maxLength": 1000,
          "description": "排序字段名"
        },
        "order": {
          "type": "string",
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
          "maxLength": 1000,
          "description": "排序方向：desc-降序, asc-升序，默认 desc"
        }
      }
    },
    "category": {
      "type": "string",
      "examples": [
        {
          "value": "Phone Cases",
          "summary": "手机壳（英文）"
        }
      ],
      "maxLength": 1000,
      "description": "类目名称（文本，用于匹配 TikTok 英文类目并解析为一级类目 ID）。TikTok 类目为英文，服务端按英文做 BM25 匹配；若用户输入非英语，请先在对话侧译为英语再传入本参数。"
    },
    "dateInfo": {
      "type": "object",
      "required": [
        "type",
        "value"
      ],
      "properties": {
        "type": {
          "type": "string",
          "examples": [
            {
              "value": "day",
              "summary": "按天"
            },
            {
              "value": "week",
              "summary": "按周"
            },
            {
              "value": "month",
              "summary": "按月"
            }
          ],
          "maxLength": 1000,
          "description": "日期类型：day-按天, week-按周, month-按月"
        },
        "value": {
          "type": "string",
          "examples": [
            {
              "value": "2025-02-01",
              "summary": "按天示例"
            },
            {
              "value": "2025-18",
              "summary": "按周示例"
            },
            {
              "value": "2025-02",
              "summary": "按月示例"
            }
          ],
          "maxLength": 1000,
          "description": "日期值，格式取决于type：day→'2025-02-01', week→'2025-18', month→'2025-02'"
        }
      }
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
            "description": "商品价格.数值类型，含价格范围时取最低值，货币单位见currency字段"
          },
          "title": {
            "type": "string",
            "description": "商品名称"
          },
          "region": {
            "type": "string",
            "description": "区域代码.如US、GB、ID等"
          },
          "coverUrl": {
            "type": "array",
            "items": {},
            "description": "商品封面图URL列表"
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
            "description": "最高价格.仅当原始价格为范围时有值，货币单位见currency字段"
          },
          "minPrice": {
            "type": "number",
            "description": "最低价格.仅当原始价格为范围时有值，货币单位见currency字段"
          },
          "shopName": {
            "type": "string",
            "description": "店铺名称"
          },
          "productId": {
            "type": "string",
            "description": "TikTok产品ID.如1730696681877443081"
          },
          "growthRate": {
            "type": "number",
            "description": "销量增长率(单位%)"
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
            "description": "商品品类ID列表.一级到三级，如[\"24\",\"914824\",\"819984\"]"
          },
          "categoryName": {
            "type": "string",
            "description": "商品品类名称路径.如Food & Beverages -> Drinks -> Meal Replacement & Protein Drinks"
          },
          "shopSellerId": {
            "type": "string",
            "description": "店铺ID"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "总销量.累计历史总销量"
          },
          "offShelvesText": {
            "type": "string",
            "description": "是否下架.是=已下架，否=在售"
          },
          "totalSale1dCnt": {
            "type": "integer",
            "description": "1天内销量"
          },
          "totalSale7dCnt": {
            "type": "integer",
            "description": "7天内销量.仅dateType=week时有值"
          },
          "totalSale30dCnt": {
            "type": "integer",
            "description": "30天内销量.仅dateType=month时有值，与筛选周期一致的区间销量"
          },
          "totalSaleGmvAmt": {
            "type": "number",
            "description": "总销售额.累计历史总销售额，货币单位见currency字段"
          },
          "totalSaleGmv1dAmt": {
            "type": "number",
            "description": "1天内销售额.仅dateType=day时有值，货币单位见currency字段"
          },
          "totalSaleGmv7dAmt": {
            "type": "number",
            "description": "7天内销售额.仅dateType=week时有值，货币单位见currency字段"
          },
          "shopTotalUnitsSold": {
            "type": "integer",
            "description": "店铺总销量"
          },
          "totalSaleGmv30dAmt": {
            "type": "number",
            "description": "30天内销售额.仅dateType=month时有值，货币单位见currency字段"
          },
          "productCommissionRate": {
            "type": "integer",
            "description": "商品佣金比例.基点制整数，1000表示10%，除以100得百分比值"
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
