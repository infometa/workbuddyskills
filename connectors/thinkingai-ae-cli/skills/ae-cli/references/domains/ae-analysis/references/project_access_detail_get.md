# project access-detail get

Use when the user needs to get company project access details.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project access-detail get --company-id <company_id>
ae-cli project access-detail get --dry-run --company-id <company_id>
```

Capability id: `project.access_detail.get`.

Input sends `company_id`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
