# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "node": {
      "type": "string",
      "maxLength": 1000,
      "description": "亚马逊类目节点"
    },
    "page": {
      "type": "integer",
      "default": 1,
      "description": "页码(从1开始，每页大概20条)"
    },
    "sort": {
      "type": "string",
      "default": "relevanceblender",
      "examples": [
        {
          "value": "relevanceblender",
          "summary": " 精选（默认）"
        },
        {
          "value": "price-asc-rank",
          "summary": "价格：从低到高"
        },
        {
          "value": "price-desc-rank",
          "summary": "价格：从高到低"
        },
        {
          "value": "review-rank",
          "summary": "平均客户评价"
        },
        {
          "value": "date-desc-rank",
          "summary": "最新到货"
        },
        {
          "value": "exact-aware-popularity-rank",
          "summary": "畅销商品"
        }
      ],
      "maxLength": 1000,
      "description": "排序"
    },
    "device": {
      "type": "string",
      "examples": [
        {
          "value": "desktop",
          "summary": "desktop"
        },
        {
          "value": "mobile",
          "summary": "mobile"
        },
        {
          "value": "tablet",
          "summary": "tablet"
        }
      ],
      "maxLength": 1000,
      "description": "设备类型(device): desktop/mobile，默认 desktop"
    },
    "keyword": {
      "type": "string",
      "maxLength": 1024,
      "description": "关键词；请尽量翻译为对应国家的语言，比如美国用英语关键词，德国用德语关键词等等 "
    },
    "language": {
      "type": "string",
      "examples": [
        {
          "value": "en_US",
          "summary": "美国站 英语"
        },
        {
          "value": "en_AU",
          "summary": "澳大利亚站 英语"
        },
        {
          "value": "nl_BE",
          "summary": "比利时站 荷兰语"
        },
        {
          "value": "fr_BE",
          "summary": "比利时站 法语"
        },
        {
          "value": "pt_BR",
          "summary": "巴西站 葡萄牙语"
        },
        {
          "value": "en_CA",
          "summary": "加拿大站 英语"
        },
        {
          "value": "fr_CA",
          "summary": "加拿大站 法语"
        },
        {
          "value": "zh_CN",
          "summary": "中国站 中文"
        },
        {
          "value": "ar_AE",
          "summary": "埃及站 阿拉伯语"
        },
        {
          "value": "en_AE",
          "summary": "埃及站 英语"
        },
        {
          "value": "fr_FR",
          "summary": "法国站 法语"
        },
        {
          "value": "de_DE",
          "summary": "德国站 德语"
        },
        {
          "value": "hi_IN",
          "summary": "印度站 印地语"
        },
        {
          "value": "en_IN",
          "summary": "印度站 英语"
        },
        {
          "value": "it_IT",
          "summary": "意大利站 意大利语"
        },
        {
          "value": "ja_JP",
          "summary": "日本站 日语"
        },
        {
          "value": "nl_NL",
          "summary": "荷兰站 荷兰语"
        },
        {
          "value": "pl_PL",
          "summary": "波兰站 波兰语"
        },
        {
          "value": "ar_AE",
          "summary": "沙特阿拉伯站 阿拉伯语"
        },
        {
          "value": "en_AE",
          "summary": "沙特阿拉伯站 英语"
        },
        {
          "value": "en_SG",
          "summary": "新加坡站 英语"
        },
        {
          "value": "es_ES",
          "summary": "西班牙站 西班牙语"
        },
        {
          "value": "sv_SE",
          "summary": "瑞典站 瑞典语"
        },
        {
          "value": "tr_TR",
          "summary": "土耳其站 土耳其语"
        },
        {
          "value": "ar_AE",
          "summary": "阿联酋站 阿拉伯语"
        },
        {
          "value": "en_AE",
          "summary": "阿联酋站 英语"
        },
        {
          "value": "en_GB",
          "summary": "英国站 英语"
        },
        {
          "value": "pt_MX",
          "summary": "墨西哥站 西班牙语"
        }
      ],
      "maxLength": 1000,
      "description": "语言"
    },
    "deliveryZip": {
      "type": "string",
      "examples": [
        {
          "value": "10001",
          "summary": "美国 纽约"
        },
        {
          "value": "2000",
          "summary": "澳大利亚 悉尼"
        },
        {
          "value": "1000",
          "summary": "比利时 布鲁塞尔"
        },
        {
          "value": "01000-000",
          "summary": "巴西 圣保罗"
        },
        {
          "value": "M5A 1A1",
          "summary": "加拿大 多伦多"
        },
        {
          "value": "100000",
          "summary": "中国 北京"
        },
        {
          "value": "11511",
          "summary": "埃及 开罗"
        },
        {
          "value": "75001",
          "summary": "法国 巴黎"
        },
        {
          "value": "10115",
          "summary": "德国 柏林"
        },
        {
          "value": "110001",
          "summary": "印度 新德里"
        },
        {
          "value": "00100",
          "summary": "意大利 罗马"
        },
        {
          "value": "100-0001",
          "summary": "日本 东京"
        },
        {
          "value": "1012",
          "summary": "荷兰 阿姆斯特丹"
        },
        {
          "value": "00-001",
          "summary": "波兰 华沙"
        },
        {
          "value": "11564",
          "summary": "沙特阿拉伯 利雅得"
        },
        {
          "value": "018989",
          "summary": "新加坡 新加坡"
        },
        {
          "value": "28001",
          "summary": "西班牙 马德里"
        },
        {
          "value": "111 22",
          "summary": "瑞典 斯德哥尔摩"
        },
        {
          "value": "34349",
          "summary": "土耳其 伊斯坦布尔"
        },
        {
          "value": "00000",
          "summary": "阿联酋 阿布扎比"
        },
        {
          "value": "EC1A 1BB",
          "summary": "英国 伦敦"
        },
        {
          "value": "01000",
          "summary": "墨西哥 墨西哥城"
        }
      ],
      "maxLength": 1000,
      "description": "Generate a recommended postal code commonly used for Amazon frontend address entry in the specified country (preferably from a major city). For example, Amazon US site often uses New York's postal code 10001"
    },
    "amazonDomain": {
      "type": "string",
      "default": "amazon.com",
      "pattern": "^(amazon\\.com|amazon\\.com\\.au|amazon\\.com\\.be|amazon\\.com\\.br|amazon\\.ca|amazon\\.cn|amazon\\.eg|amazon\\.fr|amazon\\.de|amazon\\.in|amazon\\.it|amazon\\.co\\.jp|amazon\\.nl|amazon\\.pl|amazon\\.sa|amazon\\.sg|amazon\\.es|amazon\\.se|amazon\\.com\\.tr|amazon\\.ae|amazon\\.co\\.uk|amazon\\.com\\.mx)$",
      "examples": [
        {
          "value": "amazon.com",
          "summary": "默认值，亚马逊美国站"
        },
        {
          "value": "amazon.com.au",
          "summary": "亚马逊澳大利亚站"
        },
        {
          "value": "amazon.com.be",
          "summary": "亚马逊比利时站"
        },
        {
          "value": "amazon.com.br",
          "summary": "亚马逊巴西站"
        },
        {
          "value": "amazon.ca",
          "summary": "亚马逊加拿大站"
        },
        {
          "value": "amazon.cn",
          "summary": "亚马逊中国站"
        },
        {
          "value": "amazon.eg",
          "summary": "亚马逊埃及站"
        },
        {
          "value": "amazon.fr",
          "summary": "亚马逊法国站"
        },
        {
          "value": "amazon.de",
          "summary": "亚马逊德国站"
        },
        {
          "value": "amazon.in",
          "summary": "亚马逊印度站"
        },
        {
          "value": "amazon.it",
          "summary": "亚马逊意大利站"
        },
        {
          "value": "amazon.co.jp",
          "summary": "亚马逊日本站"
        },
        {
          "value": "amazon.nl",
          "summary": "亚马逊荷兰站"
        },
        {
          "value": "amazon.pl",
          "summary": "亚马逊波兰站"
        },
        {
          "value": "amazon.sa",
          "summary": "亚马逊沙特阿拉伯站"
        },
        {
          "value": "amazon.sg",
          "summary": "亚马逊新加坡站"
        },
        {
          "value": "amazon.es",
          "summary": "亚马逊西班牙站"
        },
        {
          "value": "amazon.se",
          "summary": "亚马逊瑞典站"
        },
        {
          "value": "amazon.com.tr",
          "summary": "亚马逊土耳其站"
        },
        {
          "value": "amazon.ae",
          "summary": "亚马逊阿联酋站"
        },
        {
          "value": "amazon.co.uk",
          "summary": "亚马逊英国站"
        },
        {
          "value": "amazon.com.mx",
          "summary": "亚马逊墨西哥站"
        }
      ],
      "description": "亚马逊各个国家站点，默认 amazon.com"
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
      "description": "keyword"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "asin": {
            "type": "string",
            "description": "ASIN"
          },
          "tags": {
            "type": "string",
            "description": "标签"
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
            "description": "标题"
          },
          "badges": {
            "type": "string",
            "description": "亚马逊前台搜索标识"
          },
          "offers": {
            "type": "string",
            "description": "优惠信息"
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
            "description": "链接"
          },
          "keyword": {
            "type": "string",
            "description": "keyword"
          },
          "options": {
            "type": "string",
            "description": "选项"
          },
          "ratings": {
            "type": "integer",
            "description": "评分数"
          },
          "currency": {
            "type": "string",
            "description": "币种"
          },
          "delivery": {
            "type": "string",
            "description": "配送信息"
          },
          "imageUrl": {
            "type": "string",
            "description": "缩略图"
          },
          "oldPrice": {
            "type": "number",
            "description": "划线价格"
          },
          "position": {
            "type": "integer",
            "description": "位置"
          },
          "dimension": {
            "type": "string",
            "description": "尺寸"
          },
          "priceUnit": {
            "type": "string",
            "description": "价格单位"
          },
          "sponsored": {
            "type": "boolean",
            "description": "是否赞助商"
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
            "description": "配送信息"
          },
          "sellerNation": {
            "type": "string",
            "description": "卖家国籍"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "上架时间"
          },
          "extractedPrice": {
            "type": "number",
            "description": "解析后的价格"
          },
          "snapEbtEligible": {
            "type": "boolean",
            "description": "SNAP/EBT资格"
          },
          "extractedOldPrice": {
            "type": "number",
            "description": "解析后的划线价格"
          },
          "monthlySalesUnits": {
            "type": "integer",
            "description": "月销量"
          },
          "extractedPriceUnit": {
            "type": "number",
            "description": "解析后的价格单位"
          },
          "monthlySalesRevenue": {
            "type": "string",
            "description": "月销售额"
          }
        }
      },
      "description": "搜索结果列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
