# Lark-Task - Tasks & To-Do Lists

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Task**: Individual to-do item
- **Task List**: Collection of tasks
- **Subtask**: Task nested under parent task
- **Assignee**: User assigned to task
- **Milestone**: Deadline or target date
- **Priority**: Task importance level (low, medium, high, urgent)

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+tasks-create` | Create new task |
| `+tasks-list` | List tasks with filters/sorting |
| `+task-lists-list` | List available task lists |
| `+tasks-update` | Update task status/assignee |

## Typical Workflow

1. **View my tasks**: `lark-cli task +tasks-list --assignee me --status active`
2. **Create task**: `lark-cli task +tasks-create --title "Review PR #123" --due-date 2024-02-15`
3. **Assign task**: `lark-cli task tasks update --task-id task_xxx --assignee ou_yyy`
4. **Mark complete**: `lark-cli task tasks update --task-id task_xxx --status completed`
5. **Create subtask**: `lark-cli task subtasks create --task-id task_xxx --title "Subtask"`

## API Resources

### tasks
- `create` — Create task
- `list` — List tasks
- `get` — Get task details
- `update` — Update task (title, status, assignee, etc.)
- `delete` — Delete task

### task_lists
- `create` — Create task list
- `list` — List task lists
- `get` — Get list details
- `update` — Update list name/description
- `delete` — Delete list

### subtasks
- `create` — Create subtask
- `list` — List subtasks
- `update` — Update subtask
- `delete` — Delete subtask

### tasks.collaborators
- `create` — Add collaborator to task
- `list` — List task collaborators
- `delete` — Remove collaborator

## Status Values

- active
- completed
- archived
- cancelled

## Permission Table

| Method | Required Scope |
|--------|----------------|
| tasks.create | task:task:create |
| tasks.list | task:task:read |
| tasks.get | task:task:read |
| tasks.update | task:task:edit |
| tasks.delete | task:task:delete |
| task_lists.* | task:taskList:* |

