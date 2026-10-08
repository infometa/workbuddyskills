# analysis bi-panel share

Use when the user wants to modify BI panel sharing members.

Do not use to share dashboards or folders. Use the matching resource share command.

Command:

```bash
ae-cli analysis bi-panel share --project-id <project_id> --panel-id <panel_id> [--payload '{...}']
```

Input sends `project_id`, `panel_id`, and backend-compatible snake_case `payload`.

Supported payload fields include:

- `all_auth_user_authority`: project-wide BI panel authority. Use `READ`, `JUNIOR`, `SENIOR`, or `MAINTAIN`; `VIEWER` is accepted as `READ`.
- `auth_users`: user authority list.
- `auth_user_groups`: user-group authority list.

Output is the gateway envelope. `data` contains the share update result.
