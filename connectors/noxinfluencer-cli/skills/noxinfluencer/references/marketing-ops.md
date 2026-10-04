# Marketing Ops Workflows

Use this reference for NoxInfluencer campaign, collection, CRM, email, message, product, short-link, affiliation, creator dispute, file, report, and export operations. Keep command parameters runtime-discovered with `noxinfluencer schema <cmd>`.

## Domain Routing

| User intent | Start with |
|-------------|------------|
| Find or inspect campaigns | `campaign list`, `campaign get`, `campaign dashboard`, `campaign dropdown` |
| Create or change campaign skeleton data | `campaign init`, `campaign create`, `campaign update`, `campaign delete` |
| Find or inspect collections | `collection list`, `collection get`, `collection items`, `collection resources` |
| Add creators from search/profile results to collections | `collection add-creators` |
| Import owned creator links into one collection | `collection import-template`, then `collection import-file` |
| Find creators similar to a source creator | `creator lookalikes` |
| Export selected creator search/lookalike results | deep `creator export-preview`, then `creator export` / `creator lookalikes-export` |
| Batch move/copy/delete/label collection members | `collection batch-* validate`, then `preview`, then `apply` |
| Refresh collection base/email data or unlock audience | `collection refresh* validate`, then `preview`, then `apply` |
| Add one whole collection and platform slice to CRM | `collection add-to-crm validate`, then `preview`, then `apply` |
| Query, import, or update NoxInfluencer CRM channels | `crm list/get/update`, `crm import-template/import-file/import-report`, `crm groups ...` |
| Manage CRM labels for batch tagging | `crm labels list/create/update/delete` |
| Manage product-center records, images, and tags | `product list/get/create/update/delete`, `product image upload`, `product tags ...` |
| Manage Shopify affiliate campaigns and members | `affiliation stores list`, then `affiliation campaigns ...` / `affiliation members ...`; use member template/import and campaign export for files |
| Send standalone platform email outreach to creators | `email create`, then `email recipients add/replace` with search `data.items[].id` or creator read `data.creator_id` in the recipient `creator_id` field, `email content save`, `email sender list [task_id]` before optional `email sender update`, optional `email attachments ...`, then `email send` or `email schedule` |
| Add recipients to an intelligent Campaign fixed task | Use the SaaS intelligent Campaign page; the current CLI cannot discover or write fixed tasks safely |
| Manage email tasks | `email list`, `email drafts`, `email get`, `email create`, `email update`, `email recipients ...`, `email content ...`, `email sender ...`, `email report`, `email team-summary`, `email team-breakdown` |
| Import email recipients | `email recipients import-template`, then `email recipients import-file` |
| Manage email recipient deduplication | `email recipients filter options`, then `email recipients filter get/update/tasks` |
| Manage email task collaborators | `email collaborators list`, then `replace/add/remove` |
| Manage email task attachments | `email attachments list/upload/download/delete` |
| Send or schedule an existing email task | `email send`, `email schedule`, `email cancel` |
| Manage message threads and files | `message list/get/projects/archive`, `message draft ...`, `message attachments ...`, `message templates attachments ...` |
| Upload a public rich-text image | `file image upload`, then embed returned `file_url` in approved `html_body` |
| Download direct Excel reports | `monitor report*`, `short-link export-*`, `affiliation campaigns export` |
| Send or schedule an existing message reply | `message send`, `message schedule`, `message cancel` |
| Submit product feedback or a bug report | `feedback submit`, then `feedback inbox` / `feedback get` |
| Check or report a concrete creator collaboration dispute | `dispute records <creator_id>` first, then `dispute report` only with evidence and approval |
| Inspect or download shared async exports | `export list`, `export get`, `export download` for creator, collection, CRM, and brand-monitor tasks |

## Outreach Routing

- Standalone NoxInfluencer platform email outreach uses type 3 tasks only. Do not call `creator contacts` first. Create or select a standalone email task without `campaign_id` or `task_type`, then add recipients with search `data.items[].id` or creator read `data.creator_id` in the recipient `creator_id` field. If the user already has a canonical raw platform identity, use `platform + channel_id`; use `email_address` only for a known external address. URL, handle, and creator name are not direct recipient identifiers and must be resolved first. Save user-approved content with `email content save`, set the sender if needed, read back the task and recipients, then ask for final approval before `email send --force` or `email schedule --force`.
- An intelligent Campaign initializes exactly three fixed tasks by recipient source: type 0 manual-add, type 1 proactive invitation, and type 2 creator application. Type 1 is a source responsibility, not permission to infer a fixed task ID. The current CLI cannot discover or write these fixed tasks safely, so use the SaaS intelligent Campaign page. Never guess a fixed `task_id`, pass `task_type`, inject `campaign_id` into a standalone mutation, or use standalone recipient commands against a fixed task.
- Use `creator contacts` only when the user explicitly wants visible/exported contact info or outreach outside NoxInfluencer. If the user vaguely asks to "find emails and send", choose platform email by default and say exported email retrieval uses extra contact quota.
- Email attachments belong to the email task primary project. Upload approved files with `email attachments upload <task_id> --file <path>` before send or schedule; use `email attachments list/download/delete` to inspect, retrieve, or remove files. Email tasks support at most 1 attachment, max 10MB. Uploading or deleting an attachment cancels an existing scheduled send, so read back the task and confirm again before scheduling.
- If approved recipients come from Excel, download `email recipients import-template` and use `email recipients import-file <task_id>`. Do not invent spreadsheet columns.
- Email recipient import is only available before the task enters its active send flow.
- For one email task's reply reporting, use `email report <task_id>`. For multi-task or team-level reporting, use `email team-summary`; for SaaS team member breakdown, use `email team-breakdown`. Treat `reply_count` as email tracking replies, `replied_creator_count` as replied creators, and `inbound_message_count` as inbound reply messages. Team filters use SaaS team member `uid`, not Gmail or enterprise sender mailbox accounts. Do not recompute replies by manually scanning message threads unless the user explicitly asks for raw thread inspection.
- If the user wants in-platform DM/message, `message send` and `message schedule` require an existing `thread_id`. If the user only has an email task ID, use `message list --business_kind email_task --business_id <task_id>` to resolve the thread first. Without a thread, say that starting a new message thread is not exposed by the CLI and offer the email-task path for platform creators.
- For message-center filtering by task creator or team member, first run `message creator-filters`, then use returned `user_uid` values with `message list --creator_uids` or `message project-filters --creator_uids`.
- For message-center pending work, trust `needs_reply` / `last_message_direction`; `deal` is not the same as `unread`. If one opened task is already replied but SaaS still shows pending, inspect siblings with `message projects <thread_id>`. Use `message archive` only when the user explicitly wants the creator's entire conversation archived; it includes sibling task threads and is separate from `crm archive`. If only one task needs no reply, do not send an empty reply or archive the conversation; task-level mark-handled is not exposed yet.
- Message draft/history attachments and message-template attachments are separate. Use `message attachments list/upload/download/delete` for thread files and `message templates attachments list/upload/download/delete` for reusable template files. Never reuse IDs across the two paths. One template supports at most 2 private attachments, max 10MB each.
- Use `file image upload` for public inline images in approved email/message `html_body`. The returned `file_url` is public and is not a private email, message, or template attachment.
- `crm add-to-email` is only for adding existing NoxInfluencer CRM channels to an existing email task. Do not treat CRM as required when the user already has creator IDs or explicit email addresses.

## Affiliate Marketing

- Use `affiliation` for Shopify affiliate stores, campaigns, members, tracking links, discount codes, and performance reads. This is separate from normal `short-link`.
- Start with `affiliation stores list`. If no store is authorized or access is denied, ask the user to authorize/manage the store in SaaS; do not attempt store authorization in the Skill.
- Add NoxInfluencer creators to affiliate campaigns with search/profile `creator_id`, or use `platform + channel_id` / `custom_id` when the CLI schema calls for it.
- For owned creator links, download `affiliation members import-template` and submit `.xls` or `.xlsx` with `affiliation members import-file <campaign_id>`; max file size is 10MB.
- Executing affiliation member import writes members immediately and reads back the pending-member count; it is not validation-only.
- `affiliation campaigns export` downloads campaign-performance Excel directly to `--output`; it is not a shared async export task.

## Deduplication and Collaborators

- For a new creator search, apply `exclude_keywords` and the selected `search-filter-options` patch in the search itself. Use standalone `creator search-filter` only for an existing page. Mark or unmark a creator as Not interested only with explicit approval through `creator not-interested add/remove`.
- Email recipient deduplication is task-scoped: use `email recipients filter options` to find SaaS-aligned choices, `email recipients filter get <task_id>` to inspect saved state/counts, and `email recipients filter update <task_id> --body-file` to change it.
- Email collaborators use SaaS team `user_uid`. If the user does not know the ID, run `email collaborators list` without `task_id` first; with a `task_id`, it reads that task's current collaborator permissions. Use `add` or `remove` for incremental changes; use `replace` only when the user intends to reset the whole collaborator set.

## CRM Update Semantics

- `crm update` / `crm batch-update` may auto-create a NoxInfluencer CRM channel for valid platform `creator_id` tokens when updating cooperation status or labels. For label-only updates, the service uses the default cooperation status before applying labels.
- Use `crm labels create` when the user needs a new CRM tag ID. Use the returned `label_id` in `crm batch-update` with `labels.operation=add` or `remove`.
- Owner-only or archive-only updates do not auto-create CRM channels. Treat missing-channel failures as real failures, not successful skips.
- For batch previews and applies, report `existing_count`, `will_create_count`, and `created_count` when present; do not infer success only from requested IDs.

## Collection Add and Import

- Use `creator lookalikes` when the user asks for similar creators based on a source creator or URL. It is read-only and requires `target_platform`; save returned creator IDs with `collection add-creators` only after the user chooses targets.
- Use `collection add-creators` when the user wants to save creators returned by `creator search` or creator read commands into one or more collections. The JSON body uses `collection_ids`, `platform`, and `creator_ids`. Use `channel_ids` only when the user already has raw same-platform channel IDs. It is an add-only path, not forced collection-to-collection copy.
- Download `collection import-template` before using `collection import-file <collection_id> --file <path>` for the user's owned creator links. The spreadsheet's first column should be the YouTube, Instagram, or TikTok creator URL; an optional second column may contain email/contact data. This import is accepted asynchronously, so poll `collection items <collection_id>` by platform to confirm resolved rows.
- Do not confuse these paths with collection copy/move. `add-creators` adds explicit creators to target collections; `import-file` imports owned creator URLs into one collection.

## Spreadsheet Imports and Reports

- Always download the current SaaS `import-template` when the command family provides one. Do not infer columns from old files.
- Monitor task imports accept `.xls`/`.xlsx` up to 10MB, parse up to 1,000 rows, and save at most 500 valid rows per request. Preserve validation- and save-stage `failed_items`; use `monitor import-report` for a direct failure workbook.
- Monitor auto-track imports accept up to 50 creator homepage links and are all-or-nothing. If any row fails, no rule is created; fix `data.failed_items` and retry the complete workbook.
- CRM imports accept `.xls`/`.xlsx` up to 10MB and 500 rows. Executing the check writes valid nonduplicate rows. Use `--overwrite-existing` only after approval; upstream reports repeated-row overwrite as submitted without row-level results. Preserve `failed_items` and `repeated_items` for `crm import-report` workbooks.
- Email recipient imports accept `.xls`/`.xlsx` up to 8MB, target one existing `task_id`, and are available only before its active send flow.
- Affiliation member imports accept `.xls`/`.xlsx` up to 10MB and target one existing affiliate `campaign_id`.
- `monitor import-report`, monitor reports, short-link reports, affiliation campaign reports, and CRM import reports write Excel directly to `--output`. They do not return an `export_id`.

## File Roles

- Public rich-text images: `file image upload` returns `file_url` for approved `html_body`.
- Public product images: `product image upload` returns `file_url` for `thumbnail_url`; `campaign product-images upload` returns URLs for up to 5 entries in one product's `thumbnail_urls`.
- Private files: email, message draft/history, message-template, and owned feedback attachments require their domain-specific authorized download commands.
- Downloads use `--output`; add `--overwrite` only when replacing an existing local file is intentional.

## Mutation Rules

- Write commands default to dry-run. Treat dry-run output as a preview, not completion.
- Use `--force` only after the user has approved the exact object and action.
- Feedback submission is also a write command, but it is free and does not consume Skill quota. Use it for product bugs, confusing behavior, data issues, suggestions, or feature requests. Attach screenshots/logs with `--file` when useful, and check `feedback inbox` for asynchronous follow-up.
- Creator disputes are separate from product feedback: they require paid membership, consume no Skill Credit, and require concrete evidence. Check existing `dispute records` before an approved `dispute report`; use `dispute options` for current type/status values.
- For staged workflows, always run `validate` before `preview`, and `preview` before `apply --force`.
- For `send` and `schedule`, confirm the task/thread, recipient scope, sender identity, scheduled time when relevant, and content approval before execution.
- Do not draft outreach or negotiation copy. If content is missing, ask the user for approved content or hand off to a writing task without invoking NoxInfluencer write commands.
- Do not operate external CRM, email, messaging, or spreadsheet platforms. These commands only affect NoxInfluencer-owned objects.

## JSON-First Commands

Many marketing-ops commands intentionally keep complex selectors in JSON bodies. When a schema requires `--body-file`:

1. Run `noxinfluencer schema <cmd>` to inspect required fields and usage notes.
2. Prepare the minimal JSON body needed for the user's request.
3. Prefer the CLI's validate/preview stages when available.
4. Preserve stable opaque IDs from legitimate CLI responses (`campaign_id`, `collection_id`, `creator_id`, `thread_id`, `task_id`, `export_id`) for follow-up calls within the same supported workflow. This does not permit injecting a Campaign ID into a standalone mutation or treating a returned type value as a fixed task ID.

## Export Handling

- Shared export creation for creator, collection, CRM, and brand-monitor domains is async and returns `export_id`. Poll with `export get/list`, then use `export download <export_id> --output <path>` only when ready.
- Creator exports use 1-100 selected result `data.items[].id` values. Deep mode requires `field_keys`; preserve lookalike `data.export_context`; preview deep business quota before creation. Contact fields can consume contact quota.
- Monitor, short-link, affiliation, and import-report workbooks are direct downloads, not shared export tasks. Report the local output path and file metadata after completion.
