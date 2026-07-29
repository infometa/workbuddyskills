# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "cycle": {
      "type": "string",
      "pattern": "7|30",
      "examples": [
        {
          "value": "7",
          "summary": "近7天"
        },
        {
          "value": "30",
          "summary": "近30天"
        }
      ],
      "description": "统计周期"
    },
    "keyWord": {
      "type": "string",
      "maxLength": 50,
      "description": "搜索关键词(搜索关键词必须是中文，如果不是请先翻译)"
    },
    "endPrice": {
      "type": "number",
      "description": "批发价（结束）"
    },
    "goodsUrl": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品链接地址"
    },
    "pageSize": {
      "type": "integer",
      "default": 20,
      "maximum": 100,
      "description": "每页返回数量（10-100）"
    },
    "sendTime": {
      "type": "string",
      "examples": [
        {
          "value": "24",
          "summary": "24小时"
        },
        {
          "value": "48",
          "summary": "48小时"
        },
        {
          "value": "72",
          "summary": "72小时"
        }
      ],
      "maxLength": 1000,
      "description": "发货时间（多选），多个使用“,”号隔开，如：24,48"
    },
    "sortType": {
      "type": "string",
      "default": "desc",
      "pattern": "desc|asc",
      "examples": [
        {
          "value": "desc",
          "summary": "降序"
        },
        {
          "value": "asc",
          "summary": "升序"
        }
      ],
      "description": "排序类型"
    },
    "endTpYear": {
      "type": "integer",
      "description": "结束诚信通年限"
    },
    "offerType": {
      "type": "integer",
      "examples": [
        {
          "value": "0",
          "summary": "不限制"
        },
        {
          "value": "2",
          "summary": "新品"
        },
        {
          "value": "3",
          "summary": "1688严选"
        },
        {
          "value": "4",
          "summary": "跨境"
        },
        {
          "value": "5",
          "summary": "支持定制"
        },
        {
          "value": "6",
          "summary": "镇店之宝"
        }
      ],
      "description": "商品标识 0-不限制 2-新品 3-1688严选 4-跨境 5-支持定制 6-镇店之宝"
    },
    "pageIndex": {
      "type": "integer",
      "default": 1,
      "description": "页码（从1开始）"
    },
    "shiLiType": {
      "type": "string",
      "examples": [
        {
          "value": "superFactory",
          "summary": "超级工厂"
        },
        {
          "value": "Power",
          "summary": "实力商家"
        },
        {
          "value": "TrustPass",
          "summary": "仅诚信通会员"
        }
      ],
      "maxLength": 1000,
      "description": "卖家会员类型（多选），多个使用“,”号隔开，如：superFactory,Power"
    },
    "sortField": {
      "type": "string",
      "default": "orderCount30d",
      "pattern": "orderCount7d|saleCount7d|saleVolume7d|orderCount30d|saleCount30d|saleVolume30d|offerCreateTime|price|consignPrice",
      "examples": [
        {
          "value": "orderCount7d",
          "summary": "近7天销售笔数"
        },
        {
          "value": "saleCount7d",
          "summary": "近7天销售件数"
        },
        {
          "value": "saleVolume7d",
          "summary": "近7天预估销售额"
        },
        {
          "value": "orderCount30d",
          "summary": "近30天销售笔数"
        },
        {
          "value": "saleCount30d",
          "summary": "近30天销售件数"
        },
        {
          "value": "saleVolume30d",
          "summary": "近30天预估销售额"
        },
        {
          "value": "offerCreateTime",
          "summary": "上架时间"
        },
        {
          "value": "price",
          "summary": "批发价"
        },
        {
          "value": "consignPrice",
          "summary": "代发价"
        }
      ],
      "description": "排序字段"
    },
    "beginPrice": {
      "type": "number",
      "description": "批发价（起始）"
    },
    "productIds": {
      "type": "string",
      "maxLength": 1000,
      "description": "商品ID 多个顿号隔开，最多20个"
    },
    "searchType": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "模糊匹配"
        },
        {
          "value": "3",
          "summary": "精准匹配"
        }
      ],
      "description": "商品关键词搜索类型"
    },
    "beginTpYear": {
      "type": "integer",
      "description": "开始诚信通年限"
    },
    "companyType": {
      "type": "integer",
      "examples": [
        {
          "value": "0",
          "summary": "不限"
        },
        {
          "value": "1",
          "summary": "店铺"
        },
        {
          "value": "2",
          "summary": "工厂"
        }
      ],
      "description": "公司类型 0-不限 1-店铺 2-工厂"
    },
    "proxyRights": {
      "type": "string",
      "examples": [
        {
          "value": "4360897",
          "summary": "一件代发包邮"
        },
        {
          "value": "449154",
          "summary": "先采后付"
        }
      ],
      "maxLength": 1000,
      "description": "代发权益（多选），多个使用“,”号隔开，如：4360897,449154"
    },
    "shopService": {
      "type": "string",
      "examples": [
        {
          "value": "4057409",
          "summary": "安心购"
        },
        {
          "value": "888777",
          "summary": "深度认证报告"
        }
      ],
      "maxLength": 1000,
      "description": "卖家服务（多选），多个使用“,”号隔开，如：4057409,888777"
    },
    "endSaleCount": {
      "type": "integer",
      "description": "销售件数（结束）"
    },
    "endOrderCount": {
      "type": "integer",
      "description": "销售笔数（结束）"
    },
    "endSaleVolume": {
      "type": "number",
      "description": "销售额（结束）"
    },
    "beginSaleCount": {
      "type": "integer",
      "description": "销售件数（起始）"
    },
    "beginOrderCount": {
      "type": "integer",
      "description": "销售笔数（起始）"
    },
    "beginSaleVolume": {
      "type": "number",
      "description": "销售额（起始）"
    },
    "endConsignPrice": {
      "type": "number",
      "description": "代发价（结束）"
    },
    "buyerProtections": {
      "type": "string",
      "examples": [
        {
          "value": "商品包邮",
          "summary": "商品包邮"
        },
        {
          "value": "7天包退货",
          "summary": "7天包退货"
        },
        {
          "value": "支持运费险",
          "summary": "支持运费险"
        }
      ],
      "maxLength": 1000,
      "description": "权益保障，多个用“,”隔开。如："
    },
    "endStartQuantity": {
      "type": "integer",
      "description": "起购数量（结束）"
    },
    "beginConsignPrice": {
      "type": "number",
      "description": "代发价（起始）"
    },
    "faceToFaceSupport": {
      "type": "string",
      "examples": [
        {
          "value": "441218",
          "summary": "淘宝"
        },
        {
          "value": "386434",
          "summary": "抖音"
        },
        {
          "value": "422914",
          "summary": "拼多多"
        },
        {
          "value": "422978",
          "summary": "小红书"
        },
        {
          "value": "386370",
          "summary": "快手"
        }
      ],
      "maxLength": 1000,
      "description": "面单支持（多选），多个使用“,”号隔开，如：441218,386434"
    },
    "beginStartQuantity": {
      "type": "integer",
      "description": "起购数量（起始）"
    },
    "endOfferCreateTime": {
      "type": "string",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$",
      "description": "上架时间（结束）例如：2025-06-11"
    },
    "beginOfferCreateTime": {
      "type": "string",
      "pattern": "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$",
      "description": "上架时间（起始）例如：2025-06-11"
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
            "description": "商品编号"
          },
          "unit": {
            "type": "string",
            "description": "单位"
          },
          "price": {
            "type": "number",
            "description": "批发价"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "shopId": {
            "type": "string",
            "description": "店铺id"
          },
          "asinUrl": {
            "type": "string",
            "description": "商品链接地址"
          },
          "company": {
            "type": "string",
            "description": "店铺名称"
          },
          "offerId": {
            "type": "string",
            "description": "商品id"
          },
          "shopUrl": {
            "type": "string",
            "description": "店铺链接地址"
          },
          "currency": {
            "type": "string",
            "description": "币种"
          },
          "dataType": {
            "type": "string",
            "description": "数据类型: weeklyData: 周数据; monthlyData: 月数据"
          },
          "imageUrl": {
            "type": "string",
            "description": "图片地址"
          },
          "levelName": {
            "type": "string",
            "description": "类目层级名称"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "1688"
          },
          "consignPrice": {
            "type": "number",
            "description": "代发价"
          },
          "deliveryTime": {
            "type": "string",
            "description": "发货时间"
          },
          "availableDate": {
            "type": "string",
            "format": "date",
            "description": "商品上架时间，格式为 yyyy-MM-dd HH:mm:ss"
          },
          "quantityBegin": {
            "type": "integer",
            "description": "起批量"
          },
          "salesQuantity": {
            "type": "integer",
            "description": "销售件数（按统计周期返回对应的值）"
          },
          "quantityPrices": {
            "type": "string",
            "description": "价格区间"
          },
          "salesOrderCount": {
            "type": "integer",
            "description": "销售笔数（按统计周期返回对应的值）"
          },
          "estimatedSalesAmount": {
            "type": "integer",
            "description": "预估销售额（按统计周期返回对应的值）"
          }
        }
      },
      "description": "商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
