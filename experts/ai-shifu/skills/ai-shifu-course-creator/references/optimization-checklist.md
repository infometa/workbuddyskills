# Optimization Checklist

Observable acceptance criteria for Optimization. Use each linked owner to interpret the rule; this checklist records `pass`, `fail`, or `not-assessed` without redefining that rule.

For a pasted content-only Prompt, run every check observable from the body and record any check that needs an unprovided schema envelope or metadata table as `not-assessed`; do not manufacture the missing wrapper.

## Required References

- `language-policy.md#language-audit`

## Conditional References

- When authoritative source material or selected immutable spans are in the audit scope: `source-preservation.md#verification`
- When a Teaching Prompt is in scope: `teaching-prompt.md#validation`
- When a Course Prompt is in scope: `course-prompt.md#materialization-checks`
- When a course description is in scope: `course-description.md#validation`
- When the audited artifacts use image assets: `image-authoring.md#image-output-validation`

## Coverage and Fidelity

- When authoritative source material is supplied, every critical source point in scope is represented and no unsupported addition changes its meaning.
- Meaning and information density observable in the supplied artifact remain intact after repair.
- When selected immutable spans are in scope, every span passes `source-preservation.md#verification`.
- A content-only audit does not claim coverage of or fidelity to an external source that was not supplied.

## Artifact Boundaries

- Teaching Prompts contain lesson method and flow; the Course Prompt contributes only course-wide role and presentation behavior.
- Chapter titles, numbering, hierarchy, and ordering remain in structure metadata rather than Teaching Prompt bodies.
- No artifact relies on another artifact to supply behavior that its owner requires locally.
- Every part of a Teaching Prompt body serves learner-time execution as a teaching, presentation, interaction, feedback, branch, or close instruction, or as learner-visible exact material. Internal execution plans and authoring controls remain in their owning handoff and references.

## Teaching Prompt Behavior

- Each lesson resolves one core question through a complete loop and valid teaching pattern under `pedagogy.md`.
- When `teaching_prompt_personalization_level` is supplied, the Teaching Prompt's ordinary title and explanation wording, transition wording, example detail, and non-deterministic feedback wording match `teaching-prompt.md#personalization-levels`.
- When that level is absent from a content-only audit or supplied metadata, record personalization-level alignment as `not-assessed`; do not infer a level from the Prompt body or rewrite it toward a preferred level.
- Flag ordinary content as overly specific when it fixes wording or example or feedback detail that the selected level leaves open. Flag it as overly abstract when it remains at the empty-outline level of "explain the concept", "add an example", or "ask a question" without the content, purpose, boundaries, or expected effect needed to execute it.
- At levels `1` and `2`, do not flag near-final learner-visible wording, concrete examples, transitions, or feedback wording merely because they are concrete; flag only expression specificity that contradicts the chosen level, teaching effect, source, runtime, or author constraints.
- At levels `4` and `5`, ordinary title, explanation, transition, already-required example identity and detail, and feedback wording that the level leaves open are omitted while the core question, intended understanding, critical facts and boundaries, every required example, and every required meaning and effect remain executable.
- At every level, recover the execution signature from the actual ordered runtime instructions. The complete teaching sequence, each slide's teaching function, slide count and order, content grouping and hierarchy, required teaching actions, and the placement of interactions, images, feedback, and the close match the approved internal execution plan. Treat a level-driven difference in that signature as a defect.
- When multiple level variants or an approved execution plan are in scope, compare the actual instruction sequences explicitly. For an isolated content-only Prompt with no supplied structure reference, record cross-level structural consistency as `not-assessed` rather than inferring a plan.
- At every level, unrequested font or color choices, pixel coordinates, and animations remain defects, and every item selected for exact preservation remains complete and exact at its resolved runtime position under its owning MarkdownFlow authoring, source-preservation, or image-authoring rule.
- In the standard visual-text scope—standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint—the Teaching Prompt begins with the direct instruction that makes the first learner-visible block one brief text lead-in; no arbitrary word-count or sentence-count quota is imposed.
- Within that scope, the lesson contains at least one substantive visual unit and repeats one visual-and-explanation pair per substantive teaching turn. Flag a visual opening, consecutive visual units, several visuals followed by one delayed explanation, and any unpaired learner-visible text turn after the lead-in as cadence defects.
- Across visual delivery modes, flag any visual unit whose sole purpose is to pad the lesson's length or pacing, whether newly proposed or already present. Do not treat a unit with a defined framing, orientation, transition, atmosphere, or teaching purpose as padding merely because it is non-substantive.
- Within that scope, each explanation appears before the next visual and adds context, relationship, reasoning, inference, or application rather than merely restating the preceding visual. The final explanation also performs the required close instead of leaving an isolated closing page or paragraph.
- Within that scope, a question-bearing interaction follows the question-only visual → unchanged `?[]` control → immediate feedback or explanation sequence. The question visual contains no duplicated option labels, input hint, simulated control, or answer, while an action-only control does not require an invented question visual.
- Pure classroom slides do not use Teaching Agent narration or paired explanatory text; explicit text-only delivery uses no visual units.
- A heading used to teach Markdown syntax, a code comment beginning with `#`, or a heading explicitly permitted by the author is flagged for review rather than automatically deleted.
- Interaction presence, placement, selection type, feedback effect, and lesson close match the resolved interaction policy.
- Each action or carryover has the downstream use required by `pedagogy.md`.
- Pure-slide, explicit text-only, and standard visual-text behavior match `pedagogy.md#visual-text-coordination`.
- A schema-bearing Teaching Prompt item passes all of `teaching-prompt.md#validation`. A content-only Prompt body passes every observable body and runtime check there; its schema envelope is `not-assessed`.

## Interaction and Variable Safety

- Every interaction has the observable instructional effect and branch behavior selected by `pedagogy.md`.
- Each control, option set, input hint, assignment, and branch instruction passes `markdownflow-authoring.md#validation`.
- Variable lifecycle is represented by the resolved control syntax, `used_variables`, and `global_variable_table`; adjacent Teaching Prompt prose states only feedback, branch, or carryover behavior performed during delivery.
- Every named variable has exactly one valid collection, complete supplied metadata, and a cross-lesson or Course Prompt consumer; lesson-local answers remain unnamed. Metadata checks are `not-assessed` when a content-only input does not supply the required table.
- The observed interaction and variable counts stay within `pedagogy.md` and `data-contracts.md`.
- Learner-facing content contains no unresolved authoring placeholder; runtime `UNKNOWN` behavior remains valid only where `markdownflow.md#variables` defines it.

## Runtime Stability

- MarkdownFlow syntax produces the observable effects defined in `markdownflow.md`.
- Deterministic and inline preservation forms match their selected scope.
- Code fences, required source spans, and applicable image records survive preprocessing and generation unchanged where required.
- When images are present, each one passes `image-authoring.md#image-output-validation`; when none are present, image authoring is not loaded or required.

## Course Prompt

- The existing Course Prompt keeps all six required sections in order and has no unresolved `XXX` placeholder.
- Every non-placeholder instruction remains behaviorally represented after localization.
- Standard and pure-slide delivery behavior matches `course-prompt.md`; its `# Slides` section contains the general presentation requirements applied uniformly to every slide, without special handling for a cover or any other slide position or teaching purpose and without duplicating or changing lesson pedagogy or lesson-specific slide structure.
- The complete artifact passes `course-prompt.md#materialization-checks` and `prompt-contracts.md`.

## Course Description

- The existing description clearly states audience fit, course topic, and supported outcomes.
- It contains no authoring notes, workflow state, unsupported guarantee, Prompt content, or structure dump.
- The complete artifact passes `course-description.md#validation`.

## Language and Repair Scope

- Every applicable human-readable surface passes `language-policy.md#language-audit`, including effective build values when those are in scope.
- When a Teaching Prompt contains an authoring rationale or a summary of its internal execution plan, classify each encoded requirement by its owning artifact. Fold lesson-specific behavior into the corresponding local teaching, slide, interaction, feedback, or close instruction; keep exact material at its original runtime position; and leave course-wide uniform presentation behavior with the Course Prompt. The repaired Teaching Prompt starts with the first learner-time instruction and proceeds in execution order.
- When personalization leaves ordinary expression open, repair the local instruction by retaining only its required learner-time content and effect. The shorter instruction carries that choice without a replacement explanation about adaptable wording or detail.
- Classify a passage by its function in learner-time execution, not by the presence of authoring vocabulary alone.
- Each applied change is the smallest coherent repair and has a traceable rationale.
- Remaining gaps are reported with their risk and owner instead of being hidden by broad rewriting.
