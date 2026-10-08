# analysis project-space delete (L3)

Use when the user wants to delete one or more project spaces.

Do not use for removing dashboard or folder membership. Use the matching capability for that resource.

This capability has no curated `ae-cli analysis` command. Read [`ae-capability`](../../ae-capability/SKILL.md) High-Risk Confirmation Workflow, then:

**Phase 1 — preview:**

```bash
ae-cli capability inspect analysis.project_space.delete
ae-cli capability dry-run analysis.project_space.delete --input '{"project_id":1,"space_ids":[10,11]}'
```

Summarize capability ID, target space IDs, and `risk=high-risk-write` in chat. Ask the user to confirm.

**Phase 2 — execute (only after explicit user confirmation):**

```bash
ae-cli capability run analysis.project_space.delete --input '{"project_id":1,"space_ids":[10,11]}' --yes
```

Input uses snake_case JSON. Common fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `project_id` | integer | yes | Project ID. |
| `space_id` | integer | no | Single project space ID. |
| `space_ids` | integer[] | no | Batch project space IDs. |

Output is the gateway envelope. `data` contains the delete result.
