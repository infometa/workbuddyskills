# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "asin",
    "startDate",
    "endDate"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "examples": [
        {
          "value": "B08JYQLKXZ",
          "summary": "示例ASIN"
        }
      ],
      "maxLength": 1000,
      "description": "要查询的产品ASIN(10位Amazon标准ASIN)"
    },
    "endDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-11-02",
          "summary": "区间终点"
        }
      ],
      "maxLength": 1000,
      "description": "结束日期(YYYY-MM-DD)；须早于当前日期"
    },
    "startDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-10-01",
          "summary": "区间起点"
        }
      ],
      "maxLength": 1000,
      "description": "开始日期(YYYY-MM-DD)"
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
    "salesEstimateList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "id": {
            "type": "string",
            "description": "销售数据标识(市场/ASIN)"
          },
          "asin": {
            "type": "string",
            "description": "产品ASIN"
          },
          "type": {
            "type": "string",
            "description": "响应资源类型(固定 sales_estimate_result)"
          },
          "isParent": {
            "type": "boolean",
            "description": "是否父ASIN"
          },
          "variants": {
            "type": "array",
            "items": {},
            "description": "变体ASIN列表(查询为父体时列出子变体，否则为空数组)"
          },
          "isVariant": {
            "type": "boolean",
            "description": "是否变体ASIN"
          },
          "parentAsin": {
            "type": "string",
            "description": "父产品ASIN；与查询ASIN相同表示查询目标为父体；不同则为变体；为空表示独立ASIN"
          },
          "isStandalone": {
            "type": "boolean",
            "description": "是否独立ASIN"
          },
          "dailyEstimates": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "date": {
                  "type": "string",
                  "description": "销售日期(YYYY-MM-DD)"
                },
                "lastKnownPrice": {
                  "type": "number",
                  "description": "该日最后已知价格(USD)"
                },
                "estimatedUnitsSold": {
                  "type": "integer",
                  "description": "该日估算销量(件)"
                }
              }
            },
            "description": "按日期的销售估算序列"
          }
        }
      },
      "description": "销售估算结果列表"
    }
  }
}
```

</details>
