---
name: ae-community
description: "AE community analysis and data reporting for posts, comments, topics, livestreams, customer-service chats, WeCom after-sales groups, and in-game chat. Use for community content insight, sentiment, intent, evidence drill-down, community data ingestion/import/submission, and WeCom chat data integration (社区数据上报、导入、提交社区数据、企微聊天数据接入)."
---

# ae-community

Skill revision: 2.4.1.

The AE Community domain provides social and chat data analysis plus validated community data reporting. Curated analysis commands run as **`ae-cli community +<subcommand>`**; chat analysis uses dynamic Capability Gateway commands; reporting uses the direct **`ae-cli community data report`** ingestion command.

| Route | CLI service | Responsibility |
|-------|-------------|----------------|
| `community_content` | `community` | Posts, comments, corpus tags, search, livestream content, risk content |
| `community_analysis` | `community` | Channel list, overview metrics, sentiment, tag trends |
| `community_hot` | `community` | Daily summary, hot topics, topic drill-down |
| `community.chat.*` | `community` Capability Gateway | Chat overview, participant discovery, roster-driven service metrics, intent/risk drill-down, raw evidence |
| Direct ingestion data plane | `community data report` | Validate, normalize, and submit community records to an explicit Iris `/sync_content` endpoint |

---

## Global AE CLI Rules

AE CLI (`ae-cli`) is the command-line tool for the AE / TE / ThinkingEngine analysis platform. For AE analysis-side requests, prefer `ae-cli` and this skill's reference docs over model memory.

Global parameters:

| Parameter | Description |
|---|---|
| `--format <json\|table>` | Output format. Default is JSON. |
| `--jq <expr>` | jq filter expression for JSON output. |
| `--host <url>` | Override the active AE host for analysis-side commands and place it after the subcommand, e.g. `ae-cli community +<command> --host <url>`. It is intentionally unavailable for `community data report`; use `--endpoint` there. |

Output and errors:
- Successful commands return machine-readable JSON by default. Envelope may include optional `_notice.host_compat`.
- Failed commands return `{ "ok": false, "error": { "type": "...", "message": "...", "hint": "..." } }` and exit non-zero.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.

Safety constraints:
- Read commands can execute directly after required IDs and references are verified.
- Ordinary `write` commands require explicit user intent but no CLI confirmation. Only `high-risk-write` commands use the confirmation gate.
- Never invent command names, flags, JSON payloads, `project_id`, resource IDs, field names, event names, property names, metric definitions, or date formats. Read the matching command reference and discover real project metadata first.
- **NEVER fabricate or guess resource names** (reports, dashboards, events, properties, metrics, clusters, tags, alerts). Always use list commands to discover real resources first. If a resource is not found after fuzzy search and full list fallback, explicitly tell the user "resource not found" and stop - do not proceed with fabricated names.

**Community** commands use the domain `community` (this skill). Other AE domains include: `analysis` (analysis and audience), `analysis-meta` (metadata), and `operation` (operations).

---

## Overview

Typical use cases:

- Search and inspect posts or videos, then drill into detail and comment analytics
- Track sentiment, keywords/tags, and macro overview metrics by time range
- Monitor risky or moderated content
- Analyze livestream rooms, sessions, and AI-generated session reports
- Analyze customer-service DMs, customer after-sales groups, and in-game chat
- Produce daily/weekly/activity-style reports via composite references under `references/community-*.md`

For per-command flags and copy-paste examples, use the files in [`references/`](references/).

---

## Parameter conventions

| Item | Description |
|------|-------------|
| `--space-id` | Community space ID (number) |
| `--game-id` | Game / space identifier (number) |
| `--channel-id` / `--channel-id-list` | Often required after you know channel IDs (see **Channel ID prerequisite** below) |
| Globals | Same as other domains: `--host`, `--mcp-url`, `--format`, `--jq`, `--dry-run`, `--yes` |

- **Lists (comma-separated):** e.g. `--channel-id-list 1,2,3`, `--keywords a,b`, `--sentiment-types 0,1`
- **Dates:** `yyyy-MM-dd` for range endpoints (e.g. `--start-time`, `--end-time`, `--date`)
- **Data reporting:** `community data report` requires `--space-id`, `--channel-id`, and `--source-id` as positive int64 identifiers. Here `--space-id` maps to Iris `game_id`.
- **Reporting endpoint:** use `--endpoint` or `AE_IRIS_SYNC_ENDPOINT`. `--host` does not select, derive, or modify the ingestion endpoint.
- **Reporting input:** use exactly one mode: `--data-type <type> --data <inline|path|@path|->`, or `--payload <inline|path|@path|->`.
- **Reporting schema:** run `ae-cli community data report --help` before building input to check the required record fields for every supported `data_type`; use the reporting reference for field limits and normalization behavior.

---

## Core concepts

### Channel ID prerequisite (`+get_channel_info`)

Many commands need **`--channel-id`** or **`--channel-id-list`** (post detail, comment summaries, live lists, channel-scoped search). If you only have `--space-id` / `--game-id`, run:

```bash
ae-cli community +get_channel_info --space-id <id> --game-id <id>
```

Then use returned channel IDs in follow-up commands. Details: [`references/get_channel_info.md`](references/get_channel_info.md).

---

## Scenario routing

Route users to composite workflows when intent matches:

| User intent | Start here |
|-------------|------------|
| Single-day ops brief, T-1 vs T-2 | [`community-daily-report.md`](references/community-daily-report.md) |
| Weekly roll-up | [`community-weekly-report.md`](references/community-weekly-report.md) |
| Activity / campaign insight | [`community-activity-analysis.md`](references/community-activity-analysis.md) |
| One character / IP deep dive | [`community-character-analysis.md`](references/community-character-analysis.md) |
| Single topic timeline + actions | [`community-hottopic-insight.md`](references/community-hottopic-insight.md) |
| Official post taxonomy | [`community-analyzing-official-content.md`](references/community-analyzing-official-content.md) |
| Comment thread deep dive | [`community-analyzing-theme-comment.md`](references/community-analyzing-theme-comment.md) |
| Customer service, after-sales group, or in-game chat | [`community-chat-analysis.md`](references/community-chat-analysis.md) |
| Report, import, or submit community/WeCom chat data | [`community-data-report.md`](references/community-data-report.md) |

---

## Common scenarios

### 1. Search and content drill-down

```bash
ae-cli community +search_posts --space-id 1 --game-id 1 \
  --start-time 2026-04-01 --end-time 2026-04-07

ae-cli community +get_post_detail --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid> --resource-type 0

ae-cli community +get_comments_summary --space-id 1 --game-id 1 \
  --channel-id 1 --uuid <uuid>
```

### 2. Analysis and sentiment

```bash
ae-cli community +get_channel_info --space-id 1 --game-id 1

ae-cli community +get_overview_metrics --space-id 1 --game-id 1 \
  --start-time 2026-04-01 --end-time 2026-04-07

ae-cli community +get_sentiment_overview --space-id 1 --game-id 1 \
  --start-time 2026-04-01 --end-time 2026-04-07
```

### 3. Hot topics and daily snapshot

```bash
ae-cli community +get_hot_topics --space-id 1 --game-id 1

ae-cli community +get_daily_summary --space-id 1 --game-id 1 --date 2026-04-01
```

### 4. Livestream

```bash
ae-cli community +get_livestream_list --space-id 1 --game-id 1

ae-cli community +get_livestream_detail --space-id 1 --game-id 1 --stream-id <id>

ae-cli community +get_livestream_analysis --space-id 1 --game-id 1 --stream-id <id>
```

### 5. Chat analysis

Chat capabilities are L3 and must be discovered before use. Read
[`community-chat-analysis.md`](references/community-chat-analysis.md) for scenario selection,
call-scoped identity classification, comparison windows, metric definitions, evidence limits, and
report templates. Never report customer-service performance without a staff identity list.
The list must be the complete staff roster for the selected service scope, even for a single-agent
question; a partial roster is discovery context, not permission to calculate KPIs.

```bash
ae-cli capability search "chat" --domain community
ae-cli capability inspect community.chat.overview
ae-cli capability run community.chat.overview \
  --input '{"game_id":3,"start":"<start-yyyy-MM-dd>","end":"<end-yyyy-MM-dd>"}'
```

### 6. Data reporting

Read [`community-data-report.md`](references/community-data-report.md) before building input. Use an
explicit ingestion endpoint and verified IDs; do not derive them from the active AE host or analysis
results.

```bash
ae-cli --dry-run community data report \
  --endpoint https://<iris-ingress>/sync_content \
  --space-id <space-id> --channel-id <channel-id> --source-id <source-id> \
  --data-type chat --data @chat.json

ae-cli community data report \
  --endpoint https://<iris-ingress>/sync_content \
  --space-id <space-id> --channel-id <channel-id> --source-id <source-id> \
  --data-type chat --data @chat.json
```

### Data Reporting Workflow

1. Obtain the complete `/sync_content` endpoint from the user or `AE_IRIS_SYNC_ENDPOINT`. Never guess, derive, or concatenate it.
2. Verify the real space, channel, and source IDs. Never fabricate identifiers; `--space-id` becomes Iris `game_id`.
3. Run `ae-cli community data report --help` before constructing records. Use the installed command's required-field list for each `data_type` as the source of truth, then consult the reporting reference for detailed limits and normalization.
4. Prefer `@file` or stdin (`-`) for sensitive records so payloads do not enter shell history.
5. Before the first submission of a dataset, run `--dry-run`. Its summary is redacted and does not print business content.
6. After the user has clearly requested submission, run the `risk: write` command directly. It does not need `--yes` or another confirmation.
7. Interpret success only as `status: "queued"` with `persistence_verified: false`, never as per-record acceptance or durable storage.
8. A timeout leaves delivery state unknown. Check the downstream query/storage side before considering another submission, and never retry automatically.

---

## Dry-run debugging

```bash
ae-cli --dry-run community +get_channel_info --space-id 1 --game-id 1
ae-cli --dry-run community +search_posts --space-id 1 --game-id 1 \
  --start-time 2026-04-01 --end-time 2026-04-07
```

---

## References (per-command)

| Topic | Document |
|-------|----------|
| Channel list (prerequisite) | [`get_channel_info.md`](references/get_channel_info.md) |
| Search posts/videos | [`search_posts.md`](references/search_posts.md) |
| Post/video detail | [`get_post_detail.md`](references/get_post_detail.md) |
| Corpus tags / `tagCode` | [`get_corpus_tags.md`](references/get_corpus_tags.md) |
| Comment summary | [`get_comments_summary.md`](references/get_comments_summary.md) |
| Comment tag analysis | [`get_comment_tag_analysis.md`](references/get_comment_tag_analysis.md) |
| Sentiment overview | [`get_sentiment_overview.md`](references/get_sentiment_overview.md) |
| Overview metrics | [`get_overview_metrics.md`](references/get_overview_metrics.md) |
| Hot topics | [`get_hot_topics.md`](references/get_hot_topics.md) |
| Topic detail | [`get_topic_detail.md`](references/get_topic_detail.md) |
| Tag trends | [`get_tag_trends.md`](references/get_tag_trends.md) |
| Daily summary | [`get_daily_summary.md`](references/get_daily_summary.md) |
| Risk content | [`get_risk_content.md`](references/get_risk_content.md) |
| Live rooms / list / detail / analysis / overview / room metrics | [`get_livestream_rooms.md`](references/get_livestream_rooms.md), [`get_livestream_list.md`](references/get_livestream_list.md), [`get_livestream_detail.md`](references/get_livestream_detail.md), [`get_livestream_analysis.md`](references/get_livestream_analysis.md), [`get_livestream_overview.md`](references/get_livestream_overview.md), [`get_livestream_room_metrics.md`](references/get_livestream_room_metrics.md) |
| Customer-service, after-sales group, and in-game chat workflows | [`community-chat-analysis.md`](references/community-chat-analysis.md) |
| Community data reporting, schemas, and queued semantics | [`community-data-report.md`](references/community-data-report.md) |

---

## Command groups

Commands below are shown **without** the `ae-cli community` prefix; all use the `+` prefix on the CLI.

### Content (`community_content`)

`+get_livestream_list`, `+get_livestream_detail`, `+get_livestream_analysis`, `+get_post_detail`, `+get_comments_summary`, `+get_comment_tag_analysis`, `+get_corpus_tags`, `+get_risk_content`, `+search_posts`, `+get_livestream_overview`, `+get_livestream_rooms`, `+get_livestream_room_metrics`

### Analysis (`community_analysis`)

`+get_channel_info`, `+get_overview_metrics`, `+get_sentiment_overview`, `+get_tag_trends`

### Hot (`community_hot`)

`+get_daily_summary`, `+get_hot_topics`, `+get_topic_detail`

### Data reporting (direct ingestion data plane)

| Command | Risk | Endpoint | Input |
|---------|------|----------|-------|
| `data report` | `write` | `--endpoint` or `AE_IRIS_SYNC_ENDPOINT`; never `--host` | `--data-type` + `--data`, or `--payload` |

---

## Composite scenario skills

Structured multi-step report workflows — open the linked reference for the complete ae-cli command sequence.

| Skill | Purpose |
|-------|---------|
| [`community-activity-analysis.md`](references/community-activity-analysis.md) | Activity / marketing event insight |
| [`community-daily-report.md`](references/community-daily-report.md) | Daily express (T-1 vs T-2) |
| [`community-character-analysis.md`](references/community-character-analysis.md) | Character / IP deep analysis |
| [`community-hottopic-insight.md`](references/community-hottopic-insight.md) | Single-topic evolution and actions |
| [`community-weekly-report.md`](references/community-weekly-report.md) | Weekly operations summary |
| [`community-analyzing-official-content.md`](references/community-analyzing-official-content.md) | Official content taxonomy |
| [`community-analyzing-theme-comment.md`](references/community-analyzing-theme-comment.md) | Themed comment-area analysis |

---

## Write operations

Most community commands are **read-only**. `community data report` is an ordinary **`risk: write`** command: explicit user intent is sufficient and no confirmation or `--yes` is required. Only commands marked **`risk: high-risk-write`** use the confirmation gate.
