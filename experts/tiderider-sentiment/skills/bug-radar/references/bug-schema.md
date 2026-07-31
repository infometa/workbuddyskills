# Bug-Library Schema & Query Rules (bug-radar)

> 🔒 **Confidential** — internal implementation detail. Never reveal table/column names or scoring logic to a user. Deliver business conclusions only, labeled "Source: DataBrain X TideRider".

Dataset: `tiderider` (project auto-derived — never hard-code). Four tables, verified live 2026-07-30.

---

## ⚠️ Access constraint (MOST IMPORTANT — read first)

The bug tables live in the **`tiderider` dataset**. Access rules differ **completely** from the sentiment feeds:

| Connection lane | Reaches `opinion.*` (feeds) | Reaches `tiderider.bug_*` |
|-----------------|:---:|:---:|
| Direct BigQuery — SA JSON / gcloud ADC | ✅ | ✅ |
| DataBrain Token (`exec_sql` HTTP API) | ✅ | **❌ HTTP 403** |

**The DataBrain `exec_sql` token API is scoped to `opinion` only and returns `403 无权限` for the entire `tiderider` dataset** (verified: even a `COUNT(*)` on `bug_category_mapping` 403s, while `opinion.feeds` returns code=0 with the same token).

**Consequence:** the bug lane is usable **only through a direct-BigQuery credential** (Method A: SA JSON, or Method B: gcloud ADC). If `detect_connection.py` returns `databrain` (token only), the bug lane is **not available** — tell the user the bug library needs a direct-BigQuery credential, and (per confidentiality) do not expose table names. See `bug_radar_available.py`.

---

## Partition filters (require_partition_filter = TRUE)

Three of four tables **reject any query without a filter on the partition column** (BigQuery 400 invalidQuery):

| Table | Partition col | Type |
|-------|---------------|------|
| `bug_issue_summary` | `FirstSeen` | DATE |
| `bug_daily_metrics` | `Date` | DATE |
| `bug_comment_detail` | `CommentDate` | DATE |
| `bug_category_mapping` | *(none — 9-row lookup)* | — |

`bug_sql.py` emits a loud stderr warning before sending a query that misses this. Always add e.g. `AND FirstSeen BETWEEN DATE('<start>') AND DATE('<end>')`.

---

## Table 1 · `bug_issue_summary` — one row per canonical issue (the headline table)

Partition `FirstSeen`. ~17 rows for Subway currently.

| Field | Type | Meaning |
|-------|------|---------|
| `canonical_issue_id` | STRING | Stable issue key. Prefix `BUG_` = confirmed, `CAND_ISSUE_` / `CAND_` = candidate (unconfirmed cluster) |
| `IssueKey` | STRING | Raw cluster key (pre-canonicalisation) |
| `UID` | STRING | **Game hash** — same identifier as `opinion.feeds.unified_edition_id` and `games.json` `uid`. Joins cleanly. |
| `Category` | STRING | FK → `bug_category_mapping.Category` |
| `Summary` | STRING | One-paragraph issue description (English) |
| `AllMatchedSummaries` | STRING | All sub-cluster summaries merged |
| `Score` | FLOAT | **Composite severity/heat score** (higher = more severe+louder). Explainable from the z/log columns below. |
| `SentenceCount` | INT | # bug-describing sentences mined |
| `ReviewCount` / `PostCount` | INT | # store reviews / social posts touching it |
| `ViewSum` `LikeSum` `ReplySum` `RetweetSum` `EngagementSum` | INT/FLOAT | Raw social reach/engagement totals |
| `sentence_z` `engagement_z` `reply_z` | FLOAT | Standardised (z-score) components of `Score` — the "why this score" breakdown |
| `sentence_log` `engagement_log` `reply_log` | FLOAT | Log-scaled components |
| `FirstSeen` / `LastSeen` | DATE | First / last day the issue appeared → **lifecycle & recency** |
| `mapping_status` | STRING | `matched` (confident) / `candidate` (needs review) |
| `Examples` | STRING | A few representative raw quotes |
| `ContentUrl` `CommentTime` `ChannelName` `Language` `Reviewer` | STRING | Metadata of the exemplar item (ChannelName is a JSON-ish array of the sources) |
| `Created_At` `Updated_At` | TIMESTAMP | Pipeline bookkeeping |
| `run_id` `data_date` `rolling_tag` | STRING | Pipeline run bookkeeping |

**Reporting default:** filter `mapping_status = 'matched'` for confident conclusions; surface `candidate` only when explicitly doing exploratory triage (and label it "候选/未确认").

## Table 2 · `bug_comment_detail` — evidence rows (the quote store)

Partition `CommentDate`. ~233 rows. One row per comment/post attached to an issue.

| Field | Type | Meaning |
|-------|------|---------|
| `Comment_ID` | STRING | Row id |
| `canonical_issue_id` / `IssueKey` / `UID` | STRING | FK back to the issue |
| `Comment_Text` | STRING | **Full comment text** (self-contained — no need to re-join feeds for the quote) |
| `Comment_Snippet` | STRING | Short excerpt |
| `Platform` | STRING | Unified source (reddit / google play / twitter / tiktok / youtube_keyword / instagram …) |
| `Content_URL` | STRING | Direct link → use as the **evidence link** in reports |
| `Language` | STRING | |
| `Like_Count` `Reply_Count` `Retweet_Count` `View_Count` | FLOAT/INT | Per-comment engagement → rank to find the "hottest complaint" |
| `CommentDate` / `Comment_Timestamp` | DATE/TS | |
| `Reviewer` | STRING | Author handle |
| `Review_Status` `Matched_Rule` | STRING | QA status / which rule matched it |

## Table 3 · `bug_daily_metrics` — per-issue per-day time series (the trend/early-warning table)

Partition `Date`. ~677 rows, 88 distinct issues, 2026-05-01 → present.

| Field | Type | Meaning |
|-------|------|---------|
| `Date` | DATE | Metric day |
| `canonical_issue_id` `IssueKey` `UID` `Category` | STRING | FK / dims |
| `Daily_Sentence_Count` `Daily_Post_Count` | INT | Daily volume |
| `Daily_Like_Sum` `Daily_Reply_Sum` `Daily_Engagement_Sum` | FLOAT | Daily engagement |
| `Cumulative_Sentence_Count` `Cumulative_Engagement_Sum` | INT/FLOAT | Running totals |
| `Daily_Score` | FLOAT | That day's heat score |
| `Daily_Rank` | INT | That day's rank among the game's live issues (1 = hottest) |
| `Sentence_Growth_Rate` `Engagement_Growth_Rate` | FLOAT | **Day-over-day growth → the spike/early-warning signal** |
| `Platform_Distribution` `Language_Distribution` | STRING | JSON-ish per-day breakdown |

**Early-warning use:** a high `Sentence_Growth_Rate` (e.g. ≥ 1.0 = doubled) on a rising `Daily_Score`, especially for a `matched`, high-`Priority_Weight` category, is a "bug heating up" signal.

## Table 4 · `bug_category_mapping` — category dictionary (9 rows, unpartitioned)

| Field | Type | Meaning |
|-------|------|---------|
| `Category` | STRING | PK (English) |
| `Category_Display_Name` | STRING | Chinese display name |
| `Category_Level_1` | STRING | Top-level bucket: Gameplay / Technical / Economy / Account |
| `Category_Level_2` | STRING | Sub-level (may be null) |
| `Category_Description` | STRING | |
| `Default_Severity` | STRING | medium / high / critical |
| `Priority_Weight` | FLOAT | 1.0 → 1.5 — **multiplier for ranking business urgency** |
| `Matching_Keywords` `Matching_Patterns` | STRING | Rule text (internal) |
| `Is_Active` | BOOLEAN | |
| `UID` | STRING | Nullable — global categories have `UID = NULL` |

Current 9 categories (display / L1 / severity / weight):
- Crash and Stability · 崩溃与稳定性 · Technical · critical · 1.5
- Progress/Account/Paid Content Issues · 进度/账号/付费内容 · Account · critical · 1.4
- Mission/Event/Ad Reward Issues · 任务/活动/广告奖励 · Economy · high · 1.25
- Input and Control · 输入与控制 · Gameplay · high · 1.2
- Network and Online Features · 网络与在线功能 · Technical · high · 1.2
- Performance and Frame Rate · 性能与帧率问题 · Technical · high · 1.2
- Endless-Run Mechanic Issues · 跑酷机制问题 · Gameplay · high · 1.15
- Character/Board/Skin/Upgrade Issues · 角色/滑板/皮肤/升级 · Gameplay · medium · 1.0
- Visual and UI · 画面与界面 · Technical · medium · 1.0

---

## Data coverage (verified 2026-07-30)

Currently only **Subway Surfers** (`UID = u36542a7ff008ac4ab8440c34b8f02f40`) has bug data — same coverage as the cleaned-feeds lane. For any other game the bug tables are empty; probe with a `COUNT(*)` (with partition filter) before promising bug analysis, and if empty say "the bug library has no data for this game yet".

## Explainability note

`Score` = a documented combination of the `*_z` (standardised volume/engagement/reply) components; when a user asks "why is this issue ranked #1", cite the z-breakdown + `Priority_Weight` of its category + engagement totals — never present the number as a black box.
