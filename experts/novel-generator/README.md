# Novel Generator · 爽文小说生成专家

A CodeBuddy expert plugin that turns a **one-line Chinese fiction premise** into a full prompt, outline, and serialized 爽文 (power-fantasy web novel) — chapter by chapter, with built-in continuity memory that keeps characters, locations, plot points, and world rules consistent across a long-form work.

## What it does

- **One-line → full prompt** — Give "废柴少年获得系统逆袭" and it expands along 8 dimensions: genre positioning, world-building, protagonist design, core conflict, 爽-point design, pacing, supporting cast, opening hook.
- **Global outline** — Volume-level structure with 起承转合, power/level system, and key turning points.
- **Serialized chapters** — 2000-3000 words each, every chapter with a summary, 爽-point, emotional curve, and a chapter-end hook.
- **Continuity memory** — `.learnings/` tracks `CHARACTERS.md`, `LOCATIONS.md`, `PLOT_POINTS.md`, `STORY_BIBLE.md`, `ERRORS.md`. Every new chapter reads memory first, so the dead stay dead and setups pay off.
- **Mermaid diagrams** — Character relationship graphs, faction maps, power-tier charts, growth timelines.
- **Failure logging** — Continuity breaks, setting contradictions, pacing loss, and character-breakdown events are recorded with fixes and prevention notes.

## Powered by

- **爽文 pacing formula** — small face-slap every 1-2 chapters, medium every 3-5, big climax every 8-12, volume finale every 15-20.
- **Quality checklist** — clear underdog starting point, rule-bound cheat/system, a face-slap in the first 3 chapters, layered power tiers, a "everyone looks down → gets proven wrong" structure.
- **Capture → Record → Settle → Reuse** loop inspired by self-improving-agent's `.learnings/` pattern.

## Supported genres

都市 · 修仙 · 玄幻 · 重生 · 系统流 · 末世 · 网游 · 科幻 — and hybrids thereof.

## Requirements

- No dependencies — pure creative-writing guidance and Markdown output.
- Works in Chinese (primary); English summaries on demand.

## Example

**Request:** 帮我写一个废柴少年获得系统后逆袭的修仙爽文

The expert will:
1. Expand it into a full prompt (`output/提示词.md`) and ask you to confirm.
2. Generate the global outline (`output/大纲.md`).
3. Write chapter by chapter (`output/第01章_*.md`, `第02章_*.md`, …), updating memory after each.
4. Produce Mermaid diagrams for key battles, relationships, and power tiers.

## Notes

- Never revives dead characters, silently changes established settings, or drops established characters.
- `init-novel.sh --clean` wipes prior chapters and memory — confirm or back up first.
- Keep different novels in separate workspaces to avoid memory bleed.
- Output is creative draft; review for compliance and quality before publishing or commercializing.
