# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "productTitle",
    "limit"
  ],
  "properties": {
    "limit": {
      "type": "integer",
      "default": 100,
      "maximum": 500,
      "description": "返回结果数量限制"
    },
    "regions": {
      "type": "string",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "EM",
          "summary": "欧盟"
        },
        {
          "value": "GB",
          "summary": "英国"
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
          "value": "IT",
          "summary": "意大利"
        },
        {
          "value": "ES",
          "summary": "西班牙"
        },
        {
          "value": "AU",
          "summary": "澳大利亚"
        },
        {
          "value": "CA",
          "summary": "加拿大"
        },
        {
          "value": "MX",
          "summary": "墨西哥"
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
          "value": "WO",
          "summary": "世界知识产权"
        },
        {
          "value": "TR",
          "summary": "土耳其"
        },
        {
          "value": "BX",
          "summary": "玻利维亚"
        }
      ],
      "maxLength": 1000,
      "description": "国家/地区代码，多个用逗号分隔，支持 AU,BX,CA,DE,EM,ES,FR,GB,IT,JP,MX,TR,US,WO,CN"
    },
    "productText": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品的其他文本信息"
    },
    "productTitle": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品标题"
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
          "score": {
            "type": "integer",
            "description": "风险分数"
          },
          "holder": {
            "type": "string",
            "description": "权利人"
          },
          "region": {
            "type": "string",
            "description": "国家/地区代码"
          },
          "isFamous": {
            "type": "boolean",
            "description": "是否著名商标"
          },
          "niceClass": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "尼斯分类"
          },
          "regionStatus": {
            "type": "string",
            "description": "状态"
          },
          "isAmazonBrand": {
            "type": "boolean",
            "description": "是否亚马逊热搜品牌"
          },
          "isCommonSense": {
            "type": "boolean",
            "description": "是否常用词"
          },
          "trademarkName": {
            "type": "string",
            "description": "商标词"
          },
          "isActiveHolder": {
            "type": "boolean",
            "description": "是否活跃维权人"
          },
          "isCompatibility": {
            "type": "boolean",
            "description": "是否兼容性"
          },
          "highestModeScore": {
            "type": "integer",
            "description": "最高风险分数（范围0-5）"
          },
          "trademarksStatus": {
            "type": "string",
            "description": "最高分商标词状态"
          },
          "applicationNumber": {
            "type": "string",
            "description": "申请号"
          },
          "registrationNumber": {
            "type": "string",
            "description": "注册号"
          },
          "originalTextMatches": {
            "type": "array",
            "items": {},
            "description": "原词"
          }
        }
      },
      "description": "商标列表（扁平化）"
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
    "detectId": {
      "type": "string",
      "description": "接口调用 id"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "textTrademarkRadar": {
      "type": "string",
      "description": "产品风险等级：0低风险, 1待人工核查, 2高风险"
    },
    "blacklistTrademarks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "note": {
            "type": "string",
            "description": "备注"
          },
          "region": {
            "type": "string",
            "description": "国家"
          },
          "trademark": {
            "type": "string",
            "description": "商标"
          }
        }
      },
      "description": "黑名单"
    },
    "whitelistTrademarks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "note": {
            "type": "string",
            "description": "备注"
          },
          "region": {
            "type": "string",
            "description": "国家"
          },
          "trademark": {
            "type": "string",
            "description": "商标"
          }
        }
      },
      "description": "白名单"
    }
  }
}
```

</details>
