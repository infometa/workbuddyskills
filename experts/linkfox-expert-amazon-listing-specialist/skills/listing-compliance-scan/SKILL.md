---
name: listing-compliance-scan
description: 使用随包本地规则库扫描 Amazon Listing 的受限内容、绝对化宣称、无证据声明、用户禁用词和竞品品牌冲突。不调用商标、版权、专利或政策外部服务。
---

# Listing Compliance Scan

## 本地检查

1. 运行 `scripts/restricted_content_scan.py` 检查受限内容。
2. 运行 `scripts/brand_conflict_scan.py` 检查竞品品牌词。
3. 使用 `_listing-private-assets/data/` 中的中英文绝对化宣称规则库。
4. 合并用户提供的禁用词、品牌白名单和品类限制。
5. 输出 `pass`、`review`、`fail` 及命中字段、词项、规则来源和修复建议。

## 边界

- 这是文本规则扫描，不是法律意见，也不等于商标、版权、专利或监管数据库检索。
- 图片风险、TRO、专利有效性和国家法规需由宿主或专业人员另行确认。
- 没有可靠规则时输出 `review`，不得编造“已通过官方检测”。
