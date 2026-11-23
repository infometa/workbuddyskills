---
name: sparkx-weekly-ads-report
description: >-
  Generate a weekly ad performance recap report for ads ops / customer-facing teams to use every Monday.
  Includes a KPI card (with WoW comparison), 7-day trend, anomaly summary, top-mover lists, and next-week
  action recommendations. Use when the user says "出个周报", "周复盘", "上周表现如何", "weekly report".
  Not for monthly/quarterly reports (use sparkx-monthly-ads-report / quarterly-ads-report, not yet built),
  nor for deep-dive analysis on a specific question (use the relevant analysis skill instead).
metadata:
  version: 1.1.4
---

# Weekly Ads Report

## Scope: This Is an Orchestration Skill, Not a New MCP Tool

This skill does **not** map to a single MCP tool of its own — it orchestrates three existing read tools, each already covered by its own skill:

- `get_ads_perf` → [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md)
- `get_operation_log` → [sparkx-query-operation-log](../sparkx-query-operation-log/SKILL.md)
- `get_entity_metadata` → [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md)

> **Dependency — install these three base skills alongside this one:** `sparkx-query-ads-performance`, `sparkx-query-entity-metadata`, `sparkx-query-operation-log`. Skills install as sibling directories under your current agent's skills root (`.claude/skills/<name>/` for Claude Code; the equivalent root for other agents — see the installation notes in [README](../README.md)), which is exactly what the `../query-.../…` links above (and elsewhere in this doc) resolve against — if a base skill isn't installed there, those links won't resolve and this skill can't run. Install all three first.

**Read those three SKILL.md files first** (parameter formats, field-naming rules, the Ratio Metric Display Rule) plus [`references/platform-notes.md`](references/platform-notes.md) (auth flow, error handling, pagination, date-range limits, currency rules — shared by all three underlying tools). This document only covers logic specific to the weekly-report use case; it doesn't repeat what the three base skills already document.

## Output Language: Always Match the User, Never Hard-Code Chinese or English

**The worked examples and output templates below are written in Chinese** (matching this product's primary customer base), but they are **structural illustrations, not literal text to copy verbatim**. Generate the actual report in whatever language the user asked in — section headers, KPI labels, the one-line summary, everything. A customer who asks in English should get an English report with English headers ("Weekly KPI Overview", not "本周 KPI 概览"); a customer who asks in Japanese should get one in Japanese. Do not assume the audience is Chinese-speaking just because this skill's own documentation and templates are.

When calling `get_ads_perf`, also set the `language` parameter (`zh`/`en`/`ja`) to match the customer's language — this controls the human-readable enum companion text the tool returns (e.g. `campaignTypeText`, `targetMatchTypeText`), so a customer reading an English report doesn't see a Chinese enum label embedded in an otherwise-English table. **`get_entity_metadata` has no `language` parameter** — it's not in that tool's documented parameter list. Localize its enum values using the returned `{field}Text` companion fields, or `sparkx-query-entity-metadata`'s own [`enum-i18n.md`](../sparkx-query-entity-metadata/references/enum-i18n.md) if a given enum has no `Text` companion — don't pass `language` to `get_entity_metadata` expecting it to have the same effect as on `get_ads_perf`.

## When to Use

**Trigger phrases**: 周报, 周复盘, 上周表现, weekly report, recap last week, 周会材料

**User roles**: ads ops, customer-facing AM/CSM

**Core question**: what happened last week, what to do this week

**Not for**:
- Monthly/quarterly view → `sparkx-monthly-ads-report` / `quarterly-ads-report` (not yet built)
- A specific question the user brings ("is my SBV structure right") → `sparkx-ads-structure-analysis`
- Day-level monitoring → a dedicated alerting skill (not yet built)

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `profileIds` | array[long] | No | — | Target profile IDs. See "Resolving `profileIds`" below for the exact selection rules — don't default to "all stores" without checking those rules first |
| `weekEnding` | date (`YYYY-MM-DD`) | No | Last Sunday (local timezone) | The end date (Sunday) of the week this report covers |
| `compareBaseline` | enum | No | `wow` | `wow` \| `wow+4w_avg` (the latter also compares against the trailing-4-week average) |
| `outputFormat` | enum | No | `markdown` | `markdown` \| `structured_report` |
| `includeAiSection` | `bool` \| `"auto"` | No | `auto` | Whether to include an AI-managed summary section (`auto` = include if the store has AI management enabled) |

### Resolving `profileIds`

Always call `get_user_authorized_context` first to get the authorized `profiles` list, then apply exactly one of these cases:

1. **The user named specific store(s)** ("Demo US", "my UK store") → resolve the name(s) against the authorized list and query only the matching profile(s).
2. **The user explicitly said "all stores" / "全账号" / equivalent** → query all authorized `profileIds`.
3. **The user didn't name a store, and there's only one authorized profile** → use it directly. There's nothing to ask — one option is not a choice.
4. **The user didn't name a store, and there are multiple authorized profiles**:
   - **5 or fewer** → you may default to using all of them.
   - **More than 5** → do not silently roll everyone up into one report. Hand the user the `profiles` list and ask them to pick one, several, or explicitly confirm "all stores" before proceeding.

Case 4's threshold exists because this is a customer-facing report, not an internal dashboard: a silent multi-store aggregate can hide a single store's problem behind a healthy-looking blended number, and it forces an unannounced USD conversion (see "Multi-Store and Currency" below) the customer didn't ask for.

**Determining `includeAiSection=auto`**: call `get_entity_metadata` (`entity: aiGroup`, filtered to the relevant `profileIds`; **add `filters: {"aiStatus": 1}`, or fully paginate — default page size is 100, so an account with more managed groups than one page could otherwise have its only running group sitting past page 1 and be missed**). If any returned row has `aiStatus: 1` (running), include the full AI-managed summary section. If none are currently running but Step 2f's change summary still shows managed-group (AI) activity for the week (a group may have been toggled off partway through), include a brief one-line mention instead of a full section — the activity is still worth surfacing, just not as prominently as an actively-running group.

## Shared Rules: Target ACOS, Thresholds, Managed Groups, Promotions

These rules match `sparkx-search-term-diagnosis` and `sparkx-promo-reset`, so the same store
gets the same numbers whichever skill answers. Those two skills are separate installs: mention
them as "if installed", and when the user doesn't have them, say what to look at instead -
never promise to run a skill that may not be there.

- **One target ACOS.** Use the store-wide target the user gives (ask "整店希望 ACOS 控制在多少"
  when a threshold depends on it); without one, use the store's own ACOS for the period and say
  so where the threshold is first used. Never use managed groups' `targetAcos` as thresholds -
  one store can have dozens, from single digits to over 200%, and rank-push or launch groups set
  it high on purpose.
- **"High spend, zero orders" means spend >= `T`**, where `T` = average order value x target
  ACOS = `(Sales / Conversions) x target ACOS` over the report's scope and period (target ACOS as
  a fraction: `get_ads_perf`'s `ACOS` value `35` is `0.35`). `T` is one order's allowed spend -
  the entity already spent what an order may cost and got none. It works in every currency and
  price range, so there is no fixed money floor. No orders or no sales in the period -> `T`
  can't be derived; say so instead of flagging.
- **Campaigns in a running managed group get group-level advice.** A campaign's group is
  `campaign.aiGroupId_` in `get_ads_perf` (or `aiGroupId` on `get_entity_metadata`'s `campaign`
  entity; an unmanaged campaign has `0`); the group's `aiStatus` comes from
  `get_entity_metadata` (`entity: aiGroup`). The AI sets those campaigns' bids and budgets, so a
  manual bid or budget change gets overwritten: recommend the group's levers instead (target
  ACOS, group budget, an action-space switch) or say the AI is handling it. **No bid advice with
  numbers anywhere**; for an unmanaged campaign give at most a direction ("consider lowering
  bids on ..."). Keyword-level actions (pausing a zero-order exact keyword, negatives) need
  keyword and search-term data - point to `sparkx-search-term-diagnosis` (if installed).
- **People vs machines in the operation log.** Query without `changeBy` and classify
  `changedBy` client-side: an email or `Manual` is a person. **`Amazon Console` says where a change came from, not who made it** - Amazon's side. Report it as an Amazon-side change, not as a person. Everything else
  (`AI`, `Automation`, `AI-Custom Rule`, `Budget Management`, `Lock Ranking`, `API`, `Labels`,
  `System`) is a machine. **`changeBy=manual` is rejected by the server** (case-insensitive, in `IN`, `NOT_IN` or mixed) — it was a UI category, not an operator, and never covered changes recorded under a user's email. Inside
  managed groups the AI moves `currentBudget` every hour and those rows are also
  `Budget Increased` - leave them out of counts and "what changed" lists (a person's budget
  change is on `dailyBudget`). Group setting changes (target ACOS, personality, switches) are
  `aiGroup` rows, not campaign rows; their timestamps are UTC, while campaign rows are
  store-local when one profile is queried - label the clock.
- **Promotions distort period comparisons - but only the user confirms one.** Signals that
  one may be involved: the period or its baseline overlaps a major event (Prime Day, Prime Big
  Deal Days, Black Friday / Cyber Monday), or the operation log shows a burst of human budget /
  bid increases in or shortly before it. A signal is not a verdict: still report every anomaly
  and decline, label the affected ones "possibly promotion-related", and ask the user. Only
  after the user confirms, say so at the top and treat the swing as promo-driven. After a
  confirmed promotion whose human increases haven't been reversed, mention that
  `sparkx-promo-reset` (if installed) restores them.

## Workflow

### Step 1 · Define Time Windows

- **This week**: `[weekEnding − 6d, weekEnding]` (7 days inclusive)
- **Last week**: `[weekEnding − 13d, weekEnding − 7d]`
- **4-week average baseline** (when `compareBaseline=wow+4w_avg`): trailing **weekly** average over `[weekEnding − 34d, weekEnding − 7d]` (28 days = 4 weeks) — see Step 2g and Step 3 for why this must be a weekly figure, not a daily one

These three windows are 7 / 7 / 28 days respectively — all comfortably within `get_ads_perf`/`get_operation_log`'s 90-day single-call cap, so no window-splitting is needed.

**⚠️ T+2 data-delay check (matters especially because this report is meant to run every Monday)**: ad performance data has a T+2 processing delay. If `weekEnding` (default: last Sunday) is less than 2 days before today — e.g. the report runs Monday morning and `weekEnding` is yesterday or the day before — the last 1-2 days of "this week" may not have finished processing yet. Check the gap between `weekEnding` and today before generating the report; if it's under 2 days, add an explicit note at the top of the report ("the last X day(s) of this week's data may not be fully processed yet and could shift slightly") rather than presenting an incomplete number as final.

### Step 2 · Pull Data

The calls below are independent and can be issued in parallel. Every call needs `userContext` (non-empty string, ≤100 chars). None of them add a `campaign.campaignState_` filter — the WoW comparison needs to see a campaign that was running last week but paused this week (see Step 5); adding a state filter would make that campaign disappear from both periods instead of showing up as a real finding.

**a. This week, daily granularity (account-level trend)**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "dateStart": "{this Monday}",
  "dateEnd": "{weekEnding}",
  "select": ["date"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions", "ACOS", "ROAS", "CTR", "CVR"],
  "pageSize": 500,
  "userContext": "Weekly report - this week's daily trend"
}
```
No campaign dimension in `select` — just `["date"]` — gives account-level daily totals across all campaigns, blended across every profile in `profileIds`.

**⚠️ Overall trend vs. per-store trend — don't blend these two shapes.** The call above (`select: ["date"]`) is for the single blended trend line covered by "## 2. 7-Day Trend" below. If the customer instead wants to see **each store's trend separately** (not one blended line), that's a different call: add `profile.profileId_`/`profile.profileName_` to `select` alongside `date` — but doing so changes the row granularity from **one row per day** to **one row per day × per profile**. Don't apply the "Multi-Store and Currency" section's advice to add `profile.profileId_` to *this* call by reflex when you actually want the single blended trend — that advice is for the campaign-level calls (c/d) where per-store attribution is the point; here it would silently fragment the trend into N per-store lines instead of the one overall line the KPI section expects. If you need both, issue both shapes as separate calls rather than trying to compute one from the other after the fact.

**b. Last week, daily granularity** — identical shape, `dateStart`/`dateEnd` shifted back to last week's window.

**c. This week, campaign-level (feeds Top Movers)**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "dateStart": "{this Monday}",
  "dateEnd": "{weekEnding}",
  "select": ["campaign.campaignId_", "campaign.campaignName_", "campaign.aiGroupId_"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions"],
  "pageSize": 500,
  "userContext": "Weekly report - this week's campaign performance for WoW comparison"
}
```
**`select` must include `campaign.campaignId_`** (not just the name) — Step 5 joins by ID, not name. `campaign.aiGroupId_` tells Step 6 which campaigns sit in a managed group. Response keys drop the prefix and the trailing `_` (`campaign.campaignId_` comes back as `campaignId`) - normalize with `key.rsplit('.', 1)[-1].rstrip('_')` before joining.

**d. Last week, campaign-level** — same shape as c, `dateStart`/`dateEnd` shifted back a week; everything else (`select`/`metrics`/filters) must match c exactly, or the two periods aren't comparable.

**e. This week, Top 10 ASINs**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "asin",
  "dateStart": "{this Monday}",
  "dateEnd": "{weekEnding}",
  "select": ["asin.asin_", "asin.asinTitle_"],
  "metrics": ["TotalSalesAmount", "OrderCount", "TACOS"],
  "orderBy": [{"field": "TotalSalesAmount", "direction": "DESC"}],
  "pageSize": 10,
  "userContext": "Weekly report - top 10 ASINs by sales"
}
```
**When `profileIds` spans more than one store, decide which of two different questions you're actually answering — the same call doesn't serve both:**

- **One cross-store blended Top 10** ("top 10 ASINs by sales across all these stores combined"): do **not** add `profile.profileId_` to `select` — same as the single-store call above, `factEntity: asin` with `select: ["asin.asin_", "asin.asinTitle_"]` already aggregates `TotalSalesAmount` across every profile in `profileIds` per ASIN, and `orderBy`+`pageSize:10` gives you the correct blended top 10 directly.
- **Each store's own Top 10** ("top 10 ASINs per store"): add `profile.profileId_`/`profile.profileName_` to `select`. This changes the grouping to ASIN × profile, and **`orderBy`+`pageSize:10` at that point returns the top 10 ASIN×profile combinations *overall*** (by global rank across every store's ASINs mixed together) — it does **not** give you 10 rows for each store. To get a genuine per-store Top 10, either issue one call per `profileId`, or raise `pageSize` enough to pull the full set and then group by `profile.profileId_` client-side, sorting and truncating to 10 within each group.

Don't reach for `profile.profileId_` by default "for attribution" here — decide which of the two questions above the customer actually asked first.

**f. This week's change summary** (using `get_operation_log`, which is real — not a subscription alert feed)
```json
{
  "profileIds": [4404871489220462],
  "dateStart": "{weekEnding − 20d}",
  "dateEnd": "{weekEnding}",
  "pageSize": 200,
  "userContext": "Weekly report - changes this week, last week and the week before"
}
```
The window covers this week, last week (the baseline) and 7 days before it, so a promotion
signal in the baseline or its lead-in is visible. The change summary in Step 4b shows **this
week's** rows only; the earlier rows are used only for the promotion signal.
No `changeBy`: classify `changedBy` client-side into people and machines, and drop the AI's hourly `currentBudget` rows, per "Shared Rules" above. **Check `truncated`**: if `true`, the queried operation-log window (21 days) had more than 200 ops — follow `sparkx-query-operation-log`'s "Getting a Complete Count" procedure (split into non-overlapping sub-windows and recurse) before summing; don't treat this one page as the full window.

**Step 2f as a whole is best-effort, not a hard dependency for the rest of the report.** If splitting into sub-windows is still timing out, or the call keeps erroring, don't let it block Steps 3/5/6 (KPI overview, Top Changes, action recommendations) from completing. Produce the rest of the report normally and mark this section explicitly as "change history incomplete for the queried window" (or similar, in the report's own language) rather than failing the entire report over one section.

**g. 4-week average baseline** (only when `compareBaseline=wow+4w_avg`)
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "dateStart": "{weekEnding − 34d}",
  "dateEnd": "{weekEnding − 7d}",
  "select": ["date"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions"],
  "pageSize": 500,
  "userContext": "Weekly report - trailing 4-week average baseline"
}
```
Same shape as call (a) (account-level, `date`-only `select`), just a 28-day window instead of 7.

**Only these 5 base metrics are requested — deliberately no `ACOS`/`ROAS`/`CTR`/`CVR` in this call.** Sum each across the 28 days, then divide by 4 (not 28) to get a trailing-4-week *weekly* average. Dividing by 28 would give a *daily* average, which is not directly comparable to "this week"'s 7-day total (that mismatch would make a perfectly flat week look like a several-hundred-percent spike) — both figures compared in Step 3 must be on the same "per week" scale.

**Then recompute the ratio metrics from those summed base metrics** using the standard formulas — `ACOS = Spend/Sales×100`, `ROAS = Sales/Spend`, `CTR = Clicks/Impressions×100`, `CVR = Conversions/Clicks×100`. Ratio metrics were left out of `metrics` above specifically so there's no 28-daily-values version of them lying around to be misused — summing or averaging 28 individual days' ACOS/ROAS/CTR/CVR is never valid (same principle as never averaging pre-computed ratios across a split window — see the aggregation-over-time example in `sparkx-query-ads-performance`), so don't request them here in the first place. Whether you apply the formulas to the raw 28-day sums or to the ÷4 weekly averages makes no difference to the result (the formulas are scale-invariant).

Skip this call entirely when `compareBaseline=wow` (the default) — don't issue it if the report doesn't need it.

### Step 3 · Compute Core Metrics

**Total KPIs (8)**: Spend, Sales, ACOS, ROAS, Impressions, Clicks, CTR, CVR

**For each**: this-week value, last-week value, WoW % (`(this week − last week) / last week × 100`; undefined when last week is 0 — see below), direction arrow (↑↓ + color in a rendering context that supports them; in a plain-text-only context — e.g. a CLI that won't reliably render emoji or color — spell it out as "up"/"down"/"flat" instead)

**When `compareBaseline=wow+4w_avg`**: additionally include the trailing-4-week **weekly** average from Step 2g and a `vs. 4-week avg` % computed the same way as WoW (`(this week − 4-week avg) / 4-week avg × 100`, same zero-denominator handling). Per Step 2g: the 5 base metrics use 28-day sum ÷ 4 (**not** ÷ 28, which would be a daily figure not comparable to this week's 7-day total); the ratio metrics (`ACOS`/`ROAS`/`CTR`/`CVR`) are **not** divided by anything directly — they're recomputed from those summed base metrics via their standard formulas. Add the baseline as a third column alongside This Week / Last Week in both output templates below — don't compute this baseline without displaying it, and don't display the column without actually computing it.

**Ratio-metric display rule** (same rule shared across the three base skills): confirmed percentage metrics such as `ACOS`, `CTR`, `CVR`, `TACOS`, and the derived `*Rate` metrics explicitly listed in Platform Notes are pre-scaled ×100 (the tool returns `17.61` meaning 17.61%) — **append `%` directly, do not multiply/divide by 100 again**. Do not infer an unlisted field's scale from its name alone; `ROAS`/`CPC`/`CPA` are not percentages, they're plain ratios/unit-costs — no `%`.

**"Significant change" thresholds** (used for the initial screen in Step 5's Top Changes section — not the final sort criterion, which still follows Step 5's full procedure):
- Spend WoW absolute value ≥ 20%
- ACOS WoW absolute value ≥ 15%
- Last week's spend < 5% of last week's average spend → treat as too small to matter; apply Step 5's denominator floor to filter this out, so tiny-base noise doesn't get reported as a "spike"

### Step 4 · Identify Anomalies

**There is no independent alert/subscription data source** — `get_operation_log` is a change-history query tool, not a subscription-based alerting system; there is no `log_type=alert` parameter. Anomaly identification is entirely built from these two pieces:

**a. Built-in rule scan over this week's campaign data** (using Step 2c's result):
- High spend, zero orders: `Conversions = 0` **and** `Spend >= T` (one order's allowed spend - see "Shared Rules"; `T` comes from this week's account totals and the target ACOS). No fixed money floor.
- `This week's ACOS > last week's ACOS × 1.5 AND this week's ACOS > 30%` → ACOS spike. **Step 2c/2d's `metrics` list doesn't include `ACOS` directly** — compute it per campaign as `Spend/Sales×100` from each period's own `Spend`/`Sales`. **When a campaign's `Sales = 0`**, its ACOS is undefined (division by zero), not "infinite" — exclude that campaign from the ACOS-spike rule entirely rather than computing a fabricated huge number (a zero-Sales, nonzero-Spend campaign is already caught by the high-spend/zero-orders rule above, so it isn't silently missed).
- `This week's Impressions < last week's Impressions × 0.5` → impression collapse

**b. Step 2f's change summary**, in two parts: **people** - every human change on budgets, bids, status and managed-group settings this week (these are what Step 6 correlates with); **machines** - the top 3 action categories (`actionType`/`operationType`, hourly `currentBudget` rows excluded) + the top 3 highest-spend-impact records (cross-reference that campaign's spend from Step 2c). This is a change record, not an anomaly verdict — present it as "what changed this week," not conflated with "anomaly detected."

If neither part turns up anything notable, write "no significant anomalies this week."

### Step 5 · Extract Top Changes (Follow the Period-over-Period Procedure Strictly — Don't Simplify)

**Must follow** [sparkx-query-ads-performance's Period-over-Period and Top Movers example](../sparkx-query-ads-performance/references/example-period-comparison-top-movers.md) in full — don't simplify by intuition. This is the section most prone to error and most likely to be challenged by a customer:

1. **Join by `campaign.campaignId_`, never by name** — names can be duplicated or renamed between periods.
2. **Bucket into three groups before ranking**: new this week (present in Period A only), disappeared (present in Period B only — don't show these as unlabeled zeros), and normal comparisons (present in both). New/disappeared entities have no valid `% change` (division by zero) — don't force them into a percentage leaderboard.
3. **Spend increase Top5**: sort by absolute spend change, floor the population by `max(this week's spend, last week's spend)` — not just this week's value alone — so a campaign that shrank from big to small isn't missed just because its *current* number looks small.
4. **ACOS worsening Top5**: ACOS increase magnitude × spend weight; each period's ACOS is requested/computed independently — never average the two periods' ACOS before computing the change. **If either period's `Sales = 0` for a campaign, its ACOS is undefined for that period** — exclude it from this ranking rather than computing against a zero denominator; a campaign with zero Sales and nonzero Spend belongs in the high-spend/zero-orders anomaly (Step 4) instead, not the ACOS worsening list.
5. **Sales increase Top5**: same treatment as spend increase, positive direction.
6. **The floor for % change goes on last week's (Period B) value, not this week's** — e.g. last week's spend $1 → this week's spend $101 looks like "+10,000%" and is misleading unless floored; the floor must be applied to the prior-period (denominator) value.
7. **Every Top list shows both periods' raw values plus the absolute delta** — not just the percentage, since "+45%" is meaningless without knowing whether that's $10 or $10,000.
8. **If full pagination is impractical at scale** (e.g. `profileIds` spans dozens of stores and paging both periods to `hasNextPage: false` would take many round-trips), you may fall back to a spend-ranked sample: pull only the top N campaigns by `Spend` per period (via `orderBy` + a capped `pageSize`) instead of the full population. **This fallback must be disclosed explicitly in the report** — label the Top Changes section as based on a top-spend sample, not the full population (in whichever language the report is written), and state concretely what was actually covered (how many profiles, how many pages, and whether the underlying calls reported `hasNextPage: true` when you stopped) — never silently present a sampled result as if it were the complete Top Movers analysis.
9. **A degraded or failed Top Changes section must not fail the whole report.** If pagination times out or a call keeps erroring even after retrying/splitting, still produce Steps 3 and 6 (KPI overview, action recommendations) from whatever data did come back, and present the Top Changes section as partial/unavailable rather than aborting report generation entirely.

**Top 10 ASINs this week**: use Step 2e's result directly, no WoW comparison needed (if the customer wants one, pull the same-shape ASIN data for last week and join by ID the same way).

### Step 6 · Generate Next-Week Action Recommendations (3-5 items)

Auto-derive "what to do" from the data above, e.g.:
- Found "high spend, zero orders" on an unmanaged campaign → recommend reviewing it (spent $Y, zero orders, `T` = $Z); if it is an auto / broad / phrase campaign, recommend running `sparkx-search-term-diagnosis` (if installed) to find the terms to negate. In a running managed group → name the group and its lever (target ACOS, negative-targeting switch) instead
- Found "ACOS spike" → recommend investigating Campaign X, citing any human bid / budget / group-setting change from Step 4b in the same window (as correlation)
- Found "sales-growth standout" → recommend "scale Campaign X's structure to similar campaigns"

Follow "Shared Rules" for managed groups: no bid advice with numbers, group-level levers for managed campaigns.

**Every recommendation must have**: action + target (specific campaign/ASIN name) + evidence (data). **Correlation, not causation** — if a recommendation is based on something like "ACOS rose + there was a bid change in the same window," say explicitly that it's a correlation, not "caused by," unless `get_operation_log` has pinpointed the exact change and the timing lines up precisely.

## Multi-Store and Currency

When `profileIds` spans multiple stores:
- All monetary metrics from `get_ads_perf` auto-aggregate to **USD** — any dollar amount in the report should be explicitly labeled "(USD)" so the customer doesn't assume local currency.
- Steps 2c/2d (campaign-level) need `profile.profileId_` (usually also `profile.profileName_`) added to `select`, or multi-store rows can't be attributed to a specific store. Steps 2a/2b (the blended daily trend) and 2g (the blended 4-week baseline) deliberately do **not** get profile fields added — see the warning under Step 2a for why adding them there would change the trend's row granularity instead of just attributing it. Step 2e (Top 10 ASINs) is conditional on which question is being asked — see the two cases spelled out under Step 2e; don't add `profile.profileId_` there by default.
- `asin.asinPrice_` (if used) stays in local currency and is not affected by the USD-aggregation rule above — this report doesn't currently use that field, but note the exception if the report is later extended to include it.

## Output Format

### Naming entities in this report

Nobody reading this report knows an internal id, and the ids `get_ads_perf` returns are
Amazon's anyway. So:

- **Every entity column and every sentence uses the name** — `campaignName`, `adGroupName`,
  `asinTitle`. A `Campaign` column holds a campaign name, never a number.
- **Keep ids in your working data regardless.** Period-over-period joins must be by id,
  because names get duplicated and renamed — that requirement does not change. What changes
  is only what reaches the page.
- **An export gets both.** If the user asked for CSV / Excel / "something I can reconcile",
  add an id column next to the name. The id to publish is the **Amazon** one, which is what
  `get_ads_perf` already gives you.
- In `structured_report` mode the entity/target fields carry the **name**; when ids were
  asked for, add a separate key for the Amazon id rather than gluing both into one string.

Full convention, including the managed-group and product-ad exceptions:
[`references/platform-notes.md`](references/platform-notes.md) -> "Naming things in your
answer".

Remember: **the section headers and labels below are structural placeholders (shown in English here) — always regenerate them in the user's own language**, not copy the English (or any other) wording verbatim (see "Output Language" above).

**Plain-text fallback**: the 🔴/🟡 severity markers and ↑/↓ direction arrows below are for rendering contexts that support them (chat UIs, rendered markdown). In a plain-text-only output context, replace them with words instead — e.g. "High:"/"Medium:" for severity, "up"/"down"/"flat" for direction — rather than relying on a glyph or color the target surface might not render.

### markdown mode (default)

```markdown
# Weekly Ads Report · {profile_name}
**Period**: {week_start} ~ {weekEnding}
**Baseline**: {last week / last week + 4-week average}
{If data may be incomplete due to T+2 delay, add a note here}

## 1. This Week's KPI Overview

{If compareBaseline=wow (default), omit the "4-Week Avg" column entirely — only include it when compareBaseline=wow+4w_avg}

| Metric | This Week | Last Week | WoW | 4-Week Avg | vs. 4-Week Avg |
|---|---|---|---|---|---|
| Spend | ${spend} | ${prev_spend} | {wow%} {arrow} | ${avg4w_spend} | {vs4w%} {arrow} |
| Ad Sales | ${sales} | ${prev_sales} | {wow%} {arrow} | ${avg4w_sales} | {vs4w%} {arrow} |
| ACOS | {acos}% | {prev_acos}% | {wow%} {arrow} | {avg4w_acos}% | {vs4w%} {arrow} |
| ROAS | {roas} | {prev_roas} | {wow%} {arrow} | {avg4w_roas} | {vs4w%} {arrow} |
| Impressions | {imp} | {prev_imp} | {wow%} {arrow} | {avg4w_imp} | {vs4w%} {arrow} |
| Clicks / CTR / CVR | {clk} / {ctr}% / {cvr}% | ... | ... | ... | ... |

**One-line summary**: {a qualitative read auto-generated from the KPI changes, e.g. "Spend up 15% this week, ACOS held steady — healthy growth"}

## 2. 7-Day Trend

{Embed a trend chart or describe key inflection points in text}

**Key inflection points**:
- {date}: {what changed and a possible reason — label as correlation, not confirmed cause, unless verified via get_operation_log}

## 3. This Week's Anomalies / AI-Automation Activity

{If none, write "no significant anomalies this week"}

- 🔴 **{event type}**: {target} - {specific evidence}
- 🟡 **{event type}**: ...

Changes this week: people {M} ({brief list}); AI/automation {N}, hourly budget adjustments excluded ({brief breakdown by actionType})

## 4. Top Changes

### Spend Increase Top5
| Campaign | This Week's Spend | Last Week's Spend | Change |
|---|---|---|---|
| ... | ... | ... | ... |

### ACOS Worsening Top5
{same format as above}

### Sales Increase Top5
{same format as above}

### New / Disappeared Campaigns
{listed separately — not mixed into the three percentage leaderboards above}

### Top 10 ASINs This Week
{table}

## 5. Next Week's Action Recommendations

1. **{action}** {target}
   - Evidence: {data}
2. ...

---
_Generated: {timestamp} · Data source: SparkX AI MCP · Skill: sparkx-weekly-ads-report v{version}_
```

### structured_report mode

Output JSON schema:
```json
{
  "period": {"start": "...", "end": "..."},
  "dataFreshnessWarning": null,
  "kpiCards": [{"metric": "spend", "current": ..., "previous": ..., "wowPct": ..., "fourWeekAvg": null, "vsFourWeekAvgPct": null}],
  "trend": {"daily": [{"date": "...", "spend": ..., "sales": ...}]},
  "anomalies": [{"severity": "...", "type": "...", "entity": "...", "evidence": "..."}],
  "aiAutomationSummary": {"totalOps": ..., "byActionType": {...}},
  "topChanges": {
    "spendUp": [...],
    "acosWorse": [...],
    "salesUp": [...],
    "new": [...],
    "disappeared": [...]
  },
  "topAsins": [...],
  "actions": [{"priority": 1, "action": "...", "target": "...", "evidence": "..."}]
}
```
`kpiCards[].fourWeekAvg`/`vsFourWeekAvgPct` are only populated when `compareBaseline=wow+4w_avg`; leave them `null` for the default `wow` baseline.

## Data Boundaries

- **Paid Sponsored Ads data only** — no DSP, no AMC
- **No year-over-year comparison** — YoY belongs at the monthly/quarterly report level
- **No structural/share-of-spend deep analysis** — that's `sparkx-ads-structure-analysis`'s job
- **Anomaly rules are a lightweight built-in version** — there's no independent deep-alerting subscription capability
- **Cannot reliably compute "real-time remaining budget"** — `dailyBudget`/`currentBudget` are configuration values, not a live spend ledger, and today's `Spend` is usually incomplete due to the T+2 delay. If a customer asks this in the weekly-report context, say plainly it can't be computed reliably — don't present a subtraction as if it were precise.
- **`get_entity_metadata` has no historical-snapshot capability** — if this report needs to show "this week's config vs last week's config" (as opposed to performance data), that can only come from `get_operation_log`'s change records, not from querying `get_entity_metadata` for a past point in time.

## Example Call

**User input**:
> Give Demo US a report for last week

**Skill flow**:
1. Resolve the profile: `get_user_authorized_context` → find Demo US's `profileId`
2. `weekEnding` = last Sunday; check the T+2-delay window
3. Run Steps 2-6
4. Output the markdown report — in English, since the user asked in English

## Error Handling

Follows the shared error envelope used by all three underlying tools (`isError`/`errorType`, see [`references/platform-notes.md`](references/platform-notes.md)). Specific handling for the weekly-report use case:

| Situation | Handling |
|---|---|
| `profileIds` is empty | Follow "Resolving `profileIds`" above — call `get_user_authorized_context` first, then apply those rules; ask the user to pick only when those rules actually require it (not automatically) |
| Any call returns `isError: true` | Handle per `errorType` (`invalid_params` is usually a construction bug in this skill's own call — check parameter names and date ranges first; `rate_limited` → wait `retryAfterSeconds` before retrying, don't retry immediately) — don't treat a tool error as "no data for this period" |
| `effectiveProfileIds` doesn't match the requested `profileIds` | Explain that the actual scope differs from expected — check the token's authorized scope first, don't just treat it as "this store has no data" |
| A time window is genuinely missing data (not an error) | State clearly "data for X-Y is missing," and still produce the report with what's available |
| `get_operation_log` returns `truncated: true` | Follow its "Getting a Complete Count" procedure (split into sub-windows) rather than treating one page as the full queried window; note in the report that the change history for the queried window is incomplete (counts are lower bounds) |
| All KPIs show WoW change < 5% | Change the one-line summary to "stable week, no significant swings"; merge the Top Changes section into a brief note |

## Not Covered by This Skill

Don't do these in the weekly report — point the user to the corresponding capability instead. Where a dedicated skill exists, name it; the rest still require manually combining the three base tools:
- Deep root-cause attribution ("why did ACOS go up") → see `sparkx-query-ads-performance`'s [ACOS root-cause investigation example](../sparkx-query-ads-performance/references/example-acos-root-cause-investigation.md)
- Full product-level diagnosis → `sparkx-product-diagnosis`
- Structural/share-of-spend analysis → `sparkx-ads-structure-analysis`
- Search-term mining (negatives, terms to target as exact) → `sparkx-search-term-diagnosis` (if installed)
- Restoring bids / budgets / managed-group settings after a promotion → `sparkx-promo-reset` (if installed)
