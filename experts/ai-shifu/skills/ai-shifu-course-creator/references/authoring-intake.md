# Authoring Intake and Pipeline

## Course Design Intake (before Orchestration)

Run this intake after `course-target.md#resolve-the-course-target` and before Orchestration for: Path A end-to-end
course creation, Path B author-only generation, and existing-course edits that
change the course structure, lesson design, or interaction strategy. Do **not**
run it for deploy-only, analytics, login, publish, management, or pure
statistics requests.

Before asking anything, extract answers already present in the user's current
instruction, source material, or pulled course directory. Ask only for missing
items, in the user's language, as a step-by-step choice flow — ask the
usage-scenario question first, show its options, wait for the answer, then ask
only the next still-missing applicable question. Do not offer "you can let me
decide" or similar bypass wording before the required choice flow is complete.
Do not bypass the intake by inventing "conservative defaults" from a sparse
topic or short brief — in particular, do not assume personalized AI self-study,
thinking/self-check interactions, disabled Listen Mode, or a fixed chapter /
lesson count before asking the relevant missing questions. Defaults below apply
only after the user explicitly skips a question or asks you to continue without
answering it.

1. What usage scenarios should this course support? Multiple choices are
   allowed: students follow AI one-on-one for personalized self-study;
   interactive slides shown in class.
2. What should interactions do? Multiple choices are allowed: understand
   learner context for adaptive teaching; ask before teaching to trigger
   thinking or break old assumptions; self-check learning effect at the end of
   each lesson. Choosing none means no interactions.
3. If the course is not slide-only, should Listen Mode be enabled so AI voice
   teaches the course? When asking, also state that Listen Mode consumes more
   AI-Shifu credits. If the user does not answer, default to disabled.
4. How many chapters and lessons should the course have?

Use the answers as course-design constraints:

- **Usage scenario → content format.** Personalized AI self-study → illustrated text with fuller explanations and visual-text pairing. Only interactive classroom slides → apply the **Slide-Only Generation Override** (under `generation-workflow.md#slide-only-generation-override`) to lesson content, the Course Prompt, and Listen Mode. Question explicitly skipped → infer the format from the source material structure instead of inventing a fixed default.
- **Interaction choices → normalized interaction policy.** Resolve one policy before Orchestration: one or more purposes selected → `enabled` with exactly those selected purposes; none selected → `disabled` with an empty `purposes` array; question explicitly skipped → `unspecified` with an empty `purposes` array. Validate the shape and enums against `data-contracts.md#interaction-policy`, then pass the normalized object unchanged to Generation and Optimization. Placement, teaching effect, and non-interactive substitutions are defined only by `pedagogy.md#interaction-policy-precedence`.
- **Listen Mode**: pure slides → disable it and do not ask the question.
  Otherwise the question must mention the extra AI-Shifu credit consumption;
  unanswered → disabled; an explicit enable/disable decision carries into the
  deployment handoff.
- **Chapter and lesson counts** constrain the outline. Question explicitly
  skipped → infer structure from source volume and existing lesson-granularity
  rules instead of inventing a fixed default.

## Pipeline Overview

The phases are **not** a flat linear pipeline. **`course-target.md#resolve-the-course-target` gates the whole
pipeline.** **Orchestration is an end-to-end driver** that internally calls Segmentation and Generation. Only Optimization and Deployment actually run in linear sequence after Orchestration completes. Load `optimization-workflow.md` and `deployment-workflow.md` only when the selected path needs them.

```text
Course request
   │
   ▼
Resolve Course Target                    ← MANDATORY front guard: login + find-title + branch
   │   (new vs edit existing; pull the existing course BEFORE authoring)
   ▼
Raw material
   │
   ▼
Course Design Intake                     ← ask only for missing design constraints
   │   (usage scenario, interaction purpose, Listen Mode, chapter/lesson count)
   ▼
Orchestration                            ← end-to-end driver
   ├── calls Segmentation                 (cleanup + semantic segmentation)
   └── calls Generation                   (per-lesson Teaching Prompts)
        │
        │  Orchestration outputs: Teaching Prompts + course_index
        │                 + global_variable_table
        ▼
Optimization                              (audit + optimize)
        │
        ▼
Deployment                                (build + import + publish to platform)
        │
        ╰─ optional ─▶ Analytics          (post-deployment data queries on live courses)
```

Segmentation, Generation, and Optimization can each be invoked standalone. The main router selects only the matching phase guide for a standalone request; analytics and deployment remain separate routes.

## Usage Paths

### Path A: End-to-End

Run the full pipeline from raw material to a live deployed course.

0. **Resolve the course target (first, always)** — follow **`course-target.md#resolve-the-course-target`**; if editing an existing course, `pull` it before authoring.
1. **Orchestration** drives Segmentation and Generation end-to-end, then runs cross-lesson gating to produce Teaching Prompts + course_index + variable table.
2. **Optimization** audits and improves Orchestration's output, plus produces the Course Prompt and SEO course description.
3. **Deployment** writes the course directory, builds, imports, and publishes to the AI-Shifu platform.

### Path B: Author Only

Run Segmentation through Optimization to produce optimized Teaching Prompts, a Course Prompt, and an SEO course description without deploying. Sub-paths:
- **Segment only**: Segmentation alone for structured segments and manual review.
- **Generate only**: Generation alone on pre-existing segments to produce Teaching Prompts.
- **Optimize only**: Optimization alone to audit and improve existing Teaching Prompts.
