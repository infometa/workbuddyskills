# Matelab MCP Workflows

## Authentication and errors

Connect to the configured Matelab Streamable HTTP endpoint. The client follows its `WWW-Authenticate` challenge and
protected-resource metadata to Matelab Identity for OAuth authorization. The Identity access token must include the
exact MCP endpoint as a resource audience and the `mcp` scope; other approved audiences/scopes may coexist. An ID token
or Matelab SDK Session is not an MCP bearer. Let the client manage credentials; do not put them or user identity in
tool arguments, hard-code authorization headers, or use legacy `/mcp/oauth/*` routes.

HTTP 401 or a tool error with `category: "authentication"` requires client authorization again. HTTP 503 indicates
temporary authentication-service unavailability. Follow normalized `category`, `message`, `retryable`, and optional
`code`/`details`, including `details.recovery`; do not branch on upstream PHP error prose or numeric codes. Retry a tool
only when it explicitly permits retry. An uncertain write must be followed by a fresh read before deciding what
remains, even if an earlier step succeeded. Successful initialization or tool discovery does not establish that a
business call can obtain the user's Matelab session. OAuth scope grants access to MCP; current resource capabilities
still determine business permissions.

## Typed-resource sequence

Use discovery only to choose a candidate, then fetch it:

```text
list_notebooks → notebook_ref → list_records or search_records → record_ref → fetch
record_ref → list_record_versions → current.ref or snapshots[].ref → fetch
notebook_ref → list_deleted_records → deleted_record_ref → restore_records
search_templates → template_ref → fetch
search_template_market → offer_ref → acquire_template → template_ref → fetch
```

Resource refs identify a current resource but are not credentials. Never extract notebook titles, owner IDs, record
UIDs, template IDs, or PHP selectors from them. Pass refs only where the tool schema accepts that ref kind.

Notebook, current-record, template, and group resources pair a copy-ready outer `ref` with a `data` object containing
domain metadata. For example, a current record's title is `resource.data.title`; MCP capabilities and fingerprints
remain on `resource`. Never substitute `data.ref` or identity fields for the outer MCP ref.

Use `fetch(view="summary")` for compact identity/capabilities/fingerprint when no body or attachment download is
needed. Use `fetch(view="full")` to read current record content, obtain current attachment downloads, and inspect all
currently readable related-record summaries. It intentionally contains no edit descriptor. Historical version full fetches are
read-only and never issue attachment downloads. Use `prepare_record_edit` only immediately before changing a record.
Notebook fetch also returns `trash_count` when recycle-bin listing is permitted; use `list_deleted_records` only when
the deleted-record identities themselves are needed.

## Creating and updating notebooks

Notebook placement is immutable and must be explicit before `create_notebook`:

1. If the user explicitly asks for a personal notebook, omit `group_ref`.
2. If the user names a research group, fetch `matelab:self`, match that exact group in `resource.groups` among entries
   whose `data.notebook_creation_available` is true, and copy the entry's outer `ref` unchanged into `group_ref`.
3. If the user does not specify placement, fetch `matelab:self` and ask them to choose a personal notebook or one of
   the eligible groups. Do not call `create_notebook` until they answer, and never select the first group or imitate
   the web UI's preselection.

To change a notebook's title or summary, fetch it and require `update_notebook` in its capabilities. Call
`update_notebook` with at least one replacement; omitted fields are preserved and an empty summary clears it.
Notebook placement cannot be changed through this tool.

## Notebook and record discovery

1. Call `list_notebooks` with a title substring or `scopes` when possible. Follow `next_cursor` by copying it into
   `cursor` and omitting `query` and `scopes`; continuations retain the original filters and page size. Counts cover
   the complete matching snapshot. If its safety limit is exceeded, narrow the query/scopes and start again.
2. To browse records, pass the notebook `ref` to `list_records`. All scopes return `next_cursor`; copy it unchanged
   into `cursor` with the same notebook ref until it is null. Neither listing accepts caller-supplied page numbers.
   Both cursors expire after 30 minutes; restart without them after expiry or a visibility change. Use
   `search_records` when a public notebook exceeds the snapshot safety limit or when a useful UID/title/summary clue
   is already known. `truncated=false` does not mean the listing is complete while `next_cursor` remains non-null.
3. To locate likely records by UID, title, or summary, call `search_records`. Optional date, keyword, and content
   filters are available for owned/shared notebooks. `matched > shown` means lower-ranked matches were omitted; the
   search result is intentionally bounded and not pageable.
4. Pass a selected record `ref` to `fetch` for the full Markdown Agent View.

Owned, shared, and public transport differences are internal. Do not pass user IDs or manually build shared-notebook
selectors. Public records are read-only and expose no write capabilities.

## Versions, copies, trash, and relations

- History: require `list_record_versions` in current record capabilities. Active mutable state is always
  `current`; immutable history is always `snapshots`. Copy `current.ref` or a snapshot's outer `ref` unchanged into
  `fetch`. Current modification time is `current.modified_at` (RFC3339); historical metadata is under
  `snapshots[].data`, using its returned time representation. The complete compact snapshot list has no pagination;
  record content remains fetch-on-demand and historical attachment downloads are unavailable.
- Copy: choose a readable source and an owned/shared target whose capabilities include both `create_record` and
  `update_record`. `copy_record` resolves PHP IDs, generates the new UID, and rejects cross-server copies.
- Trash: require `list_deleted_records` on the notebook. Start at `page=1`; while `has_more` is true, increment
  `page` with the same notebook and `page_size` until the intended records are found or all pages are exhausted.
  Pass 1–25 refs from one notebook to `restore_records`. Returned deleted refs are not fetchable. There is no
  permanent-delete, `del_forever`, or empty-trash tool.
- Relations: full fetch returns every currently resolvable, readable, same-server related record ref and explicitly counts
  entries omitted because they cannot be safely reconstructed or read.
  `update_record_relations` changes one target per call, rechecks source write and target read access, and rejects
  cross-server relations. Public record refs from discovery/fetch can be targets, but relation results cannot recover
  the outer public ref, so omitted public targets must be rediscovered. Refetch after success; do not describe several
  calls as one atomic batch.

## Structured field extraction

Use `extract_record_fields` only when comparing known schema fields across an owned/shared notebook:

1. Find and fetch the relevant template.
2. Select 1–24 entries from `resource.query_fields`.
3. Copy each `field_ref` unchanged and assign a compact unique alias such as `mass`.
4. Call `extract_record_fields` with one notebook ref and optional date/keyword filters.

The template supplies field paths; it does not filter records by template ID. The tool does not support field-value
predicates, sorting, public notebooks, or pagination. A returned field can be `null`, and a truncated result is not
an exhaustive collection. Query-field refs expire after 24 hours; fetch the template again instead of reconstructing
an expired ref.

## Creating records

For one blank record, call `create_records` with one record containing a title and optional summary; omit
`template_ref`, keep values and keywords empty.

For structured records:

1. Fetch a template whose capabilities include `use_template`; inspect `import_limitations`.
2. Copy `schema_fingerprint`.
3. Build each `records[].values` only from `fillable_schema` using human module/field names. Omitted code modules keep
   their template defaults.
4. Prepare and PUT any new files before placing their `attachment_ref` in file positions.
5. Call `create_records` with 1–100 records, the template ref, and fingerprint. If any value contains a staged
   attachment, the call must contain exactly one record; use each attachment ref in only one file position.

Store/default templates may require `copy_template` followed by a fresh fetch before they can create records.
Template-backed import cannot set record summary upstream.
The successful response contains the target `notebook_ref` once and only `ref/title` for each created record; fetch a
record ref when content or current capabilities are needed.

## Updating records

1. Fetch the record only when its current readable content must be reviewed; confirm `update_record` is in capabilities.
2. Call `prepare_record_edit(record_ref)` immediately before the mutation.
3. Copy its current `content_fingerprint`.
4. Use `edit.set_values_schema`, `edit.tables`, and `edit.file_targets`; never invent paths.
5. Call `update_record` with one or more of:
   - `set_values`: scalar form fields and richtext/code module values. Richtext values are Markdown; raw HTML is
     literal text, and staged attachment refs cannot be embedded.
   - `set_cells`: values in existing zero-based table rows.
   - `append_rows`: new rows by human table/column names.
   - `append_files`: new files for listed files modules.
   - `remove_files` / `replace_files`: occurrence refs from `prepare_record_edit.attachments`, only when the occurrence advertises
     that capability.
6. Inspect the response `persistence` before doing anything else:
   - `persisted`: the database was updated; fetch again only when the new readable content is needed, and prepare again
     before another mutation because the prior fingerprint and attachment occurrence refs are stale.
   - `pending_user_save`: the accepted change remains pending in Matelab's browser draft. Ask the user to save it in
     the Matelab web UI, do not refetch yet, and never repeat the operation. Refetch after the user confirms saving.
   - `unconfirmed`: refetch and verify the intended result; do not blindly repeat non-idempotent changes.

A mutation can perform several sequential writes. A failure or pending browser save may stop later steps after
earlier changes were accepted. Follow the recovery message, complete any required browser save, then refetch and
prepare only the remaining changes. Never replay the whole request. For file targets and upload limits, read
[Attachment workflows](attachment-workflows.md).

Use `change_record_structure` for adding/removing modules, form fields, table columns, or current rows. Copy exact
names from `prepare_record_edit.edit.modules` and zero-based row indices from `edit.tables`; prepare again before a
later structural mutation. New richtext modules also take Markdown. New JSON/ECharts code modules default omitted
or null content to an empty string; explicit code strings are preserved.

Use `delete_record` only when the user wants the record moved to the recycle bin. Require that capability and copy
`content_fingerprint` from a fresh `fetch` (`summary` is sufficient). Encrypted records have no editable plaintext or
`update_record` capability, but may still allow deletion with this fingerprint; do not require `prepare_record_edit`
for deletion. The operation does not permanently erase the record or clear the bin.

## Common failures

- Reconstructing a ref from a title, UID, ID, or filename.
- Calling `create_notebook` before the user chooses personal or group placement, or treating the first visible group
  as a default.
- Writing with a fingerprint from an earlier successful mutation.
- Treating `list_records` or `extract_record_fields` as full record content.
- Treating `search_records.matched > shown` as a continuation, inventing a page number for either listing, or
  repeating notebook filters with a cursor; follow the returned `next_cursor` contract.
- Passing a marketplace offer ref to `fetch`; acquire it first.
- Passing a deleted-record ref to `fetch`, or a version ref to a mutation tool.
- Treating multiple relation calls as one atomic server operation.
- Using store/default templates for record creation without checking `use_template`.
- Sending Provider paths, hashes, canonical JSON, local paths, or base64.
