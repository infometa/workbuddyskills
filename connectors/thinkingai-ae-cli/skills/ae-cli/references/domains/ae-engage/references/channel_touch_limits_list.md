# engage-setting channel-touch-limits list

> Capability id: `engage-setting.channel-touch-limits.list` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting channel-touch-limits list --project-id <project_id>
ae-cli engage-setting channel-touch-limits list --project-id <project_id> --dry-run
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

## Output

- `data.items`: complete touch-limit rule list for the project.
- `data.total`: number of returned rules.
- Each item can contain `project_id`, `rule_id`, `channel_biz_type`, `enable`, `rule_def`, `channel_name`, `channel_type`, and `channel_list`.
- Each `channel_list` item contains `channel_id` and `channel_name`.

## Decision Rules

- Use this command when the user asks for project channel touch-limit, delivery-cap, or fatigue-control rules.
- Use `engage-setting channel list` to list channels and `engage-setting channel get` to inspect one channel; neither returns the project touch-limit rule list.
- If `items` is empty, do not invent rule IDs or channel IDs; report that no touch-limit rules were returned for the project.
