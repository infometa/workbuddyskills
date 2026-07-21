# Google Tasks Routing Reference

**App name:** `google-tasks`
**Base URL proxied:** `tasks.googleapis.com`

## API Path Pattern

```
/google-tasks/tasks/v1/{endpoint}
```

## Common Endpoints

### Task Lists

#### List Task Lists
```bash
GET /google-tasks/tasks/v1/users/@me/lists
```

Example:

```bash
maton google-tasks tasklist list
```

With pagination:
```bash
GET /google-tasks/tasks/v1/users/@me/lists?maxResults=20
```

#### Get Task List
```bash
GET /google-tasks/tasks/v1/users/@me/lists/{tasklistId}
```

Example:

```bash
maton google-tasks tasklist view <tasklistId>
```

#### Create Task List
```bash
POST /google-tasks/tasks/v1/users/@me/lists
Content-Type: application/json

{
  "title": "New Task List"
}
```

Example:

```bash
maton google-tasks tasklist create --title 'New Task List'
```

#### Update Task List
```bash
PATCH /google-tasks/tasks/v1/users/@me/lists/{tasklistId}
Content-Type: application/json

{
  "title": "Updated Title"
}
```

Example:

```bash
maton google-tasks tasklist update <tasklistId> --title 'Updated Title'
```

#### Delete Task List
```bash
DELETE /google-tasks/tasks/v1/users/@me/lists/{tasklistId}
```

Example:

```bash
maton google-tasks tasklist delete <tasklistId>
```

### Tasks

#### List Tasks
```bash
GET /google-tasks/tasks/v1/lists/{tasklistId}/tasks
```

Example:

```bash
maton google-tasks task list -l <tasklistId>
```

With filters:
```bash
GET /google-tasks/tasks/v1/lists/{tasklistId}/tasks?showCompleted=true&showHidden=true&maxResults=50
```

Example:

```bash
maton google-tasks task list -l <tasklistId> --show-completed
```

With date filters:
```bash
GET /google-tasks/tasks/v1/lists/{tasklistId}/tasks?dueMin=2026-01-01T00:00:00Z&dueMax=2026-12-31T23:59:59Z
```

#### Get Task
```bash
GET /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}
```

Example:

```bash
maton google-tasks task view <taskId> -l <tasklistId>
```

#### Create Task
```bash
POST /google-tasks/tasks/v1/lists/{tasklistId}/tasks
Content-Type: application/json

{
  "title": "New Task",
  "notes": "Task description",
  "due": "2026-03-01T00:00:00.000Z"
}
```

Example:

```bash
maton google-tasks task create -l <tasklistId> --title 'New Task' --notes 'Task description' --due 2026-03-01
```

Create subtask:
```bash
POST /google-tasks/tasks/v1/lists/{tasklistId}/tasks?parent={parentTaskId}
Content-Type: application/json

{
  "title": "Subtask"
}
```

#### Update Task (partial)
```bash
PATCH /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "completed"
}
```

Example:

```bash
maton google-tasks task update <taskId> -l <tasklistId> --title 'Updated Title' --status completed
```

#### Update Task (full replace)
```bash
PUT /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}
Content-Type: application/json

{
  "title": "Replaced Task",
  "notes": "New notes",
  "status": "needsAction"
}
```

Example:

```bash
maton google-tasks task update <taskId> -l <tasklistId> --title 'Replaced Task' --notes 'New notes' --status needsAction --replace
```

#### Delete Task
```bash
DELETE /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}
```

Example:

```bash
maton google-tasks task delete <taskId> -l <tasklistId>
```

#### Move Task
```bash
POST /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}/move?previous={previousTaskId}
```

Example:

```bash
maton google-tasks task move <taskId> -l <tasklistId> --previous <siblingTaskId>
```

Make subtask:
```bash
POST /google-tasks/tasks/v1/lists/{tasklistId}/tasks/{taskId}/move?parent={parentTaskId}
```

#### Clear Completed Tasks
```bash
POST /google-tasks/tasks/v1/lists/{tasklistId}/clear
```

Example:

```bash
maton google-tasks tasklist clear <tasklistId>
```

## Pagination

Google Tasks uses token-based pagination. The CLI handles this automatically with `--paginate`:

```bash
maton google-tasks task list -l <tasklistId> --paginate
```

For raw HTTP requests, pass the `nextPageToken` from the previous response as the `pageToken` query parameter.

## Notes

- Authentication is automatic - the router injects the OAuth token
- Task list and task IDs are opaque base64-encoded strings
- Status values: "needsAction" or "completed"
- Dates must be in RFC 3339 format (e.g., `2026-01-15T00:00:00.000Z`)
- Maximum title length: 1024 characters
- Maximum notes length: 8192 characters

## Resources

- [Google Tasks API Overview](https://developers.google.com/workspace/tasks)
- [Tasks Reference](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks)
- [TaskLists Reference](https://developers.google.com/workspace/tasks/reference/rest/v1/tasklists)
- [Maton CLI Manual](https://cli.maton.ai/manual)