# Generation Workflow

## Generation

Generate a runnable Teaching Prompt for each lesson.

### Teaching Pattern Baseline

Apply the patterns and constraints in `pedagogy.md#teaching-patterns`, `pedagogy.md#cognitive-techniques`, `pedagogy.md#variable-strategy`, `pedagogy.md#interaction-design`, and `pedagogy.md#visual-text-coordination` unless content requires a justified variation.

Encode the selected teaching method in each Teaching Prompt itself. Every lesson must carry enough pedagogical direction to run with the Course Prompt contributing only course-wide role and presentation style; do not rely on the Course Prompt to supply, repair, or override the lesson's pedagogy.

Consume the normalized Course Design Intake interaction policy only after it passes `data-contracts.md#interaction-policy`. Apply its teaching effect and substitution from `pedagogy.md#interaction-policy-precedence`; Generation does not reinterpret the modes or purposes. Whenever that policy calls for an interaction, choose its type before writing the `?[]` line per `prompt-contracts.md#prompt-contracts` Hard Rule 3. If a lesson naturally asks "which of these apply?", default to multi-select unless the source or user says only one answer is allowed.

### Single-Lesson Generation Strategy

Required anchors per lesson:

1. Opening paragraph with a teaching-start function (`prompt-contracts.md#prompt-contracts` Hard Rule 6) — not a copied chapter / lesson title or directory label.
2. Opening objective plus slide-style visual cover.
3. Evidence-chain explanation.
4. The interaction slot or non-interactive substitute required by `pedagogy.md#interaction-policy-precedence`, with visible instructional value.
5. At least one reusable deliverable.
6. Lesson close with summary or decision checkpoint.

Optional modules: viewpoint calibration, misconception correction, dual deliverables (understanding + action), cross-lesson bridge sentence, additional visual-text reinforcement blocks.

### Slide-Only Generation Override

When Course Design Intake resolves to pure slides / classroom interactive slides, replace the default explanation-heavy lesson pattern with a projection pattern. Pure slides are for classroom projection by a human instructor, not AI narration:

- Treat each lesson as a small slide deck controlled by a human instructor.
- Generate slide-facing blocks only: slide title, 2-4 short bullets, and a visual/layout instruction. When the interaction policy permits an interaction, also include its prompt, options, and concise feedback states.
- Keep policy-permitted interactions runnable with the normal MarkdownFlow syntax, but keep the surrounding content presentation-oriented. When the policy calls for the non-interactive substitute, render only the slide-facing content defined by `pedagogy.md#interaction-policy-precedence`.
- Do not include AI narration directives or learner-facing lecture prose such as
  "explain to the learner", "walk through", "向学习者说明", "讲解", "用文字解释",
  "讲清", or long paragraphs intended for the AI to speak.
- Do not require the normal visual-text explanation pair. The visual itself and
  the short on-slide labels carry the projection content; any explanation
  belongs to the human instructor, not the Teaching Prompt.
- The Course Prompt must describe the runtime role as producing classroom slides, using "interactive slides" only when the interaction policy permits interactions, not as conducting one-on-one tutoring. Do not include course-level instructions that ask the AI to verbally explain the lesson to a single learner.

### Outputs

Per-lesson schema in `data-contracts.md#lesson-schema`.

### Validation

- Each `teaching_prompt` is valid runnable MarkdownFlow.
- The first non-empty line of each Teaching Prompt performs a teaching-start function (`prompt-contracts.md#prompt-contracts` Hard Rule 6), not a duplicated `structure.json` chapter / lesson title or a copied source heading such as `# 第2章 ...`.
- Per-lesson schema populated per `data-contracts.md#lesson-schema`.
- Pedagogical and syntax constraints pass per `pedagogy.md` and `markdownflow.md`.
- The Teaching Prompt contains the lesson's teaching method and does not outsource pedagogical decisions to the Course Prompt.

### Working with Author-Provided Images

When the author supplies image assets — local files (any format incl. heic/heif) or remote URLs — three steps apply *within* Generation (and any later phase that touches the same lessons):

1. **Understand each image before placing it.** You cannot choose the lesson, position, or alt text without knowing what the image shows. Two regimes:
   - **You can see the image** (attached in this conversation and your model is multimodal): describe it to yourself in one sentence — what concept, relation, or example it conveys — then choose the lesson and position per `pedagogy.md#visual-text-coordination`.
   - **You cannot see the image** (only a file path / URL, or your model is text-only): **stop and ask the user**. Do not guess from the filename. Offer two options: (a) the user provides a one-sentence description per image (you will pass it as `--alt`), or (b) the user renames each file to a semantically meaningful name so you can infer the topic. Proceed only after one of these is in place.
2. **Upload via `shifu-cli.py upload-image`** (`--file` for local files — auto-preprocessed, or `--url` for remote; always pass `--course-dir` and `--alt`) and capture the printed `https://res.ai-shifu.cn/<uuid32>` URL. Full flags, preprocessing, and manifest behavior: `cli/cli-reference.md#image-upload`.
3. **Embed per `markdownflow.md#images`.** Default to 3.1 (deterministic-wrapped standard markdown); use 3.2 (instruction-style HTML) only when the lesson genuinely needs width control, alignment, a figure caption, or side-by-side layout — express every lock through wording (`必须原样保留` / `必须原样输出` / `不要改写`), never mix deterministic blocks into the instruction. The explanatory paragraph immediately after the image is mandatory in standard, non-slide-only lessons. Pure classroom slides follow the Slide-Only Generation Override instead and use concise slide labels without an AI explanation paragraph.
