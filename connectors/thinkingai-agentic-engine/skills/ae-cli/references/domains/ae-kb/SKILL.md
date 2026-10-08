---
name: ae-kb
version: 1.0.0
description: 'AE/TE knowledge base CLI manual for creating, importing read-only compiled snapshots, querying, LLM-powered ask, listing accessible knowledge bases and their sources, deterministic index/grep/read retrieval, checking status, ZIP source upload and directory management, raw child-file reading, revision-checked child updates and deletion, compiling, schema generation, URL sources, source deletion, and knowledge base deletion. Use when the user asks to manage TE/AE/ThinkingEngine knowledge bases, import a compiled Markdown ZIP snapshot, upload documents or URLs to a knowledge base, query knowledge, ask knowledge bases with an LLM, list accessible knowledge bases or source metadata, inspect knowledge base indexes, search knowledge base pages, read a specific knowledge base page, check knowledge base status, generate schemas, compile knowledge, remove sources, or delete a knowledge base. To choose which knowledge base is worth searching, use the ae-kb-discovery skill first; this skill runs the retrieval once a target is chosen. Must use ae-cli kb commands and must not guess knowledge base names, scopes, page paths, source IDs, source display names, JSON payload shapes, or URL formats.'
---

# ae-kb

AE CLI (`ae-cli`) knowledge base commands are invoked through:

```bash
ae-cli kb +<command> [options]
```

## Global Rules

- Use this skill for TE/AE knowledge base tasks: create, import a compiled snapshot, query, ask with LLM, list accessible knowledge bases and their sources, inspect indexes, grep pages, read pages, check status, upload sources, add URL sources, generate schema, compile, remove source files, and delete knowledge bases.
- **Searching a knowledge base for an answer is the most common task. If that is what you are doing, go straight to [Explore Knowledge Base Pages](#explore-knowledge-base-pages) and read [`references/query-workflow.md`](references/query-workflow.md) first — it is the retrieval procedure. The other commands below are for managing knowledge bases, not answering from them.**
- Read operations can run directly after required inputs are known. Write operations require explicit user intent and normally keep the confirmation prompt unless the user asks to bypass it.
- Prefer `--dry-run` before destructive or broad writes when the user has not already validated the target.
- Do not invent knowledge base names, scopes, source IDs, source display names, or JSON payloads. Ask the user or query known context when values are missing.
- When building a `--sources` ref (or `+read --source`), copy the exact `scope` and `name` from `+list` output — run `ae-cli kb +list` first when the scope of a named knowledge base is unknown.
- JSON flags must be valid JSON strings, usually wrapped in single quotes in shell commands.
- Successful commands return JSON by default. Use `--format table` only when a table is easier for a human to scan. Envelope may include optional `_notice.host_compat`.
- `--host <url>` overrides the active AE host. It is available on every command and may be placed after the subcommand, e.g. `ae-cli kb +<command> --host <url>`.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.
- Retrieval (`+index` / `+grep` / `+read`) is deterministic and server-side LLM-free; use it for simple factual lookups. Use `+ask` when the question requires synthesizing across multiple pages or multi-hop reasoning.

## Commands

| Command | Risk | Purpose |
|---|---:|---|
| `+ask` | read | LLM-powered Q&A over knowledge bases; for multi-page synthesis or multi-hop questions. |
| `+ask-status` | read | Query the current status of an ask execution by `--execution-id` without polling. |
| `+list` | read | List accessible knowledge bases filtered by buildStatus (default: compiled). |
| `+list-sources` | read | List source metadata for one knowledge base so exact source identifiers can be discovered safely. |
| `+index` | read | List accessible knowledge bases and their `index.md` navigation maps. |
| `+grep` | read | Keyword-search knowledge base pages; returns a page-level results array (hitCount / pageKind / sections previews). |
| `+read` | read | Read a full knowledge base page, a line window, or (with `--outline`) only the page heading tree. |
| `+new` | write | Create a new personal or company knowledge base. |
| `+import` | write | Import a compiled Markdown ZIP as a personal or company read-only snapshot; `--scope` defaults to `personal`. |
| `+import-status` | read | Query one snapshot import task by `--request-id` without polling; output includes the persisted `scope`. |
| `+add` | write | Upload local files (including ZIP directory sources), a non-recursive directory, or HTTP(S) pages converted to markdown. |
| `+url` | write | Upload a URL source directly with optional display name and parsing instruction. |
| `+schema` | write | Generate the compile schema for a knowledge base. |
| `+compile` | write | Compile a knowledge base in incremental or full mode. |
| `+status` | read | Query the current status of a knowledge base. |
| `+rm-source` | high-risk-write | Delete one source from a knowledge base by stable ID; exact display name is legacy compatibility only. |
| `+remove` | write | Delete an entire knowledge base. |

## Published Version History

Use the nine version commands described in [`references/versions.md`](references/versions.md) to inspect immutable published history, compare source changes, and explicitly roll back an earlier version as a new publication. These commands manage history; `+index/+grep/+read/+ask` continue to use current published content.

| Command | Risk | Purpose |
| --- | --- | --- |
| `+versions` | read | List published versions and latestVersionId. |
| `+version-show` | read | Show one version summary. |
| `+version-sources` | read | Discover historical source IDs. |
| `+version-diff` | read | Compare two versions. |
| `+version-tree` | read | List a historical ZIP/URL source directory. |
| `+version-read` | read | Preview a historical directory child file. |
| `+version-download` | read | Save one ordinary historical file source; no directory download. |
| `+rollback` | high-risk-write | Restore an earlier version and create a new version. |
| `+rollback-status` | read | Query a persisted rollback Operation without polling. |

## ZIP Directory Sources

Use `+add --files '["./sources.zip"]'` to upload one ZIP as one editable parent source, preserving its internal hierarchy. Archive validation and limits are enforced by the server. This is different from `+import`, which creates a read-only compiled snapshot. Passing a local directory to `+add` still uploads only its immediate supported files; it does not recursively package that directory.

Discover the exact parent ID with `+list-sources`. ZIP rows include `fileCount`, `sizeBytes`, `contentRevision`, and `updateStatus`.

| Command | Risk | Purpose |
| --- | --- | --- |
| `+source-ls` | read | List one directory page with revision, current children and deleted paths relative to the successful baseline. |
| `+source-read` | read | Read a child source file as UTF-8/base64, or save original bytes. |
| `+source-put` | write | Add one local file or explicitly replace the exact ZIP-relative path. |
| `+source-rm` | high-risk-write | Delete one child file or recursively delete a child directory. |

```bash
ae-cli kb +source-ls --name handbook --id <source-id> --path "" --limit 100
ae-cli kb +source-ls --name handbook --id <source-id> --path "guides" --cursor <nextCursor>
ae-cli kb +source-read --name handbook --id <source-id> --path "guides/intro.md"
ae-cli kb +source-read --name handbook --id <source-id> --path "images/chart.png" --output ./chart.png
ae-cli kb +source-read --name handbook --id <source-id> --path "images/chart.png" --encoding base64
ae-cli kb +source-put --name handbook --id <source-id> --path "guides/new.md" --file ./new.md --action add --expected-revision 7 --dry-run
ae-cli kb +source-put --name handbook --id <source-id> --path "guides/new.md" --file ./new.md --action add --expected-revision 7
ae-cli kb +source-put --name handbook --id <source-id> --path "guides/new.md" --file ./revised.md --action replace --expected-revision 8
ae-cli kb +source-rm --name handbook --id <source-id> --path "guides/new.md" --expected-revision 9
ae-cli kb +source-rm --name handbook --id <source-id> --path "guides/obsolete" --recursive --expected-revision 10
ae-cli kb +compile --name handbook --mode incremental
```

- Copy the source ID, paths and revision from current discovery. Names resolve personal then company, following the existing External API; no scope override is available on these commands.
- `--path` is relative to the ZIP root, not a local filesystem or `raw/zip/...` path. Root listing uses an empty path. Nonempty paths cannot be absolute or contain empty, dot, parent or backslash segments.
- Listing returns one page; continue using `nextCursor` and the same path. On a revision change, restart discovery before writing.
- `+source-read` reads source bytes; `+read` reads compiled Wiki pages. Default UTF-8 output fails on invalid UTF-8. Base64 preserves binary data. `--output` creates a new local file and refuses to overwrite an existing file.
- `+source-put` accepts one file up to 50 MB. Default `--action add` rejects an existing path; `--action replace` explicitly authorizes overwriting an existing child. There is no silent upsert. Dry-run shows metadata and redacts file content.
- `--expected-revision` is mandatory for writes. A 409 conflict is returned with its server error code; the command never refreshes and retries the write automatically.
- `+source-rm` keeps the parent source. Nonempty directory removal requires `--recursive`; deletion follows the CLI confirmation gate. Use `--yes` only when automated deletion of the exact target is already authorized. `+rm-source --id` deletes the entire parent.
- A mutation marks the parent changed but does not start compilation or regenerate Schema. Run incremental compilation explicitly; wait for successful publication before the next test stage.
- `+status` is the existing aggregate status query; it is not a per-run event or ZIP Diff reader. Do not interpret its compilation submission response as successful publication.
- No Gateway equivalent is registered in the current KB implementation. These commands reuse the typed External source APIs.

Transition status: transitional
Owning module: te-claude External Knowledge Base Sources API
Current transport: authenticated External REST via `kbApi` and multipart `kbUpload`.
Gateway target: TBD (ZIP source directory and raw-file capabilities)
Review after: 2026-12-06
Exit condition: migrate when equivalent typed Gateway file, directory and revision-aware mutation capabilities exist; retain CLI file handling and explicit mutation semantics.

## Common Workflows

### Create a Knowledge Base

Use `+new` with name. `--scope` is optional and defaults to `company`; valid scopes are `personal` and `company`.

```bash
ae-cli kb +new \
  --scope company \
  --name engineering-handbook \
  --description "Engineering handbook" \
  --tags '["engineering","handbook"]'
```

Optional fields:

- `--scope`: scope, defaults to `company`.
- `--description`: description, up to 200 characters.
- `--tags`: JSON array, max 2 tags, each up to 15 characters.
- `--project-id`: optional project ID to bind.
- `--project-name`: optional project display name.

### Import a Compiled Snapshot

Use `+import` only for a ZIP whose root contains `index.md` and at least one
`wiki/**/*.md` page. The server validates all archive paths, limits, UTF-8 text, and Wiki links.

```bash
ae-cli kb +import \
  --file ./knowledge-base.zip \
  --name "Imported handbook" \
  --description "Compiled documentation snapshot" \
  --tags '["docs","handbook"]'

# The submission returns requestId + queued. Query one snapshot later:
ae-cli kb +import-status --request-id <requestId>
```

- The result is always a `personal` read-only snapshot; there is no `--scope`, `--force`, or replace option.
- Imported snapshots support list, Index/Wiki reading, grep/read, Ask, and deletion. They do not expose source, Schema, usage, compile, member, settings, ownership-transfer, or company-publish operations.
- The ZIP is limited to 50 MB and supports Markdown text only. Local images, attachments, other binaries, broken Wiki links, and ambiguous Wiki links are rejected by the server.
- Submission returns `{requestId, status: "queued"}` immediately. It does not wait for ZIP validation or publication.
- `+import-status` returns one of `queued`, `running`, `succeeded`, or `failed`; success includes `knowledgeBaseId`, and failure includes a stable error code/message.
- If a `requestId` was returned, query it before retrying. If no request ID was received, run `ae-cli kb +list` before retrying the same name. A repeated same-name import is rejected.

- Transition status: transitional
- Owning module: te-claude External Knowledge Base Import API
- Current transport: authenticated KB external REST through `kbUpload` for submission and `kbApi` for status lookup.
- Gateway target: TBD (`kb.snapshot.import` proposed)
- Review after: 2026-12-01
- Exit condition: migrate to a typed Gateway capability when the equivalent multipart import capability is available, or remove this command if dynamic Gateway execution provides the same file-handling and output contract.

### Upload Files or Directories

Use `+add` when sources are local files, local directories, or pages that should be fetched and converted to markdown before upload.

```bash
ae-cli kb +add \
  --name engineering-handbook \
  --scope company \
  --files '["./README.md","./docs","https://example.com/guide"]'
```

Input rules:

- `--files` must be a JSON array of strings.
- Local directory reading is non-recursive.
- URL entries must start with `http://` or `https://`.
- Supported extensions include markdown/text, office documents, PDFs, spreadsheets, presentations, and common images. Local files are uploaded as multipart file blobs; HTTP(S) pages are fetched and converted to markdown before upload.
- Duplicate filenames are automatically suffixed as `name-1.ext`, `name-2.ext`, etc.

### Add a URL Source

Use `+url` when adding one URL source and optionally passing a display name or parsing instruction.

```bash
ae-cli kb +url \
  --name engineering-handbook \
  --scope company \
  --url https://example.com/guide \
  --display-name guide \
  --parse-instruction "Keep headings and code blocks"
```

`--url` must be `http(s)`. The server detects the platform from the URL automatically: URLs on a `*.feishu.cn` or `*.larksuite.com` subdomain are parsed with the Feishu pipeline (including sub-documents, using the server's own Feishu parsing instruction — `--parse-instruction` is ignored for them); all other URLs are fetched as regular web pages.

### Generate Schema and Compile

Generate the schema first when the knowledge base needs a compile schema.

```bash
ae-cli kb +schema --name engineering-handbook --scope company
```

Use `--force` only when `+status` reports `schema_generating` and the user explicitly wants to replace the current generation attempt. The replacement may consume additional tokens.

Schema and Compile accept the same optional model reference. Prefer the model record `id` returned by `ae-cli agent +list-models` (`Model.id`). Historical `modelId` and the unambiguous `modelId::scope` form remain compatible. A model `displayName` is presentation text, not a stable reference.

To add one-time guidance for this generation without changing stored knowledge base metadata, pass `--custom-instructions`. The server trims the value, treats whitespace-only input as absent, and accepts up to 10,000 Unicode characters. Do not include secrets or credentials.

```bash
ae-cli kb +schema \
  --name engineering-handbook \
  --scope company \
  --model <model-ref> \
  --custom-instructions "Prioritize troubleshooting workflows and preserve command examples"
```

Use `--dry-run` to inspect the request body before sending it. While generation is running, a request without `--force` is idempotent only when it supplies no new model or effective custom instructions; otherwise it fails with `KB_SCHEMA_GENERATION_IN_PROGRESS`. With `--force`, the selected model and custom instructions apply to the replacement attempt. Invalid text fails with `KB_SCHEMA_CUSTOM_INSTRUCTIONS_INVALID`.

Compile after sources and schema are ready:

```bash
ae-cli kb +compile --name engineering-handbook --scope company --mode incremental --model <model-ref>
```

Valid compile modes are `incremental` and `full`; default is `incremental`.

### Check Knowledge Base Status

Use `+status` to inspect the current status of a knowledge base.

```bash
ae-cli kb +status --name engineering-handbook --scope company
```

### Ask Knowledge (LLM)

Use `+ask` when the question requires synthesizing across multiple pages or multi-hop reasoning — a server-side agent runs the full retrieval loop and returns a synthesized answer with its source paths. Prefer `+index` -> `+grep` -> `+read` when deterministic retrieval is enough.

The `+ask` command uses asynchronous submit/poll: by default, it automatically polls for completion (every 5s, up to 10 minutes) and prints the final answer with its execution ID, sources, model usage, tool call count, and model ID.

```bash
# Default: submit and poll for completion
ae-cli kb +ask \
  --question "How do we troubleshoot payment alerts?" \
  --sources '[{"scope":"company","name":"engineering-handbook"}]' \
  --model-id claude-sonnet-4-6 \
  --locale zh

# Submit only, return executionId immediately (for batch processing)
ae-cli kb +ask --question "..." --no-wait

# Query execution status later
ae-cli kb +ask-status --execution-id <id>
```

- `--question`, alias `-q`: required natural-language question (1-2000 characters).
- `--sources`: optional JSON array of knowledge base refs. Omit to search all accessible knowledge bases.
- `--model-id`: optional LLM model ID. Omit to use the platform default.
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.
- `--no-wait`: optional boolean flag. Return immediately after submission with `{executionId, status}`, without polling.
- **Failure handling**: If execution fails, the command exits non-zero and prints the unified JSON error envelope on stderr: `{"ok":false,"error":{"type":"api","code":"<server-code>","message":"..."}}`. Stable server codes are `model_unavailable`, `sandbox_unavailable`, `agent_skill_unavailable`, `dispatch_auth_unavailable`, `provider_failed`, `retrieval_error`, `timeout`, and `process_restart`.

### List Accessible Knowledge Bases

Use `+list` when you only need accessible knowledge base metadata without loading `index.md` navigation maps. Omit `--build-status` to default to `compiled`; pass `idle` / `pending` / `compiling` / `compiled` / `failed` to filter by a specific status (system knowledge bases are always listed regardless of status):

```bash
ae-cli kb +list
ae-cli kb +list --locale zh
ae-cli kb +list --build-status compiled
```

### Explore Knowledge Base Pages

Use the deterministic retrieval primitives when an agent needs to explore knowledge base content like a code repository. These endpoints do not call an LLM on the server side.

**Before running a real query, read [`references/query-workflow.md`](references/query-workflow.md)** — it is the step-by-step procedure for turning a question into an answer without crawling. It covers candidate indexing, copied-path grep, same-page read windows, linked-page re-grep, outline-derived ranges, and coverage assessment. This section below is the per-command reference the workflow draws on.

Start with `+list` or `+index` to discover accessible knowledge bases. Use `+index` when you also need navigation maps:

```bash
ae-cli kb +list
```

```bash
ae-cli kb +index \
  --sources '[{"scope":"company","name":"engineering-handbook"}]'
```

Then use `+grep` to locate likely pages:

```bash
ae-cli kb +grep \
  --query "sandbox configuration" \
  --sources '[{"scope":"company","name":"engineering-handbook"}]' \
  --paths '["wiki/sandbox.md"]' \
  --top-k 10
```

The response is a page-level `results` array: each entry is one page with its full `hitCount`, a `pageKind` (`content` or `catalog`), up to 4 `sections` previews (breadcrumb, `sectionStartLine`/`sectionEndLine`, text preview), and `moreSections`. Use `hitCount` and the previews to decide which pages to read; `pageKind: "catalog"` marks a module directory page — treat its entries as detail-page navigation, not as an answer source. Read the section range with `--offset sectionStartLine` / `--limit sectionEndLine - sectionStartLine + 1`; when `moreSections > 0` and the answer is not in the previews, re-grep that single page to see all its hits.

Use `+read --outline` when the current target page has no reliable grep range and headings are needed to choose a section:

```bash
ae-cli kb +read \
  --source '{"scope":"company","name":"engineering-handbook"}' \
  --path "wiki/sandbox.md" \
  --outline
```

Then use `+read` to open the selected window, using a page-group section boundary or two adjacent outline headings:

```bash
ae-cli kb +read \
  --source '{"scope":"company","name":"engineering-handbook"}' \
  --path "wiki/sandbox.md" \
  --offset 42 \
  --limit 60 \
  --expand block
```

### List Sources

List sources first to discover the stable identifier for the intended source:

```bash
ae-cli kb +list-sources --name engineering-handbook --scope company
```

Copy the exact `id` from the response into `+rm-source`. Do not guess a source ID from a local filename, URL, display name, or an older upload response.

- Transition status: transitional
- Owning module: te-claude External Knowledge Base Sources API
- Current transport: authenticated KB external REST through `kbApi`.
- Gateway target: TBD (`kb.source.list` proposed)
- Review after: 2026-12-03
- Exit condition: migrate to a typed Gateway capability when an equivalent source-list capability is available, or remove this command if dynamic Gateway execution provides the same discoverability and safe output contract.

### Remove One Source

Use `+rm-source --id` with the exact ID returned by the current `+list-sources` response. This is a `high-risk-write`; keep the interactive confirmation unless the user has explicitly authorized `--yes`.

```bash
ae-cli kb +rm-source \
  --name engineering-handbook \
  --scope company \
  --id cm-source-id
```

`--display-name` is retained for legacy compatibility only when a stable source ID is unavailable:

```bash
ae-cli kb +rm-source \
  --name engineering-handbook \
  --display-name kb-1780046712-guide.md
```

If the user only gives a loose source name, do not guess a source ID. Run `+list-sources`, identify the intended row from returned metadata, and ask only when multiple rows remain ambiguous.

### Delete a Knowledge Base

Use `+remove` for deleting the entire knowledge base. Confirm the target name with the user if there is any ambiguity.

```bash
ae-cli kb +remove --name engineering-handbook --scope company
```

## Command Reference

### `+ask`

```bash
ae-cli kb +ask --question "<question>" [--sources '[{"scope":"company","name":"kb-name"}]'] [--model-id claude-sonnet-4-6] [--locale zh|en|ja|ko] [--no-wait]
```

- `--question`, alias `-q`: required natural-language question (1-2000 characters).
- `--sources`: optional JSON array of knowledge base refs. Omit to search all accessible knowledge bases.
- `--model-id`: optional LLM model ID. Omit to use the platform default.
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.
- `--no-wait`: optional. Return immediately with `{executionId, status}` instead of polling.
- When to use: multi-page synthesis or multi-hop questions. For simple factual lookups, prefer `+index` / `+grep` / `+read`.
- Output: By default, polls and returns `{executionId, answer, sources, modelUsage, toolCallCount, modelId}`. With `--no-wait`, returns `{executionId, status}` immediately. On failure, exits non-zero with the unified stderr envelope containing `error.type="api"`, the server `error.code` (`model_unavailable`, `sandbox_unavailable`, `agent_skill_unavailable`, `dispatch_auth_unavailable`, `provider_failed`, `retrieval_error`, `timeout`, or `process_restart`), and `error.message`.

### `+ask-status`

```bash
ae-cli kb +ask-status --execution-id <id>
```

- `--execution-id`: required. The execution ID returned by `+ask` submission.
- Output: Returns one successful CLI envelope snapshot. For a failed execution, the stable server code remains at `data.error.code`: `{"ok":true,"data":{"executionId":"...","status":"failed","error":{"code":"retrieval_error","message":"..."}}}`. Does not poll.

### `+list`

```bash
ae-cli kb +list [--build-status compiled] [--locale zh|en|ja|ko]
```

- `--build-status`: optional; one of `idle` / `pending` / `compiling` / `compiled` / `failed`. Omit to default to `compiled` (system knowledge bases are always listed regardless of status).
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.
- Response items include `buildStatus`.

### `+index`

```bash
ae-cli kb +index [--sources '[{"scope":"company","name":"kb-name"}]'] [--locale zh|en|ja|ko]
```

- `--sources`: optional JSON array of knowledge base refs. Omit to list all accessible knowledge bases.
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.

### `+grep`

```bash
ae-cli kb +grep --query "<keywords>" --sources '[{"scope":"company","name":"kb-name"}]' --paths '["wiki/page.md"]' [--top-k 10] [--locale zh|en|ja|ko]
```

- `--query`, alias `-q`: required keywords to search.
- `--sources`: required JSON array of knowledge base refs.
- `--paths`: required JSON array of wiki pages or subdirectories **copied** from `+index`. A single page is still an array, e.g. `["wiki/sandbox.md"]`. Distinct from `+read --path` (one string).
- `--top-k`: optional max number of hits, 1-50, default 10.
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.
- Each page entry in results carries `hitCount` (full match count), `pageKind`, and `sections` previews with `sectionStartLine` / `sectionEndLine` — use the section range as the `+read` window.

### `+read`

```bash
ae-cli kb +read --source '{"scope":"company","name":"kb-name"}' --path "index.md" [--offset 1] [--limit 200] [--expand block|none] [--outline] [--locale zh|en|ja|ko]
```

- `--source`: required JSON object pointing to exactly one knowledge base.
- `--path`: required page path relative to the knowledge base root, such as `index.md` or `wiki/concepts/data-model.md`.
- `--offset`: optional 1-based integer start line.
- `--limit`: optional max line count, 1-2000.
- `--expand`: optional Markdown block expansion mode. `block` lets the server include a complete Markdown block outside the requested line window; `none` keeps the exact offset/limit window. Omit it to use the server default, `block`.
- `--outline`: optional. Return only the whole-page heading tree (`{level, heading, line}`) with empty content, independent of `--offset` / `--limit`. Use it on long pages to choose which section to read.
- `--locale`: optional locale: `zh`, `en`, `ja`, or `ko`.

### `+new`

```bash
ae-cli kb +new --name "<name>" [--scope personal|company] [--description "..."] [--tags '["t1","t2"]'] [--project-id "..."] [--project-name "..."]
```

### `+add`

```bash
ae-cli kb +add --name "<name>" --files '["./a.md","./docs","https://example.com/page"]' [--scope personal|company]
```

### `+import`

```bash
ae-cli kb +import --file "./knowledge-base.zip" --name "<name>" [--description "..."] [--tags '["t1","t2"]'] [--project-id "..."]
```

- `--file`: required local `.zip` file.
- `--name`: required personal knowledge-base name, up to 30 characters.
- `--description`: optional, up to 200 characters.
- `--tags`: optional JSON array, max 2 unique tags, each up to 15 characters.
- `--project-id`: optional project binding.
- Scope and terminal build state are generated by the server and cannot be supplied by the client.
- Output: `{requestId, status: "queued"}`. Use `+import-status`; the command does not poll.

### `+import-status`

```bash
ae-cli kb +import-status --request-id <requestId>
```

- `--request-id`: required ID returned by `+import`.
- Output: `{requestId, status, knowledgeBaseId?, errorCode?, errorMessage?}`.
- Returns a single snapshot and does not poll. A failed import is returned as `status: "failed"` with its stable error code/message; an unknown or inaccessible request exits non-zero.

### `+url`

```bash
ae-cli kb +url --name "<name>" --url "https://example.com/page" [--scope personal|company] [--display-name "..."] [--parse-instruction "..."]
```

### `+schema`

```bash
ae-cli kb +schema --name "<name>" [--scope personal|company] [--force] [--model <model-ref>] [--custom-instructions "<one-time guidance>"]
```

- `--custom-instructions`: Optional per-run schema-generation guidance. It is not persisted; whitespace-only input is omitted. The server allows at most 10,000 Unicode characters and rejects disallowed control characters. Do not include secrets or credentials.
- `--force`: Replace the current attempt only when schema generation is already running and the user explicitly requests the replacement. The selected model and custom instructions apply to the new attempt, which may consume additional tokens.
- `--dry-run`: Shows the same `customInstructions` request field that execution will send.
- `--model`: Optional stable model reference. Prefer `Model.id` from `ae-cli agent +list-models`; historical `modelId` and `modelId::scope` remain compatible.
- `--scope`: Optional exact knowledge-base scope. Omit it to retain the legacy personal-to-company lookup order.
- Errors: `KB_SCHEMA_CUSTOM_INSTRUCTIONS_INVALID` means the field failed validation. `KB_SCHEMA_GENERATION_IN_PROGRESS` means generation is active and a request without `--force` supplied a new model or effective custom instructions.

### `+compile`

```bash
ae-cli kb +compile --name "<name>" [--scope personal|company] [--mode incremental|full] [--model <model-ref>]
```

### `+status`

```bash
ae-cli kb +status --name "<name>" [--scope personal|company]
```

### `+list-sources`

```bash
ae-cli kb +list-sources --name "<name>" [--scope personal|company]
```

- `--name`: required knowledge base name.
- Output: `items` contains effective sources with stable `id`. `pendingDeletions` contains soft-deleted sources still included in the current successful version. `deletionMaintenance` is separate and may report already-published deletions awaiting cleanup. Paths, hashes, credentials, and source content are not returned.
- Check `deletionProjection.state` and its `baseline` before interpreting deletion lists. `ready` with `pendingDeletions: []` means no pending deletion at that baseline. `changing`, `review_required`, or `unavailable` with `pendingDeletions: null` means undetermined; display the `reasonCode`, never turn null into an empty list. Legacy libraries without a verifiable complete publication manifest return unavailable until a real version is published.
- A rollback creates a new current version. An older deletion receipt cannot override membership in that version. A later source deletion needs publication again.
- Copy the exact `id` from the current response before deleting a source; never guess it.

### `+rm-source`

```bash
ae-cli kb +rm-source --name "<name>" --id "<source-id>" [--scope personal|company]
```

- `--id`: preferred stable source identifier copied from `+list-sources`.
- `--display-name`: legacy compatibility selector used only when an ID is unavailable.
- If both are supplied, `--id` wins. The command removes one source only.

### `+remove`

```bash
ae-cli kb +remove --name "<name>" [--scope personal|company]
```
