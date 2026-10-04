# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "marketplace",
    "keyword",
    "startDate",
    "endDate"
  ],
  "properties": {
    "endDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-02-01",
          "summary": "周期终点"
        }
      ],
      "maxLength": 1000,
      "description": "结束日期(YYYY-MM-DD)；与开始日期间隔最大366天"
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "sushi",
          "summary": "示例关键词"
        }
      ],
      "maxLength": 1000,
      "description": "要查询的关键词"
    },
    "startDate": {
      "type": "string",
      "examples": [
        {
          "value": "2025-01-05",
          "summary": "周期起点"
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
    "historicalSearchVolumeList": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "id": {
            "type": "string",
            "description": "数据周期标识(市场/关键词/日期范围)"
          },
          "type": {
            "type": "string",
            "description": "响应资源类型(固定 historical_keyword_search_volume)"
          },
          "estimateEndDate": {
            "type": "string",
            "description": "周期结束日期(YYYY-MM-DD，7天统计周期终点)"
          },
          "estimateStartDate": {
            "type": "string",
            "description": "周期开始日期(YYYY-MM-DD，7天统计周期起点)"
          },
          "estimatedExactSearchVolume": {
            "type": "integer",
            "description": "该周期内精确匹配搜索量(次/周)"
          }
        }
      },
      "description": "历史搜索量周期列表"
    }
  }
}
```

</details>
