# engage-activity activity-type

> Capability ids: `engage-activity.activity-type.{list,batch-add,update,batch-delete}` · Domain: `engage`.

Campaign activities — activity types (system + custom). Batch add/delete loops single-item backend calls inside the capability service (no dedicated batch backend API).

## Commands

```bash
# List activity types
ae-cli engage-activity activity-type list --project-id <project_id>

# Batch-add custom activity types
ae-cli engage-activity activity-type batch-add --project-id <project_id> --type-names '["t1","t2"]'

# Update a custom activity type name
ae-cli engage-activity activity-type update --project-id <project_id> --id <type_id> --type-name t3

# Batch-delete custom activity types (high-risk)
ae-cli engage-activity activity-type batch-delete --project-id <project_id> --ids '["id1","id2"]' --yes
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| list | `--project-id` | read. |
| batch-add | `--project-id`, `--type-names` | `--type-names` = JSON array of names. |
| update | `--project-id`, `--id`, `--type-name` | write. |
| batch-delete | `--project-id`, `--ids` | high-risk; `--ids` = JSON array; requires `--yes`; no dry-run. |

## Output

- `list`: `data.total`, `data.items`.
- `batch-add`: `data.total`, `data.ids`.
- `update`: `data.success`.
- `batch-delete`: `data.total`, `data.deleted`.

## Decision Rules

- `batch-delete` is `high-risk-write` — requires `--yes`, no dry-run; loops single delete (non-atomic).
- Only custom types are editable; system types are read-only.
