# ae-community +get_topic_detail


In-depth statistics on specified topics: content/total number of replies, sentiment distribution, daily trends by channel, and hot keywords.

Mapping command: `ae-cli community +get_topic_detail`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--topic-id` | string | yes | Topic ID, obtained from get_hot_topics |
| `--start-time` | string | Yes | Statistics start date, format yyyy-MM-dd, priority is given to the start time of the topic |
| `--end-time` | string | Yes | Statistics end date, format yyyy-MM-dd, priority is given to the end time of the topic |

## Example

```bash
# Get topic details
ae-cli community +get_topic_detail \
  --space-id 1 --game-id 1 \
  --topic-id <topic-id> \
  --start-time 2024-01-01 --end-time 2024-01-07
```
