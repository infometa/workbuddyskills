# Authoring Controls

Read this file for every Segmentation, Orchestration, Generation, or Optimization task.

## Execution Modes

Two modes apply uniformly across all authoring phases:

- **Standard mode** (default): Input quality is sufficient; run phases in full with standard schemas.
- **Fallback mode**: When input is incomplete, conflicting, or low-quality, produce coarse outputs, mark uncertainty explicitly, and provide focused rerun hints. Extend output schemas with the phase-specific fields in `data-contracts.md#fallback-output-extensions`.

See `../examples/fallback-mode.md` for the four phase scenarios.

## Cross-File Concept Routing

Use the authoritative source for each aspect before authoring or auditing:

| Concept | Syntax / Format | Strategy / Rules | Schema / Data |
|---|---|---|---|
| Variables | `markdownflow.md#variables` | `pedagogy.md#variable-strategy` | `data-contracts.md#variable-table` |
| Interaction policy | `markdownflow.md#interactions` | `pedagogy.md#interaction-policy-precedence` and `pedagogy.md#interaction-design` | `data-contracts.md#interaction-policy` |
| Transfer signals | — | `pedagogy.md#transfer-signals` | `data-contracts.md#segment-schema` |
| Visual boundaries | `markdownflow.md#images` | `pedagogy.md#visual-text-coordination`, `generation-workflow.md#working-with-author-provided-images`, and `generation-workflow.md#slide-only-generation-override` | `data-contracts.md#segment-schema` |
| Preservation | `markdownflow.md#preservation` | `pedagogy.md#lesson-loop` | — |
| Output language | — | — | `data-contracts.md#language-resolution` |

## Authoring Control Inputs

Use these optional controls across authoring phases:

- `course_author_name` (string): course author's real name for the Course Prompt role.
- `course_profile` (json): audience and pedagogical parameters.
- `delivery_constraints` (json): platform limits, topic policy, and non-negotiable fragments.
- `interaction_policy` (json): normalized Course Design Intake result with `mode` and selected `purposes`; see `data-contracts.md#interaction-policy`.
- `target_language` (BCP-47 string): explicit output language; apply the global resolution rules in `session-controls.md#output-language`.

Field-level schemas and example JSON: `data-contracts.md#recommended-object-shapes`.
