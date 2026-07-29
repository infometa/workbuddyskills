# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "examples": [
        {
          "value": "B08N5WRWNW",
          "summary": "示例ASIN"
        }
      ],
      "maxLength": 1000,
      "description": "亚马逊商品ASIN"
    },
    "sortBy": {
      "type": "string",
      "default": "recent",
      "pattern": "recent|helpful",
      "examples": [
        {
          "value": "recent",
          "summary": "最新评论"
        },
        {
          "value": "helpful",
          "summary": "最有用评论"
        }
      ],
      "description": "评论排序方式"
    },
    "star1Num": {
      "type": "integer",
      "maximum": 100,
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "获取10条1星评论"
        }
      ],
      "description": "1星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条"
    },
    "star2Num": {
      "type": "integer",
      "maximum": 100,
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "获取10条2星评论"
        }
      ],
      "description": "2星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条"
    },
    "star3Num": {
      "type": "integer",
      "maximum": 100,
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "获取10条3星评论"
        }
      ],
      "description": "3星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条"
    },
    "star4Num": {
      "type": "integer",
      "maximum": 100,
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "获取10条4星评论"
        }
      ],
      "description": "4星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条"
    },
    "star5Num": {
      "type": "integer",
      "maximum": 100,
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "获取10条5星评论"
        }
      ],
      "description": "5星评论数量，最多100条；若任意星级字段有传值，仅查询传入且大于0的星级；若所有星级字段均未传，默认每个星级获取10条"
    },
    "mediaType": {
      "type": "string",
      "default": "all_contents",
      "pattern": "all_contents|media_reviews_only",
      "examples": [
        {
          "value": "all_contents",
          "summary": "所有内容"
        },
        {
          "value": "media_reviews_only",
          "summary": "仅包含媒体的评论"
        }
      ],
      "description": "媒体类型"
    },
    "domainCode": {
      "type": "string",
      "default": "com",
      "pattern": "com|ca|co.uk|in|de|fr|it|es|co.jp|com.au|com.br|nl|se|com.mx|ae",
      "examples": [
        {
          "value": "com",
          "summary": "美国站"
        },
        {
          "value": "ca",
          "summary": "加拿大站"
        },
        {
          "value": "co.uk",
          "summary": "英国站"
        },
        {
          "value": "in",
          "summary": "印度站"
        },
        {
          "value": "de",
          "summary": "德国站"
        },
        {
          "value": "fr",
          "summary": "法国站"
        },
        {
          "value": "it",
          "summary": "意大利站"
        },
        {
          "value": "es",
          "summary": "西班牙站"
        },
        {
          "value": "co.jp",
          "summary": "日本站"
        },
        {
          "value": "com.au",
          "summary": "澳大利亚站"
        },
        {
          "value": "com.br",
          "summary": "巴西站"
        },
        {
          "value": "nl",
          "summary": "荷兰站"
        },
        {
          "value": "se",
          "summary": "瑞典站"
        },
        {
          "value": "com.mx",
          "summary": "墨西哥站"
        },
        {
          "value": "ae",
          "summary": "阿联酋站"
        }
      ],
      "description": "亚马逊域名代码"
    },
    "formatType": {
      "type": "string",
      "default": "all_formats",
      "pattern": "current_format|all_formats",
      "examples": [
        {
          "value": "all_formats",
          "summary": "所有格式"
        },
        {
          "value": "current_format",
          "summary": "当前格式"
        }
      ],
      "description": "格式类型"
    },
    "reviewerType": {
      "type": "string",
      "default": "all_reviews",
      "pattern": "all_reviews|avp_only_reviews",
      "examples": [
        {
          "value": "all_reviews",
          "summary": "所有评论"
        },
        {
          "value": "avp_only_reviews",
          "summary": "仅认证购买"
        }
      ],
      "description": "评论者类型"
    },
    "filterByKeyword": {
      "type": "string",
      "examples": [
        {
          "value": "quality",
          "summary": "筛选包含'quality'的评论"
        }
      ],
      "maxLength": 1000,
      "description": "按关键词筛选评论"
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
          "asin": {
            "type": "string",
            "description": "产品ASIN"
          },
          "date": {
            "type": "string",
            "description": "评论日期"
          },
          "text": {
            "type": "string",
            "description": "评论内容"
          },
          "vine": {
            "type": "boolean",
            "description": "是否Vine Voice评论"
          },
          "title": {
            "type": "string",
            "description": "评论标题"
          },
          "locale": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "rating": {
            "type": "string",
            "description": "评分"
          },
          "filters": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "reviewId": {
            "type": "string",
            "description": "评论ID"
          },
          "userName": {
            "type": "string",
            "description": "评论者名称"
          },
          "verified": {
            "type": "boolean",
            "description": "是否已验证购买"
          },
          "domainCode": {
            "type": "string",
            "description": "国家代码"
          },
          "statusCode": {
            "type": "integer",
            "description": "状态码"
          },
          "currentPage": {
            "type": "integer",
            "description": "当前页码"
          },
          "profilePath": {
            "type": "string",
            "description": "评论者个人资料路径"
          },
          "variationId": {
            "type": "string",
            "description": "变体ID"
          },
          "countRatings": {
            "type": "integer",
            "description": "产品评分数量"
          },
          "countReviews": {
            "type": "integer",
            "description": "产品评论数量"
          },
          "imageUrlList": {
            "type": "array",
            "items": {},
            "description": "评论图片列表"
          },
          "productTitle": {
            "type": "string",
            "description": "产品标题"
          },
          "sortStrategy": {
            "type": "string",
            "description": "排序策略"
          },
          "videoUrlList": {
            "type": "array",
            "items": {},
            "description": "评论视频列表"
          },
          "productRating": {
            "type": "string",
            "description": "产品评分"
          },
          "reviewSummary": {
            "type": "object",
            "required": [],
            "properties": {}
          },
          "statusMessage": {
            "type": "string",
            "description": "状态消息"
          },
          "variationList": {
            "type": "array",
            "items": {},
            "description": "变体列表"
          },
          "numberOfHelpful": {
            "type": "integer",
            "description": "有用数量"
          }
        }
      },
      "description": "评论列表"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "总评论数"
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
      "description": "总Token消耗"
    }
  }
}
```

</details>
