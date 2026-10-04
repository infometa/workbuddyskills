# analysis project-space get

Use when the user needs one project space detail or name.

Do not use to list all spaces. Use `project-space list`.

Command:

```bash
ae-cli analysis project-space get --project-id <project_id> --space-id <space_id> [--fields '["space_id","space_name"]']
```

Input sends `project_id`, `space_id`, and optional `fields`.

Supported fields are `space_id`, `space_name`, `space_desc`, `avatar_type`, `color_key`, `avatar`,
`all_auth_user_authority`, `create_time`, `update_time`, and `owner`.

Output is the gateway envelope. `data` contains project-space detail with snake_case field names.
