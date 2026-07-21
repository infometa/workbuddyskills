# Review Checklist

Optimization 全面审计清单 — Optimization Optimization 必须把每条都过一遍。其他 Phase 的阶段交付检查见 SKILL.md 各 Phase 内的 Validation 段。

## Coverage

- All critical source points are present.
- No unsupported additions alter meaning.
- Source information density preserved (no substance traded for fluency).

## Script Style

- Directive / model-guiding language; no polished learner-facing manuscript prose.
- No author-side meta labels ("Knowledge Block", "Lesson Objective", "Deliverable").
- No internal authoring terms exposed in learner-facing text.

## Lesson Loop

- Minimum teaching loop satisfied: setup → explanation → interaction → close.
- One core question per lesson; resolved by lesson close.
- Action tasks executable now or explicitly linked to a downstream lesson.
- Variable naming consistent and traceable across lessons.
- Carryover statements only where cross-lesson dependency is allowed.
- Lesson structure follows the content, not a forced uniform template that erases lesson specificity.

## Interaction Quality

- Interactions are concrete and answerable.
- Learner-facing questions appear before interaction syntax, not after `%{{var}}` inside `?[%{{var}} ...]`.
- Each `?[]` interaction appears on its own line.
- If the pre-interaction text enumerates or describes choices, the `?[]` option labels match those choices exactly — same set, order, and wording.
- Input interactions include a specific pre-interaction question plus a shorter `...` placeholder.
- At least one deepening interaction per lesson (calibration, boundary check, or misconception correction).
- Branching paths are distinct where required; `*_viewpoint_check` interactions branch by option.
- Interaction results affect later content (visible downstream effect).
- Repeated interaction semantics avoided across lessons unless comparison intent is explicit.
- After every interaction, the script restates the learner's selection and uses `{{var}}` to drive downstream content.

## Variable Safety

- Variables are collected before use.
- No duplicate semantic collection unless comparison intent is explicit.
- No unresolved placeholders in learner-facing content.
- No more than three consecutive variable collections before feedback.
- Every variable has downstream utility (branching, depth control, deliverable variation).

## Visual-Text Coordination

- Every core concept has visual-plus-text explanation when a visual is used.
- When **no** image asset exists: visuals are described in natural language, not inlined as SVG/HTML/Mermaid markup.
- When an image asset **is** embedded: its URL is on the `resource.ai-shifu.cn` domain and has a corresponding entry in `<course-dir>/assets/image-manifest.json` (no orphan URLs, no externally hot-linked images).
- Fixed-display images are wrapped in single-line deterministic blocks (`===![alt](url)===`); HTML-view images use instruction-style directives per `markdownflow.md#images` 3.2 (no HTML inside `=== … ===` / `!=== … !===`).
- HTML-view image instructions include the `(必须原样保留)` phrase on every URL line, and locked text (e.g. figure captions) is enforced through wording (`必须原样输出`), not by mixing in deterministic blocks.
- Alt text and `图片内容` descriptions carry information about what the image conveys (no `image1` / `示意图`).
- Text adds context (background / causality / examples), not just a restatement of the image.

## Runtime Stability

- MarkdownFlow syntax is valid.
- Deterministic blocks used only where necessary; not wrapping full lessons.
- Interaction count per lesson at most five (recommended three to four).
- Code, image, and required source spans preserved per `markdownflow.md#preservation`.

## Course Prompt

- A `course_prompt` artifact is produced when input includes course material.
- All six required sections present (`# Role`, `# Task`, `# Teaching Techniques`, `# Writing Style`, `# Format`, `# Drawing`).
- `# Translation Rules` included when (and only when) trigger condition applies.
