---
name: joyrec-find
display_name: 查找录音
display_name_en: Find Recordings
description: "Find JOY recordings by name or date range. Use when the user says 'last week's meetings', 'the recording about the design review', 'recordings from 2026-10-01 to 2026-10-07'."
description_zh: "按名称或日期范围查找 JOY 录音。"
description_en: "Find JOY recordings by name or date range."
version: 1.0.0
author: SZITON
---

# joyrec-find

**先读 [`joyrec-shared`](../joyrec-shared/SKILL.md)**，了解鉴权、错误语义与输出格式。

## When to use

- 用户带时间范围：「上周」「昨天」「10 月 8 日」
- 用户带关键词：「关于评审的录音」「产品周会」
- 两者组合

## Steps

1. 把自然语言时间换算成 `YYYY-MM-DD`：
   - 「上周」按用户所在时区计算周一至周日
   - 「今天」「昨天」同理，不要臆造时区
2. 调用 `…list_files`，传 `date_from` / `date_to` 与/或 `query`
   - `query`：名称子串匹配，忽略大小写
   - 日期为**闭区间**
3. 筛选与分页正交，可同时传 `page` / `page_size`
4. 结果多于 20 条时，先展示第一页并说明总数
5. 无结果时明确说明，并建议放宽日期或关键词

## Anti-patterns

- 不要静默忽略用户给的时间范围
- `date_from` 晚于 `date_to` 会被拒绝，先自行校验
- 不要用 `get_note` 的全文去代替名称搜索

## Example

用户：「上周的会都聊了啥」

Agent：
- `…list_files(date_from=<上周一>, date_to=<上周日>, page=1, page_size=20)`
- 若无结果：「上周没有找到录音，要不要看看前一周？」
