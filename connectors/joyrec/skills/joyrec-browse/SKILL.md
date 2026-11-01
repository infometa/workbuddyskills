---
name: joyrec-browse
display_name: 浏览录音
display_name_en: Browse Recordings
description: "Browse, list, or paginate through JOY recordings. Use when the user says 'what recordings do I have', 'show my recent recordings', 'list my recordings', or asks for the next page."
description_zh: "浏览、列出或翻页查看 JOY 录音列表。"
description_en: "Browse, list, or paginate through JOY recordings."
version: 1.0.0
author: SZITON
---

# joyrec-browse

**先读 [`joyrec-shared`](../joyrec-shared/SKILL.md)**，了解鉴权、错误语义与输出格式。

## When to use

- 用户想看库里有什么，但没有明确目标
- 用户说「最近的录音」「翻页」「下一页」「再来一些」

## Steps

1. 调用 `…list_files`，参数 `page=1`、`page_size=20`
2. 用紧凑表格展示：**名称**、**日期**（YYYY-MM-DD）、**时长**（`5m23s` 风格）
3. 若返回条数少于 `page_size`，告知「没有下一页」
4. 用户要更多时，`page` 加 1 再调；**惰性分页**，不主动拉全量

## Anti-patterns

- 不要主动循环拉取所有页
- 浏览阶段不要调用 `…get_note` / `…get_transcript`
- 不要把毫秒时长或内部 id 直接展示给用户

## Example

用户：「我最近的录音都有哪些」

Agent：
- `…list_files(page=1, page_size=20)`
- 渲染表格，末尾提示「这是第 1 页，说『下一页』继续」
