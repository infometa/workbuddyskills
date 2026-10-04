# analysis bi-panel-version get

Use when the user needs a BI panel's released version or unpublished draft version.

Do not use `bi-panel get` for draft verification; `bi-panel get` reads only the
released/queryable structure.

Command:

```bash
ae-cli analysis bi-panel-version get --project-id <project_id> --panel-id <panel_id> --version-type draft
ae-cli analysis bi-panel-version get --project-id <project_id> --panel-uuid <panel_uuid> --version-type release
```

Input sends `project_id`, one of `panel_id` or `panel_uuid`, optional
`version_type` (`release` by default), and optional `fields`.

Output is the gateway envelope. `data` contains `panel_id`, `panel_uuid`,
`requested_version_type`, `version_type`, `version`, `page_content`,
`panel_config`, and `worksheet_map`.

When the result is used before publishing, save `data.version` and pass it as
`--source-version` to `bi-panel-version publish`.
