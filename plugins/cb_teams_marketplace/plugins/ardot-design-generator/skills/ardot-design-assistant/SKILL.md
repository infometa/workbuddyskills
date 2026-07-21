---
name: ardot-design-assistant
description: "This skill should be used for any design-related tasks involving creating, editing, or modifying visual designs, UI screens, pages, layouts, or components, as well as converting designs to frontend code. Trigger phrases include: generate/create/design a page, design a screen, create a landing page, make a dashboard, design a login screen, modify the design, update the layout, change colors, add a component, edit design file, create wireframe, design a form, build a UI, generate homepage, create slides, design a presentation, generate style guide, create design system from website, extract design tokens, convert design to code, design to HTML, export as webpage, pixel-perfect reproduction, implement slide transitions, 生成设计指南, 提取设计风格, 网站风格转设计稿, 设计稿转代码, 转为前端代码, 生成HTML, 导出为网页, 一比一还原, 复刻设计稿, 设计稿出码, 切图, 幻灯片转网页, or Chinese equivalents like 生成页面, 设计页面, 创建界面, 修改设计稿, 调整布局, 修改样式, 生成设计, 做一个页面, 画一个页面. Routes all design work through the ardot MCP server."
allowed-tools: 
---

# Ardot Design Assistant

Standard workflow for completing design tasks on `.ardot` files via the ardot MCP server. All canvas manipulation MUST go through ardot MCP tools.

## Reference Files

Load on demand based on task type:

| File | When to load |
|------|--------------|
| `../../rules/design-rules.md` | **Single source of truth** — editing principles, coordinates, flexbox, text, components, colors, variables, tables, images, effects, SVG, property schema, troubleshooting, post-generation validation |
| `../../rules/style-guide.md` | Visual style guide — typography, color, layout, surface treatment, variance levels, forbidden AI patterns, bento grid |
| `../../rules/style-guide-tags.md` | Static list of valid tags for `fetch_style_guide(tags)` — read this instead of calling `fetch_style_guide_tags` |
| `references/ardot-workflow.md` | End-to-end workflow examples (create, modify, global style update, tokens, form) and detailed operation syntax |
| `references/slides-workflow.md` | Slides / deck creation — 5-phase process (use when current model is **NOT** opus4.7) |
| `references/slides-agent-teams-workflow.md` | Slides / deck creation — Agent teams workflow (use when current model **IS** opus4.7; first ask the user whether to enable agent teams, clarifying that it takes more time and consumes more tokens — if yes, use this workflow; if no, fall back to `references/slides-workflow.md`) |
| `references/extract-style-guide-from-web.md` | Website → design guide extraction |
| `references/design-to-code-workflow.md` | Design → HTML/CSS/JS conversion, generate Application, to code, slide transitions, responsive scaling |
| `references/guidelines-landing-page.md` | Landing / marketing page |
| `references/guidelines-web-app.md` | Web app (default for generic design tasks) |
| `references/guidelines-mobile-app.md` | Mobile / app screen |
| `references/guidelines-slides.md` | Slide deck design rules (L01–L20, typography, visuals) |
| `references/guidelines-table.md` | Tables / dashboards with tables |
| `references/guidelines-code.md` | Design-to-code implementation |
| `references/guidelines-tailwind.md` | Tailwind v4 implementation (alongside `guidelines-code.md`) |

## Preparation: (IMPORTANT: Ensure a Design File Is Open)

Before any canvas operation, make sure an Ardot design file is loaded in the editor. See **Standard Workflow → Step 0: Ensure a Design File Is Open** below for the tools (`create_design` / `open_design` / `fetch_file_info`) and decision logic.

## Standard Workflow

### Step 0: Ensure a Design File Is Open

Before any canvas operation, make sure an Ardot design file is loaded in the editor:

- **`create_design`** — Create a new blank Ardot design file and open it in the editor. Optionally accepts a `fileName`. If the user wants to start from scratch or no existing file is mentioned, call this first.
- **`open_design`** — Open an existing Ardot design file by URL or file ID. Accepts a `fileUrl` parameter (e.g. `https://ardot.tencent.com/file/667788990055443` or bare ID `667788990055443`). If the user provides a file link or ID, call this to load it.
- **`fetch_file_info`** — Fetch the current loaded file ID, after `create_design` or `open_design` has been called to get the file ID.

**Decision logic**:
1. If the user explicitly provides a file URL or ID → call `open_design`.
2. If the user asks to create a new design / start fresh → call `create_design`.(optionally with the given 'fileName').
3. If the editor already has a file loaded (determined in Step 1) → skip this step.
4. If call `create_design` produces an empty canvas, **MAKE SURE SKIP** `fetch_editor_state` at any workflow, the default PageID is `0:1`, use it as the root container.

> ⛔ **Hard gate — do NOT issue any other MCP call until the file is ready.**
>
> After calling `create_design` or `open_design`, the file loads asynchronously. You MUST wait for the context update / ready confirmation before issuing **any** other MCP call.
>
> **Never** bundle `create_design` / `open_design` in the same parallel batch as `fetch_editor_state`, `fetch_variables`, or any other read — those reads will hit an empty or not-yet-loaded editor and return stale/empty state.
>
> Correct order (two separate messages):
> 1. Message 1: `create_design` or `open_design` → wait for ready signal.
> 2. Message 2: subsequent reads (Step 1) — may be parallel, see below.
>
> Exception: if Step 0 is skipped (a file is already loaded from a previous turn), Step 1 can be the first message of the turn.

### Step 1: Read Existing State (parallel, conditional)

Read whatever state is relevant to the task. **Issue all independent reads in a single message as parallel tool calls** — do not serialize them.

| Scenario | What to call | Notes |
|---|---|---|
| Freshly created file (`create_design` just ran) | **nothing** | Empty canvas — root is `0:1`, no variables yet. Skip Step 1, go straight to Step 2. |
| Opened existing file / file already loaded | `fetch_editor_state({includeSchema: false})` + `fetch_variables` | Parallel in one message. |
| Pure modification (file already loaded, target known) | The above **plus** any of `batch_read` / `capture_layout` / `capture_screenshot` as needed | All parallel in one message. |

> **Do NOT call `fetch_style_guide_tags`.** The tag list is static — read `../../rules/style-guide-tags.md` instead.

### Step 2: Creative vs. Compositional

- **Creative** (new screen, page, dashboard, restyle) → proceed to Steps 3–4
- **Compositional** ("add a button", "move this") → skip to Step 5 and load `design-rules.md`

### Step 3: Load Design Guidelines

Load **one or more** design-type guideline, first match wins:

| Priority | Trigger | File |
|---|---|---|
| 1 | slides, presentation, deck, 幻灯片, 演示文稿 | `references/guidelines-slides.md` |
| 2 | mobile, app, iOS, Android, 移动端 | `references/guidelines-mobile-app.md` |
| 3 | landing, marketing, SaaS, 落地页, 营销 | `references/guidelines-landing-page.md` |
| 4 | table, dashboard with tables, 表格 | `references/guidelines-table.md` |
| 5 | convert to code, to App, HTML, 转代码, 出码, 生成应用，转应用 | `references/guidelines-code.md` (+ `guidelines-tailwind.md` if Tailwind) |
| 6 | (web app, default) | `references/guidelines-web-app.md` |

`guidelines-code.md` / `guidelines-tailwind.md` are implementation guidelines and can be loaded **alongside** a design-type guideline when code generation is involved.

### Steps 4–6: Style + Space + Inspection (parallel)

Issue these as **a single parallel batch** in one message — they have no mutual dependency:

- **`fetch_style_guide(tags)`** — pick 5–10 fitting tags from `../../rules/style-guide-tags.md` (see the Selection Guidance section there).
- **`locate_available_space({width, height})`** — required for new top-level screens; skip for pure modification tasks. Never overlap existing content.
- **Inspection calls** (only if modifying existing design and not already covered in Step 1): `batch_read` (find by pattern/ID, `readDepth: 3` for component structure), `capture_layout` (detect problems), `capture_screenshot` (visual verify).

Skip any sub-call that doesn't apply to the current task. The point of parallel batching is to collapse independent reads into one round-trip, not to force every tool to run.

> If a follow-up read depends on this batch's result (e.g. `batch_read({readDepth: 3})` targeting a component discovered via an earlier `batch_read`), issue it as a separate message afterward. Most tasks don't need that.

### Step 7: Execute Design

`batch_edit` with ≤ 25 ops per call. Build order: **structure → content → style → verify**. Ops: **I()** Insert, **U()** Update, **C()** Copy, **M()** Move, **D()** Delete, **G()** Image. For detailed syntax and examples, load `references/ardot-workflow.md`.

### Step 8: Validate

Follow the **Post-Generation Validation Pattern** in `design-rules.md`. Use **tiered validation** — pick the lightest check that matches what the batch changed (T1 structural → `capture_layout` only; T2 content → skip; T3 visual → `capture_screenshot` only; T4 section-complete → both once; T5 final page → one screenshot). **Do not run full dual-verification after every batch_edit.** Enforce the convergence threshold: **max 2 fix iterations per section**, ignore ≤4px spacing noise, no subjective re-polishing once the section matches spec.

## Specialized Workflows

When the task matches one of the following, load the linked reference and follow it strictly (do not improvise the procedure from SKILL.md):

- **Slides / presentation / deck** → choose workflow based on the current model. When the model is **opus4.7**, ask the user whether to use the agent teams workflow (clarify that it takes more time and consumes more tokens): if yes, use `references/slides-agent-teams-workflow.md`; if no, use `references/slides-workflow.md`. For other models, use `references/slides-workflow.md` directly. Mandatory design rules live in `references/guidelines-slides.md`.
- **Website → style guide extraction** → `references/extract-style-guide-from-web.md`
- **Design → frontend code** → `references/design-to-code-workflow.md`

## Essential Constraints

These rules apply at all times. Full rule set and troubleshooting are in `design-rules.md`.

- **Every node needs a `name`** — assign meaningful names to all created nodes
- **Keep float colors to 2 decimals** — avoid long floating-point values
- **Text is invisible by default** — always set `fill` on text nodes
- **Use `fill` for all colors** — never use `textColor`, `backgroundColor`, `color`, or `fillColor`
- **Use `cornerRadius`** — not `borderRadius`
- **Font weight must be numeric strings** — `"400"`, `"700"`, not `"bold"`
- **Alignment uses uppercase enums** — `counterAxisAlignItems: "CENTER"`, not `alignItems: "center"`
- **Prefer flexbox layout** — always set `width` and `height` on new frames explicitly
- **Layout default sizing is FIXED** — when setting `layout` to `horizontal`/`vertical`, must explicitly set `width`/`height` for dynamic sizing
- **x/y are ignored in flexbox** — if you need to set x/y on children of flexbox parents, also set `layoutPositioning: "ABSOLUTE"`
- **`fill_container` requires flexbox parent** — only valid when parent has layout
- **`hug_contents` requires own flexbox layout** — only valid on a node that itself has flexbox layout
- **Default frame has white background** — set `fills: []` to remove
- **Max 25 ops per batch_edit** — split by logical sections
- **Every I/C/R needs a binding name** — `document` is predefined for root only
- **No U() on copied descendants** — copied nodes get new IDs; use `descendants` in C() instead
- **No image node type** — images are fills on frames; use G() with `"stock"` preferred
- **Icon frames must set `layout: "none"`** — and always `capture_screenshot()` to verify
- **Create icons as components** — then use `I(parentId, {type: "ref", ref: "iconId"})` to insert instances
- **Variable binding uses `$` prefix** — `fill: "$primary-color"`, `gap: "$spacing-small"`
- **Favor copying + updating** over generating from scratch
- **Parallelize independent reads** — when multiple MCP read calls have no data dependency (e.g. `fetch_editor_state` + `fetch_variables`), issue them in a single message as parallel tool calls; do not serialize them. **Exception**: never bundle these reads in the same message as `create_design` / `open_design` — wait for the file-ready context update first
- **Validate with tiered checks** — match the tier to the batch type (see `design-rules.md` Post-Generation Validation Pattern); do NOT run full screenshot+layout after every batch_edit
- **Text wrapping needs both** — `textAutoResize: "HEIGHT"` AND `width: "fill_container"` (or fixed width)
- **`lineHeight`** — set `lineHeight: "AUTO"` for automatic (preferred) or `lineHeight: 22` for explicit spacing
