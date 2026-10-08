# ae-community +get_overview_metrics


Overall community metrics within time range: number of posts/replies, sentiment count, channel breakdown.

Mapping command: `ae-cli community +get_overview_metrics`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id-list` | string | No | List of channel IDs, comma separated |
| `--start-time` | string | Yes | Start date for statistics, format yyyy-MM-dd |
| `--end-time` | string | Yes | End date for statistics, format yyyy-MM-dd |

## Example

```bash
# Get overall indicators
ae-cli community +get_overview_metrics \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07
```
