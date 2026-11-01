# Material symmetry identification

## Input and upload

Accept magnetic mPOSCAR/POSCAR-like structures or magnetic CIF (`mcif`).
Magnetic mPOSCAR atom rows carry moments after positions, typically
`x y z mx my mz`; zero-moment sites may have only positions. Do not invent
missing moments. A nonmagnetic result at the selected tolerance does not
identify a magnetic or spin space group.

1. Call `hsp_prepare_structure_upload(filename, format)` with the plain
   filename and `format="mposcar"` or `"mcif"`. A local path is not a
   filename argument. The response supplies `structure_ref`, `upload_url`,
   `upload_headers`, `expires_at` and `max_bytes`.
2. Before expiry and within `max_bytes`, PUT the original raw UTF-8 file
   bytes to the exact `upload_url` using all returned headers. Upload
   capabilities last 15 minutes. Do not send JSON, multipart, Base64, a
   path or the file contents in MCP arguments. Use a host that can access
   the local file and make the HTTP PUT. If transfer is unavailable,
   report that limitation without claiming an upload or analysis occurred.
3. Use `structure_ref` only after a successful PUT. Uploaded structures
   are immutable and reusable. An expired or missing reservation needs a
   fresh upload; changing the input file also needs a fresh upload.

## Identification and polling

Call `hsp_identify_structure_symmetry` with:

| Field | Default | Contract |
| --- | --- | --- |
| `structure_ref` | Required | Copy the completed upload's opaque reference |
| `tolerance` | `1e-3` | IRSSG spatial tolerance (`--tolerance`); finite number, greater than 0 and at most 1 |
| `magnetic_tolerance` | `1e-4` | IRSSG spin tolerance (`--magtolerance`); same numeric bounds |

Apply the user's tolerances and report actual returned `parameters`.
Defaults are a starting point, not evidence that a structure is numerically
stable. Do not silently change tolerances to obtain a preferred group.

Retain `analysis_id` and poll `hsp_get_symmetry_analysis(analysis_id)` only
while status is `queued` or `running`, allowing time between requests.
Stop on `completed` or `failed`.

- On completion, `result.identifiers` supplies SG number/symbol, MSG OG
  number, BNS number and symbol, and SSG number/symbol where identified.
  Report `result.engine_version`, `warnings`, `spin_basis` and the requested
  complete material operation tables. Use each table's own `count` and
  `text`; the MSG subset does not define the full SSG table.
- Fetch catalogue records with the returned identifiers for Wyckoff
  positions, k-vectors and group representations. Those records do not
  replace this material's operation tables.
- On failure, report `error` and inspect available diagnostic artifacts.
  Repeating the same `structure_ref` and tolerances reuses the persisted
  analysis, including failure. A fresh upload enables a deliberate retry
  when the cause has been addressed.

Use returned `artifacts[].download_url` links directly, retaining their
paths and query strings. Offer only artifacts actually listed, such as
stdout/stderr logs, `ssg.data`, `msg.data` or generated structures. These
files are provenance or downstream inputs; their presence does not mean
that electronic-structure band calculations ran.

## Error recovery

Tool errors contain `code`, `message`, `retryable` and sometimes `recovery`.
Follow the reported recovery rather than repeating invalid input.

- `input_not_uploaded`: complete the prepared raw PUT before identification.
- `input_expired` or `input_not_found`: reserve and upload again.
- `analysis_not_found`: check the returned analysis ID.
- `indeterminate_write`: the response may have been lost after submission.
  For identification, retry with exactly the same reference and tolerances
  to recover its persisted analysis. For uncertain upload preparation,
  create a fresh reservation; do not guess a capability URL.
- `upstream_unauthorized`: use the deployment's existing gateway access
  configuration. The MCP adapter does not accept the upstream wrapper's
  `HSP_API_KEY` flags or require a bundled API key.
