# MatRouter Screening

Screening is an Agent workflow over routed data, not a fixed MatRouter policy.

## Workflow

1. State composition space, required properties, ranges, source preferences,
   missing-data treatment and output size.
2. Call `matrouter_search_materials` for the formula or elements and selected sources;
   retain its `bundle_ref` and exact returned `record_ref` values.
3. Call `matrouter_get_material_data` with that base Bundle, selected refs, and requested
   `data_kinds`. Read the resulting immutable Bundle through bounded
   `matrouter_read_evidence` pages; no separate route, execute, or assemble tool is needed.
4. Apply user-declared filters and ranking in the Agent control plane.
5. Preserve missing fields, warnings and provenance in the candidate table.
6. Retrieve follow-up structures or artifacts only for candidates that need them.

If the user gives a vague term such as “good semiconductor” or “stable
catalyst”, propose explicit criteria and label them as assumptions. Do not
present them as universal thresholds or built-in MatRouter rules.

## Patterns

- Semiconductor search: filter the observed band-gap field, then inspect
  stability-related data separately.
- Stability search: prefer hull distance, source-native stability fields or
  phase-diagram data; formation energy alone is not stability.
- Two-dimensional materials: preserve dimensionality and prefer 2D-specific
  sources such as C2DB when appropriate.
- Experimental structures: prefer COD/MPDS and keep literature provenance.

Return rank, formula/material ID, qualified source, observed criteria, important
context, warnings, missing fields and recommended next data. Separate
“promising under the declared screen” from a confirmed scientific conclusion.
