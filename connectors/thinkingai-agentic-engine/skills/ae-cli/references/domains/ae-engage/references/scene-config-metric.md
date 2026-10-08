# engage-scene config-metric

> Trigger keywords: config center, config item · Capability ids: `engage-scene.config-metric.{list,get,batch-add,update-rule,batch-delete}` · Domain: `engage`.

Scene management / config center — config item related-metric management.

## Commands

```bash
# List related metrics of a config item (optionally include preset metrics)
ae-cli engage-scene config-metric list --project-id <project_id> --config-id <config_id> [--all-metric]

# Get a related metric's detail
ae-cli engage-scene config-metric get --project-id <project_id> --metric-id <metric_id>

# Batch-relate TA (event-analysis) metrics to a config item
ae-cli engage-scene config-metric batch-add --project-id <project_id> --config-id <config_id> --ta-metric-ids '[1,2]'

# Update a config metric's event relation rule
ae-cli engage-scene config-metric update-rule \
  --project-id <project_id> --metric-id <metric_id> \
  --event-list '[{"event_name":"e1","filter":"true"}]'

# Batch-remove related metrics (high-risk)
ae-cli engage-scene config-metric batch-delete --project-id <project_id> --config-id <config_id> --metric-ids '[1,2]' --yes
```

## Parameters

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |
| `--all-metric` | No | Include preset metrics as well. |

### get

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--metric-id` | Yes | Config metric primary ID. |

### batch-add

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |
| `--ta-metric-ids` | Yes | JSON array of TA metric IDs. |

### update-rule

`event_list` is a scene metric attribution-rule list, not a complete analysis QP. It intentionally
keeps its existing `event_name`/`filter` contract and does not use TriggerEvent conversion.

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--metric-id` | Yes | Config metric primary ID. |
| `--event-list` | Yes | JSON array of event rules (`event_name` or `eventName`, plus `filter`). |

### batch-delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--config-id` | Yes | Config item ID. |
| `--metric-ids` | Yes | JSON array of config metric primary IDs. |

## Output

- `list`: `data.items` + `data.total`.
- `get`: `data` — metric detail.
- `batch-add` / `update-rule`: `data.success`.
- `batch-delete`: `data.success`.

## Decision Rules

- Discover real metric IDs via `list`/`get`; never invent IDs.
- `batch-delete` is `high-risk-write` and requires `--yes`.
