# 任务 D：对比差异分析

`analysis_type: "comparison"`

对比两张截图，逐项列出差异，分类为 major/minor/cosmetic。

## Schema

```json
{
  "analysis_type": "comparison",
  "overall_similarity": "high | medium | low",
  "changes": [
    {
      "type": "added | removed | modified | moved | resized | recolored | text_changed | layout_changed",
      "what": "变更对象",
      "where": "页面位置",
      "before": "变更前",
      "after": "变更后",
      "severity": "major | minor | cosmetic",
      "category": "layout | color | typography | spacing | content | interaction | new_feature | removed_feature"
    }
  ],
  "summary": "总体变更概要",
  "change_stats": {"total": 0, "major": 0, "minor": 0, "cosmetic": 0}
}
```

**严重度**：`major`（影响功能/架构） > `minor`（影响视觉） > `cosmetic`（细微差异）。

## 分析方法论

1. **整体对齐**：同页面不同版本 vs 不同页面？结构一致？
2. **逐区域对比**：存在/位置/大小/内容/样式 逐项检查
3. **变更分类**：type + severity(major/minor/cosmetic) + category
4. **总结**：主要变更、整体影响、保真度评估（如适用）
