# Teaching Prompt

Generate one runnable per-lesson Teaching Prompt from approved segments and design controls. This file materializes teaching decisions; it does not define pedagogy, MarkdownFlow runtime behavior, or image handling.

## Required References

- `language-policy.md`
- `prompt-contracts.md`
- `data-contracts.md#teaching-prompt-personalization-level`
- `data-contracts.md#lesson-schema`
- `data-contracts.md#generation-fallback-fields`
- `pedagogy.md`
- `markdownflow-authoring.md`

## Conditional References

- When an image asset must be understood, uploaded, embedded, or validated: `image-authoring.md`

## Generation

1. Select the teaching pattern that best fits the lesson's core question and source evidence. Preserve the pattern order defined in `pedagogy.md#teaching-patterns`; do not force every lesson into Evidence Chain.
2. Apply the normalized interaction policy without adding unselected purposes or blanket interactions.
3. Resolve the teaching objective, must-cover evidence and boundaries, required path, interaction purpose and visible effect, and required close from the approved lesson design.
4. Build one internal lesson execution plan from the approved design, selected pedagogy, delivery mode, and interaction policy without using the personalization level to decide its structure. Resolve the ordered teaching actions, every required content position and effect, interaction and feedback adjacency, close, and, when slides are used, exact slide count and order. For standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, resolve the complete lead-in and visual-and-explanation cadence from `pedagogy.md#visual-text-coordination` at this step.
5. Apply the normalized `teaching_prompt_personalization_level` only to how much ordinary wording and example detail generation includes at each position in that plan through [Personalization Levels](#personalization-levels).
6. Materialize the plan as direct local instructions to the Teaching Agent in learner-time execution order. Begin with the first teaching action for the selected delivery mode. At each position, combine the action with the content, relationship, boundary, or intended effect needed there; the resulting sequence and adjacency carry the lesson structure. When the level leaves ordinary expression open, write only those required runtime elements and end the instruction there.
7. Insert every selected interaction, deterministic block, required code or source span, and image instruction directly at its resolved learner-time position using its owning syntax. Express variable lifecycle through the MarkdownFlow control and schema fields; write only the feedback, branch, or carryover behavior the Teaching Agent performs into the Prompt body.
8. Apply `markdownflow-authoring.md` after those teaching decisions are complete.
9. Load `image-authoring.md` only when the lesson actually uses an image asset.

Every lesson must carry enough direction to run with the Course Prompt contributing only course-wide role and general presentation requirements shared by every slide. Do not rely on the Course Prompt to supply, repair, or override lesson pedagogy, lesson-specific slide structure, or treatment tied to a particular slide position or teaching purpose.

Enough direction means that the ordered runtime instructions tell the Teaching Agent what to teach, show, ask, and respond at each point; why the required relationships and boundaries matter; what effect each interaction must have; and how the lesson completes. The selected personalization level decides how much ordinary learner-visible wording, already-required example identity and detail, transition wording, and feedback wording to include in those local instructions.

## Personalization Levels

Course Design Intake resolves one course-wide integer and passes it unchanged to every Teaching Prompt generated in that authoring run. Before applying it, resolve one internal lesson execution plan from the approved lesson design, selected pedagogy, delivery mode, and interaction policy. The plan includes the teaching sequence and the required presence, position, and teaching effect of titles, ordinary explanations, examples, transitions, interactions, images, feedback states, and the close. When slides are used, it also includes the exact slide count, each slide's ordinal position and teaching function, required content groups, visual hierarchy, and semantic layout.

Apply the level only while writing the local runtime instructions for that plan. A higher value writes less ordinary title, explanation, transition, example-detail, and non-deterministic feedback wording while retaining the concrete message, evidence, boundaries, selection constraints, and effect needed to execute each position. The shorter local instruction itself represents the open expression; no runtime sentence substitutes for the omitted wording or detail. Every level materializes the same teaching actions, slide order and grouping, interactions, images, feedback states, and close. The level adds no learner-context collection, interactions, variables, or branches. The level itself and this authoring rationale remain in the in-memory handoff.

| Level | Author-facing name | Teaching Prompt materialization |
| --- | --- | --- |
| `1` | High determinism | Write exact or near-final title wording, selected example details, ordinary explanations, transitions, and feedback wording into the corresponding runtime instructions. Permit only minor fluency or learner-context substitutions that preserve meaning. |
| `2` | Determinism-leaning | Write the main title wording, example identity and key details, principal explanation language, and required feedback points. Leave ordinary transition wording, secondary elaboration, incidental example details, and non-essential feedback phrasing unwritten. |
| `3` | Balanced | Write each title's communicative meaning, each required example's type and teaching point, all key definitions and conclusions, and each feedback response's required meaning and effect. Include ordinary explanation detail only where it is needed for reliable execution. |
| `4` | Personalization-leaning | Write each title's intent, must-cover points, each required example's selection constraints and intended takeaway, and the required feedback effect. Omit ordinary title, example-detail, explanation, transition, and feedback wording that is not needed to preserve those requirements. |
| `5` | High personalization | Write the concrete message and outcome for every teaching action, critical facts and boundaries, each required example's material requirements and intended takeaway, and feedback completion conditions and effects. Omit all other ordinary wording and example identity or detail. |

Levels `1` and `2` may produce near-final learner-visible delivery, but the artifact remains a Prompt rather than a mandatory spoken transcript. Levels `4` and `5` retain enough content and effect to execute without guessing; an empty outline such as "explain the concept", "add an example", or "ask a question" is incomplete.

### Cross-Level Constraints

The level changes only content-expression specificity. It does not change factual or source fidelity, the selected teaching pattern and loop, interaction policy, variable lifecycle, delivery mode, Course Prompt responsibility, or the internal lesson execution plan.

The actual ordered runtime instructions at every level implement the same structural decisions:

- the complete teaching sequence and the position and effect of every required teaching action;
- the exact slide count, slide order and placement in the teaching loop, each slide's teaching function, content grouping, visual hierarchy, and semantic layout; and
- whether and where titles, ordinary explanations, examples, transitions, interactions, images, feedback states, and the close appear. Every required action remains executable at every level. For a required example, only its permitted identity and details may vary; its required meaning and effect remain fixed.

Insert material selected for exact preservation directly at its resolved runtime position:

- the complete learner-facing interaction question, the `?[]` form, option wording and order, variable assignment and references, literal `UNKNOWN` behavior, and the selected feedback or branch effect;
- deterministic output and required code or fence structure;
- regulated wording, fixed numeric thresholds, and source spans already selected as immutable;
- wording or layout the author explicitly requires; and
- selected image URLs, alt or caption text, ordering, and form.

Apply each item through its owning MarkdownFlow authoring, source-preservation, or image-authoring reference at every level. A level changes ordinary expression only; exact material keeps its selected form and scope.

## Lesson Materialization

Each Teaching Prompt must:

- Begin its body with a direct instruction that produces the teaching-start behavior defined in `pedagogy.md#lesson-loop`.
- For standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, express the lesson as one brief learner-visible text lead-in followed by the ordered local instructions for at least one substantive visual-and-explanation pair. Place every explanation instruction before the next visual instruction and make the final explanation perform the close, exactly as defined in `pedagogy.md#visual-text-coordination`.
- Resolve exactly one core question through the selected teaching pattern.
- Make the teaching objective, must-cover facts and boundaries, and required explanatory relationships unambiguous at the specificity selected by the normalized personalization level.
- Use the interaction or non-interactive loop selected by the normalized policy.
- Preserve required source evidence and any downstream deliverable defined by the lesson design.
- Close with the summary, decision checkpoint, or action required by the selected pattern.
- Place each interaction's complete learner-facing question, unchanged `?[]` control, and immediate feedback instruction next to one another at the point where the interaction affects teaching.

Whenever a Teaching Prompt creates one or more slides, give slide 1 a clear cover-page visual treatment with lesson title and author information. Apply every other slide and explanation rule normally for the selected delivery mode.

For pure classroom slides, write the complete ordered sequence of direct slide-creation instructions needed by `pedagogy.md#visual-text-coordination`. Each instruction supplies that slide's required visible content, teaching function, content grouping, visual hierarchy, and semantic layout at the specificity selected by the personalization level. General slide presentation and delivery-mode behavior remain owned by `course-prompt.md`.

## Outputs

Produce one `lesson_teaching_prompts` item per lesson using `data-contracts.md#lesson-schema`. Apply `language-policy.md` to authored strings and preserve machine-facing values and immutable source spans.

Under fallback mode, add only the Generation extensions defined in `data-contracts.md#generation-fallback-fields`.

## Validation

- Every `teaching_prompt` is valid runnable MarkdownFlow.
- Every item passes `data-contracts.md#lesson-schema`.
- The normalized personalization level is an integer from `1` through `5`, and the Teaching Prompt's content-expression specificity matches that level.
- The internal lesson execution plan is resolved before the level is applied. Recover the execution signature from the Teaching Prompt's actual ordered instructions and verify that it matches the plan: teaching actions, slide count and order, content grouping and hierarchy, interaction and feedback adjacency, images, and the close all occur at their resolved positions with their resolved effects.
- When multiple level variants are generated from the same approved design and controls, compare their actual ordered runtime instructions. They have identical execution signatures, including the presence, position, and teaching function of every required example; only ordinary content-expression specificity may differ.
- The Teaching Prompt body begins with the first learner-time teaching instruction for the selected delivery mode, and every following instruction performs a learner-time teaching, presentation, interaction, feedback, or close function.
- In standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, the first instruction makes the first learner-visible block a brief text lead-in; the actual instruction sequence contains at least one substantive visual unit, no consecutive visual units, one concise but complete explanation after every visual and before the next, no unpaired learner-visible text turn after the lead-in, and a final explanation that also performs the close.
- A standard question-bearing interaction uses the question-only visual, unchanged `?[]` control, and immediate feedback or explanation sequence defined by `pedagogy.md#visual-text-coordination`; pure classroom slides and explicit text-only delivery retain their respective overrides.
- When a Teaching Prompt creates one or more slides, slide 1 has a clear cover-page visual treatment with lesson title and author information, and every other slide or explanation behavior follows the selected delivery mode's existing rules.
- In other delivery modes, the first instruction produces the applicable teaching-start behavior.
- The Teaching Prompt contains the selected teaching method and does not outsource pedagogy to the Course Prompt.
- The Teaching Prompt's actual slide instructions implement lesson-specific order, content, teaching function, and position- or purpose-specific treatment without restating the general presentation requirements that the Course Prompt applies to every slide.
- The objective, must-cover facts and boundaries, required sequence, interaction effect, and close are specific enough to execute without guessing.
- Levels `1` and `2` provide the requested near-final specificity without introducing unrequested typography, color, coordinates, animation, or deterministic markers.
- Levels `4` and `5` omit ordinary wording and example or feedback detail that the selected level leaves open while every required teaching action, content relationship, boundary, and effect remains executable in the actual instruction sequence.
- At levels `2` through `5`, open ordinary expression is visible as a shorter local instruction, not as a runtime explanation of who may choose or adapt the omitted wording, example identity or detail, transition, or feedback phrasing.
- Level `3` preserves the balanced division defined in the level table rather than silently behaving like either endpoint.
- Every item selected for exact preservation appears in its required form at its resolved runtime position at every level.
- Interaction and variable lifecycle decisions appear through their resolved MarkdownFlow syntax and schema fields; related Prompt prose performs only the required feedback, branch, or carryover behavior.
- Interaction, variable, branch, and preservation encoding pass `markdownflow-authoring.md`.
- Image-specific validation runs only for lessons that use image assets.
- Authored human-facing content passes `language-policy.md`.
