# engage-setting channel update-config

> Trigger keywords: push channel · Capability id: `engage-setting.channel.update-config` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting channel update-config \
  --project-id <project_id> --channel-id <channel_id> --enable-touch-event <0|1> \
  [--channel-name <name>] [--push-id-type <prop>] [--config '<json_string>'] \
  [--touch-event-source <src>] [--event-delivery-name <name>] [--event-click-name <name>]
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--channel-id` | Yes | Channel ID to update. |
| `--enable-touch-event` | Yes | Reach funnel toggle: `1` enabled, `0` disabled. |
| `--channel-name` | No | New channel name. |
| `--push-id-type` | No | Prefixed push ID: webhook prefers `user:…`; client allows `user:…` or `client:…` (see `add-channel.md`). |
| `--config` | No | Channel JSON string. Webhook `url` = HTTP(S); client `url` = scene key. Custom `columnName` prefixes differ — see `add-channel.md`. |
| `--touch-event-source` | No | Reach event source. |
| `--event-delivery-name` | No | Actual delivery event name. |
| `--event-click-name` | No | Click event name. |

## Output

- `data.success`: whether the channel config was updated.

## Decision Rules

- Use this command when the user asks to edit/update an existing channel's name, config, push-id type, or reach-funnel settings.
- `--config` is the channel-specific JSON config; discover the existing config with `ae-cli engage-setting channel get` first rather than inventing it.
- Keep webhook vs client rules from `add-channel.md` when editing `url` / `pushIdType` / `userParamsList`.
- Risk is `write`; ordinary update, no confirmation gate.
