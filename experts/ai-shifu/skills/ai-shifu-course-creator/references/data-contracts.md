# Data Contracts

Authoritative source for schemas, enum values, and cross-field invariants at the boundaries between authoring phases.

## Required References

None.

## Input Contract

### Required

Provide one of:

- A single long transcript or course document.
- A set of topic-aligned documents with intended order.

### Optional

- Learner persona.
- Lesson granularity preference (`short`, `medium`, `long`).
- Tone constraints.
- Non-negotiable source fragments.
- `course_author_name` (string): the optional name the author wants the Teaching Agent to use as the teacher identity during course delivery. A blank or unanswered value normalizes to an empty string, which produces no named teacher identity in the Course Prompt.
- `course_profile` object.
- `delivery_constraints` object.
- `interaction_policy` object.
- `teaching_prompt_personalization_level` (integer from `1` through `5`): a course-wide, transient authoring input that controls how much learner-visible wording, explanation, already-required example identity and detail, and feedback wording each Teaching Prompt predetermines. It does not control teaching or slide structure.

### Teaching Prompt Personalization Level

`teaching_prompt_personalization_level` is a top-level scalar and transient authoring input, and it must be strictly an integer from `1` through `5`. It is not a member of `course_profile`, `delivery_constraints`, or `interaction_policy`. Its author-facing names, level semantics, and materialization rules are owned exclusively by `teaching-prompt.md#personalization-levels`.

This is a content-expression control, not a structure control. It never changes the internal lesson execution plan, including the teaching sequence, required actions and effects, slide count and order, or interaction and feedback placement.

Pass the normalized value unchanged through the in-memory authoring handoff to Teaching Prompt generation and, when applicable, optimization review. Its only effect on `teaching_prompt` is the amount of ordinary wording and already-permitted example detail materialized inside direct local runtime instructions. Keep the control's name, value, and authoring semantics absent from Prompt bodies, output fields, course-directory files, CLI inputs or configuration, all build or deployment payloads including `shifu-import.json`, and platform metadata. In particular, do not serialize this control as a field in `lesson_teaching_prompts`, `course_index`, `global_variable_table`, `course_prompt`, `course_description`, or fallback output extensions.

### Recommended Object Shapes

#### `course_profile`

```json
{
  "audience_level": "beginner|intermediate|advanced",
  "prerequisite_level": "none|basic|strong",
  "lesson_duration_minutes": 12,
  "lesson_count_target": 8,
  "assessment_mode": "quiz|project|discussion|mixed"
}
```

#### `delivery_constraints`

```json
{
  "platform_limits": ["no_iframe", "markdown_only"],
  "must_cover_topics": ["topic-a", "topic-b"],
  "avoid_topics": ["topic-x"],
  "non_negotiable_fragments": ["required source fragment or code block id"]
}
```

#### Interaction Policy

```json
{
  "mode": "enabled|disabled|unspecified",
  "purposes": [
    "learner_context",
    "pre_content_thinking",
    "lesson_end_self_check"
  ]
}
```

- `mode` is required and must be exactly `enabled`, `disabled`, or `unspecified`.
- `purposes` is required, duplicate-free, and may contain only `learner_context`, `pre_content_thinking`, and `lesson_end_self_check`.
- `enabled` requires a non-empty `purposes` array. `disabled` and `unspecified` require an empty `purposes` array.

### Input Invariants

- Input files must be readable text or Markdown.
- When multiple files are provided, their order must be explicit.
- `interaction_policy` must satisfy its mode and purpose invariants.
- When present, `teaching_prompt_personalization_level` must be an integer from `1` through `5`. Reject booleans, floats, numeric strings, and out-of-range values rather than coercing them.

## Output Contract

Full-course authoring produces these required artifacts:

1. `lesson_teaching_prompts` — one item per lesson; see [Lesson Schema](#lesson-schema).
2. `course_index` — an array of course-index items.
3. `global_variable_table` — see [Variable Table](#variable-table).
4. `course_prompt` — a course-level Markdown string.
5. `course_description` — a learner-facing description string stored in `course-description.md`.

### `course_index` Schema

Each array item contains:

- `lesson_id` (string, required).
- `lesson_title` (string, required).
- `core_question` (string, required).
- `source_span_map` (array of `{source_id, start, end}`, required).

## Segment Schema

Each Segmentation item contains:

- `segment_id` (string, required) — stable within the run.
- `segment_type` (string enum, required) — one value from [Segment Types](#segment-types).
- `core_point` (string, required) — the single teachable point.
- `preserve_block` (boolean, required) — `true` exactly when the source span is selected as immutable; otherwise `false`.
- `source_span` (object, required):
  - `source_id` (string, required).
  - `start` (non-negative integer, required) — inclusive character offset.
  - `end` (integer greater than `start`, required) — exclusive character offset.
- `transfer_signals` (object, required) — satisfies [Transfer Signals](#transfer-signals).

Entries in `course_index.source_span_map` use the same `source_span` object shape.

### Segment Types

| Value        | Meaning                                   |
| ------------ | ----------------------------------------- |
| `concept`    | Explanatory statements and definitions.   |
| `example`    | Concrete demonstrations and walkthroughs. |
| `code`       | Executable or pseudo-code blocks.         |
| `image`      | Image files and their source references.  |
| `exercise`   | Learner action prompts.                   |
| `transition` | Bridge text that links ideas.             |

### Transfer Signals

`transfer_signals` must be non-empty. Include every applicable canonical key, omit inapplicable keys, and give every included key a non-empty, concise string value.

| Key | Meaning |
| --- | --- |
| `learner_hook` | Teaching entry point. |
| `evidence_type` | Form of source evidence. |
| `visual_cue` | Cue for expressing the segment as a slide. |
| `concept_conflict` | Conceptual conflict or misconception. |
| `boundary_cue` | Applicability boundary. |
| `action_cue` | Executable application. |
| `density_cue` | Information that must not be compressed away. |
| `quote_cue` | Quotation that should be preserved or used. |
| `visual_text_pair_cue` | Division of work between slide and text. |
| `interaction_intent_cue` | Interaction purpose and expected instructional effect. |
| `compare_cue` | Comparison objects or dimensions. |

## Variable Table

`global_variable_table` is an array. Each item contains:

- `name` (string, required) — the name referenced by `{{var}}` or `?[%{{var}} ...]`; letters, numbers, and underscores only.
- `collected_in` (string, required) — `lesson_id` where the variable is first collected.
- `used_in` (array of strings, required) — every lesson that references the variable through `{{var}}`, plus reserved value `course_prompt` when the Course Prompt references it. Include `collected_in` only if that lesson also references `{{var}}` after collection.
- `effect_scope` (string constant `cross_lesson`, required).

Only named variables belong in `global_variable_table`; no-variable `?[...]` interactions do not create entries. Every referenced learner-answer variable has exactly one variable-backed collection and one matching table entry. Every table entry has cross-lesson or Course Prompt use and lists every consumer in `used_in`.

## Lesson Schema

Each `lesson_teaching_prompts` item contains:

- `lesson_id` (string, required) — stable and deterministic.
- `lesson_title` (string, required) — concise learner-facing title.
- `teaching_prompt` (string, required) — per-lesson Teaching Prompt content in MarkdownFlow.
- `used_variables` (array of strings, required) — every named variable collected or referenced in the lesson; no-variable interactions are excluded.
- `depends_on_lessons` (array of lesson ids, required) — empty when none.

Every item in `used_variables` has a matching `global_variable_table` entry. The matching entry lists the lesson in `used_in` when the variable is referenced outside its collection control, and also lists `course_prompt` when the Course Prompt references it.

Chapter titles, numbering, hierarchy labels, and ordering markers belong in `course_index` or `structure.json`, not in the Teaching Prompt body.

## Fallback Output Extensions

Fallback mode augments the standard schema with the fields below. Standard mode omits them.

### Segmentation Fallback Fields

Per segment:

- `uncertainty` (string enum `low|medium|high`) — confidence in the segment's interpretation.

Top-level:

- `rerun_hints` (array of strings) — focused prompts describing the authoritative input needed to resolve uncertainty.

### Orchestration Fallback Fields

Per `course_index` item:

- `uncertainty` (string enum `low|medium|high`).

Top-level, required when any lesson is uncertain:

- `rerun_plan` (object):
  - `lessons_to_rerun` (array of lesson ids).
  - `reason` (string) — why the rerun is needed.

### Generation Fallback Fields

Per lesson:

- `fallback_mode` (boolean constant `true`) — identifies a lesson generated in fallback mode.
- `assumptions` (array of strings) — assumptions made because input is incomplete or conflicting.
- `upgrade_notes` (array of strings) — additional input that would allow a standard-mode lesson.

### Optimization Fallback Fields

Inside `risk_and_issue_report`:

- `coverage_status` (string enum `complete|partial|unknown_without_source`).

Top-level:

- `follow_up` (array of strings) — inputs needed to complete a full-coverage audit.
