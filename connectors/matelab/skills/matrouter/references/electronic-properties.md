# MatRouter Electronic Properties

Gather electronic and spectral data without conflating scalar metadata, parsed
curves, rendered plots, raw files and source-specific documents.

## Workflow

1. Search records, then call `matrouter_get_material_data` with `base_bundle_ref`, exact
   returned `record_ref` values, and the requested `data_kinds`.
2. Preserve every exact source-qualified outcome in the returned Bundle.
3. If a figure is needed, call `matrouter_render_band_structure` or
   `matrouter_render_density_of_states` only after acquisition, using its returned
   `bundle_ref + item_ref` and explicit plot parameters.
4. Let the Agent select an explicit comparison method when needed; state its
   exact inputs, parameters, assumptions, and limitations.

## Guardrails

- `band_gap_eV` is not a band structure.
- A file manifest is not parsed electronic evidence, and a rendered figure is
  not an independent source observation.
- Preserve method, functional, SOC, Hubbard U, spin, dimensionality, geometry,
  temperature, pressure, correction and observable type when reported.
- Do not average cross-source band gaps or spectra without a declared method.
- Keep source-native labels separate from independent validation.
- Report parser, dependency, credential and raw-data limitations.

## Topology

Use `topology_no_soc` or `topology_soc` in `data_kinds`; request both explicitly
when comparing SOC conditions. `electronic_structure_no_soc` and
`electronic_structure_soc` are not current data kinds. Topology detail routing
is qualified to `materialsgalaxy:topo_crystals`.

Report the exact `mg_id`, qualified source, SOC setting, source-native class,
available indicators and limitations. Prefer wording such as “source X reports
class Y under SOC setting Z.” Do not say MatRouter independently validated an
invariant, surface state or every polymorph sharing the formula.

## Independent Data Kinds

Use `band_structure` or `density_of_states` for parsed electronic spectra.
`phonon_dispersion` and `phonon_dos` are separate products; request either or both
as needed. `optical_spectrum`, static `dielectric`, and `xas` are also independent;
one does not implicitly retrieve another. XAS may return multiple spectrum items;
preserve their element, edge, and type rather than selecting or merging silently.
Likewise, keep source-native `ferroelectric`, `piezoelectric`, and `magnetism`
reports separate and preserve their conditions. Use the current tool schema and
`matrouter_inspect_sources` for available kinds and source coverage.

## Raw Files

Always list before downloading. AFLOW and JARVIS file guidance helps select an
artifact but does not prove that it was parsed. Unknown file size remains
unknown. A downloaded archive becomes usable bundle data only through a typed
artifact acquisition.

Acquisition must not create a plot. Rendering consumes the exact acquired
artifact, preserves its energy reference, and records caller-selected format,
limits, title, and DOS projection keys. For every result report source, source
ID, property/artifact type, units, energy zero, k-path or projection context,
parser, method context, generated files, warnings and unresolved data needs.
Rendering returns a server-local `plot_artifact.path`; the packaged remote MCP
has no plot-download tool. Report the artifact metadata and delivery limitation
instead of presenting that path as a file available on the user's device.

## Elasticity

Use the ordinary `elasticity` evidence route for source-native tensors and
metadata. Preserve tensor convention, units, method/workflow context, source
record, parser status, and missing fields. MatRouter currently has no general
elasticity plotting contract; do not claim one or infer cross-source agreement.
