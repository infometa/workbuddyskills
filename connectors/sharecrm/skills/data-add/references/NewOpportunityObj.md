# NewOpportunityObj（商机）

## 报价数据处理补充

在商机新建流程中，如果上游已构造并回填报价草稿或报价明细数据，必须保证 `details` 节点下的 `product_id` 不丢失。

## 数据结构格式如下
```json
{
  "object_api_name": "NewOpportunityObj",
  "object_data": {
  },
  "details": {
    "NewOpportunityLinesObj": [
      {
      }
    ],
    "XXXObj": [
      {
      }
    ]
  }
}
```

以上处理完，继续走主流程下的逻辑。
