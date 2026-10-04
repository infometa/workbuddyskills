# ae-community +get_sentiment_overview


Sentiment distribution and hot word overview: Return keywords and their trends by sentiment type, as well as overall keyword rankings.

Mapping command: `ae-cli community +get_sentiment_overview`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id-list` | string | No | List of channel IDs, comma separated |
| `--start-time` | string | Yes | Start date for statistics, format yyyy-MM-dd |
| `--end-time` | string | Yes | End date for statistics, format yyyy-MM-dd |
| `--is-merged` | boolean | No | Whether to aggregate and merge keywords |
| `--limit` | number | No | Maximum number of returned keywords |

## Example

```bash
#emotionoverview
ae-cli community +get_sentiment_overview \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07

# Limit the number of returns
ae-cli community +get_sentiment_overview \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07 \
  --limit 50
```
