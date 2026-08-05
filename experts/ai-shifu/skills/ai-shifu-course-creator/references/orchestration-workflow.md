# Orchestration Workflow

Drive Segmentation and Teaching Prompt generation, then produce the cross-lesson course index and global variable table. This file coordinates phases; it does not redefine their rules.

## Required References

- `language-policy.md`
- `authoring-mode.md#mode-selection`
- `data-contracts.md#output-contract`
- `data-contracts.md#variable-table`
- `data-contracts.md#orchestration-fallback-fields`
- `segmentation-workflow.md`
- `teaching-prompt.md`
- `pedagogy.md`

## Lesson Structure Finalization

Use this section after Segmentation when the requested output is a decided course structure or chapter and lesson count, without Teaching Prompt generation.

1. Review the traceable segments and lesson-boundary candidates in source order.
2. Finalize lesson cuts so every lesson has one core question and every valid source span is assigned exactly once.
3. Group the lessons into chapters without changing the finalized lesson cuts or source order unless the author supplied an explicit ordering constraint.
4. Return the decided chapter count, lesson count, ordered chapter and lesson titles, each lesson's core question, and its source-segment references.
5. Apply Segmentation's preservation and traceability validation before reporting the plan.

Do not run Teaching Prompt generation or build `course_index` and `global_variable_table` unless the selected route also loads the complete Workflow below.

## Workflow

1. Normalize source ordering and merge the input material.
2. Run Segmentation and retain its traceable segments and lesson-boundary candidates.
3. Finalize lesson cuts with one core question per lesson.
4. Finalize an internal execution plan for each lesson: the teaching sequence, every required teaching action's presence, placement, and effect, interaction and feedback adjacency, close, and, when applicable, exact slide count and order, each slide's teaching function, content grouping, visual hierarchy, and semantic layout. Resolve this plan without using `teaching_prompt_personalization_level` as an input.
5. Run Teaching Prompt generation for each lesson with that plan and the normalized `teaching_prompt_personalization_level` passed unchanged across the course. Materialize the plan as direct local runtime instructions in final execution order; the Teaching Prompt begins with the first learner-time teaching action, while the plan and personalization control remain in the in-memory authoring handoff.
6. Build `course_index` and `global_variable_table` from the completed lesson set.
7. Apply the gates below. Rerun the phase that owns each failed output rather than treating every failure as a lesson-only generation failure.
8. After every affected Segmentation and Teaching Prompt rerun passes, rebuild both `course_index` and `global_variable_table`, then reapply the gates. Block handoff while any gate still fails.

## Mandatory Gates

- Verify syntax and runtime results through the requirements loaded by `teaching-prompt.md`.
- Recover each Teaching Prompt's execution signature from its actual ordered instructions and compare it with the internal execution plan. Verify teaching and slide order, slide count, local content and effects, content grouping and hierarchy, interaction-control-feedback adjacency, images, and the close from the artifact itself.
- Verify each Teaching Prompt's content-expression specificity against `teaching-prompt.md#personalization-levels`. Across level variants, the recovered execution signature remains unchanged while only ordinary wording and already-permitted example detail vary.
- Verify every learner-answer variable against `data-contracts.md#variable-table`.
- Verify the selected teaching loop, interaction effects, variable-persistence decisions, and delivery-mode behavior against `pedagogy.md`.
- Require Segmentation's preservation validation to pass.
- Verify every required interaction effect and branch against `pedagogy.md#interaction-design`.
- Verify that material selected for exact preservation appears directly at its resolved runtime position in the completed Teaching Prompt.

Do not partially pass a phase or lesson.

## Rerun Rules

- When a preservation, traceability, or lesson-boundary gate fails, rerun Segmentation for the affected source scope, then rerun every Teaching Prompt affected by the changed segments or lesson cuts.
- When a Teaching Prompt authoring or runtime gate fails, rerun only the affected lesson and any dependency-linked lessons.
- After a rerun changes lesson boundaries, variables, or their consumers, rebuild both cross-lesson outputs from the passing lesson set; never hand off a stale `course_index` or `global_variable_table`.
- Recompute the full course only when global source order changes. If an owning phase cannot pass after its focused rerun, stop and report the blocking gate instead of handing off partial outputs.

## Fallback Handling

Under fallback mode, deliver coarse lesson drafts, mark uncertain `course_index` entries, and emit the `rerun_plan` defined in `data-contracts.md#orchestration-fallback-fields`. Keep best-effort work separate from artifacts that passed all gates.

## Outputs

Produce `lesson_teaching_prompts`, `course_index`, and `global_variable_table` exactly as defined in `data-contracts.md#output-contract`.

Keep these as structured phase-handoff data. When a local course directory is materialized, follow the closed artifact set owned by `cli/course-directory-spec.md`.

## Validation

- All three Orchestration outputs are present and mutually consistent.
- Every lesson passes the Mandatory Gates.
- Fallback outputs include the required uncertainty and rerun fields.
