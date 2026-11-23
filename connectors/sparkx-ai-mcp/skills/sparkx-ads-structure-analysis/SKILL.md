---
name: sparkx-ads-structure-analysis
description: >-
  Analyze how ad spend and efficiency break down across a structural dimension — campaign type
  (SP/SB/SD), marketplace/site, portfolio, weekday-vs-weekend, hour-of-day, or campaign size tiers (head vs long tail) — and diagnose where spend share
  and efficiency don't match (over-invested underperformers, under-invested strong performers).
  Optional sub-scenarios: SP deep-dive (manual vs auto targeting), SB new-to-brand focus. Use when
  the user asks "我 SP/SB/SD 结构合理吗", "各站点谁强", "SB 新客到底行不行", "工作日和周末哪个好",
  "structure analysis", "campaign type breakdown". Not for a single-entity trend/anomaly check (use
  sparkx-weekly-ads-report / sparkx-monthly-ads-report / a lighter ad-hoc analysis skill), product-level diagnosis
  (use sparkx-product-diagnosis), or search-term diagnosis (use sparkx-search-term-diagnosis).
metadata:
  version: 1.1.5
---

# Ads Structure Analysis

## Scope: This Is an Orchestration Skill, Not a New MCP Tool

This skill does **not** map to a single MCP tool of its own — it orchestrates two existing read tools, each already covered by its own skill:

- `get_ads_perf` → [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md)
- `get_entity_metadata` → [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md)

> **Dependency — install these two base skills alongside this one:** `sparkx-query-ads-performance`, `sparkx-query-entity-metadata`. Skills install as sibling directories under your current agent's skills root (`.claude/skills/<name>/` for Claude Code; the equivalent root for other agents — see the installation notes in [README](../README.md)), which is exactly what the `../query-.../…` links above (and elsewhere in this doc) resolve against — if a base skill isn't installed there, those links won't resolve and this skill can't run. Install both first.

**Read those two SKILL.md files first** (parameter formats, field-naming rules, the Ratio Metric Display Rule) plus [`references/platform-notes.md`](references/platform-notes.md) (auth flow, error handling, pagination, date-range limits, currency rules). This document only covers logic specific to structural analysis; it doesn't repeat what the base skills already document.

Rewritten against the new tool's conventions from the start — carries forward the same discipline established across `sparkx-weekly-ads-report`/`sparkx-monthly-ads-report`: full `profileIds` resolution rules, currency-aware thresholds, output-language adaptivity, disclosed sampling fallback, and zero-denominator handling.

## Output Language: Always Match the User, Never Hard-Code Chinese or English

**The worked examples and output templates below are written in Chinese** (matching this product's primary customer base), but they are **structural illustrations, not literal text to copy verbatim**. Generate the actual report in whatever language the user asked in. When calling `get_ads_perf`, also set the `language` parameter (`zh`/`en`/`ja`) to match the customer's language. **`get_entity_metadata` has no `language` parameter** — it's not in that tool's documented parameter list. Localize its enum values using the returned `{field}Text` companion fields, or `sparkx-query-entity-metadata`'s own [`enum-i18n.md`](../sparkx-query-entity-metadata/references/enum-i18n.md) if a given enum has no `Text` companion — don't pass `language` to `get_entity_metadata` expecting it to have the same effect as on `get_ads_perf`.

## When to Use

**Trigger phrases**: 结构分析, 结构合理吗, 类型对比, 站点对比, SP/SB/SD 结构, SB 新客, 工作日 周末, 头部活动, 长尾要不要清, 活动太碎, structure analysis, campaign type breakdown

**User roles**: ads managers, account managers, ads ops doing a deep-dive (not a periodic report)

**Core question**: how is spend distributed across this dimension, is that distribution matched by efficiency, and where's the structural imbalance

**Not for**:
- Periodic recaps (WoW/MoM cadence) → `sparkx-weekly-ads-report` / `sparkx-monthly-ads-report`
- Single-campaign root-cause investigation → [ACOS root-cause investigation example](../sparkx-query-ads-performance/references/example-acos-root-cause-investigation.md)
- Product-level diagnosis → `sparkx-product-diagnosis`; search-term diagnosis → `sparkx-search-term-diagnosis` (if installed)

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `profileIds` | array[long] | No | — | See "Resolving `profileIds`" below |
| `breakdownBy` | enum | No | `campaignType` | `campaignType` \| `marketplace` \| `portfolio` \| `dayOfWeek` \| `hourOfDay` \| `campaignTier`. See "Breakdown Dimensions" for how each is actually queried — some require client-side derivation, not a native `groupBy` |
| `dateStart` / `dateEnd` | string (`YYYY-MM-DD`) | No | Trailing 30 days ending yesterday | The analysis window. Must satisfy `get_ads_perf`'s 90-day span / 15-month lookback caps like any other call |
| `focusMetrics` | array[string] | No | `["Spend", "Sales", "ACOS", "ROAS", "CPA"]` | Which metrics drive the share/efficiency comparison. `CPA` is included by default alongside `ACOS` — the product's own canonical "Campaign Type Analysis" board treats them as equally core, not `ACOS` alone. Must be valid for the entities involved — check `sparkx-query-ads-performance`'s Metrics × Entity Support Matrix |
| `includeTrend` | bool | No | `true` | Whether to include a per-segment trend view (Step 3) alongside the single-period snapshot — on by default, matching how the product's own dashboards present this analysis (trend lines, not just a static table). Set `false` for a lighter, snapshot-only response |
| `subScenario` | enum | No | — | `spDeepDive` \| `sbNtb` \| `weekdayWeekend`. See "Sub-Scenarios" below. **`sbvCreative` (creative-type breakdown) is not offered — see Data Boundaries for why** |

### Resolving `profileIds`

Always call `get_user_authorized_context` first to get the authorized `profiles` list, then apply exactly one of these cases:

1. **The user named specific store(s)** → resolve the name(s) against the authorized list and query only the matching profile(s).
2. **The user explicitly said "all stores" / "全账号" / equivalent** → query all authorized `profileIds`.
3. **The user didn't name a store, and there's only one authorized profile** → use it directly — there's nothing to ask.
4. **The user didn't name a store, and there are multiple authorized profiles**:
   - **5 or fewer** → you may default to using all of them.
   - **More than 5** → do not silently roll everyone up. Hand the user the `profiles` list and ask them to pick one, several, or explicitly confirm "all stores" first.

Case 4's threshold exists because a silent multi-store aggregate can hide a single store's structural pattern behind a blended number, and forces an unannounced USD conversion (see "Multi-Store and Currency" below).

## Breakdown Dimensions

**`campaignType`** (default) — `campaign.campaignType_` (`sponsoredProducts`/`sponsoredBrands`/`sponsoredDisplay`). A native dimension field; group directly via `select`.

**`marketplace`** — `profile.countryCode_`. Only meaningful when `profileIds` spans multiple countries; if it's a single-country selection, say so and suggest `campaignType` or `portfolio` instead of producing a one-row "breakdown."

**`portfolio`** — `portfolio.portfolioId_`, displayed via `portfolio.portfolioName_`. Rows with no portfolio must be grouped as an explicit "no portfolio" bucket, not silently dropped from the total.

**`dayOfWeek`** — **not a native `groupBy` expression.** `get_ads_perf`'s time-aggregation options are calendar day/week/month/quarter/year (see `sparkx-query-ads-performance`'s Time Aggregation table) — there is no "bucket every Monday together regardless of week" expression. To do this breakdown: pull daily-granularity data (`select: ["date"]`, one row per day across the window), then **client-side** map each row's `date` to a weekday name and aggregate the 4-5 occurrences of each weekday within the window yourself. Don't attempt to express this as a single server-side `groupBy`.

**`hourOfDay`** — available via hourly (AMS) data, with tighter limits than every other breakdown here. Query `factEntity: "campaign"` with `timeGranularity: "hourly"` and explicitly include both `date` and `hour` in `select`; hourly mode changes the source table but does not inject `hour` into the selected grouping. Aggregate the returned rows by hour **client-side** (same shape as `dayOfWeek`).

Constraints you must respect and disclose:
- **Campaign level only.** There is no hourly adGroup / target / placement / ASIN data — `timeGranularity: hourly` on any other entity is a hard error. So an hourly breakdown cannot be crossed with `portfolio` or `marketplace` beyond what campaign-level `select` fields give you.
- **7-day window per call, not 30 or 90.** This breaks the skill's default trailing-30-day window: either narrow to ≤7 days, or split the requested window into contiguous ≤7-day calls and aggregate hour-of-day across all chunks. Call it a **sample** only when you deliberately cover a subset (for example, the latest 14 of 30 days), and disclose that subset. If every day is covered by non-overlapping chunks, describe it as a split full-window query, not sampling.
- **Averaging**: divide each hour's totals by the number of *days* covered, not the number of rows.
- **No AI columns.** Hourly campaign data returns AI metrics as placeholders (`AISpend`/`AISales` = 0, `AIACOS`/`AIROAS` = null), so an hour-of-day table cannot split AI-managed vs manual spend; leave AI columns out and say so if the user asks.
- **Recent hours are provisional, not missing.** Hourly rows appear ~2 hours after the hour ends, but conversions are backfilled onto them afterwards, and **when an hour stops changing is undocumented** — T+2 is the daily pipeline's figure and should not be quoted as the hourly settling time. Label the trailing hours provisional, say the final window can't be confirmed, and re-pull before treating them as final, rather than reporting a fake evening collapse.
- **Hour labels are store-local** (the profile's IANA `timezone` from `get_user_authorized_context`, not UTC - see `sparkx-query-ads-performance`'s hourly/AMS example). Say so when you name an hour, and treat a daylight-saving changeover day as ambiguous.

**What you can actually change after reading an hourly pattern.** Finding a dead window is
only useful if something can act on it, and MCP's reach here is narrower than the platform's:

| | Writable through MCP |
|---|---|
| Turn AI bid-dayparting on/off | ✅ `aiActionSettings.bidDaypartStatus` on the managed group |
| Turn AI budget-dayparting on/off | ✅ `aiActionSettings.budgetDaypartStatus` |
| How aggressive each is | ✅ the matching AI personality field |
| Which days budget-dayparting runs | ✅ `aiAutomation.budgetDaypartExcuteDays` |
| **A specific hour-by-hour schedule** | ❌ not writable - no tool writes the hour matrix |
| **Rule mode for dayparting** | ❌ `1` = Rule mode is rejected by the tool; only `0` (AI mode) |
| **Campaign-level hourly bid multipliers** | ❌ `batch_update_ads` has no dayparting route |

So the useful recommendation is usually "hand the pattern to AI dayparting and set how
aggressive it should be", not "set 8pm to -40%". When the user wants a specific hour schedule,
say plainly that it has to be set in the platform, and offer the AI route as the alternative -
don't describe an hour matrix you cannot write.

A keyword × placement structural view is also possible (`factEntity: "keywordPlacement"`, SP only, hourly, ≤7 days) — see `sparkx-query-ads-performance`'s hourly/AMS example. Note its AI metrics are placeholders (`AISpend`/`AISales` = 0, `AIACOS`/`AIROAS` = null), so don't put AI columns in that table.

**`campaignTier`** — campaigns ranked by spend and cut into five bands, to see whether efficiency
changes with campaign size ("头部活动是不是最差的", "长尾要不要清"). Not a native field: pull
campaign-level window totals and band them client-side (Step 2 and "Campaign tiers" in Step 4).

## Sub-Scenarios

**`spDeepDive`**: narrow to `campaign.campaignType_ = sponsoredProducts`, then further break down by `campaign.targetingType_` (`manual`/`auto`) — compare manual vs auto targeting's spend share and efficiency within SP specifically. **Don't confuse this with `target.targetingType_`**, a different field with different values (`keyword`/`target`/`auto`/`audience` — categorizing the target's own type, not the campaign's manual/auto setting).

**`sbNtb`**: narrow to `campaign.campaignType_ = sponsoredBrands`, and add the NTB metrics (`NTBOrders`, `NTBSales`, `NTBUnits`, `NTBOrdersRate`, `NTBUnitsRate`, `NTBSalesRate`) to the metrics pulled — these are confirmed available for `campaign`/`adGroup`/`target`/`searchTerm`/`productAd` (not `placement`/`asin`), so request them at whichever entity level the rest of the breakdown is using. Report NTB share alongside the regular spend/efficiency breakdown, since "is SB driving new customers" is specifically what NTB answers.

**`weekdayWeekend`**: use the `dayOfWeek` breakdown above, then bucket further into two groups (Mon-Fri vs Sat-Sun) rather than 7 separate days, if that's what the user actually asked ("workday vs weekend" is coarser than "which specific day of the week").

**Companion breakdowns customers often ask for alongside `campaignType`**: the product's own "Campaign Type Analysis" dashboard template pairs the campaign-type view with a **targeting-type breakdown** (manual vs auto — covered here via `spDeepDive`) and a **search-term match-type breakdown** (broad/phrase/exact, etc.). The second one is **not covered by this skill** — `sparkx-search-term-diagnosis` (if installed) covers it (spend by match-type source). If a customer's ask naturally extends into match-type territory (e.g. "结构分析完了，再看看搜索词匹配类型"), say plainly that this skill's scope stops at campaign/targeting-type structure and point them to that skill instead of folding match-type analysis into this output.

## Before recommending that something be stopped

A structural analysis often ends in "this campaign isn't earning its share". Two things to get
right before that becomes an action.

**1. Check what depends on it.** Stopping a campaign stops every ad group, product ad and
keyword under it, and a product advertised *only* there loses all its advertising. Read
`get_entity_metadata(entity='productAd')` for the campaign and say which ASINs go dark - and
whether any of them run nowhere else. A long-tail campaign is often the only place a long-tail
product is advertised.

**2. There is no delete, and archiving is the irreversible one.** `batch_update_ads` takes
`enabled`, `paused` and `archived` - nothing hard-deletes. So the choice is:

- **pause** - reversible, the default recommendation for "stop spending on this"
- **archive** - **cannot be undone**, and it is what the user means by "delete". Never pick it
  for them: say it is irreversible, say what pausing would do instead, and let them choose.

Recommend pausing unless the user asked to clean up permanently. Either way the usual
confirmation rules in `sparkx-edit-ads` apply - this skill analyses, it does not write.

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
- **Campaigns in a running managed group get group-level advice.** A campaign's group is
  `campaign.aiGroupId_` in `get_ads_perf` (or `aiGroupId` on `get_entity_metadata`'s `campaign`
  entity; an unmanaged campaign has `0`); the group's `aiStatus` comes from
  `get_entity_metadata` (`entity: aiGroup`). The AI sets those campaigns' bids and budgets, so a
  manual bid or budget change gets overwritten: recommend the group's levers instead (target
  ACOS, group budget, an action-space switch) or say the AI is handling it. **No bid advice with
  numbers anywhere**; for an unmanaged campaign give at most a direction ("consider lowering
  bids on ..."). Keyword-level actions (pausing a zero-order exact keyword, negatives) need
  keyword and search-term data - point to `sparkx-search-term-diagnosis` (if installed).
- **Promotions.** This skill reads no operation log, so the only signals are the user and the
  event calendar. If the window overlaps a major event (Prime Day, Prime Big Deal Days, Black
  Friday / Cyber Monday), ask whether the store ran a promotion; if confirmed, say so - shares
  and efficiency during a promo are not the store's normal structure - and suggest a window
  without it for structural conclusions.

In structure analysis the target ACOS replaces the account average as the efficiency bar when
the user gives one (Step 4).

## Workflow

### Step 1 · Define the Analysis Window

Default: trailing 30 days ending yesterday (T+2 delay — see below). If the user gives an explicit range, use it, but confirm it satisfies `get_ads_perf`'s 90-day max span and 15-month lookback before issuing the call — if it doesn't, split into multiple ≤90-day calls per the standard procedure (see `sparkx-query-ads-performance`'s aggregation-over-time example) rather than sending an oversized request.

**T+2 data-delay check**: if the window's end date is within 2 days of today, note that the most recent day(s) may not have finished processing yet.

### Step 2 · Pull Data

**a. Breakdown-level performance**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "dateStart": "{window start}",
  "dateEnd": "{window end}",
  "select": ["campaign.campaignType_"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions"],
  "pageSize": 500,
  "userContext": "Structure analysis - breakdown by campaign type"
}
```
For `campaignTier`, `select: ["campaign.campaignId_", "campaign.campaignName_", "campaign.campaignType_", "campaign.targetingType_"]` over the whole window (no `date`), fully paginated, plus `get_entity_metadata(entity='campaign', filters={"campaignState": "enabled"})` to count enabled campaigns that had **no** spend in the window. Build the set of Amazon campaign ids whose performance row has `Spend > 0`; every enabled campaign whose `amazonCampaignId` is **not** in that set is zero-spend for the window. Don't subtract "all ids that returned a row" - a campaign with impressions but no clicks can return a row with `Spend` of `0` or `null`. Response keys drop the prefix and trailing `_` (`campaign.campaignId_` -> `campaignId`). **Match on the Amazon id**: the performance rows' `campaignId` is Amazon's, so compare it with the metadata's `amazonCampaignId`, never with the metadata's internal `campaignId` - that join matches nothing and silently reports every enabled campaign as zero-spend.

For the `campaignTier` trend, the bands are fixed on the whole window first (Step 4); then pull
`campaign.campaignId_` + the week expression from Step 2c and sum each band's fixed members per
week. Never re-band week by week - a campaign that moves between bands makes the trend
incomparable.

`select` changes per `breakdownBy`: `["campaign.campaignType_"]` for `campaignType`, `["profile.countryCode_"]` for `marketplace`, `["portfolio.portfolioId_", "portfolio.portfolioName_"]` for `portfolio`, `["date"]` for `dayOfWeek` (aggregate to weekday buckets client-side per "Breakdown Dimensions" above), and `["date", "hour"]` plus `timeGranularity: "hourly"` for `hourOfDay` (aggregate the same hour across dates client-side). **Recompute ACOS/ROAS/CTR/CVR from the summed base metrics per segment** rather than requesting them directly alongside a `select` that spans the whole window in one row per segment — request the base metrics (`Impressions`/`Clicks`/`Spend`/`Sales`/`Conversions`) and derive the ratios, so there's no ambiguity about which period/grouping a pre-computed ratio belongs to.

**If `subScenario` is set, this call changes further — don't run the plain breakdown call above and expect Step 5 to somehow retrofit it:**
- **`spDeepDive`**: add `{"campaign.campaignType_": "sponsoredProducts"}` to `filters`, and add `campaign.targetingType_` to `select` alongside (or instead of, if not also doing the base `campaignType` breakdown) the `breakdownBy` dimension.
- **`sbNtb`**: add `{"campaign.campaignType_": "sponsoredBrands"}` to `filters`, and add `NTBOrders`/`NTBSales`/`NTBUnits`/`NTBOrdersRate`/`NTBUnitsRate`/`NTBSalesRate` to `metrics`.
- **`weekdayWeekend`**: same as the `dayOfWeek` breakdown's call shape (`select: ["date"]`) — the Mon-Fri/Sat-Sun bucketing happens client-side afterward, no additional field needed here.

**b. Segment-level entity config** (only if the diagnosis needs config context, e.g. explaining *why* a segment underperforms): `get_entity_metadata` for the relevant entity (`campaign`, `portfolio`, etc.) to pull status/settings for the segments identified as imbalanced in Step 4.

**c. Segment-level weekly trend** (only when `includeTrend=true`, the default): same shape as (a), but `select` adds a weekly time-aggregation expression alongside the breakdown dimension — e.g. `["campaign.campaignType_", "toMonday(parseDateTime32BestEffort(date)) as week"]` — so each segment gets one row per week across the window instead of one row for the whole period. **Use weekly, not daily, granularity for the trend view**: a 30-day default window is ~4-5 weekly points per segment, which reads cleanly in a text report; daily granularity (30 points × N segments) is what the product's own web dashboard can render as a line chart but is too dense for a markdown table. Recompute `ACOS`/`CPA` per segment per week from that week's own summed base metrics — never average pre-computed weekly ratios across weeks, and never derive a week's ratio from another week's base metrics.

**d. Per-campaign sample distribution** (every run, not only `campaignTier`): pull one row per
campaign for the whole window with `select: ["campaign.campaignId_",
"campaign.campaignName_", "campaign.campaignType_"]` and base metrics including `Clicks` and
`Spend`, fully paginated. Reuse Step 2a when `breakdownBy=campaignTier`; otherwise this is a
separate campaign-level call. This distribution is required because an account-wide average
cannot establish that every campaign has enough evidence.

**Exception for `breakdownBy=hourOfDay`: do not issue this separate weekly-trend call.** The 24-point intraday curve derived from Step 2a's `date` + `hour` rows is already this mode's trend output, and its ≤7-day source window does not produce a meaningful 4-5-point weekly series. Treat `includeTrend` as satisfied by the intraday curve; only add a day-by-day comparison when the user explicitly asks, using the same rows client-side rather than a weekly aggregation expression.

**⚠️ `breakdownBy=dayOfWeek` or `subScenario=weekdayWeekend` need a different shape here — the breakdown "dimension" isn't a native field to add alongside `week` the way `campaign.campaignType_`/`profile.countryCode_`/`portfolio.portfolioId_` are.** There's no server-side field for "which weekday" to combine with a week aggregation. Instead: `select: ["date"]` only (same as the base breakdown call), pull daily rows across the whole window, then **client-side** derive two labels per row — the weekday/weekend segment (per "Breakdown Dimensions" above) and the week bucket it falls in — and organize the trend as segment × week from those two derived labels together. Don't expect the server to return a "Monday" or "weekday" row directly at any granularity.

**Fully paginate before analyzing** — loop `page` while `hasNextPage` is `true`. **If full pagination would be impractical at scale** (e.g. very many portfolios or campaigns), you may fall back to a spend-ranked sample instead of the full population — this fallback **must be disclosed explicitly**, stating what was actually covered, and **a degraded section must not fail the whole analysis** — produce whatever's complete and mark only the affected part as partial.

### Step 3 · Compute Share and Efficiency Per Segment

For each segment in the breakdown: **share of total** (`segment Spend / account total Spend`, and separately `segment Sales / account total Sales` — report both, they can diverge) plus the segment's own `ACOS`/`ROAS`/`CTR`/`CVR`/`CPA` recomputed from its summed base metrics (`CPA = Spend/Conversions`).

**Zero-denominator handling**: a segment with `Sales = 0` has undefined `ACOS` — don't compute it, don't treat it as infinite; report the segment's `Spend` and note "no sales this period" instead of a fabricated ratio. Likewise, a segment with `Conversions = 0` has undefined `CPA`.

**Trend view (when `includeTrend=true`)**: using Step 2c's weekly-grouped data, show each segment's `ACOS`/`CPA` across the weeks in the window — the product's own canonical dashboard treats this trend, not just the period snapshot, as the primary way to read structural efficiency. Call out any segment whose trend moved meaningfully within the window (e.g. "SB's ACOS was stable at ~24% for three weeks, then jumped to 31% in the last week") — a snapshot alone would average that shift away and miss it.

**Where an ACOS gap comes from.** ACOS itself is always computed from the sums: `Spend / Sales`
is a **fraction** (0.24); shown as a percentage it is `Spend / Sales × 100` (24%). The
decomposition below only explains a difference, and it also yields fractions - multiply by 100
before showing an ACOS from it, or a 24% ACOS comes out as 0.24%. With the factors computed from summed base metrics - CPC =
`Spend / Clicks`, CVR = `Conversions / Clicks` **as a fraction** (not the ×100 `CVR` field; divide
that by 100 if you use it), order value = `Sales / Conversions` - ACOS = CPC ÷ (CVR × order value),
so two segments compare as **ACOS ratio = CPC ratio ÷ (CVR ratio × order-value ratio)**. Whenever
Step 4 flags a gap, say which factor carries it, using all three - a ratio built from two of them
gives the wrong answer whenever order values differ by more than about 10%. Undefined factors:
`Clicks = 0` -> no CPC or CVR; `Conversions = 0` -> no order value; then no decomposition for that
segment.

- **Lower order value** carries it -> the segment sells cheaper things; that is structural
  (price), not something bids or budgets fix. A low order value sets a floor: at a given CPC and
  CVR the ACOS cannot go lower, so "ACOS is high" may simply be the product's price. (A higher
  order value pulls ACOS **down**, so it never explains a worse ACOS.)
- **Higher CPC** carries it -> bids, placements, competition.
- **Lower CVR** carries it -> relevance of the traffic, or the listing / price / reviews / stock
  after the click.

**Ratio-metric display rule**: the confirmed percentage metrics used here — `ACOS`, `CTR`, `CVR`, `TACOS`, and the listed NTB `*Rate` metrics — are already pre-scaled ×100. Append `%`, never re-scale. Do not apply this rule to an unlisted ratio-shaped field solely from its name. `ROAS`/`CPA` are plain ratios/unit-costs, not percentages — no `%`. See the base skill's Ratio Metric Display Rule.

### Step 4 · Diagnose Structural Imbalance

Compare each segment's **spend share** against its **efficiency** (ACOS/ROAS) and **sales share** relative to the account average:

- **Over-invested, underperforming**: spend share meaningfully higher than sales share, and/or ACOS meaningfully worse than the account average — flag as a candidate for reallocating budget away from.
- **Under-invested, strong performer**: spend share meaningfully lower than sales share, and/or ACOS meaningfully better than the account average — flag as a candidate for scaling up.
- **Currency-aware thresholds**: define "meaningfully" using percentage-point gaps (share) and relative ACOS deviation (e.g. ">20% worse than the target ACOS", or than the account average when no target was given), not a hardcoded absolute dollar gap — a fixed dollar threshold breaks for non-USD single-store analyses the same way it would in the weekly/monthly report skills.
- Don't diagnose a segment with negligible spend share (e.g. <2% of total) as a meaningful imbalance either way — flag it as "too small to be structurally significant" instead, to avoid noise from long-tail segments.

**Campaign tiers (`breakdownBy=campaignTier`).** Defaults below come from internal reviews of
many accounts; state them in the output and use the user's own if given.

1. **Bands.** Sort campaigns with spend by spend descending (ties: by campaign id ascending).
   Walk the list; each campaign goes to **one** band, chosen by the cumulative spend share
   **before** it is added: under 20% -> A, 20-40% -> B, 40-60% -> C, 60-80% -> D, 80% or more -> E.
   So a campaign that alone is 55% of spend is A, and the next one starts at 55% and lands in C -
   **B is then empty, which is allowed**; never split or repeat a campaign. Per band: campaign
   count, spend share, ACOS, CPC, CVR and average order value, all from summed base metrics.
   Banding by share, not by fixed amounts, keeps stores of any size and currency comparable.
   A band is **valid** for the shape only if it has campaigns and sales (`Sales > 0`). Fewer than
   5 campaigns, or fewer than 3 valid bands -> no shape verdict: show the campaigns themselves
   and say why. A non-empty band with `Spend > 0` and `Sales = 0` is reported on its own as
   "spent but sold nothing" (its spend and spend share), never just dropped; if it holds 2% or
   more of total spend, the shape is `notJudged` - leaving it out would let the remaining bands
   read "flat" while the worst money sits in the excluded one.
2. **Check campaign function before reading the shape.** Size bands often line up with what
   campaigns are for - branded-keyword campaigns tend to be large and cheap, category, competitor
   and auto ones smaller and dearer - and then the "shape" is really a function mix. Tag each
   campaign's function. Always available: ad type and, for SP, auto vs manual (the two fields
   added to `select` above). Finer functions (brand / category / competitor / auto) only from a
   naming convention: propose a mapping from the name fragments the campaigns actually use
   (e.g. "Branded", "Category", "Competitor", "Auto"), show which campaigns land in each, and use
   it only after the user confirms - never guess a convention. If the best and the worst valid
   bands are each dominated (60% or more of the band's spend) by a **different** function, say
   "the gap follows campaign function, not size", keep the shape as background only, and re-cut
   by function instead of acting on it. (A backtest store, 2026-10: band A was 72% branded at
   ACOS 16%, the worst band B 67% keyword-boost campaigns at ACOS 85% - a function gap, not a
   "head" problem.)
3. **Shape** of ACOS across the valid bands (empty and zero-sales bands are left out of
   max - min and of "worst"), and what it means:

| Shape | Test | What to do |
|---|---|---|
| Flat | max - min band ACOS < 4 pp | Campaign size is not the lever; switch dimension (placement, match type, product, campaign type) |
| Head worst | the worst band is A or B | Stop the bleeding at the head: hold their budgets, find the worst campaigns inside A/B; leave the rest |
| Tail worst | the worst band is E (or D) | The long tail is not converging; review it per the tail rule below |
| Middle worst | the worst band is C, with both A and E better | Campaigns that scaled but never worked. Not a budget change; what to cut inside them needs keyword and search-term evidence, so point to `sparkx-search-term-diagnosis` (if installed) scoped to these campaigns - campaign-level data cannot justify negatives |

   **Tail rule** (the worse of the valid tail bands D and E vs the account ACOS): under 1 pp ->
   leave it; 1-3 pp -> watch; over 3 pp
   -> review the tail campaigns (pause / consolidate candidates), with keyword-level evidence from
   `sparkx-search-term-diagnosis` (if installed) before cutting anything inside them.
   **Check order value before calling a band a problem.** If the worst band's order value is
   clearly **lower** than the account's (about 2/3 of it or less), part of the gap is price - say
   so before recommending cuts. If its order value is the same or **higher** and its ACOS is still
   the worst, the CPC / CVR problem is larger than the ACOS gap shows.
4. **Fragmentation.** Keep the account-level average for context:
   `clicksPerCampaign30d = totalClicks / spendingCampaignCount × 30 / windowDays`, where
   `spendingCampaignCount` counts campaigns with `Spend > 0` and `windowDays` counts both the
   first and last day (1-30 Jun = 30). But never use that average as proof that individual
   campaigns are sufficiently observed.

   From Step 2d, compute `campaignClicks30d = campaignClicks × 30 / windowDays` for every
   spending campaign and report the **median**, **P25**, and these mutually exclusive buckets:

   - **over 200**: sufficient for campaign-level judgement;
   - **100-200 inclusive**: limited sample - recommendations must be cautious;
   - **under 100**: continue observing; do not issue a campaign-specific pause, consolidation
     or budget action from this structure analysis alone.

   Report each bucket's campaign count, share of spending campaigns and spend share. List the
   under-100 campaigns by customer-facing name with clicks and spend. Decisions about the thin
   population may be made at group level, but do not describe every member as individually
   mature merely because the account average exceeds 200. Judge sample on clicks, not spend -
   spend per campaign misleads across price levels.
   Also report the enabled campaigns with no spend in the window (count and share of enabled) as
   **to check**, not as clutter to archive: a new campaign, a start date in the future, an
   out-of-stock or ineligible product, or a bid / budget too low to win can all produce zero
   spend. Say what to check; don't recommend archiving on this count alone.

### Step 5 · Sub-Scenario Section (if `subScenario` was requested)

Add the relevant specialized section per "Sub-Scenarios" above — this supplements, not replaces, the base breakdown from Steps 3-4.

### Step 6 · Structural Recommendations

Derive 3-5 recommendations from Step 4's findings, each with: action + target segment + evidence (share %, efficiency numbers). Budget moves follow "Shared Rules": where the segment's campaigns sit in running managed groups, the lever is the groups' budgets / targets, not campaign budgets. A clearly weak weekend (`weekdayWeekend`) on SP is a reason to **ask** whether the products are bought mainly by businesses (B2B). Only if the user confirms, mention the B2B system templates that cut weekend budget - they apply only when **creating a new SP managed group** (`sparkx-create-ai-group`); applying them to an existing group is rejected, so don't point to the edit skill for them. Same discipline as the report skills — **correlation, not causation**: a structural finding ("SD share grew while overall ACOS worsened") is not proof SD caused the ACOS change unless you've actually isolated SD's own ACOS as the driver; say what the data shows, not more.

## Multi-Store and Currency

When `profileIds` spans multiple stores:
- All monetary metrics from `get_ads_perf` auto-aggregate to **USD** — label dollar amounts "(USD)" explicitly.
- Add `profile.profileId_`/`profile.profileName_` to Step 2a's `select` if you need to know which store each row belongs to (e.g. combining `marketplace` breakdown with multi-store detail) — but don't add it when the point is one blended breakdown across all selected stores, since that would fragment each segment's row by store instead of aggregating it.

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

### markdown mode

```markdown
# 广告结构分析 · {profile_name}
**维度**：{campaignType / marketplace / portfolio / dayOfWeek / hourOfDay / campaignTier}
**周期**：{dateStart} ~ {dateEnd}
{If data may be incomplete due to T+2 delay, or a section is based on a partial sample, note it here}

## 一、结构占比

| 分段 | 花费占比 | 销售额占比 | ACOS | ROAS | CPA |
|---|---|---|---|---|---|
| SP | {pct} | {pct} | {acos}% | {roas} | {cpa} |
| SB | ... | ... | ... | ... | ... |
| SD | ... | ... | ... | ... | ... |

{仅当 includeTrend=true 时展示——按周展示每个分段的 ACOS/CPA 走势，不只是期末快照}

### 分段周度趋势（ACOS / CPA）

| 分段 | 第1周 | 第2周 | 第3周 | 第4周 | ... |
|---|---|---|---|---|---|
| SP · ACOS | {pct}% | ... | ... | ... | ... |
| SP · CPA | {value} | ... | ... | ... | ... |
| SB · ACOS | ... | ... | ... | ... | ... |
| SB · CPA | ... | ... | ... | ... | ... |

{如果某个分段的趋势中途有明显变化，单独点出来，不要让期末快照把这个变化平均掉}

## 二、结构失衡诊断

- **过度投入/表现不佳**：{segment} — 花费占比 {pct}，销售额占比仅 {pct}，ACOS 比账户均值差 {pct}
- **投入不足/表现优秀**：{segment} — ...

{Segments below the 2% spend-share floor: mention briefly as "too small to be structurally significant," don't over-analyze}

{仅当 breakdownBy=campaignTier：}

### 活动分层（按花费五档）

| 档位 | 活动数 | 花费占比 | ACOS | CPC | CVR | 客单价 |
|---|---|---|---|---|---|---|
| A（头部） | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... |
| E（长尾） | ... | ... | ... | ... | ... | ... |

**形态**：{平坦 / 头部最差 / 长尾最差 / 中间最差 / 无法判断（活动少于 5 个 / 有效档位不足 3 个 / 有档位花费占比 ≥2% 却没有销售额）}，极差 {x}pt → {对应动作}
{有花费但没出单的档位单独列一行：档位、花费、花费占比}
{若最好和最差的有效档分别被不同用途主导（各占本档花费 ≥60%）：写“差距主要来自活动用途（如品牌词 vs 加投词），不是活动大小”，形态只作背景，并按用途重新切一次}
{空档或零销售档在表中标“—”，不参与极差和最差档判断}
**碎片化**：每个有花费的活动平均 {n} 次标准化 30 天点击；中位数 {n}，P25
{n}。超过 200：{count} 个（{pct}，占花费 {spendShare}）；100-200：{count}
个（{pct}，占花费 {spendShare}）；不足 100：{count} 个（{pct}，占花费
{spendShare}）。

| 需要继续观察的活动（标准化 30 天点击 <100） | 点击 | 花费 |
|---|---:|---:|
| ... | ... | ... |

启用但零花费的活动 {m} 个（占启用活动 {pct}），待排查原因（新建、未到开始日期、
缺货或不可投放、出价或预算过低），不直接建议归档。

## 三、{子场景标题，若有 subScenario}

{spDeepDive: manual vs auto targeting 对比表；sbNtb: NTB 指标专区；weekdayWeekend: 工作日 vs 周末对比表}

## 四、结构调整建议

1. **{action}** {target}
   - 依据：{data}
2. ...

---
_生成时间：{timestamp} · 数据源：SparkX AI MCP · Skill: sparkx-ads-structure-analysis v{version}_
```

### structured_report mode

```json
{
  "dimension": "campaignType",
  "period": {"start": "...", "end": "..."},
  "dataFreshnessWarning": null,
  "segments": [{"segment": "...", "spendShare": ..., "salesShare": ..., "acos": ..., "roas": ..., "cpa": ..., "tooSmallToAnalyze": false}],
  "trend": null,
  "imbalances": [{"segment": "...", "type": "overinvested|underinvested", "evidence": "..."}],
  "subScenario": null,
  "campaignSample": {"clicksPerCampaign30d": 0, "medianClicks30d": 0, "p25Clicks30d": 0, "buckets": [{"level": "sufficient|limited|observe", "campaigns": 0, "campaignShare": 0, "spendShare": 0}], "observeCampaigns": [{"campaign": "...", "amazonCampaignId": null, "clicks30d": 0, "spend": 0}], "zeroSpendEnabled": 0, "zeroSpendShare": 0},
  "campaignTier": null,
  "recommendations": [{"priority": 1, "action": "...", "target": "...", "evidence": "..."}]
}
```
`"campaignTier"` is `null` unless `breakdownBy=campaignTier`; then it is
`{"tiers": [{"band": "A", "campaigns": 12, "spend": 2140.5, "sales": 8808.6, "spendShare": 0.21, "acos": 24.3, "cpc": 1.12, "cvr": 9.4, "orderValue": 49.1, "valid": true, "invalidReason": null}], "shape": "flat|headWorst|tailWorst|middleWorst|notJudged", "notJudgedReason": null, "functionGap": null, "spreadPp": null, "tailGapPp": null, "fragmentation": {"clicksPerCampaign30d": 0, "medianClicks30d": 0, "p25Clicks30d": 0, "buckets": [{"level": "sufficient|limited|observe", "campaigns": 0, "campaignShare": 0, "spendShare": 0}], "observeCampaigns": [{"campaign": "...", "amazonCampaignId": null, "clicks30d": 0, "spend": 0}], "zeroSpendEnabled": 0, "zeroSpendShare": 0}}`
- one entry per band A-E, empty bands included with `campaigns: 0` and `valid: false`; `invalidReason` is `empty` (no campaigns) or `zeroSales` (spend but no sales), `null` for a valid band; `functionGap` is `null` unless the best and worst valid bands are each dominated by a different function, then `{"bestBand": "A", "bestFunction": "...", "worstBand": "B", "worstFunction": "...", "source": "campaignType|targetingType|namingConvention"}` (`namingConvention` only after the user confirmed it); `notJudgedReason` is `null` unless `shape` is `notJudged`, then `tooFewCampaigns`, `insufficientValidBands` or `materialZeroSalesBand` (a zero-sales band with 2% or more of spend); undefined
ratios are `null`, never 0. Units: `acos` and `cvr` in percent (×100, like the tool's own fields), `spendShare`, `campaignShare` and `zeroSpendShare` as fractions, `cpc`, `spend` and `orderValue` in the report's currency. In this mode `segments` holds the same five bands.
`campaignSample` is populated on every run from Step 2d. When `campaignTier` is also present,
its `fragmentation` value must be identical to `campaignSample`, not a separately recomputed result.
`"trend"` is `null` when `includeTrend=false`; otherwise it's `[{"segment": "...", "weekly": [{"weekStart": "...", "acos": ..., "cpa": ...}]}]` — one entry per segment, each with its own array of weekly points.

## Data Boundaries

- **`sbvCreative` (creative-type breakdown) is not offered by this skill.** `get_ads_perf`/`get_entity_metadata`'s documented fields don't include a "creative type" dimension anywhere in the campaign/adGroup/target/productAd entity tables — this isn't a documented capability of either tool. Don't invent a field name for it; if a customer asks for creative-level SBV analysis, say plainly this data isn't currently queryable via these tools rather than guessing at an undocumented field.
- **`dayOfWeek` is a client-side derivation, not a server aggregation** — see "Breakdown Dimensions." Accuracy depends on correctly mapping each `date` to a weekday; don't get this wrong for reports spanning a daylight-saving or year boundary (unlikely at a 30-day default window, but worth checking for longer custom windows).
- **No historical structural snapshot** — `get_entity_metadata` has no point-in-time capability, so "how has the structure changed since 6 months ago" can only be approximated by re-running this analysis over a past window with `get_ads_perf`, not by querying `get_entity_metadata` for a past config state.
- **Structural findings are correlational**, not causal — see Step 6.

## Example Call

**User input**:
> 看下 Demo US 最近 30 天 SP/SB/SD 结构合不合理

**Skill flow**:
1. Resolve the profile: `get_user_authorized_context` → find Demo US's `profileId`
2. `breakdownBy = campaignType`, window = trailing 30 days ending yesterday
3. Run Steps 2-6
4. Output the markdown report — in Chinese, since the user asked in Chinese

## Error Handling

Follows the shared error envelope used by both underlying tools (`isError`/`errorType`, see [`references/platform-notes.md`](references/platform-notes.md)).

| Situation | Handling |
|---|---|
| `profileIds` is empty | Follow "Resolving `profileIds`" above — ask only when those rules require it |
| Any call returns `isError: true` | Handle per `errorType` — `invalid_params` usually means a construction bug in this skill's own call; `rate_limited` → wait `retryAfterSeconds` |
| `effectiveProfileIds` doesn't match requested `profileIds` | Explain the scope mismatch before concluding "no data" |
| A segment has `Sales = 0` | Report Spend and "no sales," don't compute ACOS against a zero denominator |
| A degraded/sampled section | Disclose what was covered; don't fail the whole analysis over one segment's pagination trouble |

## Not Covered by This Skill

- Periodic WoW/MoM cadence recaps → `sparkx-weekly-ads-report` / `sparkx-monthly-ads-report`
- Creative-type (SBV) breakdown → not currently a queryable capability, see Data Boundaries
- Product-level diagnosis → `sparkx-product-diagnosis`
- Keyword/search-term-level diagnosis → `sparkx-search-term-diagnosis` (if installed)
- Single-campaign root-cause investigation → [ACOS root-cause investigation example](../sparkx-query-ads-performance/references/example-acos-root-cause-investigation.md)
