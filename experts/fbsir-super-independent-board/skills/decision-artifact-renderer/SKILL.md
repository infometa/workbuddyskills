---
name: decision-artifact-renderer
description: 将已经完成的超级独董会 DecisionRecord 转换为聊天、一页纸、HTML、演示、信息图或视频脚本，并保持判断语义不变。
user-invocable: false
---

# Decision Artifact Renderer

## 触发

只有以下情况使用：

- 用户明确要求一种格式；
- 核心 Skill 已推荐产物且用户选择继续制作；
- 当前决定需要给团队、管理层、客户或合作方沟通；
- 用户需要行动包或结果复审卡。

不要因为宿主存在文件能力就自动写盘。

## 输入门

必须收到完整 DecisionRecord，至少包含：

- 真问题；
- AI 建议；
- 证据边界；
- 最强反方；
- 成立与失效条件；
- 人工关卡；
- 一个下一步；
- 用户决定状态。

输入不完整或相互冲突时退回核心 Skill，不自行补写判断。

## 语义不可变

渲染不得改变：

- 建议状态和正文含义；
- 事实、估计、假设和未知；
- 最强反方；
- 成立与失效条件；
- 人工复核边界；
- 用户决定；
- 当前动作和复审触发器。

可以改变版式、顺序、信息密度、视觉层次和读者解释，但不能新增事实、风险或权威。

详细规则：@references/artifact-contract.md
格式配方：@references/format-recipes.md

## 一主一伴

每轮只选择一个主产物，最多一个伴生产物。主产物解决当前使用任务，伴生产物只用于必要的分发适配。

## 格式与降级

1. Chat：始终可用。
2. Markdown：可在聊天交付；真实文件需要写入回执。
3. HTML：先交付源稿；保存和预览需要真实回执。
4. DOCX/PDF：当前宿主可生成并完成渲染检查时才交付文件，否则退到 HTML 或 Markdown。
5. PPTX：宿主可生成和预览时交付，否则交付逐页结构和讲稿。
6. 图片：宿主可生成和保存时交付，否则交付信息图 brief、构图和提示词。
7. 视频：本版本保证脚本、分镜、旁白、字幕和封面方案；实际成片只有真实视频能力和播放回执存在时才交付。
8. 行动与提醒：真实任务或提醒需要目标、时间、批准和计划 ID；否则交付手动行动包。

## 回执表达

- 回答中完整内容可直接使用：已交付；
- 文件保存并同路径回读：已执行本地文件动作；
- 只生成源稿：已交付源稿，尚未物化；
- 宿主能力缺失：未执行对应格式，已提供降级产物；
- 外部发送或发布前：待授权。

预览不等于客户已读，文件存在不等于外部送达。

## 模板

- 一页纸：@templates/decision-brief.md
- HTML：@templates/decision-page.html
- 演示稿：@templates/presentation-outline.md
- 信息图：@templates/infographic-brief.md
- 视频：@templates/video-storyboard.md
- 行动包：@templates/action-packet.md
- 结果复审：@templates/outcome-review-card.md

机器合同：[artifact contract](../../contracts/artifact-contract.json)

## 完成检查

- 主产物是否与读者和使用场景匹配；
- 是否只有一主一伴；
- 关键反方和失效条件是否仍可见；
- 是否引入了 DecisionRecord 中不存在的事实；
- 是否把源稿、文件、预览、送达和业务结果混为一谈；
- 格式不可用时是否已按顺序降级。
