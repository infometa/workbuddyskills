# 版式数据格式参考（deck_spec.json → data 字段）

> ⚠️ **铁律：所有复合数据字段一律使用数组/元组格式，绝不传字典/对象。**
>
> 引擎内部通过 Python 解包（`for i, (a, b, c) in enumerate(items)`）获取值。
> 如果传入 `{"key": "value"}` 格式，Python 解包字典得到的是 **key 名称**（如 "value"、"label"），而不是实际数据。

---

## 通用规则

1. **所有复合数据字段用数组格式** `[[a, b, c], [d, e, f]]`，永远不用 `[{key: val}]`
2. **label/编号字段**：放在圆圈里，必须 ≤3 字符（推荐 "01"-"05" 数字编号）
3. **points/detail_items**：单个字符串，用 `\n` 换行拼接；不用字符串数组
4. **col_widths**：永远不传，让引擎自动分配（传数字会被当作 EMU 单位导致列宽几乎为零）
5. **需要 RGBColor 的版式**（grouped_bar / horizontal_bar）：在 JSON 中无法使用，改用替代版式
6. **desc 字段**：控制在 50 字符以内（gate_check_s3 会拦截）
7. **source 字段**：结构化数组 `[{"label": "来源名", "url": ""}]`，不是纯字符串

---

## 结构类版式

### cover
```json
"data": {
  "title": "演示标题",
  "subtitle": "副标题",
  "author": "作者",
  "date": "2026-07"
}
```
全部是简单字符串，无复合字段。`cover_image` 可选：`null`（默认深色封面）、`"auto"`（AI生成）、文件路径。

### section_divider
```json
"data": {
  "section_label": "第一部分",
  "title": "章节标题",
  "subtitle": "可选副标题"
}
```

### toc
```json
"data": {
  "title": "目录",
  "items": [
    ["01", "市场概览", "全球智能体市场规模与增长趋势"],
    ["02", "竞争格局", "头部厂商定位与差异化策略"],
    ["03", "投资建议", "进入时机与路径选择"]
  ]
}
```
- `items`：`[编号, 标题, 描述]` 三元组数组

### closing
```json
"data": {
  "title": "谢谢",
  "message": "如有疑问请联系团队",
  "source_text": ""
}
```

### appendix_title
```json
"data": {
  "title": "附录",
  "subtitle": "补充数据与详细测算"
}
```

---

## 数据展示类版式

### big_number
```json
"data": {
  "number": "449",
  "unit": "亿元 [E]",
  "description": "2026年全球智能体平台市场预计规模",
  "detail_items": "• 年复合增长率 107%\n• 企业级占比 68%\n• 亚太增速最快",
  "bottom_bar": ["数据来源", "IDC & Gartner 综合估算"]
}
```
- `detail_items`：**单个字符串**，用 `\n` 换行，不是数组
- `bottom_bar`：`[标签, 文字]` 二元组或 null

### two_stat
```json
"data": {
  "stats": [
    ["449亿元", "2026年预计市场规模", true],
    ["107%", "年复合增长率(CAGR)", false]
  ],
  "detail_items": "• 企业级智能体占比 68%\n• 垂直行业应用增速最快"
}
```
- `stats`：`[数字, 标签, 是否深色底]` 三元组数组
  - 第三个布尔值：`true` = 深色底白字（NAVY），`false` = 浅色底深字
- `detail_items`：单个字符串，`\n` 换行

### three_stat
```json
"data": {
  "stats": [
    ["40%", "企业已评估", true],
    ["23%", "规模化部署", false],
    ["107%", "年复合增长率", true]
  ],
  "detail_items": "• 金融与零售业领跑\n• 中小企业采纳率仍低"
}
```
- 同 `two_stat` 格式，3 个三元组

### scorecard
```json
"data": {
  "items": [
    ["自然语言理解", "9.2/10", 0.92],
    ["工具调用能力", "8.5/10", 0.85],
    ["多轮对话管理", "7.8/10", 0.78],
    ["安全与合规", "6.5/10", 0.65]
  ]
}
```
- `items`：`[名称, 评分字符串, 百分比浮点数(0-1)]` 三元组数组

### data_table
```json
"data": {
  "headers": ["厂商", "定位", "核心能力", "估值", "差异化"],
  "rows": [
    ["Microsoft Copilot", "通用办公助手", "Office生态集成", "$3T+", "渠道垄断"],
    ["OpenAI GPTs", "开发者平台", "模型能力领先", "$150B", "技术壁垒"],
    ["Salesforce Einstein", "企业CRM", "销售场景深耕", "$200B", "数据飞轮"]
  ],
  "bottom_bar": ["关键发现", "头部集中度高，CR3 超过 60%"]
}
```
- `headers`：字符串数组
- `rows`：字符串数组的数组（每行列数必须等于 headers 长度）
- **绝不传 `col_widths`**，引擎自动等宽分配
- `bottom_bar`：`[标签, 文字]` 或省略

### table_insight
```json
"data": {
  "headers": ["维度", "现状", "趋势"],
  "rows": [
    ["市场规模", "449亿元", "年增107%"],
    ["渗透率", "23%", "快速上升"]
  ],
  "insights": [
    "市场处于爆发前夜，先发者将获得数据飞轮优势",
    "垂直场景比通用平台更容易建立壁垒",
    "企业采购决策权正在从IT部门向业务部门转移"
  ],
  "insight_title": "启示：",
  "bottom_bar": ["结论", "窗口期约18-24个月"]
}
```
- `insights`：字符串数组（右侧面板的要点列表）
- 表格相关同 `data_table` 规则

### rag_status
```json
"data": {
  "headers": ["能力模块", "状态", "得分", "备注"],
  "rows": [
    ["NLU引擎", "RGBColor(0x27,0xAE,0x60)", "92%", "已达到产线标准"],
    ["工具编排", "RGBColor(0xF3,0x9C,0x12)", "75%", "需要改进错误恢复"]
  ]
}
```
- ⚠️ 此版式的 `status_color` 需要 RGBColor 对象，**JSON 中建议避免使用此版式**，改用 `scorecard` 或 `data_table`

---

## 框架类版式

### matrix_2x2
```json
"data": {
  "quadrants": [
    ["高价值高可行", "BG_GRAY_color", "客服自动化、销售助手——ROI明确，技术成熟"],
    ["高价值低可行", "BG_GRAY_color", "复杂决策支持——价值大但实施难度高"],
    ["低价值高可行", "BG_GRAY_color", "内部知识检索——易做但差异化弱"],
    ["低价值低可行", "BG_GRAY_color", "通用闲聊机器人——价值低且竞争激烈"]
  ],
  "axis_labels": ["可行性 →", "↑ 商业价值"],
  "bottom_bar": ["建议", "优先投入左上象限场景"]
}
```
- `quadrants`：4 个 `[标签, 背景色, 描述]` 三元组
  - ⚠️ 背景色在 JSON 中无法用 RGBColor，**建议省略此字段或传 null，让引擎用默认色**
  - 实际上引擎代码会直接使用传入的颜色值，如果你无法传真实 RGBColor，请使用 `data_table` 或 `side_by_side` 替代
- `axis_labels`：`[X轴标签, Y轴标签]` 二元组

### pyramid (阶梯演进图)
```json
"data": {
  "levels": [
    ["单点工具", "解决单一任务的AI助手", "1"],
    ["流程自动化", "跨系统编排工作流", "2"],
    ["自主决策", "具备推理和自主行动能力", "3"]
  ],
  "detail_rows": [
    ["代表产品", ["ChatGPT插件", "Zapier AI", "Devin/Manus"]],
    ["核心壁垒", ["模型能力", "集成生态", "数据飞轮"]]
  ]
}
```
- `levels`：`[标签, 描述, 图标]` 三元组数组
  - 图标可以是：数字字符串（"1"）、Unicode 符号、或 PNG 文件路径
- `detail_rows`：可选，`[行标签, [各列文字]]` 数组

### process_chevron
```json
"data": {
  "steps": [
    ["01", "选准场景", "客服/销售/财务\n回收期<6个月"],
    ["02", "垂直深耕", "金融/零售/制造\n构建行业壁垒"],
    ["03", "治理壁垒", "审计/合规/身份\n成为采购必选项"],
    ["04", "生态锁定", "API/数据/工作流\n进化为基础设施"]
  ],
  "bottom_bar": ["战略节奏", "每阶段约6-12个月"]
}
```
- `steps`：`[label, stitle, desc]` 三元组数组
  - **label**：放在圆圈里，**必须 ≤3 字符**（推荐 "01"-"05" 数字编号）
  - **stitle**：步骤名称，放在主体区域
  - **desc**：描述，≤50 字符
- 支持 2-5 步，超过 5 步必须合并或拆页

### temple (屋顶-支柱-基石)
```json
"data": {
  "roof_text": "智能体平台竞争力",
  "pillar_names": ["模型能力", "工具生态", "数据飞轮", "安全合规"],
  "foundation_text": "底层基础设施：算力 + 数据湖 + MLOps"
}
```
- `pillar_names`：字符串数组
- ⚠️ `pillar_colors` 需要 RGBColor，省略即可（引擎用默认色）

### value_chain
```json
"data": {
  "stages": [
    ["基础模型", "预训练大模型能力", "NAVY_color"],
    ["开发平台", "Agent编排与调试工具", "NAVY_color"],
    ["行业应用", "垂直场景解决方案", "NAVY_color"],
    ["终端交付", "对话/API/嵌入式", "NAVY_color"]
  ],
  "bottom_bar": ["价值分布", "中游开发平台利润率最高"]
}
```
- `stages`：`[标题, 描述, 强调色]` 三元组
  - ⚠️ 颜色需要 RGBColor 对象，JSON 中无法直接传递。**建议：省略颜色字段不传（需要修改引擎支持），或改用 `process_chevron` 替代**

---

## 比较类版式

### side_by_side
```json
"data": {
  "options": [
    ["自建平台", "• 完全自主可控\n• 数据不出域\n• 长期成本可控\n• 技术积累沉淀"],
    ["采购SaaS", "• 快速上线(2-4周)\n• 无需自建团队\n• 持续获得更新\n• 风险较低"]
  ]
}
```
- `options`：**2 个** `[选项标题, 内容字符串]` 二元组数组
  - 内容是**单个字符串**，用 `\n` 拼接各要点
  - ⚠️ 不是 `[{heading, points}]`

### before_after
```json
"data": {
  "before_title": "传统模式",
  "before_points": ["人工处理客服工单，平均响应 4 小时", "重复问题占比 70%，浪费人力"],
  "after_title": "智能体模式",
  "after_points": ["自动分类+即时响应，平均 30 秒", "70% 重复问题自动解决，释放人力"],
  "bottom_bar": ["效果", "人力成本降低 60%，客户满意度提升 25%"]
}
```
- 简单模式：`before_points` / `after_points` 是字符串数组
- 高级模式（结构化数据行）：参见引擎 docstring

### pros_cons
```json
"data": {
  "pros_title": "✓ 优势",
  "pros": ["快速部署能力\n2-4周即可上线", "生态集成丰富\n200+预集成工具"],
  "cons_title": "✗ 风险",
  "cons": ["数据安全隐患\n模型调用涉及外传", "供应商锁定\n迁移成本高"],
  "conclusion": ["综合建议", "推荐混合方案：核心数据自建+非敏感场景SaaS"]
}
```
- `pros` / `cons`：字符串数组（每条可以包含 `\n` 换行）
- `conclusion`：`[标签, 文字]` 二元组或 null

### swot
```json
"data": {
  "quadrants": [
    ["Strengths", "NAVY_color", "BG_color", ["模型能力行业领先", "数据积累深厚", "品牌认知度高"]],
    ["Weaknesses", "GRAY_color", "BG_color", ["垂直场景经验不足", "企业服务团队薄弱"]],
    ["Opportunities", "NAVY_color", "BG_color", ["市场爆发期窗口", "政策利好AI产业"]],
    ["Threats", "GRAY_color", "BG_color", ["巨头快速跟进", "开源模型挤压利润"]]
  ]
}
```
- `quadrants`：4 个 `[标签, 强调色, 背景色, 要点列表]` 四元组
  - ⚠️ 颜色需要 RGBColor，**建议改用 `matrix_2x2` 或 `side_by_side` 替代**

---

## 叙事类版式

### executive_summary
```json
"data": {
  "headline": "智能体平台市场将在未来3年经历整合，先发者需在18个月内建立数据壁垒",
  "items": [
    ["01", "市场爆发", "全球规模 449 亿元 [E]，CAGR 107%，企业级占主导"],
    ["02", "格局未定", "CR3 约 60%，但垂直领域仍有窗口"],
    ["03", "紧迫时间窗", "18-24 个月内数据飞轮将形成不可逆壁垒"]
  ]
}
```
- `items`：`[编号, 标题, 描述]` 三元组数组
  - **编号**：字符串，放在圆圈里（如 "01"）

### four_column
```json
"data": {
  "items": [
    ["01", "市场规模", "全球449亿元\nCAGR 107%"],
    ["02", "竞争格局", "CR3约60%\n垂直赛道分散"],
    ["03", "技术成熟度", "NLU 9.2/10\n工具调用 8.5/10"],
    ["04", "进入建议", "垂直场景切入\n18个月窗口期"]
  ]
}
```
- `items`：`[编号, 列标题, 描述]` 三元组数组
  - 描述可以是字符串（`\n` 换行）或字符串数组

### key_takeaway
```json
"data": {
  "left_text": ["分析要点1：市场集中度正在快速提升...", "分析要点2：垂直场景是差异化关键..."],
  "takeaways": ["窗口期仅剩18-24个月", "数据飞轮是核心壁垒", "应优先选择垂直场景切入"]
}
```
- `left_text`：字符串数组
- `takeaways`：字符串数组

### two_column_text
```json
"data": {
  "columns": [
    ["A", "短期策略(0-6月)", ["选定2-3个垂直场景快速验证", "建立种子客户数据飞轮", "形成MVP产品"]],
    ["B", "中期策略(6-18月)", ["扩展场景覆盖至5-8个行业", "构建开发者生态", "完成A轮融资"]]
  ]
}
```
- `columns`：2 个 `[字母, 列标题, 要点列表]` 三元组

### quote
```json
"data": {
  "quote_text": "AI Agent 不是工具的升级，而是工作方式的重新定义。",
  "attribution": "—— Satya Nadella, CEO of Microsoft, 2025"
}
```

---

## 时间线与步骤类版式

### timeline
```json
"data": {
  "milestones": [
    ["2024 Q1", "概念验证期\n市场教育阶段"],
    ["2024 Q3", "产品爆发期\nGPTs/Copilot发布"],
    ["2025 H1", "企业试点期\n23%规模化部署"],
    ["2026 H2", "市场成熟期\n预计CR3>70%"]
  ],
  "bottom_bar": ["趋势判断", "当前处于企业试点→市场成熟的过渡阶段"]
}
```
- `milestones`：`[标签, 描述]` 二元组数组

### vertical_steps
```json
"data": {
  "steps": [
    ["01", "场景筛选", "从20+候选场景中选出ROI最高的3个垂直场景"],
    ["02", "MVP验证", "4周内完成最小可行产品并获得种子客户反馈"],
    ["03", "数据飞轮", "基于真实使用数据持续优化，建立竞争壁垒"],
    ["04", "规模化扩展", "复制成功模式到相邻场景，扩大市场份额"]
  ],
  "bottom_bar": ["执行节奏", "每阶段3-6个月"]
}
```
- `steps`：`[编号, 步骤标题, 描述]` 三元组数组

---

## 团队与案例类版式

### meet_the_team
```json
"data": {
  "members": [
    ["张三", "CTO", "10年AI经验\n前Google Brain研究员\n3个AI产品从0到1"],
    ["李四", "VP Product", "8年产品经验\n前字节跳动产品总监\n DAU过亿产品负责人"]
  ]
}
```
- `members`：`[姓名, 角色, 简介]` 三元组数组
  - 简介可以是 `\n` 拼接的字符串

### case_study
```json
"data": {
  "sections": [
    ["S", "场景", "某银行信用卡中心\n日均处理10万+咨询工单"],
    ["A", "方案", "部署智能体自动分类+自动应答\n覆盖70%重复问题"],
    ["R", "结果", "人力成本降低60%\n客户满意度提升25%\n响应时间从4h→30s"]
  ],
  "result_box": ["ROI", "6个月回本，年化节省 2400 万元"]
}
```
- `sections`：`[字母, 标题, 描述]` 三元组数组
- `result_box`：`[标签, 文字]` 二元组或 null

### action_items
```json
"data": {
  "actions": [
    ["场景筛选工作坊", "Week 1-2", "组织跨部门工作坊\n确定3个优先场景\n明确ROI测算标准", "产品VP"],
    ["MVP开发", "Week 3-6", "选定技术栈\n完成核心功能开发\n种子客户接入", "CTO"],
    ["商业验证", "Week 7-10", "获取付费意愿验证\n建立定价模型\n签订LOI", "CEO"]
  ]
}
```
- `actions`：`[标题, 时间线, 描述, 负责人]` 四元组数组

---

## 高级类版式

### content_right_image
```json
"data": {
  "subtitle": "核心发现",
  "bullets": ["93% IT领导者计划2年内引入智能体 [F]", "但仅23%实现规模化部署 [F]", "主要卡点：数据安全与集成复杂度 [I]"],
  "takeaway": "关键洞察：意愿与落地之间存在巨大GAP，这正是创业机会",
  "image_label": "Market Gap Illustration"
}
```
- `bullets`：字符串数组

### checklist
```json
"data": {
  "columns": ["能力模块", "负责人", "截止日期", "状态"],
  "col_widths": null,
  "rows": [
    ["NLU引擎优化", "AI团队", "2026-08", "active"],
    ["工具生态扩展", "平台团队", "2026-09", "risk"],
    ["安全合规认证", "安全团队", "2026-10", "pending"]
  ]
}
```
- ⚠️ **`col_widths` 必须传 null 或省略**（不可传数字数组）
  - 此版式是唯一一个引擎签名里有 col_widths 参数但需要 Inches 对象的版式
  - JSON 中传数字会被当作 EMU 处理
- `rows`：每行最后一个元素是状态 key（'active'/'risk'/'pending'/'done'）

### cycle
```json
"data": {
  "phases": [
    ["数据采集", 0.5, 2.0],
    ["模型训练", 3.5, 1.5],
    ["部署上线", 6.5, 2.0],
    ["用户反馈", 3.5, 4.0]
  ],
  "right_panel": ["持续改进", ["每月迭代一次模型", "A/B测试新功能", "监控关键指标"]]
}
```
- `phases`：`[标签, x坐标(英寸), y坐标(英寸)]` 三元组
- `right_panel`：`[面板标题, 要点列表]` 二元组或 null

---

## ⛔ 禁止使用的版式（JSON 不兼容）

以下版式的数据字段需要 Python `RGBColor` 对象，在 `deck_spec.json` 中无法正确序列化：

| 版式 | 原因 | 替代方案 |
|------|------|---------|
| `grouped_bar` | `series` 的颜色需要 RGBColor | 改用 `data_table` 或 `three_stat` |
| `horizontal_bar` | `items` 的颜色需要 RGBColor | 改用 `scorecard` 或 `data_table` |
| `swot` | `quadrants` 的颜色需要 RGBColor | 改用 `matrix_2x2`（默认色）或 `side_by_side` |

---

## ⚠️ 已废弃版式（不要使用）

| 版式 | 状态 | 替代方案 |
|------|------|---------|
| `venn` | RETIRED | 改用 `matrix_2x2` 或 `side_by_side` |
| `funnel` | RETIRED | 改用 `vertical_steps` 或 `process_chevron` |

---

## 常见错误对照表

| 错误写法 | 正确写法 | 影响 |
|---------|---------|------|
| `"stats": [{"value": "449", "label": "亿元"}]` | `"stats": [["449亿元", "标签", true]]` | 显示 "value" / "label" 文字 |
| `"options": [{"heading": "X", "points": [...]}]` | `"options": [["X", "内容字符串"]]` | 显示 "heading" / "points" 文字 |
| `"steps": [{"label": "生态锁定", "detail": "..."}]` | `"steps": [["01", "生态锁定", "描述≤50字"]]` | label 放圆圈里竖排 |
| `"col_widths": [8, 15, 22, 12, 43]` | 不传此字段 | 列宽为 0，文字竖排 |
| `"items": [{"title": "X", "desc": "Y"}]` | `"items": [["01", "X", "Y"]]` | 显示 dict keys |
| `"detail_items": ["项目1", "项目2"]` | `"detail_items": "• 项目1\n• 项目2"` | 可能报错或格式异常 |
