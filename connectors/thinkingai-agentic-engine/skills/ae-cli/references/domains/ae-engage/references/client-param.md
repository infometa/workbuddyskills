# engage-setting client-param

> Capability ids: `engage-setting.client-param.{create,update,delete,list}` · Domain: `engage`.

Manage custom client params. `select_type` is derived server-side from `column_type`. `column_type` / `select_type` are immutable after create.

## Commands

```bash
# Create a custom client param
ae-cli engage-setting client-param create \
  --project-id <project_id> --column-name <name> --column-type varchar \
  [--column-desc <desc>] [--column-remark <remark>] [--alternative-val '["a","b"]']

# Update display metadata (type is immutable)
ae-cli engage-setting client-param update \
  --project-id <project_id> --column-name <name> \
  [--column-desc <desc>] [--column-remark <remark>] [--alternative-val '["a","b"]']

# Delete a custom client param (high-risk)
ae-cli engage-setting client-param delete --project-id <project_id> --column-name <name> --yes

# List client params (custom + preset)
ae-cli engage-setting client-param list --project-id <project_id>
```

## Parameters

### create

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--column-name` | Yes | Must match `^[A-Za-z][A-Za-z0-9_]*$`, max 80. |
| `--column-type` | Yes | `varchar` \| `bigint` \| `double` \| `boolean`. `timestamp` is not supported. `select_type` is derived server-side (`varchar→string`, `bigint/double→number`, `boolean→bool`). |
| `--column-desc` | No | Display name. Defaults to an empty string. |
| `--column-remark` | No | Description/remark. |
| `--alternative-val` | No | JSON array of alternative values. Only allowed when `--column-type` is `varchar`. |

### update

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--column-name` | Yes | Existing custom client param name. |
| `--column-desc` | No | Display name. Omit to keep existing. |
| `--column-remark` | No | Description/remark. Omit to keep existing. |
| `--alternative-val` | No | JSON array of alternative values. Only allowed when existing `column_type` is `varchar`. Omit to keep existing. |

Do **not** pass `--column-type` / `--select-type` on update — they are rejected and cannot be changed.

### delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--column-name` | Yes | Client param column name to delete. |

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

## Output

- `create` / `update`: `data.success`.
- `delete`: `data.success` and `data.task_list` (tasks still referencing the param, which block deletion; each item has `task_id`, `task_name`).
- `list`: `data.items` (each with `column_name`, `column_type`, `select_type`, `column_source`, `column_desc`, `column_remark`, `alternative_val`, `system_id_param`) and `data.total`.

## Decision Rules

- Prefer `list` first to avoid duplicate `column_name` and to confirm existing type before update.
- Use only the four allowed `column_type` values; never invent types like `string` / `single`.
- After create, re-`list` to verify the stored row.
- `delete` is `high-risk-write` and requires `--yes`. When `data.success` is false, report `data.task_list` instead of forcing deletion.
