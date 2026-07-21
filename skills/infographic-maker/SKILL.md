---
name: infographic-maker
description: "Generate hand-drawn cartoon-style infographics from articles, concepts, reports, or data. Use when a user wants a visual summary, knowledge card, illustrated overview, or one-page explainer. Distill 3-7 key points, map them to concrete visual metaphors, and produce a single 16:9 infographic image with minimal text and strong visual hierarchy."
description_zh: "把文章、概念和数据提炼成手绘卡通信息图"
description_en: "Turn articles, concepts, and data into hand-drawn infographic visuals"
display_name: "infographic-maker"
display_name_en: "infographic-maker"
visibility: "public"
---

# Infographic Maker

## Overview

Transform any input content — articles, concepts, data, meeting notes, or ideas — into a visually engaging, hand-drawn cartoon-style infographic. The output is a single 16:9 landscape image optimized for quick comprehension and visual memorability.

## Workflow

### Phase 1: Content Analysis & Distillation

Before generating any image, analyze the input content thoroughly:

1. **Identify the core theme** — Determine the single overarching topic or message.
2. **Extract 3-7 key points** — Distill the most important facts, concepts, or takeaways. Prefer odd numbers (3, 5, 7) for visual balance.
3. **Determine visual metaphors** — For each key point, identify a concrete visual element (icon, character, object, scene) that can represent it.
4. **Detect language** — Unless the user explicitly requests a specific language, match the language of the input content for all text in the infographic.
5. **Identify notable figures** — If the content mentions well-known people, plan to include simplified cartoon portraits (not realistic).

### Phase 2: Prompt Construction

Construct the image generation prompt following these mandatory style rules. Refer to `references/style-guide.md` for detailed prompt patterns and examples.

#### Mandatory Style Constraints

- **Art style**: Hand-drawn, sketch-like, cartoon illustration. Thick outlines, slightly imperfect lines, warm and friendly aesthetic.
- **Composition**: Landscape orientation (16:9 ratio). Use `size: "1536x1024"` in the image generation call.
- **Layout**: Clear visual hierarchy with a prominent title area. Content flows logically (top-to-bottom, left-to-right, or radial). Generous whitespace between elements.
- **Typography**: All text rendered in hand-drawn lettering style. Title text large and bold. Supporting text minimal — keywords and short phrases only, never full sentences.
- **Color palette**: Soft, muted tones with 2-3 accent colors. Avoid neon or overly saturated colors. Pastel backgrounds work well.
- **Elements**: Simple cartoon icons, doodle-style illustrations, hand-drawn arrows/connectors, speech bubbles, banners, and frames. No photorealistic elements whatsoever.
- **People**: If depicting people, use simplified cartoon characters with exaggerated features. For famous figures, use recognizable but stylized caricatures.
- **Information density**: Less is more. Highlight keywords and core concepts only. Aim for instant comprehension — the viewer should grasp the main message within 5 seconds.

#### Prompt Template

Build prompts using this structure:

```
A hand-drawn cartoon infographic about [TOPIC], landscape 16:9 format.

Title: "[TITLE TEXT]" in bold hand-lettered style at the top.

Main content organized as [LAYOUT TYPE: grid/flow/radial/timeline]:
- [Key point 1 with visual element description]
- [Key point 2 with visual element description]
- [Key point 3 with visual element description]
...

Style: hand-drawn sketch illustration, thick outlines, soft pastel colors with [ACCENT COLOR] highlights, doodle icons, whitespace-rich layout, cartoon characters, no photorealistic elements. All text in hand-drawn lettering. [LANGUAGE] text only.
```

### Phase 3: Image Generation

Generate the infographic using the image generation capability:

- **Size**: Always use `1536x1024` (landscape 16:9).
- **Quality**: Use high quality for better detail in text and illustrations.
- **Style**: Prefer a natural rendering style to keep the hand-drawn feel organic.

If the current task is complex or multi-step, and generating the infographic is one step among many, consider delegating the generation to a sub-agent. This allows:
- The main agent to continue with other work while the image generates.
- A focused sub-agent to handle prompt refinement and generation quality.
- Post-generation review before continuing the main task.

When delegating to a sub-agent, include the full constructed prompt and all style constraints in the task description.

### Phase 4: Review & Iteration

After generation, briefly assess the output:

1. Does it capture the core theme?
2. Are key points visually distinguishable?
3. Is the text readable and in the correct language?
4. Does it maintain the hand-drawn aesthetic?

If the user requests adjustments, iterate by modifying the prompt and regenerating. Common adjustments include:
- Adding/removing key points
- Changing the color scheme
- Adjusting information density
- Switching layout structure

## Usage Examples

### Example 1: Article Summary

**User**: "帮我把这篇关于量子计算的文章做成信息图"

**Action**: Read the article → Extract core concepts (叠加态、量子纠缠、量子门、量子优势) → Construct prompt with science-themed cartoon elements (atoms, cats, circuits) → Generate with Chinese text.

### Example 2: Concept Explanation

**User**: "Create an infographic explaining the Agile methodology"

**Action**: Identify key Agile concepts (sprints, standups, retrospectives, user stories, continuous delivery) → Use a cyclical layout → Include cartoon characters in a team setting → Generate with English text.

### Example 3: Data Highlights

**User**: "把这份年度报告的关键数据做成信息图"

**Action**: Extract top 5 data points → Use large hand-drawn numbers with supporting illustrations → Organize in a clear visual hierarchy → Generate with matching language.

## Important Notes

- The image generation model may not always render long text perfectly. Focus prompts on visual elements and keep text elements minimal.
- For content with more than 7 key points, prioritize the most important ones and group related points together.
- When the input is very long (articles, reports), summarize aggressively — the infographic should be a visual abstract, not a transcript.
- Always preserve the hand-drawn aesthetic. Never mix in photorealistic elements, stock photo styles, or 3D renders.
