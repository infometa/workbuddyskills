# MatRouter Phase Diagrams and Thermochemical Data

Use MatRouter to retrieve source-native formation energies/hull fields or exact
thermochemical entries without merging their meanings. Construct a new hull only
with `matrouter_compute_phase_diagrams` and an explicit energy/reference frame.

## Retrieve Inputs

1. Decide whether the task needs source-native scalar fields or a new hull.
2. For a new hull, call `matrouter_get_thermochemical_entries` with one exact chemical
   system and set `sources` to `["materials_project"]`. Set one exact
   `source_filters` entry with `source="materials_project"` and
   `filter={"thermo_types":["GGA_GGA+U_R2SCAN"]}`. Exactly one thermo type is required.
3. Set `limit` high enough for the intended source set.
   A bounded prefix is returned with typed `truncated` completeness and cannot
   be used as a complete hull.
4. Pass the returned thermochemical-entry-set `bundle_ref + item_ref` into the phase-diagram
   dataset; the server resolves the exact item that binds per-entry content and
   stores shared dataset/frame/context only once.

The retrieval route returns compatible calculation inputs. It does not compute
a hull, emit `is_stable`, or choose which entries the Agent should trust.

## Compute Independent Panels

Build one `PhaseDiagramDataset` per compatible origin/frame. Supply:

- a panel `label` and unique sorted 2–4 element `chemical_system`;
- the exact returned `bundle_ref` and `item_ref` for its entry set;
- explicit `method_parameters.on_hull_tolerance_eV_per_atom` and every plot parameter.

The server resolves the entry-set item and validates that it has 2–2000 entries
and `record_completeness.state="complete"`; do not copy the full item or pass
completeness as a dataset argument. It derives energy/model/correction/reference/
condition/frame context from that exact item. The current public seam has no cross-origin
calibration override: mixed source, dataset snapshot, entry set, or frame is
rejected. Separate datasets are independent panels and are not cross-compared.

Set `plot.output_directory` to null when only numerical results are needed.
When plotting, the returned `plot_artifact.path` is server-local; the packaged
remote MCP has no plot-download tool. Report that delivery limitation rather
than treating the server path as a client file.

Report the input manifest, frame, completeness, formation energy, energy above hull,
decomposition, composition fractions, `on_hull_within_tolerance`, on-hull
references, degeneracy groups, plot artifact, and warnings. The plotting library
may display only a representative point; the structured result retains the
tolerance-relative references. Treat the
on-hull field as a result under the caller's explicit tolerance and finite exact
entry set, not a source stability label or synthesizability verdict.
Decomposition `amount` is a pymatgen fractional-composition barycentric
coefficient; it reports one valid decomposition and does not establish uniqueness.

## Guardrails

- Negative formation energy alone is not hull stability.
- Do not mix source-native hull distances as repeated measures.
- Do not use formula-level data to identify a named polymorph.
- Keep source-native `is_stable` scoped to its upstream definition.
- Keep bulk hulls, 2D stability, experimental existence, Pourbaix stability,
  defect energetics, and kinetic accessibility distinct.
- Report truncated entry sets, missing frame
  evidence, and failed retrievals.

Materials Project, OQMD, JARVIS-DFT, Alexandria, and C2DB expose different
source-native energetics. AFLOW formation enthalpy is not a normalized hull
distance. COD, TCOD, and MPDS are not default computed-hull sources.
