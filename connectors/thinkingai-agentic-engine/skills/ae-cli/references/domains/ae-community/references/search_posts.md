# ae-community +search_posts


Search community posts/videos for multi-criteria filtering.

Mapping command: `ae-cli community +search_posts`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | Yes | Community Space ID |
| `--game-id` | number | Yes | Game/Space Logo |
| `--channel-id-list` | string | No | List of channel IDs, comma separated |
| `--keywords` | string | No | List of keywords, comma separated |
| `--start-time` | string | Yes | Minimum content post time, format yyyy-MM-dd |
| `--end-time` | string | Yes | Maximum content post time, format yyyy-MM-dd |
| `--official` | boolean | No | Official account only |
| `--resource-type` | string | No | Resource type: 0 posts, 1 video, comma separated |
| `--search-mode` | number | No | Search mode: 0 word (default), 1 exact match, 2 author names |
| `--search-word` | string | No | Full-text search term, in conjunction with searchMode |
| `--sentiment-types` | string | No | Emotion type: 0 negative, 1 positive, 2 neutral, comma separated |
| `--order-by` | number | No | Sort: 0 time desc, 1 weight desc, 2 time asc, 3 replies desc, 4 heat desc |
| `--page-num` | number | No | Page from 1 |
| `--page-size` | number | No | Number of bars per page |

Examples

```bash
Basic search
ae-cli community +search_posts \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07

# Filter by channel and sentiment
ae-cli community +search_posts \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07 \
  --channel-id-list 1,2 \
  --sentiment-types 0,1

Pagination Query
ae-cli community +search_posts \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07 \
  --page-num 1 --page-size 20
```
