# Seller-report funnel diagnosis

只有用户或宿主提供 Seller Central 报表或等价数据时使用。本 Skill 不授权店铺、不拉取报表，只消费已经投影好的目标 ASIN、周期和指标证据。

## Required normalization

```json
{
  "asin": "B0...",
  "marketplace": "US",
  "period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "comparison_period": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "traffic_source": "organic|ads|combined|unknown",
  "metrics": [],
  "source_path": "/abs/report.tsv",
  "confidence": "verified|partial"
}
```

缺少 comparison period、类目/历史基线或明确阈值时，不写“低于正常”；只写观察值、变化方向和数据缺口。

## Diagnosis mapping

| 证据模式 | 可验证方向 | Field actions | Operational actions |
|---|---|---|---|
| 展现/查询份额弱且相关查询缺失 | 关键词、索引、属性承接 | Title、Highlights、ST、结构化属性 | 类目节点、索引检查 |
| 展现正常但 CTR 相对基线下降 | 搜索首屏表达 | Title、Highlights | 主图、价格、评分、促销 |
| CTR 稳定但 CVR 相对基线下降 | 疑虑、规格、信任和场景 | Bullets、Description、A+ 文案建议 | 价格、配送、库存、评价结构 |
| 广告点击高但查询不匹配 | 搜索意图错配 | 仅清理不相关 ST/正文词 | 否词、匹配方式、投放结构 |
| 退货/差评集中在兼容或尺寸 | 预期管理、适配和边界 | Highlights、Bullets、兼容说明 | 产品/包装/质检改进 |
| 特定查询转化持续更好 | 高价值意图承接不足 | 自然前置到 Title/前两点 | 广告预算与落地页策略 |

不得把相关性写成因果保证。每条动作包含 `metric_evidence → diagnosis → target_field → expected_direction → confidence`。

## Report workflow

1. 已有报告：直接解析目标 ASIN；不重复授权和拉取。
2. 无报告时：明确说明缺少漏斗证据，并请用户或宿主提供对应周期的数据。
3. 不尝试授权店铺、调用平台报告接口或自动替换数据源。
4. 报表通常需要轮询，耗时可能明显高于 Listing 本地审计；完成后仅增量更新漏斗视角。
