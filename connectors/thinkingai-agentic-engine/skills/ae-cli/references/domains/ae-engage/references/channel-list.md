# ae-engage engage-setting channel list

> Trigger keywords: push channel · Mapped command: `ae-cli engage-setting channel list`

Query the list of Engage push channels in a project.

The result is `{ data: { items, total } }`. Channel fields recursively use snake_case, for
example `data.items[].channel_id`, `data.items[].channel_status`, and `data.items[].channel_type`.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--provider-list` | json | No | Provider list JSON array |
| `--channel-status` | number | No | Channel status filter |

## Enum Notes

### `--channel-status`

- `1`: enabled
- `2`: disabled

### `--provider-list`

Common provider / channelSubBizType values:

- `webhook`
- `fcm`
- `aurora`
- `apns`
- `client`
- `wechat_mini_game`
- `dou_yin_recommended_game_card`

## Examples

```bash
ae-cli engage-setting channel list --project-id 1
ae-cli engage-setting channel list --project-id 1 --provider-list '["webhook","fcm"]'
```
