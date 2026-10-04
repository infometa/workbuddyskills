# CLI Guidance

> Installation and quick start see [SKILL.md](../SKILL.md).

## Authentication and paid API

```bash
xparse-cli auth                                    # Standalone interactive menu
xparse-cli auth app-key                            # Interactive AppKey setup
xparse-cli auth device                             # Uses the shipped public client
xparse-cli auth browser                            # Uses the shipped public client
xparse-cli auth browser --prompt=consent
```

For non-interactive AppKey automation, set both environment variables:

```bash
export XPARSE_APP_ID=your_app_id
export XPARSE_SECRET_CODE=your_secret_code
```

| `--api` value | Behavior |
|---------------|----------|
| _(omitted)_ | Same as `auto` |
| `auto` | Query current quota, use the daily free allowance first, then an authenticated user's reported free-package allowance when available |
| `free` | Force the free endpoint only |
| `paid` | Explicitly use the paid API; pair with `--auth-method app-key` or `oauth` when both are configured |

AppKey priority: CLI flags → env vars → config file. Normal OAuth login uses
the shipped public client automatically; private deployments may override it
through a CLI flag, `XPARSE_OAUTH_CLIENT_ID`, or the config file.
Device OAuth and AppKey credentials represent different authentication paths.
The current quota service reports `free_package` only for an
AppKey-authenticated request; do not infer package access from Device OAuth.
Automatic package routing uses only `free_package.free_remain_count`; the
historical `free_count` field is display-only.
Login does not authorize an explicit paid parse. Only use `--api paid` after the
user has approved paid service behavior.

See [authentication.md](authentication.md) for all login modes and
[textin-key-setup.md](textin-key-setup.md) for legacy AppKey setup.

## API limits

| Dimension | Free/automatic route | Explicit paid route |
|-----------|----------------------|---------------------|
| File types | PDF and supported images | Office, HTML, OFD, RTF, PDF, images, and other service-supported types |
| Request limits | Read current page and MB limits from `xparse-cli quota --output json`; reduce the file or use an explicit `--page-range` when the structured error requires it | Service/account configuration is authoritative |
| Allowance | Daily free pages, then authenticated free-package pages reported by quota | Existing server package/balance billing behavior |
| Authentication | Anonymous; AppKey identity is used when querying package quota | OAuth Bearer or AppKey + Secret, subject to the selected service route |

> For 40302 (file limit), 40307 (daily quota exhausted), or 40303 (unsupported format), use [error-handling.md](error-handling.md) to decide whether to propose the paid API.

Agents should prefer JSON quota output so authentication, daily allowance,
free-package counters, request limits, and reset time remain machine-readable.

## Output Views

Choose how to see results:

```bash
# Markdown to stdout (default)
xparse-cli parse document.pdf --api auto

# JSON (explicit)
xparse-cli parse document.pdf --api auto --view json

# Save to directory (auto-names as <basename>.json/.md)
xparse-cli parse document.pdf --api auto --output ./result/
```

The CLI creates the output directory when it does not exist. If creation or
writing fails, inspect the structured `OUTPUT_FAILED` diagnostics.

## Common Scenarios

| Scenario | Command |
|----------|---------|
| Read document content | `xparse-cli parse doc.pdf --api auto` |
| Inspect parse result as JSON | `xparse-cli parse doc.pdf --api auto --view json` |
| Specific pages only | `xparse-cli parse doc.pdf --api auto --page-range 1-5` |
| Encrypted document | `xparse-cli parse doc.pdf --api auto --password secret123` |
| Save to directory | `xparse-cli parse doc.pdf --api auto --output ./result/` |
| Upload without parsing | `xparse-cli upload doc.pdf --operation-id <OPERATION_ID>` |
| Create extraction from uploaded or parsed asset | `xparse-cli task run --task-type extract --instruction '<REQUEST>' --file-id <FILE_ASSET_ID>` |

`upload` returns the original File Asset ID. A new extraction Task can use that
ID directly: parsed files reuse results, while raw files first enter paid
managed parsing. The upload itself starts no Parse or Extract Task. An existing
extraction Task's `task add --file-id` still requires a parsed asset.

## Advanced Options

| Scenario | Command |
|----------|---------|
| Single page only | `xparse-cli parse doc.pdf --api auto --page-range 3` |
| Multiple page ranges | `xparse-cli parse doc.pdf --api auto --page-range 1-2,5-10` |
| Character details & coordinates | `xparse-cli parse doc.pdf --api auto --view json --include-char-details --output ./result/` |
| Force paid OAuth | `xparse-cli parse doc.pdf --api paid --auth-method oauth` |
| Force paid AppKey | `xparse-cli parse doc.pdf --api paid --auth-method app-key` |

## API Capabilities — What You Get by Default

CLI automatically enables these capabilities (you don't need to specify them):

| Capability | What It Does |
|-----------|--------------|
| Hierarchy | Document structure (headings, nesting) |
| Inline objects | Embedded content (links, mentions) |
| Image data | Image extraction and analysis |
| Table structure | Table parsing with cell information |
| Pages | Page-level metadata |
| Title tree | Document outline/TOC |

**Exception:** Character details (`--include-char-details`) must be explicitly enabled—it increases response size significantly.

## Understanding Output

**JSON view** — Complete structured result with all parsed elements, title tree, and metadata.
For field details, see [api-reference.md](api-reference.md).

**Markdown view** — Clean, readable text format. Good for content summarization and review.

## Exit Codes

| Code | Meaning | Next Step |
|------|---------|-----------|
| 0 | Success | Parse succeeded, check stdout |
| 1 | API or network error | Check stderr for details; may retry |
| 2 | Parameter error | Check command syntax; fix and retry |
| 3 | API returned structured error | See stderr for error code + fix |

## Troubleshooting

For all error codes, recovery actions, and retry policy, see [error-handling.md](error-handling.md).
