# engage-scene config-group

> Trigger keywords: config center, scene config · Capability ids: `engage-scene.config-group.{list,batch-add,update,batch-delete}` · Domain: `engage`.

Scene management / config center — config item group management.

## Commands

```bash
# List config groups of a project
ae-cli engage-scene config-group list --project-id <project_id>

# Batch-create config groups
ae-cli engage-scene config-group batch-add --project-id <project_id> --group-names '["g1","g2"]'

# Rename a config group
ae-cli engage-scene config-group update --project-id <project_id> --group-id <group_id> --group-name <name>

# Batch-delete config groups (high-risk)
ae-cli engage-scene config-group batch-delete --project-id <project_id> --group-ids '[1,2]' --yes
```

## Parameters

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

### batch-add

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--group-names` | Yes | JSON array of group names (<=80 chars each). |

### update

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--group-id` | Yes | Group ID to update. |
| `--group-name` | Yes | New group name (<=80 chars). |

### batch-delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--group-ids` | Yes | JSON array of group IDs. |

## Output

- `list`: `data.items` + `data.total`.
- `batch-add` / `batch-delete`: `data.success_num` + `data.fail_list` (looped single calls; non-atomic).
- `update`: `data.success`.

## Decision Rules

- Discover real `group_id`s with `list` before update/delete; never invent IDs.
- `batch-delete` is `high-risk-write` and requires `--yes`.
