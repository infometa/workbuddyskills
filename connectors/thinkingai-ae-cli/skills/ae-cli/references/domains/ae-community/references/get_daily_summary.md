# ae-community +get_daily_summary


Community daily news for a given day: hot list rankings and selected opinions (positive/negative).

Mapping command: `ae-cli community +get_daily_summary`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--date` | string | Yes | Date, format yyyy-MM-dd |

## Example

```bash
# Get daily report
ae-cli community +get_daily_summary \
  --space-id 1 --game-id 1 --date 2024-01-01
```
