# Infographic Style Guide

## Prompt Engineering Patterns

### Core Style Keywords

Always include these keywords in every prompt to maintain consistency:

```
hand-drawn sketch illustration, thick outlines, soft pastel colors,
doodle-style icons, cartoon characters, hand-lettered text,
whitespace-rich layout, no photorealistic elements, no 3D renders
```

### Color Palette Presets

Select based on content theme:

| Theme | Primary | Accent | Background |
|-------|---------|--------|------------|
| Technology | Soft blue | Electric teal | Light gray |
| Business | Warm beige | Coral orange | Cream white |
| Science | Mint green | Deep purple | Light mint |
| Education | Warm yellow | Sky blue | Pale yellow |
| Health | Soft pink | Fresh green | White |
| Creative | Lavender | Golden yellow | Light purple |
| Finance | Sage green | Navy blue | Off-white |

### Layout Patterns

#### Grid Layout (best for 4-6 equal-weight points)
```
Organize content in a [2x2 / 2x3 / 3x2] grid layout.
Each cell contains a cartoon icon at the top with a keyword below.
Grid separated by hand-drawn dashed lines.
```

#### Flow Layout (best for processes or sequences)
```
Content flows left-to-right connected by hand-drawn arrows.
Each step shown as a doodle vignette with label below.
Curved arrows with playful style connecting each step.
```

#### Radial Layout (best for a central concept with related ideas)
```
Central concept in a large circle at the center.
Related ideas radiate outward connected by hand-drawn lines.
Each satellite idea has its own small illustration.
```

#### Timeline Layout (best for chronological content)
```
Horizontal hand-drawn timeline across the center.
Events marked with illustrated milestones above and below the line.
Dates or labels in hand-drawn banners.
```

#### Comparison Layout (best for vs/pros-cons content)
```
Split layout with hand-drawn divider in the center.
Left and right sides use contrasting accent colors.
Matching elements on each side for easy comparison.
```

### Visual Element Library

Use these descriptions to guide cartoon element generation:

- **People**: Round heads, dot eyes, simple expressions, exaggerated proportions
- **Buildings**: Slightly crooked lines, warm lighting from windows
- **Devices**: Simplified shapes, glowing screens, thick bezels
- **Nature**: Swirly clouds, simple trees, wavy water
- **Data**: Hand-drawn bar charts, pie charts with thick borders, upward arrows
- **Connections**: Curvy arrows, dotted lines, speech bubbles, thought clouds
- **Emphasis**: Stars, exclamation marks, underlines, highlight boxes, banners

### Text Rendering Tips

Since AI image generation has limitations with text rendering:

1. **Minimize text in the prompt** — Focus on visual elements and use text sparingly.
2. **Use short keywords** (1-3 words per label) rather than phrases or sentences.
3. **Title text** should be 3-6 words maximum.
4. **Prefer icons over labels** where the meaning is obvious.
5. **Number lists** rather than label them when possible (1, 2, 3 are rendered more reliably than words).

### Quality Boosters

Add these modifiers for higher quality output:

```
professional illustration quality, clean composition,
balanced visual weight, cohesive color scheme,
editorial illustration style, magazine quality
```

### Negative Guidance

Explicitly exclude these in complex prompts:

```
no photography, no 3D rendering, no stock photo style,
no gradients, no drop shadows, no glossy effects,
no realistic textures, no computer-generated look
```

## Full Prompt Examples

### Example: AI Technology Infographic (Chinese)

```
A hand-drawn cartoon infographic about artificial intelligence key concepts, landscape 16:9 format.

Title: "AI 核心概念一图读懂" in bold hand-lettered style at the top center, decorated with small doodle stars.

Main content organized in a 2x3 grid layout:
- Top left: A cute robot character with a glowing brain representing "机器学习", with small data dots flowing in
- Top center: Two cartoon neural network nodes connected by wavy lines representing "深度学习"
- Top right: A speech bubble coming from a computer screen representing "自然语言处理"
- Bottom left: A cartoon eye with sparkles representing "计算机视觉"
- Bottom center: A robotic arm doing a thumbs up representing "机器人技术"
- Bottom right: A crystal ball with graph lines representing "预测分析"

Each grid cell has a hand-drawn dashed border. Small decorative doodles (gears, lightbulbs, binary code) scattered in the margins.

Style: hand-drawn sketch illustration, thick outlines, soft blue and teal color palette on light gray background, doodle-style icons, cartoon characters with round heads and dot eyes, hand-lettered Chinese text, whitespace-rich layout, no photorealistic elements. Professional illustration quality, clean composition.
```

### Example: Project Management Infographic (English)

```
A hand-drawn cartoon infographic about agile project management workflow, landscape 16:9 format.

Title: "The Agile Journey" in bold hand-lettered style at the top, with a small rocket doodle.

Main content organized as a circular flow layout:
- Starting point: A cartoon character with a lightbulb labeled "Backlog"
- Arrow flows to: A group of stick figures in a huddle labeled "Sprint Planning"
- Arrow flows to: A cartoon calendar with checkmarks labeled "Daily Standup"
- Arrow flows to: A small stage with a presenter labeled "Sprint Review"
- Arrow flows to: A mirror/magnifying glass labeled "Retrospective"
- Curved arrow loops back to Sprint Planning

Center of the cycle: Large hand-drawn text "ITERATE" with circular arrows.

Small doodle elements: sticky notes, kanban board, coffee cups, high-five hands scattered around margins.

Style: hand-drawn sketch illustration, thick outlines, warm yellow and coral orange palette on cream background, cartoon characters, hand-lettered English text, playful and energetic mood, whitespace-rich, no photorealistic elements.
```
