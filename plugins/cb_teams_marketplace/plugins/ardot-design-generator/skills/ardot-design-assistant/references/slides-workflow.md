# Slides Creation Workflow

This is the end-to-end workflow for creating presentation decks on the ardot canvas. Follow the phases in order — do NOT skip phases or reorder steps.

**Mandatory design rules are defined in `references/guidelines-slides.md`** — load it in Phase 0.3 and enforce throughout all phases. Key rules referenced below as "Rule 1" (Large Typography), "Rule 2" (Rich Backgrounds), "Rule 3" (Decorative Elements & SVG Charts).

## Table of Contents

- [Phase 0: Preparation](#phase-0-preparation) — read references, fetch state, guidelines, style guide
- [Phase 1: Planning](#phase-1-planning) — slide count, outline, canvas grid
- [Phase 2: Canvas Setup](#phase-2-canvas-setup) — locate space, create all slide frames
- [Phase 3: Slide Generation](#phase-3-slide-generation) — per-slide generate → screenshot → layout check → fix
- [Phase 4: Final Review](#phase-4-final-review) — holistic visual pass

---

## Phase 0: Preparation

Before doing anything on the canvas, load all required knowledge and context. This phase is non-negotiable — skipping it will produce low-quality slides that violate design rules.

### 0.0 Ensure Design File Is Open

Before any canvas operation, make sure an Ardot design file is loaded:
- **`create_design`** — Create a new blank file and open it. Optionally accepts a `fileName`.
- **`open_design`** — Open an existing file by URL or file ID. 
- If the editor already has a file loaded (determined in Step 0.2) → skip this step.

### 0.1 Load Reference Knowledge (read these files if not already loaded)

- `design-rules.md` (at `skills/` level) — ardot design constraints (flexbox, text, components, property reference)
- `references/ardot-workflow.md` — `batch_edit` operation syntax, binding rules, full tool parameters

### 0.2 Fetch Editor State

Call `fetch_editor_state` with `includeSchema: false` to get:
- Current page ID
- Active selection
- Available components in the file

### 0.3 Load Slide Design Guidelines

Load `references/guidelines-slides.md` — this is the **authoritative source** for all slide design rules, including:
- **Rule 1**: Large Typography (Title ≥40px, Body ≥24px, no text below 22px)
- **Rule 2**: Rich Backgrounds (gradients + decorative patterns, no pure white/black)
- **Rule 3**: Decorative Elements & SVG Data Charts (≥2 decorative elements per slide)
- 20 Layout Contracts (L01-L20) for different slide types
- Color, imagery, and content density guidelines

These rules are enforced throughout Phase 1-4. References to "Rule 1/2/3" in later phases point to this file.

### 0.4 Fetch Visual Style Inspiration

1. Read `../../../rules/style-guide-tags.md` to see the available tags (static list — do **not** call `fetch_style_guide_tags`)
2. Select 5–10 tags that match the deck's topic and tone
3. Call `fetch_style_guide` with those tags to receive a palette, typography, spacing tokens, and decorative patterns
4. If the returned style guide does not fit the topic, discard it and call again with different tags

**Output of Phase 0**: a concrete color palette, type scale, spacing tokens, and decorative motif to apply consistently across all slides.

---

## Phase 1: Planning

Plan the deck before touching the canvas. Do NOT start creating frames until planning is complete.

### 1.1 Determine Slide Count & Outline

Based on the user's request, decide:
- Total slide count N (typical decks: 8-10 slides)
- Slide roles: Cover → Agenda → Content × M → Section dividers → Data/KPI → Closing
- Per-slide purpose: one clear message per slide
- At least 1–2 dark accent slides for visual rhythm (see guidelines-slides.md Rule 2)
- Which slides contain data that warrant SVG charts (see guidelines-slides.md Rule 3)

### 1.2 Plan Canvas Grid Layout

Each slide frame is **1920 × 1080** px. Lay slides out on the canvas in a grid:
- **Max 5 slides per row**
- Horizontal gap between slides: **100px**
- Vertical gap between rows: **100px**

For N slides:
- `rows = ceil(N / 5)`
- `totalWidth = min(N, 5) × 1920 + (min(N, 5) - 1) × 100`
- `totalHeight = rows × 1080 + (rows - 1) × 100`

---

## Phase 2: Canvas Setup

### 2.1 Locate Available Space

Call `locate_available_space` with `totalWidth` and `totalHeight` from Phase 1.2. Record the returned `space.x` and `space.y` as the grid origin.

### 2.2 Create All Slide Frames in One Batch

Use `batch_edit` (≤25 ops per call; split into multiple calls if N > 25) to create all slide frames up front.

For slide at grid position `(row, col)` where `row = floor(i / 5)` and `col = i % 5`:
- `x = space.x + col × (1920 + 100)`
- `y = space.y + row × (1080 + 100)`

Each frame must set:
- `width: 1920, height: 1080`
- `clipsContent: true`
- Meaningful `name` (e.g., `"Slide 3 - Market Size"`)
- Base `fill` from the style guide (avoid pure white/black — see guidelines-slides.md Rule 2)

Example:
```javascript
slide1=I(document, {type: "frame", name: "Slide 1 - Cover", width: 1920, height: 1080, clipsContent: true, x: X1, y: Y1, fills: [/* gradient from style guide */]})
slide2=I(document, {type: "frame", name: "Slide 2 - Agenda", width: 1920, height: 1080, clipsContent: true, x: X2, y: Y2, fills: [/* gradient from style guide */]})
// ... continue for all N slides
```

**Do NOT populate slide content in this phase.** Only create the empty frames.

---

## Phase 3: Slide Generation

Generate slides **one at a time, sequentially**. For each slide `i` from 1 to N, run this sub-loop:

### 3.1 Generate Slide Content

Call `batch_edit` (≤25 ops) to add content into slide `i`'s frame. Build order:
1. **Background layer** — gradient fill + decorative pattern (Rule 2)
2. **Structure** — title area, content area, footer/page number
3. **Content** — titles, body text, data elements (with font sizes from Rule 1)
4. **Decoration** — 2–3 decorative elements per slide (Rule 3)
5. **Charts** — if data is present, inline SVG chart (Rule 3)

If a single slide needs more than 25 ops, split into multiple sequential `batch_edit` calls on the same frame.

### 3.2–3.4 Verify & Fix

Follow the **Post-Generation Validation Pattern** in `design-rules.md`:
1. `capture_screenshot` on slide `i` — check text readability (Rule 1), background richness (Rule 2), decorative elements (Rule 3), color consistency
2. `capture_layout` on slide `i` with `problemsOnly: true` — check overlapping, clipping, misalignment
3. If issues found → `batch_edit` corrections → re-run 1 + 2

Only advance to slide `i+1` after the current slide passes both checks.

---

## Phase 4: Final Review

After all N slides have passed their per-slide checks:

### 4.1 Deck-Level Screenshot

Screenshot each slide one more time to compare neighbors side-by-side. Verify:
- Consistent palette across all slides (Rule 2)
- Dark accent slides appear at planned positions
- Typography hierarchy is uniform (same title/body sizes across similar slide types)

### 4.2 Final Fixes

For any cross-slide inconsistencies, issue fix-up `batch_edit` calls and re-screenshot. Stop only when the full deck is visually cohesive.
