# ae-community +get_livestream_analysis


AI-generated single livestream analysis report: highlight periods (with indicators and AI interpretation) and emotional views.

Mapping command: `ae-cli community +get_livestream_analysis`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--stream-id` | string | Yes | Livestream session ID, streamId from `get_livestream_list` |

## Example

```bash
ae-cli community +get_livestream_analysis \
  --space-id 1 --game-id 1 \
  --stream-id <stream-id>
```
