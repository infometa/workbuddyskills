# system ops-alert-contact upsert

Use when the user needs to create or update an operations-alert contact without exposing webhooks on argv.

Do not use it outside the system ops-alert-contact operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system ops-alert-contact upsert --company-id <company_id> --name <name> --mail-address <mail_address> --on-status 1
ae-cli system ops-alert-contact upsert --company-id <company_id> --contact-id <contact_id> --feishu-webhook-file <chmod_600_file>
```

Capability id: `system.ops_alert_contact.upsert`.

Sensitive values are accepted only through a permission-protected file or stdin. Never put a secret value in argv, examples, logs, validation output, dry-run output, or the response.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--contact-id` | No | Existing contact ID; omit to create. |
| `--name` | No | Contact name. |
| `--mail-address` | No | Email delivery target. |
| `--mobile` | No | Mobile delivery target. |
| `--on-status` | No | Enable state: 0 or 1; required on create. |
| `--dingding-webhook-file` | No | DingTalk webhook. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--dingding-webhook-stdin` | No | DingTalk webhook. Read from stdin; do not combine with --dingding-webhook-file. |
| `--wechat-webhook-file` | No | WeCom webhook. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--wechat-webhook-stdin` | No | WeCom webhook. Read from stdin; do not combine with --wechat-webhook-file. |
| `--feishu-webhook-file` | No | Feishu webhook. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--feishu-webhook-stdin` | No | Feishu webhook. Read from stdin; do not combine with --feishu-webhook-file. |
| `--slack-webhook-file` | No | Slack webhook. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--slack-webhook-stdin` | No | Slack webhook. Read from stdin; do not combine with --slack-webhook-file. |
| `--kim-webhook-file` | No | KIM webhook. Read from a local permission-protected file; the value is never accepted directly on argv. |
| `--kim-webhook-stdin` | No | KIM webhook. Read from stdin; do not combine with --kim-webhook-file. |
