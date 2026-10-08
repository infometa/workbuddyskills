# system seat update

Use when the user needs to assign management/view BI seats or remove seats from an explicit member set.

Do not use it without first reading current seat assignments and company quota with `ae-cli system seat list`.

Command:

```bash
ae-cli system seat update --dry-run --company-id <company_id> --seat-type <manage_or_view_or_empty> --open-ids '["ou_xxx"]'
ae-cli system seat update --company-id <company_id> --seat-type <manage_or_view_or_empty> --open-ids '["ou_xxx"]' --yes
```

Capability id: `system.seat.update`.

`seat-type=empty` removes seats. Run `--dry-run` first and verify additions, removals, unchanged members, and license quota impact. Wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. A quota conflict is not proof of a partial update; inspect the returned transactional result.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--seat-type` | Yes | `manage`, `view`, or `empty`; `empty` removes seats. |
| `--open-ids` | Yes | Non-empty company member open-ID JSON array. |
