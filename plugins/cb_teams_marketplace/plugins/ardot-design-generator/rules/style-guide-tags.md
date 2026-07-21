# Style Guide Tags — Static Reference

> This is the canonical list of tags accepted by the `fetch_style_guide(tags)` MCP call. The list is **static** — prefer reading this file over calling `fetch_style_guide_tags` so you save one MCP round-trip per session.
>
> Usage: pick 5–10 tags that best match the user's intent (platform + mood + style + color + typography + layout), then pass them to `fetch_style_guide(tags)`.

## Tag Categories

### Platform
`webapp` · `mobile` · `dashboard` · `data-dashboard`

### Tone Mode
`dark-mode` · `light-mode` · `monochrome` · `black-white` · `dual-tone` · `dark-to-light`

### Design Style
`brutalist` · `bauhaus` · `swiss` · `scandinavian` · `japanese` · `nordic` · `zen` · `editorial` · `constructivist` · `architectural` · `publication` · `magazine`

### Texture / Mood
`luxury` · `premium` · `high-end` · `elegant` · `sophisticated` · `refined` · `timeless` · `classical` · `cozy` · `friendly` · `playful` · `approachable` · `warm` · `calm` · `quiet` · `subtle` · `airy`

### Intensity / Expression
`bold` · `confident` · `expressive` · `high-impact` · `high-contrast` · `vibrant` · `colorful` · `bright` · `electric` · `crisp`

### Soft / Natural
`soft` · `organic` · `nature-inspired` · `earthy` · `wellness` · `pastel`

### Color
`neon` · `neon-green` · `primary-colors` · `earth-tones` · `warm-tones`

### Accent Color
`lime-accent` · `gold-accent` · `blue-accent` · `red-accent` · `green-accent` · `orange-accent` · `navy-accent` · `yellow-accent` · `cyan-accent` · `burgundy-accent` · `crimson-accent` · `sage-accent`

### Typography
`serif` · `serif-display` · `serif-sans` · `monospace` · `condensed` · `condensed-type` · `bold-type` · `bold-typography` · `typography` · `typography-only` · `dual-font` · `single-font` · `display` · `italic` · `typographic`

### Letter Case
`uppercase` · `lowercase` · `snake_case`

### Shape
`rounded` · `soft-corners` · `sharp-corners` · `sharp-edged` · `pill-shaped` · `geometric` · `shapes` · `sharp`

### Layout
`bento-grid` · `sidebar` · `dark-sidebar` · `icon-sidebar` · `icon-rail` · `icons-only-nav` · `icon-nav` · `floating-nav` · `numbered-nav` · `masthead` · `flush-layout`

### Industry / Function
`fintech` · `corporate` · `enterprise` · `financial` · `institutional` · `developer` · `devtools` · `cli` · `terminal` · `command-line` · `code-inspired` · `code-native` · `engineering` · `engineered`

### Visual Effects
`gradient` · `mesh-gradient` · `soft-shadows` · `shadowed` · `flat` · `stroke-based` · `ruled-lines` · `color-blocks`

### Tonal Base
`cream` · `ivory` · `parchment` · `off-white` · `champagne` · `stone` · `stone-palette` · `slate` · `terracotta` · `sage-green`

### Mood / Temperament
`minimal` · `minimalist` · `clean` · `precise` · `rational` · `functional` · `literary` · `modern` · `technical` · `professional` · `informational` · `data-focused` · `data-driven` · `executive` · `analytical` · `industrial` · `mechanical` · `urban` · `noir`

### Miscellaneous
`command-center` · `matrix` · `numbered` · `print` · `poster` · `graphic` · `austere` · `humanist` · `badges` · `tactile` · `layered` · `whitespace` · `green-gray` · `paper` · `neutral`

### Navigation / Interaction
`black-stroke`

---

## Selection Guidance

Pick 5–10 tags total, ideally one from each of these axes:
1. **Platform** (1): `webapp` / `mobile` / `dashboard` / ...
2. **Tone mode** (1): `dark-mode` / `light-mode` / `monochrome` / ...
3. **Design style or mood** (1–2): `minimal`, `brutalist`, `editorial`, `playful`, ...
4. **Accent / color** (1–2): `lime-accent`, `earth-tones`, `neon-green`, ...
5. **Typography or shape** (1–2): `serif-display`, `rounded`, `condensed`, ...
6. **Layout / industry hint** (1, optional): `bento-grid`, `sidebar`, `fintech`, ...

Avoid stacking contradictory tags (e.g. `minimal` + `vibrant` + `high-impact`) unless the user explicitly asked for that tension.
