---
name: wechat-draft-writer
description: "依据文风 DNA 和结构大纲撰写公众号初稿的技能。强制遵循 DNA 的语气、节奏、段落和标点规则，产出风格一致、结构完整的初稿，并提供质量自检。用于把大纲转化为可发布的文章初稿。当用户已有大纲/文风 DNA、需要按个人风格撰写正文时使用此技能。"
description_zh: "按文风 DNA 和大纲撰写风格一致的公众号初稿（含 DNA 合规自检）"
description_en: "Write a WeChat draft following a style DNA and outline"
version: 0.1.0
allowed-tools: Read,Write
metadata:
  clawdbot:
    emoji: "✍️"
---

# Wechat Draft Writer

## 目标
把大纲和文风 DNA 转化为风格一致、结构完整的初稿。

## 输入要求
1. 文章大纲（必填，来自 `wechat-topic-outline-planner`）
2. 文风 DNA 文件（必填，来自 `wechat-style-profiler`；缺失时用 `references/style-dna-default-template.md` 简版兜底）
3. 目标字数（可选，默认 1500-2500）
4. 补充素材（可选）

## 工作流
1. 读取文风 DNA 和大纲。
2. 加载 DNA 强制规则（见 `references/draft-dna-enforcement.md`）。
3. 按大纲逐段撰写，实时校验 DNA 合规。
4. 完成初稿后运行质量自检清单（见 `references/draft-quality-checklist.md`）。
5. 标注仍需人工确认或补充的位置。
6. 给出与标题技能和去 AI 味技能的衔接说明。

## DNA 强制规则
详见 `references/draft-dna-enforcement.md`，核心：
- 段落 1-3 句。
- 禁用破折号。
- 自然过渡，避免机械连接词。
- 禁用违禁词清单。
- 禁止“不是 X，而是 Y”这类否定框架强调句式。

## 输出契约
按以下顺序输出：
1. `初稿正文`
2. `字数统计`
3. `DNA 合规自检结果`
4. `需人工确认的位置`
5. `与标题/去AI味技能的衔接说明`

## 质量红线
- 不允许偏离文风 DNA。
- 不允许出现破折号。
- 不允许使用违禁词。
- 不允许出现否定框架句式。
- 不允许结构与大纲不一致。
- 不允许跳过质量自检。

## 与本专家其它技能的衔接
- 上游：`wechat-topic-outline-planner`（大纲）、`wechat-style-profiler`（文风 DNA）。
- 下游：初稿 → `wechat-title-generator`（起标题）→ `humanizer`（去 AI 味）→ `mp-draft-push`（推送草稿箱）。
