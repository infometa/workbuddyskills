# analysis dashboard share

Use when the user explicitly wants to add, remove, or batch modify dashboard sharing.

Do not use to read sharing only. Use `dashboard share-info`.

Command:

```bash
ae-cli analysis dashboard share --project-id <project_id> --dashboard-id <dashboard_id> --member-authorities '{"10001":"READ","10002":"EDIT"}'
```

Input sends `project_id`, `dashboard_id`, and either `member_authorities` or a documented snake_case `payload`.

`member_authorities` is the complete directly shared user map, not an incremental patch:

- each key is a numeric user ID encoded as a JSON object key;
- each value is `READ`, `EDIT`, `CREATOR`, or `MAINTAIN`;
- users omitted from the map are removed from direct sharing;
- `{}` removes all directly shared users.

Call `analysis dashboard share-info` first when the user intends to preserve existing members while adding or changing only some entries.

Output is the gateway envelope. `data` contains the share update result.
