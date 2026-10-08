# ae-community +get_livestream_rooms


Search livestream rooms by time range and channel, and return room lists and statistics.

Mapping command: `ae-cli community +get_livestream_rooms`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id-list` | string | No | List of channel IDs, comma separated |
| `--start-time` | string | No | Start date for statistics, format yyyy-MM-dd |
| `--end-time` | string | No | End date for statistics, format yyyy-MM-dd |

## Example

```bash
# Search livestream room
ae-cli community +get_livestream_rooms \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07
```
