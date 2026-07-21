---
name: style-guide
description: Visual design principles and style directives for generating high-quality, non-generic ardot designs — typography, color calibration, layout philosophy, surface treatment, design variance levels, forbidden AI patterns, creative inspiration arsenal, and bento grid paradigm.
metadata:
  tags: ardot, design, style, typography, color, layout, bento-grid, creative
---

# Visual Style Guide

This reference provides visual design principles and style directives for generating high-quality design compositions in ardot. Use these rules to ensure premium, non-generic output.

## 1. BASELINE CONFIGURATION

* **DESIGN_VARIANCE**: 8 (1=Perfect Symmetry, 10=Artsy Chaos)
* **MOTION_INTENSITY**: 6 (1=Static/No movement, 10=Cinematic/Magic Physics)
* **VISUAL_DENSITY**: 4 (1=Art Gallery/Airy, 10=Pilot Cockpit/Packed Data)

The standard baseline for all designs is strictly set to these values (8, 6, 4). Adapt dynamically based on what the user explicitly requests. Use these values as global variables to drive the design logic below.

## 2. TYPOGRAPHY

**Display/Headlines:**
* Large headlines: bold weight, tight tracking, minimal leading.
* **ANTI-SLOP:** Discourage `Inter` for "Premium" or "Creative" vibes. Prefer distinctive typefaces like `Geist`, `Outfit`, `Cabinet Grotesk`, or `Satoshi`.
* **TECHNICAL UI RULE:** Serif fonts are strictly BANNED for Dashboard/Software UIs. Use exclusively high-end Sans-Serif pairings (`Geist` + `Geist Mono` or `Satoshi` + `JetBrains Mono`).

**Body/Paragraphs:**
* Standard body text: neutral gray tone, relaxed leading, max ~65 characters per line for readability.

**Hierarchy Control:**
* Do NOT rely solely on massive scale for hierarchy. Control hierarchy with a combination of weight, color contrast, and spacing.
* Serif fonts ONLY for creative/editorial designs. NEVER use Serif on clean Dashboards.

## 3. COLOR CALIBRATION

* **Constraint:** Max 1 Accent Color. Saturation < 80%.
* **THE LILA BAN:** The "AI Purple/Blue" aesthetic is strictly BANNED. No purple button glows, no neon gradients. Use absolute neutral bases (Zinc/Slate tones) with high-contrast, singular accents (e.g., Emerald, Electric Blue, or Deep Rose).
* **COLOR CONSISTENCY:** Stick to one palette for the entire design. Do not fluctuate between warm and cool grays within the same project.
* **NO Pure Black:** Never use `#000000`. Use Off-Black, Zinc-950, or Charcoal equivalents.
* **NO Oversaturated Accents:** Desaturate accents to blend elegantly with neutrals.

## 4. LAYOUT DIVERSIFICATION

* **ANTI-CENTER BIAS:** Centered Hero/H1 sections are strictly BANNED when `DESIGN_VARIANCE > 4`. Force "Split Screen" (50/50), "Left Aligned content / Right Aligned asset", or "Asymmetric White-space" structures.
* **Grid over Flex-Math:** Prefer CSS Grid-style column structures for reliable, predictable layouts rather than complex percentage math.
* **Contain page layouts** within a max-width boundary (e.g., ~1400px centered) to prevent content from stretching too wide.
* **Responsive consideration:** For high-variance designs, asymmetric layouts on wider viewports MUST fall back to a single-column layout on narrow viewports.

## 5. MATERIALITY, SHADOWS & SURFACE TREATMENT

* **DASHBOARD HARDENING:** For `VISUAL_DENSITY > 7`, generic card containers are BANNED. Use dividers, separators, or purely negative space to group data. Metrics should breathe without being boxed in.
* **Card usage:** Use cards ONLY when elevation communicates hierarchy. When a shadow is used, tint it to the background hue for a natural look.
* **"Liquid Glass" Refraction:** When glassmorphism is needed, go beyond simple blur. Add a 1px inner border (white at ~10% opacity) and a subtle inner shadow to simulate physical edge refraction.
* **NO Neon/Outer Glows:** Do not use default outer glow shadows. Use inner borders or subtle tinted shadows instead.

## 6. DESIGN VARIANCE LEVELS

### DESIGN_VARIANCE (1–10)
* **1–3 (Predictable):** Centered layouts, strict symmetrical grids, equal paddings.
* **4–7 (Offset):** Overlapping elements, varied image aspect ratios (e.g., 4:3 next to 16:9), left-aligned headers over center-aligned data.
* **8–10 (Asymmetric):** Masonry layouts, fractional column grids (e.g., 2fr 1fr 1fr), massive empty zones for dramatic negative space.

### MOTION_INTENSITY (1–10)
* **1–3 (Static):** No automatic animations. Hover and active states only.
* **4–7 (Fluid):** Subtle transitions, staggered load-in sequences.
* **8–10 (Advanced Choreography):** Complex scroll-triggered reveals, parallax depth effects.

### VISUAL_DENSITY (1–10)
* **1–3 (Art Gallery Mode):** Lots of white space. Huge section gaps. Clean and expensive feel.
* **4–7 (Daily App Mode):** Normal spacing for standard apps.
* **8–10 (Cockpit Mode):** Tiny paddings, 1px separators, packed data. Monospace for all numbers.

## 7. INTERACTIVE STATES

Even in static design compositions, plan for full interaction cycles:
* **Loading:** Skeleton loaders matching layout sizes (not generic spinners).
* **Empty States:** Beautifully composed empty states showing how to populate data.
* **Error States:** Clear, inline error indication (especially for forms).
* **Tactile Feedback:** Active states with subtle scale or translate to simulate physical press.

## 8. FORM & DATA PATTERNS

* **Forms:** Label MUST sit above input. Helper text optional. Error text below input. Consistent vertical spacing between input blocks.
* **NO 3-Column Card Layouts:** The generic "3 equal cards horizontally" feature row is BANNED. Use a 2-column Zig-Zag, asymmetric grid, or horizontal scrolling approach.

## 9. AI TELLS — FORBIDDEN PATTERNS

To guarantee premium, non-generic output, strictly avoid these common AI design signatures:

### Visual
* **NO Neon/Outer Glows** — use inner borders or subtle tinted shadows
* **NO Pure Black (#000000)** — use Off-Black or Zinc-950
* **NO Oversaturated Accents** — desaturate to blend with neutrals
* **NO Excessive Gradient Text** — avoid text-fill gradients on large headers
* **NO Custom Mouse Cursors** — outdated and disruptive

### Typography
* **NO Inter Font** — use `Geist`, `Outfit`, `Cabinet Grotesk`, or `Satoshi`
* **NO Oversized H1s** — control hierarchy with weight and color, not massive scale
* **Serif Constraints** — Serif ONLY for creative/editorial, NEVER on Dashboards

### Layout & Spacing
* **Align & Space Perfectly** — padding and margins must be mathematically precise
* **NO 3-Column Equal Cards** — use Zig-Zag, asymmetric grid, or horizontal scroll

### Content & Data (The "Jane Doe" Effect)
* **NO Generic Names** — "John Doe", "Sarah Chan" are banned. Use creative, realistic-sounding names.
* **NO Generic Avatars** — no standard "egg" or user icons. Use creative, believable photo placeholders or specific styling.
* **NO Fake Numbers** — avoid `99.99%`, `50%`. Use organic data (`47.2%`, `+1 (312) 847-1928`).
* **NO Startup Slop Names** — "Acme", "Nexus", "SmartFlow" are banned. Invent premium, contextual brand names.
* **NO Filler Words** — avoid "Elevate", "Seamless", "Unleash", "Next-Gen". Use concrete verbs.

### External Resources
* **NO Broken Unsplash Links** — use reliable placeholders like `https://picsum.photos/seed/{random_string}/800/600` or SVG UI Avatars.

## 10. THE CREATIVE ARSENAL (Design Inspiration)

Do not default to generic UI. Pull from this library of advanced visual concepts:

### Hero Sections
* Stop centering text over a dark image. Try asymmetric heroes: Text aligned to one side. Background with high-quality imagery featuring subtle fade into the background color.

### Navigation & Menus
* Mac OS Dock Magnification — icons scale fluidly on hover
* Magnetic Button — buttons that pull toward the cursor
* Gooey Menu — sub-items detach like viscous liquid
* Dynamic Island — pill-shaped component that morphs for status/alerts
* Contextual Radial Menu — circular menu expanding at click coordinates
* Floating Speed Dial — FAB that springs out secondary actions in a curve
* Mega Menu Reveal — full-screen dropdowns with staggered content

### Layout & Grids
* Bento Grid — asymmetric, tile-based grouping (Apple Control Center style)
* Masonry Layout — staggered grid without fixed row heights (Pinterest style)
* Chroma Grid — grid borders showing subtle animating color gradients
* Split Screen Scroll — two halves sliding in opposite directions
* Curtain Reveal — hero parting in the middle like a curtain

### Cards & Containers
* Parallax Tilt Card — 3D-tilting card tracking mouse position
* Spotlight Border Card — borders illuminating dynamically under cursor
* Glassmorphism Panel — true frosted glass with inner refraction
* Holographic Foil Card — iridescent rainbow reflections shifting on hover
* Tinder Swipe Stack — physical stack of cards users can swipe
* Morphing Modal — button expanding seamlessly into full-screen dialog

### Scroll Animations
* Sticky Scroll Stack — cards sticking to top and stacking over each other
* Horizontal Scroll Hijack — vertical scroll translating into horizontal pan
* Zoom Parallax — central image zooming as user scrolls
* Scroll Progress Path — SVG lines drawing themselves on scroll
* Liquid Swipe Transition — page transitions wiping like viscous liquid

### Galleries & Media
* Dome Gallery — 3D panoramic dome feel
* Coverflow Carousel — 3D carousel with center focused, edges angled
* Drag-to-Pan Grid — boundless grid draggable in any direction
* Accordion Image Slider — narrow strips expanding fully on hover
* Hover Image Trail — mouse leaving a trail of popping/fading images
* Glitch Effect Image — brief RGB-channel shifting on hover

### Typography & Text Effects
* Kinetic Marquee — endless text bands reversing direction on scroll
* Text Mask Reveal — massive typography as transparent window to video
* Text Scramble Effect — matrix-style character decoding on load/hover
* Circular Text Path — text curved along a spinning circular path
* Gradient Stroke Animation — outlined text with gradient running along stroke
* Kinetic Typography Grid — grid of letters dodging/rotating away from cursor

### Micro-Interactions & Effects
* Particle Explosion Button — CTAs shattering into particles on success
* Skeleton Shimmer — shifting light reflections across placeholder boxes
* Directional Hover Aware Button — hover fill entering from mouse entry side
* Ripple Click Effect — waves rippling from click coordinates
* Animated SVG Line Drawing — vectors drawing their own contours
* Mesh Gradient Background — organic, lava-lamp-like animated color blobs
* Lens Blur Depth — dynamic focus blurring background to highlight foreground

## 11. BENTO GRID PARADIGM

When generating modern SaaS dashboards or feature sections, use this "Bento 2.0" architecture:

### Core Design Philosophy
* **Aesthetic:** High-end, minimal, and functional.
* **Palette:** Light background (~#f9fafb). Cards are pure white (#ffffff) with a subtle 1px border.
* **Surfaces:** Large rounded corners (~2.5rem) for major containers. Use a "diffusion shadow" (very light, wide-spreading) for depth without clutter.
* **Typography:** Strict `Geist`, `Satoshi`, or `Cabinet Grotesk` font stack with tight tracking for headers.
* **Labels:** Titles and descriptions placed outside and below cards for clean gallery-style presentation.
* **Spacing:** Generous padding (32–40px) inside cards.

### Card Archetypes for Bento Grids
Suggested layout: Row 1 with 3 columns | Row 2 with 2 columns (70/30 split):

1. **The Intelligent List** — vertical stack with auto-sorting visual, simulating AI-driven prioritization
2. **The Command Input** — search/AI bar with typewriter cycling through prompts, blinking cursor, processing shimmer
3. **The Live Status** — scheduling interface with breathing status indicators and notification badges
4. **The Wide Data Stream** — horizontal infinite carousel of metrics, seamless and effortless
5. **The Contextual UI (Focus Mode)** — document view with staggered highlights and floating action toolbar
