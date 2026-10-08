# analysis bi-panel update

Use only when the user wants to rename a BI dashboard.

This first-version capability does not modify pages, charts, worksheets, draft
content, or released content. Do not use it as a content-update command.

`bi-panel get` reads only the released/queryable version. If another product
entry point has created a draft, use
`bi-panel-version get --version-type draft` to inspect it and
`bi-panel-version publish` to publish its matching `source_version`.

Command:

```bash
ae-cli analysis bi-panel update --project-id <project_id> --panel-uuid <uuid> --panel-name <new_name>
```

Input sends required `project_id`, `panel_uuid`, and new `panel_name`.

Output is the gateway envelope. `data.updated=true` confirms the rename.
