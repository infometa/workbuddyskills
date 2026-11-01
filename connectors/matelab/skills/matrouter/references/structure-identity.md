# MatRouter Structure Comparison

Use MatRouter to retrieve exact structures and provenance, then call
`matrouter_match_structures` only when a crystallographic comparison is useful. Same
formula, display label, prototype, or space group is not automatic phase identity.

## Workflow

1. Discover records first. Retrieve each structure with `matrouter_get_material_data`
   from an exact base Bundle and returned `record_ref`.
2. Keep the structures and all route executions in the returned EvidenceBundle.
3. Pass each returned structure's owning `bundle_ref` with its `item_ref` as the
   first and second inputs. The tool revalidates their source binding,
   item IDs, and original JSON payloads, then computes content digests and
   occupancy from those payloads.
4. Supply every matcher parameter: `ltol`, `stol`, `angle_tol`, primitive cell,
   scale, supercell, subset, comparator, supercell size, ignored species,
   symmetric fit, and structure-reduction choice.
5. Call `matrouter_match_structures` and report its method/version, exact references,
   parameters, boolean result, RMS/maximum distance, and limitations.

Pymatgen and OPTIMADE disordered occupations are preserved. A fallback payload
that cannot represent occupations losslessly fails rather than selecting the
first species. The current matcher also requires source-declared exact periodic
axes and two fully 3D periodic structures; 2D, nonperiodic, unknown-occupancy, or
conflicting-periodicity inputs fail closed.

## Interpretation Levels

- Formula-only: composition metadata, no structure resolution.
- Metadata-aligned: formula plus space group, prototype, or source labels.
- Structure-available: exact structure payloads were retrieved.
- Method-matched: this comparator matched these inputs under these parameters.
- Method-different: this comparator did not match these inputs.
- Unresolved: payload, occupancy, dependency, or context is missing.

Keep experimental crystallography (COD/MPDS), theoretical crystallography
(TCOD), and computed structures distinct. A StructureMatcher result does not
establish magnetic, electronic, defect, or topological phase identity.
