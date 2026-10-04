# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "uid": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "examples": [
        {
          "value": "1",
          "summary": "第一页"
        }
      ],
      "description": "页码，从1开始，默认为1"
    },
    "chatId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "stepId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "filters": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"isOnePsale\",\"certifiedFactory\"]",
          "summary": "筛选支持一件代发且为认证工厂的商品"
        },
        {
          "value": "[\"totalEpScoreLv2\",\"shipIn24Hours\"]",
          "summary": "筛选综合体验分4.5星以上且支持24小时发货的商品"
        }
      ],
      "maxItems": 1000,
      "description": "过滤条件列表，数组每一项为下列可选值之一，仅支持以下过滤条件: 【履约质量】综合体验分5星(totalEpScoreLv1), 综合体验分4.5星-5.0星(totalEpScoreLv2), 综合体验分4星-4.5星(totalEpScoreLv3), 综合体验分4星以下(totalEpScoreLv4), 认证工厂(certifiedFactory), 24小时揽收率<95%(getRate24HLv1), 24小时揽收率>=95%(getRate24HLv2), 24小时揽收率>=99%(getRate24HLv3), 48小时揽收率<95%(getRate48HLv1), 48小时揽收率>=95%(getRate48HLv2), 48小时揽收率>=99%(getRate48HLv3), 当日发货(shipInToday), 24小时发货(shipIn24Hours), 48小时发货(shipIn48Hours), 7天无理由(noReason7DReturn); 【商品属性】支持一件代发(isOnePsale), 支持包邮代发(isOnePsaleFreePost), 7天上新(new7), 30天上新(new30), 1688严选(1688Selection), 全球严选(isQqyx); 【品质退款】近30天品质退款率5%-10%(qrr10), 近30天品质退款率1%-5%(qrr5), 近30天品质退款率0-1%(qrr1), 近30天品质退款率0%无品质退款(qrr0); 【排除地区】排除日本(JPFL), 排除美国(USFL), 排除韩国(KRFL), 排除越南(VNFL), 排除沙特阿拉伯(SAFL), 排除东欧(RUFL), 排除哈萨克斯坦(KZFL), 排除中国香港(HKFL), 排除中国澳门(MOFL), 排除中国台湾(TWFL)"
    },
    "groupId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "imageId": {
      "type": "string",
      "maxLength": 1000,
      "description": "图片ID(1688图片ID),以图搜图查询结果中也返回，建议当分页page>1查询时带imageId，加快响应速度"
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "书本",
          "summary": "搜索关键词"
        }
      ],
      "maxLength": 1000,
      "description": "关键词，在结果中搜索"
    },
    "imageUrl": {
      "type": "string",
      "examples": [
        {
          "value": "https://cbu01.alicdn.com/img/ibank/O1CN01otREEX1ZFA7hteom8_!!2217114123164-0-cib.jpg",
          "summary": "商品图片URL"
        }
      ],
      "maxLength": 1000,
      "description": "图片URL地址，请确保图片URL有效且可公开访问，仅支持 png、jpg、jpeg 格式"
    },
    "memberId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "pageSize": {
      "type": "integer",
      "maximum": 50,
      "minimum": 1,
      "examples": [
        {
          "value": "20",
          "summary": "20条"
        }
      ],
      "description": "每页返回的商品数量，默认20，最大不超过50"
    },
    "priceMax": {
      "type": "number",
      "minimum": 0,
      "examples": [
        {
          "value": "100",
          "summary": "最高价格100元"
        }
      ],
      "description": "价格筛选最大值（单位：人民币元，如 100 表示 100 元）"
    },
    "priceMin": {
      "type": "number",
      "minimum": 0,
      "examples": [
        {
          "value": "10",
          "summary": "最低价格10元"
        }
      ],
      "description": "价格筛选最小值（单位：人民币元，如 10 表示 10 元）"
    },
    "messageId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "requestId": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "sortField": {
      "type": "string",
      "examples": [
        {
          "value": "price",
          "summary": "按批发价排序"
        },
        {
          "value": "monthSold",
          "summary": "按月销量排序"
        }
      ],
      "maxLength": 1000,
      "description": "排序字段，仅支持：price(批发价)、rePurchaseRate(复购率)、monthSold(月销量)。不传时默认按月销量倒序"
    },
    "sortOrder": {
      "type": "string",
      "examples": [
        {
          "value": "asc",
          "summary": "升序"
        },
        {
          "value": "desc",
          "summary": "降序"
        }
      ],
      "maxLength": 1000,
      "description": "排序方式，仅支持：asc(升序)、desc(降序)。不传时默认 desc"
    },
    "userInput": {
      "type": "string",
      "maxLength": 1000,
      "description": "平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数"
    },
    "imageBase64": {
      "type": "string",
      "maxLength": 1000,
      "description": "图片 Base64 编码字符串（imageUrl为空时使用），仅支持 png、jpg、jpeg 格式，不包含 data:image/jpeg;base64, 前缀"
    },
    "productCollectionId": {
      "type": "string",
      "examples": [
        {
          "value": "262105288",
          "summary": "跨境趋势品-跨境销量飙升商品"
        },
        {
          "value": "262105286",
          "summary": "韩国畅销品-韩国市场上销售情况良好商品"
        },
        {
          "value": "262105253",
          "summary": "日本畅销品-日本市场上销售情况良好商品"
        },
        {
          "value": "262105281",
          "summary": "一件代发时效保障货盘-一件代发且历史履约较好"
        },
        {
          "value": "262105280",
          "summary": "跨境爆品-跨境头部成交商品"
        },
        {
          "value": "262105277",
          "summary": "圣诞节-圣诞节节令商品货盘"
        },
        {
          "value": "262105276",
          "summary": "万圣节-万圣节节令商品货盘"
        },
        {
          "value": "262105274",
          "summary": "夏季节令货盘-夏季属性商品货盘"
        },
        {
          "value": "262105269",
          "summary": "全球严选畅销货盘-跨境属性商品货盘"
        },
        {
          "value": "262185282",
          "summary": "官方验货-官方验样保障货品外观规格与描述一致"
        }
      ],
      "maxLength": 1000,
      "description": "货盘ID，单选，仅支持以下货盘: 262105288(跨境趋势品-跨境销量飙升商品), 262105286(韩国畅销品-韩国市场上销售情况良好商品), 262105253(日本畅销品-日本市场上销售情况良好商品), 262105281(一件代发时效保障货盘-商品标签为一件代发且历史履约较好的货盘), 262105280(跨境爆品-跨境头部成交商品), 262105277(圣诞节-圣诞节节令商品货盘), 262105276(万圣节-万圣节节令商品货盘), 262105274(夏季节令货盘-夏季属性商品货盘), 262105269(全球严选畅销货盘-跨境属性商品货盘), 262185282(官方验货-官方验样保障货品外观规格与描述一致)"
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
      "description": "样式"
    },
    "total": {
      "type": "integer",
      "description": "总商品数量（总行数），上游未返回总数时为 null"
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
    "imageId": {
      "type": "string",
      "description": "上传后的图片ID"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "unit": {
            "type": "string",
            "description": "单位"
          },
          "price": {
            "type": "number",
            "description": "批发价（单位：元，人民币）"
          },
          "title": {
            "type": "string",
            "description": "商品标题"
          },
          "isJxhy": {
            "type": "boolean",
            "description": "是否精选货源"
          },
          "shopId": {
            "type": "string",
            "description": "店铺ID"
          },
          "company": {
            "type": "string",
            "description": "店铺名称"
          },
          "offerId": {
            "type": "string",
            "description": "商品ID"
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
            "description": "数据类型.weeklyData-周数据 monthlyData-月数据"
          },
          "imageUrl": {
            "type": "string",
            "description": "图片URL"
          },
          "isSelect": {
            "type": "boolean",
            "description": "跨境select货盘标识"
          },
          "jxhyPrice": {
            "type": "string",
            "description": "代发精选货源价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回）"
          },
          "levelName": {
            "type": "string",
            "description": "类目层级名称"
          },
          "isOnePsale": {
            "type": "boolean",
            "description": "是否一件代发"
          },
          "modifyDate": {
            "type": "string",
            "description": "商品修改时间（格式 yyyy-MM-dd HH:mm:ss，时区 Asia/Shanghai）"
          },
          "productUrl": {
            "type": "string",
            "description": "商品链接地址"
          },
          "sourceTool": {
            "type": "string",
            "description": "来源工具"
          },
          "sourceType": {
            "type": "string",
            "description": "数据来源类型"
          },
          "tradeScore": {
            "type": "string",
            "description": "商品交易评分"
          },
          "pfJxhyPrice": {
            "type": "string",
            "description": "批发精选货源价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回）"
          },
          "productCode": {
            "type": "string",
            "description": "商品编号（1688 商品 offerId）"
          },
          "consignPrice": {
            "type": "number",
            "description": "一件代发价（单位：元，人民币）.当isOnePsale=true时有效"
          },
          "deliveryTime": {
            "type": "string",
            "description": "发货时间"
          },
          "hasPromotion": {
            "type": "boolean",
            "description": "是否有营销活动"
          },
          "availableDate": {
            "type": "string",
            "description": "商品上架时间（格式 yyyy-MM-dd HH:mm:ss，时区 Asia/Shanghai）"
          },
          "promotionType": {
            "type": "string",
            "description": "营销类型"
          },
          "quantityBegin": {
            "type": "integer",
            "description": "起批量"
          },
          "salesQuantity": {
            "type": "integer",
            "description": "销售件数.按dataType统计周期返回"
          },
          "promotionPrice": {
            "type": "string",
            "description": "营销价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回）"
          },
          "quantityPrices": {
            "type": "string",
            "description": "价格区间（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回）"
          },
          "repurchaseRate": {
            "type": "string",
            "description": "复购率.例如: 13%"
          },
          "isPatentProduct": {
            "type": "boolean",
            "description": "是否为专利商品"
          },
          "offerIdentities": {
            "type": "string",
            "description": "商品标.严选"
          },
          "salesOrderCount": {
            "type": "number",
            "description": "销售笔数.按dataType统计周期返回"
          },
          "tradeMedalLevel": {
            "type": "string",
            "description": "卖家交易勋章等级"
          },
          "sellerIdentities": {
            "type": "string",
            "description": "商家身份标识.超级工厂/实力商家/诚信通会员"
          },
          "estimatedSalesAmount": {
            "type": "number",
            "description": "预估销售额（单位：元，人民币）.按dataType统计周期返回"
          },
          "offerExperienceScore": {
            "type": "string",
            "description": "商品体验分"
          },
          "sendGoodsAddressText": {
            "type": "string",
            "description": "发货地"
          },
          "compositeServiceScore": {
            "type": "string",
            "description": "综合服务体验分"
          },
          "disputeComplaintScore": {
            "type": "string",
            "description": "纠纷投诉处理分"
          },
          "repeatPurchasePercent": {
            "type": "string",
            "description": "重复购买率"
          },
          "logisticsExperienceScore": {
            "type": "string",
            "description": "物流体验分"
          },
          "afterSalesExperienceScore": {
            "type": "string",
            "description": "售后体验分"
          },
          "consultingExperienceScore": {
            "type": "string",
            "description": "咨询体验分"
          }
        }
      },
      "description": "商品列表"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "totalPage": {
      "type": "integer",
      "description": "总页数"
    },
    "sourceType": {
      "type": "string",
      "description": "来源类型"
    },
    "pageItemCount": {
      "type": "integer",
      "description": "本页商品数量"
    }
  }
}
```

</details>
