# Review Checklist

Optimization 全面审计清单 — Optimization Optimization 必须把每条都过一遍。其他阶段的交付检查见 `segmentation-orchestration.md`、`generation-workflow.md` 和 `deployment-workflow.md` 内的 Validation 段。

## Coverage

- All critical source points are present.
- No unsupported additions alter meaning.
- Source information density preserved (no substance traded for fluency).

## Script Style

- Directive / model-guiding language; no polished learner-facing manuscript prose.
- No author-side meta labels ("Knowledge Block", "Lesson Objective", "Deliverable").
- No internal authoring terms exposed in learner-facing text.
- Each Teaching Prompt contains the lesson's teaching method and flow.

## User-Visible Language

- User-visible agent output outside generated course content follows the resolved target language from `data-contracts.md#language-resolution`.
- Generated course artifacts and learner-facing passages follow the resolved target language.
- Effective build metadata follows the resolved target language after precedence is applied: course title (`--title`, `README.md`, or directory-name fallback), course description (`--description` or `course-description.md`), chapter titles (`structure.json`, `--chapter-name`, or course-title fallback), and lesson titles.
- Human-facing labels for canonical concepts follow [session-controls.md#canonical-term-translation-table](session-controls.md#canonical-term-translation-table) when the resolved target language is listed there.
- Machine-facing identifiers and verbatim source material remain unchanged: JSON keys, file names, CLI flags, API fields, code symbols, MarkdownFlow syntax, URLs, code samples, and required verbatim source quotes.

## Structure Separation

- Chapter titles, lesson titles, numbering, and hierarchy labels live in `structure.json` / `course_index`, not in Teaching Prompt body text.
- Each lesson file's first non-empty line performs a teaching-start function: scenario, guiding question, prior-experience activation, task setup, or practice start.
- High-confidence structure pollution is absent: the first line is not a Markdown heading copied from `structure.json`, not a `第X章` / `Chapter X` directory label, and not an exact repeat of the chapter or lesson title.
- Medium-confidence cases are flagged for review instead of auto-deleted: headings used to teach Markdown syntax, code comments beginning with `#`, or courses with an explicit `allow_headings` / heading-supported rendering decision.

## Lesson Loop

- The interaction policy used for this audit resolves to `enabled`, `disabled`, or `unspecified` and matches the Course Design Intake answer.
- The observed lesson loop and any non-interactive substitute match `pedagogy.md#interaction-policy-precedence` and `pedagogy.md#lesson-loop` for that resolved policy.
- The final paragraph of each lesson is non-interactive.
- One core question per lesson; resolved by lesson close.
- Action tasks executable now or explicitly linked to a downstream lesson.
- Variable naming consistent and traceable across lessons; new variable names follow the resolved output language and are composed of letters, numbers, and underscores.
- Carryover statements only where cross-lesson dependency is allowed.
- Lesson structure follows the content, not a forced uniform template that erases lesson specificity.

## Interaction Quality

- Under `disabled`, no `?[]` block, learner-answer request, learner-answer variable, or answer-dependent branch is present.
- Interactions that are present are concrete and answerable.
- Interaction type matches the decision: single-select for mutually exclusive path choices, multi-select for non-exclusive learner context, goals, interests, modules, blockers, scenarios, experience, or practice needs. For multi-select, downstream content is driven through combined feedback, prioritization, or tailored examples rather than exhaustive branching for every combination.
- Learner-facing questions appear before interaction syntax, not after `%{{var}}` inside `?[%{{var}} ...]`.
- Each `?[]` interaction appears on its own line.
- If the pre-interaction text enumerates or describes choices, the `?[]` option labels match those choices exactly — same set, order, and wording.
- Input interactions include a specific pre-interaction question plus a shorter `...` placeholder.
- Interaction presence, placement, and deepening match the resolved policy in `pedagogy.md#interaction-policy-precedence`.
- Branching paths are distinct for viewpoint/path interactions and whenever `require_branching_feedback` is explicit.
- Instructional interaction results affect later content through immediate feedback or a visible downstream effect.
- Repeated interaction semantics avoided across lessons unless comparison intent is explicit.
- Variable-backed interactions are used only when the answer must leave the current lesson.
- Lesson-local branching, examples, feedback, summaries, and inputs use no-variable `?[...]` and do not introduce `{{var}}`.

## Variable Safety

- `disabled` lessons contain no learner-answer variables.
- Every referenced learner-answer variable has a corresponding variable-backed interaction and metadata entry.
- Any learner answer used outside the current lesson, including `course-prompt.md`, later lessons, or cross-lesson personalization, difficulty control, examples, summaries, or deliverables, has a named variable.
- No duplicate semantic collection unless comparison intent is explicit.
- No unresolved placeholders in learner-facing content.
- Variable references in Teaching Prompt and Course Prompt content are written as substituted values; references that may run before the learner assigns a value handle the literal `UNKNOWN` fallback.
- Variable-based branches state the substituted value in a natural sentence first, then use natural-language condition phrasing.
- Every variable has cross-lesson or Course Prompt utility.
- No throwaway named variables for continue buttons, confirmations, choices, or inputs used only inside the current lesson.

## Visual-Text Coordination

- In standard non-slide-only lessons, every core concept that uses a visual has a visual-plus-text explanation.
- Raw graphic source code (SVG, HTML drawings, Mermaid, PlantUML, or Graphviz) appears in a Teaching Prompt only when the author explicitly requests that raw format; approved HTML-view image instructions are checked separately below.
- Pure classroom slides follow `generation-workflow.md#slide-only-generation-override` and are not failed for omitting AI narration or a full explanation paragraph.
- When an image asset **is** embedded: its URL is on the `res.ai-shifu.cn` domain and has a corresponding entry in `<course-dir>/assets/image-manifest.json` (no orphan URLs, no externally hot-linked images).
- Fixed-display images are wrapped in single-line deterministic blocks (`===![alt](url)===`); HTML-view images use instruction-style directives per `markdownflow.md#images` 3.2 (no HTML inside `=== … ===` / `!=== … !===`).
- HTML-view image instructions include the `(必须原样保留)` phrase on every URL line, and locked text (e.g. figure captions) is enforced through wording (`必须原样输出`), not by mixing in deterministic blocks.
- Alt text and `图片内容` descriptions carry information about what the image conveys (no `image1` / `示意图`).
- In standard non-slide-only lessons, text adds context (background / causality / examples), not just a restatement of the image.

## Runtime Stability

- MarkdownFlow syntax is valid.
- Deterministic blocks used only where necessary; not wrapping full lessons.
- Interaction count per lesson at most five (recommended three to four).
- Code, image, and required source spans preserved per `markdownflow.md#preservation`.

## Course Prompt

- A `course_prompt` artifact is produced when input includes course material.
- All six required canonical sections are present in order, with headings rendered in the resolved output language: Role, Task, Teaching Techniques, Writing Style, Format, and Slides.
- No `XXX` placeholder remains; every non-placeholder instruction from `course-prompt.md#fillable-template` is represented.
- The Teaching Techniques section treats the current Teaching Prompt as authoritative and limits the Course Prompt to presentation-layer adjustments.
- The Course Prompt introduces no generic lesson loop, cognitive rhythm, explanation structure, practice design, or interaction-feedback method that competes with a Teaching Prompt.
- The Slides section lets the Teaching Prompt determine whether accompanying text is required and preserves the template's writing guidelines when it is.
