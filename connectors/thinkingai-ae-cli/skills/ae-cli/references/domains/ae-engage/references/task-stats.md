# ae-cli engage-task task stats


Query task status statistics.

Mapped command: `ae-cli engage-task task stats`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--req` | json | Yes | statistics-condition JSON object |

## `--req` Object Fields

The `--req` structure of `engage-task task stats` is broadly the same as `engage-task task list`, and common fields include:

| Field | Type | Required | Description |
|------|------|------|------|
| `mappingStatus` | number | No | status filter |
| `triggerType` | number | No | trigger type filter |
| `channelType` | number | No | channel type filter |
| `groupId` | number | No | group ID |
| `creator` | string | No | creator open_id |
| `fuzzyField` | string | No | fuzzy search by task ID or task name |
| `belongActivity` | number | No | activity association filter |
| `expStatusList` | array | No | experiment status list |
| `expReleaseStatusList` | array | No | experiment release status list |
| `expTypeList` | array | No | experiment type list |

`projectId` is automatically injected into `--req` by the CLI.

## Enum Notes

### `req.mappingStatus`

- `0`: draft
- `1`: in progress
- `2`: paused
- `3`: ended
- `4`: approving
- `5`: denied

### `req.triggerType`

- `0`: scheduled-single
- `1`: scheduled-recurring
- `2`: manual
- `3`: trigger-complete A
- `4`: trigger-complete A then B
- `5`: trigger-complete A but not B
- `6`: custom trigger

### `req.channelType`

- `1`: webhook
- `2`: app_push
- `3`: client_push
- `4`: wechat
- `5`: dou_yin

### `req.belongActivity`

- `0`: all
- `1`: activity linked
- `2`: activity not linked

### `req.expStatusList[]`

- `0`: experiment not created
- `1`: experiment created

### `req.expReleaseStatusList[]`

- `0`: experiment not released
- `1`: experiment released

### `req.expTypeList[]`

- `0`: normal
- `1`: orthogonal

## Examples

```bash
ae-cli engage-task task stats --project-id 1 --req '{"pageNum":1,"pageSize":20}'
```
