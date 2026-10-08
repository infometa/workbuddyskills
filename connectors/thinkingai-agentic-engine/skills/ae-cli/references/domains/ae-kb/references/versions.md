# Published knowledge-base versions

Versions are immutable successful publications. No historical version is created until the first successful compile. Failed or cancelled compiles do not consume a version number. Existing `+compile`, `+status` and `+list-sources` responses pass through server version labels and draft state; `+index`, `+grep`, `+read` and `+ask` always address current content.

When `+status` returns `wiki_review_required`, inspect `publicationReview.code`, report that administrator review is required, and stop ordinary compile polling. The active Run and write lock remain in place; do not cancel or force another compile. This also covers an interrupted publication after server restart.

Discover exact names/scopes via `kb +list`, then inspect history:

```bash
ae-cli kb +versions --name handbook --scope company --limit 100
ae-cli kb +version-show --name handbook --scope company --version 2
ae-cli kb +version-sources --name handbook --scope company --version 2 --source-type zip
ae-cli kb +version-diff --name handbook --scope company --from 1 --to 2
ae-cli kb +version-tree --name handbook --scope company --version 2 --id <historical-source-id>
ae-cli kb +version-read --name handbook --scope company --version 2 --id <historical-source-id> --path guides/start.md
ae-cli kb +version-download --name handbook --scope company --version 2 --id <historical-file-source-id> --output ./manual.pdf
```

- `--version`, `--from` and `--to` use integer version numbers, without a `v` prefix. `+version-sources` IDs come from that historical snapshot; never substitute current source metadata.
- `+versions`, `+version-sources` and `+version-tree` return one page. Use `--cursor` with the returned `nextCursor`, retaining the same target and filters. `--limit` is 1–200.
- `--scope personal|company` is exact. Omitting it keeps the existing personal-then-company lookup. A missing target in an explicit scope never falls back.
- `+version-tree/+version-read` accept ZIP or URL parent sources. Paths are source-relative and cannot contain absolute, parent or backslash segments. Text preview is bounded; supported PDF/images use a typed data URL. Unsupported or oversized files return metadata and `previewable: false`.
- `+version-download` accepts ordinary file sources only and creates a new local file with exclusive creation. It never overwrites an existing file. Directory sources return `KB_VERSION_DIRECTORY_DOWNLOAD_UNSUPPORTED`; the CLI does not reconstruct ZIPs or export an entire version.

## Rollback

Copy `latestVersionId` and an earlier target version from `+versions`. Explicitly explain the effects before requesting rollback: target-source edits and deletion intents are replaced; target-external sources with a previous successful publication are soft-deleted; target-external unpublished additions and their files remain unchanged.

```bash
ae-cli kb +rollback --name handbook --scope company --version 1 --expected-latest-version-id <latestVersionId> --request-id <stable-request-id> --dry-run
ae-cli kb +rollback --name handbook --scope company --version 1 --expected-latest-version-id <latestVersionId> --request-id <stable-request-id>
ae-cli kb +rollback-status --name handbook --scope company --operation-id <operationId>
```

`+rollback` is `high-risk-write`; use `--yes` only for an already authorized exact operation. A target must be strictly older than the current version. Success creates a new version (for example v3 → v1 produces v4), retaining all previous snapshots.

The caller must supply a stable ASCII `request-id` containing letters, digits, underscores or hyphens (1–191 characters). Reuse that exact ID, target and expected latest ID after a network interruption. The CLI does not generate another request ID, pick a different target, or retry a 409 automatically. A changed request under the same ID returns `KB_VERSION_OPERATION_REQUEST_CONFLICT`.

`queued/running` means accepted but not completed. Query `+rollback-status` using the returned `operationId`; only `status: success` with `resultVersionId` proves publication. `failed` is a terminal result; a later intentional attempt needs a new request ID. When `running` includes `KB_PUBLICATION_COMMIT_UNKNOWN`, `KB_PUBLICATION_ROLLBACK_INCOMPLETE`, or `KB_PUBLICATION_REVIEW_REQUIRED`, tell the user administrator review is required and writes remain blocked. Stop normal progress/polling; do not start another rollback. Status remains readable.

Transition status: transitional
Owning module: te-claude External Knowledge Base Versions API
Current transport: authenticated External REST via kbApi
Gateway target: TBD (published history and persistent rollback operations)
Review after: 2026-12-07
Exit condition: migrate when equivalent immutable-history and idempotent rollback Gateway capabilities exist; retain stable request IDs, exact-scope targeting and local file safety.
