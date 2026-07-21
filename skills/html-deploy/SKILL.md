---
name: html-deploy
description: "Publish a single self-contained HTML page to htmlcode.fun and return live URLs. Use when generated HTML needs quick public sharing, demos, reports, landing pages, or QR-share pages."
description_zh: "将单文件 HTML 快速发布为可分享公网链接"
description_en: "Publish self-contained HTML pages to htmlcode.fun for live links"
version: 1.3.1
homepage: https://www.htmlcode.fun/s/htmlcode-fun-guide
allowed-tools: Bash,Read,Write
---
# HTML Instant Deploy

## Overview

Use `htmlcode.fun` when the deliverable is one standalone HTML document and speed matters more than full project hosting. The service is an open HTML app marketplace: agents deploy or revise HTML, users can manually like a version in the web UI, and liked versions become preserved immutable snapshots.

Live guide:
- https://www.htmlcode.fun/s/htmlcode-fun-guide

Bundled script:
- `scripts/htmlcode_deploy.py` for deploy, version append, version inspection, content fetch, and unlocked-version edits.

## Decision rule

Use this skill when:
- The deliverable is a single HTML page.
- The page can be self-contained or nearly self-contained.
- Fast sharing matters more than custom domains, CI/CD, or multi-file assets.

Do not use this skill when:
- The project is a React, Vue, Next, or multi-file frontend app.
- The site needs build steps, environment variables, server logic, or asset pipelines.
- The user specifically needs their own domain or production-grade hosting.
- The HTML payload is likely to exceed about 1 MB.

## Current htmlcode.fun rules

- Always use JSON; never use multipart/form-data or `curl -F`.
- `description` is required: one concise sentence, max 240 characters.
- One request deploys one HTML document only.
- Stable projects should use `enableCustomCode=true` + `customCode`.
- For recurring or iterative work, append a new version with `createVersion=true` instead of creating daily/random short codes.
- A version with `likeCount > 0` is locked and must not be overwritten or deleted.
- An unlocked version (`likeCount == 0`) may be overwritten or unpublished when appropriate.
- Agents must not call like endpoints. Likes are intentionally user/manual actions in the htmlcode.fun web UI.
- After deploy, tell the user the returned `url`, `detailUrl`, and/or `versionUrl`, plus the returned `preserveHint` when present.
- Successful deploys have a global cooldown of about 10 seconds. On `429`, respect `retryAfterSeconds`.

## Recommended workflows

### New one-off page

1. Produce a complete HTML document with `<title>`, viewport, and useful metadata.
2. Deploy with `POST /api/deploy` and a required `description`.
3. Return the live link and tell the user they can open the detail page and manually like the current version to preserve it.

Script:

```bash
python scripts/htmlcode_deploy.py deploy page.html --title "Launch Page" --description "A concise one-sentence summary of this HTML page."
```

### Stable short link or recurring project

Use a stable `customCode`; append new versions for future updates.

```bash
python scripts/htmlcode_deploy.py deploy page.html --code ai-daily --title "AI Daily 2026-05-08" --description "Daily AI briefing for 2026-05-08."
python scripts/htmlcode_deploy.py append ai-daily page.html --title "AI Daily 2026-05-09" --description "Daily AI briefing for 2026-05-09."
```

### Inspect or reuse an app

```bash
python scripts/htmlcode_deploy.py versions ai-daily
python scripts/htmlcode_deploy.py get ai-daily --version 3 --output ai-daily-v3.html
```

By default, `get --output` writes the HTML `content` field to the file. Use `--download` only when you explicitly want the server's raw download response.

### Fix an existing version

Before overwriting, inspect versions. Only overwrite if the target version has `likeCount == 0`. If it has likes, append a new version instead.

```bash
python scripts/htmlcode_deploy.py versions landing-demo
python scripts/htmlcode_deploy.py overwrite landing-demo 2 fixed.html --description "Fixes layout issues in version 2."
```

The script also performs this `likeCount` check automatically before `overwrite`, `status`, and `delete-version`.

### Publish or unpublish one version

```bash
python scripts/htmlcode_deploy.py status landing-demo 2 inactive
python scripts/htmlcode_deploy.py status landing-demo 2 active
```

## Raw API map

- `POST /api/deploy` — deploy a new app or append a version with `createVersion=true`.
- `GET /api/deploy/content?code={code}&version={version}` — read metadata and source.
- `GET /api/deploys/{code}/versions` — list version history and `likeCount`.
- `PATCH /api/deploys/{code}/versions/{version}` — overwrite or set status for an unlocked version.
- `DELETE /api/deploys/{code}/versions/{version}` — delete one unlocked version. Treat deletion as sensitive; ask first unless the user explicitly requested it.
- `PATCH /api/deploys/{code}/current` — switch the public current version when needed.

## Response handling

On success, save and report relevant fields:
- `code`
- `url`
- `detailUrl`
- `versionUrl`
- `versionNumber`
- `qrCode`
- `preserveHint`

If an API response contains `errorCode`, `hint`, `detail`, `stage`, `requestId`, or `retryAfterSeconds`, use those fields in troubleshooting. For locked-version errors, append a new version instead of trying to overwrite.

## Best practices for agents

- Prefer one high-quality deploy over many tiny edits.
- For user-visible pages, include Open Graph tags when sharing matters.
- Keep CSS/JS inline when practical; avoid large base64 images.
- Use meaningful stable codes for recurring content, e.g. `ai-daily`, not `ai-daily-0508`.
- If updating an existing code, read versions first and avoid touching liked versions.
- Treat htmlcode.fun as a fast publication channel, not a full static hosting platform.
- Tell the user when Vercel, Netlify, GitHub Pages, or a real app host is a better fit.

## Good fit

- Temporary landing pages
- Demo pages
- Shareable documentation pages
- QR-linked event or campaign pages
- AI-generated single-file frontends
- Recurring reports with stable short links and version history

## Poor fit

- Multi-page sites with shared assets
- Framework builds
- Large production frontends
- Apps requiring backend auth, databases, or secrets
- Team workflows with preview environments and rollback controls
