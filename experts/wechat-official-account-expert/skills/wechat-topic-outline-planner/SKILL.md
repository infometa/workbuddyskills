---
name: wechat-topic-outline-planner
description: "面向公众号选题与结构规划的技能。基于文风 DNA 和用户想法，产出选题方向、结构化大纲、开头钩子与结尾方案，为写稿技能提供明确输入。用于把粗略想法转化为可执行的文章蓝图。当用户有选题想法、需要规划文章结构/大纲时使用此技能。"
description_zh: "把粗略想法转化为选题方向 + 结构化大纲（含钩子与结尾方案）"
description_en: "Turn rough ideas into WeChat article angles and structured outlines"
version: 0.1.0
allowed-tools: Read,Write
metadata:
  clawdbot:
    emoji: "🗺️"
---

# Wechat Topic Outline Planner

## 目标
把粗糙想法变成结构清晰、可直接写作的选题与大纲。

## 输入要求
1. 选题想法或方向（必填）
2. 文风 DNA 文件路径（可选，但强烈建议，来自 `wechat-style-profiler`）
3. 目标读者（可选）
4. 参考资料（可选，可用 `wechat-article-search` 检索竞品/热点）

## 工作流
1. 明确选题意图与目标读者。
2. 结合文风 DNA 判断选题是否契合作者定位。
3. 产出 2-3 个候选切入角度，说明差异。
4. 每个角度给出一句话核心观点。
5. 用户选择后生成结构化大纲。
6. 大纲需包含开头钩子、主体骨架、结尾方案。
7. 标注每个部分的预期字数与作用。
8. 给出与写稿技能衔接的说明。

## 选题评估
使用 `references/topic-evaluation-rubric.md` 进行评估打分。

## 大纲模式
参考 `references/outline-patterns.md` 选择合适结构。

## 输出契约
按以下顺序输出：
1. `选题分析`
2. `候选角度（2-3个）`
3. `推荐角度与理由`
4. `结构化大纲`
5. `开头钩子方案`
6. `结尾方案`
7. `与写稿技能的衔接说明`

## 质量红线
- 不允许脱离文风 DNA 做选题。
- 不允许输出无差异的候选角度。
- 不允许大纲缺少钩子和结尾方案。
- 不允许跳过字数与作用标注。

## 与本专家其它技能的衔接
- 上游：`wechat-style-profiler`（文风 DNA）、`wechat-article-search`（选题/竞品调研）。
- 下游：确认的大纲直接交给 `wechat-draft-writer` 撰写初稿。
