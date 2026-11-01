---
name: hsp-symmetry
description: Identify material SG, MSG and SSG from magnetic mPOSCAR/mcif structures through HSP, query catalogue operations, Wyckoff positions and k-vectors, and obtain group representations. Use for HSP symmetry analysis and catalogue queries; material band-character calculations and point-group or subgroup queries are outside this MCP workflow.
display_name: "HSP 怀柔对称性研究平台"
display_name_en: "HSP Huairou Symmetry Platform"
description_zh: "从 mPOSCAR/mcif 磁结构识别空间群、磁空间群与自旋空间群，查询对称操作、Wyckoff 位置、高对称 k 矢量及群表示，并提供分析文件。"
description_en: "Identify space, magnetic and spin space groups from mPOSCAR/mcif structures; query symmetry operations, Wyckoff positions, high-symmetry k-vectors and group representations, and retrieve analysis files."
version: "0.1.2"
author: "Tiannian Zhu"
---

# HSP Symmetry

Use the packaged `hsp` MCP server. Tool names here are raw MCP names;
let the client resolve their namespace. IRSSG identification runs on the
service; no local IRSSG installation or wrapper is needed.

## Choose the workflow

- For an mPOSCAR or magnetic CIF (`mcif`), read
  [material analysis](references/material-analysis.md). Use
  `hsp_prepare_structure_upload`, upload raw bytes, then
  `hsp_identify_structure_symmetry` and `hsp_get_symmetry_analysis`.
- For an already known SG, MSG or SSG, call `hsp_get_symmetry_group` with a
  `group` object as below. Read [catalogue workflows](references/catalogue-workflows.md)
  for parent-group discovery, stored SG/MSG representations, or custom
  SSG k-point calculations.

| Group | `group` example | Identifier contract |
| --- | --- | --- |
| Space group (SG) | `{"kind":"space","number":194}` | Integer 1–230 |
| Magnetic space group (MSG) | `{"kind":"magnetic","number":"63.7.517"}` | OG `a.b.c` or BNS `a.b` string; retain the scheme |
| Spin space group (SSG) | `{"kind":"spin","number":"194.1.6.1.P"}` | Exact catalogue identifier, including `.L`/`.P` when present |

Examples illustrate identifier formats, not guaranteed catalogue coverage.
For material identification, use the returned SG integer, MSG OG/BNS
numbers and SSG identifier to fetch each available group's complete
`record`. Missing MSG/SSG identifiers are unavailable results, not an
invitation to select a group from the catalogue.

## Scientific interpretation

- Identification results describe the input material. Catalogue records
  supply group data, including Wyckoff positions and k-vectors. Keep these
  sources distinct when their operation sets or coordinate conventions differ.
- For material SSG/MSG operations, use `result.spin_operations` and
  `result.magnetic_operations`, preserving the complete `text`, `count`,
  order, printed precision and basis. MSG-to-SSG indices are a cross-reference;
  do not use them to truncate the SSG table.
- IRSSG's `spin_basis` (`D`) defines SSG spin axes. MSG spin matrices use
  Cartesian coordinates. Collinear/coplanar SSG tables contain reduced spin
  blocks; do not expand them into assumed 3-by-3 matrices.
- Preserve complete returned coordinate expressions, operation order,
  primitive/conventional conventions and representation metadata. A
  k-vector's multiplicity need not equal its number of coordinate strings.
- The tools do not run IRSSG `-pw`/`-wann` or determine electronic band
  characters. Stored or custom group representations do not establish a
  material's band assignment.

## Present the requested data

Report identifiers with their schemes, actual analysis parameters,
warnings, and the source of each operation table. For requested complete
tables, include every returned row directly in the answer; artifact links
provide additional provenance. Respect requests for a summary or another format.

- **Wyckoff positions:** include label, multiplicity, site symmetry when
  available, coordinate index and every `coordinates` string. Use one row
  per coordinate.
- **High-symmetry k-vectors:** display `label`, multiplicity, little
  cogroup when available, coordinate convention, coordinate index and all
  `coordinates_primitive` and available `coordinates_conventional` strings.
  Use one row per coordinate. Keep internal `letter` for representation
  lookup rather than showing it by default.
- **Operations and representations:** retain operation indices and the
  matching matrix/character order. Include all operations for a complete
  table request; counts and download links alone do not supply the table.

Keep stored values unchanged. For display, use exact crystallographic
symbols only when their interpretation is supported by the source and
precision: for example, `0.5` as `1/2`, and a confirmed standard
`0.866025…` coefficient as `sqrt(3)/2`, including coefficients attached to
variables or moments. Do not infer exact values from arbitrary decimals
or zero small terms without justification; otherwise show the returned value.

For combined position/spin or k/spin coordinates, show the full parenthesized
expression. In Markdown tables, encode its separator as `&#124;` so the
visible pipe stays inside the cell. Avoid HTML layout tags. Omit columns
that are unavailable throughout; use a dash and explain partial missing
values without printing literal `null`.

Scientific workflow reference:
[upstream HSP symmetry skill](https://github.com/zjwang11/IRSSG/tree/main/skills/hsp-symmetry).
