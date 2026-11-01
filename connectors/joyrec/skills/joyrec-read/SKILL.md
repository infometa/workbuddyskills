---
name: joyrec-read
display_name: 精读录音
display_name_en: Read Recording
description: "Read the AI notes or the full timestamped transcript of one JOY recording. Use when the user asks what was said in a specific recording or wants the original transcript."
description_zh: "读取单条 JOY 录音的 AI 纪要或带时间戳的完整转写。"
description_en: "Read the AI notes or the full timestamped transcript of one JOY recording."
version: 1.0.0
author: SZITON
---

# joyrec-read

**先读 [`joyrec-shared`](../joyrec-shared/SKILL.md)**，了解鉴权、错误语义与输出格式。

## When to use

- 已经定位到具体录音，需要看内容
- 用户要「纪要」「原文」「完整转写」「谁说了什么」

## Steps

1. 没有 `record_id` 时，先用 `joyrec-find` 或 `joyrec-browse` 定位，再把 `id` 作为 `file_id`
2. 先调用 `…get_note(file_id)`：
   - 有纪要：直接按 markdown 展示
   - 返回「暂无纪要」：改用 `…get_transcript`
3. 需要原文时调用 `…get_transcript(file_id, limit=50)`：
   - 返回 `next_cursor` 时，仅在用户要求「继续/完整」时才翻页
   - 长转写不要一次拉完，按需分页
4. 转写按 `[MM:SS-MM:SS] 说话人：内容` 展示
5. 若 `has_timestamps=false`，说明这是降级数据，**不要编造时间戳**

## Anti-patterns

- 不要再把整条转写塞进摘要里；摘要交给 `joyrec-digest`
- 不要一次性拉取全部游标（长录音会超上下文）
- 不要在没有确认录音的情况下猜内容

## Example

用户：「把上周产品评审那条的原文发我」

Agent：
- `…list_files(query="产品评审", date_from=..., date_to=...)` → 取 `id`
- `…get_transcript(file_id, limit=50)`
- 按时间戳分段展示，末尾提示「还有下一页，需要继续吗？」
