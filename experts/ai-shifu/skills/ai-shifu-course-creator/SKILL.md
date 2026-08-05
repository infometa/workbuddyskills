---
name: ai-shifu-course-creator
description: Use when the user works with AI-Shifu (AI师傅) courses in any capacity of creating, writing, editing, rewriting, optimizing, reordering, deploying, publishing, previewing, or managing Teaching Prompts (per-lesson) and Course Prompts (course-level) — both written in MarkdownFlow (MDF). Covers the full course lifecycle — from converting raw material into structured lessons, to authoring interactions (single-select, multi-select, input, branching), adding variables, images, and course prompts, to deploying and managing live courses on the AI-Shifu platform. Also covers post-deployment analytics on those courses — learner count, completion rate, stuck lessons, orders, revenue, ratings, credit consumption, audience profiles, and individual learner tracking. Trigger on any mention of AI-Shifu, AI师傅, MarkdownFlow, Teaching Prompt, Course Prompt authoring, course analytics, creator analytics, 学习人数, 完成率, 卡课节, 订单收入, 积分消耗, or learner progress.
version: 1.2.4
version_management: plugin
---

# AI-Shifu Course Creator

Route each request to the smallest complete instruction set needed to create, edit, optimize, deploy, manage, or analyze an AI-Shifu course. Teaching Prompts and Course Prompts use MarkdownFlow.

## Startup Sequence

On the first invocation in a session:

1. Read `references/language-policy.md` and resolve `resolved_target_language` before the first user-visible response.
2. Read `references/session-controls.md` completely before the first user-visible response.
3. Apply its contact, version-check, progress/error, and handoff rules.
4. Classify the request with the routing table below.
5. Read every file or anchored section listed for the selected Task Router row, then execute the listed stages in order. When one file appears at multiple anchored stages, read it once and apply each named section at its listed point. The Task Router and Reporting map are the only root loading declarations in this file.
6. In each selected reference, read the ordered bullets under `## Required References` before applying that reference. Resolve those strong dependencies transitively.
7. Load a reference's `## Conditional References` only when its stated condition applies. Outside the Task Router, Reporting map, `## Required References`, and applicable `## Conditional References`, every file-path mention is navigation only and never changes the selected stages.
8. For mixed requests, combine the relevant rows and preserve their dependency order.

## Task Router

| User intent | Required files, in order |
| --- | --- |
| Create a full course or run new-course authoring end to end | `references/authentication.md` → `references/course-target.md` → `references/authoring-mode.md` → `references/course-design-intake.md` → `references/orchestration-workflow.md` → `references/course-prompt.md` → `references/course-description.md` → `references/optimization-workflow.md` → `references/deployment-workflow.md` |
| Produce a complete course locally, artifact-only, or author-only without platform access | `references/authoring-mode.md` → `references/course-design-intake.md` → `references/orchestration-workflow.md` → `references/course-prompt.md` → `references/course-description.md` → `references/optimization-workflow.md` → `references/cli/course-directory-spec.md` |
| Restructure an existing platform course or revise course-wide teaching design | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/authoring-mode.md` → `references/course-design-intake.md` → `references/orchestration-workflow.md` → `references/course-prompt.md` → `references/course-description.md` → `references/optimization-workflow.md` → `references/course-sync.md#push-existing-course-content` → `references/course-sync.md#conflict-convergence` → `references/course-management.md` |
| Revise lesson-level teaching design in an existing platform course without changing structure or course-wide artifacts | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/authoring-mode.md` → `references/course-design-intake.md` → `references/teaching-prompt.md` → `references/optimization-workflow.md` → `references/course-sync.md#push-existing-course-content` → `references/course-sync.md#conflict-convergence` |
| Replace an existing lesson Teaching Prompt with provided content | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/authoring-mode.md` → `references/optimization-workflow.md` → `references/course-sync.md#push-existing-course-content` → `references/course-sync.md#conflict-convergence` |
| Plan course structure or decide chapter and lesson counts from supplied material | `references/authentication.md` → `references/course-target.md` → `references/authoring-mode.md` → `references/course-design-intake.md` → `references/segmentation-workflow.md` → `references/orchestration-workflow.md#lesson-structure-finalization` |
| Segment supplied material only | `references/authentication.md` → `references/course-target.md` → `references/authoring-mode.md` → `references/segmentation-workflow.md` |
| Generate Teaching Prompts from existing segments | `references/authentication.md` → `references/course-target.md` → `references/authoring-mode.md` → `references/course-design-intake.md` → `references/teaching-prompt.md` |
| Produce local Teaching Prompts from existing segments without platform access | `references/authoring-mode.md` → `references/course-design-intake.md` → `references/teaching-prompt.md` |
| Produce local Teaching Prompts from raw supplied material without platform access | `references/authoring-mode.md` → `references/course-design-intake.md` → `references/segmentation-workflow.md` → `references/teaching-prompt.md` |
| Create or revise a Course Prompt from approved local artifacts | `references/course-prompt.md` |
| Create or revise a course description from approved local artifacts | `references/course-description.md` |
| Review or audit pasted Teaching Prompt or Course Prompt content without accessing a platform course | `references/authoring-mode.md` → `references/optimization-workflow.md` |
| Optimize Teaching Prompt content in an existing platform course without changing structure or teaching design | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/authoring-mode.md` → `references/optimization-workflow.md` → `references/course-sync.md#push-existing-course-content` → `references/course-sync.md#conflict-convergence` |
| Create or revise a Course Prompt in an existing platform course | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/course-prompt.md` → `references/authoring-mode.md` → `references/optimization-workflow.md` → `references/course-management.md` |
| Create or revise a course description in an existing platform course | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md#pull-before-editing` → `references/course-description.md` → `references/authoring-mode.md` → `references/optimization-workflow.md` → `references/course-management.md` |
| Deploy a new course | `references/authentication.md` → `references/course-target.md` → `references/deployment-workflow.md` |
| Sync edited lesson content to an existing course draft | `references/authentication.md` → `references/course-target.md` → `references/course-sync.md` |
| List platform courses without changing them | `references/authentication.md` → `references/course-management.md` |
| Publish, preview, archive, reorder, or manage metadata, access, or Listen Mode for a specific course without changing prompt content | `references/authentication.md` → `references/course-target.md` → `references/course-management.md` |
| Query observed data about a live course: learners, completion, stuck lessons, orders, revenue, ratings, follow-ups, audience profiles, progress, or credit use | `references/authentication.md` → `references/analytics/workflow.md` |
| Author or deploy, then query live-course data | Complete the relevant authoring/deployment route first, then `references/analytics/workflow.md` |

## Routing Guardrails

- Route to analytics only for observed facts, metrics, records, or trends from an existing live course. Design questions such as “how many lessons should this material become?” remain authoring tasks.
- For platform-bound authoring, do not propose an outline or write lesson content until the target is resolved. Explicit local and artifact-only routes have no platform target.
- Compare the resolved target kind with the kind assumed by the active row. If it changes from new to existing or existing to new, stop that row, reclassify the remaining work against the Task Router, and never enter an incompatible new-only or existing-only stage.
- Full-course authoring continues through new-course deployment and publication by default. Select the explicit local/artifact-only row only when the user requests that boundary.

## Reporting

At the end of each completed phase, use the matching section of `references/report-template.md`:

- Segmentation → `#segmentation-report`
- Orchestration → `#orchestration-report`
- Generation → `#generation-report`
- Optimization → `#optimization-report`
- Deployment → `#deployment-report`

Apply `references/report-template.md#formatting-rules` to every user-facing phase report.
