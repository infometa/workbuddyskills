---
name: noxinfluencer
description: Operate NoxInfluencer creator intelligence and marketing systems through the CLI, including search, analysis, contacts, monitoring, campaigns, CRM, outreach operations, products, affiliation, brand intelligence, exports, account setup, quota, and troubleshooting. Use when a task calls for NoxInfluencer data, records, or execution capabilities.
metadata: {"openclaw":{"requires":{"bins":["noxinfluencer"]},"install":[{"kind":"node","package":"@noxinfluencer/cli","bins":["noxinfluencer"]}],"homepage":"https://www.noxinfluencer.com/skills"}}
---

# NoxInfluencer

NoxInfluencer execution skill for creator intelligence and marketing operations across YouTube, TikTok, and Instagram. Turn business intent into valid CLI operations, verified system state, and evidence the wider marketing workflow can use for its next decision.

The user interacts through natural language. Execute CLI commands yourself and report results in plain language. Never expose raw commands to the user.

## When to Use

- User wants NoxInfluencer creator intelligence, records, or execution capabilities
- User wants creator search, analysis, contact retrieval, monitoring, exports, campaign, collection, CRM, email/message, product-center, short-link, affiliate, or brand-monitor operations through NoxInfluencer
- User needs to set up NoxInfluencer access or check quota
- User hits an auth, quota, or CLI error

## Business Collaboration

Contribute NoxInfluencer-backed creator evidence and operations to the user's wider marketing workflow. Begin from the current objective, business decision, and approved operating rule; return results in business language with the verified IDs and system state needed for the next step.

Use the appropriate business-management or writing capability to shape strategy, creator-fit judgment, outreach copy, negotiation positions, creative briefs, and lifecycle decisions. This Skill then supplies the NoxInfluencer data and execution those decisions require. Carry an active manager or Campaign's goals, stage definitions, and decision rights through every operation so both layers reinforce the same business logic.

External writes follow the user's approved action or operating rule. Important commercial commitments are presented with their material terms for the user's or qualified reviewer's decision.

## Core Principles

### Agent-First

The user does not operate the CLI. You do. Run commands silently, tell the user the result. Only share URLs when the user needs to take action in a browser (sign in, register, authorize CLI login, subscribe).

### CLI Self-Description

The CLI is self-describing — use it instead of memorizing parameters:

- **Parameters**: `noxinfluencer schema <cmd>` (e.g., `schema creator.search`; quoted path form `schema 'creator search'` also works)
- **Help**: `noxinfluencer <cmd> --help`
- **Diagnostics**: `noxinfluencer doctor`
- **Local auth state**: `noxinfluencer auth status` reads persisted or environment-provided credentials without a network call; `noxinfluencer auth logout` clears locally persisted credentials and pending device logins
- **Cost planning**: `noxinfluencer pricing tools --charged-only` shows current server-side Skill Credit prices; `noxinfluencer quota usage --days 7` reviews recent consumption
- **Login**: direct terminals can run `noxinfluencer login`; Agents/remote terminals use `login start --json` and `login wait <login_id>` (the CLI returns the user-safe authorization URL and code)
- **Command-tree check**: `noxinfluencer schema --all` must include `creator`, `monitor`, `campaign`, `collection`, `email`, `message`, `crm`, `product`, `short-link`, `affiliation`, `brand-monitor`, `dispute`, `export`, `file`, `feedback`, `quota`, `pricing`, and `agent`
- **Exit codes**: `noxinfluencer agent exit-codes`
- **Preview**: `--dry-run` (shows request without executing)
- **Language routing**: `--lang zh` switches all URLs to `cn.noxinfluencer.com`

## Routing Cheat Sheet

Use `noxinfluencer schema <cmd>` for exact parameters. Prefer broad command families over memorizing flags:

- Creator sourcing: `creator search`, `creator search-filter*`, `creator not-interested ...`, `creator lookalikes`, `creator export*`, `creator lookalikes-export`
- Creator reads: `creator profile/audience/content/cooperation`; use `creator contacts` only for visible/exported contacts
- Monitoring: `monitor list/create/add-task/import-*/tasks/history/summary/report*`; use `monitor auto-track ...` for newly published creator content
- Operations: `campaign`, `collection`, `crm`, `email`, `message`, `product`, `short-link`, `affiliation`, `export`, `file`
- Brand monitoring: `brand-monitor ...`
- Creator dispute due diligence: `dispute records/search/mine/get/report/update/withdraw`
- Setup, quota, and pricing: `login`, `doctor`, `quota`, `quota usage`, `pricing`, `pricing tools`, `agent exit-codes`
- Feedback: `feedback submit/inbox/get`

If the user does not have a `creator_id`, the first creator read may use `--url` or `--platform --channel-id`; afterwards preserve and reuse returned `creator_id`. For marketing-ops commands, expect JSON bodies and dry-run defaults; use `schema <cmd>` and `--force` only after explicit approval.

### User Feedback

If the user wants to report a bug, confusing behavior, data issue, suggestion, or feature request, offer to submit feedback through `noxinfluencer feedback submit`. Ask for a short confirmation before sending. Attach screenshots or logs with `--file` when available. Feedback is free, does not consume Skill quota, and may receive asynchronous follow-up; check `noxinfluencer feedback inbox` or `noxinfluencer feedback get <feedback_id>` later.

### Creator Disputes

Use `feedback` for product, data, or CLI issues. Use `dispute` only for a concrete creator collaboration breach or due-diligence concern. Before a new report, run `dispute records <creator_id>` when available, require concrete screenshot evidence, and get explicit approval before report/update/withdraw. Private reports hide their description and evidence publicly, but not their type/count. This feature requires paid membership and consumes no Skill Credit; use `dispute options` or `schema dispute.report` for the current fields.

### Email Task Boundary

Standalone `email create` and `email update` operate only type 3 email tasks. Their request bodies must never contain `campaign_id`, and an Agent must not pass `task_type` to turn a standalone task into a Campaign task.

An intelligent Campaign initializes exactly three fixed source tasks: type 0 for manual-add recipients, type 1 for proactive invitation recipients, and type 2 for creator applications. These types describe recipient sources; type 1 does not authorize guessing a `task_id`. The current CLI cannot discover or write these fixed tasks safely. Do not infer a fixed `task_id`, and do not use standalone email mutations or recipient commands to modify one. Route Campaign recipient changes to the SaaS intelligent Campaign page.

---

## 1. Getting Started

Run `noxinfluencer doctor`, then fix only what is missing:

1. No CLI or stale command tree → ask the user to install `@noxinfluencer/cli@latest`; verify with `schema --all`.
2. No API key → use Device Flow. For an Agent or remote terminal, run `noxinfluencer login start --json`, give the user `verification_uri_complete` and `user_code`, then run `noxinfluencer login wait <login_id>` after authorization. On a direct terminal, `noxinfluencer login` does this in one command. `login --browser` is only for a local loopback callback. Manual API-key handoff is fallback only; use `auth --key-stdin`, never argv/logs or expose `device_code`.
3. Configured → run `quota` and report blocking quota or entitlement issues.

### Quota and Billing

Run `quota` yourself and report the snapshot. For cost planning or optimization, use `pricing tools --charged-only` for current per-action prices and `quota usage` for historical consumption. API-backed calls may consume Skill quota and may also depend on SaaS-side capability quota or entitlement. If the response includes `action.url`, pass it to the user.

---

## 2. Discovering Creators

Turn an open-ended search into a usable shortlist.

Ask for only the missing essentials: platform, niche, region, creator size, and whether email signal matters. Search directly once the request is specific enough. Multi-platform sourcing requires separate platform searches.

Use `schema creator.search` for flags. Search a known creator name/handle with `--creator_name`; use `--keywords` for topic discovery, never both. Put user-specified unwanted topics in `exclude_keywords`, and apply the SaaS cooperation, CRM communication, contacted-scope, and collection filters in the same search. Use `creator search-filter-options` when the matching patch is unclear; standalone `search-filter` is only for an already returned page. Add `--has_email true` when platform email outreach needs creators with an email signal, but do not imply visible email was retrieved. For pagination, reuse the prior filters and `data.search_after`; prefer a JSON body.

Only run `creator not-interested add` when the user explicitly asks to mark that creator as Not interested. Treat it as an approved, reversible mutation; a weak match or noisy result alone is not approval.

Creator search and lookalike discovery charge by returned creator count, not by a fixed page request. Check `pricing tools --action creator_search` or `--action creator_lookalikes` when the user asks about cost. Default to smaller, purposeful pages for exploration; use larger pages only when the user asks for a broad shortlist or bulk follow-up.

### Lookalike Discovery

Use `creator lookalikes` when the user asks for creators similar to a source creator or URL. Treat results as recommendations, use the returned opaque `creator_id` values directly, and save them separately only after the user chooses targets.

### Selected Result Exports

Use `creator export` or `creator lookalikes-export` only after the user selects 1-100 returned `data.items[].id` values. Base mode uses standard SaaS columns; deep mode requires supported `field_keys`. Preserve lookalike `data.export_context` unchanged. Run deep `creator export-preview` first to estimate business quota without creating a task or consuming Skill Credit. Contact fields can consume contact quota. Poll approved export tasks through shared `export` commands.

### Shortlist Presentation

Present 3–5 comparable candidates first: name, platform, size, performance, geography, tags, and why they match. If results are noisy, ask for one narrowing filter. Preserve `creator_id` for follow-up actions.

---

## 3. Analyzing Creators

Help the user decide whether a creator is worth pursuing. Lead with a verdict, not a wall of numbers.

Prefer `creator_id` from prior results. Check the user's requested concern first; otherwise use profile → audience → content → cooperation. Use `--detail` only when deeper evidence is needed, and skip platform-limited dimensions unless relevant. Return verdict first, then evidence.

### Verdict Framework

Use one of four conclusions: high-priority, viable with risks, needs manual review, or not a priority. Always surface dispute/negative cooperation signals. See `@references/verdict-heuristics.md` for detailed heuristics.

---

## 4. Retrieving Contacts

Retrieve visible contact info only when the user explicitly wants exported contact details, external outreach, or to use email outside NoxInfluencer.

Strong rule: platform email outreach must not call `creator contacts` unless the user explicitly asks for visible/exported contact info. Put creator search `data.items[].id` or creator read `data.creator_id` into the recipient object's `creator_id` field for `email recipients add/replace`. If the user already has a canonical raw platform identity, `platform + channel_id` is also supported; use `email_address` only for a known external address. A URL, handle, or creator name must be resolved through creator search/read first. If the user vaguely asks to "find emails and send", default to platform email and mention that exporting visible emails uses extra contact quota. Email sending may still consume the email service's own quota.

When contacts are explicitly needed, run `creator contacts` for the selected creator and return only the visible contact info plus quality signal. If email is missing or low-confidence, say so plainly. Do not add outreach recommendations or restate creator metrics.

---

## 5. Tracking Performance

Manage video monitoring projects and tracked content. Operational only — manages monitoring, not performance judgment.

List projects first when unclear. For known published URLs, use `monitor add-task` or the SaaS template/import path. Use summary for project-level performance, tasks for tracked videos, and history for time-series detail. Preserve stable IDs and returned `creator_id` values. Use monitor report commands for direct SaaS Excel downloads, not shared async export polling.

For ongoing creator monitoring, use `monitor auto-track`. Its Excel import validates every row before creating one rule; if it returns `failed_items`, fix the workbook and retry because no partial rule was created.

---

## 6. Marketing Ops

Operate NoxInfluencer campaign, collection, CRM, email, message, product-center, short-link, affiliation, and export workflows. Stay operational: retrieve state, prepare changes, preview impact, then apply only after approval.

### Workflow

1. Identify the target domain and read current state first when IDs are unclear.
2. For platform email outreach to creators found in NoxInfluencer, use the standalone email-task path and add recipients with search `data.items[].id` or creator read `data.creator_id` in the recipient `creator_id` field; do not retrieve contacts first. Use `platform + channel_id` only when the user already has that canonical raw platform identity. Standalone `email create/update` is type 3 only and must not include `campaign_id` or `task_type`. Manage intelligent Campaign fixed tasks in SaaS because the current CLI cannot discover or write them safely. Discover bound senders with `email sender list [task_id]`; never ask the user to inspect browser Network for sender IDs. See the CLI schema and `@references/marketing-ops.md`.
3. Use `message send` or `message schedule` only for existing `thread_id` replies. If no thread exists, offer the email-task path for platform creators. For an explicit whole-conversation archive, use `message archive`; never substitute `crm archive`.
4. For JSON-first commands, run `schema <cmd>` and prepare the minimal `--body-file` object required by the CLI.
5. For staged workflows, run `validate` first, then `preview`, then `apply --force` only after user approval.
6. For direct mutations, rely on dry-run first unless the user has already approved the exact action.
7. For new creator searches, use integrated exclusions/hide rules; keep standalone `creator search-filter` for an existing page. Email-recipient deduplication remains task-scoped through its `filter` commands.
8. Use `short-link` for normal Nox short links only; use `affiliation` for Shopify affiliate campaigns, members, tracking links, discount codes, and performance reads.
9. If Shopify store authorization is missing, send the user to SaaS; do not try to authorize stores inside the Skill.
10. For creator, collection, CRM, and brand-monitor async exports, create the task, poll with `export get` or `export list`, then use `export download --output` only when ready.
11. Monitor, short-link, and affiliation Excel reports download directly to `--output`; do not poll them through shared export tasks.
12. Keep SaaS spreadsheet templates, import `failed_items`, public image URLs, and private attachments distinct. Use `file image upload` for public rich-text images and attachment commands for authorized private files.

Do not draft outreach copy. If the user asks to send or schedule an email task or message, confirm the task/thread, recipients, sender, scheduled time, and content are already approved.

See `@references/marketing-ops.md` for domain routing, mutation guardrails, and export handling.

---

## 7. Brand Monitoring

Use brand-monitor commands for owned/competitor brand analysis and brand asset exports. This is distinct from creator due diligence: it starts from `brand_id`, not `creator_id`.

### Workflow

1. When `brand_id` is unclear, use `search` for a known brand name, `rank` for category/market discovery, and `list` only for this account's monitored, unlocked, or sample brands; use `get` after selecting an ID.
2. Use matrix/strategy reads for brand-level analysis: competition, cooperation, influencer portrait, defense gap, and product signals.
3. Use asset list commands for raw influencer/content/tag/product rows; these are JSON-first and usually require `--body-file`.
4. Product signal commands currently support YouTube only. Do not run them for TikTok or Instagram unless the CLI schema later shows support.
5. Use export commands for downloadable brand assets; follow up through shared `export` commands.
6. Treat `add`, `unlock-base`, `unlock-high`, and all `*-export` commands as mutations or async job creation: dry-run first, `--force` only after approval.

See `@references/brand-monitor.md` for command routing and platform boundaries.

---

## Error Handling

For API-backed failures (`quota`, `pricing`, `creator`, `monitor`, `campaign`, `collection`, `email`, `message`, `crm`, `product`, `short-link`, `affiliation`, `brand-monitor`, `dispute`, `export`, `file`, `feedback`), use the CLI response's `action` field when present:
- `action.url` — where the user should go
- `action.hint` — what to do

Local/helper commands (`auth`, `doctor`, `schema`, `env`, `agent exit-codes`) may not include `action`. Read their native output directly instead of assuming the API error envelope.

For unexpected failures, run `doctor` as a first diagnostic step.

## References

- `@references/cli-response-format.md` — response envelope differences and error action handling
- `@references/marketing-ops.md` — campaign, spreadsheet, file, email/message, report/export workflows and mutation guardrails
- `@references/brand-monitor.md` — brand monitor routing, YouTube-only product signals, export boundaries
- `@references/platform-support.md` — data availability by platform
- `@references/search-filters.md` — filter selection by user intent
- `@references/verdict-heuristics.md` — detailed due-diligence rules and output structure
