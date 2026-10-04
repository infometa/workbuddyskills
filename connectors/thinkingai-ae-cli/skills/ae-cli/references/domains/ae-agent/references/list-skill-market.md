# agent +list-skill-market (List Skill Market)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Market (browse) / read**

## Use Cases
- List Skills from the market (only approved items; system / company / personal scopes).
- Endpoint: `GET /api/sandbox/agent/skills/market`.
- Supports filtering by scope, category, search, and sort, with pagination.
- Use this to discover Skills before copying one with `+copy-skill`.

## Mandatory Rules (MUST)
- `--scope` must be one of the market scopes when provided (see below).
- `--category` must be one of the market category keys when provided (see below).
- `--sort` must be one of the sort options when provided (see below).
- Only approved Skills appear in the market; pending/rejected submissions are not listed.

## Market Scope
`all | system | company | custom` (`custom` = personal; `all` = system + company + personal)

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Sort Options
`newest | calls | likes` (`calls` sorts Skills by download count)

## Command
```bash
ae-cli agent +list-skill-market
ae-cli agent +list-skill-market --search "code review" --sort newest --format table
ae-cli agent +list-skill-market --scope company --category dev_tool --sort calls
ae-cli agent +list-skill-market --limit 20 --offset 0
ae-cli agent +list-skill-market --dry-run --scope system
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--scope` | No | Market scope (see above; default `all`) |
| `--category` | No | Category key (see above) |
| `--search` | No | Fuzzy search on name/displayName/description |
| `--sort` | No | Sort option (see above; default `newest`) |
| `--limit` | No | Page size (1–100, default 50) |
| `--offset` | No | Page offset (>=0, default 0) |

## Decision Rules
- When the user wants to browse available Skills, call this first.
- `--sort calls` finds the most-downloaded Skills; `--sort newest` finds the latest.
- Use `--format table` for a scannable overview.
- To bring a system/company Skill into your personal workspace, use `+copy-skill` (not `+add-skill`).

## Next Steps on Failure
- `--scope must be one of...`: use one of the market scope values.
- `--category must be one of...`: use one of the category keys.
- Empty result: widen filters (remove `--category` / `--scope`).

## Recommended Chaining
- `+list-skill-market` (browse) → `+copy-skill` (copy to personal) → `+list-skills` (verify)
