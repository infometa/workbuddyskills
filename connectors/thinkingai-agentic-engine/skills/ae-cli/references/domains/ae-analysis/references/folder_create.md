# analysis folder create (L3)

Use when the user wants to create a folder in personal space or project space.

Do not use to create a project space. Use `analysis.project_space.create` via capability run.

This capability has no curated `ae-cli analysis` command. Read [`ae-capability`](../../ae-capability/SKILL.md) (on-demand validate/dry-run table), then:

```bash
ae-cli capability inspect analysis.folder.create
ae-cli capability run analysis.folder.create --input '{"project_id":1,"folder_name":"Weekly","space_id":10}'
```

`risk=write` — no chat confirmation required.

Input uses snake_case JSON. Common fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `project_id` | integer | yes | Project ID. |
| `folder_name` | string | no | Folder name. |
| `space_id` | integer | no | Project space ID. Omit for personal-space folders. |
| `parent_folder_id` | integer | no | Parent project-space folder ID. |
| `payload` | object | no | Optional snake_case object for complex create payloads. |

Output is the gateway envelope. `data` contains the created folder result.
