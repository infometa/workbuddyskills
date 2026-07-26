# Chart Data Limits — Circular Chart Experience

> Self-Refinement 经验沉淀。AI 在 S3 内容填充前必须读取。

## Experience 001: Donut/Pie Max 6 Segments

**Date**: 2026-05-02
**Problem**: donut 和 pie 版式超过6段时，标签区宽度不足，文字严重溢出。
**Root Cause**: 每段对应一条图例标签，7+段时标签列高度超出内容区。
**Fix**: donut/pie 最多 6 段。超过时自动合并为 top-N + "其他"。
**Rule**: 在 S3 门禁中检查 `len(segments) <= 6`，否则 FAIL。

```python
# ✅ 超过6段时自动合并
if len(segments) > 6:
    top5 = sorted(segments, key=lambda x: x[0], reverse=True)[:5]
    rest_pct = 1.0 - sum(s[0] for s in top5)
    segments = top5 + [(rest_pct, MED_GRAY, '其他')]
```

## Experience 002: grouped_bar Max 6 Categories × 3 Series

**Date**: 2026-05-02
**Problem**: 分组柱状图超过6个类别时，每组柱宽度过窄，文字标签重叠。
**Root Cause**: 动态宽度计算结果导致字体降级不够。
**Fix**: 最多 6 categories，最多 3 series。超出时建议拆分为多张幻灯片。
**Rule**: S3 门禁检查 `len(categories) <= 6 and len(series) <= 3`。
