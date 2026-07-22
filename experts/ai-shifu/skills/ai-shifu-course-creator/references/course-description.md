# Course Description

Create and validate the learner-facing SEO and listing description for a course. This file owns only the description artifact; it does not define course structure, lesson pedagogy, Prompt behavior, or deployment metadata precedence.

## Required References

- `language-policy.md`
- `data-contracts.md#input-contract`
- `data-contracts.md#output-contract`

## Authoring

Derive the description from the approved course topic, target learner, prerequisite level, course-level goal, and concrete learning outcomes. State what the learner will understand or be able to do, using only claims supported by the source and approved course design.

- Write complete learner-facing prose in `resolved_target_language`.
- Make the opening specific enough to work as listing copy and search-result context.
- Prefer concrete outcomes and audience fit over workflow terminology or generic praise.
- Keep author-side assumptions, issue notes, implementation details, and deployment status out of the description.
- Do not copy the Course Prompt, lesson sequence, or structure metadata into the description.

## Output

Populate `course_description` and write the same learner-facing content to `course-description.md` in the generated course directory.

## Validation

- The target learner, course topic, and concrete outcomes are clear.
- Every substantive claim is supported by approved source material or design controls.
- The complete artifact passes `language-policy.md`.
- No authoring notes, unresolved placeholders, unsupported guarantees, or machine-facing metadata appear.
