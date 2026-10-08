# tracking sdk-sample generate

Use when submit an AI SDK sample generation task.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking sdk-sample generate --project-id <project_id> --sdk-types '<json_array>'
```

Capability id: `tracking.sdk_sample.generate`

Input sends `project_id` and `sdk_types`. The backend resolves company ID, app ID, and receiver URL from the authorized project. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | Numeric project ID. | Yes |
| `--sdk-types` | SDK type array. Supported values include `android-java`, `ios-swift`, `web-js`, `server-java`, `server-python`, `server-nodejs`, `unity-csharp`, and the other values listed by command help/schema. | Yes |
