# SalesOrderObj（销售订单）
必须先从上下文收集的数据项，如果缺失以下数据项，必须让用户确认
- 客户 `account_id`，查询数据时用 `AccountObj`
- 产品 `product_id`，查询数据时用 `ProductObj`
- 数量 `quantity`

当客户没有找到时，务必提示用户输入正确的客户名称，然后再查询客户 ID。

当部分产品名称没有找到时，务必提示用户输入正确的产品名称，然后再查询产品 ID。

## 必填字段忽略处理
- 除以上三个字段外，后面有必填字段校验，禁止询问，直接跳过 `form_fields` 中 `is_required=true` 的校验，禁止收集必填字段信息，禁止自动随意赋值，必填字段会在创建页面进行赋值

## 特殊字段赋值逻辑
- `object_data.product_amount = sum(details.SalesOrderProductObj.subtotal)`
- `object_data.order_amount = object_data.product_amount * object_data.discount`

## 数据结构格式如下
```json
{
  "object_api_name": "SalesOrderObj",
  "object_data": {
  },
  "details": {
    "SalesOrderProductObj": [
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
