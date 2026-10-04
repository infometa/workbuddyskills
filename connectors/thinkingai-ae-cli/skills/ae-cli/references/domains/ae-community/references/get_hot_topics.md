# ae-community +get_hot_topics


Ranking of hot topics within a time range.

Mapping command: `ae-cli community +get_hot_topics`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--start-time` | string | No | Topic statistics start time, format yyyy-MM-dd |
| `--end-time` | string | No | Topic statistics end time, format yyyy-MM-dd |
| `--order-by` | number | No | Sort: 0 by popularity desc, 1 by start time desc |

## Example

```bash
# Get hot topics
ae-cli community +get_hot_topics \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07
```
