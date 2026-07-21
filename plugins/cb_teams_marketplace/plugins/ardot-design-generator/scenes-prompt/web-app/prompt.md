# Web App Scene Injection Prompt

This file is the Agent injection prompt for the **Web App (SaaS / Dashboard / Admin Panel)** scene. When the Agent receives requests involving SaaS interfaces, backend admin systems, data dashboards, in-app pages, workbenches, etc., it MUST strictly follow the instructions in this file.

---

## 1. Scene Definition

**Scene Name**: Web App (SaaS / Admin Panel)
**`fetch_guidelines` topic**: `web-app`
**Default Canvas Size**: 1440 wide (some admin panels may use 1600 / 1920); height varies with content, typically 900–1800.
**Layout Paradigms**: Sidebar + TopBar + Content three-pane, or TopBar + Content two-pane.

**Trigger Keywords** (entering this scene if any is matched):
- English: web app, SaaS, dashboard, admin panel, backend, workspace, console, settings page (web), data table, analytics, CRM, workbench, in-app page
- Chinese: Web 应用、后台、管理后台、控制台、仪表盘、数据看板、工作台、配置页、设置页（Web）、SaaS、CRM、报表页、应用内页

---

## 2. Required Skill to Load

```
use_skill("ardot-design-assistant")
```

---

## 3. Required Rules / References to Load

| Reference File                               | When to Load                                               |
|----------------------------------------------|------------------------------------------------------------|
| `rules/style-guide.md`                       | **Always load** — information density, grayscale system, card grids. |
| `rules/design-rules.md`                      | Required reading before executing `batch_edit`.            |
| `references/ardot-workflow.md`               | Load when orchestrating complex multi-section layouts.     |
| `references/design-to-code-workflow.md`      | Enable only for "Web App to code / React code generation" tasks. |
| `references/extract-style-guide-from-web.md` | Enable only for "extract style from an existing Web App" tasks. |

**Required guidelines fetch**:
```
fetch_guidelines(topic: "web-app")
```

**Additional requirement for table / dashboard scenarios**:
```
fetch_guidelines(topic: "table")   // When the task involves data tables / dashboards
```

---

## 4. MCP Tool Whitelist (Strictly Limited)

**Core Tools**:
- `fetch_editor_state`
- `fetch_guidelines` (topic is `web-app`; additionally use `table` for table-related tasks)
- `fetch_style_guide_tags` (optional — prefer reading `../../rules/style-guide-tags.md` directly; the tag list is static)
- `fetch_style_guide` (tags MUST include `webapp` / `dashboard` / `saas`)
- `fetch_variables`
- `apply_variables`
- `locate_available_space` (width: 1440/1600/1920)
- `batch_read`
- `batch_edit` (≤ 25 ops / call)
- `capture_screenshot`
- `capture_layout`
- `upload_images`

**Code Generation Tasks**:
- `scan_exportable_resources`
- `export_nodes`

---

## 5. Scene-Specific Constraints

1. **Layout Skeleton**:
   - Standard: `Sidebar (240/256)` + `TopBar (56/64)` + `Content (fill)`; Sidebar is collapsible (72).
   - The Content area has a maximum width of 1200–1440, with 24–32 left/right padding and 16–24 spacing between sections.
2. **Information Density**: Web Apps tend toward **medium-high density**; body 14px, secondary 12px, titles 16–24px; line height 20–28. Titles larger than 18px are forbidden for regular inner pages.
3. **Required Base Components**: Sidebar Nav, TopBar, Breadcrumb, Button, Input, Select, Checkbox, Radio, Switch, Table, Pagination, Tabs, Tag, Badge, Avatar, Card, Modal, Drawer, Toast, Empty, Skeleton, Tooltip, Dropdown, Date Picker.
4. **Table Specifications** (if applicable): Header background light gray / 1px row separator / hover highlight / sortable columns show sort indicators; header font 12–13 bold; cells 14; cell vertical padding 12–16. Refer to `fetch_guidelines(topic: "table")`.
5. **State Coverage**: Lists / tables MUST include empty state, loading state (Skeleton / Spinner), and error state samples; Button / Input MUST include all five states: default / hover / active / disabled / focus.
6. **Grid**: The content area uses a 12-column grid with 24 gutter; minimum card width is 240, and flexbox `layout: "horizontal"` + `gap` is preferred.
7. **Primary Color Usage**: The primary color is used only for primary CTAs, selected states, links, and progress; large areas of solid primary color as backgrounds are **forbidden** — use 50/100 light gradients instead.
8. **Reusability**: Any structure repeated 3+ times on a single page MUST be abstracted into a `reusable: true` component; the same type of component across pages MUST be referenced via `type: "ref"` to the base components defined in `DESIGN.md`.

---

## 6. Acceptance Checklist (Agent Self-Check)

- [ ] The three-pane skeleton is complete (Sidebar / TopBar / Content)
- [ ] All lists / tables provide empty state + loading state samples
- [ ] Table styles align with the `fetch_guidelines(topic: "table")` specification
- [ ] Base components reuse `DESIGN.md` with no duplicate redundancy
- [ ] `capture_screenshot` is performed after each section is completed
- [ ] `capture_layout` shows no overlap / clipping / text overflow
- [ ] The primary color is not overused as a large background area
- [ ] For code generation: `preview_url` verifies that the responsive 1440 / 1200 / 1024 breakpoints work correctly
