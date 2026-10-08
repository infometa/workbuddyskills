# ae-engage engage-setting channel update-status

> Trigger keywords: push channel · Mapped command: `ae-cli engage-setting channel update-status`

Enable or disable an Engage push channel.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--channel-id` | string | Yes | channel ID |
| `--status` | number | Yes | channel status |

## Enum Notes

### `--status`

- `1`: enabled
- `2`: disabled

## Safety Constraints

This command is a **write operation** and Before executing, confirm that the user explicitly wants to change the channel status.

## Examples

```bash
ae-cli engage-setting channel update-status --project-id 1 --channel-id <channel_id> --status 1
```
