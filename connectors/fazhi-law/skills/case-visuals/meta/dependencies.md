# 依赖关系

## 上游技能依赖

| 技能 | 依赖程度 | 用途 |
|------|----------|------|
| civil-fact-multisource | 推荐 | 提供多源事实提取的结构化输出，作为本技能的 content 输入 |
| civil-fact-strategy | 推荐 | 提供事实策略分析产物（事实分层+法律映射），增强图表的信息深度 |
| payment-field-extract | 可选 | 提供付款字段提取结果，用于资金流向关系图 |
| plaintiff-evidence-map | 可选 | 提供原告证据组织结果，用于证据关联图 |

## 下游协同技能

| 技能 | 协同方式 | 用途 |
|------|----------|------|
| legal-document-formatter | 下游消费 | 将图表代码嵌入法律文书格式化输出 |
| lawyer-content-generator | 下游消费 | 将图表用于律师内容创作（公众号、短视频等） |
| answer-draft | 下游消费 | 在答辩状中引用图表作为事实梳理附件 |
| counsel-annual-report | 下游消费 | 在法律服务报告中嵌入图表 |

## 被替代技能

本技能整合并替代以下两个已有技能：
- **case-graph-gen**（案情图谱生成）：v1.0.0 → DEPRECATED，全部能力已整合
- **fact-timeline-cite**（法律事实时间轴生成）：v1.0.0 → DEPRECATED，全部能力已整合

替代关系映射：
| 原技能能力 | 本技能对应 | 对应图表类型 |
|------------|-----------|-------------|
| 人物关系图 | 主体关系图 | relation |
| 事件链时间轴 | 时间轴图 | timeline |
| 证据关联图 | 证据关联图 | evidence |
| 核心争议链路 | 争议链路图 | dispute |
| 证据锚点绑定 | 时间轴证据标注 | timeline |
| 断点矛盾识别 | 断点矛盾分析 | timeline / evidence |

## 外部依赖与平台适配

- **Mermaid.js**：图表生成与渲染引擎，建议 v10+；优先复用 `assets/mermaid.min.js`。
- **可截图的浏览器或 Mermaid CLI**：将 Mermaid 渲染为 PNG/SVG；不可用时降级为 Mermaid 源码。
- **平台对话内展示能力**：具体调用契约独立维护在 `references/inline-render-adapter.md`。目标平台已注册 `PureShowWidget` 时，将它作为 conversation_inline 的首选适配器并以 `mode=inline` 逐图渲染 SVG；未注册时才使用平台原生组件、Markdown 图片或可预览附件。
- **Markdown 渲染器**：支持文字、表格、图片嵌入和 Mermaid 代码块。

默认交付通道为 `conversation_inline`。平台能力降级顺序：PureShowWidget 内联 SVG → 原生 Widget/SVG 组件 → 对话内嵌 PNG/SVG 图片 → 可预览图片附件 → 精简文字。Mermaid 源码仅在 `include_source=true` 时输出。HTML 仅在用户明确要求或 `deliver_style=html_report` 时启用，不是默认依赖或默认产物。
