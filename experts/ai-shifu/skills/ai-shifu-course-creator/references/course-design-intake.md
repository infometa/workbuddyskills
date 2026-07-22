# Course Design Intake

Collect and normalize the author's design choices before course structure or Teaching Prompt generation begins. This file owns the author-facing preview of what each choice changes; the course pipeline, artifact schemas, and actual teaching effects remain defined by their downstream owners.

## Required References

- `language-policy.md`
- `data-contracts.md#input-contract`
- `data-contracts.md#interaction-policy`
- `data-contracts.md#teaching-prompt-personalization-level`
- `pedagogy.md#interaction-policy-precedence`
- `pedagogy.md#visual-text-coordination`
- `teaching-prompt.md#personalization-levels`

## Intake Scope

Collect only the unresolved design choices requested by the selected authoring route. Deployment, authentication, platform management, and analytics questions are outside this file.

Before asking anything, extract answers already present in the user's instruction, source material, or pulled course directory. Ask only for missing items, one choice at a time and in the order below. Do not invent defaults from a sparse topic or brief, and do not proactively offer to bypass a required choice or “decide for the author.” Apply a listed fallback only after the author explicitly skips that question or asks to continue without answering.

Before every applicable question, give a concise effect preview in `resolved_target_language`. Name the downstream course decision that the answer controls and describe the learner- or author-visible effect of every option presented. Surface the relevant AI-Shifu capability through that concrete consequence — such as one-on-one guidance, classroom projection, answer-informed teaching, AI voice with slides, or lesson granularity — without adding a separate sales pitch or an unsupported outcome. If an effect preview is the first user-facing introduction of the Teaching Agent concept in the conversation, follow `language-policy.md#teaching-agent-first-mention` before using its short name. Never present only bare option labels, numbers, or names. When the answer is a free-form value such as a chapter or lesson count, explain the tradeoff dimensions before asking instead of inventing choices.

1. Ask which usage scenarios the course should support. Explain that this answer controls the learner's delivery experience: personalized AI one-on-one self-study lets the Teaching Agent guide one learner directly and adapt ordinary explanation or feedback to available learner context; interactive classroom slides produce projection-ready content paced by a human instructor; the combined option prepares the course for both experiences.
2. Unless the course is slide-only, ask how much personalization freedom the final learner-facing course should allow. Explain that a higher level makes the Teaching Prompt emphasize teaching intent and key points while fixing less exact learner-facing wording, example identity and detail, and feedback wording. State that the complete teaching sequence, exact slide count, each slide's position and teaching purpose, and which content slots appear, where they appear, and what teaching purpose each serves — including whether an example is required — stay fixed at every level; only expression inside those slots varies. State that the level uses only learner context already available and never authorizes new context collection, interactions, variables, or branches. Present all five ordered choices from `teaching-prompt.md#personalization-levels`: `1` — High determinism, `2` — Determinism-leaning, `3` — Balanced, `4` — Personalization-leaning, and `5` — High personalization. Render the question, option names, and owner-defined behavior descriptions in `resolved_target_language`; each description must say what the author will see fixed in advance and what the Teaching Agent may adapt for the learner. Do not silently skip this question for standard or combined delivery. For slide-only delivery with no already-provided level, do not ask it and use level `1` (High determinism).
3. Ask what interactions should do. Explain each purpose's effect from `pedagogy.md#interaction-policy-precedence`: learner-context collection occurs at an early course or module point and gives later teaching selected context to use, pre-content thinking or misconception activation gives the following explanation an initial judgment to refine, and lesson-end self-check lets the learner check or consolidate the lesson's core understanding. Explain that choosing none removes learner-answer controls and uses worked applications, demonstrations by the Teaching Agent, or consolidation instead of leaving a teaching gap.
4. Unless the course is slide-only, ask whether Listen Mode should be enabled. Explain that enabling it adds AI voice with slides and consumes more AI-Shifu credits, while disabling it leaves the course available without Listen Mode and avoids that additional credit consumption. An unanswered question defaults to disabled.
5. Ask for the desired chapter and lesson counts. Explain that the chapter count controls how lessons are grouped into broader topics, while the lesson count controls course granularity and how much material each single-question lesson must resolve: fewer lessons concentrate more material into each lesson, while more lessons distribute it across more single-question units. Neither choice may drop required source material or break source order.
6. When a Course Prompt is in scope, ask what name the author wants AI-Shifu's Teaching Agent to use as the teacher identity during course delivery. Explain that providing a name lets the Teaching Agent teach under that teacher identity, while leaving it blank does not affect course creation. Accept a free-form answer; an unanswered question defaults to no named teacher identity.

## Normalized Design Controls

Produce these controls once and pass them unchanged to downstream workflows:

- **Usage scenario**: normalize personalized AI self-study to standard one-on-one delivery, classroom projection to pure-slide delivery, and an explicit combined choice to both modes. If skipped, infer the delivery mode from source structure. Teaching and presentation effects remain in their owning references.
- **Teaching Prompt personalization level**: preserve an explicit integer from `1` through `5` as the top-level `teaching_prompt_personalization_level` and pass it unchanged. Reuse a value already present in context instead of asking again, including for pure-slide delivery. When pure-slide delivery has no explicit value, normalize directly to level `1` without asking. For standard or combined delivery, apply fallback level `3` only when the author explicitly skips or asks to continue without answering; absence alone is not a skip, and the level must not be inferred from source style or other controls. Level semantics and materialization remain owned by `teaching-prompt.md#personalization-levels`.
- **Interaction policy**: one or more purposes produces `enabled` with exactly those purposes; none produces `disabled` with an empty `purposes` array; skipped produces `unspecified` with an empty `purposes` array. Validate only the shape against `data-contracts.md#interaction-policy`; teaching effects belong to `pedagogy.md#interaction-policy-precedence`.
- **Listen Mode**: pure slides always disable it. Otherwise preserve the explicit answer or use disabled after a skipped/unanswered question.
- **Chapter and lesson counts**: preserve the explicit numbers. If skipped, infer them from source volume and lesson granularity rather than using a fixed count.
- **Course author name**: preserve the supplied free-form `course_author_name`. If the supplied value is blank, or the question is skipped or unanswered, use an empty string; an empty value means the Course Prompt has no named teacher identity.

## Validation

- Every answer available from existing context is reused rather than asked again.
- Every missing applicable question is asked before its fallback is applied.
- Every asked question includes an effect preview that identifies its downstream course decision, and every presented option describes its learner- or author-visible consequence rather than showing a bare label.
- Effect previews match their owning references, surface relevant AI-Shifu capabilities through concrete course behavior, and make no promotional or unsupported promise.
- The first effect preview that introduces the Teaching Agent concept follows `language-policy.md#teaching-agent-first-mention`.
- Pure-slide delivery resolves an otherwise missing `teaching_prompt_personalization_level` to level `1` without asking the personalization question.
- The normalized `teaching_prompt_personalization_level` passes `data-contracts.md#teaching-prompt-personalization-level`; invalid values are rejected rather than converted or treated as a skip.
- The normalized interaction policy passes the data-contract invariants.
- The selected delivery mode, Listen Mode, and structure constraints are internally consistent.
