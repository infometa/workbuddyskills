# MatRouter Query

Use MatRouter to retrieve material records, structures, properties and artifacts
while preserving exact source identity and execution status.

## Workflow

1. Inspect sources only when source configuration or coverage is unknown.
   Continue with its returned `next_cursor` as `cursor`, omitting the original
   `sources` and `evidence_kind` filters.
2. Let the Agent choose `sources`: a nonempty list selects exact sources and an
   empty list means all qualified sources. Ranking is operational ordering
   metadata, never a source-membership filter.
3. Call `matrouter_search_materials` directly with one formula or elements subject. Keep
   its `bundle_ref` and returned `record_ref` values.
4. For detail work, call `matrouter_get_material_data` with that base Bundle, exact record
   references, and requested data kinds. Use `matrouter_get_thermochemical_entries` for
   an exact element system.
5. Use `matrouter_read_evidence` for bounded records, items, attempts, or sources. The
   items view contains only structures and scientific artifacts with `item_ref`,
   not inherited source records. On continuation send the returned
   `next_cursor` as `cursor`; do not repeat `bundle_ref` or `view`. Use
   `matrouter_export_evidence_bundle` for the exact complete canonical object and prefer
   its direct HTTP `download_url`; do not inject the complete MCP resource into
   model context or reconstruct chunks. If that URL expires, export the same
   Bundle again for a fresh URL while its `bundle_ref` remains active.
6. Retry only returned attempt references from `source_issues` or the attempts view. Preserve every `SourceOutcome` in
   its exact Bundle execution and pass only returned `bundle_ref + item_ref`
   pairs to explicit scientific methods.

The packaged server uses remote HTTP, so do not call `matrouter_download_source_file`:
its `output_path` is server-local and cannot deliver a file to the client.
`matrouter_list_source_files` remains useful only for inspecting source-native file
availability. Prefer typed acquisition or a returned HTTP `download_url`. A
download is not bundle data until typed acquisition materializes it.

## Source Guidance

- Materials Project: computed summaries, structures, property documents, bands,
  DOS and thermodynamic records when credentials are available.
- OQMD: public computational records, formation energies, structures and scalar
  properties; do not relabel formation energy as hull stability.
- AFLOW: public records, structures, scalar properties and listed processed/raw
  artifacts.
- JARVIS-DFT: fixed data snapshots, structures, properties and Figshare-linked
  artifacts.
- Alexandria: public native search and structures; report upstream failures.
- NOMAD: entry metadata, archives, structures and upload-dependent raw files.
- COD / MPDS: experimental crystallographic records and literature metadata.
- TCOD: theoretical crystallography records.
- C2DB: two-dimensional structures and source-native properties.
- MaterialsGalaxy: aggregated search plus credentialed structures, topology and
  specialist datasets.
- OPTIMADE: provider-qualified common records and structures; native-only
  artifacts remain outside its interface.

## Interpretation

- Missing fields are missing data, not negative results.
- Preserve source, source ID, units, warnings, citations and source metadata.
- Keep `ready` separate from succeeded and failed execution status. Keep warnings
  separate from execution status and derive empty only from complete record
  retrieval with zero returned records.
- Do not merge experimental and computational records without saying so.
- Do not infer agreement, confidence or independence from source count alone.
- Report unavailable routes and credential blockers when they affect coverage.

Summarize material identity, source IDs, observed values with units, method or
dimensional context, warnings, missing data and useful follow-up routes.
