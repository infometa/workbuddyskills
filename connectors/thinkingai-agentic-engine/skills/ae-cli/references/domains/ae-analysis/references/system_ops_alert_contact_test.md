# system ops-alert-contact test

Use when the user explicitly asks to send one test alert through a configured channel.

Do not use it for bulk delivery, repeated probing, or an unconstrained HTTP destination.

Command:

```bash
ae-cli system ops-alert-contact test --dry-run --company-id <company_id> --channel <channel> --target-file <chmod_600_file>
ae-cli system ops-alert-contact test --company-id <company_id> --channel <channel> --target-file <chmod_600_file>
```

Capability id: `system.ops_alert_contact.test`.

The target is sensitive and is accepted only through a permission-protected file or stdin. Never place it directly in argv, examples, logs, validation output, dry-run output, or the response.

Webhook channels accept only constrained HTTPS hosts. The service rate-limits each caller and channel to one request per 60 seconds. Use `--dry-run` when the destination or channel needs review, then execute directly as an ordinary write.

The response returns only the channel and delivery result; it must not return the target or stored channel secrets. Do not retry a rate-limit or host-validation failure unchanged.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--channel` | Yes | `email`, `sms`, `dingding`, `wechat`, `feishu`, or `slack`. |
| `--target-file` | No | Sensitive destination in a permission-protected file; one of file/stdin is required. |
| `--target-stdin` | No | Read the sensitive destination from stdin; one of file/stdin is required. |
