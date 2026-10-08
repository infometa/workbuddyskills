# ae-community +get_livestream_list


Get the list of livestream sessions for a room (stream history).

Mapping command: `ae-cli community +get_livestream_list`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id` | number | no | Channel ID (obtain via `get_livestream_rooms`) |
| `--room-id` | string | No | Room ID (obtain via `get_livestream_rooms`) |
| `--start-time` | string | No | Start date for statistics, format yyyy-MM-dd |
| `--end-time` | string | No | End date for statistics, format yyyy-MM-dd |

## Example

```bash
# Get the livestream session list
ae-cli community +get_livestream_list \
  --space-id 1 --game-id 1 --channel-id 1
```
