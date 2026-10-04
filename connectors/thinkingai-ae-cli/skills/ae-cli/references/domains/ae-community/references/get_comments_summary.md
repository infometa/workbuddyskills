# ae-community +get_comments_summary


Get a summary of comment analysis for a post, including sentiment distribution and time trends. Only aggregate statistics are returned, no raw review list.

Mapping command: `ae-cli community +get_comments_summary`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id` | number | yes | channel ID |
| `--uuid` | string | yes | content UUID |
| `--start-time` | string | No | Earliest comment publish date, format yyyy-MM-dd, default is the publishing time of the post |
| `--end-time` | string | No | Latest comment publish date, format yyyy-MM-dd |

## Example

```bash
# Get comment summary
ae-cli community +get_comments_summary \
  --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid>

#Specify time range
ae-cli community +get_comments_summary \
  --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid> \
  --start-time 2024-01-01 --end-time 2024-01-07
```
