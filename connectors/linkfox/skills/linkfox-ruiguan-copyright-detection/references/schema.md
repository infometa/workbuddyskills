# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "imageUrl",
    "topNumber",
    "enableRadar"
  ],
  "properties": {
    "imageUrl": {
      "type": "string",
      "maxLength": 1000,
      "description": "检测的版权图片URL"
    },
    "topNumber": {
      "type": "integer",
      "default": 100,
      "maximum": 100,
      "minimum": 10,
      "description": "召回数量（默认100，最大200）"
    },
    "enableRadar": {
      "type": "boolean",
      "default": true,
      "description": "是否开启雷达检测"
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
          "link": {
            "type": "string",
            "description": "版权官网链接"
          },
          "path": {
            "type": "string",
            "description": "版权画图片路径"
          },
          "troCase": {
            "type": "boolean",
            "description": "是否有TRO维权史"
          },
          "pathThumb": {
            "type": "string",
            "description": "版权画缩略图路径"
          },
          "troHolder": {
            "type": "boolean",
            "description": "是否是TRO权利人的版权"
          },
          "similarity": {
            "type": "string",
            "description": "相似度"
          },
          "rightsOwner": {
            "type": "string",
            "description": "权利人"
          },
          "copyrightUrl": {
            "type": "string",
            "description": "来源"
          },
          "copyrightCode": {
            "type": "string",
            "description": "版权标识码"
          },
          "subRadarResult": {
            "type": "integer",
            "description": "1-侵权 0-不侵权 ,null 没有进行雷达检测"
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
    }
  }
}
```

</details>
