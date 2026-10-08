# Cross-source asset configuration (L3)

Use this workflow for Asset Center → Cross-source asset configuration when the user has or can prepare an Excel configuration workbook. The CLI scope is intentionally limited to upload and validation. Do not use it for row-by-row configuration creation, editing, deletion, template export, source preview, or enum management.

## Discover the deployed contract

```bash
ae-cli capability search "cross_source_config" --domain metadata --project-id <project_id>
ae-cli capability inspect metadata.cross_source_config.upload --project-id <project_id>
ae-cli capability inspect metadata.cross_source_config.check --project-id <project_id>
ae-cli capability inspect metadata.cross_source_config.check_status --project-id <project_id>
ae-cli analysis input-file purpose list --project-id <project_id>
```

The expected catalog contains only:

- `metadata.cross_source_config.upload`
- `metadata.cross_source_config.list`
- `metadata.cross_source_config.check`
- `metadata.cross_source_config.check_status`

Use the **metadata** namespace; it routes through the analysis gateway. The deployed catalog and each capability's `input_schema` are authoritative. If upload purpose or a capability is unavailable, report that the Host has not deployed this workflow. Do not fall back to page REST, MCP, browser tokens, or direct database writes.

## Upload a workbook

1. Prepare the product-compatible XLS/XLSX configuration workbook from the user's source table and mapping requirements. If the workbook format is uncertain, obtain a current sample or use the page documentation before writing it; do not guess sheet names or column headers.
2. Upload the bytes once:

   ```bash
   ae-cli analysis input-file upload \
     --project-id <project_id> \
     --purpose cross_source_config.workbook \
     --file ./configured.xlsx
   ```

3. Retain `data.input_file_id`. It is bound to the authenticated user, project, purpose, and expiry. A local path is never an `input_file_id`.
4. Inspect the upload capability, then execute it once:

   ```bash
   ae-cli capability run metadata.cross_source_config.upload \
     --input '{"project_id":<project_id>,"input_file_id":"<input_file_id>","lang":"zh"}'
   ```

Upload is a synchronous call to the same import service used by the Asset Center page. It creates new route codes and updates existing route codes contained in the workbook. It does not delete configurations absent from the workbook. Because an existing route can be replaced, `upload` is `high-risk-write` and requires user review before execution. Use the CLI confirmation prompt interactively; in non-interactive execution, append the global `--yes` flag only after the exact upload has been authorized.

`status=success` means workbook parsing and persistence completed. If `requires_review=true`, inspect `result.fail` and open `page_url`. An error response keeps the business result in `meta.business_result`. Do not automatically retry after a timeout or lost response; call `list` and inspect the page first.

## Validate uploaded configurations

List configurations to resolve real IDs and current states:

```bash
ae-cli capability run metadata.cross_source_config.list \
  --input '{"project_id":<project_id>}'
```

Submit validation only for explicit IDs from that project:

```bash
ae-cli capability run metadata.cross_source_config.check \
  --input '{"project_id":<project_id>,"ids":[<route_id>]}'
```

Then poll the same ID set with a bounded interval:

```bash
ae-cli capability run metadata.cross_source_config.check_status \
  --input '{"project_id":<project_id>,"ids":[<route_id>]}'
```

Interpret the aggregate fields before reading individual `items`:

- `status=checking`, `completed=false`: wait and poll again.
- `status=un_checked`, `completed=false`: validation has not been submitted for every selected configuration; `next_action=check`.
- `status=check_success`, `completed=true`, `successful=true`: all selected configurations passed.
- `status=check_fail`, `completed=true`, `successful=false`: inspect each item's `msg_map` and open `page_url`.

A successful gateway envelope only means the read succeeded. Validation passes only when `successful=true`. Do not resubmit `check` while a selected configuration is already `checking`.

## Page handoff

`list`, `upload`, `check`, and `check_status` return `page_path`. ae-cli converts it to a Host-qualified `page_url`. Surface this URL after upload warnings, validation failures, or whenever the user asks to review the configurations visually.

Gateway `validate` and `dry-run` validate input, project scope, selected IDs, and uploaded-file ownership. They do not parse/import the workbook or start configuration validation.
