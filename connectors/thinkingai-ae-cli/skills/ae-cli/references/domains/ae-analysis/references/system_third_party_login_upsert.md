# system third-party-login upsert

Use when the user needs to create or update a third-party login configuration using protected secret sources.

Do not use it outside the system third-party-login operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system third-party-login upsert --company-id <company_id> --login-type feishu --app-id <app_id> --app-secret-file <chmod_600_file>
ae-cli system third-party-login upsert --company-id <company_id> --login-type dingtalk --app-id <app_id> --corp-id <corp_id> --agent-id <agent_id> --dd-scan-app-id <scan_app_id> --app-secret-file <chmod_600_file> --dd-scan-app-secret-file <chmod_600_file>
```

Capability id: `system.third_party_login.upsert`.

Sensitive values are accepted only through a permission-protected file or stdin. Never put a secret value in argv, examples, logs, validation output, dry-run output, or the response.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--login-type` | Yes | Third-party login type. |
| `--app-id` | Yes | Provider application ID. |
| `--corp-id` | No | Provider corporation ID. |
| `--agent-id` | No | Provider agent ID. |
| `--dd-scan-app-id` | No | DingTalk scan-login application ID. |
| `--app-secret-file` | No | Provider application secret. Read from a local permission-protected file; one of file/stdin is required. |
| `--app-secret-stdin` | No | Provider application secret. Read from stdin; one of file/stdin is required. |
| `--dd-scan-app-secret-file` | No | DingTalk scan-login application secret. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--dd-scan-app-secret-stdin` | No | DingTalk scan-login application secret. Read from stdin; do not combine with --dd-scan-app-secret-file. |
