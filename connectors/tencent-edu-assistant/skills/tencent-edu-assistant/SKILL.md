---
name: tencent-edu-assistant
display_name: 腾讯教育学习助手
display_name_en: Tencent Edu Assistant
description: 用户在 WorkBuddy 中打开学习空间专题页时使用。触发词：这页、这篇、这个专题、当前资料、我选中的、当前专家、生成笔记 / 测验 / 闪卡 / 课程、学习空间任务 requestId。先调用 get_page_context 获取页面上下文与待完成的生成任务，再基于资料作答或按任务要求生成并交付。
description_zh: 基于学习空间专题资料答疑，并把生成的笔记、测验、闪卡、互动课程回填到专题
description_en: Answer questions from Tencent Edu Assistant topic materials and deliver generated notes, quizzes, flashcards and courses back to the topic
examples_zh:
- "这一页讲的是什么？帮我总结一下"
- "根据当前专题的资料出 10 道测验题"
- "用当前专家的口吻解释一下我选中的这段话"
examples_en:
- "What is this page about? Summarize it for me"
- "Create 10 quiz questions from this topic's materials"
- "Explain the text I selected in the current expert's voice"
version: 0.1.2
author: "Tencent"
---

# 腾讯教育学习助手 · 学习空间

本连接器（MCP 服务 `tencent-edu-assistant`）连接用户在 WorkBuddy 内打开的「学习空间 · 专题详情」页面。页面上下文和生成任务都**不会自动出现在对话里**，需要你主动调用 `get_page_context` 获取。

## 什么时候调用 get_page_context

满足任一条件就先调用，再回答或执行：

1. 用户提到「这页 / 这篇 / 这个专题 / 当前资料 / 我选中的 / 当前专家」，而对话中还没有 `[学习空间页面上下文]`；
2. 用户要求生成笔记、测验、闪卡或课程；
3. 用户消息里带有「学习空间任务 requestId：…」（由学习空间页面填入）。

同一轮对话里上下文可能变化（用户切换了资料、页码或选区），用户再次提到页面内容时重新调用一次。

返回「当前没有学习空间页面上下文」时，告诉用户先在 WorkBuddy 中打开学习空间专题详情页；在此之前只能基于对话内容作答。

## 工具

| 工具 | 用途 | 参数 |
|---|---|---|
| `get_page_context` | 页面上下文（专题、全部文件的签名下载地址、阅读位置、选中文本、答疑专家）+ `[待完成的生成任务]` | 无 |
| `get_active_expert` | 用户选中的答疑专家及档案 | 无 |
| `get_topic_detail` | 专题详情（权威数据） | `topicId`（可选，默认当前专题） |
| `list_topic_menu` | 专题能做什么（资料精读 / 视频学习 / AI 生课等入口） | 无 |
| `list_experts` | 可选的学科专家 | 无 |
| `report_generation_progress` | 上报生成任务进度 | `requestId`、`stage`，可选 `message`、`done`、`total`、`error` |
| `deliver_file_to_assistant` | 把产物文件交付到专题 | `requestId`、`filePath`（绝对路径） |

## 基于资料答疑

- 资料原文**只能**通过 `get_page_context` 返回的签名地址用 curl / WebFetch 下载读取，禁止在本地磁盘搜索同名文件。
- 优先围绕用户正在阅读的文件和页码、选中文本作答；不要凭空作答。
- 页面指定了答疑专家时，完全代入该专家的身份、学科视角与表达风格。

## 执行生成任务

`[待完成的生成任务]` 中的每个任务都给出了 requestId、技能包地址、产物文件名、表单参数，以及进度上报和交付要求，严格照做：

1. **只在用户本条消息明确要求生成该类产物时开始**；已生成但未交付的任务，立即补交。
2. 下载并解压任务给出的技能包，按技能说明生成。技能包签名失败时使用本地已安装的同名技能。
3. 开始后立即 `report_generation_progress(stage=reading)`；进入大纲 / 结构报 `outlining`；正文生成报 `generating`；校验与写入报 `validating`。每完成一个阶段或一批内容都上报，**不要省略**：页面靠它判断任务是否还在进行，超过几分钟没有上报会提示用户「可能已中断」。
   - `done/total` 只在 `generating` 阶段成对传：测验为题数，闪卡为卡片数，课程为章节数，笔记不传。
   - `message` 只写简短中文说明，不要放 URL 或密钥。
4. 把产物写到 WorkBuddy 工作目录，文件名用任务给出的产物文件名（后缀必须一致：`-note.md` / `-quiz.json` / `-flashcard.json` / `-course.html`）。
5. 最后调用 `deliver_file_to_assistant(requestId, filePath=绝对路径)`。**交付成功前不要告诉用户已完成**；成功后用一句话告诉用户，不要复述文件内容。
6. 任一步失败且无法继续：`report_generation_progress(stage=failed, error=原因)`，再告诉用户原因。

开始执行时就把「各阶段进度上报」和「最后交付」列入待办，交付作为最后一项，避免生成过程很长、上下文被压缩后遗漏。

## 常见错误与处理

| 返回 | 处理 |
|---|---|
| 当前没有学习空间页面上下文 | 请用户先在 WorkBuddy 中打开学习空间专题详情页 |
| 任务不存在或已过期/已交付/已失败 | 不要重试；请用户在页面重新点击生成 |
| 文件名后缀不符 / filePath 必须是绝对路径 | 按提示改文件名或路径后重试交付 |
| 产物校验失败：… | 按原因修正产物内容（如 JSON 结构）后重试交付 |
| 该任务正在交付中 | 等待上一次交付结果，不要重复调用 |
| 端口 3101 被其他程序占用 / 本地服务正在切换 | 稍后重试；持续出现时请用户检查是否有其他程序占用 3101 端口 |

## 确认规则

- 交付会把文件保存到用户的学习空间专题，只交付当前任务的产物，不要把其他文件交付到专题。
- 用户没有要求生成时，不要因为看到 `[待完成的生成任务]` 就自行开始生成。
