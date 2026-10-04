# engage-scene config-item

> Trigger keywords: config center, scene config, config item · Capability ids: `engage-scene.config-item.{list,get,create,update,delete}` · Domain: `engage`.

Scene management / config center — config item management.

## Commands

```bash
# List config items of a project
ae-cli engage-scene config-item list --project-id <project_id>

# Get config item detail
ae-cli engage-scene config-item get --project-id <project_id> --config-id <config_id>

# Create a config item (business type, group, optional avatar)
ae-cli engage-scene config-item create \
  --project-id <project_id> --config-id <config_id> --config-name <name> \
  --business-type <config_file|params> \
  [--config-remark <remark>] [--group-id <group_id>] \
  [--avatar-word '["A"]'] [--file-name icon.png] [--file-content "$(base64 -i icon.png)"]

# Update a config item's basic info and bound channel
ae-cli engage-scene config-item update \
  --project-id <project_id> --config-id <config_id> \
  [--config-name <name>] [--config-remark <remark>] [--business-type <type>] \
  [--group-id <group_id>] [--channel-id <channel_id>]

# Delete a config item (high-risk)
ae-cli engage-scene config-item delete \
  --project-id <project_id> --config-id <config_id> --open-id <operator_open_id> --yes
```

## Parameters

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

### create

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID (unique within the project). |
| `--config-name` | Yes | Config item display name (<=80 chars). |
| `--business-type` | Yes | Business type: `config_file` or `params`. |
| `--config-remark` | No | Remark (<=200 chars). |
| `--group-id` | No | Group ID (0 = default group). |
| `--avatar-word` | No | JSON array of avatar words for the icon. |
| `--file-name` | No | Avatar file name including extension. |
| `--file-content` | No | Base64-encoded avatar file content. |

### get

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |

### update

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID to update. |
| `--config-name` | No | New display name. |
| `--config-remark` | No | New remark. |
| `--business-type` | No | New business type. |
| `--group-id` | No | New group ID. |
| `--channel-id` | No | Config channel ID to bind. |

### delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID to delete. |
| `--open-id` | Yes | Operator open ID retained by the original deletion workflow. |

## Output

- `list`: `data.items` + `data.total`.
- `get`: `data.item`.
- `create` / `update` / `delete`: `data.success` — whether the operation succeeded.

## Decision Rules

- `create` / `update` are `write`; `delete` is `high-risk-write` and requires `--yes`; `list` / `get` are read. Use `config-item list` to discover real `config_id`s and group IDs; never invent IDs.
