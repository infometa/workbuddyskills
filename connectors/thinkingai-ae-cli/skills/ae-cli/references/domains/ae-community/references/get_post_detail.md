# ae-community +get_post_detail


Get complete details of the post/video, including text, media, comments, emotions, keywords, topics, tag values ​​and comment pagination.

Mapping command: `ae-cli community +get_post_detail`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id` | number | yes | channel ID |
| `--uuid` | string | yes | content UUID |
| `--resource-type` | number | Yes | Resource type: `0` for posts, `1` for videos |
| `--danmu-order-by` | number | No | Danmu sorting: 0 timestamp desc, 1 release time desc |
| `--danmu-page-num` | number | No | Danmu page number, starting from 1 |
| `--danmu-page-size` | number | No | Number of danmaku messages per page |
| `--reply-order-by` | number | No | Comment sorting: 0 release time desc, 1 release time asc |
| `--reply-page-num` | number | no | Comment page number, starting from 1 |
| `--reply-page-size` | number | No | Number of comments per page |

## Example

```bash
# Get post details
ae-cli community +get_post_detail \
  --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid> --resource-type 0

# Get video details and page comments
ae-cli community +get_post_detail \
  --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid> --resource-type 1 \
  --reply-page-num 1 --reply-page-size 20
```
