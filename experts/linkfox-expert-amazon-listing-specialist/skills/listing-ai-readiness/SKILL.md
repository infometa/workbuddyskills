---
name: listing-ai-readiness
description: 对已提供的 Amazon Listing 做本地 AI 导购内容结构检查，评估买家问题承接、信息完整度、可回答性和事实边界。不调用 Alexa、Rufus 或任何外部平台。
---

# Listing AI Readiness

仅执行离线内容检查。输入为完整 Listing、商品事实和可选买家问题；输出问题覆盖、四柱状态与逐字段修复建议。

## 检查维度

- `what`：商品是什么、关键属性是否明确。
- `who_scene`：适用人群与场景是否具体。
- `pain_solution`：痛点与解决方式是否形成闭环。
- `trust_boundary`：限制、兼容性、规格与声明边界是否清楚。
- `question_coverage`：已提供的买家问题能否在标题、五点或描述中找到明确答案。

## 规则

- 不发起任何外部问答实测，不输出引用率、推荐状态或平台验证结论。
- 缺少商品事实时标记 `unknown`，不通过猜测补齐。
- 只给建议，不在本 Skill 内改写文案；改写由对应 writer 或 `listing-core mode=rewrite` 执行。
- 输出保存为普通 JSON 或 Markdown，由宿主决定落点与展示方式。
