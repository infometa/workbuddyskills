# tracking plan import-excel

Use when import a tracking plan Excel file that was uploaded as an input file.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking plan import-excel [options]
```

Capability id: `tracking.plan.import_excel`

Input sends `project_id`, `input_file_id`, and optional `lang`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--input-file-id` | See command help | Yes |
| `--lang` | See command help | No |

