# Optimization Workflow

## Optimization

Audit and improve existing Teaching Prompts (and the Course Prompt). This phase is not for writing from scratch.

### When to Use

Use Optimization when existing Teaching Prompts or a Course Prompt need audit and targeted improvement — gap analysis against source, quality upgrades without full rewrites, and lowering runtime failure risk. Not for from-scratch authoring.

### High-Standard Constraints

Apply Optimization audits against artifact-specific constraints:

- Teaching Prompt pedagogical constraints and issue taxonomy (interaction-policy effects, variable strategy, interaction design, visual-text coordination, lesson loop, information density): `pedagogy.md#interaction-policy-precedence`, `pedagogy.md#variable-strategy`, `pedagogy.md#interaction-design`, `pedagogy.md#visual-text-coordination`, `pedagogy.md#lesson-loop`, and `pedagogy.md#optimization-methodology`.
- Course Prompt deference and presentation-layer boundaries: `course-prompt.md#purpose` and `course-prompt.md#boundaries`.
- Interaction-policy shape and enums: `data-contracts.md#interaction-policy`.
- Syntax / runtime constraints (preservation, deterministic blocks, variable references): `markdownflow.md`.
- Observable audit checks: `review-checklist.md`.

### Optimization Workflow

1. Define scope (single lesson vs full course); if multiple script versions exist, declare the authoritative one before editing.
2. Build a coverage matrix mapping source points to script coverage.
3. Run the full audit per `review-checklist.md`, classify findings using the issue taxonomy in `pedagogy.md#optimization-methodology`, and apply smallest safe edits first.

### Course Prompt

Optimization also produces a course-level `course_prompt` artifact when input includes course material. Generate it by **copying and filling `course-prompt.md#fillable-template`, not by free-form composition**. Preserve the six sections, their order, and every non-placeholder instruction; replace every `XXX` with course-specific content and render the result in the resolved output language.

The Course Prompt must not originate an independent teaching method. Its Teaching Techniques section defers to the current Teaching Prompt, while the remaining sections contribute only course-wide role, tone, wording, format, slides, and intentional cross-lesson personalization.

Auto-fill placeholders from existing artifacts (`course_author_name`, `course_profile`, `delivery_constraints`, resolved target language per `data-contracts.md#language-resolution`, Segmentation visual cues). The Role must use the course author's real name; if `course_author_name` is missing, ask the author instead of inventing a persona. Do not duplicate per-lesson interaction logic or variable collection there — those belong in Teaching Prompts.

### Validation

- Conclusion and overall risk level presented first (report structure per `report-template.md`).
- Full review against `review-checklist.md` passes, or remaining gaps are explicitly listed as non-blocking suggestions.
- A `course_prompt` artifact is produced when input includes course material, with all six required canonical sections present.
- Generated `course_prompt` has no unresolved `XXX`, retains every non-placeholder template instruction, and applies delivery-mode behavior consistent with the Course Design Intake.
