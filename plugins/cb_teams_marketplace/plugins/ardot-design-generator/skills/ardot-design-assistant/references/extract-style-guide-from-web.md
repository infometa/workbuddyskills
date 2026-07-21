# Website-to-Design-Guide Extraction Workflow

This reference documents the complete workflow for extracting a website's visual design language and producing a structured, production-grade design style guide in an .ardot file.

## When to Use

Activate this workflow when the user provides a website URL and asks to:
- Generate a design style guide from a website
- Extract design tokens / design system from a URL
- Convert a website's visual style into a design specification
- Analyze and document a website's design language
- 将网站设计风格转为设计稿/设计指南
- 提取网站的配色/字体/组件规范

## Overview

The workflow has **4 phases**:

```
Phase 0: Ensure Design File Is Open (create or open an .ardot file)
    ↓
Phase 1: Website Analysis (extract raw design data)
    ↓
Phase 2: Design Token Creation (create reusable variables)
    ↓
Phase 3: Design Guide Assembly (build the guide frame-by-frame)
    ↓
Phase 4: Verification (screenshot each section)
```

---

## Phase 0: Ensure Design File Is Open

Before any canvas operation, make sure an Ardot design file is loaded:
- **`create_design`** — Create a new blank file for the style guide. Optionally accepts a `fileName`.
- **`open_design`** — Open an existing file by URL or file ID.
- If the editor already has a file loaded → skip this phase.

---

## Phase 1: Website Analysis

### Goal
Extract all visual design information from the target website: colors, fonts, spacing, layout patterns, component styles, and overall aesthetic direction.

### Step 1.1: Fetch HTML Source

Use `curl` or `WebFetch` to retrieve the page HTML:

```bash
curl -sL "https://example.com" 2>&1 | head -500
```

From the HTML, identify:
- **Meta theme-color** — often reveals the brand accent color
- **CSS file paths** — `<link href="css/app.xxx.css">`
- **Font references** — `@font-face` declarations, Google Fonts links
- **Framework** — Vue SPA, React, static HTML, etc.

### Step 1.2: Fetch and Parse CSS

Download the main CSS file and extract design tokens:

```bash
# Get CSS variables (colors, spacing, fonts)
curl -sL "https://example.com/css/app.xxx.css" | tr ';' '\n' | grep -E '^\s*--' | sort -u

# Get font families
curl -sL "https://example.com/css/app.xxx.css" | tr ';' '\n' | grep -i 'font-family' | sort -u

# Get font sizes
curl -sL "https://example.com/css/app.xxx.css" | tr ';' '\n' | grep -i 'font-size' | sort -u

# Get @font-face declarations
curl -sL "https://example.com/css/app.xxx.css" | tr '{' '\n' | grep '@font-face' -A5
```

Key data to extract:
- **CSS custom properties** (`--theme-color`, `--bg-color`, etc.)
- **Color values** (hex, rgb, hsl)
- **Font families** (primary/display font, body font, CJK font fallbacks)
- **Font sizes** (establish the type scale)
- **Border radius values**
- **Spacing/padding patterns**

### Step 1.3: Take Screenshots

Use Playwright to capture the full page and viewport screenshots:

```bash
# Full page screenshot
npx playwright screenshot --wait-for-timeout 5000 --full-page "https://example.com" /tmp/site_full.png

# Viewport screenshot (hero section)
npx playwright screenshot --wait-for-timeout 5000 --viewport-size=1440,900 "https://example.com" /tmp/site_hero.png
```

If Playwright is not installed, use `npx playwright install chromium` first.

Analyze screenshots for:
- Overall color scheme (dark/light, accent colors)
- Typography style (serif/sans-serif, bold/light, uppercase patterns)
- Layout patterns (grid, full-width sections, sidebar)
- Component styles (buttons, cards, navigation)
- Visual effects (gradients, shadows, textures, patterns)
- Spacing density (tight/airy)
- Corner radius patterns (sharp/rounded/pill)

### Step 1.4: Synthesize Design Language

Compile findings into a structured brief:

| Category | Extracted Value | Design Decision |
|----------|----------------|-----------------|
| Primary BG | `#171717` | Deep black background |
| Accent | `#17F700` | Neon green for highlights |
| Text Primary | `#F7F7F7` | Near-white for readability |
| Eng Font | Custom sans-serif | Use Inter as closest match |
| ZH Font | 思源黑体 | Source Han Sans / fallbacks |
| Radius | 0px main, 100px buttons | Sharp containers, pill buttons |
| Style | Dark, high-contrast, techy | Brutalist + neon aesthetic |

---

## Phase 2: Design Token Creation

### Goal
Create a reusable variable set in the .ardot file using `apply_variables`.

### Step 2.1: Define Variable Structure

Organize tokens into logical groups:

```json
{
  "<ProjectName> Design Tokens": {
    "modes": ["Default"],
    "variables": {
      "theme-primary": { "type": "COLOR", "value": {...}, "scopes": ["ALL_FILLS"] },
      "theme-accent": { "type": "COLOR", "value": {...}, "scopes": ["ALL_FILLS"] },
      "theme-surface": { "type": "COLOR", "value": {...}, "scopes": ["ALL_FILLS"] },
      "text-primary": { "type": "COLOR", "value": {...}, "scopes": ["TEXT_FILL"] },
      "text-secondary": { "type": "COLOR", "value": {...}, "scopes": ["TEXT_FILL"] },
      "text-muted": { "type": "COLOR", "value": {...}, "scopes": ["TEXT_FILL"] },
      "border-default": { "type": "COLOR", "value": {...}, "scopes": ["STROKE"] },
      "spacing-xs": { "type": "FLOAT", "value": 4, "scopes": ["GAP"] },
      "spacing-sm": { "type": "FLOAT", "value": 8, "scopes": ["GAP"] },
      "spacing-md": { "type": "FLOAT", "value": 16, "scopes": ["GAP"] },
      "spacing-lg": { "type": "FLOAT", "value": 24, "scopes": ["GAP"] },
      "spacing-xl": { "type": "FLOAT", "value": 32, "scopes": ["GAP"] },
      "spacing-2xl": { "type": "FLOAT", "value": 48, "scopes": ["GAP"] },
      "spacing-3xl": { "type": "FLOAT", "value": 64, "scopes": ["GAP"] },
      "radius-none": { "type": "FLOAT", "value": 0, "scopes": ["CORNER_RADIUS"] },
      "radius-sm": { "type": "FLOAT", "value": 4, "scopes": ["CORNER_RADIUS"] },
      "radius-md": { "type": "FLOAT", "value": 8, "scopes": ["CORNER_RADIUS"] },
      "radius-lg": { "type": "FLOAT", "value": 12, "scopes": ["CORNER_RADIUS"] },
      "radius-pill": { "type": "FLOAT", "value": 100, "scopes": ["CORNER_RADIUS"] }
    }
  }
}
```

### Token naming conventions
- Colors: `theme-*` for brand, `text-*` for text fills, `border-*` for strokes
- Spacing: `spacing-xs/sm/md/lg/xl/2xl/3xl` (4/8/16/24/32/48/64)
- Radius: `radius-none/sm/md/lg/pill`
- COLOR values must be `{r, g, b, a}` with 0–1 range, NOT hex strings

---

## Phase 3: Design Guide Assembly

### Goal
Build the design guide as a single vertical frame containing all specification sections.

### Step 3.1: Get Editor State & Find Space

```
fetch_editor_state(includeSchema: false)   → understand canvas state
locate_available_space(width: 1440, height: 5000)  → find placement
```

### Step 3.2: Create Main Container

```javascript
page=I(document, {type: "frame", name: "<ProjectName> Design Style Guide", layout: "vertical", width: 1440, height: "hug_contents", fill: "<bg-color>", padding: [80, 100], gap: 80})
```

The main frame uses the website's background color as `fill`. All child sections use `fills: []` (transparent) to inherit the parent background.

### Step 3.3: Build Sections

Build sections in this order (each as a separate `batch_edit` call, ≤ 25 ops):

#### Section Pattern (reuse for each)

Each section follows this structure:

```javascript
section=I("<pageId>", {type: "frame", name: "<Section Name>", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 40, fills: []})
sectionTag=I(section, {type: "text", name: "Section Tag", content: "0N — SECTION TITLE", fontSize: 14, fontWeight: "500", letterSpacing: 4, fill: "<accent-color>", fontName: {family: "Inter", style: "Medium"}})
sectionHeading=I(section, {type: "text", name: "Section Heading", content: "中文标题", fontSize: 48, fontWeight: "700", fill: "<text-primary>", fontName: {family: "Inter", style: "Bold"}})
sectionDesc=I(section, {type: "text", name: "Section Description", content: "描述文字...", fontSize: 16, fontWeight: "400", fill: "<text-secondary>", width: "fill_container", textAutoResize: "HEIGHT", lineHeight: 28, fontName: {family: "Inter", style: "Regular"}})
```

---

### Section 1: Color Palette (`01 — COLOR PALETTE`)

**Structure:**
- Section header (tag + heading + description)
- Primary color swatches row (horizontal, `fill_container` width)
  - For each color: swatch frame (160px height) + label + hex + RGB + usage text
- Auxiliary gray scale row

**Color Swatch Card Pattern:**

```javascript
card=I(colorRow, {type: "frame", name: "Color Card - <Name>", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 16, fills: []})
swatch=I(card, {type: "frame", name: "<Name> Swatch", layout: "none", width: "fill_container", height: 160, fill: "<color-hex>"})
label=I(card, {type: "text", name: "<Name> Label", content: "<Color Name>", fontSize: 18, fontWeight: "600", fill: "<text-primary>", fontName: {family: "Inter", style: "SemiBold"}})
hex=I(card, {type: "text", name: "<Name> Hex", content: "<#HEXVAL>", fontSize: 14, fill: "<text-muted>", fontName: {family: "Inter", style: "Regular"}})
rgb=I(card, {type: "text", name: "<Name> RGB", content: "RGB <r>, <g>, <b>", fontSize: 12, fill: "<text-muted>", fontName: {family: "Inter", style: "Regular"}})
usage=I(card, {type: "text", name: "<Name> Usage", content: "用途说明", fontSize: 12, fill: "<text-secondary>", fontName: {family: "Inter", style: "Regular"}})
```

**Gray Scale Pattern:**
- Smaller swatches (60px height) in horizontal row
- Each with hex label below

---

### Section 2: Typography (`02 — TYPOGRAPHY`)

**Structure:**
- Section header
- English font display box (bordered frame with padding)
  - Font family label (accent color, 12px, uppercase)
  - Display/H1/H2/Body/Caption samples at actual sizes
- CJK font display box (same pattern)
- Type scale table

**Font Display Box Pattern:**

```javascript
fontBox=I(typoSection, {type: "frame", name: "English Font Display", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 16, padding: [32, 32], fills: [], strokes: [{type: "SOLID", color: {r: 0.2, g: 0.2, b: 0.2, a: 1}}], strokeWeight: 1})
fontLabel=I(fontBox, {type: "text", content: "ENG — <Font Family>", fontSize: 12, fontWeight: "500", letterSpacing: 2, fill: "<accent-color>"})
displaySample=I(fontBox, {type: "text", content: "SAMPLE TEXT", fontSize: 72, fontWeight: "900", fill: "<text-primary>", letterSpacing: -2})
bodySample=I(fontBox, {type: "text", content: "Body text sample...", fontSize: 16, fill: "<text-secondary>", lineHeight: 28, width: "fill_container", textAutoResize: "HEIGHT"})
```

**Type Scale Table Pattern:**

```javascript
scaleTable=I(typoSection, {type: "frame", name: "Type Scale Table", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 0, fills: []})
// For each row:
row=I(scaleTable, {type: "frame", name: "Scale Row", layout: "horizontal", width: "fill_container", height: "hug_contents", padding: [16, 0], gap: 24, fills: [], counterAxisAlignItems: "CENTER", strokes: [{type: "SOLID", color: {r: 0.2, g: 0.2, b: 0.2, a: 1}}], strokeWeight: 1, strokeAlign: "OUTSIDE"})
level=I(row, {type: "text", content: "Display", fontSize: 14, fontWeight: "500", fill: "<accent>", width: 120})
size=I(row, {type: "text", content: "72–120px", fontSize: 14, fill: "<text-primary>", width: 120})
weight=I(row, {type: "text", content: "Black (900)", fontSize: 14, fill: "<text-secondary>", width: 140})
usage=I(row, {type: "text", content: "首屏标题", fontSize: 14, fill: "<text-muted>"})
```

**Standard type scale levels:** Display, H1, H2, H3, Body, Caption

---

### Section 3: Components (`03 — COMPONENTS`)

**Structure:**
- Section header
- Button subsection: label + horizontal row of button variants
- Card subsection: label + horizontal row of card examples
- Description notes for each subsection

**Button Pattern:**

```javascript
// Primary button (filled)
btn=I(btnRow, {type: "frame", name: "Button - Primary", layout: "horizontal", width: "hug_contents", height: "hug_contents", padding: [14, 40], fill: "<accent>", cornerRadius: <radius>, primaryAxisAlignItems: "CENTER", counterAxisAlignItems: "CENTER"})
btnText=I(btn, {type: "text", content: "LABEL", fontSize: 14, fontWeight: "600", fill: "<contrast-text>", letterSpacing: 2})

// Outline button (stroked)
btnO=I(btnRow, {type: "frame", name: "Button - Outline", layout: "horizontal", width: "hug_contents", height: "hug_contents", padding: [14, 40], fills: [], cornerRadius: <radius>, strokes: [{type: "SOLID", color: {...}}], strokeWeight: 2})

// Ghost button (light stroke)
btnG=I(btnRow, {type: "frame", name: "Button - Ghost", layout: "horizontal", ..., strokes: [{type: "SOLID", color: {...}}], strokeWeight: 1})
```

**Card Pattern:**

```javascript
card=I(cardRow, {type: "frame", name: "Card Example", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 0, fills: [], cornerRadius: <radius>, strokes: [{type: "SOLID", color: {...}}], strokeWeight: 1})
cardImg=I(card, {type: "frame", name: "Card Image", layout: "none", width: "fill_container", height: 200, fill: "<surface-dark>"})
cardBody=I(card, {type: "frame", name: "Card Body", layout: "vertical", width: "fill_container", height: "hug_contents", padding: 20, gap: 12, fills: []})
cardNum=I(cardBody, {type: "text", content: "01", fontSize: 14, fontWeight: "700", fill: "<accent>"})
cardTitle=I(cardBody, {type: "text", content: "Title", fontSize: 20, fontWeight: "600", fill: "<text-primary>"})
cardDesc=I(cardBody, {type: "text", content: "Description", fontSize: 14, fill: "<text-muted>"})
```

Optionally use `G()` to add stock/AI images to card image areas.

---

### Section 4: Spacing & Radius (`04 — SPACING & RADIUS`)

**Structure:**
- Section header
- Spacing visualization row (green bars of increasing width)
- Radius visualization row (bordered shapes with different corner radii)

**Spacing Bar Pattern:**

```javascript
spGroup=I(spRow, {type: "frame", name: "Spacing <N>", layout: "vertical", width: "hug_contents", height: "hug_contents", gap: 8, fills: [], counterAxisAlignItems: "CENTER"})
spBar=I(spGroup, {type: "frame", name: "<N>px Box", layout: "none", width: <N>, height: 40, fill: "<accent>"})
spLabel=I(spGroup, {type: "text", content: "<N>", fontSize: 12, fill: "<text-muted>"})
```

Standard spacing scale: 4, 8, 16, 24, 32, 48, 64

**Radius Example Pattern:**

```javascript
rdGroup=I(rdRow, {type: "frame", name: "Radius <N> Group", layout: "vertical", width: "hug_contents", height: "hug_contents", gap: 12, fills: [], counterAxisAlignItems: "CENTER"})
rdBox=I(rdGroup, {type: "frame", name: "Radius <N> Box", layout: "none", width: 80, height: 80, fills: [], cornerRadius: <N>, strokes: [{type: "SOLID", color: <accent-color>}], strokeWeight: 2})
rdLabel=I(rdGroup, {type: "text", content: "<N>px\n用途说明", fontSize: 12, fill: "<text-muted>", textAlignHorizontal: "CENTER", textAutoResize: "HEIGHT", width: 100, lineHeight: 18})
```

For pill shapes, use a wider box (160×50) with `cornerRadius: 100`.

---

### Section 5: Design Principles (`05 — DESIGN PRINCIPLES`)

**Structure:**
- Section header
- Wrapped grid of principle cards (3 columns)

**Principle Card Pattern:**

```javascript
pCard=I(pGrid, {type: "frame", name: "Principle <N>", layout: "vertical", width: 380, height: "hug_contents", gap: 16, padding: 32, fills: [], strokes: [{type: "SOLID", color: {...}}], strokeWeight: 1})
pNum=I(pCard, {type: "text", content: "0<N>", fontSize: 48, fontWeight: "900", fill: "<accent>"})
pTitle=I(pCard, {type: "text", content: "原则标题", fontSize: 20, fontWeight: "700", fill: "<text-primary>"})
pDesc=I(pCard, {type: "text", content: "原则描述...", fontSize: 14, fill: "<text-secondary>", lineHeight: 24, width: "fill_container", textAutoResize: "HEIGHT"})
```

Use `layoutWrap: "WRAP"` on the grid container for auto-wrapping.

Common design principles to document:
- Color contrast philosophy
- Animation/motion approach
- Pattern/texture usage
- Typography conventions (uppercase, tracking, etc.)
- Grid/layout system
- Iconography style

---

### Section 6: Layout & Motion (`06 — LAYOUT & MOTION`)

**Structure:**
- Section header
- Two-column info grid (layout spec + motion spec)

**Two-Column Pattern:**

```javascript
grid=I(section, {type: "frame", name: "Info Grid", layout: "horizontal", width: "fill_container", height: "hug_contents", gap: 24, fills: []})
col1=I(grid, {type: "frame", name: "Column 1", layout: "vertical", width: "fill_container", height: "hug_contents", gap: 20, padding: 32, fills: [], strokes: [{...}], strokeWeight: 1})
col1Title=I(col1, {type: "text", content: "页面布局", fontSize: 20, fontWeight: "700", fill: "<text-primary>"})
col1Content=I(col1, {type: "text", content: "• 布局要点1\n• 布局要点2\n...", fontSize: 14, fill: "<text-secondary>", lineHeight: 28, width: "fill_container", textAutoResize: "HEIGHT"})
// Repeat for col2
```

Layout specs to document:
- Page width / content width
- Section structure (full-width, contained, etc.)
- Responsive breakpoints
- Navigation pattern
- Scroll behavior (progress bar, parallax, etc.)

Motion specs to document:
- Animation library (GSAP, CSS, Framer Motion, etc.)
- Entrance animations (clip-path, fade, slide, etc.)
- Hover effects
- Loading animations
- Easing functions and duration ranges

---

### Section 7: Footer

```javascript
divider=I("<pageId>", {type: "frame", name: "Footer Divider", layout: "none", width: "fill_container", height: 3, fill: "<accent>"})
footer=I("<pageId>", {type: "frame", name: "Footer", layout: "horizontal", width: "fill_container", height: "hug_contents", fills: [], primaryAxisAlignItems: "SPACE_BETWEEN", counterAxisAlignItems: "CENTER"})
brand=I(footer, {type: "text", content: "<SITE>.COM", fontSize: 14, fontWeight: "700", fill: "<text-primary>", letterSpacing: 4})
copyright=I(footer, {type: "text", content: "© <Year> <Name>. All Rights Reserved. | Style Guide v1.0", fontSize: 12, fill: "<text-muted>"})
```

---

## Phase 4: Verification

Follow the **Post-Generation Validation Pattern** in `design-rules.md` for each section.

**Do NOT screenshot the entire page** if height exceeds 2000px — screenshot sections individually.

Additional checks specific to style guides:
- [ ] Color swatches display correct hex values
- [ ] Font samples render at intended sizes and weights
- [ ] Buttons show correct fill/stroke patterns
- [ ] Spacing bars match the defined scale (4, 8, 16, 24, 32, 48, 64)
- [ ] Layout wraps properly (principles grid with `layoutWrap: "WRAP"`)

---

## Design Conventions

### Section numbering
Use uppercase English labels with numbering: `01 — COLOR PALETTE`, `02 — TYPOGRAPHY`, etc.

### Text hierarchy within the guide
| Role | Size | Weight | Color |
|------|------|--------|-------|
| Section tag | 14px, Medium | 500 | Accent color |
| Section heading | 48px, Bold | 700 | Text primary |
| Description | 16px, Regular | 400 | Text secondary |
| Subsection label | 20–24px, SemiBold | 600 | Text primary |
| Body/notes | 14px, Regular | 400 | Text muted |
| Swatch label | 18px, SemiBold | 600 | Text primary |
| Hex/RGB value | 12–14px, Regular | 400 | Text muted |

### Frame naming convention
Every node must have a meaningful `name`. Use this pattern:
- Sections: `"Color Palette Section"`, `"Typography Section"`
- Cards: `"Color Card - Green"`, `"Principle 1"`
- Swatches: `"Green Swatch"`, `"Gray 666 Swatch"`
- Text: `"Green Label"`, `"Green Hex"`, `"P1 Title"`
- Rows: `"Color Swatches Row"`, `"Button Examples Row"`

### Accent color as section marker
The website's accent/brand color should be used for:
- Section tag text (e.g., "01 — COLOR PALETTE")
- Principle card numbers
- Spacing bar fills
- Radius example strokes
- Divider lines
- Card numbering in component examples
