# CLI Guidance

> Installation and quick start see [SKILL.md](../SKILL.md).

Inside WorkBuddy, insert `--profile workbuddy` immediately after `xparse-cli`
for every command. Standalone CLI commands remain unchanged.

## Paid API (optional, higher quota)

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
| _(omitted)_ | Always use the anonymous free API |
| `auto` | Compatibility alias for `free`; stored credentials are ignored |
| `free` | Always use the anonymous free API |
| `paid` | Explicitly use the paid API; pair with `--auth-method app-key` or `oauth` when both are configured |

AppKey priority: CLI flags → env vars → config file. Normal OAuth login uses
the shipped public client automatically; private deployments may override it
through a CLI flag, `XPARSE_OAUTH_CLIENT_ID`, or the config file.
WorkBuddy keeps its credentials in the isolated `workbuddy` profile and uses
Device OAuth. Login never changes the default parse route; only `--api paid`
permits paid API use.

See [authentication.md](authentication.md) for all login modes and
[textin-key-setup.md](textin-key-setup.md) for legacy AppKey setup.

## API Limits

| 维度 | Free API | Paid API |
|------|----------|----------|
| 文件类型 | PDF + 图片（jpg/jpeg/png/bmp/tiff/webp） | 所有支持类型（Doc(x)/Ppt(x)/Xls(x)/HTML/OFD/RTF 等） |
| 单次文件大小 | ≤ 10 MB | ≤ 500 MB |
| 单次页数 | ≤ 50 页 | ≤ 1000 页 |
| 每日页数 | 单 IP ≤ 1000 页/天（UTC+8 零点重置） | 按账户余额扣费，无每日上限 |
| 频率控制 | 1 次/秒/IP | QPS 限流（按账户配置） |
| 认证 | 无需认证（IP 标识） | OAuth Bearer 或 AppKey + Secret |

> 遇到 40302（文件超限）、40307（每日额度用完）或 40303（格式不支持）时，参考 [error-handling.md](error-handling.md) 决定是否升级到付费 API。

## Output Views

Choose how to see results:

```bash
# Markdown to stdout (default)
xparse-cli parse document.pdf

# JSON (explicit)
xparse-cli parse document.pdf --view json

# Save to directory (auto-names as <basename>.json/.md)
xparse-cli parse document.pdf --output ./result/

# Save to specific file (default view is markdown)
xparse-cli parse document.pdf --output result.md
```

## Common Scenarios

| Scenario | Command |
|----------|---------|
| Read document content | `xparse-cli parse doc.pdf` |
| Inspect parse result as JSON | `xparse-cli parse doc.pdf --view json` |
| Specific pages only | `xparse-cli parse doc.pdf --page-range 1-5` |
| Encrypted document | `xparse-cli parse doc.pdf --password secret123` |
| Save to directory | `xparse-cli parse doc.pdf --output ./result/` |
| Save to specific file | `xparse-cli parse doc.pdf --output ./parsed.md` |

## Advanced Options

| Scenario | Command |
|----------|---------|
| Single page only | `xparse-cli parse doc.pdf --page-range 3` |
| Multiple page ranges | `xparse-cli parse doc.pdf --page-range 1-2,5-10` |
| Character details & coordinates | `xparse-cli parse doc.pdf --view json --include-char-details --output ./parsed.json` |
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
