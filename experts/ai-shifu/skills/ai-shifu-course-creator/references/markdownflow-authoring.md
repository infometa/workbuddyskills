# MarkdownFlow Authoring

Encode already-resolved teaching, interaction, variable, and preservation decisions into MarkdownFlow. Parser recognition and runtime effects remain defined only in `markdownflow.md`.

## Required References

- `language-policy.md`
- `data-contracts.md#variable-table`
- `pedagogy.md#interaction-design`
- `pedagogy.md#variable-strategy`
- `pedagogy.md#visual-text-coordination`
- `markdownflow.md`

## Conditional References

- When immutable source spans were selected for encoding: `source-preservation.md`

## Interaction Encoding

- Encode the complete learner-facing question in the block immediately before every question-bearing interaction control, and put the unchanged `?[]` control on its own line.
- In standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, make that preceding block a question-only visual instruction and place the control immediately after it. Make the complete question the visual's central content, without option labels, input hints, simulated controls, or answers. Pure classroom slides retain their projection behavior, and explicit text-only delivery uses ordinary question text as the preceding block, as defined in `pedagogy.md#visual-text-coordination`.
- Keep only option labels, the optional `%{{name}}` assignment prefix, and any free-text marker plus short hint inside `?[]`.
- For an action-only control such as `?[Continue]`, do not invent a learner question or question slide; put the control on its own line after the content or instruction it advances.
- Use `|` for single-select, `||` for multi-select, and `...` immediately before the input hint or custom-answer label.
- Use `%{{name}}` only when the answer must leave the current lesson. Lesson-local answers use the no-variable form; a blank variable name is invalid.
- For input interactions, use a specific question in the preceding block and a shorter hint after `...` in the control; in standard visual-text delivery, that preceding block is the question-only visual. For select-plus-input, put `...` at the start of the custom-answer option.
- Keep the complete option set, order, and wording only in the interaction control. In the standard visual-text scope, do not duplicate those labels on the question-only visual.
- After the control, encode the feedback or visible instructional effect selected by `pedagogy.md#interaction-design`.

Standard visual-text shapes:

```markdown
Create a question-only slide whose complete central question is "Which path best matches the current case?" Do not show option labels, simulated controls, or the answer.

?[Path A | Path B]

After the learner answers, explain the selected path and contrast it with the other path.

Create a question-only slide whose complete central question is "What course-wide goal should later lessons use?" Do not show an input hint or simulated input field.

?[%{{learning_goal}} ...One-sentence goal]

After the learner responds, acknowledge the goal and explain that later lessons will use it to adapt examples and emphasis.
```

## Variable and Branch Encoding

- Write branch behavior as natural-language instructions; MarkdownFlow has no programmatic conditional syntax.
- Refer to lesson-local answers naturally rather than inventing a variable.
- For a named value, first bind the substituted value in a natural sentence such as `The learner goal is {{learning_goal}}.`, then describe branches against that value.
- When a named value can be read before collection, branch on the literal substituted value `UNKNOWN`; do not test readiness or marker existence.
- Every named learner-answer reference must have a matching variable-backed collection and pass `data-contracts.md#variable-table`.
- Compose newly authored variable names under `language-policy.md` using only letters, numbers, and underscores. Preserve existing names when changing them would break the contract.

## Preservation Encoding

When immutable source spans were selected, load `source-preservation.md` and encode only those spans:

- Put a complete standalone single-line span that must bypass the Teaching Agent inside `===...===`.
- Put a complete multi-line span that must bypass the Teaching Agent inside `!===...!===`; include the full code fence and language tag when exact fenced output is required.
- In otherwise generated content, wrap only the position- and formatting-sensitive span inline with `===...===`. Inline preservation remains mediated by the Teaching Agent and may be translated.
- Encode each selected span independently and leave adaptive content outside deterministic markers.

Image composition is owned by `image-authoring.md` and is loaded conditionally by the selected workflow.

## Validation

- Every interaction control is on its own line and matches the preceding question or options. Standard question-bearing controls immediately follow their question-only visual instructions and precede their feedback or explanatory effects.
- Every named variable passes collection, reference, and metadata invariants.
- Branch instructions use natural language and literal `UNKNOWN` where required.
- Each immutable span uses the runtime form matching its selected preservation scope.
