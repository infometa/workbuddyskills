# ae-community +get_channel_info


Get the list of valid channels for the community space, including channel IDs and names. **This is the prerequisite step for most commands that require `--channel-id` / `--channel-id-list`: First get the real channel ID here, and then call `+search_posts`, `+get_post_detail`, `+get_comments_summary`, `+get_livestream_list`, etc. with parameters (subject to the reference of each command).

Mapping command: `ae-cli community +get_channel_info`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |

## Example

```bash
# Get channel list
ae-cli community +get_channel_info --space-id 1 --game-id 1
```
