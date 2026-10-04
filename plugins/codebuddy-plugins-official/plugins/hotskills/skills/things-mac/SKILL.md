---
name: things-mac
description: Manage Things 3 via the `things` CLI on macOS (add/update projects+todos via URL scheme; read/search/list from the local Things database). Use when a user asks CodeBuddy Code to add a task to Things, list inbox/today/upcoming, search tasks, or inspect projects/areas/tags.
---

# Things 3 CLI

Use `things` to read your local Things database (inbox/today/search/projects/areas/tags) and to add/update todos via the Things URL scheme.

Setup
- Install: `GOBIN=/opt/homebrew/bin go install github.com/ossianhempel/things3-cli/cmd/things@latest`
- If DB reads fail: grant **Full Disk Access** to the calling app.
- Optional: set `THINGSDB` or pass `--db` to point at your `ThingsData-*` folder.
- Optional: set `THINGS_AUTH_TOKEN` to avoid passing `--auth-token` for update ops.

Read-only (DB)
- `things inbox --limit 50`
- `things today`
- `things upcoming`
- `things search "query"`
- `things projects` / `things areas` / `things tags`

Write (URL scheme)
- Prefer safe preview: `things --dry-run add "Title"`
- Add: `things add "Title" --notes "..." --when today --deadline 2026-01-02`
- With tags: `things add "Call dentist" --tags "health,phone"`
- Checklist: `things add "Trip prep" --checklist-item "Passport" --checklist-item "Tickets"`

Modify (needs auth token)
- Get ID: `things search "milk" --limit 5`
- Title: `things update --id <UUID> --auth-token <TOKEN> "New title"`
- Complete: `things update --id <UUID> --auth-token <TOKEN> --completed`

Notes
- macOS-only.
- `--dry-run` prints the URL and does not open Things.
