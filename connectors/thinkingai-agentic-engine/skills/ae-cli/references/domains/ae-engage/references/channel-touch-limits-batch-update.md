# engage-setting channel-touch-limits batch-update

> Capability id: `engage-setting.channel-touch-limits.batch-update` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting channel-touch-limits batch-update \
  --project-id <project_id> \
  --items '[{"rule_id":"r1","enable":true,"rule_def":"[]"},{"rule_id":"r2","enable":false,"rule_def":"[]"}]'
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--items` | Yes | JSON array of rule updates. Each item: `rule_id`, `enable` (boolean), `rule_def` (rule definition JSON string). |

## Output

- `data.success`: whether the batch update succeeded.

## Decision Rules

- Use this command when the user asks to batch edit/update multiple touch-limit (fatigue-control) rules at once.
- Discover existing rule IDs with `ae-cli engage-setting channel-touch-limits list --project-id <project_id>` first; never invent rule IDs.
- Risk is `write`; ordinary update, no confirmation gate.
