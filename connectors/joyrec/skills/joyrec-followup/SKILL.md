---
name: joyrec-followup
display_name: 提取待办
display_name_en: Extract Follow-ups
description: "Extract action items, owners and follow-up items from a JOY recording. Use when the user says 'what do I need to do after this meeting', 'extract todos', or 'draft a follow-up'."
description_zh: "从 JOY 录音中提取待办事项、责任方与跟进内容。"
description_en: "Extract action items, owners and follow-up items from a JOY recording."
version: 1.0.0
author: SZITON
---

# joyrec-followup

**先读 [`joyrec-shared`](../joyrec-shared/SKILL.md)**，了解鉴权、错误语义与输出格式。

## When to use

- 用户要「待办」「跟进事项」「谁负责什么」
- 用户要根据会议内容写跟进邮件/消息

## Steps

1. 定位录音并调用 `…get_note(file_id)`；纪要不全时再用 `…get_transcript`
2. 提取三类信息：
   - **事项**：要做什么
   - **责任方**：谁负责（未提及写「未提及」）
   - **时间要求**：截止时间/时间点（未提及写「未提及」）
3. 用编号列表输出；同一事项不要拆成多条
4. 用户要跟进邮件时，基于以上列表生成，语气简洁，不添加未经确认的承诺
5. 如果录音里没有明确待办，直接说明「没有提取到明确待办」

## Anti-patterns

- 不要根据常识补全责任人
- 不要把讨论中的假设当成已决定事项
- 不要输出与录音无关的通用建议

## Example

用户：「这次会我需要跟进什么」

Agent：
- `…get_note(file_id=...)`
- 输出：
  1. 完善接口文档 —— 产品 —— 周五前
  2. 补齐越权测试 —— 后端 —— 未提及
