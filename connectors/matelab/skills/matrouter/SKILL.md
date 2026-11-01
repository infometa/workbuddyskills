---
name: matrouter
description: "Use MatRouter to discover and route heterogeneous materials-data sources, aggregate source-qualified records into provenance-preserving EvidenceBundle objects, retrieve scientific artifacts, and run explicit methods over exact inputs, including structure matching, phase diagrams, and band/DOS rendering. Use for materials records, structures, properties, bands, DOS, elastic tensors, thermochemical entries, source coverage, and auditable multi-source research."
display_name: "MatRouter 材料数据与分析"
display_name_en: "MatRouter Materials Data Analysis"
description_zh: "跨材料数据库检索结构、性质与计算数据，保留数据来源；支持结构匹配、相图计算及能带、态密度可视化。"
description_en: "Search structures, properties and calculations across materials databases with source provenance; match structures, calculate phase diagrams, and visualize bands and density of states."
version: "0.1.2"
author: "MatRouter contributors"
---

# MatRouter

Use MatRouter as a routing and aggregation data plane. Let the Agent choose the
source/record scope, explicit scientific method, interpretation, and prose. Do
not turn retrieval success into a scientific verdict.

Inspect the host's actual MCP `tools/list` before using a capability. MatRouter
has one goal-shaped surface plus `matrouter_match_structures`,
`matrouter_compute_phase_diagrams`, `matrouter_render_band_structure`, and
`matrouter_render_density_of_states`. Do not simulate tools absent from `tools/list`.
The tool names in this Skill are raw MCP names; let the client resolve their
namespace.

If MatRouter MCP is unavailable, ask the user to connect the packaged
`matrouter` server. Do not bypass it with provider HTTP APIs, substitute local
file processing, or guess source data. If client authorization expires, ask
the user to authorize through the client; never request bearer tokens or put
credentials, identities, or authentication headers in tool arguments.

## Choose a Reference

- Read `references/query.md` for search, records, structures, sources, and files.
- Read `references/electronic-properties.md` for bands, DOS, phonons, transport,
  optical data, topology, and elastic tensors.
- Read `references/screening.md` for user-declared filters and rankings.
- Read `references/phase-diagram.md` before retrieving entries or constructing a hull.
- Read `references/structure-identity.md` before comparing structures.
- Read `references/report-workflow.md` when projecting a bundle into prose.
- Read `references/mcp-setup.md` for setup, credentials, or connection failures.

## Core Control Loop

1. Call `matrouter_search_materials` directly for formula/element discovery. There is no
   prepare/begin call: the first real acquisition creates internal authority
   state and returns an immutable `bundle_ref` plus short `record_ref` values.
2. Call `matrouter_inspect_sources` only when source coverage or configuration is
   uncertain. Copy its `next_cursor` into `cursor` and omit the original source
   and Evidence Kind filters. Treat `ready` as configured, not healthy or
   scientifically sufficient.
3. Call `matrouter_get_material_data` with the exact base `bundle_ref`, returned
   `record_ref` values, and explicit data kinds. Call
   `matrouter_get_thermochemical_entries` for an exact element system. Both create a new
   immutable Bundle without exposing requirements, routes, or assembly steps.
   Read their `summary`, bounded `data`, and `source_issues`; use the returned
   counts and truncation fields to assess coverage.
4. Use `matrouter_read_evidence` for bounded `records`, `items`, `attempts`, or `sources`
   views; `items` contains only structures and scientific artifacts with
   `item_ref`, not inherited source records. For continuation, send the returned
   `next_cursor` as `cursor` without repeating `bundle_ref` or `view`. Use
   `matrouter_export_evidence_bundle` when the complete canonical object is required.
   Prefer its direct HTTP `download_url`; do not read the complete MCP resource
   into model context or reconstruct it from byte chunks.
5. Call `matrouter_retry_sources` only with retryable `attempt_ref` values returned in
   `source_issues` or an attempts view. It preserves record-bound inputs,
   appends occurrences, and returns a derived Bundle; failed is not empty.
6. Pass each short `item_ref` with its owning `bundle_ref` and all explicit
   parameters to scientific methods. Preserve implementation, provenance, coverage, warnings,
   limitations, and separation from Agent interpretation.

## Tool Map

- Optional source readiness: `matrouter_inspect_sources`.
- Source-record discovery: `matrouter_search_materials`.
- Exact record-derived retrieval: `matrouter_get_material_data`.
- Thermochemical entry sets: `matrouter_get_thermochemical_entries`.
- Explicit new attempts: `matrouter_retry_sources`.
- Bounded read and exact export: `matrouter_read_evidence`, `matrouter_export_evidence_bundle`.
- Source-file inventory: `matrouter_list_source_files`. The packaged remote server cannot
  deliver `matrouter_download_source_file` output to the client; prefer typed acquisition
  or an explicit HTTP `download_url` returned by a tool.
- Exact structure comparison: `matrouter_match_structures`.
- Exact frame-bound hull computation/plotting: `matrouter_compute_phase_diagrams`.
- Exact band-structure rendering: `matrouter_render_band_structure`.
- Exact density-of-states rendering: `matrouter_render_density_of_states`.

A downloaded file remains transport state until typed acquisition materializes
its content and provenance in an `EvidenceBundle`.

Scientific data and actual attempts remain in one immutable Bundle. The MCP
facade exposes an explicitly rooted `bundle_ref`; record/item/attempt refs are
Bundle-relative, while bundle/cursor/file refs are short process-global control
identities. The exported canonical Bundle retains stable content IDs and all
exact outcomes and warnings.

## Explicit Scientific Methods

For structure matching, retrieve two exact JSON structures first. Pass their
returned `bundle_ref + item_ref` pairs as the first and second inputs. Supply every
`StructureMatcher` tolerance and comparison option. The current matcher requires
source-declared periodic axes, expressible occupancy, and fully 3D periodic
inputs. Report only the match under those inputs and parameters; do not infer
magnetic, electronic, defect, or topological identity.

For a hull, retrieve an exact `thermochemical_entries` set. Pass its returned
`bundle_ref + item_ref` in each phase-diagram dataset. Retrieval currently requires
`sources=["materials_project"]` and one `source_filters` entry with an explicit
`filter.thermo_types` value. The current seam rejects every mixed source, dataset
snapshot, entry set, or frame and rejects truncated entry sets; keep different sets in separate panels. Supply
`method_parameters.on_hull_tolerance_eV_per_atom`, then report input manifest,
frame, coverage, `on_hull_within_tolerance`, degeneracy, decomposition, plot
artifact, and warnings. Do not translate any hull result into synthesizability.

Keep acquisition of bands, DOS, elastic tensors, and other source artifacts on
the ordinary evidence route. Acquisition does not render. For a band/DOS figure,
pass the spectral artifact's returned `item_ref` to the corresponding render
request together with its owning `bundle_ref`, and explicitly supply all plot parameters;
the renderer preserves the acquired energy reference and creates a derived view,
not new evidence. Do not add imaginary symmetry tools. Preserve energy zero,
units, k-path/projection or tensor context, parser, artifact provenance, and
limitations. MatRouter does not currently expose a general elasticity plot.
Returned plot paths are on the server; the packaged remote MCP does not provide
a tool to download those plot files onto the user's device.

## Agent Discipline

- Preserve exact `source`, `source_id`, units, citations, native semantics,
  context, warnings, lineage declarations, and artifact provenance.
- Keep route readiness separate from execution outcome and record completeness.
- Treat failed as failed, not verified empty; treat unknown/truncated coverage as unresolved.
- Do not merge or select records by formula, space group, source order, lineage,
  or a derived numerical predicate.
- Keep formation energy, energy above hull, source-native stability labels,
  caller-tolerance hull results, and synthesizability distinct.
- Preserve dimensionality, SOC, method, functional, Hubbard U, spin,
  temperature, pressure, correction, energy zero, and reference frame.
- Treat missing fields as missing data, not negative evidence.
- Distinguish experimental crystallography from computed structures.
- Describe source-native topology/classification as “source X reports Y under
  context Z,” not as independent validation.
- Treat OPTIMADE as complementary provider-side interoperability; do not call
  MatRouter its replacement.
