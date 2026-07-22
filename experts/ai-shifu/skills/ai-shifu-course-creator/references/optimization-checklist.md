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
- Chapter titles, lesson titles, numbering, hierarchy, and ordering remain in structure metadata rather than Teaching Prompt bodies.
- No artifact relies on another artifact to supply behavior that its owner requires locally.

## Teaching Prompt Behavior

- Each lesson resolves one core question through a complete loop and valid teaching pattern under `pedagogy.md`.
- When `teaching_prompt_personalization_level` is supplied, the Teaching Prompt's ordinary title and explanation wording, transition wording, example detail, and non-deterministic feedback wording match `teaching-prompt.md#personalization-levels`.
- When that level is absent from a content-only audit or supplied metadata, record personalization-level alignment as `not-assessed`; do not infer a level from the Prompt body or rewrite it toward a preferred level.
- Flag ordinary content as overly specific when it fixes wording or example or feedback detail that the selected level leaves open. Flag it as overly abstract when it remains at the empty-outline level of "explain the concept", "add an example", or "ask a question" without the content, purpose, boundaries, or expected effect needed to execute it.
- At levels `1` and `2`, do not flag near-final learner-visible wording, concrete examples, transitions, or feedback wording merely because they are concrete; flag only expression specificity that contradicts the chosen level, teaching effect, source, runtime, or author constraints.
- At levels `4` and `5`, ordinary title, explanation, transition, already-required example identity and detail, and feedback wording remain open to runtime adaptation without omitting the core question, intended understanding, critical facts and boundaries, any required example, or the required meaning and effect of each fixed content slot.
- At every level, keep the complete teaching sequence, every content slot's and slide's teaching purpose, slide count, slide order and placement in the teaching loop, content grouping, every required content slot's presence and placement, visual hierarchy, semantic layout, and the placement of interactions, images, feedback, and the close fixed. Treat any structural or teaching-purpose change made because of the personalization level as a defect.
- When multiple level variants or an approved lesson skeleton are in scope, compare their structural signatures explicitly. For an isolated content-only Prompt with no supplied structure reference, record cross-level structural consistency as `not-assessed` rather than inferring a skeleton.
- At every level, unrequested font or color choices, pixel coordinates, and animations remain defects, and each resolved constraint island remains complete and exact under its owning MarkdownFlow authoring, source-preservation, or image-authoring rule.
- In the standard visual-text scope—standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint—the first non-empty instruction makes the first learner-visible block one brief text lead-in instead of a heading, structure label, slide, or image; no arbitrary word-count or sentence-count quota is imposed.
- Within that scope, the lesson contains at least one substantive visual unit and repeats one visual-and-explanation pair per substantive teaching turn. Flag a visual opening, consecutive visual units, several visuals followed by one delayed explanation, a cover or decorative or objective-only page, and any unpaired learner-visible text turn after the lead-in as cadence defects.
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
- Standard and pure-slide delivery behavior matches `course-prompt.md`; lesson pedagogy is not duplicated there.
- The complete artifact passes `course-prompt.md#materialization-checks` and `prompt-contracts.md`.

## Course Description

- The existing description clearly states audience fit, course topic, and supported outcomes.
- It contains no authoring notes, workflow state, unsupported guarantee, Prompt content, or structure dump.
- The complete artifact passes `course-description.md#validation`.

## Language and Repair Scope

- Every applicable human-readable surface passes `language-policy.md#language-audit`, including effective build values when those are in scope.
- Each applied change is the smallest coherent repair and has a traceable rationale.
- Remaining gaps are reported with their risk and owner instead of being hidden by broad rewriting.
