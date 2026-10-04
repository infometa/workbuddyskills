# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "productId"
  ],
  "properties": {
    "userId": {
      "type": "string",
      "maxLength": 1000,
      "description": "达人ID"
    },
    "pageNum": {
      "type": "integer",
      "default": 1,
      "description": "分页页码"
    },
    "pageSize": {
      "type": "integer",
      "default": 50,
      "description": "分页条数(须为10的倍数, 最大100; 官方接口单页上限10, 内部按10每页多次拉取后合并)"
    },
    "sortType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "0",
          "summary": "升序"
        },
        {
          "value": "1",
          "summary": "降序"
        }
      ],
      "description": "排序方式, 0=升序 1=降序"
    },
    "productId": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品ID"
    },
    "maxCreateTime": {
      "type": "integer",
      "description": "视频发布时间区间-结束(秒级时间戳)"
    },
    "minCreateTime": {
      "type": "integer",
      "description": "视频发布时间区间-开始(秒级时间戳)"
    },
    "productVideoSortField": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "播放量"
        },
        {
          "value": "2",
          "summary": "点赞数"
        },
        {
          "value": "3",
          "summary": "分享数"
        },
        {
          "value": "4",
          "summary": "视频销量"
        },
        {
          "value": "5",
          "summary": "视频销售GMV"
        },
        {
          "value": "6",
          "summary": "发布时间"
        }
      ],
      "description": "排序字段, 1=播放量 2=点赞数 3=分享数 4=视频销量 5=视频销售GMV 6=发布时间"
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
          "ratio": {
            "type": "string",
            "description": "视频清晰度"
          },
          "width": {
            "type": "string",
            "description": "视频宽度"
          },
          "height": {
            "type": "string",
            "description": "视频高度"
          },
          "region": {
            "type": "string",
            "description": "区域代码"
          },
          "userId": {
            "type": "string",
            "description": "达人ID"
          },
          "hashTag": {
            "type": "string",
            "description": "话题标签"
          },
          "videoId": {
            "type": "string",
            "description": "视频ID"
          },
          "coverUrl": {
            "type": "string",
            "description": "视频封面URL"
          },
          "dataSize": {
            "type": "string",
            "description": "视频文件大小"
          },
          "duration": {
            "type": "integer",
            "description": "视频时长(秒)"
          },
          "playAddr": {
            "type": "string",
            "description": "视频播放地址(可能过期)"
          },
          "productId": {
            "type": "string",
            "description": "商品ID"
          },
          "videoDesc": {
            "type": "string",
            "description": "视频描述"
          },
          "createDate": {
            "type": "string",
            "format": "date",
            "description": "视频发布日期"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "商品来源"
          },
          "officialUrl": {
            "type": "string",
            "description": "TikTok官方视频地址"
          },
          "totalDiggCnt": {
            "type": "integer",
            "description": "点赞数"
          },
          "totalViewsCnt": {
            "type": "integer",
            "description": "播放量"
          },
          "totalSharesCnt": {
            "type": "integer",
            "description": "分享数"
          },
          "totalCommentsCnt": {
            "type": "integer",
            "description": "评论数"
          },
          "totalFavoritesCnt": {
            "type": "integer",
            "description": "收藏数"
          },
          "totalVideoSaleCnt": {
            "type": "integer",
            "description": "视频销量(估算)"
          },
          "totalVideoSaleGmvAmt": {
            "type": "integer",
            "description": "视频销售GMV(估算)"
          }
        }
      },
      "description": "视频列表"
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
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
