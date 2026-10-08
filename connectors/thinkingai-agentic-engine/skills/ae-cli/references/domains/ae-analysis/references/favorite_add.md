# analysis favorite add

Use when the user wants to favorite one dashboard, BI panel, or folder.

Do not use for sharing or moving assets.

Command:

```bash
ae-cli analysis favorite add --project-id <project_id> --asset-id <id> --asset-type dashboard|bi_panel|folder [--space-id <space_id>]
```

Input sends `project_id`, `asset_id`, `asset_type`, and optional `space_id`.

Output is the gateway envelope. `data` contains the favorite result.
