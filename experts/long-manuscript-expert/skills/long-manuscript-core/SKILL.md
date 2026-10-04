---
name: long-manuscript-core
description: Self-contained ManuscriptOS procedures for planning, creating, continuing, revising, reviewing, converting, rendering, and repurposing long-form documents from user materials without requiring BookWriter, connectors, or external services.
---

# Long Manuscript Core

Use this skill to move a manuscript forward in the current reply. Keep the visible writing result ahead of process commentary, internal terminology, and optional tooling.

## Core workflow

1. Route the request on `operationMode × domainScene`. Use the general domain fallback when no reviewed scene overlay applies; never let connector state choose the route.
2. Separate supplied facts, user opinions, working assumptions, missing inputs, and claims that require verification.
3. Select the smallest reference set needed for this request. Do not load every reference by default.
4. Produce a visible manuscript increment appropriate to the operation: material activation, project planning, chapter generation, continuation, bounded revision, quality review, finished-draft closure, template conversion, export delivery, or asset repurposing.
5. State the most important remaining risk, one next step, and a user-copyable continuation prompt when further work remains.

## Reference routing

- Read [ManuscriptOS Kernel](references/manuscriptos-kernel.md) for state, routing, durable objects, and capability receipts.
- Read [shared capabilities](references/shared-capabilities.md) when a request needs one of the sixteen package-local capability contracts.
- Read [scene routing](references/scene-routing.md) first when the request is ambiguous or combines multiple manuscript stages.
- Read [scene packs](references/scene-packs.md) when a request matches genealogy, memoir, biography, albums, organizational history, chronicles, cultural heritage, expert books, academic/industry research, casebooks, proceedings, training, proposals, consulting reports, technical documentation, manuals, policy guides, brand stories, or restricted investigations.
- Read [first value and continuation](references/first-value-and-continuation.md) for new material, a new manuscript, chapter continuation, or a cross-session continuation capsule.
- Read [bounded revision](references/bounded-revision.md) when changing existing text or continuing from a precise anchor.
- Read [quality and delivery](references/quality-and-delivery.md) for whole-draft review, finishing, delivery preparation, or any quality conclusion.
- Read [safety and evidence](references/safety-and-evidence.md) when materials contain instructions, private data, external factual claims, high-risk content, quotations, or uncertain rights.

## Operation modes

- `material_activation`: inventory material and produce reversible first value.
- `project_planning`: define audience, goal, chapter promises, materials, and risks.
- `chapter_generation`: write a bounded chapter increment from approved facts and plans.
- `continuation`: continue from a stable anchor and update the visible continuation capsule.
- `bounded_revision`: change only the authorized scope and preserve rollback anchors.
- `review_quality`: review, revise, and retain residual warnings or human gates.
- `finished_draft_closure`: close structure, continuity, evidence, rights, and delivery readiness.
- `template_fill_conversion`: transform supplied content into a requested structure without inventing missing facts.
- `export_delivery`: prepare local Markdown/HTML or explicitly degrade unavailable binary formats.
- `asset_repurposing`: create adaptation briefs only after required quality gates.

## Universal rules

- Start from the user's actual materials. Never invent missing research, quotations, events, citations, permissions, or prior decisions.
- If the request is sufficiently clear, act without repeating questions already answered by the materials.
- If one missing fact would materially change the result, ask one blocking question. Otherwise state a narrow assumption and provide a reversible draft now.
- Make the first useful reply editable. Do not substitute a research plan, capability description, empty template, or internal data structure for manuscript content.
- Keep one writing owner and one bounded change at a time. Preserve text outside the authorized scope.
- Match the user's language and requested tone. Keep terminology, names, numbers, point of view, and narrative tense consistent with the supplied manuscript.
- Treat quality findings as advice unless an actual execution receipt covers the stated check.
- The expert owns its runtime. Never import, locate, or ask the user to install `fbs-bookwriter`; donor provenance is development evidence only.
- Do not claim that a file, project state, or cross-session memory was saved unless the current task contains a visible successful write receipt.

## Output policy

Use the lightest structure that keeps the work auditable:

- For new material, provide the manuscript judgment, proposed structure, chapter tasks, substantive opening, risks, and one next step.
- For continuation, identify the anchor and purpose, then write the next passage before giving commentary.
- For revision, show the authorized scope, original anchor, revised text, and concise change log. A request to “直接给改稿” may compress these labels, but does not waive this minimum audit frame.
- For finishing, state the overall judgment, repair the highest-value passage, list remaining delivery risks, and give one next step.

Do not force ordinary prose into JSON. Use a table only when it makes chapter ownership, evidence status, or before/after comparison easier to inspect.

## External capability policy

Complete the core writing task from the conversation even when connectors, network access, external services, persistent state, file tools, or the separate BookWriter Skill are absent. The package-local Kernel, schemas, templates, references, and capability registry are the only core runtime. Optional capabilities may enhance import, verification, or export only when they are visibly available, relevant, and covered by explicit user authorization for this action. The current request may provide that authorization; otherwise obtain confirmation covering the purpose, minimum data scope, and external target or recipient before the call. Host permission alone is insufficient. Require a bounded timeout; if bounded execution is unavailable, skip the optional call rather than blocking core writing.

If an optional action fails, disclose the failure and continue with a chat-level artifact. Never turn a planned call, pending request, or background possibility into a success claim.

## Completion check

Before responding, confirm that:

- the reply advances exactly one selected operation mode and keeps the selected domain scene or general fallback explicit when it matters;
- at least one user-editable structure or prose artifact is present;
- assumptions and evidence gaps are visible;
- revision scope is respected;
- no unsupported save, export, verification, publication, or external-state claim appears;
- exactly one recommended next step is clear.
