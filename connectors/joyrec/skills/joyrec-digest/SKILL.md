---
name: joyrec-digest
display_name: 生成摘要
display_name_en: Digest Recording
description: "Turn a JOY recording into a structured summary or meeting minutes. Use when the user says 'summarize this recording', 'turn it into meeting notes', or 'make a digest'."
description_zh: "把 JOY 录音整理成结构化摘要或会议纪要。"
description_en: "Turn a JOY recording into a structured summary or meeting minutes."
version: 1.0.0
author: SZITON
---

# joyrec-digest

**先读 [`joyrec-shared`](../joyrec-shared/SKILL.md)**，了解鉴权、错误语义与输出格式。

## When to use

- 用户要把某条录音整理成摘要、纪要、会议记录
- 用户要把多条录音汇总成一份周报/复盘

## Steps

1. 定位录音：`…list_files` → 取 `id`
2. 优先调用 `…get_note(file_id)`；纪要为空的再调用 `…get_transcript`
3. 输出固定三段式：
   - **概述**：2–4 句，说清主题、参与方、结论
   - **核心信息**：要点列表，每条一句话
   - **待办清单**：事项 + 责任方 + 时间要求（缺失标注「未提及」）
4. 多段转写超过一页时，先读完本页并说明「基于当前页」，不要假装读过全部
5. 只依据录音内容，不补充外部知识

## Anti-patterns

- 不要编造参会人、日期或结论
- 不要把口头语逐句复述当成摘要
- 不要在没有内容依据时输出「待办」

## Example

用户：「把今天这条录音整理成纪要」

Agent：
- `…get_note(file_id=...)`
- 按「概述 / 核心信息 / 待办清单」输出
- 若纪要未生成：提示「纪要尚未生成，我先基于转写整理一份」，再取转写前 50 段
