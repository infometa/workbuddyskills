# analysis folder share (L3)

Use when the user wants to modify folder sharing members.

Do not use to inspect members only. Use `analysis.folder.members` via `capability search/inspect/run`; see [`analysis_gateway_assets.md`](analysis_gateway_assets.md) L3 members section.

This capability has no curated `ae-cli analysis` command. Read [`ae-capability`](../../ae-capability/SKILL.md) (on-demand validate/dry-run table), then:

```bash
ae-cli capability inspect analysis.folder.share
ae-cli capability run analysis.folder.share --input '{"project_id":1,"folder_id":1001,"payload":{...}}'
```

`risk=write` — no chat confirmation required. Compose nested `payload` from the inspect `input_schema`.

Input uses snake_case JSON. Common fields:

| field | type | required | description |
| --- | --- | --- | --- |
| `project_id` | integer | yes | Project ID. |
| `folder_id` | integer | yes | Folder ID. |
| `payload` | object | no | Optional snake_case share/member update payload. Inspect the capability schema before composing it. |

Output is the gateway envelope. `data` contains the share update result.
