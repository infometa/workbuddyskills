# Landing Page Scene Injection Prompt

This file is the Agent injection prompt for the **Landing Page (Marketing Website Homepage)** scene. When the Agent receives requests involving landing pages, marketing pages, product homepages, promotional pages, or campaign pages, it MUST strictly follow the instructions in this file.

---

## 1. Scene Definition

**Scene Name**: Landing Page
**`fetch_guidelines` topic**: `landing-page`
**Default Canvas Size**: Desktop 1440 wide (height varies with content, typically 3000–6000); if a mobile version is required, create a mirrored 375×N version separately.

**Trigger Keywords** (entering this scene if any is matched):
- English: landing page, marketing page, product homepage, hero section, promotional page, campaign page, startup homepage, SaaS landing
- Chinese: 落地页、营销页、推广页、产品首页、首屏、官网首页、活动页、着陆页、获客页

---

## 2. Required Skill to Load

```
use_skill("ardot-design-assistant")
```
> This scene strictly follows the Skill's standard workflow (Steps 1–7).

---

## 3. Required Rules / References to Load

| Reference File                               | When to Load                                             |
|----------------------------------------------|----------------------------------------------------------|
| `rules/style-guide.md`                       | **Always load** — provides bento grid, hero impact, and creative layouts. |
| `rules/design-rules.md`                      | Required reading before executing `batch_edit`.          |
| `references/ardot-workflow.md`               | Reference for Example A (Creating a New Landing Page) end-to-end workflow. |
| `references/design-to-code-workflow.md`      | Enable only for "landing page to code / export as webpage" tasks. |
| `references/extract-style-guide-from-web.md` | Enable only for "referencing competitors / extracting styles" tasks. |

**Required guidelines fetch**:
```
fetch_guidelines(topic: "landing-page")
```

---

## 4. MCP Tool Whitelist (Strictly Limited)

**Core Tools**:
- `fetch_editor_state`
- `fetch_guidelines` (topic fixed to `landing-page`)
- `fetch_style_guide_tags` (optional — prefer reading `../../rules/style-guide-tags.md` directly; the tag list is static)
- `fetch_style_guide` (tags MUST include `landing-page` or `website` / `marketing`)
- `fetch_variables`
- `apply_variables` (if new landing-specific colors are required)
- `locate_available_space` (width: 1440)
- `batch_read`
- `batch_edit` (≤ 25 ops / call)
- `capture_screenshot`
- `capture_layout`
- `upload_images`

---

## 7. Acceptance Checklist (Agent Self-Check)

- [ ] Total page height is 3000–6000px, with reasonable section rhythm
- [ ] Each section has been verified with `capture_screenshot`
- [ ] All colors / font sizes / spacings come from `DESIGN.md` or `fetch_variables`
- [ ] All images are retrieved via `G()`; no manually entered URLs
- [ ] `capture_layout` shows no overlap / clipping
