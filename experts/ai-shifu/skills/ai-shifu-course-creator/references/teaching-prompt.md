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
4. Resolve and lock one lesson skeleton from the approved design, selected pedagogy, delivery mode, and interaction policy without using the personalization level to decide any structural surface. For standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, resolve the complete lead-in and visual-and-explanation cadence from `pedagogy.md#visual-text-coordination` at this step.
5. Apply the normalized `teaching_prompt_personalization_level` only to content expression within that fixed skeleton through [Personalization Levels](#personalization-levels).
6. Express the resulting decisions as executable instructions under `prompt-contracts.md#prompt-semantics`.
7. Apply `markdownflow-authoring.md` after those teaching decisions are complete.
8. Load `image-authoring.md` only when the lesson actually uses an image asset.

Every lesson must carry enough direction to run with the Course Prompt contributing only course-wide role and general presentation requirements shared by every slide. Do not rely on the Course Prompt to supply, repair, or override lesson pedagogy, lesson-specific slide structure, or treatment tied to a particular slide position or teaching purpose.

Enough direction means that the Teaching Agent can identify what must be taught, why it matters, the complete teaching order and content slots, the teaching purpose of every content slot and slide, the intended learner effect, and the completion condition. The selected personalization level decides how much ordinary learner-visible wording, already-required example identity and detail, transition wording, and feedback wording to prewrite within the fixed lesson skeleton.

## Personalization Levels

Course Design Intake resolves one course-wide integer and passes it unchanged to every Teaching Prompt generated in that authoring run. Before applying it, resolve one fixed lesson skeleton from the approved lesson design, selected pedagogy, delivery mode, and interaction policy. The skeleton includes the teaching sequence and the required presence, position, and teaching purpose of every content slot, including titles, ordinary explanations, examples, transitions, interactions, images, feedback states, and the close. When slides are used, it also includes the exact slide count, each slide's ordinal position and teaching purpose, required content groups, visual hierarchy, and semantic layout.

Apply the level only to the expressive realization inside that skeleton. A higher value gives the Teaching Agent more freedom to adapt ordinary title wording, explanations, transition wording, the identity and details of already-required examples, and non-deterministic feedback wording to learner context that is already available. It never makes any content slot optional or required. Across levels, never add, omit, or relocate a content slot; add, remove, reorder, split, or merge slides; move content between slides; change any content slot's or slide's teaching purpose; change content grouping, visual hierarchy, or layout; alter the teaching sequence; or move an interaction, image, feedback state, or close. The level never authorizes new learner-context collection, interactions, variables, or branches.

| Level | Author-facing name | Teaching Prompt materialization |
| --- | --- | --- |
| `1` | High determinism | Within the fixed lesson skeleton, prewrite exact or near-final title wording, selected example details, ordinary explanations, transitions, and feedback wording. Let the Teaching Agent make only minor fluency or learner-context substitutions that preserve meaning. |
| `2` | Determinism-leaning | Within the fixed lesson skeleton, prescribe the main title wording, example identity and key details, principal explanation language, and required feedback points. Let the Teaching Agent paraphrase transitions, secondary elaboration, incidental example details, and non-essential feedback phrasing. |
| `3` | Balanced | Within the fixed lesson skeleton, fix each title's communicative meaning, each example slot's type and teaching point, all key definitions and conclusions, and each feedback response's required meaning and effect. Leave ordinary explanation, example-detail, transition, and feedback phrasing adaptable. |
| `4` | Personalization-leaning | Within the fixed lesson skeleton, specify each title's intent, must-cover points, every required example slot's selection constraints and intended takeaway, and the required feedback effect. Let the Teaching Agent choose most non-exact title, example, explanation, transition, and feedback wording from available learner context. |
| `5` | High personalization | Within the fixed lesson skeleton, state the concrete message and outcome for every content slot, critical facts and boundaries, every required example slot's material requirements and intended takeaway, and feedback completion conditions and effects needed for execution. Let the Teaching Agent choose all other title wording, example identity and details, explanation phrasing, transitions, and feedback phrasing. |

Levels `1` and `2` may produce near-final learner-visible delivery, but the artifact remains a Prompt rather than stage directions or a mandatory spoken transcript. Levels `4` and `5` must retain enough content and effect to execute without guessing; do not reduce them to an empty outline such as "explain the concept", "add an example", or "ask a question".

### Cross-Level Constraints

The level changes only content-expression specificity. It does not change factual or source fidelity, the selected teaching pattern and loop, interaction policy, variable lifecycle, delivery mode, Course Prompt responsibility, or the fixed lesson skeleton.

At every level, keep these structural decisions unchanged:

- the complete teaching sequence and every content slot's position and teaching purpose;
- the exact slide count, slide order and placement in the teaching loop, each slide's teaching purpose, content grouping, visual hierarchy, and semantic layout; and
- whether and where titles, ordinary explanations, examples, transitions, interactions, images, feedback states, and the close appear. Every required content slot remains populated at every level. For a required example slot, only its permitted identity and details may vary. Each slot's required meaning and effect stay fixed even when its non-exact wording remains adaptable.

Once selected by their owning contracts, keep these constraint islands exact without expanding their scope:

- the complete learner-facing interaction question, the `?[]` form, option wording and order, variable assignment and references, literal `UNKNOWN` behavior, and the selected feedback or branch effect;
- deterministic output and required code or fence structure;
- regulated wording, fixed numeric thresholds, and source spans already selected as immutable;
- wording or layout the author explicitly requires; and
- selected image URLs, alt or caption text, ordering, and form.

Apply each island through its owning MarkdownFlow authoring, source-preservation, or image-authoring reference at every level. A lower level does not automatically add MarkdownFlow deterministic markers, and a higher level never relaxes an exact island.

## Lesson Materialization

Each Teaching Prompt must:

- Start with the teaching-start behavior defined in `pedagogy.md#lesson-loop`, not a copied chapter title.
- For standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, materialize instructions that produce one brief learner-visible text lead-in followed by at least one substantive visual-and-explanation pair, with every explanation before the next visual and the final explanation carrying the close, exactly as defined in `pedagogy.md#visual-text-coordination`. Express every required visual unit as an explicit slide or image instruction in the Teaching Prompt.
- Resolve exactly one core question through the selected teaching pattern.
- Make the teaching objective, must-cover facts and boundaries, and required explanatory relationships unambiguous at the specificity selected by the normalized personalization level.
- Use the interaction or non-interactive loop selected by the normalized policy.
- Preserve required source evidence and any downstream deliverable defined by the lesson design.
- Close with the summary, decision checkpoint, or action required by the selected pattern.

Whenever a Teaching Prompt creates one or more slides, give slide 1 a clear cover-page visual treatment with lesson title and author information. Apply every other slide and explanation rule normally for the selected delivery mode.

For pure classroom slides, materialize the required visible content and teaching effects from `pedagogy.md#visual-text-coordination` as a fixed slide skeleton with an exact count, order, placement, teaching purpose for each slide and content slot, content grouping, visual hierarchy, and semantic layout. Then use the selected personalization level only to decide how much title, body, example, transition, and feedback wording to prewrite inside that skeleton. General slide presentation and delivery-mode behavior remain owned by `course-prompt.md`.

## Outputs

Produce one `lesson_teaching_prompts` item per lesson using `data-contracts.md#lesson-schema`. Apply `language-policy.md` to authored strings and preserve machine-facing values and immutable source spans.

Under fallback mode, add only the Generation extensions defined in `data-contracts.md#generation-fallback-fields`.

## Validation

- Every `teaching_prompt` is valid runnable MarkdownFlow.
- Every item passes `data-contracts.md#lesson-schema`.
- The normalized personalization level is an integer from `1` through `5`, and the Teaching Prompt's content-expression specificity matches that level.
- The fixed lesson skeleton is resolved before the level is applied and is explicit enough that the Teaching Agent cannot change the teaching sequence; add, omit, or relocate a content slot; change any content slot's or slide's teaching purpose; change slide count, slide placement, content grouping, visual hierarchy, or layout; or change the placement of interactions, images, feedback, and the close.
- When multiple level variants are generated from the same approved design and controls, their structural signatures are identical, including every content slot's and slide's teaching purpose and the presence and placement of every example slot; only content-expression specificity may differ.
- In standard one-on-one teaching and the standard teaching branch of combined delivery, except under an explicit text-only constraint, the first non-empty instruction makes the first learner-visible block a brief text lead-in rather than a heading, slide, or image; the fixed skeleton contains at least one substantive visual unit, no consecutive visual units, one concise but complete explanation after every visual and before the next, no unpaired learner-visible text turn after the lead-in, and a final explanation that also performs the close.
- A standard question-bearing interaction uses the question-only visual, unchanged `?[]` control, and immediate feedback or explanation sequence defined by `pedagogy.md#visual-text-coordination`; pure classroom slides and explicit text-only delivery retain their respective overrides.
- When a Teaching Prompt creates one or more slides, slide 1 has a clear cover-page visual treatment with lesson title and author information, and every other slide or explanation behavior follows the selected delivery mode's existing rules.
- In other delivery modes, the first non-empty instruction produces the applicable teaching-start behavior and does not duplicate structure metadata.
- The Teaching Prompt contains the selected teaching method and does not outsource pedagogy to the Course Prompt.
- The Teaching Prompt fixes lesson-specific slide structure, teaching purpose, and position- or purpose-specific treatment without restating the general presentation requirements that the Course Prompt applies to every slide.
- The objective, must-cover facts and boundaries, required sequence, interaction effect, and close are specific enough to execute without guessing.
- Levels `1` and `2` provide the requested near-final specificity without introducing unrequested typography, color, coordinates, animation, or deterministic markers.
- Levels `4` and `5` leave ordinary wording and example or feedback detail open without omitting the executable teaching content or effect and without delegating structure to the Teaching Agent.
- Level `3` preserves the balanced division defined in the level table rather than silently behaving like either endpoint.
- Every resolved constraint island remains exact at every level.
- Interaction, variable, branch, and preservation encoding pass `markdownflow-authoring.md`.
- Image-specific validation runs only for lessons that use image assets.
- Authored human-facing content passes `language-policy.md`.
