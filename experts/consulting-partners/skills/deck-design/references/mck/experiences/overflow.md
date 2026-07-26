# Overflow Experiences — Text Overflow Patterns

> Self-Refinement 经验沉淀。AI 在 S3 内容填充前必须读取。

## Experience 001: Action Title Too Long

**Date**: 2026-05-02
**Problem**: Action Title 超过 40 个字符时，22pt 字体导致标题溢出到内容区。
**Root Cause**: 标题栏高度固定 0.9"，超长文字换行后高度超出。
**Fix**: Action Title 限制在 40 字符以内。超过时拆成主标题（简短）+ 副标题。
**Rule**: S3 门禁检查 `len(title) <= 40`。

## Experience 002: Four-Column Desc Too Long

**Date**: 2026-05-02
**Problem**: `four_column` 每栏描述超过 120 字时底部溢出。
**Root Cause**: 4栏均分后每栏宽度约 2.7"，正文14pt 120字超出高度限制。
**Fix**: 每栏描述不超过 120 字符。超出时用 bullet points 替代段落。
**Rule**: S3 门禁检查 `len(col_desc) <= 120`。

## Experience 003: process_chevron 5+ Steps

**Date**: 2026-05-02
**Problem**: `process_chevron` 超过 5 个步骤时，箭头间距变为负值导致文件损坏。
**Root Cause**: Rule 10 保护了外框，但箭头连接器间距公式未同步收窄。
**Fix**: 引擎 v2.3 已修复动态宽度，但描述文字仍需控制在 50 字以内。
**Rule**: S3 门禁检查步骤数 `<= 5`，desc `<= 50 chars`。

## Experience 004: process_chevron Step Label 不能含 \n

**Date**: 2026-05-02
**Problem**: `process_chevron` 步骤标签（第一个元素）中使用 `\n` 换行，导致 Oval 高度溢出 21%。
**Root Cause**: Oval 圆形标签固定高度 0.45"，多行文字撑爆容器。
**Fix**: 步骤标签不得含 `\n`，必须是单行文字（如 "1990-2010" 而非 "阶段一\n1990-2010"）。
**Rule**: S3 门禁检查 `'\n' not in step_label`。

## Experience 005: four_column items 需要三元组 (num, title, desc)

**Date**: 2026-05-02
**Problem**: 传入二元组 `(title, desc)` 导致 `ValueError: not enough values to unpack`。
**Root Cause**: engine 期望 `(num, col_title, desc)` 三元组，num 用于圆形编号显示。
**Fix**: 始终传三元组，第一个元素是编号/标识符（如 "RS1", "1", "A"）。
**Rule**: S3 门禁确认 `four_column` items 每个元素有 3 个字段。

## Experience 006: timeline 最后一个 milestone 标签容易溢出右边界

**Date**: 2026-05-02
**Problem**: timeline 5个里程碑时，最后一个标签位置接近右边界，标签超出 0.47"。
**Root Cause**: timeline engine 均分布局后，最后节点的标签文字向右对齐导致超出内容区。
**Fix**: 最后一个 milestone 标签控制在 6 个字符以内，或使用简短表述。
**Rule**: S3 门禁检查最后一个 milestone label `len(label) <= 6`。
