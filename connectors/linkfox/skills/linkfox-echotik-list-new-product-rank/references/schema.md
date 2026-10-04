# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "date"
  ],
  "properties": {
    "date": {
      "type": "string",
      "maxLength": 1000,
      "description": "日期, 格式为YYYY-MM-DD"
    },
    "region": {
      "type": "string",
      "default": "US",
      "pattern": "^(US|ID|TH|PH|MY|VN|GB|MX|SG|SA|BR|ES|JP|DE|IT|FR)$",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "ID",
          "summary": "印度尼西亚"
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
          "value": "MY",
          "summary": "马来西亚"
        },
        {
          "value": "VN",
          "summary": "越南"
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
          "value": "SG",
          "summary": "新加坡"
        },
        {
          "value": "SA",
          "summary": "沙特阿拉伯"
        },
        {
          "value": "BR",
          "summary": "巴西"
        },
        {
          "value": "ES",
          "summary": "西班牙"
        },
        {
          "value": "JP",
          "summary": "日本"
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
          "value": "FR",
          "summary": "法国"
        }
      ],
      "description": "区域"
    },
    "pageNum": {
      "type": "integer",
      "default": 1,
      "description": "分页页码"
    },
    "pageSize": {
      "type": "integer",
      "default": 50,
      "description": "分页页码"
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
          "asin": {
            "type": "string",
            "description": "商品ID"
          },
          "price": {
            "type": "number",
            "description": "SPU平均价格"
          },
          "title": {
            "type": "string",
            "description": "商品名称"
          },
          "region": {
            "type": "string",
            "description": "区域代码"
          },
          "currency": {
            "type": "string",
            "description": "货币"
          },
          "imageUrl": {
            "type": "string",
            "description": "商品图片"
          },
          "maxPrice": {
            "type": "number",
            "description": "最高价格"
          },
          "minPrice": {
            "type": "number",
            "description": "最低价格"
          },
          "categoryId": {
            "type": "string",
            "description": "商品分类ID"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "商品来源"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论数量"
          },
          "totalIflCnt": {
            "type": "integer",
            "description": "总达人数"
          },
          "totalLiveCnt": {
            "type": "integer",
            "description": "直播总数"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "总销量"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "首次爬取日期-firstCrawlDt"
          },
          "productRating": {
            "type": "number",
            "description": "商品评分"
          },
          "totalVideoCnt": {
            "type": "integer",
            "description": "视频总数"
          },
          "totalSale30dCnt": {
            "type": "integer",
            "description": "近30天销量"
          },
          "totalSaleGmvAmt": {
            "type": "number",
            "description": "总销售额"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "商品图片URL列表"
          },
          "salesTrendFlagText": {
            "type": "string",
            "description": "销售趋势标识, 0=平稳 1=上升 2=下降"
          },
          "totalSaleGmv30dAmt": {
            "type": "number",
            "description": "近30天销售额"
          },
          "productCommissionRate": {
            "type": "number",
            "description": "商品佣金比例"
          }
        }
      },
      "description": "最新商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
