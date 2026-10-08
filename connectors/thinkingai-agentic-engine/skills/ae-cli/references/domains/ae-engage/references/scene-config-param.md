# engage-scene config-param

> Trigger keywords: config center, scene config, config item · Capability ids: `engage-scene.config-param.{list,batch-add,update,batch-delete}` · Domain: `engage`.

Scene management / config center — config item parameter management.

## Commands

```bash
# List params of a config item
ae-cli engage-scene config-param list --project-id <project_id> --config-id <config_id>

# Batch-add params to a config item
ae-cli engage-scene config-param batch-add \
  --project-id <project_id> --config-id <config_id> \
  --params '[{"param_name":"title","param_display_name":"Title","param_type":"STRING","param_sub_type":"SHORT_TEXT","is_required":1}]'

# Update a param
ae-cli engage-scene config-param update \
  --project-id <project_id> --config-id <config_id> --param-id <param_id> \
  [--param-name <name>] [--param-display-name <name>] [--param-type <type>] \
  [--param-sub-type <sub>] [--table-id <table_id>] [--param-placeholder <ph>] \
  [--is-required 1] [--default-value <value>]

# Batch-delete params (high-risk)
ae-cli engage-scene config-param batch-delete --project-id <project_id> --param-ids '[1,2]' --yes
```

## Parameters

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |

### batch-add

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |
| `--params` | Yes | JSON array of params (`param_name`, `param_display_name`, `param_type`, `param_sub_type`, `table_id`, `param_placeholder`, `is_required`, `default_value`). `param_type` must be uppercase enum: `STRING`, `NUM`, `DATE`, `DATE_TIME`, `BOOLEAN`, `OBJ`, `SINGLE_SELECT`, `ARRAY`, `JSON`. For `STRING`/`ARRAY`, `param_sub_type` is required (e.g. `SHORT_TEXT`, `LONG_TEXT`, `NUM`). For `SINGLE_SELECT`, `table_id` is required. **`param_display_name` must be unique within the config item** — duplicate display names return `INVALID_CAPABILITY_REQUEST`. |

### update

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |
| `--param-id` | Yes | Param ID to update. |
| others | No | See flag descriptions above. |

### batch-delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--param-ids` | Yes | JSON array of param IDs. |

## Output

- `list`: `data.items` + `data.total`.
- `batch-add` / `update`: `data.success`.
- `batch-delete`: `data.success_num` + `data.fail_list` (looped single deletes; non-atomic).

## Decision Rules

- Use `list` to discover real `param_id`s before update/delete; never invent IDs.
- `param_type` is case-sensitive; lowercase values like `"string"` are rejected with `PARAM_TYPE_INVALID`.
- `batch-delete` is `high-risk-write` and requires `--yes`.
