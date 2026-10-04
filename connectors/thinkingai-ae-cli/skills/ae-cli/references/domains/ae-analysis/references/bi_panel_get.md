# analysis bi-panel get

Use when the user needs one BI panel's released page structure.

This command reads only the released/queryable structure. It can fail with
`NOT_FOUND` for a newly created or draft-only panel. To inspect unpublished
edits, use `bi-panel-version get --version-type draft`. To make draft edits
queryable, publish them with `bi-panel-version publish`.

Do not use to query chart data. Use `bi-panel-page-data run` or `bi-panel-page-data export`.

Command:

```bash
ae-cli analysis bi-panel get --project-id <project_id> --panel-id <panel_id> [--fields '["pages"]']
```

Input sends `project_id`, `panel_id`, and optional `fields`.

Supported fields are `basic`, `pages`, `charts`, `chartFilterControls`, `summary`,
`parameterControls`, and `permissionControls`.

Output is the gateway envelope. `data` contains the BI panel structure.
