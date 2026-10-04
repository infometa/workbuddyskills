# ae-community +get_livestream_room_metrics


Core metrics and annual calendar for a single livestream room: Overview KPIs plus daily livestream duration calendar.

Mapping command: `ae-cli community +get_livestream_room_metrics`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--channel-id` | number | Yes | Channel ID (obtain via `get_livestream_rooms`) |
| `--room-id` | string | yes | Room ID (obtain via `get_livestream_rooms`) |
| `--year` | string | No | Year, format yyyy, default is the current year |

## Example

```bash
# Get the annual indicators of the livestream room
ae-cli community +get_livestream_room_metrics \
  --space-id 1 --game-id 1 \
  --channel-id 1 --room-id <room-id> --year 2024
```
