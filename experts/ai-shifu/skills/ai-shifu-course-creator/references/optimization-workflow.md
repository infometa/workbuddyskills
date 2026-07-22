# Optimization Workflow

Audit an existing, substantially complete course artifact set and apply the smallest repairs that restore correctness, fidelity, pedagogy, and runtime safety. Optimization does not perform first-time course authoring or deployment.

## Required References

- `language-policy.md`
- `authoring-mode.md#mode-selection`
- `data-contracts.md#optimization-fallback-fields`
- `optimization-checklist.md`
- `report-template.md#optimization-report`

## Conditional References

- When authoritative source material or selected immutable spans are in the audit scope: `source-preservation.md`

## Entry Conditions

Use this workflow only when the supplied artifact set already contains the Teaching Prompts and any Course Prompt or course description that the requested audit covers. If a required artifact is absent, report it as outside the Optimization scope instead of silently creating it here.

Declare the audit scope before editing: one lesson, selected artifacts, or the complete existing course. When multiple versions exist, identify the authoritative version.

A pasted Prompt body may be audited as a content-only artifact. Apply every check observable from that body, but do not invent an absent lesson-schema envelope, variable table, or other metadata. Record checks that require unprovided envelope data as `not-assessed` in the Optimization report.

## Optimization Method

1. When authoritative source material is supplied, build a source-to-artifact coverage map for the declared scope. Otherwise, declare a content-only audit and do not claim external-source fidelity.
2. Run every applicable observable check in `optimization-checklist.md`.
3. Classify each finding and rank it by learner risk and runtime risk.
4. Repair blockers first with the narrowest coherent edit.
5. Revalidate the changed artifact and every directly affected consumer.
6. Record each change, its rationale, and any remaining issue in the Optimization report.

Apply these priorities throughout:

1. Correctness before style.
2. Minimal safe edits before broad rewrites.
3. Learner impact before formatting polish.
4. Traceable changes before unexplained cleanup.

## Controlled Rewriting

- With authoritative source material in scope, preserve its coverage, intended meaning, information density, and every selected immutable span. In a content-only audit, preserve the meaning and information density expressed by the supplied artifact without claiming comparison against an absent source.
- Allow filler removal, sentence smoothing, and local structural repair only when those invariants still pass.
- Never introduce a silent factual change or an unmarked omission of required evidence.
- Broaden a rewrite only when a smaller edit cannot resolve the issue coherently; record why and revalidate affected source coverage when source material is in scope.
- After touching an interaction, variable, branch instruction, image instruction, or deterministic span, rerun its owner-defined authoring and runtime checks.

## Issue Taxonomy

- Coverage gap
- Meaning shift
- Explanation clarity
- Interaction effect or branching gap
- Visual requirement missing
- Variable or syntax risk
- Artifact-boundary violation

## Outputs

Return the minimally repaired existing artifacts plus the Optimization report, applying `language-policy.md` to every changed or reported value.

Under fallback mode, add only the Optimization extensions defined in `data-contracts.md#optimization-fallback-fields`.

Optimization must not create a Course Prompt, course description, or Teaching Prompt from scratch, choose new preservation scope on behalf of an earlier phase, build a course directory, or publish a course.

## Validation

- The conclusion and overall risk appear first in the report.
- Every applicable item in `optimization-checklist.md` passes, or the remaining gap is explicitly reported.
- Each repair is the smallest coherent change and retains the meaning and density observable in the supplied scope. When source material is in scope, it also retains source coverage and immutable content.
- Repaired artifacts still satisfy their owning contracts.
- Checks that require unprovided schema-envelope data are reported as `not-assessed`, never guessed or silently marked as passing.
- Any fallback extension matches `data-contracts.md#optimization-fallback-fields` and remains additive to the standard output.
