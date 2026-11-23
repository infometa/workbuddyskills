---
name: sparkx-monthly-ads-report
description: >-
  Generate a monthly ad performance recap for ads managers / account managers at month-end.
  Includes full-month KPIs (MoM + YoY), goal attainment, structural breakdown (campaign type /
  site / portfolio share), product analysis (Top ASIN changes, newly advertised products, long-tail), keyword
  performance (Top keywords; search-term negatives / harvesting go to sparkx-search-term-diagnosis),
  an issues list with attribution, and next-month structural recommendations. Use when the user says "出个月报",
  "月度复盘", "这个月表现如何", "monthly report". Not for weekly recaps (use sparkx-weekly-ads-report) or
  quarterly/QBR-level strategic review (use quarterly-ads-report, not yet built).
metadata:
  version: 1.2.1
---

# Monthly Ads Report

## Scope: This Is an Orchestration Skill, Not a New MCP Tool

This skill does **not** map to a single MCP tool of its own — it orchestrates three existing read tools, each already covered by its own skill:

- `get_ads_perf` → [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md)
- `get_operation_log` → [sparkx-query-operation-log](../sparkx-query-operation-log/SKILL.md)
- `get_entity_metadata` → [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md)

> **Dependency — install these three base skills alongside this one:** `sparkx-query-ads-performance`, `sparkx-query-entity-metadata`, `sparkx-query-operation-log`. Skills install as sibling directories under your current agent's skills root (`.claude/skills/<name>/` for Claude Code; the equivalent root for other agents — see the installation notes in [README](../README.md)), which is exactly what the `../query-.../…` links above (and elsewhere in this doc) resolve against — if a base skill isn't installed there, those links won't resolve and this skill can't run. Install all three first.

**Read those three SKILL.md files first** (parameter formats, field-naming rules, the Ratio Metric Display Rule) plus [`references/platform-notes.md`](references/platform-notes.md) (auth flow, error handling, pagination, date-range limits, currency rules — shared by all three underlying tools). This document only covers logic specific to the monthly-report use case; it doesn't repeat what the three base skills already document.

This skill shares its overall shape with [sparkx-weekly-ads-report](../sparkx-weekly-ads-report/SKILL.md) (same underlying tools, same output-language and multi-store discipline) but goes deeper: AdGroup-level granularity, structural share analysis, product and keyword analysis, and a MoM+YoY baseline instead of WoW.

## Output Language: Always Match the User, Never Hard-Code Chinese or English

**The worked examples and output templates below are written in Chinese** (matching this product's primary customer base), but they are **structural illustrations, not literal text to copy verbatim**. Generate the actual report in whatever language the user asked in — section headers, KPI labels, everything. Do not assume the audience is Chinese-speaking just because this skill's own documentation and templates are.

When calling `get_ads_perf`, also set the `language` parameter (`zh`/`en`/`ja`) to match the customer's language, so returned enum companion text (e.g. `campaignTypeText`) is localized consistently with the rest of the report. **`get_entity_metadata` has no `language` parameter** — it's not in that tool's documented parameter list. Localize its enum values using the returned `{field}Text` companion fields, or `sparkx-query-entity-metadata`'s own [`enum-i18n.md`](../sparkx-query-entity-metadata/references/enum-i18n.md) if a given enum has no `Text` companion — don't pass `language` to `get_entity_metadata` expecting it to have the same effect as on `get_ads_perf`.

## When to Use

**Trigger phrases**: 月报, 月度复盘, 这个月表现如何, monthly report, recap this month

**User roles**: ads managers, account managers (client-facing)

**Core question**: how did this month perform, did we hit target, where are the problems, what's the plan for next month

**Not for**:
- Weekly recap → `sparkx-weekly-ads-report`
- Quarterly/QBR strategic review → `quarterly-ads-report` (not yet built)
- A specific question the user brings ("why did this one campaign's ACOS spike") → a dedicated analysis skill (not yet built), or the [ACOS root-cause investigation example](../sparkx-query-ads-performance/references/example-acos-root-cause-investigation.md)

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `profileIds` | array[long] | No | — | Target profile IDs. See "Resolving `profileIds`" below for the exact selection rules — don't default to "all stores" without checking those rules first |
| `month` | string (`YYYY-MM`) | No | Last full calendar month | The month this report covers. Always a **completed** month, not the current in-progress one |
| `monthlyTarget` | object | No | — | Optional KPI target for this month (a single metric+target+direction), e.g. `{"metric": "ACOS", "target": 25, "direction": "at_most"}` or `{"metric": "Spend", "target": 50000, "direction": "at_least"}`. `direction` is `at_least` (hit or exceed the target) or `at_most` (stay at or under it). Supplied by the user/account team — not retrievable from any tool |
| `compareBaseline` | enum | No | `mom+yoy` | `mom` \| `yoy` \| `mom+yoy`. **Controls only the KPI section (Step 3) baseline columns.** Structural analysis (Step 5) and product MoM changes (Step 6) are always month-over-month regardless of this setting — they always pull last-month data (2e/2g) |
| `outputFormat` | enum | No | `markdown` | `markdown` \| `structured_report` |

### Resolving `profileIds`

Always call `get_user_authorized_context` first to get the authorized `profiles` list, then apply exactly one of these cases:

1. **The user named specific store(s)** → resolve the name(s) against the authorized list and query only the matching profile(s).
2. **The user explicitly said "all stores" / "全账号" / equivalent** → query all authorized `profileIds`.
3. **The user didn't name a store, and there's only one authorized profile** → use it directly — there's nothing to ask.
4. **The user didn't name a store, and there are multiple authorized profiles**:
   - **5 or fewer** → you may default to using all of them.
   - **More than 5** → do not silently roll everyone up into one report. Hand the user the `profiles` list and ask them to pick one, several, or explicitly confirm "all stores" first.

Case 4's threshold exists because this is a customer-facing report: a silent multi-store aggregate can hide a single store's problem behind a healthy blended number, and it forces an unannounced USD conversion (see "Multi-Store and Currency" below) the customer didn't ask for.

**Determining whether to include an AI-managed section**: call `get_entity_metadata` (`entity: aiGroup`, filtered to the relevant `profileIds`; **add `filters: {"aiStatus": 1}`, or fully paginate — default page size is 100, so a running AI group sitting past page 1 would otherwise be missed and the section wrongly skipped**) — if any returned row has `aiStatus: 1`, include an AI-managed performance callout in the KPI section; otherwise omit it. **This check only decides whether to show the callout — it doesn't supply the callout's actual data.** For the content itself, add `AISales`/`AIACOS`/`AIROAS` to Steps 2a/2b/2c's existing `metrics` list (these are campaign-level-only metrics per the platform notes, which is already `factEntity: campaign` for these calls, so no separate call is needed) whenever the callout applies, and report those alongside the regular KPI table — don't include the callout with only a "yes, AI management is on" statement and no actual performance figures.

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

In the monthly report: when `monthlyTarget` is an ACOS target, that is the target ACOS above.
When the user confirms a promotion in this month or last month, MoM is misleading - put the
YoY column first when it was pulled.

## Workflow

### Step 1 · Define Time Windows

- **This month**: the full calendar month named by `month` (default: last full calendar month) — `dateStart` = 1st of that month, `dateEnd` = last day of that month.
- **Last month (MoM baseline)**: the calendar month immediately before "this month".
- **Same month last year (YoY baseline)**: the same calendar month, 12 months earlier.

All three windows are single calendar months (28-31 days) — comfortably within the 90-day single-call cap, no window-splitting needed for any of them individually.

**⚠️ Full calendar months are not equal length — do not force them to be.** Per the shared platform rule: compare the two full calendar months as-is (don't truncate the longer one or pad the shorter one), and **explicitly note the day-count difference** to the user when it exists (e.g. "July has 31 days, June has 30"). If the user cares about rate/efficiency rather than raw totals, additionally compute each month's **daily average** (`total ÷ day count`) alongside the raw totals.

**⚠️ Check the YoY lookback against the 15-month cap.** Same-month-last-year reaches back up to 13 months from "this month" (1 month for MoM + 12 more for YoY) when `month` defaults to last month — comfortably within the 15-month lookback. But if the user explicitly requests a `month` further in the past, recompute the actual YoY lookback distance and confirm it's still ≤15 months before issuing the call; if it isn't, say so explicitly rather than silently returning an error or omitting the YoY column without explanation.

**T+2 data-delay check**: if `month` is very recently completed (e.g. the report is generated on the 1st-2nd of the following month), the last day or two of that month's data may not have finished processing. Check how many days have elapsed since the month ended; if fewer than 2, add an explicit note that the month's final days' figures may still shift slightly.

### Step 2 · Pull Data

The calls below are independent and can be issued in parallel. Every call needs `userContext` (non-empty string, ≤100 chars). Structure/product/keyword calls deliberately **don't** filter by `campaignState`/`asinIsDelete` etc unless noted — MoM/YoY comparisons need to see entities that existed in one period but not the other (see Step 6's new/disappeared bucketing, which applies the same way to Steps 5 and 7).

**a. This month, account-level KPIs**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "dateStart": "{this month start}",
  "dateEnd": "{this month end}",
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions", "ACOS", "ROAS", "CTR", "CVR"],
  "pageSize": 500,
  "userContext": "Monthly report - this month's account-level KPIs"
}
```
No dimension in `select` — global aggregate across all campaigns. **If the AI-managed callout applies** (per the check under "Input Parameters"), add `AISales`/`AIACOS`/`AIROAS` to this call's `metrics` (and the same-shape calls b/c) — don't request them unconditionally on every report, since they're only meaningful when AI management is actually active.

**b. Last month** (only when `compareBaseline` is `mom` or `mom+yoy` — skip entirely when `compareBaseline=yoy`) and **c. same month last year** (only when `compareBaseline` is `yoy` or `mom+yoy` — skip entirely when `compareBaseline=mom`) — identical shape to (a), `dateStart`/`dateEnd` shifted to each baseline window. Don't issue a call whose baseline the report doesn't need.

**d. This month, AdGroup-level (feeds structure + attribution)**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "adGroup",
  "dateStart": "{this month start}",
  "dateEnd": "{this month end}",
  "select": ["adGroup.adGroupId_", "adGroup.adGroupName_", "campaign.campaignId_", "campaign.campaignName_", "campaign.campaignType_", "campaign.aiGroupId_", "portfolio.portfolioId_", "portfolio.portfolioName_", "profile.countryCode_"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions"],
  "pageSize": 500,
  "userContext": "Monthly report - this month's adGroup-level data for structure analysis"
}
```
**e. Last month, AdGroup-level** — same shape as (d), shifted back one month. `select` must match (d) exactly for a valid comparison.

**f. This month, Top ASINs**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "asin",
  "dateStart": "{this month start}",
  "dateEnd": "{this month end}",
  "select": ["asin.asin_", "asin.asinTitle_"],
  "metrics": ["TotalSalesAmount", "OrderCount", "TACOS"],
  "orderBy": [{"field": "TotalSalesAmount", "direction": "DESC"}],
  "pageSize": 500,
  "userContext": "Monthly report - this month's ASIN-level sales for product analysis"
}
```
**g. Last month, Top ASINs** — same shape as (f), shifted back one month, for MoM product comparison (Step 6).

**h. Newly-advertised-product identification** (first SP go-live this month — see the caveat at the end of this step, this is **not** the same as newly listed): `get_entity_metadata` (`entity: asin`). **`asinOpenDate` is NOT a filterable field** — asin's filterable fields are `asin`/`parentAsin`/`sku`/`asinBrand`/`asinTitle`/`asinBsr`/`asinPrice`/`asinInventoryStatus`/the eligibility flags/`asinIsDelete`/`productLine*` — so you can't filter the call by open date. Instead, pull the asin metadata (**fully paginate — loop `page` while `hasNextPage` is `true`; default page size is 100, so a catalog past one page silently truncates otherwise**), then read the returned `asinOpenDate` field and filter to this month's window **client-side**. `asinOpenDate` is a datetime-with-timezone string, e.g. `"2026-06-01 00:00:00 PST"` — not `YYYYMMDD`, and not the `YYYY-MM-DD` used by `dateStart`/`dateEnd` — so parse it and mind the **PST timezone** when judging whether an ASIN opened inside the month, to avoid month-boundary misclassification. (`campaignStartDate`/`EndDate` are strings of no guaranteed shape — a different problem again, not this field's format.)

⚠️ **`asinOpenDate` is the SP go-live date, not the date the product was first listed.** The underlying column is `sp_open_date`. An ASIN that has sold for years and only started running Sponsored Products this month carries a this-month `asinOpenDate`, so a naive read reports it as a new product. Two things follow:
- Call it **newly advertised** rather than **newly listed** in the report, or say "first ran SP this month".
- **Falsify it against sales that predate the SP go-live date.** **Step 2f cannot do this** — it covers this month only and returns a single aggregate per ASIN, so it can neither reach earlier months nor show whether this month's sales fell before or after `asinOpenDate`. Use instead:
  - **at minimum, Step 2g** (last month, same shape): any `TotalSalesAmount` there is sales that predate a this-month `asinOpenDate`;
  - **when it matters, one extra `get_ads_perf`** — the only check that works when an ASIN went live mid-month, or when there is no MoM baseline. **Candidates have different `asinOpenDate`s, so there is no single `dateEnd` that serves them all.** Pick one of these two shapes, don't improvise a third:
    - **Daily grain, one call** (preferred): `factEntity: asin`, `filters` on `asin.asin_` for every candidate, `dateStart` = the earliest candidate's `asinOpenDate` minus the lookback you choose, `dateEnd` = the **latest** candidate's `asinOpenDate - 1 day`, and **`date` in `select`** so rows stay per-day. Then, client-side, keep only each ASIN's rows strictly before **its own** `asinOpenDate`. Without `date` in `select` the response is one aggregate per ASIN and the per-ASIN cutoff cannot be applied — that is the mistake this shape exists to prevent.
    - **Group by `asinOpenDate`, one call per group**: simpler to reason about and the right choice when the dates cluster, but it costs one call per distinct date.
    Respect the 90-day span and 15-month lookback caps either way, splitting the window if needed.
  - **State the span you actually checked.** "No earlier sales" only ever means "none in the window queried". Write the window into the report ("no sales in the 6 months before its SP go-live date"), so nobody reads a 30-day check as proof the product is new.
  An ASIN with sales before its `asinOpenDate` is an **existing product newly put on SP**. Report it on its own line rather than mixing it into the new-product section, where it would distort every "how are new launches doing" comparison.
- **The check only works in one direction.** Finding earlier sales *disproves* "new product". Finding none **does not prove** the product is newly listed — it may have been listed for a year and simply never sold, or sold outside the window you queried. So call the remaining group what the data actually supports: **first ran SP this month, no earlier sales observed**. Don't promote it to "new product", and if a customer needs true listing age, say this field cannot provide it.

⚠️ **One ASIN returns several rows, one per SKU, each with its own `asinOpenDate`** (some on `Inactive` SKUs). Take the **earliest** date across an ASIN's rows — that is when the ASIN first went live on SP; the later ones are re-listings of individual SKUs, and picking whichever row arrives first gives a different answer run to run. The parent-level `parentAsinOpenDate` is `any(sp_open_date)` and is not reproducible at all — derive a parent's SP age from the minimum of its children instead.

**i. Keyword-level performance**: `get_ads_perf` with `factEntity: target`, `queryType: keyword`, this month's window, `select` including `target.targetId_`/`target.targetText_`/`target.targetMatchType_`, metrics `Impressions/Clicks/Spend/Sales/Conversions/ACOS`.

**k. Operation log** (feeds Step 8's attribution and the promotion signal): `get_operation_log` from 7 days before last month's start through this month's end (within the 90-day cap), no `changeBy` filter, `pageSize: 200`. Attribution uses this month's rows; the earlier rows only feed the promotion signal for the MoM baseline. The YoY baseline has no log here - for it, rely on the event calendar and ask; classify people vs machines and drop the hourly `currentBudget` rows per "Shared Rules". **Check `truncated`** — if `true`, follow `sparkx-query-operation-log`'s "Getting a Complete Count" procedure (split into non-overlapping sub-windows) rather than treating one page as the full month.

**Step 2k as a whole is best-effort, not a hard dependency for the rest of the report.** If splitting into sub-windows still times out or keeps erroring, don't let it block the rest of the report from completing — produce Steps 3-7/9 normally and mark Step 8's attribution as "operation log data incomplete this month" (or similar, in the report's own language) rather than failing the entire report over one section.

**Fully paginate (d)/(e)/(f)/(g)/(i) before analyzing** — loop `page` while `hasNextPage` is `true`. **If full pagination across many profiles/entities would be impractical at scale**, you may fall back to a spend-ranked sample (top N by `Spend`/`TotalSalesAmount` via `orderBy` + a capped `pageSize`) instead of the full population — but this fallback **must be disclosed explicitly** in the relevant section (e.g. "structure breakdown based on top-spend sample, not full population"), stating concretely what was actually covered (how many profiles/entities, how many pages, whether `hasNextPage` was still `true` when you stopped), never silently presented as complete. **A degraded or failed section (structure, product, or keyword analysis) must not fail the whole report** — produce whatever sections do have complete data normally, and present only the affected section as partial/unavailable rather than aborting report generation entirely.

### Step 3 · Full-Month KPIs (MoM + YoY)

**Core KPIs**: Spend, Sales, ACOS, ROAS, Impressions, Clicks, CTR, CVR.

For each: this-month value, last-month value (if `compareBaseline` includes `mom`), same-month-last-year value (if includes `yoy`), and the % change against each baseline — computed independently per Step 3's zero-denominator rules below, never averaged across baselines.

**Zero-denominator handling** (same discipline as any period comparison): if the baseline period's value is `0` and this month's is nonzero, there's no valid percentage — report "N/A (no prior baseline)," never a fabricated large number or "+∞%". If both are `0`, report "flat / no activity."

**Ratio-metric display rule**: confirmed percentage metrics such as `ACOS`, `CTR`, `CVR`, `TACOS`, and the derived `*Rate` metrics explicitly listed in Platform Notes are pre-scaled ×100. Append `%` directly, don't re-scale. Do not infer an unlisted field's scale from its name alone. `ROAS`/`CPC`/`CPA` are plain ratios, no `%`.

### Step 4 · Goal Attainment (if `monthlyTarget` supplied)

Compare the relevant KPI's actual this-month value against `monthlyTarget.target` — **the attainment formula depends on `monthlyTarget.direction`,** don't infer direction from the metric name alone:

- **`direction: "at_least"`** (hit-or-exceed a floor — typically `Sales`, `Conversions`, `ROAS`, or a *spend goal* meaning "make sure we deploy at least this much budget"): attainment `= actual / target × 100`; "exceeded" means `actual > target`.
- **`direction: "at_most"`** (stay at-or-under a ceiling — typically `ACOS`, `CPC`, `CPA`, or a *spend cap* meaning "don't blow past this budget"): attainment `= target / actual × 100`, or state it plainly as "under target" / "over target by X" rather than forcing a percentage that reads backwards — a lower `actual` than `target` is the good outcome here.

**`Spend` is genuinely ambiguous without `direction`** — it can mean either a budget cap (`at_most`: don't overspend) or a deployment goal (`at_least`: make sure the budget actually gets spent). Don't default it to either interpretation silently. If `monthlyTarget.direction` is missing for a `Spend` target specifically, ask the user which they meant, or state explicitly which assumption you're using and why, rather than guessing. `ACOS`/`CPC`/`CPA` and `Sales`/`Conversions`/`ROAS` are unambiguous enough that a missing `direction` can default to `at_most` and `at_least` respectively, but `Spend` should not get a silent default.

Report a plain-language verdict either way ("hit," "missed by X," "exceeded by X") consistent with the direction above. If `monthlyTarget` wasn't supplied, omit this section entirely rather than inventing a target or comparing against an arbitrary baseline.

### Step 5 · Structural Analysis

Using Step 2's (d)/(e) AdGroup-level data, compute **share of total Spend/Sales** (not just raw totals) for three breakdowns, each month independently, then compare the share shift MoM:

- **By campaign type** (`campaign.campaignType_`): SP / SB / SD share of total Spend and Sales.
- **By site** (`profile.countryCode_`): only meaningful when `profileIds` spans multiple stores/countries.
- **By portfolio** (`portfolio.portfolioId_`, displayed using `portfolio.portfolioName_`): rows with no portfolio should be grouped as "no portfolio," not silently dropped.

Report both months' share percentages and the point-change (e.g. "SP share: 62% → 58%, -4pp"), not just one month's snapshot — a structural shift is only visible in the comparison, not a single period's numbers.

### Step 6 · Product Analysis

**Top ASIN MoM changes**: follow the same rigorous join procedure as [sparkx-query-ads-performance's Period-over-Period and Top Movers example](../sparkx-query-ads-performance/references/example-period-comparison-top-movers.md) — join Step 2's (f)/(g) by `asin.asin_` (not by title), bucket into new/disappeared/present-in-both, floor the "% change" ranking on the **prior month's** (denominator) value, and show both months' raw values plus the absolute delta alongside any percentage.

**Newly-advertised-product performance**: for ASINs identified in Step 2h (first ran SP this month, no earlier sales observed — excluding the ones Step 2h flagged as existing products newly put on SP), report their this-month `TotalSalesAmount`/`OrderCount`/`TACOS` from Step 2f (the actual metrics that call requests — not `Sales`/`Conversions`, which aren't part of it) — there is no "last month" **advertising** baseline for these, so don't compute a MoM % for them; present as "first advertised this month" with their standalone numbers, and never as "newly launched" unless the customer confirmed the listing date from their own records. **Don't assume every newly advertised ASIN is present in Step 2f**: if 2f was reduced to a disclosed spend/sales-ranked sample (per Step 2's pagination fallback), first-SP-go-live candidates — which usually have low sales — likely fall outside the top sample. In that case, issue a separate `get_ads_perf` (`factEntity: asin`) call scoped to the Step 2h ASIN list (`filters` on `asin.asin_`) to fetch their performance, rather than reporting them as "no data" just because they weren't in the Top-ASIN sample. **If Step 2h's candidate list is large, batch this supplemental call** — split the ASIN list into chunks of a reasonable size for the `in` filter rather than one unbounded `asin.asin_: {"in": [...hundreds...]}` call, fully paginate each batch (`hasNextPage`), and merge/dedupe the batches' results by `asin.asin_` before reporting — don't silently drop ASINs because a single oversized call or an unpaginated batch left some out.

**Long-tail situation**: from Step 2f's full (paginated) ASIN list, compute what share of total Sales comes from the top N ASINs vs the rest (a simple Pareto-style cut, e.g. "top 20% of ASINs account for X% of Sales") — this characterizes concentration, not a specific product recommendation.

### Step 7 · Keyword Analysis

**Top keyword performance**: from Step 2i, rank by Spend or Sales, report Impressions/Clicks/Spend/Sales/ACOS per keyword. If a MoM comparison is wanted, pull the same-shape data for last month and join by `target.targetId_` the same way as Step 6.

**Search-term negatives and harvesting are out of scope here.** Doing them properly needs brand terms, a whitelist, own ASINs, the exact keywords already running, match-type sources and order thresholds by product stage - that is `sparkx-search-term-diagnosis` (if installed). In the report, add one line pointing to it ("要看该否哪些词、哪些词值得单独投，可以跑搜索词诊断"), and offer to run it for the same month.

**Zero-Sales ACOS handling** (Step 2i): a keyword with `Sales = 0` has an undefined `ACOS` - never treat it as "infinite" or sort it to the extreme end of an ACOS ranking; show its Spend and "no sales" instead.

### Step 8 · Issues List + Attribution

Compile the notable findings from Steps 3/5/6/7 (e.g. "ACOS worsened driven by a mix shift toward SD," "ASIN X's sales collapsed," "Portfolio Y's share shrank") and cross-reference Step 2k's operation log for changes in the same window that might explain them.

Correlate with **human** changes first (people's budget / bid / status / managed-group setting changes); the AI's own adjustments are its normal operation, not a finding on their own. If the month or its baseline covers a promotion **the user confirmed**, attribute the swing to it before anything else; an unconfirmed signal only gets the "possibly promotion-related" label (see "Shared Rules").

**Correlation, not causation** — same discipline as the weekly skill: say "ACOS rose in the same window a bid change was recorded on this campaign" rather than "the bid change caused the ACOS rise," unless the operation log pinpoints the exact change and the timing lines up precisely enough to say so with confidence.

### Step 9 · Next-Month Plan

Derive 3-6 structural-adjustment recommendations from Steps 5-8, e.g.:
- Structural share shift toward an underperforming type → recommend rebalancing budget back toward the higher-ROAS type
- A long-tail concentration finding → recommend consolidating spend toward top performers or testing budget on emerging mid-tier ASINs
- Search-term work (negatives, harvesting) → recommend running `sparkx-search-term-diagnosis` (if installed) for the month
- Campaigns in a running managed group → recommend the group's levers, not bids / budgets (see "Shared Rules")

**Every recommendation must have**: action + target (specific campaign/ASIN/keyword) + evidence (data) — same requirement as the weekly skill.

## Multi-Store and Currency

When `profileIds` spans multiple stores:
- All monetary metrics from `get_ads_perf` auto-aggregate to **USD** — label dollar amounts "(USD)" explicitly.
- **Steps 2a/2b/2c (account-level KPIs) deliberately do NOT get `profile.profileId_` added.** They're single blended totals for the whole month (no dimension in `select` at all) — adding a `profile` field would change the grouping from "one row for the month" to "one row per profile per month," which is a different question (per-store KPIs, not the one blended KPI overview Step 3 expects). If the customer wants each store's KPIs broken out separately, that's a distinct call with `profile.profileId_`/`profile.profileName_` added to `select` alongside whatever else is there — issue it separately rather than trying to derive one shape from the other.
- **Steps 2d/2e (AdGroup-level) need `profile.profileId_`/`profile.profileName_` added to `select`** — they already carry `profile.countryCode_` for the Step 5 "by site" breakdown, but `countryCode_` alone doesn't disambiguate two profiles sharing a country, and Step 8's attribution needs to know which store a given adGroup/campaign belongs to.
- **Step 2f/2g (Top ASINs) — decide which question you're answering, same as `sparkx-weekly-ads-report`'s equivalent call:** for one cross-store blended Top-N, don't add `profile.profileId_` (the call as written already aggregates `TotalSalesAmount` per ASIN across every profile in `profileIds`). For each store's own Top-N, add `profile.profileId_`/`profile.profileName_` — but note that once you do, `orderBy`+`pageSize` returns the top rows by *global* rank across every store's ASINs mixed together, not N rows per store; a genuine per-store Top-N needs one call per `profileId`, or the full set pulled and grouped client-side.
- `asin.asinPrice_` (if ever added to this report) stays local currency, unaffected by the USD-aggregation rule above.
- The "site" breakdown in Step 5 is only meaningful for a multi-country `profileIds` selection — for a single-store report, omit it or note it's not applicable.

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

**Plain-text fallback**: any severity markers or direction arrows used below are for rendering contexts that support them (chat UIs, rendered markdown). In a plain-text-only output context, replace them with words instead ("High"/"Medium" for severity, "up"/"down"/"flat" for direction).

### markdown mode (default)

```markdown
# Monthly Ads Report · {profile_name}
**Month**: {month} ({day_count} days)
**Baseline**: {MoM / YoY / both}
{If data may be incomplete due to T+2 delay, or day-count differs from the baseline month, note it here}

## 1. Monthly KPI Overview

{Show only the column(s) that match `compareBaseline`: `mom` → drop the "MoM Change" column entirely; `yoy` → drop the "YoY Change" column entirely; `mom+yoy` → show both, as below. Don't display a comparison column the report didn't actually request/compute. Each cell shows the baseline's own raw value alongside the % change — not the % alone — so the reader isn't left guessing whether "+8.4%" is $100 or $100,000: e.g. "$12,300 / +8.4%".}

| Metric | This Month | MoM Change | YoY Change |
|---|---|---|---|
| Spend | ${spend} | ${last_month_spend} / {mom%} | ${last_year_spend} / {yoy%} |
| Sales | ${sales} | ${last_month_sales} / {mom%} | ${last_year_sales} / {yoy%} |
| ACOS | {acos}% | {last_month_acos}% / {mom%} | {last_year_acos}% / {yoy%} |
| ROAS | {roas} | {last_month_roas} / {mom%} | {last_year_roas} / {yoy%} |
| Impressions / Clicks / CTR / CVR | ... | ... | ... |

## 2. Goal Attainment
{Only if monthlyTarget was supplied — actual vs target, % attainment, verdict}

## 3. Structural Analysis

{Step 5 computes share of both Spend and Sales — show both as separate columns per breakdown below, since a category's spend-share and sales-share can move in different directions (e.g. shrinking spend-share with growing sales-share signals improving efficiency, not decline).}

### By Campaign Type
| Type | This Month Spend Share | Last Month Spend Share | Spend Share Change | This Month Sales Share | Last Month Sales Share | Sales Share Change |
|---|---|---|---|---|---|---|
| SP | {pct} | {pct} | {pp change} | {pct} | {pct} | {pp change} |
| SB | ... | ... | ... | ... | ... | ... |
| SD | ... | ... | ... | ... | ... | ... |

### By Site (if multi-country)
{same format}

### By Portfolio
{same format}

## 4. Product Analysis

### Top ASIN Changes (MoM)
| ASIN | This Month Sales | Last Month Sales | Change |
|---|---|---|---|
| ... | ... | ... | ... |

### First Advertised This Month
{table — standalone figures, no MoM %}
{Say in one line that this is first SP go-live, not listing date, and name separately any ASIN that already had sales before it.}

### Long-Tail Concentration
{one or two sentences + a simple share breakdown}

## 5. Keyword Analysis

### Top Keywords
{table}

{Only if sparkx-search-term-diagnosis is installed: one line pointing to it for search-term negatives / harvesting, and offer to run it for this month. Otherwise omit this line}

## 6. Issues List

- **{issue}**: {evidence} — {correlated change from operation log, if any, framed as correlation}

## 7. Next Month's Plan

1. **{action}** {target}
   - Evidence: {data}
2. ...

---
_Generated: {timestamp} · Data source: SparkX AI MCP · Skill: sparkx-monthly-ads-report v{version}_
```

### structured_report mode

Output JSON schema:
```json
{
  "period": {"month": "...", "dayCount": ...},
  "dataFreshnessWarning": null,
  "kpiCards": [{"metric": "spend", "current": ..., "momValue": null, "momPct": null, "yoyValue": null, "yoyPct": null}],
  "goalAttainment": [{"metric": "...", "target": ..., "actual": ..., "direction": "at_least|at_most", "attainmentPct": ...}],
  "structure": {
    "byCampaignType": [{"type": "...", "thisMonthSpendShare": ..., "lastMonthSpendShare": ..., "spendShareChangePp": ..., "thisMonthSalesShare": ..., "lastMonthSalesShare": ..., "salesShareChangePp": ...}],
    "bySite": [...],
    "byPortfolio": [...]
  },
  "productAnalysis": {
    "topAsinChanges": [...],
    "newlyAdvertisedProducts": [...],
    "existingProductsNewlyAdvertised": [...],
    "longTail": {"topSharePct": ..., "topNCount": ...}
  },
  "keywordAnalysis": {
    "topKeywords": [...],
    "searchTermPointer": null
  },
  "issues": [{"issue": "...", "evidence": "...", "correlatedChange": "..."}],
  "nextMonthPlan": [{"priority": 1, "action": "...", "target": "...", "evidence": "..."}]
}
```
`keywordAnalysis.searchTermPointer` is `"sparkx-search-term-diagnosis"` only when that skill is installed, otherwise `null`. `kpiCards[].momValue`/`momPct` and `yoyValue`/`yoyPct` should be `null` for whichever baseline `compareBaseline` didn't request (e.g. all four stay populated for `mom+yoy`, but both `yoyValue` and `yoyPct` are `null` throughout when `compareBaseline=mom`) — never fabricate a value for a baseline that wasn't computed. `momValue`/`yoyValue` carry the baseline period's own raw figure (not just the % change), matching the markdown template's "raw value / % change" cell format.

## Data Boundaries

- **Paid Sponsored Ads data only** — no DSP, no AMC
- **`monthlyTarget` is user-supplied, not tool-derived** — this skill has no way to independently know what a customer's KPI goal should be
- **No structural analysis below the AdGroup/portfolio/campaign-type level** — SKU-level margin/profitability analysis is out of scope
- **Cannot reliably compute "real-time remaining budget"** — same caveat as sparkx-weekly-ads-report; `dailyBudget`/`currentBudget` are configuration values, not a live spend ledger
- **`get_entity_metadata` has no historical-snapshot capability** — "this month's config vs last month's config" can only be inferred from `get_operation_log`'s change records, not from querying current config as if it were historical
- **No search-term negatives or harvesting** — those come from `sparkx-search-term-diagnosis` (if installed), which applies brand / whitelist / exact-keyword checks this report doesn't

## Example Call

**User input**:
> 给 Demo US 出个上个月的月报，ACOS 目标是 25%

**Skill flow**:
1. Resolve the profile: `get_user_authorized_context` → find Demo US's `profileId`
2. `month` = last full calendar month; `monthlyTarget` = `{"metric": "ACOS", "target": 25, "direction": "at_most"}`
3. Run Steps 2-9
4. Output the markdown report — in Chinese, since the user asked in Chinese

## Error Handling

Follows the shared error envelope used by all three underlying tools (`isError`/`errorType`, see [`references/platform-notes.md`](references/platform-notes.md)).

| Situation | Handling |
|---|---|
| `profileIds` is empty | Follow "Resolving `profileIds`" above — call `get_user_authorized_context` first, then apply those rules; ask the user to pick only when those rules actually require it |
| Any call returns `isError: true` | Handle per `errorType` — `invalid_params` usually means a construction bug in this skill's own call (check field names/date ranges first); `rate_limited` → wait `retryAfterSeconds`, don't retry immediately |
| `effectiveProfileIds` doesn't match requested `profileIds` | Explain the scope mismatch before concluding "no data" |
| YoY window would exceed the 15-month lookback | Say so explicitly and omit the YoY column rather than sending an invalid request or silently dropping it without explanation |
| `get_operation_log` returns `truncated: true` | Split into sub-windows per its "Getting a Complete Count" procedure; note in the report if the operation count ends up as a partial/lower-bound figure |
| A time window is genuinely missing data (not an error) | State clearly which days/range is missing, and still produce the report with what's available |

## Not Covered by This Skill

- Weekly-cadence recap → `sparkx-weekly-ads-report`
- Quarterly/QBR strategic review → `quarterly-ads-report` (not yet built)
- Deep root-cause attribution on a single campaign → [ACOS root-cause investigation example](../sparkx-query-ads-performance/references/example-acos-root-cause-investigation.md)
- SKU-level margin/profitability analysis (needs the customer's own cost data, not just ad data)
- Search-term negatives and harvesting → `sparkx-search-term-diagnosis` (if installed)
- Restoring bids / budgets / managed-group settings after a promotion → `sparkx-promo-reset` (if installed)
