# Prompt Contracts

Define the semantics shared by Teaching Prompts and Course Prompts, plus the responsibility boundary between those two artifacts. This file does not route workflows or own syntax, pedagogy, schemas, or materialization.

## Required References

- `markdownflow.md#interactions`
- `markdownflow.md#deterministic-blocks`

## Prompt Semantics

The **Teaching Agent** is AI-Shifu's learner-time AI role that executes Course Prompts and Teaching Prompts during course delivery, gives interaction feedback, and answers learner follow-up questions. A deployment may route those responsibilities to different underlying models, but this skill always refers to the product role as the Teaching Agent.

Teaching Prompts and Course Prompts are Prompts, not Scripts. The Teaching Agent consumes them. Their purpose is to tell the Teaching Agent how to teach the learner: what to explain, ask, show, adapt, and how to respond. They are not text for a person to read aloud or finished lesson prose addressed directly to the learner.

Set the amount of prewritten delivery from the artifact's owning rules and applicable design controls. Regardless of that amount, state the behavior and outcome the Teaching Agent must produce, the information and boundaries it must not omit, and any ordering or adaptation that materially affects the result.

The Teaching Prompt's selected personalization level is a content-expression control, not a structure control. It controls only ordinary title and explanation wording, transition wording, the identity and details of already-required examples, and non-deterministic feedback wording within an already fixed lesson and slide structure. Which content slots are required, where they appear, and the teaching purpose each content slot and slide serves are fixed before the level is applied; its owning definition is [teaching-prompt.md#personalization-levels](teaching-prompt.md#personalization-levels).

For a Teaching Prompt, make the core question, teaching objective, must-cover evidence and boundaries, complete teaching path, fixed slide structure, each required content slot's and slide's teaching purpose, interaction purpose and visible effect, and required close concrete enough to execute. Depending on its selected personalization level, the same fixed content slots may contain near-final learner-visible wording or intent-and-constraint direction. Directions such as "explain the concept", "add an example", or "ask a question" are incomplete when they do not identify the content, purpose, or expected effect.

Precision chosen for ordinary content expression is separate from exact output. Use MarkdownFlow deterministic forms only when exactness protects correctness, teaching effect, runtime behavior, source fidelity, or an explicit author requirement; choosing a more deterministic Teaching Prompt does not make its ordinary content immutable. The owning pedagogy, MarkdownFlow authoring, image, and source-preservation references decide the applicable form.

Address imperative instructions to the Teaching Agent. When an instruction refers to a learner action or experience, name that person explicitly as "the learner" or "the student", for example:

- "Explain ... to the learner."
- "Ask the student to ..."

Within Prompt instructions, every second-person form in any language refers only to the Teaching Agent. This includes `you`, `your`, `yours`, and `yourself` in English and `你`, `您`, and their possessive forms in Chinese. Learner-visible text inside a MarkdownFlow `?[]` interaction or [standalone deterministic output](markdownflow.md#deterministic-blocks) is the exception: it may use second-person forms to address the learner because the platform displays that content directly or verbatim. Outside `?[]` and standalone deterministic output, do not use a second-person form to mean the learner.

Do not turn a Prompt into stage directions or a mandatory spoken transcript. A Teaching Prompt may contain near-final learner-visible wording when its selected personalization level calls for it, but the level never changes the already fixed teaching sequence, slide structure, or teaching purpose of any content slot or slide, and the artifact remains an instruction consumed by the Teaching Agent. Keep author-side structure implicit: do not emit labels such as "Knowledge Block 1/2/3", "Lesson Objective", or "Deliverable", and do not expose internal authoring terms in learner-facing output. Authoring rules, pipeline notes, and process instructions stay in skill docs and references, never in Prompt content; internal design notes may appear only in HTML comments when needed. Do not prescribe routine wording details merely to make a Prompt look complete when neither the selected level nor an explicit constraint calls for them.

## Artifact Responsibilities

This file owns the semantics shared by Teaching Prompts and Course Prompts and the top-level responsibility boundary between the two artifacts. Detailed syntax, teaching decisions, schemas, and materialization rules live in the sources indexed below.

- A **Teaching Prompt** is the per-lesson runtime instruction artifact. It owns the lesson's teaching intent and execution, including whether and where that lesson uses slides, each slide's teaching purpose and required content, and any treatment tied to a particular slide's position or teaching purpose. It also owns learner interactions and variable collection.
- A **Course Prompt** is the course-level runtime instruction artifact. It owns shared role, general presentation requirements applied uniformly to every slide, and intentional cross-lesson personalization, but it follows each Teaching Prompt and does not own lesson pedagogy, lesson-specific slide structure, or special handling for an individual slide position or purpose. It may reference persisted learner variables; it contains no MarkdownFlow `?[]` interaction controls, does not collect learner input, and does not define lesson-local branches.
