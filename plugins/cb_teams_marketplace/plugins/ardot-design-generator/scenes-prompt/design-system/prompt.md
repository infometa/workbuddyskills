# Design System Scene Injection Prompt

This file is the Agent injection prompt for the **Design System** scene. When the Agent receives requests involving design systems, design guides, design languages, design tokens, component library foundations, extracting styles from websites, etc., it MUST strictly follow the instructions in this file.

---

## 1. Scene Definition

**Scene Name**: Design System (Design Guide)
**Deliverables**: `DESIGN.md` (at the workspace root) + Design System pages (visualized tokens / component inventory / typography samples on the canvas) + optional variable sets (via `apply_variables`)

**Trigger Keywords** (entering this scene if any is matched):
- English: design system, design tokens, design guide, style guide, component library basics, generate style guide from website, extract design style, convert website to design guide, design language, brand system
- Chinese: 设计系统、设计指南、设计语言、设计规范、设计 tokens、基础组件库、从网站提取风格、网站风格转设计稿、将网站设计转为设计指南、分析网站设计风格、色板、字体系统、间距圆角规范、图标库

---

## 2. Required Skill to Load

When the Agent enters this scene, it MUST first invoke:

```
use_skill("ardot-design-assistant")
```
> This scene is the core implementation of the Skill's "Extract Style Guide From Web Workflow" and "Step 3 Build Design Guide" capabilities.

---

## 3. Required Rules / References to Load

Read the following files under `ardot-design-assistant/references/` on demand:

| Reference File                               | When to Load                                             |
|----------------------------------------------|----------------------------------------------------------|
| `references/extract-style-guide-from-web.md` | **Core reference**. MUST load for any "extract style from website" task. |
| `rules/style-guide.md`                       | Always load — visual philosophy, creative direction, bento grid, etc. |
| `rules/design-rules.md`                      | Required reading before executing `batch_edit` / building components. |
| `references/ardot-workflow.md`               | Reference for Example D (Setting Up Design Tokens) workflow. |

**Do NOT execute `fetch_guidelines`**: this scene is not bound to a single scenario topic. Instead, the user selects or explicitly specifies it via Skill Step 3.1 (valid options: landing-page / web-app / mobile-app / slides).

---

## 4. MCP Tool Whitelist (Strictly Limited)

**Core Tools**:
- `fetch_editor_state`
- `fetch_style_guide_tags` (optional — prefer reading `../../rules/style-guide-tags.md` directly; the tag list is static)
- `fetch_style_guide`
- `fetch_variables`
- `apply_variables` (**high frequency in this scene** — create COLOR / FLOAT / STRING / BOOLEAN variable sets, supporting Light / Dark multi-mode)
- `locate_available_space`
- `batch_read`
- `batch_edit` (≤ 25 ops / call)
- `capture_screenshot`
- `capture_layout`
- `upload_images`

**Website Extraction Only** (enabled only when the user provides a URL or requests style extraction from a website):
- `web_fetch` (fetch HTML / CSS)
- `export_nodes` (if reference images need to be exported)

**Forbidden**: Any structural changes to existing business pages on the canvas, unless the user explicitly requests to sync tokens.

---

## 5. Acceptance Checklist (Agent Self-Check)

- [ ] `DESIGN.md` has been generated and contains the structure and content specified by the user
