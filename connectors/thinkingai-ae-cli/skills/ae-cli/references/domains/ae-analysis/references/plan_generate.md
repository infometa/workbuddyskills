# tracking plan generate

Use when submit an AI tracking plan generation task.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking plan generate --project-id <project_id> --language <zh-CN|en-US|ja-JP|ko-KR> --form-data '<json_object>' [--development-carrier '<json_array>'] [--predefined-event '<json_array>']
```

Capability id: `tracking.plan.generate`

Input sends `project_id`, `language`, `form_data`, optional `development_carrier`, and optional `predefined_event`. The backend resolves `company_id` from the authorized project. `form_data` is the intentionally open business-context object; all surrounding fields are explicit. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | Numeric project ID. | Yes |
| `--language` | Generation language: `zh-CN`, `en-US`, `ja-JP`, or `ko-KR`. | Yes |
| `--form-data` | Structured business context, for example account system, revenue model, core gameplay, currency system, and main entries. | Yes |
| `--development-carrier` | Development platforms such as Android, iOS, or Unity. | No |
| `--predefined-event` | Predefined event names such as install, start, or close. | No |
