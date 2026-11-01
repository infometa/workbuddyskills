# Catalogue and representation workflows

## Group records and parent discovery

`hsp_get_symmetry_group(group)` returns `kind` and a complete `record`, including
`operations`, `wyckoff_positions` and `k_points`. Use the matching `kind`
and identifier type from the skill's identifier table.

To discover groups associated with a parent SG:

| Tool | Inputs |
| --- | --- |
| `hsp_list_magnetic_groups` | `parent_number` (integer 1–230), `scheme` (`"og"` default or `"bns"`), `offset=0`, `limit=50` |
| `hsp_list_spin_groups` | `parent_number` (integer 1–230), `offset=0`, `limit=50` |

Limits are 1–100. Each page has `total`, `offset`, `next_offset` and `data`.
For a complete list, continue with the returned `next_offset` until it is
null, keeping the same parent and numbering scheme. A page size or list
of candidates is not the total catalogue or a material identification.

MSG OG and BNS schemes can have different parent groups. Preserve both
returned numbers and specify the scheme used for filtering. For SSG,
copy the exact returned `group_id`, retaining any `.L`/`.P` suffix.

Keep complete coordinate lists. For k-vectors, `coordinates_primitive`
and `coordinates_conventional` describe different bases. A displayed
`label` is not the internal `letter` used to select a representation branch.

## Stored SG/MSG representations

1. Fetch the SG or MSG record.
2. Copy the desired `record.k_points[].letter` unchanged into `variant`.
   Show its `label` to the user; do not derive the branch from that label
   or from coordinates.
3. Call `hsp_get_group_representations(group, variant)` with the same SG/MSG
   `group` object. SSG is not accepted by this tool.
4. Preserve `single_data`, `double_data`, available local/source metadata
   and matching `operations` order when reporting characters or matrices.

A valid catalogue branch may have no stored representation. On
`representation_not_found`, verify the copied letter and report missing
data rather than inventing a table or silently using another branch.

## Custom SSG k-point representations

Call `hsp_calculate_spin_group_representations(group_id, k_point)` only when
the requested task needs a calculation. It can create a backend job and
write a result cache. Use the exact SSG identifier and fractional components
in that group's primitive k-coordinate convention:

```json
{"ka":"1/3","kb":"0","kc":"0"}
```

Components must be finite fraction or decimal strings; preserve them
without rounding. Optional `selected_letter` prefers a branch copied
from that SSG's `k_points[].letter`. Resolve an ambiguous coordinate
convention before calculating rather than assuming a basis conversion.

The response contains `group_id` and `job`:

- `job.status="completed"`: use `job.result`; cache hits may have no job ID.
- `job.status="pending"`: retain `job.job_id`, then poll
  `hsp_get_spin_group_representation_job(group_id, job_id)` with the returned
  group ID. Allow time between requests and poll only while pending.
- `job.status="failed"`: report `job.error` and stop polling.

Jobs are process-local, disappear on restart and expire six hours after
completion. On `representation_job_not_found`, check both IDs; resubmit
the original calculation if it is gone and the calculation is still needed.
For `indeterminate_write`, retry only the same group, exact k-point strings
and branch. Matching pending requests share a job, but this workflow has
no durable idempotency guarantee for completed/failed jobs.

For other tool failures, report `code`, `message` and relevant `recovery`.
Check SG versus OG/BNS MSG versus exact SSG identifiers on
`record_not_found`; a group missing from the deployed snapshot is not
proof that the input material has another symmetry.
