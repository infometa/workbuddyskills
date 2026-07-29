# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "productIds": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "maxItems": 1000,
      "description": "商品ID列表, 多个使用英文逗号分隔"
    },
    "productUrls": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "maxItems": 1000,
      "description": "商品URL列表, 形如 https://shop.tiktok.com/us/pdp/<slug>/<productId>?... ; 将从每个URL中提取末尾的productId并合并到productIds, 与productIds不排斥"
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
          "region": {
            "type": "string",
            "description": "区域代码"
          },
          "isSShop": {
            "type": "integer",
            "description": "是否全托管店铺"
          },
          "offMark": {
            "type": "integer",
            "description": "商品下架标识"
          },
          "discount": {
            "type": "string",
            "description": "折扣信息"
          },
          "imageUrl": {
            "type": "string",
            "description": "商品图片"
          },
          "maxPrice": {
            "type": "number",
            "description": "最高SKU价格(USD)"
          },
          "minPrice": {
            "type": "number",
            "description": "最低SKU价格(USD)"
          },
          "sellerId": {
            "type": "string",
            "description": "卖家ID"
          },
          "productId": {
            "type": "string",
            "description": "商品ID"
          },
          "salesFlag": {
            "type": "integer",
            "description": "主要配送方式"
          },
          "categoryId": {
            "type": "string",
            "description": "一级分类ID"
          },
          "descDetail": {
            "type": "string",
            "description": "商品详情描述"
          },
          "productName": {
            "type": "string",
            "description": "商品名称"
          },
          "reviewCount": {
            "type": "integer",
            "description": "评论数量"
          },
          "spuAvgPrice": {
            "type": "number",
            "description": "SPU平均价格(USD)"
          },
          "totalIflCnt": {
            "type": "integer",
            "description": "总达人数量"
          },
          "categoryL2Id": {
            "type": "string",
            "description": "二级分类ID"
          },
          "categoryL3Id": {
            "type": "string",
            "description": "三级分类ID"
          },
          "firstCrawlDt": {
            "type": "string",
            "description": "首次爬取日期"
          },
          "freeShipping": {
            "type": "integer",
            "description": "是否免运费"
          },
          "totalLiveCnt": {
            "type": "integer",
            "description": "总直播数量"
          },
          "totalSaleCnt": {
            "type": "integer",
            "description": "总销量"
          },
          "productRating": {
            "type": "number",
            "description": "商品评分"
          },
          "totalVideoCnt": {
            "type": "integer",
            "description": "总视频数量"
          },
          "totalViewsCnt": {
            "type": "integer",
            "description": "总观看次数"
          },
          "salesTrendFlag": {
            "type": "integer",
            "description": "销售趋势标识(0=稳定 1=上升 2=下降)"
          },
          "totalLive1dCnt": {
            "type": "integer",
            "description": "近1天直播数量"
          },
          "totalLive7dCnt": {
            "type": "integer",
            "description": "近7天直播数量"
          },
          "totalSale1dCnt": {
            "type": "integer",
            "description": "近1天销量"
          },
          "totalSale7dCnt": {
            "type": "integer",
            "description": "近7天销量"
          },
          "totalLive15dCnt": {
            "type": "integer",
            "description": "近15天直播数量"
          },
          "totalLive30dCnt": {
            "type": "integer",
            "description": "近30天直播数量"
          },
          "totalLive60dCnt": {
            "type": "integer",
            "description": "近60天直播数量"
          },
          "totalLive90dCnt": {
            "type": "integer",
            "description": "近90天直播数量"
          },
          "totalSale15dCnt": {
            "type": "integer",
            "description": "近15天销量"
          },
          "totalSale30dCnt": {
            "type": "integer",
            "description": "近30天销量"
          },
          "totalSale60dCnt": {
            "type": "integer",
            "description": "近60天销量"
          },
          "totalSale90dCnt": {
            "type": "integer",
            "description": "近90天销量"
          },
          "totalSaleGmvAmt": {
            "type": "number",
            "description": "总销售额"
          },
          "totalVideo1dCnt": {
            "type": "integer",
            "description": "近1天视频数量"
          },
          "totalVideo7dCnt": {
            "type": "integer",
            "description": "近7天视频数量"
          },
          "totalViews1dCnt": {
            "type": "integer",
            "description": "近1天观看次数"
          },
          "totalViews7dCnt": {
            "type": "integer",
            "description": "近7天观看次数"
          },
          "productImageUrls": {
            "type": "array",
            "items": {},
            "description": "商品图片列表"
          },
          "totalVideo15dCnt": {
            "type": "integer",
            "description": "近15天视频数量"
          },
          "totalVideo30dCnt": {
            "type": "integer",
            "description": "近30天视频数量"
          },
          "totalVideo60dCnt": {
            "type": "integer",
            "description": "近60天视频数量"
          },
          "totalVideo90dCnt": {
            "type": "integer",
            "description": "近90天视频数量"
          },
          "totalViews15dCnt": {
            "type": "integer",
            "description": "近15天观看次数"
          },
          "totalViews30dCnt": {
            "type": "integer",
            "description": "近30天观看次数"
          },
          "totalViews60dCnt": {
            "type": "integer",
            "description": "近60天观看次数"
          },
          "totalViews90dCnt": {
            "type": "integer",
            "description": "近90天观看次数"
          },
          "totalIflLive1dCnt": {
            "type": "integer",
            "description": "近1天达人直播数量"
          },
          "totalIflLive7dCnt": {
            "type": "integer",
            "description": "近7天达人直播数量"
          },
          "totalSaleGmv1dAmt": {
            "type": "number",
            "description": "近1天销售额"
          },
          "totalSaleGmv7dAmt": {
            "type": "number",
            "description": "近7天销售额"
          },
          "totalIflLive15dCnt": {
            "type": "integer",
            "description": "近15天达人直播数量"
          },
          "totalIflLive30dCnt": {
            "type": "integer",
            "description": "近30天达人直播数量"
          },
          "totalIflLive60dCnt": {
            "type": "integer",
            "description": "近60天达人直播数量"
          },
          "totalIflLive90dCnt": {
            "type": "integer",
            "description": "近90天达人直播数量"
          },
          "totalIflVideo1dCnt": {
            "type": "integer",
            "description": "近1天达人视频数量"
          },
          "totalIflVideo7dCnt": {
            "type": "integer",
            "description": "近7天达人视频数量"
          },
          "totalLiveSale1dCnt": {
            "type": "integer",
            "description": "近1天直播销量"
          },
          "totalLiveSale7dCnt": {
            "type": "integer",
            "description": "近7天直播销量"
          },
          "totalSaleGmv15dAmt": {
            "type": "number",
            "description": "近15天销售额"
          },
          "totalSaleGmv30dAmt": {
            "type": "number",
            "description": "近30天销售额"
          },
          "totalSaleGmv60dAmt": {
            "type": "number",
            "description": "近60天销售额"
          },
          "totalSaleGmv90dAmt": {
            "type": "number",
            "description": "近90天销售额"
          },
          "totalIflVideo15dCnt": {
            "type": "integer",
            "description": "近15天达人视频数量"
          },
          "totalIflVideo30dCnt": {
            "type": "integer",
            "description": "近30天达人视频数量"
          },
          "totalIflVideo60dCnt": {
            "type": "integer",
            "description": "近60天达人视频数量"
          },
          "totalIflVideo90dCnt": {
            "type": "integer",
            "description": "近90天达人视频数量"
          },
          "totalLiveSale15dCnt": {
            "type": "integer",
            "description": "近15天直播销量"
          },
          "totalLiveSale30dCnt": {
            "type": "integer",
            "description": "近30天直播销量"
          },
          "totalLiveSale60dCnt": {
            "type": "integer",
            "description": "近60天直播销量"
          },
          "totalLiveSale90dCnt": {
            "type": "integer",
            "description": "近90天直播销量"
          },
          "productCommissionRate": {
            "type": "number",
            "description": "商品佣金比例"
          },
          "totalLiveSaleGmv1dAmt": {
            "type": "integer",
            "description": "近1天直播销售额"
          },
          "totalLiveSaleGmv7dAmt": {
            "type": "integer",
            "description": "近7天直播销售额"
          },
          "totalLiveSaleGmv15dAmt": {
            "type": "integer",
            "description": "近15天直播销售额"
          },
          "totalLiveSaleGmv30dAmt": {
            "type": "integer",
            "description": "近30天直播销售额"
          },
          "totalLiveSaleGmv60dAmt": {
            "type": "integer",
            "description": "近60天直播销售额"
          },
          "totalLiveSaleGmv90dAmt": {
            "type": "integer",
            "description": "近90天直播销售额"
          }
        }
      },
      "description": "商品详情列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
