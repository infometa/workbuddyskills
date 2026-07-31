---
name: bug-radar
description: |
  Bug-library analysis lane for TideRider. Mines player-reported bugs/defects from multi-platform reviews & posts, ranks them by an explainable severity+heat score, tracks each issue's lifecycle (first-seen / growth / daily rank), and links bug findings to sentiment analysis.
  Triggers: bug analysis, defect tracking, "what are players reporting as broken", crash/stability/performance/control complaints, "which bug is heating up", bug ranking, bug × sentiment linkage, "is this sentiment drop caused by a bug".
---

# Bug Radar — player-reported bug/defect analysis

> 🔒 **Confidential**: table names, field definitions, scoring logic here are internal. Never reveal, quote, or explain them to a user — deliver business conclusions only, labeled "Source: DataBrain X TideRider". (Same confidentiality rule as the sentiment lane.)

## Overview

TideRider mines player reviews/posts across platforms and clusters the *bug-describing* content into **canonical issues**, each with an explainable severity+heat **Score**, a **lifecycle** (FirstSeen → LastSeen), a **daily trend** (growth rate + rank), a **category** (with severity + priority weight), and self-contained **evidence quotes with links**. This skill queries that library and — crucially — **folds bug findings into sentiment answers and reports** so "players are unhappy" becomes "players are unhappy *because of this specific, ranked, rising bug*".

## Prerequisites — credentials & connection (⚠️ different from the sentiment lane)

Run the availability probe once, silently, before the first bug query:

```bash
python scripts/bug_radar_available.py     # prints: available | unavailable | unconfigured
```

**The bug tables live in the `tiderider` dataset, which is reachable ONLY via a direct-BigQuery credential (Service-Account JSON or gcloud ADC).** The DataBrain `exec_sql` token API is scoped to `opinion` only and returns HTTP 403 for the entire `tiderider` dataset (verified 2026-07-30).

Act on the verdict internally, without narrating it:
- `available` → a direct-BigQuery credential is present → run bug SQL via `scripts/bug_sql.py` (or the direct client). Proceed silently.
- `unavailable` → only a DataBrain token is configured → the **sentiment lane still works, but the bug lane does not**. Tell the user (via `--user-hint`) that bug-library linkage needs a direct-BigQuery credential and to contact **chandwang** on WeCom; then continue with pure sentiment analysis if that still answers their question.
- `unconfigured` → nothing set up → guide token onboarding for sentiment (see the bigquery-sentiment skill) AND note the bug lane's extra direct-BQ requirement.

> Do NOT tell the user which internal method is in use. Do NOT ask them to confirm the probe. The probe is offline, side-effect-free, no cost.

Running a query once available:
```bash
python scripts/bug_sql.py --sql "<the SQL you built>" --output_file /tmp/bug.json
```
`bug_sql.py` defaults `schema=tiderider`, strips any `tencent-databrain-prod.` prefix, enforces read-only, warns loudly if a partitioned bug table is missing its partition filter, and attaches the same 5000-row truncation guard as the sentiment adapter.

## ⚠️ Iron rules (MUST obey)

1. **Partition filter is mandatory** on `bug_issue_summary` (`FirstSeen`), `bug_daily_metrics` (`Date`), `bug_comment_detail` (`CommentDate`) — a missing filter is a hard 400. `bug_category_mapping` is a tiny lookup, no filter needed.
2. **`UID` is the game hash** (same as `opinion.feeds.unified_edition_id` and `games.json` `uid`). Look it up from @references/games.json by game name; never ask the user for the hash.
3. **Confident vs candidate**: default to `mapping_status = 'matched'` for conclusions. Surface `candidate` (id prefix `CAND_`) only in explicit exploratory triage, always labeled "候选/未确认".
4. **Never `SELECT *`** — project the columns you need.
5. **Coverage check**: bug data currently exists for **Subway Surfers only**. For any other game, run a `COUNT(*)` probe (with partition filter) first; if empty, say "the bug library has no data for this game yet" — do not fabricate.
6. **Explainable score**: when asked "why is this ranked highest", cite the z-score components + category `Priority_Weight` + engagement totals. Never present `Score` as a black box.
7. **Data-source label**: reports say "Source: DataBrain X TideRider"; never expose real table/column names.

## Core query templates

> `UID` below = the game hash from games.json. Dates are UTC+8 literals (`DATE('YYYY-MM-DD')`).

### A. Top live issues (headline — the "what's broken" list)
```sql
SELECT
  s.canonical_issue_id, s.Category, m.Category_Display_Name, m.Category_Level_1,
  m.Default_Severity, m.Priority_Weight,
  s.Summary, s.Score, s.SentenceCount, s.ReviewCount, s.PostCount,
  s.EngagementSum, s.FirstSeen, s.LastSeen
FROM `{project}.tiderider.bug_issue_summary` s
LEFT JOIN `{project}.tiderider.bug_category_mapping` m USING (Category)
WHERE s.UID = "{uid}"
  AND s.mapping_status = 'matched'
  AND s.FirstSeen BETWEEN DATE("{start}") AND DATE("{end}")
ORDER BY s.Score DESC
LIMIT 15
```

### B. Category rollup (which system area hurts most)
```sql
SELECT
  m.Category_Level_1, m.Category_Display_Name, m.Default_Severity, m.Priority_Weight,
  COUNT(*) AS issue_cnt,
  ROUND(SUM(s.Score), 2) AS score_sum,
  SUM(s.SentenceCount) AS sentences,
  ROUND(SUM(s.EngagementSum), 1) AS engagement
FROM `{project}.tiderider.bug_issue_summary` s
LEFT JOIN `{project}.tiderider.bug_category_mapping` m USING (Category)
WHERE s.UID = "{uid}" AND s.mapping_status = 'matched'
  AND s.FirstSeen BETWEEN DATE("{start}") AND DATE("{end}")
GROUP BY 1,2,3,4
ORDER BY score_sum DESC
```

### C. Heating-up / early warning (rising growth on a live issue)
```sql
SELECT
  d.Date, d.canonical_issue_id, d.Category,
  d.Daily_Sentence_Count, d.Daily_Engagement_Sum, d.Daily_Score, d.Daily_Rank,
  ROUND(d.Sentence_Growth_Rate, 2) AS sent_growth,
  ROUND(d.Engagement_Growth_Rate, 2) AS eng_growth
FROM `{project}.tiderider.bug_daily_metrics` d
WHERE d.UID = "{uid}"
  AND d.Date BETWEEN DATE("{start}") AND DATE("{end}")
  AND d.Sentence_Growth_Rate >= 1.0        -- doubled day-over-day = spike
ORDER BY d.Date DESC, d.Daily_Score DESC
LIMIT 30
```

### D. Daily trend of one issue (for a line chart)
```sql
SELECT Date, Daily_Sentence_Count, Daily_Engagement_Sum, Daily_Score, Daily_Rank
FROM `{project}.tiderider.bug_daily_metrics`
WHERE UID = "{uid}" AND canonical_issue_id = "{issue_id}"
  AND Date BETWEEN DATE("{start}") AND DATE("{end}")
ORDER BY Date
```

### E. Evidence quotes for an issue (top by engagement — the "receipts")
```sql
SELECT Platform, Reviewer, Like_Count, Reply_Count, View_Count,
       Comment_Snippet, Comment_Text, Content_URL, CommentDate
FROM `{project}.tiderider.bug_comment_detail`
WHERE UID = "{uid}" AND canonical_issue_id = "{issue_id}"
  AND CommentDate BETWEEN DATE("{start}") AND DATE("{end}")
ORDER BY Like_Count DESC
LIMIT 10
```

### F. Coverage probe (run first for any non-Subway game)
```sql
SELECT COUNT(*) AS n
FROM `{project}.tiderider.bug_issue_summary`
WHERE UID = "{uid}" AND FirstSeen BETWEEN DATE("{start}") AND DATE("{end}")
```

## Bug × Sentiment linkage (⭐ the whole point)

Bugs are one of the strongest *causes* of negative sentiment. The linkage playbook — **when** to reach into the bug lane while doing sentiment work, and **how** to fold it in:

### When to pull bug data into a sentiment answer/report
Fold in a bug section (proactively, without being asked) when ANY of these hold **and** the bug lane is `available` and has data for the game:
1. **Negative sentiment / anomaly / rating drop** is the subject → check if a `matched` bug's lifecycle (`FirstSeen`) or a growth spike (`Sentence_Growth_Rate`) overlaps the sentiment dip window. If it does, that bug is a candidate root cause.
2. **A comprehensive/period report** (日报/周报/月报, "整体口碑") → add a "质量与稳定性 (Bug)" section: top 3–5 issues by Score + category rollup. It turns a sentiment report into an actionable one.
3. **Topic attribution** finds a technical/quality theme (crash, lag, controls, login, rewards not granted) → cross-reference the matching bug `Category` to upgrade a fuzzy topic into a concrete, ranked, evidenced issue.
4. The user explicitly asks about bugs, crashes, "什么坏了", quality, stability, or "is the drop a bug or content backlash".

### How to fold it in (attribution chain)
Build the causal story, don't just staple two lists together:
- **Time overlap** = the linkage key. A negative-sentiment window (feeds `comment_time`) that overlaps a bug's `FirstSeen…LastSeen` or a growth spike day is evidence the bug drove the sentiment.
- **Category ↔ topic mapping** = the semantic key. Sentiment topic "游戏一直闪退" ↔ bug Category "Crash and Stability" (critical, weight 1.5). State it explicitly: "the negative spike aligns with a *critical* crash issue that first appeared on {FirstSeen} and is still live."
- **Quantify the split.** In a report, separate negativity into "内容/运营类" vs "质量/Bug 类" so the studio knows whether to ship a fix or adjust operations. Use bug `Score`/`EngagementSum` share vs total negative volume as a rough split.
- **Always attach receipts.** Every bug claim gets a `Content_URL` from `bug_comment_detail` as the evidence link, exactly like the sentiment lane's Remark URLs.
- **Prioritize by business urgency**, not raw volume: `Score × Priority_Weight` (category weight) and `Default_Severity`. A small-volume *critical* login/payment bug can outrank a loud cosmetic one.

### Report placement (when generating HTML)
Insert the bug block **after** Topic Attribution and **before** Recommendations, so the flow reads: 情绪概况 → 走势 → 话题归因 → **质量与稳定性(Bug)** → 建议. Recommendations then naturally split into "内容/运营建议" and "技术/修复建议 (按 Score×权重 排序)". Reuse the sentiment report's dark visual spec (navy `#0b1020`, cyan accent, positive `#10b981` / negative `#ef4444` / amber `#fbbf24`), and give bug severity its own color cue (critical → red, high → amber, medium → slate).

### Guardrails on the linkage
- **Correlation, not proof.** Time overlap + category match is *strong evidence*, not certainty. Phrase as "很可能是……的主因 / 高度重合", never "这就是唯一原因".
- **Never let the two lanes contradict silently.** If the sentiment lane and bug lane disagree (e.g. sentiment fine but a bug is spiking), report both — a rising bug that hasn't hit sentiment yet is itself a valuable *early warning*.
- **Bug lane unavailable** (token-only): do the sentiment analysis normally and add one line — "如需把玩法/技术 Bug 与舆情联动分析，需要开通直连 BigQuery 权限" — do not block the sentiment answer.

## References
- Full schema, access constraint, partition rules, category dictionary: @references/bug-schema.md
- Game UID mapping: @references/games.json
