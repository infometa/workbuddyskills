# Audit to rewrite handoff

`listing-audit` 与 `listing-core mode=rewrite` 共用以下契约：

```json
{
  "kind": "listingAuditHandoff",
  "schema_version": 1,
  "target": {"asin": "B0...", "marketplace": "US"},
  "source_listing_path": "/abs/listing.json",
  "evidence_paths": {
    "product_facts": "/abs/product-facts.md",
    "product_detail": "/abs/product-detail.json",
    "keywords": "/abs/keywords.json",
    "buyer_questions": "/abs/buyer-questions.json",
    "insight": "/abs/insight.md",
    "reviews": "/abs/reviews.json",
    "compliance": "/abs/compliance.json",
    "seller_reports": "/abs/performance-evidence.json"
  },
  "score_panel_path": "/abs/score-result.json",
  "field_actions": [
    {
      "field": "title|item_highlights|bullets|description|search_terms|structured_attributes",
      "priority": "high|medium|low",
      "problem": "...",
      "evidence": [],
      "objective": "...",
      "constraints": [],
      "expected_direction": "...",
      "confidence": "verified|partial"
    }
  ],
  "operational_actions": [],
  "locked_fields": [],
  "data_freshness": {"captured_at": "ISO-8601", "cache_window_hours": 24}
}
```

## Consumer rules

- Core 校验 `kind/schema_version`、ASIN、marketplace 和路径存在性；不匹配的证据不得复用。
- 24 小时窗口内的同参 Product Detail、SIF、Reviews List 和合规结果优先复用；只补缺失或过期证据。
- 同轮 Audit 同时产出 `keywords`、`buyer_questions`、`insight` 且三者存在时，Core 直接复用为 S3；任一缺失、过期或目标不匹配则执行原 S3，不允许降级为空产物。
- `field_actions` 决定局部重写范围；`locked_fields` 和未受影响字段逐字保持不变。
- `operational_actions` 不传给 writer，只进入交付建议。
- 卖家报表只提供改写方向，不成为商品材质、规格、认证或效果声明的事实源。
- 改写完成后必跑 Core 基础 QA。完整 before/after 分数仅在用户要求评分/报告时调用 scorer，不重跑完整 Audit。
