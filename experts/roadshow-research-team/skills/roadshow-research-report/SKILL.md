---
name: roadshow-research-report
description: "生成A股上市公司资本市场路演时间线研究报告（.docx）。当用户要求对某A股公司生成路演、投资者交流会、业绩说明会的时间线研究Word报告时使用。触发词：路演研究、路演时间线、投资者关系活动、业绩说明会研究、资本市场时间线报告。"
---

# 路演研究报告生成

生成一份面向A股上市公司的近三年资本市场路演时间线研究报告（Word），包含以下标准章节：

1. 公司概况
2. 三大年度业绩说明会
3. 2024年时间线
4. 2025年时间线
5. 2026年时间线
6. 主题演变
7. 统计分析
8. 总结与展望

## 工作流程

### 一、研究阶段

本技能提供报告结构模板（详见 [report-structure.md](references/report-structure.md)）和 docx 验证脚本（`scripts/validate_docx.py`），供 report-composer 成员在报告生成阶段使用。

实际的路演数据采集由团队中的 `roadshow-curator` 成员负责，数据来源包括深交所/上交所公告、巨潮资讯网、全景路演等公开渠道。

### 二、报告生成阶段

使用 `docx-js` 库生成 Word 报告。详见 [docx-js-checklist.md](references/docx-js-checklist.md) 的编码防错检查清单。

### 三、验证阶段

生成后必须运行 `scripts/validate_docx.py` 脚本验证文档结构完整性。

## 报告结构

标准8章结构详见 [report-structure.md](references/report-structure.md)。

## 编码注意事项

**以下两条是本次踩坑总结，必须严格遵守：**

1. **Bullet列表文本必须是纯字符串** — 使用 `.map((text) => ...)` 时，数组元素不能是 `["sometext"]`，必须是 `"sometext"`。否则 `TextRun({ text: text })` 收到的是数组，内容渲染为空。

2. **所有表格必须列数一致** — 包括表头和所有数据行。如果某行缺少某列，用 `"—"` 填充，不能用 `[...]` 跳过。

3. **中文文本使用 Unicode 转义** — JS 源码中的中文用 `\uXXXX` 编码，避免编码问题。
