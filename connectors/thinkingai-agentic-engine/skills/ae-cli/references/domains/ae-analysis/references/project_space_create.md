# analysis project-space create (L3)

Use when the user explicitly wants to create a project space.

Do not use to create folders inside a space. Use `analysis.folder.create` via capability run.

This capability has no curated `ae-cli analysis` command. Read [`ae-capability`](../../ae-capability/SKILL.md) (on-demand validate/dry-run table), then:

```bash
ae-cli capability inspect analysis.project_space.create
ae-cli capability run analysis.project_space.create --input '{"project_id":1,"space_name":"lds-test-071301","avatar_type":1}'
```

`risk=write` — no chat confirmation required.

Input uses snake_case JSON. Common fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `project_id` | integer | yes | Project ID. |
| `space_name` | string | no | Project space name. |
| `space_desc` | string | no | Project space description. |
| `avatar_type` | integer | no | Avatar type: 1=WORD, 2=ICON, 3=IMAGE. Default 1. |
| `color_key` | string | no | Avatar color key. |
| `avatar` | string | no | Avatar content. |
| `payload` | object | no | Optional snake_case object for complex create payloads. |

Output is the gateway envelope. `data` contains the created project-space result.
