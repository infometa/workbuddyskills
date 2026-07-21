# Ardot Design-to-Frontend-Code Workflow

This document covers the complete workflow for pixel-perfect conversion of .ardot design files into frontend HTML/CSS/JS code. It applies to slide presentations, landing pages, showcase pages, and other multi-page/multi-screen designs.

## Workflow Overview

```markdown
Phase 1: Design Analysis (read design file structure and style data)
    ↓
Phase 2: Asset Export (export image and SVG vector resources)
    ↓
Phase 3: Code Generation (HTML structure + CSS styles + JS interactions)
    ↓
Phase 4: Verification & Preview (local server preview and comparison)
```

---

## Phase 1: Design Analysis

### Step 1.1: Get Editor State

```markdown
fetch_editor_state() → understand canvas state, current page, top-level nodes, available components
```
Read `references/guidelines-code.md` to get code generation guidelines. (`references/guidelines-tailwind.md` optional for Tailwind)

**Key information to extract:**
- Identify each top-level frame as an independent page/slide
- Record each frame's `name`, `width`, `height`, `x`, `y`
- Understand page ordering (typically arranged left-to-right by x coordinate, top-to-bottom by y coordinate)

### Step 1.2: Scan Exportable Resources

```
scan_exportable_resources() → get all image nodes and SVG vector nodes
```

**Returns two lists:**
- `image`: nodes with image fills (export as PNG/JPEG/WEBP)
- `svg`: nodes with only vector/shape elements (export as SVG)

**Critical decision principles:**
- **Only export image nodes** (background images, scene images, character art, screenshots, etc.) — do NOT export entire slides/pages as images
- SVG decorative elements (corner decorations, dividers, icons, etc.) should be exported separately as SVG format
- Elements achievable with pure CSS (solid rectangles, gradients, simple borders) do not need exporting — reproduce them with code

### Step 1.3: Deep Read Each Page

Call separately for each page frame:

```markdown
batch_read(nodeIds: ["<frameId>"], readDepth: 10, resolveVariables: true)
```

**Read all pages in parallel** for efficiency. Extract the following key information:

| Category | Extraction Method | Purpose |
|----------|------------------|---------|
| Node hierarchy | Recursive `children` traversal | HTML DOM structure mapping |
| Layout mode | `layoutMode` (HORIZONTAL/VERTICAL/NONE) | CSS flex direction |
| Dimensions | `width`, `height` | CSS width/height |
| Positioning | `x`, `y`, `layoutPositioning` | CSS positioning method |
| Spacing | `itemSpacing`, `padding*` | CSS gap/padding |
| Alignment | `primaryAxisAlignItems`, `counterAxisAlignItems` | CSS justify/align |
| Clipping | `clipsContent` | CSS overflow |

### Step 1.4: Read Style Details

Call with `properties: [...]` for key nodes (text, decorative frames, backgrounds) to get complete styles:

```
batch_read(nodeIds: [...textIds, ...bgIds], readDepth: 0, properties: ["fills", "strokes", "effects", "cornerRadius", "opacity"])
```

**Required text node properties:**

| Property | CSS Mapping | Notes |
|----------|------------|-------|
| `fontSize` | `font-size` | Direct mapping |
| `fontName.family` | `font-family` | Note the font family name |
| `fontName.style` | `font-weight` | Regular→400, Medium→500, Bold→700 |
| `fills[0].color` | `color` | RGB 0~1 range, convert to hex |
| `letterSpacing.value` | `letter-spacing` | Note unit: PIXELS/PERCENT |
| `lineHeight` | `line-height` | AUTO or {value, unit} |
| `textAlignHorizontal` | `text-align` | LEFT/CENTER/RIGHT |
| `opacity` | `opacity` | Node-level opacity |
| `textAutoResize` | Affects wrapping behavior | HEIGHT → requires width to be set |

**Required frame/background node properties:**

| Property | CSS Mapping | Notes |
|----------|------------|-------|
| `fills` | `background` | SOLID→solid color, GRADIENT→gradient, IMAGE→background image |
| `fills[].opacity` | Fill opacity | Different from node opacity |
| `opacity` | `opacity` | Node-level opacity, affects entire element including children |
| `strokes` | `border` | Color, weight, position |
| `cornerRadius` | `border-radius` | |
| `effects` | `box-shadow`/`filter` | DROP_SHADOW/BLUR |
| `clipsContent` | `overflow: hidden` | |

### Step 1.5: Screenshot Each Page

```
capture_screenshot(nodeIds: ["<frameId>", ...]) → get visual references for all pages in one call
```

**Screenshot all pages in parallel.** Carefully analyze screenshots to understand:
- Overall color tone and atmosphere
- Element layering relationships
- Image positioning and cropping behavior
- Decorative element visual effects

---

## Phase 2: Asset Export

### Step 2.1: Create Output Directories

```bash
mkdir -p <project>/assets/images <project>/assets/svg
```

### Step 2.2: Export Image Assets

```
export_nodes(nodeIds: [...imageNodeIds], outputDir: "<project>/assets/images", format: "png", scale: 1)
```

**Key rules:**
- For SVG format there is no limit on the number of nodes per call. 
- For image formats (PNG/JPEG/WEBP), it is recommended to export no more than 5 nodes per batch, split into batches if exceeding
- Only export nodes from the `image` list returned by `scan_exportable_resources`
- **Do NOT export entire slide/page frames** — only export image nodes within them (backgrounds, scenes, etc.)
- Use `scale: 1` for background images (original size is sufficient; larger sizes slow down loading)
- Use `scale: 2` for small icons/graphics to maintain clarity
- If an image node export fails, reduce batch size and retry

### Step 2.3: Export SVG Vector Assets

call `export_nodes` with parameters (nodeIds: [...svgNodeIds], outputDir: "<project>/assets/svg", format: "svg")

**SVG export rules:**
- SVG always uses 1x scale (unaffected by the scale parameter)
- Suitable for SVG export: corner decorations, dividers, icons, emblems, arrows, etc.
- Not suitable for SVG export: nodes with image fills, complex lighting effects

### Step 2.4: Naming Conventions

Exported files automatically use `nodeId` as the filename (colons replaced with underscores), e.g., `2_5.svg`.
It is recommended to preserve semantic names in code via comments or variable names for maintainability:

```html
<!-- Corner Decor Top Left -->
<img src="assets/svg/2_5.svg" alt="">
```

---

## Phase 3: Code Generation

### Step 3.1: Project Structure

```markdown
<project>/
├── index.html          # Main page
├── style.css           # Stylesheet
├── script.js           # Interaction logic
└── assets/
    ├── images/         # PNG/JPEG images
    └── svg/            # SVG vectors
```

For complex projects, expand to:
```markdown
├── css/
│   ├── reset.css
│   ├── variables.css   # CSS variables
│   ├── slides.css      # Per-page styles
│   └── nav.css         # Navigation styles
├── js/
│   ├── main.js
│   └── slide-nav.js
```

### Step 3.2: CSS Variable Extraction

use `fetch_variables()` to extract variables from the design.
Extract frequently reused colors, fonts, etc. from the design and define as CSS variables:

```css
:root {
  /* Converted from fills[0].color RGB 0~1 values */
  --bg: #0D0A0F;           /* r:0.05, g:0.04, b:0.06 */
  --gold: #D4AF37;         /* r:0.83, g:0.69, b:0.22 */
  --white: #FFFFFF;
  --gray: #A0A0A0;         /* r:0.63, g:0.63, b:0.63 */
  --dark-gray: #666666;    /* r:0.40, g:0.40, b:0.40 */
}
```

**Color conversion formula:** `hex = Math.round(floatValue * 255).toString(16)`

### Step 3.3: Design-to-CSS Mapping Rules

#### Layout Mapping

| Ardot Property | CSS Property | Conversion Notes |
|---------------|-------------|-----------------|
| `layoutMode: "HORIZONTAL"` | `display: flex; flex-direction: row;` | |
| `layoutMode: "VERTICAL"` | `display: flex; flex-direction: column;` | |
| `layoutMode: "NONE"` | `position: relative;` (children use absolute) | |
| `itemSpacing` | `gap` | Direct pixel mapping |
| `primaryAxisAlignItems: "CENTER"` | `justify-content: center;` | |
| `primaryAxisAlignItems: "SPACE_BETWEEN"` | `justify-content: space-between;` | |
| `counterAxisAlignItems: "CENTER"` | `align-items: center;` | |
| `layoutGrow: 1` | `flex: 1;` | |
| `width: "fill_container"` | `flex: 1;` or `width: 100%;` | Context-dependent |
| `height: "hug_contents"` | `height: auto;` or `height: fit-content;` | |
| `clipsContent: true` | `overflow: hidden;` | |
| `padding: [top, right, bottom, left]` | `padding` | |

#### Text Mapping

| Ardot Property | CSS Property |
|---------------|-------------|
| `fontSize: 96` | `font-size: 96px;` |
| `fontWeight: "700"` | `font-weight: 700;` |
| `letterSpacing: {value: 24, unit: "PIXELS"}` | `letter-spacing: 24px;` |
| `lineHeight: {value: 36, unit: "PIXELS"}` | `line-height: 36px;` |
| `lineHeight: {unit: "AUTO"}` | (omit or `line-height: normal;`) |
| `textAlignHorizontal: "CENTER"` | `text-align: center;` |

#### Fill/Background Mapping

| Ardot Fill Type | CSS Implementation |
|----------------|-------------------|
| `type: "SOLID"` | `background-color: #hex;` |
| `type: "IMAGE"` + `scaleMode: "FILL"` | `background-image` or `<img>` + `object-fit: cover;` |
| `type: "GRADIENT_LINEAR"` | `background: linear-gradient(...)` |
| `type: "GRADIENT_RADIAL"` | `background: radial-gradient(...)` |
| Node `opacity: 0.35` with IMAGE fill | Set `opacity: 0.35;` on the wrapper container |

**Gradient conversion details:**

`gradientTransform: [[0, -1, 1], [1, 0, 0]]` represents a bottom-to-top direction.

Common gradientTransform to CSS direction mapping:
- `[[0, -1, 1], [1, 0, 0]]` → `linear-gradient(to top, ...)`
- `[[1, 0, 0], [0, 1, 0]]` → `linear-gradient(to right, ...)`
- `[[0, 1, 0], [-1, 0, 1]]` → `linear-gradient(to bottom, ...)`

In gradientStops, `color.a` controls color transparency, and `position` corresponds to the percentage position in CSS.

### Step 3.4: HTML Structure Generation

**Principle: Preserve the design's layer hierarchy**

```markdown
Design Frame Hierarchy     →    HTML Hierarchy
─────────────────────      ────────────────────
Slide 01 - Cover           <section class="slide slide-01">
  ├── Hero Background        <div class="hero-bg"><img></div>
  ├── Top Gradient           <div class="gradient-top"></div>
  ├── Center Content         <div class="center-content">
  │   ├── Subtitle Top          <p class="subtitle-top">...</p>
  │   ├── Main Title            <h1 class="main-title">...</h1>
  │   └── Tagline              <p class="tagline">...</p>
  └── Bottom Info            <div class="bottom-info">...</div>
```

**Naming rules:**
- Convert the design's `name` property to CSS class names (CamelCase to kebab-case)
- e.g., `"Center Content"` → `.center-content`
- e.g., `"Hero Background"` → `.hero-bg`

**Image references:**
- Image fill nodes → `<img src="assets/images/2_xxx.png">`
- SVG decorative nodes → `<img src="assets/svg/2_xxx.svg">`
- Pure CSS elements (gradients, solid rectangles) → no images needed, implement with CSS

### Step 3.5: Multi-Page/Slide Transition Effects

For slide-style designs, implement page transition effects:

**HTML structure:**
```html
<div class="slides-wrapper">
  <section class="slide slide-01">...</section>
  <section class="slide slide-02">...</section>
  ...
</div>
<div class="nav-controls">
  <button class="prev-btn">‹</button>
  <div class="slide-indicators">...</div>
  <button class="next-btn">›</button>
</div>
```

**CSS transition animation:**
```css
.slide {
  position: absolute;
  width: 1920px; height: 1080px;
  opacity: 0;
  transition: opacity 0.8s ease, transform 0.8s ease;
  pointer-events: none;
}
.slide.active { opacity: 1; pointer-events: auto; z-index: 2; }
.slide.prev { opacity: 0; transform: translateX(-100px) scale(0.95); }
.slide.next { opacity: 0; transform: translateX(100px) scale(0.95); }
```

**JS interaction key points:**
- Keyboard navigation (←/→, ↑/↓, Space, PageUp/PageDown)
- Mouse wheel navigation (with throttle/debounce)
- Touch swipe navigation (mobile support)
- Dot indicator click-to-jump
- Responsive window scaling (preserve original design aspect ratio)

**Responsive scaling core logic:**
```javascript
const scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
const offsetX = (window.innerWidth - 1920 * scale) / 2;
const offsetY = (window.innerHeight - 1080 * scale) / 2;
slide.style.transform = `scale(${scale})`;
slide.style.left = offsetX + 'px';
slide.style.top = offsetY + 'px';
slide.style.transformOrigin = 'top left';
```

---

## Phase 4: Verification & Preview

### Step 4.1: Start Local Server

```bash
cd <project> && python3 -m http.server <port>
```

Or using Node.js:
```bash
npx serve <project> -p <port>
```

### Step 4.2: Preview and Compare

Use `preview_url` to preview in the IDE's built-in browser, comparing page-by-page against design screenshots:

**Checklist:**
- [ ] Background colors/images are correct
- [ ] Text content, size, color, and spacing match exactly
- [ ] Layout and alignment match the design (flex direction, alignment mode)
- [ ] Images load correctly with proper cropping (object-fit: cover)
- [ ] Decorative elements (SVG corner ornaments, dividers) are correctly positioned and sized
- [ ] Gradient directions and colors are correct
- [ ] Opacity effects are faithfully reproduced
- [ ] Page transition interactions are smooth
- [ ] Window scaling maintains correct proportions

---

## Lessons Learned & Best Practices

### Parallelization Strategy

The following steps throughout the workflow should be parallelized whenever possible for significant efficiency gains:
- All pages' `batch_read` calls in parallel
- All pages' `capture_screenshot` calls in parallel
- Text node and frame node `fullData` reads in parallel
- Image and SVG exports in parallel batches

### Image Export Strategy

- **Only export image nodes**: Use `scan_exportable_resources` to identify which nodes are images
- **Do NOT export entire slides**: Slides are composed of images + text + decorations; exporting the whole slide as an image loses editability
- **Batch exports**: `export_nodes` supports max 10 nodes per call; 5 per batch is more stable in practice
- **Create directories first**: Ensure target directories exist before exporting; otherwise exports may fail
- **Retry on failure**: Reducing batch size and retrying usually resolves export failures

### Color Value Conversion

Design files use 0~1 float values for colors; these must be converted to CSS hex values:

```javascript
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(v => 
    Math.round(v * 255).toString(16).padStart(2, '0')
  ).join('').toUpperCase();
}
// Example: {r: 0.831, g: 0.686, b: 0.216} → #D4AF37
```

### Common Opacity Handling

Design files contain two types of opacity:
1. **Node opacity**: e.g., background image frame `opacity: 0.35`, affects the entire element → CSS `opacity: 0.35`
2. **Fill opacity**: e.g., `fills[0].opacity: 0.8`, affects only the fill → CSS `rgba()` or opacity on the fill
3. **Gradient color alpha**: e.g., `color.a: 0`, controls gradient endpoint transparency → CSS `rgba(r, g, b, 0)`

### Absolute Positioning Elements

In frames with `layoutMode: "NONE"` or children has `layoutPosition: "ABSOLUTE"`, use `x`, `y` for absolute positioning:

```css
.parent { position: relative; }
.child {
  position: absolute;
  left: <x>px;
  top: <y>px;
  width: <width>px;
  height: <height>px;
}
```

### Gradient Overlay Common Patterns

Designs frequently use gradient overlays to enhance text readability:

```css
/* Top-down gradient darkening */
.gradient-top {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 400px;
  background: linear-gradient(to bottom, var(--bg), transparent);
}

/* Left-side gradient darkening (for text overlaid on images) */
.dark-overlay-left {
  position: absolute;
  top: 0; left: 0;
  width: 900px; height: 100%;
  background: linear-gradient(to right, rgba(13, 10, 15, 0.95), transparent);
}
```

### Letter Spacing Handling

The `letterSpacing` unit in design files can be `PIXELS` or `PERCENT`:
- `PIXELS` → use directly as `letter-spacing: <value>px`
- `PERCENT` → convert to `letter-spacing: <value/100>em`

### Decorative Border Lines Implementation

Double-line borders in design files are often implemented with two RECTANGLE nodes; CSS can use `::before`/`::after` pseudo-elements:

```css
.border-decor-top::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 2px;
  background: var(--gold);
}
.border-decor-top::after {
  content: '';
  position: absolute;
  top: 4px; left: 60px;
  width: calc(100% - 120px); height: 1px;
  background: rgba(212, 175, 55, 0.3);
}
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Image export fails | Batch too large or directory missing | Run `mkdir -p` first; reduce to 5 per batch |
| Text styles don't match | fullData not read | Re-read text nodes with `fullData: true` |
| Gradient direction wrong | gradientTransform misinterpreted | Cross-reference with the mapping table |
| Opacity stacking anomaly | Node opacity and fill opacity confused | Handle the two opacity types separately |
| Layout misaligned | Flex property mapping error | Verify primaryAxis/counterAxis mapping |
| SVG not displaying | Path error or viewBox issue | Check export path and SVG content |
| Responsive scaling offset | transformOrigin set incorrectly | Ensure it is set to `top left` |
