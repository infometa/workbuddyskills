# agent +del-attachment (Delete Attachment)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Attachments / write**

## Use Cases
- Soft-delete an attachment.
- Endpoint: `DELETE /api/sandbox/agent/attachments?id=[id]`.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real attachment ID via `+list-attachments` — do not guess.
- This is a soft delete — prefer `--dry-run` before executing.
- This is a high-risk-write operation; never execute it before the dry-run impact is explicitly confirmed.

## Command
```bash
ae-cli agent +del-attachment --id <attachment-id> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli agent +del-attachment --id <attachment-id> --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Attachment ID |

## Decision Rules
- Confirm the attachment ID with `+list-attachments` before deleting.
- This is a soft delete, not a physical removal.

## Next Steps on Failure
- `404` / not found: re-run `+list-attachments` to verify the attachment ID.

## Recommended Chaining
- `+list-attachments` → confirm `id` → `+del-attachment`
