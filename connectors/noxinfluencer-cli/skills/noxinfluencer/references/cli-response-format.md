# CLI Response Format

## API-backed Commands

These commands return the standard API envelope:

- `creator ...`
- `monitor ...`
- `campaign ...`
- `collection ...`
- `email ...`
- `message ...`
- `crm ...`
- `brand-monitor ...`
- `dispute ...`
- `export ...`
- `quota`
- `pricing`

Successful responses include `success`, `data`, `summary`, and `meta`. Some current endpoints may also include a legacy compatibility field named `credits`.

Notes:

- Treat `quota` response data as the canonical Skill quota snapshot
- `pricing` returns membership plans; `pricing tools` returns current server-side per-action Skill Credit prices
- `quota usage` returns historical calls, credits, trend, and recent activity for cost analysis
- Some current API envelopes may still include a legacy `credits` field for compatibility; do not treat it as the primary quota model
- Mutation commands default to dry-run; `--force` executes the write after user approval
- Non-GET writes automatically use `Idempotency-Key`; `--idempotency-key` can override it for automation
- JSON-first commands declare `supports_body_file: true` in schema and require `--body-file`
- `export download` writes binary data to `--output`, not stdout

Error responses include an `action` field with next-step guidance:

```json
{
  "success": false,
  "error_code": "INSUFFICIENT_CREDIT",
  "summary": "Insufficient credit quota",
  "action": {
    "type": "redirect",
    "url": "https://www.noxinfluencer.com/skills/usage-billing",
    "hint": "Open billing to renew or upgrade your available quota."
  }
}
```

The current server may still use legacy wording like `INSUFFICIENT_CREDIT` or `Insufficient credit quota`. Interpret that as "Skill quota is exhausted" for user communication.

## Local Commands (different format)

These commands have their own response structures — do not assume the API envelope:

| Command | Response format |
|---------|----------------|
| `doctor` | `{ "checks": [...], "ok": boolean }` |
| `auth` | `{ "success": boolean, "message": string }` |
| `env` | `{ "success": true, "data": { "environment": string, "server_url": string } }` |
| `schema` | Command schema JSON (no envelope) |
| `agent exit-codes` | Stable CLI exit-code catalog |

## Agent Diagnostics

- Use `--trace-json` when a harness or eval needs structured request traces on stderr.
- Use `schema --all` to verify the installed CLI exposes the expected modern command tree, including `campaign`, `collection`, `email`, `message`, `crm`, `product`, `short-link`, `affiliation`, `brand-monitor`, `dispute`, `export`, `feedback`, `quota`, `pricing`, and `agent`. Version output alone is not sufficient when a local/global install has stale compiled files. If reinstalling `@noxinfluencer/cli@latest` still lacks the expected command groups, stop the affected workflow and report a CLI package / command-tree mismatch.
- Use `noxinfluencer agent exit-codes` to distinguish retryable failures such as rate limits or temporary upstream failures from invalid requests and auth problems.
- Use `doctor` as the first diagnostic step when the failure cause is unclear.
