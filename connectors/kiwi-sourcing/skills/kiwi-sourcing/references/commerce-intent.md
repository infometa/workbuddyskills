# CommerceIntent 构造

只传完成本次采购所需的信息。商品 `query` 使用短商品词；型号、接口、颜色、地区、预算和交期
放入 `constraints` 或 `preferences`。`quantity` 必须是 `{ "value": number, "unit": string }`。

```json
{
  "intent_type": "purchase",
  "items": [
    {
      "query": "USB-C 扩展坞",
      "quantity": { "value": 200, "unit": "个" }
    }
  ],
  "constraints": {
    "currency": "CNY",
    "deadline": "<RFC3339>"
  },
  "preferences": {
    "delivery_region": "上海",
    "required_features": ["双 HDMI", "100W PD"]
  },
  "context_projection": {
    "disclosure_boundary": "commerce_required",
    "projected_fields": ["items", "constraints", "preferences"]
  }
}
```

不要加入完整聊天历史、通讯录、无关邮箱、其他 WorkBuddy 文件内容或长期记忆。地址只有在报价
确实需要送达区域时才传最小必要粒度；在 handoff 前不要主动披露详细收货地址。
