# Zoho Projects Routing Reference

**App name:** `zoho-projects`
**Base URL proxied:** `projectsapi.zoho.com`

## API Path Pattern

```
/zoho-projects/api/v3/portals
/zoho-projects/api/v3/portal/{portal_id}/projects
/zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks
/zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasklists
/zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/milestones
/zoho-projects/api/v3/portal/{portal_id}/users
```

## Important Notes

- V3 uses `/api/v3/` prefix (not `/restapi/`)
- No trailing slashes — trailing slashes return 400
- All POST/PATCH requests use `application/json` (not form-urlencoded)
- Updates use PATCH method (not POST)
- Portal ID is required for most endpoints
- Date format for milestones: `MM-dd-yyyy`
- Delete operations return 204 No Content
- Create operations return 201 Created

## Common Endpoints

### Portals

#### List Portals
```bash
GET /zoho-projects/api/v3/portals
```

### Projects

#### List Projects
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects
```

#### Get Project
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}
```

#### Create Project
```bash
POST /zoho-projects/api/v3/portal/{portal_id}/projects
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description"
}
```

#### Update Project
```bash
PATCH /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Name"
}
```

#### Delete Project
```bash
DELETE /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}
```

### Tasks

#### List Tasks
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks
```

#### Get Task
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}
```

#### Create Task
```bash
POST /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks
Content-Type: application/json

{
  "name": "New Task",
  "priority": "high"
}
```

#### Update Task
```bash
PATCH /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "priority": "medium"
}
```

#### Delete Task
```bash
DELETE /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}
```

### Task Comments

#### List Comments
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/comments
```

#### Add Comment
```bash
POST /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/comments
Content-Type: application/json

{
  "comment": "Comment text"
}
```

Note: The field name is `comment`, not `content`.

#### Delete Comment
```bash
DELETE /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/comments/{comment_id}
```

### Tasklists

#### List Tasklists
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasklists
```

#### Create Tasklist
```bash
POST /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasklists
Content-Type: application/json

{
  "name": "New Tasklist",
  "flag": "internal"
}
```

#### Update Tasklist
```bash
PATCH /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasklists/{tasklist_id}
Content-Type: application/json

{
  "name": "Updated Name"
}
```

#### Delete Tasklist
```bash
DELETE /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasklists/{tasklist_id}
```

### Milestones

#### List Milestones
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/milestones
```

#### Create Milestone
```bash
POST /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/milestones
Content-Type: application/json

{
  "name": "Phase 1",
  "start_date": "06-01-2026",
  "end_date": "06-15-2026",
  "flag": "internal",
  "owner_zpuid": "{user_zpuid}"
}
```

Required fields: `name`, `start_date`, `end_date`, `flag`, `owner_zpuid`

#### Update Milestone
```bash
PATCH /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/milestones/{milestone_id}
Content-Type: application/json

{
  "name": "Updated Phase"
}
```

#### Delete Milestone
```bash
DELETE /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/milestones/{milestone_id}
```

### Users

#### List Users
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/users
```

## Pagination

Page-based pagination with `page` and `per_page` parameters:
```bash
GET /zoho-projects/api/v3/portal/{portal_id}/projects/{project_id}/tasks?page=1&per_page=50
```

Response includes `page_info`:
```json
{
  "page_info": {
    "page": 1,
    "per_page": 50,
    "has_next_page": true
  },
  "tasks": [...]
}
```

When `has_next_page` is `true`, increment `page` to get the next batch.

## Resources

- [Zoho Projects API V3 Documentation](https://projects.zoho.com/api-docs)
- [Zoho Projects Developer Portal](https://www.zoho.com/projects/help/rest-api/zohoprojectsapi.html)
