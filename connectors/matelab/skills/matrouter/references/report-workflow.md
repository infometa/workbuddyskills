# MatRouter Report Projection

Turn an assembled EvidenceBundle handle and its exact read views into
human-readable prose without creating a second, independently editable evidence
truth.

## Workflow

1. Keep the acquisition result's immutable `bundle_ref`. Inspect `operation_state`,
   `summary`, and `source_issues` for attempt counts, failed sources, configuration
   gaps, and incomplete retrieval. `completed_with_gaps` is not complete coverage.
2. Use `matrouter_read_evidence` with that `bundle_ref` and a `records`, `items`, `attempts`,
   or `sources` view. Follow `next_cursor` as `cursor` without repeating the
   Bundle or view. Preserve `data_total`, `data_shown`, `data_truncated`, and
   `content_omitted` when assessing what was actually read. If source issues or
   row content are omitted, use `matrouter_export_evidence_bundle` for the complete canonical
   object. For `delivery="http_download"`, save its non-null `download_url`
   outside model context. If the client cannot save the returned delivery type,
   report that limitation without reading the complete resource into context.
3. Separate source-reported data, deterministic calculations performed with
   declared parameters, literature context and Agent interpretation.
4. Preserve qualified source, source ID, units, method context, warnings,
   lineage declarations and artifact provenance where relevant.
5. If more data are needed, extend the relevant Bundle with `matrouter_search_materials`,
   `matrouter_get_material_data`, or `matrouter_get_thermochemical_entries`. Use `matrouter_retry_sources` only
   for an intentional new attempt with returned retryable `attempt_ref` values.
   Continue reporting from the derived `bundle_ref`; retain its
   `derived_from_bundle_ref` and do not mix relative refs from different Bundles.

## Required Content

- material subject, Evidence Kinds, and source scope;
- sources attempted and all non-success outcomes;
- observed values/artifacts with units and context;
- missing fields, mismatches, warnings and provenance limits;
- methods and parameters used for derived calculations;
- the Agent's bounded interpretation and useful next action.

Do not infer scientific support from route readiness or execution success. Do
not equate formation energy with hull stability, formula with phase identity, or
different source IDs with proven independence. External literature statements
remain separate from MatRouter retrieval provenance.
