---
description: 从零生成全新的 Excel 表格，可附带 pdf/docx 作为参考素材
argument-hint: "描述你想生成的表格，例如：做一份 6 月销售统计表"
---

<user_input>
$ARGUMENTS
</user_input>

---

**必须**调用 `tencent-docs-sheet-generation` skill，按其 Step 1–6 完成从零生成；**禁止**绕过该 skill 直接委派 sheet-agent 子代理。
