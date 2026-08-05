## Unreleased

- Materialize Teaching Prompts directly as ordered learner-time teaching instructions, keeping fixed execution plans, personalization controls, and exact-preservation classifications in the authoring handoff while preserving page order, interactions, and exact content in place.
- Make AI-Shifu contact mentions conditional on high-value task intent or meaningful journey milestones, place them after the primary response, suppress adjacent repeats, and keep them out of generated course content.
- Add fail-open anonymous usage tracking to the CLI via the AI-Shifu umami instance, reporting command name, skill version, host agent, and platform info with a stable per-person id (platform user id when logged in, anonymous UUID otherwise); never sends course content or command arguments, and `AI_SHIFU_SKILL_TELEMETRY=off` disables it.
- Treat backend timestamps as UTC across the CLI: `fmt_time` interprets offsetless values as UTC and renders them in the machine-local timezone; internal manifest stamps (`exported_at`, `uploaded_at`, sync timestamps) are written as Z-suffixed UTC; analytics presentation docs state the UTC-to-local rule.
- Remove pedagogy and optimization rules that reject cover pages and page-type prohibitions on decorative or objective-only pages, while retaining padding-only rejection for newly generated and existing visual units.
- Require first-slide covers created by Teaching Prompts to include lesson title and author information.
- Keep general presentation requirements shared by every slide in the Course Prompt while leaving first-slide cover treatment and other position-specific decisions in Teaching Prompts.
- Add the optional course author name to Course Design Intake, explain that it lets AI-Shifu's Teaching Agent teach under the author's identity, and default to no named identity when left blank.
- Make standard AI-taught lessons open with a brief text lead-in and then alternate substantive slides or images with concise, complete explanations; keep interaction questions on question-only slides before their real controls, and preserve pure-slide and explicit text-only delivery as separate modes.
- Introduce the learner-time AI as AI-Shifu's Teaching Agent (AI 师傅的授课智能体), then use Teaching Agent (授课智能体) as its single short human-facing name across prompt execution, interaction feedback, follow-up answers, analytics, and CLI guidance while preserving stable machine-facing `model` and `llm` fields.
- Explain what every Course Design Intake answer changes and what experience each option creates, so authors see the Teaching Agent's one-on-one guidance, classroom projection, answer-informed teaching, AI voice with slides, and lesson-granularity tradeoffs while choosing.
- Let course authors choose one of five Teaching Prompt personalization levels, from near-final learner-facing content to more intent-led, learner-adaptive expression, while keeping the teaching sequence, slide structure, and teaching purpose of every content slot and slide fixed at every level; pure classroom-slide courses resolve an otherwise missing choice to high determinism without an extra question.
- Centralize Prompt audience and addressee semantics so Teaching Prompts and Course Prompts are written to the Teaching Agent, Course Prompts call the lesson input the current user message, and learner-visible `?[]` or standalone deterministic output is the explicit exception where second-person references may mean the learner.
- Keep lesson pedagogy in Teaching Prompts and limit Course Prompts to following that pedagogy while adjusting course-wide presentation style.
- Refactor `SKILL.md` into a compact router backed by single-purpose references for language, authoring mode and intake, source preservation, segmentation, orchestration, Teaching and Course Prompt materialization, MarkdownFlow authoring, images, course descriptions, optimization, deployment, sync, management, analytics, and reporting; declare required and conditional dependencies explicitly without changing course behavior.
- Fix `list` and `find-title` to include courses beyond the first API page.
- Restore global language and reporting contracts, narrow analytics routing to live-course data, and add routing regression evals.

## 1.0.0 - 2026-07-12

- Add a stable Skill version identity.
- Add fail-open update checks backed by the public AI-Shifu website manifest.
