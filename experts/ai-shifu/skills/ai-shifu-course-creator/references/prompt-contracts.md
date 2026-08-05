# Prompt Contracts

Define the semantics shared by Teaching Prompts and Course Prompts, plus the responsibility boundary between those two artifacts. This file does not route workflows or own syntax, pedagogy, schemas, or materialization.

## Required References

- `markdownflow.md#interactions`
- `markdownflow.md#deterministic-blocks`

## Prompt Semantics

The **Teaching Agent** is AI-Shifu's learner-time AI role that executes Course Prompts and Teaching Prompts during course delivery, gives interaction feedback, and answers learner follow-up questions. A deployment may route those responsibilities to different underlying models, but this skill always refers to the product role as the Teaching Agent.

Teaching Prompts and Course Prompts are Prompts, not Scripts. The Teaching Agent consumes them. Their purpose is to tell the Teaching Agent how to teach the learner: what to explain, ask, show, adapt, and how to respond. They are not text for a person to read aloud or finished lesson prose addressed directly to the learner.

Set the amount of prewritten delivery from the artifact's owning rules and applicable design controls. Regardless of that amount, state the behavior and outcome the Teaching Agent must produce, the information and boundaries it must not omit, and any ordering or adaptation that materially affects the result.

The Teaching Prompt's selected personalization level is a transient authoring control, not runtime Prompt content. Orchestration resolves the lesson and slide structure first, then the level controls how much ordinary title, explanation, transition, example-detail, and non-deterministic feedback wording generation writes into the local runtime instructions. Its owning definition is [teaching-prompt.md#personalization-levels](teaching-prompt.md#personalization-levels).

For a Teaching Prompt, turn the resolved lesson design into the actual sequence of learner-time teaching actions. Make the core question, teaching objective, must-cover evidence and boundaries, ordered teaching path, slide or image actions, interaction behavior and visible effect, and required close concrete enough to execute. Depending on its selected personalization level, a local instruction may include near-final learner-visible wording or only the message, evidence, boundaries, selection constraints, and effect needed at that point. When ordinary expression remains open, end the local instruction after those required runtime facts and effects; leaving the rest unwritten is the materialization of that authoring choice. Directions such as "explain the concept", "add an example", or "ask a question" are incomplete when they do not identify the content, purpose, or expected effect.

Precision chosen for ordinary content expression is separate from exact output. Use MarkdownFlow deterministic forms only when exactness protects correctness, teaching effect, runtime behavior, source fidelity, or an explicit author requirement; choosing a more deterministic Teaching Prompt does not make its ordinary content immutable. The owning pedagogy, MarkdownFlow authoring, image, and source-preservation references decide the applicable form.

Materialize interaction and variable lifecycle choices through the resolved MarkdownFlow control, `used_variables`, and `global_variable_table`. Teaching Prompt prose carries the feedback, branch, or cross-lesson use that the Teaching Agent must perform; the machine-facing encoding choice remains in its syntax and schema fields.

Address imperative instructions to the Teaching Agent. When an instruction refers to a learner action or experience, name that person explicitly as "the learner" or "the student", for example:

- "Explain ... to the learner."
- "Ask the student to ..."

Within Prompt instructions, every second-person form in any language refers only to the Teaching Agent. This includes `you`, `your`, `yours`, and `yourself` in English and `你`, `您`, and their possessive forms in Chinese. Learner-visible text inside a MarkdownFlow `?[]` interaction or [standalone deterministic output](markdownflow.md#deterministic-blocks) is the exception: it may use second-person forms to address the learner because the platform displays that content directly or verbatim. Outside `?[]` and standalone deterministic output, do not use a second-person form to mean the learner.

A Prompt remains an instruction consumed by the Teaching Agent rather than a mandatory spoken transcript. Every part of its body serves learner-time delivery by specifying a teaching action, required content, presentation or interaction behavior, feedback or branch behavior, or learner-visible exact material. Represent the lesson structure through the order and grouping of those runtime instructions. Authoring state such as the fixed-skeleton model, personalization rationale, pipeline notes, and preservation classifications remains in the in-memory handoff and owning references. Runtime-facing labels appear only when they perform a real teaching or delivery function. Write ordinary wording and detail only to the degree selected by the personalization level or required by an explicit constraint.

## Artifact Responsibilities

This file owns the semantics shared by Teaching Prompts and Course Prompts and the top-level responsibility boundary between the two artifacts. Detailed syntax, teaching decisions, schemas, and materialization rules live in the sources indexed below.

- A **Teaching Prompt** is the per-lesson runtime instruction artifact. It owns the lesson's teaching intent and execution, including whether and where that lesson uses slides, each slide's teaching purpose and required content, and any treatment tied to a particular slide's position or teaching purpose. It also owns learner interactions and variable collection.
- A **Course Prompt** is the course-level runtime instruction artifact. It owns shared role, general presentation requirements applied uniformly to every slide, and intentional cross-lesson personalization, but it follows each Teaching Prompt and does not own lesson pedagogy, lesson-specific slide structure, or special handling for an individual slide position or purpose. It may reference persisted learner variables; it contains no MarkdownFlow `?[]` interaction controls, does not collect learner input, and does not define lesson-local branches.
