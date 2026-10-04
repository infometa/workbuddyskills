# tracking plan sync-display-names

Use this local orchestration command after uploading a tracking plan, and rerun it after the first Debug or production data arrives.
Do not use it to rename metadata that already has a display name, create missing metadata, or replace the tracking-plan upload flow.

Command:

```bash
ae-cli tracking plan sync-display-names \
  --project-id <project_id> \
  --draft <draft.json>
```

The command reads localized `display_name` values from the local tracking-plan draft, lists the project's event, event-property, and user-property metadata, then calls `metadata.super_metadata.batch_edit` in bounded batches.

Safety and result rules:

- Only blank metadata display names are filled.
- Existing non-empty AE display names are never overwritten.
- `missing_in_metadata` means an event/property has not appeared in project metadata yet; rerun after data arrives.
- `missing_display_name_in_draft` means the draft is incomplete; add the localized display name, regenerate and validate the xlsx, then retry.

## Parameters

| Parameter      | Required | Description                                                                       |
| -------------- | -------- | --------------------------------------------------------------------------------- |
| `--project-id` | Yes      | Numeric AE project ID.                                                            |
| `--draft`      | Yes      | Local tracking-plan `draft.json` containing event/property `display_name` values. |
