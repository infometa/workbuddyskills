# ae-engage engage-setting channel get

> Trigger keywords: push channel · Mapped command: `ae-cli engage-setting channel get`

Query the details of a single Engage push channel.

## Response shape

The channel detail is under `data.item`. Every response key is snake_case, for example
`data.item.channel_status`, `data.item.channel_type`, and `data.item.config.params_list`.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--channel-id` | string | Yes | channel ID |

## Common enums in the response

### `data.item.channel_status`

- `0`: disabled
- `1`: enabled

### `data.item.channel_type`

- `1`: `WEBHOOK`
- `2`: `APP_PUSH`
- `3`: `CLIENT_PUSH`
- `4`: `WECHAT`
- `5`: `DOU_YIN`

### `data.item.channel_sub_biz_type`

Common values include:

- `webhook`
- `fcm`
- `aurora`
- `apns`
- `client`
- `wechat_mini_game`
- `dou_yin_recommended_game_card`

### `data.item.enable_touch_event`

- `0`: disable the touch funnel
- `1`: enable the touch funnel

## Examples

```bash
ae-cli engage-setting channel get --project-id 1 --channel-id <channel_id>
```
