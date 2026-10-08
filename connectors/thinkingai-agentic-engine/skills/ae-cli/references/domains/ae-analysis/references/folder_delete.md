# analysis folder delete (L3)

Use when the user wants to delete one or more folders.

This capability has no curated `ae-cli analysis` command. Read [`ae-capability`](../../ae-capability/SKILL.md) High-Risk Confirmation Workflow, then:

**Phase 1 — preview:**

```bash
ae-cli capability inspect analysis.folder.delete
ae-cli capability dry-run analysis.folder.delete --input '{"project_id":1,"folder_ids":[1001,1002]}'
```

Summarize capability ID, target folder IDs, and `risk=high-risk-write` in chat. Ask the user to confirm.

**Phase 2 — execute (only after explicit user confirmation):**

```bash
ae-cli capability run analysis.folder.delete --input '{"project_id":1,"folder_ids":[1001,1002]}' --yes
```

Input uses snake_case JSON. Common fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `project_id` | integer | yes | Project ID. |
| `folder_id` | integer | no | Single folder ID. |
| `folder_ids` | integer[] | no | Batch folder IDs. |

Output is the gateway envelope. `data` contains the delete result.
