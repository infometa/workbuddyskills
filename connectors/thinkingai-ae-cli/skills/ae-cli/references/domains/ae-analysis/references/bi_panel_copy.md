# analysis bi-panel copy

Use when the user wants to copy a BI panel, optionally targeting a project space or folder.

Do not use to create a blank BI panel. Use `bi-panel create`.

Command:

```bash
ae-cli analysis bi-panel copy --project-id <project_id> [--panel-name <name>] [--panel-uuid <source_uuid>] [--space-id <space_id>] [--folder-id <folder_id>] [--payload '{...}']
```

Input sends `project_id`, optional source/target fields, and `payload`.

Output is the gateway envelope. `data` contains the copied BI panel result.
