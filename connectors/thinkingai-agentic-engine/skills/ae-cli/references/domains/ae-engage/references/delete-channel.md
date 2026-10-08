# ae-engage engage-setting channel delete

> Trigger keywords: push channel · Mapped command: `ae-cli engage-setting channel delete`

Delete an Engage push channel.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--channel-id` | string | Yes | channel ID |

## Safety Constraints

This command is a **write operation** and Before executing, confirm that this channel is allowed to be deleted.

## Examples

```bash
ae-cli engage-setting channel delete --project-id 1 --channel-id <channel_id>
```
