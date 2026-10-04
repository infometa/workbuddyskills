# ae-cli engage-task task manage


Perform task lifecycle actions such as send, pause, end, or review.

Mapped command: `ae-cli engage-task task manage`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--task-id` | string | Yes | task ID |
| `--action` | string | Yes | action type |
| `--reason` | string | No | reason for review actions |

## Enum Notes

### `--action`

- `send`: send immediately, typically for manually triggered tasks in the waiting state
- `pause`: pause a running task
- `end`: end a running or paused task
- `approve`: review approved
- `deny`: review denied
- `cancel`: cancel review

## Safety Constraints

This command is a **write operation** and and changes the task status.

## Examples

```bash
ae-cli engage-task task manage --project-id 1 --task-id task_123 --action pause
```
