# ae-community +get_livestream_overview


Livestream overview trends: number of active rooms, number of sessions, number of interactions and livestream duration.

Mapping command: `ae-cli community +get_livestream_overview`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--start-time` | string | No | Start date for statistics, format yyyy-MM-dd |
| `--end-time` | string | No | End date for statistics, format yyyy-MM-dd |

## Example

```bash
# Get livestream overview
ae-cli community +get_livestream_overview \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07
```
