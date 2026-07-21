# Pedagogy

Authoritative source for **Teaching Prompt** design constraints — patterns, cognitive techniques, segmentation methodology, optimization methodology, and the teaching-side rules around variables, interactions, and visual-text coordination. Violating anything here generally produces a Teaching Prompt that *runs* but teaches poorly.

For format syntax / runtime constraints (which make any prompt fail to parse), see [markdownflow.md](markdownflow.md). For Course Prompt design (the course-level AI persona / style document), see [course-prompt.md](course-prompt.md).

## Script Style

A Teaching Prompt is the per-lesson MarkdownFlow document the AI engine reads at runtime — it is a *script that guides teaching*, not a polished learner-facing lecture. Write in imperative, model-guiding language.

Preferred patterns:
- "Explain to the learner …"
- "Ask the learner to …"
- "Have the learner choose …"
- "After collecting {{var}}, restate the choice and branch …"

Disallowed patterns:
- Long, polished prose written as if it is the final learner-facing lecture.
- Author/lesson-plan meta narration (e.g., "Knowledge Block …", "In this lesson you will …", "Deliverable: …").
- Author-side meta labels such as "Knowledge Block 1/2/3", "Lesson Objective", or "Deliverable" — keep those as implicit structure, not visible narration.
- Exposing internal authoring terms in learner-facing text.

## Teaching Patterns

### Pattern A: Evidence Chain

1. Observable phenomenon
2. Mechanism explanation
3. Practical implication
4. Learner interaction
5. Summary and action

### Pattern B: Misconception Repair

1. Surface common misconception
2. Explain why it sounds plausible
3. Correct with mechanism and boundary
4. Run interaction check
5. Apply corrected model to a real case

### Pattern C: Comparison-Driven Learning

1. Baseline response capture
2. Alternate scenario or constraint
3. Side-by-side interpretation
4. Updated decision path

## Cognitive Techniques

Increase learner understanding through targeted cognitive moves rather than information dumping. Each lesson should include at least one of these as a deepening interaction.

1. **Calibration prompt** — Ask learners to make a concrete judgment before explanation.
2. **Boundary framing** — Clarify where the concept works and where it breaks.
3. **Counterintuitive contrast** — Introduce a surprising but valid case to deepen mental models.
4. **Action translation** — Turn conceptual understanding into an immediately executable step.
5. **Reflection loop** — Ask learners to compare current understanding with prior assumptions.

## Lesson Loop

Every lesson must satisfy a minimum teaching loop and a few cross-cutting constraints:

- **Minimum teaching loop**: setup → explanation → interaction → close. A lesson missing any of these four phases is incomplete.
- **One core question per lesson**: each lesson resolves exactly one teachable question.
- **Action tasks** must be either immediately executable by the learner or explicitly linked to a downstream lesson — no orphan actions.
- **Variable naming** must be consistent and traceable across lessons (use the same name for the same concept; cross-check with [data-contracts.md#variable-table](data-contracts.md#variable-table)).
- **Source information density** must be preserved through optimization — do not trade substance for fluency.
- **Carryover statements** are allowed only when cross-lesson dependency is explicitly permitted; otherwise remove them along with any unbound carryover variables.

## Segmentation Methodology

### Objective

Produce stable lesson-oriented semantic segments from noisy source material while preserving immutable artifacts.

### Core Rules

1. Preserve source order unless explicit ordering hints are provided.
2. Keep code/image/table blocks immutable.
3. Segment by semantic shift, not heading depth alone.
4. Keep each lesson candidate centered on one teachable question.
5. Attach source spans to every segment.

### Segment Types

- `concept`: explanatory statements and definitions.
- `example`: concrete demonstrations and walkthroughs.
- `code`: executable or pseudo-code blocks.
- `image`: visual references and diagrams.
- `exercise`: learner action prompts.
- `transition`: bridge text that links ideas.

### Transfer Signals

Every segment should include transferable signals for downstream script quality:
- learner hook
- evidence type
- visual cue
- concept conflict
- boundary cue
- action cue
- density cue
- quote cue
- visual-text-pair cue
- interaction-intent cue
- compare cue

### Failure Handling

If structure is weak, output a fallback segmentation and mark uncertain spans for focused reruns.

## Optimization Methodology

### Principles

1. Correctness before style.
2. Minimal safe edits before broad rewrites.
3. Learner impact before formatting polish.
4. Traceable changes with explicit rationale.

### Issue Taxonomy

- Coverage gap
- Meaning shift
- Explanation clarity
- Interaction no-branching
- Visual requirement missing
- Variable or syntax risk

### Execution Sequence

1. Build source-to-script coverage matrix.
2. Rank issues by learner risk and runtime risk.
3. Fix blockers first.
4. Revalidate variable lifecycle and interaction effects.
5. Run final syntax and density checks.

## Variable Strategy

These are the *teaching* rules around variables — when to collect, how often, how to ensure they matter. For variable *syntax* see [markdownflow.md#variables](markdownflow.md#variables); for variable *schema* see [data-contracts.md#variable-table](data-contracts.md#variable-table).

- Prefer at most one variable collection per module; distribute, don't front-load.
- Max five interactions per lesson (recommended three to four).
- No more than three consecutive variable collections before learner-visible feedback.
- Reuse global variables when possible; add lesson-local variables only when required.
- Every variable must have downstream utility (branching, depth control, or deliverable variation).
- Do not recollect the same variable unless explicitly marked as staged comparison.
- Prevent semantic duplicates even when variable names differ.
- Spread global variable collection across lessons.

## Interaction Design

These are the *teaching* rules around interactions. For interaction *syntax* see [markdownflow.md#interactions](markdownflow.md#interactions).

- Each lesson includes at least one deepening interaction (calibration, boundary check, or misconception correction — see [Cognitive Techniques](#cognitive-techniques)).
- Interaction prompts must be concrete and directly answerable.
- Place interactions at decision points, not only at lesson start.
- Every interaction must trigger immediate feedback **and** a visible downstream effect (branching explanation, examples, practice difficulty, feedback).
- After every interaction, restate the learner's selection explicitly as an instruction (e.g., `Restate the learner's current choice as {{var}}.`), not as polished narration.
- `*_viewpoint_check` interactions must branch by option and drive different next steps.
- Use no more than one `viewpoint_check` per lesson unless justified.
- Avoid repetitive interaction semantics across lessons unless comparison intent is explicit.
- For input interactions, the pre-interaction question must be more specific than the short `...` placeholder.

## Visual-Text Coordination

- If a visual is needed, describe it in natural language (e.g., "Show an image that …").
- Pair every visual instruction with a brief explanation of what the visual is meant to convey.
- Do not embed raw SVG/HTML/Mermaid/PlantUML/Graphviz markup inside Teaching Prompts unless the user explicitly asks for that format.
- Default to natural-language image/diagram placeholders.
- Every core concept needs visual + textual explanation together; the visual carries structural prompting, the text carries the full explanation (assume the learner has not seen the image).
