# system smtp upsert

Use when the user needs to create or update company SMTP configuration using a protected password source.

Do not use it outside the system smtp operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system smtp upsert --company-id <company-id> --server-host <server-host> --server-port <server-port> --sender-address <sender-address> --sender-name <sender-name> --password-file <chmod_600_file>
```

Capability id: `system.smtp.upsert`.

Sensitive values are accepted only through a permission-protected file or stdin. Never put a secret value in argv, examples, logs, validation output, dry-run output, or the response.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--server-host` | Yes | SMTP server host. |
| `--server-port` | Yes | SMTP server port. |
| `--has-encrypt` | No | Encryption mode: 0, 1, or 2. |
| `--sender-address` | Yes | Sender email address. |
| `--sender-name` | Yes | Sender display name. |
| `--subject-prefix` | No | Optional subject prefix. |
| `--password-file` | No | SMTP password. Read from a local permission-protected file; one of file/stdin is required. |
| `--password-stdin` | No | SMTP password. Read from stdin; one of file/stdin is required. |
