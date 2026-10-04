# analysis bi-panel create

Use when the user explicitly wants to create a BI dashboard (`仪表盘`) as an empty shell, including requests phrased as `BI 仪表盘`.

Do not use for an analysis board (`看板`); use `analysis dashboard create` instead. Do not use to copy an existing BI dashboard; use `bi-panel copy`.

This first-version capability creates an empty BI-dashboard shell only. It does
not create pages, charts, worksheets, draft content, or released content.
Use `bi-panel copy` when the new BI dashboard should inherit an existing
released definition. The CLI does not currently expose draft-content writes.

Command:

```bash
ae-cli analysis bi-panel create --project-id <project_id> --panel-name <name> [--space-id <space_id>] [--folder-id <folder_id>]
```

Input sends required `project_id` and `panel_name`, plus optional target
`space_id` and `folder_id`.

Output is the gateway envelope. `data` contains the created BI-dashboard shell
identifier. Released-only reads and page-data queries remain unavailable until
content is created and released through another supported producer.
