# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "topNumber",
    "imageUrl"
  ],
  "properties": {
    "regions": {
      "type": "string",
      "pattern": "^(US|WO|ES|GB|DE|IT|CA|MX|EM|AU|FR|JP|TR|BX|CN)(,(US|WO|ES|GB|DE|IT|CA|MX|EM|AU|FR|JP|TR|BX|CN))*$",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "WO",
          "summary": "世界知识产权"
        },
        {
          "value": "ES",
          "summary": "西班牙"
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
          "value": "IT",
          "summary": "意大利"
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
          "value": "EM",
          "summary": "欧盟"
        },
        {
          "value": "AU",
          "summary": "澳大利亚"
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
          "value": "TR",
          "summary": "土耳其"
        },
        {
          "value": "BX",
          "summary": "玻利维亚"
        },
        {
          "value": "CN",
          "summary": "中国"
        }
      ],
      "description": "需要检测的国家/地区，不传默认全部国家, 选择多个时，使用逗号隔开，如：US,WO,ES"
    },
    "imageUrl": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品图片base64文件"
    },
    "topNumber": {
      "type": "integer",
      "default": 5,
      "maximum": 100,
      "description": "返回yolo坐标的最大数量（有可能返回数量少于传参数量）"
    },
    "enableRadar": {
      "type": "boolean",
      "default": true,
      "description": "是否雷达监测"
    },
    "productTitle": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品标题"
    },
    "trademarkName": {
      "type": "string",
      "maxLength": 1000,
      "description": "可能的图形logo名称"
    },
    "enableLocalizing": {
      "type": "boolean",
      "default": false,
      "description": "是否开切图,不传默认不开启"
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
          "bid": {
            "type": "string",
            "description": "logo标识"
          },
          "image": {
            "type": "string",
            "description": "图片地址"
          },
          "niceClass": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "尼斯分类名称"
          },
          "similarity": {
            "type": "number",
            "description": "相似度"
          },
          "boundingBox": {
            "type": "string",
            "description": "yolo坐标（逗号隔开）"
          },
          "applicantName": {
            "type": "string",
            "description": "权利人（逗号隔开）"
          },
          "niceClassName": {
            "type": "string",
            "description": "尼斯分类名称（逗号隔开）"
          },
          "trademarkName": {
            "type": "string",
            "description": "图片中的文字商标名称"
          },
          "subRadarResult": {
            "type": "string",
            "description": "子雷达检测结果"
          },
          "applicationDate": {
            "type": "string",
            "description": "申请日期"
          },
          "tradeMarkStatus": {
            "type": "string",
            "description": "商标状态，枚举：\"DEL\",\"ended\"，\"registered\",\"act\",\"pend\",\"filed\",\"\""
          },
          "registrationDate": {
            "type": "string",
            "description": "注册日期"
          },
          "applicationNumber": {
            "type": "string",
            "description": "申请号"
          },
          "registrationNumber": {
            "type": "string",
            "description": "注册号"
          },
          "registrationOfficeCode": {
            "type": "string",
            "description": "商标受理局"
          }
        }
      },
      "description": "检测结果列表"
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
      "description": "检测id"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "radarResult": {
      "type": "string",
      "description": "雷达检测结果"
    },
    "boundingBoxCount": {
      "type": "integer",
      "description": "检测结果数量"
    }
  }
}
```

</details>
