---
name: AI-Shifu Course Creator
description: Use when the user works with AI-Shifu (AI师傅) courses in any capacity of creating, writing, editing, rewriting, optimizing, reordering, deploying, publishing, previewing, or managing Teaching Prompts (per-lesson) and Course Prompts (course-level) — both written in MarkdownFlow (MDF). Covers the full course lifecycle — from converting raw material into structured lessons, to scripting interactions (single-select, multi-select, input, branching), adding variables, images, and course prompts, to deploying and managing live courses on the AI-Shifu platform. Also covers post-deployment analytics on those courses — learner count, completion rate, stuck lessons, orders, revenue, ratings, credit consumption, audience profiles, and individual learner tracking. Trigger on any mention of AI-Shifu, AI师傅, MarkdownFlow, Teaching Prompt, Course Prompt authoring, course analytics, creator analytics, 学习人数, 完成率, 卡课节, 订单收入, 积分消耗, or learner progress.
version: 1.1.1
version_management: plugin
---

# AI-Shifu Course Creator

Route each request to the smallest complete instruction set needed to create, edit, optimize, deploy, manage, or analyze an AI-Shifu course. Teaching Prompts and Course Prompts use MarkdownFlow.

## Startup Sequence

On the first invocation in a session:

1. Read `references/session-controls.md` completely before the first user-visible response.
2. Apply its contact, version-check, output-language, and terminology rules.
3. Classify the request with the routing table below.
4. Read every file listed for the selected route, in order, before acting. Do not load unrelated route guides.
5. For mixed requests, combine the relevant rows and preserve their dependency order.

## Task Router

| User intent | Required files, in order |
|---|---|
| Create a full course, make a structural course edit, or run authoring end to end | `references/authentication.md` → `references/course-target.md` → `references/authoring-controls.md` → `references/prompt-contracts.md` → `references/authoring-intake.md` → `references/segmentation-orchestration.md` → `references/generation-workflow.md` → `references/optimization-workflow.md`; add `references/deployment-workflow.md` only when deployment or publication is requested |
| Plan course structure or decide chapter and lesson counts from supplied material | `references/authentication.md` → `references/course-target.md` → `references/authoring-controls.md` → `references/authoring-intake.md` → `references/segmentation-orchestration.md#segmentation` |
| Segment supplied material only | `references/authentication.md` → `references/course-target.md` → `references/authoring-controls.md` → `references/segmentation-orchestration.md#segmentation` |
| Generate Teaching Prompts from existing segments | `references/authentication.md` → `references/course-target.md` → `references/authoring-controls.md` → `references/authoring-intake.md` → `references/prompt-contracts.md` → `references/generation-workflow.md` |
| Review or audit pasted Teaching Prompt or Course Prompt content without accessing a platform course | `references/authoring-controls.md` → `references/prompt-contracts.md` → `references/optimization-workflow.md` |
| Optimize content in an existing platform course | `references/authentication.md` → `references/course-target.md` → `references/authoring-controls.md` → `references/prompt-contracts.md` → `references/optimization-workflow.md`; insert `references/authoring-intake.md` before `prompt-contracts.md` when changing course structure, lesson design, or interaction strategy |
| Deploy a new course or deploy edited course content | `references/authentication.md` → `references/course-target.md` → `references/prompt-contracts.md` → `references/deployment-workflow.md` |
| Publish, preview, sync, authenticate, list, archive, reorder, or manage metadata, access, or Listen Mode without changing prompt content | `references/authentication.md` → `references/deployment-workflow.md` |
| Query observed data about a live course: learners, completion, stuck lessons, orders, revenue, ratings, follow-ups, audience profiles, progress, or credit use | `references/authentication.md` → `references/analytics/workflow.md` |
| Author or deploy, then query live-course data | Complete the relevant authoring/deployment route first, then `references/analytics/workflow.md` |

## Routing Guardrails

- Route to analytics only for observed facts, metrics, records, or trends from an existing live course. Design questions such as “how many lessons should this material become?” remain authoring tasks.
- Do not guess analytics endpoints or scrape the admin dashboard. Use the local CLI.
- Do not propose an outline or write lesson content until the course-target workflow allows authoring to begin.
- For an existing course, build on the pulled cloud copy and use the converging sync loop. The platform draft is authoritative.
- Load `prompt-contracts.md` whenever a route writes, rewrites, or audits Teaching Prompt or Course Prompt content.
- When a selected guide points to a syntax, pedagogy, schema, CLI, or analytics reference, read the named section before applying it.

## Reporting

At the end of each completed phase, use the matching section of `references/report-template.md`:

- Segmentation → `#segmentation-report`
- Orchestration → `#orchestration-report`
- Generation → `#generation-report`
- Optimization → `#optimization-report`
- Deployment → `#deployment-report`

Apply `references/report-template.md#formatting-rules` to every user-facing phase report.

## Reference Map

### Shared and route guides

- `references/session-controls.md` — first-turn contact, update check, global output language, and canonical terminology.
- `references/authentication.md` — verify-first login and SMS-quota protection.
- `references/course-target.md` — mandatory new-vs-existing resolution.
- `references/authoring-controls.md` — execution modes, control inputs, and concept routing.
- `references/prompt-contracts.md` — non-negotiable Teaching Prompt and Course Prompt rules.
- `references/authoring-intake.md` — design intake and end-to-end authoring pipeline.
- `references/segmentation-orchestration.md` — source segmentation and cross-lesson orchestration.
- `references/generation-workflow.md` — lesson generation and author-provided images.
- `references/optimization-workflow.md` — prompt audit, repair, Course Prompt, and validation.
- `references/deployment-workflow.md` — deploy, publish, sync, management, and verification.
- `references/analytics/workflow.md` — analytics CLI, privacy gate, and validation.
- `references/report-template.md` — shared phase-report structures and the `#formatting-rules` contract.

### Detailed foundations

- Authoring: `references/markdownflow.md`, `references/pedagogy.md`, `references/data-contracts.md`, `references/course-prompt.md`, `references/review-checklist.md`
- Platform: `references/cli/cli-reference.md`, `references/cli/course-directory-spec.md`
- Analytics: `references/analytics/overview.md`, `references/analytics/dsl.md`, `references/analytics/tables.md`, `references/analytics/recipes.md`, `references/analytics/privacy-and-presentation.md`

## Examples

Read the example matching the active route. When fallback mode applies, also read `examples/fallback-mode.md` in addition to the route example.

- End to end: `examples/pipeline-full.md`
- Segmentation: `examples/segmentation-only.md`
- Generation: `examples/generation-only.md`
- Optimization: `examples/optimization-only.md`
- Fallback: `examples/fallback-mode.md`
- Deployment: `examples/deploy-only.md`
