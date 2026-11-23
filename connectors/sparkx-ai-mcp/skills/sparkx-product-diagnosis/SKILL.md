---
name: sparkx-product-diagnosis
description: >-
  Diagnose product-level (ASIN) health: rank products by spend/sales/ACOS, segment the catalog into
  a portfolio tier (star / core / long-tail) and, separately, a lifecycle stage
  (new / growth / mature / declining) from SP advertising age and total-sales trend, compare sibling
  variants under a parent ASIN, produce a diagnostic card for flagged underperformers (inventory/eligibility/buy-box
  issues, correlated operation-log changes), and give keep/optimize/cut recommendations. Use when
  the user asks "我哪些 ASIN 有问题", "变体谁在拖后腿", "新品该不该继续投", "product diagnosis",
  "ASIN health check". Not for account-wide structural share analysis (use sparkx-ads-structure-analysis)
  or periodic WoW/MoM recaps (use sparkx-weekly-ads-report / sparkx-monthly-ads-report).
metadata:
  version: 1.2.2
---

# Product Diagnosis

## Scope: This Is an Orchestration Skill, Not a New MCP Tool

This skill does **not** map to a single MCP tool of its own — it orchestrates three existing read tools, each already covered by its own skill:

- `get_ads_perf` → [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md)
- `get_entity_metadata` → [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md)
- `get_operation_log` → [sparkx-query-operation-log](../sparkx-query-operation-log/SKILL.md) (used in Step 2e for the diagnostic card's correlated-changes check)

> **Dependency — install these three base skills alongside this one:** `sparkx-query-ads-performance`, `sparkx-query-entity-metadata`, `sparkx-query-operation-log`. Skills install as sibling directories under your current agent's skills root (`.claude/skills/<name>/` for Claude Code; the equivalent root for other agents — see the installation notes in [README](../README.md)), which is exactly what the `../query-.../…` links above (and elsewhere in this doc) resolve against — if a base skill isn't installed there, those links won't resolve and this skill can't run. Install all three first.

**Read all three SKILL.md files first** (parameter formats, field-naming rules, the Ratio Metric Display Rule, and — specific to this skill — [`references/ad-type-dependent-metrics.md`](references/ad-type-dependent-metrics.md)'s rule that ASIN business metrics must never be joined or filtered against campaign/adGroup/aiGroup-level fields) plus [`references/platform-notes.md`](references/platform-notes.md) (auth flow, error handling, pagination, date-range limits, currency rules). This document only covers logic specific to product diagnosis; it doesn't repeat what the base skills already document.

Rewritten against the new tool's conventions from the start — carries forward the discipline established across `sparkx-weekly-ads-report`/`sparkx-monthly-ads-report`/`sparkx-ads-structure-analysis`: full `profileIds` resolution rules, currency-aware thresholds, output-language adaptivity, disclosed sampling fallback, and zero-denominator handling.

## Output Language: Always Match the User, Never Hard-Code Chinese or English

**The worked examples and output templates below are written in Chinese** (matching this product's primary customer base), but they are **structural illustrations, not literal text to copy verbatim**. Generate the actual report in whatever language the user asked in. When calling `get_ads_perf`, also set the `language` parameter (`zh`/`en`/`ja`) to match the customer's language. **`get_entity_metadata` has no `language` parameter** — it's not in that tool's documented parameter list. Localize its enum values (e.g. `asinInventoryStatus`, `asinSpEligibilityStatus`) using the returned `{field}Text` companion fields, or `sparkx-query-entity-metadata`'s **own** [`enum-i18n.md`](../sparkx-query-entity-metadata/references/enum-i18n.md) if a given enum has no `Text` companion — that tool's enum-i18n file, not `sparkx-query-ads-performance`'s, since the two don't cover an identical field set. Only fall back to `sparkx-query-ads-performance`'s [`enum-i18n.md`](../sparkx-query-ads-performance/references/enum-i18n.md) for fields that are actually `get_ads_perf` fields (e.g. when this skill's Step 2a/2b calls need enum labels). Don't pass `language` to `get_entity_metadata` expecting it to have the same effect as on `get_ads_perf`.

## When to Use

**Trigger phrases**: 商品诊断, 哪些 ASIN 有问题, 变体对比, 新品该不该投, product diagnosis, ASIN health

**User roles**: ads managers, account managers doing a product-level deep-dive

**Core question**: which products are healthy, which need attention, and what specifically is wrong with the ones that don't

**Not for**:
- Account-wide spend/efficiency structure by campaign type / site / portfolio → `sparkx-ads-structure-analysis`
- Periodic WoW/MoM cadence recaps → `sparkx-weekly-ads-report` / `sparkx-monthly-ads-report`
- Keyword/search-term level diagnosis → `sparkx-search-term-diagnosis` (if installed) (it can be scoped to one product or parent ASIN)

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `profileIds` | array[long] | No | — | See "Resolving `profileIds`" below |
| `granularity` | enum | No | `asin` | `asin` (child ASIN) \| `parentAsin` \| `variant` (siblings under one parent — requires `parentAsin` or a specific ASIN to anchor on, see "Granularity" below) |
| `scope` | enum | No | `topN` | `topN` \| `all` \| `specifiedAsins` \| `underperformingOnly` |
| `topN` | int | No | 20 | Only used when `scope=topN` |
| `specifiedAsins` | array[string] | No | — | Only used when `scope=specifiedAsins` |
| `dateStart` / `dateEnd` | string (`YYYY-MM-DD`) | No | Trailing 30 days ending yesterday | The analysis window — must satisfy the 90-day span / 15-month lookback caps like any other `get_ads_perf` call |
| `classificationRules` | object | No | the defaults in Step 3 | Customer overrides for either axis or the recent-deterioration signal — any of `starSpendPrefix`, `coreSpendPrefix`, `newSpAgeDays`, `minValidWeeks`, `decliningSlopeMax`, `decliningDrawdownMin`, `cliffDrawdownMin`, `growthSlopeMin`, `stockoutDaysMax`, `recentSalesDeclineMin`, `recentSalesBaselineOrders`, `recentSalesBaselineAmount`, `recentAdOrderDeclineMin`, `recentAdOrderBaselineMin`. Whatever the customer supplies wins; everything they leave out keeps the default. **Echo the values you actually used in the output either way**, so a reader never has to guess which set produced the labels |

### Resolving `profileIds`

Always call `get_user_authorized_context` first to get the authorized `profiles` list, then apply exactly one of these cases:

1. **The user named specific store(s)** → resolve the name(s) against the authorized list and query only the matching profile(s).
2. **The user explicitly said "all stores" / "全账号" / equivalent** → query all authorized `profileIds`.
3. **The user didn't name a store, and there's only one authorized profile** → use it directly — there's nothing to ask.
4. **The user didn't name a store, and there are multiple authorized profiles**:
   - **5 or fewer** → you may default to using all of them.
   - **More than 5** → do not silently roll everyone up. Hand the user the `profiles` list and ask them to pick one, several, or explicitly confirm "all stores" first.

### Granularity

**`asin`** (default) — child ASIN is the unit of analysis throughout.

**`parentAsin`** — roll up to the parent level. Query `get_ads_perf` (`factEntity: asin`) with `select` including `asin.parent_asin_`, and aggregate child-ASIN rows under the same parent client-side (this tool has no native `factEntity: parentAsin` for performance data — only `get_entity_metadata`'s `asin` entity nests parent-ASIN fields alongside child fields, and that's metadata, not performance metrics).

**`variant`** — compare sibling child ASINs under one parent. **Requires an anchor**: either the user names a specific parent ASIN, or names one child ASIN (resolve its `parentAsin` via `get_entity_metadata` first — plain camelCase, that tool's convention, not `get_ads_perf`'s `asin.parent_asin_` — then pull all children under that parent). Don't attempt a "variant" comparison across the whole catalog at once — it's inherently a one-parent-at-a-time comparison; if the user wants this for many parents, run it once per parent and present each as its own comparison, not a single merged table.

## "Which variant should get the budget?"

The question behind a variant comparison is usually not "which one is worse" but "where should
the money go". Answer it, but be exact about what can actually be moved.

**There is no per-ASIN budget.** Budget lives on the campaign (`dailyBudget`); a product has
none. So a budget recommendation is always one of three shapes, and you should name which one
you mean:

| What the user wants | What that actually is |
|---|---|
| Spend more on variant A | raise the budget of the campaign(s) where A is the product being advertised |
| Stop wasting on variant B | pause or archive B's product ad, or move it out of a shared ad group |
| Split budget between variants | only possible if they sit in **different** campaigns - otherwise the campaign budget is shared and cannot be apportioned |

⚠️ **Check whether the variants share a campaign before promising anything.** Siblings very
often sit in one ad group, and then "give A more budget" is not available at all - the honest
answer is "these two share a campaign budget; to fund them separately they have to be split
into different campaigns first". Query `get_entity_metadata(entity='productAd')` for the ASINs
and compare their `adGroupId` / `campaignId`.

⚠️ **Do not attribute a shared campaign's spend to one variant.** When several ASINs run in one
campaign, campaign- or ad-group-level metrics belong to the whole set. For per-product figures
use `factEntity: "productAd"`; see the fan-out rules in `sparkx-query-ads-performance`.

State the comparison before the recommendation: each variant's own spend, sales and ACOS from
`productAd` rows, then what you suggest moving and what that costs the other variant.

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

In product diagnosis a promotion is the common trap, and it bites in two different places:

- **In the comparison window**, the post-promo drop makes a healthy product's period-over-period
  figures look like a collapse.
- **Anywhere in Step 2f's 12-week series**, a promotion week can become the series peak, which
  inflates the drawdown gate and pushes the lifecycle stage to Declining on its own — see Step 3.

When there is a signal either way, keep the label but mark it "possibly post-promotion", name
the week, and ask; drop the label only after the user confirms.

## Workflow

### Step 1 · Define the Analysis Window

Default: trailing 30 days ending yesterday (T+2 delay — note if the window's end is within 2 days of today, the most recent day(s) may be incomplete). If the user gives an explicit range, confirm it satisfies the 90-day span / 15-month lookback caps before issuing the call; split into multiple ≤90-day calls if it doesn't, per the standard procedure.

**Also define a comparison window** (immediately preceding period, same length) — needed for Step 5's diagnostic correlation and the period-over-period figures in the ranking. Same equal-length-prior-period discipline as the report skills.

**And a separate 12-week lifecycle lookback**, which is *not* derived from either of the above — see Step 2f. Step 3's lifecycle stage is built on that window alone, so that a 7-day report and a 90-day report return the same stage for the same product.

### Step 2 · Pull Data

**a. This-period ASIN performance**
```json
{
  "profileIds": [4404871489220462],
  "factEntity": "asin",
  "dateStart": "{window start}",
  "dateEnd": "{window end}",
  "select": ["asin.asin_", "asin.asinTitle_", "asin.parent_asin_"],
  "metrics": ["Spend", "Sales", "Conversions", "ACOS", "TotalSalesAmount", "OrderCount", "TACOS", "Sessions", "BuyBoxPercentage", "UnavailabilityRate", "CustomerReturns"],
  "pageSize": 500,
  "userContext": "Product diagnosis - this period's ASIN performance"
}
```
**⚠️ `Spend`/`ACOS` alongside `asin`-only business metrics in one call**: `get_ads_perf`'s ASIN business metrics (`TotalSalesAmount`, `Sessions`, `BuyBoxPercentage`, etc.) are confirmed valid only on `factEntity: asin`, and so are the regular ad metrics when queried at that same `factEntity` — this is fine as one call. What's **not** fine is joining or filtering these `asin`-only business metrics against campaign/adGroup/aiGroup-level fields (see [`ad-type-dependent-metrics.md`](references/ad-type-dependent-metrics.md)) — don't add `campaign.*`/`adGroup.*` dimension fields to this call's `select`.

**⚠️ Campaign-level spend is never split by ASIN.** If you also show a campaign-level figure next to an ASIN-level one, say which is which. Filtering a campaign-level query by ASIN **selects rows, it does not divide the money**: it returns the campaigns that contain that ASIN, each with its **whole** spend, including the other products in them. So campaign-level spend >= that ASIN's own spend whenever a campaign carries more than one product, and the gap is simply the other products' share — not a reconciliation error, and not something to chase. Only a campaign with exactly one ad group and one promoted product should match an ASIN figure, and even then only within T+N backfill. Label the gap when you show it; a customer seeing two numbers and no explanation will read it as a bug.

**⚠️ `Sales` and `TotalSalesAmount` are two different things, both requested deliberately**: `Sales` is ad-attributed sales (the numerator context for `ACOS`, whose formula is `Spend/Sales×100`); `TotalSalesAmount` is the ASIN's total business sales including organic (the denominator for `TACOS`, whose formula is ad `Spend/TotalSalesAmount`). Don't drop either thinking the other covers it — see Step 3's zero-denominator handling, which depends on both being present.

**✅ `TotalSalesAmount`/`TACOS` work on Vendor profiles too.** They are unified metrics: on a Vendor row they are computed on the shipped basis, deliberately so that Seller and Vendor rows can be summed in one query. **Do not re-query with `OrderedRevenue`/`ShippedRevenue` on seeing a Vendor profile** - that was guidance from before the metrics were unified, and it costs a round trip for nothing. (What remains Vendor-specific is the *extra* breakdown: `OrderedRevenue`/`OrderedTACOS` only under `distributorView_=MANUFACTURING`, `ShippedRevenue`/`ShippedTACOS`/`ShippedCogs`/`NetPPM` on both views.) A genuinely null `TotalSalesAmount` means no sales in the window, not a wrong field.


Scope this call per `scope`:
- `topN` → `orderBy` on the primary ranking metric (default `Spend` descending), `pageSize` = `max(1, min(topN, 500))` — `get_ads_perf` rejects a `pageSize` of `0`, a negative number, or anything over `500` with `invalid_params` (it does **not** clamp), so both ends need guarding: a `topN` of `0` must not become `pageSize: 0`, and if `topN > 500`, keep `pageSize: 500` and loop `page` while `hasNextPage` to collect the remainder instead of requesting an oversized page
- `all` → fully paginate, no `orderBy` requirement, disclosed sampling fallback applies at scale
- `specifiedAsins` → `filters: {"asin.asin_": {"in": [...]}}`, batched per "Batching Large ASIN Lists" below if the list is long
- `underperformingOnly` → pull the full/sampled population first (Step 3-4 needs the full picture to correctly classify "underperforming" relative to the rest of the catalog), then filter to the **flagged set defined in Step 3** when presenting — don't pre-filter the query itself on a guessed threshold before you've computed both axes

**`granularity=variant` overrides the above regardless of `scope`**: add `filters: {"asin.parent_asin_": "{anchored parentAsin}"}` to this call (on top of, not instead of, whatever `scope` would otherwise apply) so it returns only the anchored parent's own children — not a `topN`/`all` sweep of the whole catalog. Resolve the anchor's `parentAsin` first (per "Granularity" above) before issuing this call.

**`granularity=parentAsin` also overrides the `topN` scope rule above — don't apply `orderBy`/`pageSize` at the child-ASIN query level.** Ranking by child-level `Spend` and capping `pageSize` *before* aggregating to parents produces an incomplete/wrong parent ranking — a parent whose spend is split across several children, none individually in the child-level top N, would be undercounted or missed entirely, even though its *aggregated* total might rank highly. Instead: fully paginate the child-ASIN population first (or, if that's impractical at catalog scale, fall back to a spend-ranked **child** sample per the disclosed-sampling-fallback rule — and if you do, say explicitly that the parent ranking is therefore based on a child-level sample, not the complete population), aggregate child rows into parents by `asin.parent_asin_` client-side, **then** apply `topN` to the aggregated parent-level results.

**b. Prior-period ASIN performance** — same shape as (a), `dateStart`/`dateEnd` shifted to the comparison window, same `select`/`filters` so the two periods are comparable.

**c. New-product identification**: `get_entity_metadata` (`entity: asin`). **`asinOpenDate` is NOT a filterable field**, so don't filter the call on it. Pull the asin metadata for the current analysis set (**fully paginate — loop `page` while `hasNextPage` is `true`; default page size is 100, so a catalog past one page silently truncates otherwise**), then read the returned `asinOpenDate` and apply the **New** cutoff **client-side**. **The cutoff is a fixed age (90 days by default), not the analysis window.** Tying it to the window was wrong in both directions: a 7-day window made almost nothing New, and a 12-month window made a year-old product New.

> **⚠️ `asinOpenDate` is the SP go-live date, not the date the product was first listed.** The column behind it is `sp_open_date`, for both `asinOpenDate` and `parentAsinOpenDate`. An ASIN that sold for years and only recently started running Sponsored Products carries a recent `asinOpenDate` and would be labelled New. So call this **SP advertising age** in the output, never "listing age", and **falsify it against Step 2f's own series**: if the weeks before `asinOpenDate` already carry `TotalSalesAmount`, the product is not new - it is newly advertised. Report it as **newly advertised, not a new product** and classify it on the trend instead.

> **⚠️ One ASIN returns several rows, one per SKU, each with its own `asinOpenDate`.** The child-side query is not deduplicated, so a 12-ASIN request can come back as 22 rows with three different dates for the same ASIN (some on `Inactive` SKUs). **Take the earliest `asinOpenDate` across an ASIN's rows** - that is when this ASIN first went live on SP; the later ones are re-listings of individual SKUs. Picking whichever row arrives first, or the `Active` one, gives a different answer run to run.

> **⚠️ `parentAsinOpenDate` is not reproducible and must not decide a parent's New stage.** The parent side is deduplicated with `any(sp_open_date)`, which returns an arbitrary SKU's value and can differ between two identical calls. Under `granularity=parentAsin`, derive the parent's SP age as the **minimum of its children's `asinOpenDate`** instead, and say that is how it was derived. `asinOpenDate` is a datetime-with-timezone string, e.g. `"2026-06-01 00:00:00 PST"` (not `YYYYMMDD`, not `YYYY-MM-DD`; `campaignStartDate` is a string of no guaranteed shape, which is a different problem again), so parse it and mind the **PST timezone**. **Under `scope=specifiedAsins` or `granularity=variant`, scope this pull to the current analysis set** (the user's specified ASIN list, or the anchored parent's children) — don't scan the whole catalog and then tag "New" onto ASINs that aren't part of what's being analyzed.

**d. Stock cover and eligibility** — **two separate pulls, in this order. Don't merge them**: Axis B's stockout check feeds the flagged set, so scoping the stock-cover pull to flagged rows would be circular (a row cannot be flagged until it has been checked, and it cannot be checked until it is flagged).

- **d1 — stock cover, for the whole analysis set** (feeds Axis B, before any stage is assigned): `get_entity_metadata` (`entity: asin`), scoped to the analysis set and fully paginated. **The `select` depends on `granularity`** — the stockout gate needs the figure for the entity being classified, and under `granularity=parentAsin` that entity is the parent:
  - `granularity=asin` / `variant` — `select: ["asin", "asinDayAvailability30", "asinInventoryStatus"]`
  - `granularity=parentAsin` — `select: ["parentAsin", "parentAsinDayAvailability30", "parentAsinInventoryStatus"]`, then **deduplicate by `parentAsin`**: rows come back at child/SKU grain, so a parent with four children repeats its own figures four times. Counting those repeats, or averaging them, is not a different number — it is the same number counted several times.
  Keep `select` narrow either way rather than pulling the whole row for every ASIN in the catalog.
  ⚠️ **Do not compute the parent's available days from its children's.** They use different formulas: a parent is `floor(summedStock / summedDailyRate)` (each child contributes its own daily sales rate to the denominator), a child is `floor(stock x days / units)`. The field reference's own example gives a parent **34** days where its four children read **33 / 33 / 33 / 39** — neither the sum, the average, nor the minimum of the children reproduces it. Query the parent field.
  ⚠️ **`asinDayAvailability30` is per ASIN, but `asinInventoryStatus` is per SKU** — the same ASIN's rows repeat one identical availability figure while their statuses differ (a real ASIN came back `Active`, `Inactive`, `Inactive`). Collapse the availability by taking any row's value, and collapse the status as **`Active` if any SKU is `Active`**: one discontinued SKU does not make the ASIN unavailable. Never average or count the repeated availability rows.
  ⚠️ **A missing availability field means unknown, not zero.** Vendor profiles and Seller profiles without SP-API authorization omit the whole inventory group (`meta.hint` names those profileIds), and `asinDayAvailability30` / `parentAsinDayAvailability30` are also `null` when the product had no sales to project from. Say the stockout check could not be run rather than treating absence as "in stock".
- **d2 — eligibility, for Step 3's flagged set only** (feeds Step 5's diagnostic card, not the ranking and not either axis): `asinSpEligibilityStatus`/`asinSbEligibilityStatus`/`asinSdEligibilityStatus`. This is diagnostic detail — don't pull it for the whole catalog.
- **d3 — deleted-ASIN probe, flagged set only.** ⚠️ **`asinIsDelete` cannot be selected from `get_entity_metadata`.** It is a **filter parameter only**; it is not in that entity's output field list, and putting it in `select` is **silently ignored** (the server replies `Unknown select fields ignored: [asinIsDelete]` in `meta.hint`, and the call otherwise succeeds — so a "not deleted" conclusion drawn from its absence is worthless). Ask the question as a filter instead, in its own call:
  ```json
  {"entity": "asin", "filters": {"asin": {"in": ["<flagged ASINs>"]}, "asinIsDelete": 1}, "select": ["asin", "sku"]}
  ```
  Every ASIN that comes back is deleted; an empty result means none of them are. Rows are per SKU, so dedupe by `asin`. (The selectable `asinIsDelete` lives on the **`get_ads_perf`** side as the dimension `asin.asinIsDelete_` — a different tool with a different field set, which is why the name looks available but isn't here.)

**e. Operation log for flagged ASINs** (feeds Step 5 and the promotion signal): `get_operation_log`, from 7 days before the comparison window through the end of the analysis window (split if that exceeds 90 days), `resourceIds` scoped to `campaignId`/`adGroupId` (resolve each flagged ASIN → its `campaignId`/`adGroupId` via `get_entity_metadata`'s `productAd` entity first, since `get_operation_log` takes IDs, not ASINs directly). **`resourceIds.idEntity` has no `productAd` value** (see `sparkx-query-operation-log`'s field reference) — don't resolve to `amazonAdId` and try to pass it in; use `idEntity: "campaign"`/`"adGroup"` instead.

⚠️ **Those ids must be `amazonCampaignId` / `amazonAdGroupId`, not the internal `campaignId` / `adGroupId` the `productAd` entity returns.** Getting this wrong does not raise an error: with `entities` set as below, the filter simply matches nothing and you get an **empty result** that looks exactly like "nobody touched these campaigns". **Decide by the field name the value came out of, never by how long it looks** — a log row carries `entityId` (internal) and `amazonCampaignId` (Amazon) side by side, and lengths are not a contract. Magnitude is at best a smell test: if a number looks wrong for the field it is going into, re-check its source field. And treat an empty log for a busy campaign as a suspected id-type mistake before reporting it as a finding.

So the resolution is **three hops, not one**, and **both** levels need their own hop:

1. flagged ASIN → `get_entity_metadata` (`entity: productAd`) → internal `campaignId` **and** `adGroupId`
2. internal `campaignId` → `get_entity_metadata` (`entity: campaign`) → **`amazonCampaignId`** (this is the same call that supplies `campaignName`, `campaignState`, `aiGroupId` and `dailyBudget`, so it is not an extra round trip)
3. internal `adGroupId` → `get_entity_metadata` (`entity: adGroup`) → **`amazonAdGroupId`**. **Don't skip this one.** Step 2e asks for ad-group history too, and there is no ad-group equivalent hiding in the campaign rows — without this hop the `adGroup` scope is silently unfiltered.

⚠️ **Always pass `entities` explicitly.** Omitting it queries **every entity type except `audience`** — portfolio, profile, aiGroup, target, placement and the rest — which is how an ASIN-scoped question comes back carrying portfolio-level rows that have nothing to do with the product. Run **three separate calls**, not one:
- `entities: ["campaign"]` with the Amazon campaign ids
- `entities: ["adGroup"]` with the Amazon ad-group ids
- `entities: ["aiGroup"]` with the internal managed-group ids (below)

Separate calls also restore real pagination: `page` only works when a single non-`aiGroup` entity is specified, so a combined query is limit-only. It does not fail silently — it comes back with `meta.truncated: true` and no way to page — so **check `truncated` on every response** and, when it is set, split the query (by entity, then by sub-window) rather than reporting a partial log as the whole history.

⚠️ **The `productAd` resolution is far bigger than it looks, and it decides whether this step is worth running at all.** A real six-ASIN flagged set resolved to **1,556 product-ad rows across 144 campaigns**, and **one** ASIN alone sat in **120 campaigns and 177 ad groups**. So:
- **Paginate the resolution** (`total` and `hasNextPage` are both returned) and count the distinct campaigns **per ASIN** before querying any log.
- **Above ~20 campaigns for one ASIN, don't run the campaign-scoped log for it.** The result would be dominated by operations on campaigns that have nothing to do with this product, and presenting that as "correlated changes" is worse than presenting nothing. Say the ASIN is spread across N campaigns so campaign-level history isn't attributable to it, and fall back to what *is* ASIN-specific: the `productAdState` spread from this same resolution (how many of its product ads are enabled/paused/archived) and the carrying campaigns' current `campaignState`.
- **`campaignName` is NOT selectable on `productAd`** — the available fields are `adGroupId`, `amazonAdId`, `asin`, `campaignId`, `campaignType`, `productAdId`, `productAdState`, `profileId`, `sku`, and anything else in `select` is silently dropped with a `meta.hint`. Since the output must name entities rather than show bare IDs, follow the resolution with one `get_entity_metadata` (`entity: campaign`) call over the distinct `campaignId`s for `campaignName`, `campaignState`, `aiGroupId` and `dailyBudget` — that one call also supplies Step 5's "is it even still being advertised" check and the managed-group lookup below, so it is not an extra round trip.

⚠️ **The two mistakes above fail differently — don't confuse the symptoms.**
- **Wrong id type** (internal instead of Amazon), `entities` set correctly: the filter matches nothing, so you get an **empty result** of the right entity type.
- **`entities` omitted**: the query fans out across every entity type except `audience`, so you get **rows of other entities** — e.g. a `PORTFOLIO` row for a `Portfolio Out of Budget` event — regardless of which ids you passed.

Either way, fix the call rather than interpreting the result. A portfolio-level budget event may well be a real finding, but it is **not** evidence about this ASIN or even about these campaigns specifically, so it belongs in a separate, clearly labelled note. Read `entity` on every row either way.

⚠️ **An empty campaign-row result does not mean nothing happened.** For campaigns inside a managed group the changes are recorded on the group, not the campaign (see below). Beyond that, the campaign/adGroup result is never narrowed to the one product ad — say so whenever the customer might read it as ASIN-exclusive. **Also pull the managed-group rows**: for campaigns in a managed group (`aiGroupId` on the `campaign` entity), query `resourceIds: [{"idEntity": "aiGroup", "idType": "increment", "ids": [...]}]` - a target-ACOS or switch change on the group is invisible in the campaign rows. Classify people vs machines per "Shared Rules". **Check `truncated`** and follow the standard split-and-recurse procedure if so.

**⚠️ Steps 2c/2d/2e above are written for `granularity=asin`/`variant` (child-ASIN identity). Under `granularity=parentAsin`, each needs a parent-level adjustment — don't run them unchanged and silently produce child-level diagnostics under a parent-level report:**

- **New (2c)**: use the **earliest `asinOpenDate` across the parent's children**, and **not** `parentAsinOpenDate` — that column is `any(sp_open_date)` and returns an arbitrary child's value, so it is neither the earliest nor stable between calls (see 2c). The intent behind the old "use the parent's own field" rule still holds and is what the minimum delivers: don't infer the parent's status from whichever child happens to be queried first, or from an arbitrary one. A parent can mix long-standing and newly-added children, so the earliest child is the one that dates the parent — a parent is only New when **every** child is. If a customer specifically wants to know "which children under this parent are new," report that as a supplementary note on the parent's diagnostic card, not as the parent's own stage.
- **Stock cover (d1)**: already handled by d1's `granularity=parentAsin` branch above — `parentAsinDayAvailability30` and `parentAsinInventoryStatus`, deduplicated by `parentAsin`. Don't re-pull it here, and don't fall back to the children's `asinDayAvailability30` for the parent's stockout gate.
- **Eligibility (d2)**: prefer the parent-level fields — `parentAsinSpEligibilityStatus`/`parentAsinSbEligibilityStatus`/`parentAsinSdEligibilityStatus`, alongside the `parentAsinInventoryStatus` d1 already returned — as the primary signal for the parent's diagnostic card. **There is no `parentAsinIsDelete` field, and the child-level one is not readable either** — `asinIsDelete` is a filter, not an output field (see d3). So deletion status at the parent level is answered the same way as at the child level: run d3's probe over the parent's children and treat the parent as deleted only when **every** child comes back. Don't invent a parent-level flag, and don't read the probe's empty result for a *subset* of children as "the parent is alive". If the parent-level status looks healthy but the parent's aggregated performance is still flagged as Declining/underperforming, additionally check the individual children's `asinInventoryStatus`/eligibility (from 2d's child-level pull) to find which specific child is actually driving the problem, and list it as supporting detail under the parent's card.
- **Operation log (2e)**: expand the parent to its full child-ASIN list first (`get_entity_metadata`, `entity: asin`, `filters: {"parentAsin": "{parent}"}`), then resolve **each** child's `campaignId`/`adGroupId` via the `productAd` entity (same as the child-level procedure), and query `get_operation_log` across all of them. This is still campaign/adGroup-level, not parent/ASIN-exclusive — label it as such in the diagnostic card the same way the child-level version does, and additionally note it covers operations across all the parent's children, not just one.

**f. Twelve-week weekly series for the lifecycle stage** (feeds Step 3's Axis B):

```json
{
  "profileIds": [4404871489220462],
  "factEntity": "asin",
  "dateStart": "{the Monday 12 complete weeks back}",
  "dateEnd": "{the Sunday of the last complete week}",
  "select": ["asin.asin_", "toMonday(parseDateTime32BestEffort(date)) as week"],
  "metrics": ["TotalSalesAmount", "OrderCount", "Sessions", "Spend"],
  "pageSize": 500,
  "userContext": "Product diagnosis - 12-week lifecycle trend"
}
```

- **This window is independent of the Step 1 analysis window** — not the trailing 30 days, not
  the comparison window. Don't substitute either: a 30-day window cannot carry a 12-week trend,
  and the lifecycle stage would then change every time the user asked for a different reporting
  period, which is exactly the behaviour this axis exists to remove.
- **Align both ends to week boundaries** — start on a Monday, end on a Sunday — or the first
  and last buckets are partial weeks, and that trailing partial week reads as a decline that
  isn't there. Under the T+2 rule the last complete week is usually the week before last.
- **12 weeks, not 13**: 84 days fits one call; 13 weeks is 91 days and exceeds `get_ads_perf`'s
  90-day span cap, turning every lifecycle run into a two-call merge for one extra week of signal.
- **Year-over-year companion call** (for Step 3's seasonality check): same shape with both dates
  shifted back **364** days — 52 whole weeks, so Monday stays Monday; don't shift by 365. Run
  it when the shifted `dateStart` is still inside the 15-month lookback **and** the ASIN's
  `asinOpenDate` precedes it; otherwise skip it and say the check couldn't be run.
- Scope it to the same analysis set as 2a (the `asin.asin_` `in` filter under `specifiedAsins`,
  the `asin.parent_asin_` filter under `variant`) and fully paginate. **Under
  `granularity=parentAsin`, sum the children into the parent week by week *before* smoothing** —
  smoothing each child separately and averaging their slopes is the ratio-of-averages mistake the
  parent-aggregation rules elsewhere in this skill already warn about.

**Batching Large ASIN Lists** — the filter field differs by tool, don't carry one convention into the other:
- **`get_ads_perf`** (Step 2a/2b's `specifiedAsins` scope): filter field is `asin.asin_` (that tool's `entity.field_` convention).
- **`get_entity_metadata`** (Step 2c/d's flagged-ASIN follow-ups): filter field is plain `asin` (no prefix/suffix — that tool's camelCase convention).

Either way, when the list is long: split into chunks for the `in` filter rather than one unbounded call, fully paginate each batch, and merge/dedupe results by ASIN.

**Fully paginate (a)/(b) before analyzing** — loop `page` while `hasNextPage` is `true`. **If full pagination would be impractical at scale** (very large catalogs under `scope=all`), you may fall back to a spend-ranked sample instead of the full population — this fallback **must be disclosed explicitly**, stating what was actually covered, and **a degraded section must not fail the whole diagnosis** — produce whatever's complete and mark only the affected part as partial.

### Step 3 · Rank and Segment

**Ranking table**: sort by the requested/default metric (`Spend` unless the user asked for `Sales`/`ACOS` ranking specifically), showing `Spend`/`TotalSalesAmount`/`ACOS`/`TACOS` per ASIN. **Zero-denominator handling — `ACOS` and `TACOS` have different denominators, don't conflate them**: an ASIN with `Sales = 0` (ad-attributed sales) has undefined `ACOS`; an ASIN with `TotalSalesAmount = 0` (total business sales) has undefined `TACOS` — these can differ (e.g. an ASIN can have `Sales = 0` this period while still showing organic `TotalSalesAmount`, or vice versa). Check each independently and report "no ad sales this period" / "no total sales this period" as appropriate, never a fabricated ratio for either. If `TotalSalesAmount` is zero across every row, report that no total sales were returned for the window; do not infer a Seller/Vendor field mismatch or switch metric families solely from that result.

**Two independent classifications — don't collapse them into one label.** Every product gets a
**portfolio tier** (how much it matters to *this account's* spend right now) **and** a **lifecycle
stage** (where the product itself is in its life). The axes are orthogonal, and the pair carries
information neither one does alone: a star product can be declining, and surfacing that is the
most valuable thing this step does.

> **Why this is two axes and not one.** An earlier version of this skill merged both into a single
> five-way "lifecycle tier", which produced statements no operator would accept — that a product's
> *lifecycle* depends on its spend rank inside one account, that the same ASIN has a different
> lifecycle in a large account than in a small one, that a product cannot be both a top earner and
> in decline, and that "mature" doesn't exist at all. Report both axes, always.

> **These are default rules, not a certified classification.** State the cutoffs you actually used
> in the output, and use the customer's own definitions whenever they give them — every threshold
> below is a parameter, not a fact about Amazon.

#### Axis A — Portfolio tier

Account-relative and window-relative **by design**: the same ASIN is a star in a small account and
long-tail in a large one, and the tier moves when the analysis window moves. That is correct for
this axis — it answers "where is my money going", not "how old is this product".

Rank entities by this period's `Spend` (descending). "Top X% of spend" means the **smallest prefix
of that ranking whose cumulative share reaches X%, including the row that crosses X%** — so if the
first product alone is 60% of spend, it is the whole top 50%. First match wins.

| Tier | Default rule |
|---|---|
| 无广告投放 No ad spend | this row's `Spend` is `0` or `null` |
| 明星 Star | in the top 50% of spend (see above) **and** ACOS <= target ACOS |
| 腰部 Core | in the top 80% of spend |
| 长尾 Long-tail | the rest |

**An ASIN with no ad spend is not long-tail advertising, it is unadvertised.** The `asin` entity
returns organic rows too, and they come back with `Spend: null` — in one real run 8 of 20 rows
were like this. Dropping them into the bottom tier reads as "we spend a little here and it isn't
working", which is the opposite of what the row says. Give them **无广告投放 No ad spend** and keep them in the
table: an unadvertised ASIN with real `TotalSalesAmount` is a candidate to *start* advertising, which
is a finding the other tiers cannot express.

**When the analysis set's total `Spend` is `0`** (or every row is `0`/`null`), the cumulative-share
prefix is undefined — `0/0`. Do not fall back to an arbitrary split. Give **every** row
**无广告投放 No ad spend**, say no ad spend was recorded for the window, and rank the table by `TotalSalesAmount`
instead so the output is still useful. Axis B is unaffected and should still be reported: it does
not depend on spend.

**Star needs a target ACOS the customer actually gave you.** "Shared Rules" falls back to the
store's own ACOS for the period when none is supplied, and that is circular here: roughly half the
catalog sits below its own average by construction, so Star stops meaning "performing well". A
real run awarded Star to an ASIN at **59.9% ACOS** purely because the store averaged 63.2%. **With no
customer target, award no Star** — classify the top 80% as 腰部 Core, and say in the output that Star was
not assigned because no target ACOS was given, and what to supply to get it.

#### Axis B — Lifecycle stage

Product-intrinsic: driven by **total business performance** (`TotalSalesAmount`, `Sessions`)
over the 12-week series from Step 2f, plus SP advertising age and current stock cover —
**not** by ad-attributed orders, and **not** by spend rank. Using ad orders here would be a
category error: ad orders move when *you* change bids and budgets, so a trend built on them
measures your campaign management, not the product's life.

Unlike Axis A, this axis does **not** move when the reporting period moves.

Apply in this order, first match wins.

| Stage | Default rule |
|---|---|
| 新品 New | earliest `asinOpenDate` within the last **90 days** (Step 2c) **and** no sales in the weeks before it |
| 数据不足 Insufficient data | fewer than **6** of the 12 weeks show any activity (`TotalSalesAmount > 0` or `Sessions > 0`) |
| 衰退 Declining | **either** gate pair below hits: the **drift** pair (slope <= **-0.10** **and** drawdown >= **0.25**) **or** the **cliff** test (drawdown >= **0.50**) |
| 成长 Growth | normalized slope >= **+0.10** |
| 成熟 Mature | everything else — enough history, neither clearly rising nor clearly falling |

**Before any of the above, check stock cover.** Step 2d's **d1** pull supplies it for the **whole analysis set**, not only for flagged rows, and **at the grain being classified** — `asinDayAvailability30` under `granularity=asin`/`variant`, `parentAsinDayAvailability30` under `granularity=parentAsin`. When stock cover is **<= 7 days** (or `0`) and the series fell in its last weeks, the collapse is a **stockout, not a lifecycle event**: keep the stage the pre-collapse weeks support, and attach an independent **`stockout`** flag with the days figure. Do not relabel the product Declining for running out of stock - restocking reverses it, and a target-ACOS cut would be the wrong response. A missing availability field means *unknown*, not zero (Vendor profiles and profiles without SP-API authorization omit the whole group) - say the check could not be run.

**Computing the two gates**, on the weekly `TotalSalesAmount` series from Step 2f:

1. **MA3 smoothing** — trailing 3-week mean, keeping only complete windows, so a 12-week series
   yields 10 smoothed points. A week that returns no row is a **zero-activity week, not a missing
   one** — carry it as `0` rather than closing the gap, which would silently compress the
   timeline. The one exception is weeks before the ASIN's `asinOpenDate`: drop those entirely.
2. **Normalized slope** = ordinary-least-squares slope of the smoothed series against week index,
   divided by `max(|mean of the smoothed series|, a small epsilon)`. The normalization is what
   makes one -0.10 cutoff meaningful for a 200/week ASIN and a 200,000/week one alike; an
   un-normalized slope would classify almost entirely by product size.
3. **Peak drawdown** = `max(0, (peak - latest) / peak)`, where `peak` is the highest smoothed point
   and `latest` the final one. Report `0` when `peak <= 0`; never divide by a zero peak.
4. **Two ways in, and they catch different shapes.**
   - **Drift** (slope <= `decliningSlopeMax` **and** drawdown >= `decliningDrawdownMin`): a
     steady slide. Requiring both is deliberate — a product oscillating around a flat mean can
     produce a mildly negative slope without ever having fallen away from its own healthy
     level, and flagging that as decline is how a rule like this loses an operator's trust.
   - **Cliff** (drawdown >= `cliffDrawdownMin`, default **0.50**, on its own): a collapse in the last
     weeks. **The drift pair cannot see this.** A least-squares slope measures the whole line's
     tilt, so an end-of-series collapse is diluted by the flat weeks before it: a real case came
     back with a drawdown of **0.70** and a slope of only **-0.079**, and another with a drawdown
     of **1.00** (latest week at zero) and a *positive* slope. Both would read Mature on the drift
     pair alone, and a sudden collapse is the one an operator most needs to see.
   Say which path fired — "drift" and "cliff" are different problems with different fixes, and a
   cliff is far more often a stockout, a suppressed listing or a Buy Box loss than a life stage.

**⚠️ Twelve weeks is one quarter, so a seasonal product reads as declining right after its peak.**
This is the biggest failure mode of this axis and you must handle it, not report through it. Run
the **year-over-year check** from Step 2f: pull the same 12 calendar weeks one year earlier and
**run the identical stage computation on that window, with the same thresholds**. "Seasonal" means
that window also comes out **衰退 Declining** — by the same path, drift or cliff. Anything looser is not
reproducible: two agents given "a comparable fall" will disagree, and the lifecycle label would
stop being a property of the product. When it does come out Declining a year ago too, report the
stage as **成熟 Mature (seasonal downswing)** and show both windows' slope and drawdown as the evidence. When the history isn't there
(the ASIN is younger than ~15 months, or the lookback doesn't reach), say so and mark the stage
**unconfirmed against seasonality** — don't present it as settled.

**⚠️ A promotion week inflates the peak, and therefore the drawdown.** Prime Day, a large coupon
or a Deal week can become the series `peak`, after which every ordinary week looks like a 30-40%
drawdown and the second gate opens for free. `get_ads_perf` has no "this was a promotion" flag, so
check the window for a promotion per "Shared Rules" before reporting any 衰退 Declining stage whose
drawdown rests on one exceptional week — and name that week in the evidence.

**What this axis deliberately does not do.** A fuller lifecycle model would also exclude
out-of-stock weeks from both the trend and the peak, separate growth from mature by a weekly sales
target rather than by slope, and weight in review rating and return rate. None of those are
available here: `get_entity_metadata` returns only the **current** inventory status with no
history, and this product has no weekly-sales-target or review-rating field at all. So this axis is
the subset the available data actually supports, and saying which parts are missing is part of the
output. If the customer keeps weekly sales targets of their own, tell them that supplying those
converts the growth/mature split from a slope test into a target-attainment test — and use theirs
when they give them.


#### The flagged set — one definition, used everywhere

`scope=underperformingOnly`, Step 2d's follow-up pull, Step 5's diagnostic cards and Step 6's
**Optimize** verdict all operate on the **same** set. Define it once, here, and cite it from each:

> An entity is **flagged** when any of these holds:
> 1. its lifecycle stage is **衰退 Declining** (by either path), or it carries the **`stockout`** flag; **or**
> 2. it has **zero orders** this period with `Spend >= T` (`T` per "Shared Rules"); **or**
> 3. `Spend >= T` **and** `ACOS` > the target ACOS, where the target is one the **customer supplied**
>    (with no customer target this clause does not apply - see Axis A - and the flagged set is
>    clauses 1 and 2 only); **or**
> 4. it has a **recent deterioration signal** from the reporting-period comparison below.

Everything else is not flagged. **无广告投放 No ad spend** rows can be flagged by clause 1 or
clause 4: with no spend there is nothing to waste, so clauses 2 and 3 cannot fire. Say which
clause fired for each entity - "declining", "recent business-sales deterioration", "recent
ad-conversion deterioration", "spent without converting" and "converting too expensively"
lead to different actions.

#### Recent deterioration — independent of lifecycle stage

Lifecycle is a 12-week product-stage label. It must not suppress a sharp change between the
reporting period and its immediately preceding equal-length period. After joining Step 2a and
2b by ASIN (or by parent after the required child aggregation), compute two independent flags:

- **Recent business-sales deterioration**: prior `OrderCount >= recentSalesBaselineOrders`
  (default `5`) **and** prior `TotalSalesAmount >= recentSalesBaselineAmount` (default: one
  `T`, per "Shared Rules" — so it scales with the store's price level and currency), and
  current `TotalSalesAmount <= prior × (1 - recentSalesDeclineMin)`, default
  `recentSalesDeclineMin = 0.20`.
  **Echo the resolved number, not the symbol.** `recentSalesBaselineAmount` defaults to a
  value computed at run time, so report the store-currency amount you actually used (e.g.
  `42.5`) together with `recentSalesBaselineAmountSource` = `derivedFromT` or `customer`.
  Printing `T` or `null` leaves the reader unable to reproduce the classification.
  **The two baselines are the point**: without them `$1.00 → $0.70` is a 30% decline and would
  pull a trivial product into the diagnostic set. Below either baseline, report the row as
  **too small to judge**, not as deterioration, and say which baseline it missed.
- **Recent ad-conversion deterioration**: prior `Conversions >= recentAdOrderBaselineMin`
  (default `3`) and current `Conversions <= prior × (1 - recentAdOrderDeclineMin)`, default
  `recentAdOrderDeclineMin = 0.30`.

Use raw period totals, not ACOS or smoothed lifecycle points. A zero/missing prior denominator is
**not comparable**, not a 100% decline. Either flag adds clause 4 to `flaggedBy` and generates a
diagnostic card even when the lifecycle stage remains **成熟 Mature**. Present both facts together,
for example: "Lifecycle: Mature; recent status: business sales down 22% and ad conversions down
35% versus the preceding equal-length period." Do not relabel the lifecycle stage.

Apply the existing promotion discipline before interpreting the signal. If the prior/current
comparison crosses a confirmed promotion, retain the measured flag but label it
`possiblyPostPromotion` and do not present the decline as an organic trend.

#### Reporting both axes together

Present the pair, never a single label. The combinations that are findings in their own right:

| Combination | Why it matters |
|---|---|
| 明星 Star x 衰退 Declining | a main earner is falling — the highest-priority finding here, and exactly the case a single-label scheme hides |
| 明星 Star / 腰部 Core x 成长 Growth | working; a candidate for more budget (take the reallocation angle to `sparkx-ads-structure-analysis`) |
| 长尾 Long-tail x 成长 Growth | small but rising — a winner before it is obvious |
| 长尾 Long-tail x 衰退 Declining | the ordinary cut candidate |
| any x 新品 New | low volume is expected — don't read it as weakness, and don't cut on this period's numbers alone |
| any x 数据不足 Insufficient data | report the ranking, then say the stage could not be determined, and why |

**No fixed money cutoffs**: Axis A uses spend shares and the target ACOS, Axis B uses a normalized
slope and a ratio; zero-order checks use `T` (see "Shared Rules"). The rules hold in any currency.

### Step 4 · Variant Comparison (if `granularity=variant`)

For the anchored parent's child ASINs (from Step 2a/b, filtered to that `parent_asin_`): compare each sibling's spend share within the parent, ACOS, and `BuyBoxPercentage`/`UnavailabilityRate` — variants of the same product often compete for the same demand, so a spend/efficiency imbalance here is a genuine "which variant should get the budget" finding, distinct from the catalog-wide portfolio tiers and lifecycle stages in Step 3.

### Step 5 · Diagnostic Card (for every entity in Step 3's flagged set)

For each flagged entity (ASIN or parent ASIN — see the parent-mode adjustments to 2c/2d/2e above; don't drop back to child-only fields under `granularity=parentAsin`), assemble:
- **Is it even still being advertised?** (from 2e's `productAd` resolution and the `campaign` lookup it needs) — **check this first.** `campaignState` and `productAdState` of the entities carrying this ASIN: if every campaign holding it is `paused`/`archived`, or its product ads are, the spend and sales going to zero is not a life stage, a stockout or a Buy Box problem — **the ads were turned off**, and everything below is beside the point. In a real run this was the whole explanation for the only genuinely Declining ASIN: its single campaign was paused. Report the campaign names and states, and say whether *all* or only *some* of the carrying entities are off — partial pausing is a reallocation, full pausing is a decision someone already made.
- **Inventory/eligibility status** (Step 2d): out-of-stock (`asinInventoryStatus`/`parentAsinInventoryStatus`), lost ad-type eligibility, or deleted (the d3 probe above, **not** a `select`) — these can fully explain a sales collapse on their own and should be surfaced before the advertising-side explanations.
- **Buy Box / returns signal** (Step 2a): a `BuyBoxPercentage` drop or elevated `CustomerReturns` alongside declining sales is a strong non-advertising explanation — flag it as such rather than assuming the cause is bid/budget-related.
- **Correlated operation-log changes** (Step 2e): bid/budget/status changes on the campaigns/adGroups containing this ASIN's product ads in the same window — **not** changes on the ASIN itself (per Step 2e, `get_operation_log` can't be scoped to a single `productAd`/ASIN, only to `campaign`/`adGroup`). Label this explicitly in the diagnostic card (e.g. "非 ASIN 专属——该 campaign/adGroup 下的操作记录") so it isn't read as ASIN-specific evidence. **Correlation, not causation** — same discipline as the report skills: state what changed and when, don't claim it caused the decline unless the timing and magnitude clearly line up, and weigh that correlation more cautiously here given the change wasn't even necessarily on this specific product ad.

If none of the above turns up anything, say so plainly ("no inventory/eligibility/buy-box issue found, no correlated operation-log change found") rather than forcing a narrative onto an unexplained decline.

### Step 6 · Recommendations (Keep / Optimize / Cut)

Derive one verdict per flagged ASIN (and optionally per healthy ASIN if the user wants a full-catalog verdict, not just the problems). **The verdict reads both axes, not one** — the portfolio tier says how much is at stake, the lifecycle stage says which way the product is going, and the same stage deserves a different answer at each tier:
- **保 (Keep)**: Star or Core at the Growth or Mature stage **with no recent-deterioration flag** — no action needed, or note it as a candidate for the *other* skill (`sparkx-ads-structure-analysis`) if there's a structural budget-reallocation angle. A **New** product at any tier also defaults to Keep unless a non-lifecycle diagnostic flag such as stockout or recent deterioration needs investigation; do not turn that flag into a Cut verdict on this window alone.
- **优 (Optimize)**: every entity in **Step 3's flagged set** where Step 5 found a fixable driver — no other reading of "underperforming" applies here. A **`stockout`** flag means the fixable driver is restocking, and the ad-side answer is to hold, not to cut. **Star x Declining goes first in the list** — it is the largest amount of money moving the wrong way, and it is the case the old single-label scheme could not express at all (e.g. restock, buy-box recovery, a managed-group setting) — action + evidence. Bid / budget advice follows "Shared Rules" (group levers for managed campaigns, no numbers). For traffic-side problems, suggest running `sparkx-search-term-diagnosis` (if installed) scoped to this product.
- **撤 (Cut)**: zero orders with spend >= `T` in **both** this and the prior period, and no fixable driver found; or **Long-tail x Declining** with negligible volume. **Never cut on a Declining stage that the year-over-year check could not confirm against seasonality**, and never cut a **New** product on this window alone — say what is missing instead. Action + evidence.

**Every recommendation must have**: action + target ASIN + evidence (data), same requirement as the other skills in this family.

## Multi-Store and Currency

When `profileIds` spans multiple stores:
- All monetary metrics from `get_ads_perf` auto-aggregate to **USD**, **except** `asin.asinPrice_` (if ever used) and ASIN-entity pricing in `get_entity_metadata`, which stay local currency per-row — label dollar amounts "(USD)" explicitly elsewhere.
- Add `profile.profileId_`/`profile.profileName_` to Step 2a/2b's `select` when `profileIds` spans multiple stores, so a ranking/lifecycle-tier call can attribute each ASIN to its store — the same ASIN can exist under multiple stores with different performance. **This attribution must actually reach the output**: add a 店铺/Store column to Step 3's ranking table (and the markdown template's table below) whenever `profileIds` has more than one entry, and add `profileId`/`profileName` to `structured_report`'s `ranking` entries in the same case — don't pull the per-store `select` fields in Step 2a/2b only to drop them before presenting.

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
# 商品诊断 · {profile_name}
**维度**：{asin / parentAsin / variant}　**范围**：{topN / all / 指定ASIN / 仅问题商品}
**周期**：{dateStart} ~ {dateEnd}
{If data may be incomplete due to T+2 delay, or a section is based on a partial sample, note it here}
{若 profileIds 涉及多个店铺，标题的 {profile_name} 不要写死单个店铺名——改成店铺列表或 "{N}个店铺"，具体归因见下方排名表的店铺列}

## 一、商品排名表

{列名用 "ASIN" 还是 "Parent ASIN" 取决于 granularity：asin/variant 用 "ASIN"，parentAsin 用 "Parent ASIN"——不要不管 granularity 都固定写 "ASIN"}
{仅当 profileIds 涉及多个店铺时才加"店铺"列——单店铺场景不要加这一列造成冗余}

| ASIN / Parent ASIN | 店铺（仅多店铺时） | 花费 | 广告销售额 | ACOS | 总销售额 | TACOS | 订单数 / 转化数 | 投放分层 | 生命阶段 | 近期状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | 明星/腰部/长尾/无广告投放 | 新品/成长/成熟/衰退/数据不足{+断货标记} | 稳定/销售额下降N%/广告转化下降N% |

## 二、投放分层与生命阶段

{在这里写明两个轴各自实际使用的阈值，并说明这是默认规则、客户可以自定义}
{生命阶段窗口：完整 12 周 {lifecycle_start} ~ {lifecycle_end}，与上方报告周期相互独立}

**投放分层**（本报告周期内占本账户花费的比重）
- 明星：{N} 个，贡献 {pct} 花费 / {pct} 销售额
- 腰部：{N} 个
- 长尾：{N} 个

**生命阶段**（SP 投放时长 + 12 周总销售额趋势；注：`asinOpenDate` 是 SP 开投日期，不是商品上架日期）
- 新品：{N} 个（近 90 天内开始投 SP）
  {另有 {N} 个属于「新开投的老品」——SP 开投日期之前已有销售，按趋势判定而非判为新品}
- 成长：{N} 个
- 成熟：{N} 个{，其中 N 个已确认为季节性回落}
- 衰退：{N} 个 — 需要关注{；其中 N 个未能通过同比确认季节性}
- 数据不足：{N} 个

**交叉**（只写构成结论的组合）
- 明星 × 衰退：{N} 个 — {逐个列出；这是优先处理清单}
- 长尾 × 成长：{N} 个

## 三、变体对比（若 granularity=variant）

| 变体 ASIN | 花费占比 | ACOS | Buy Box % |
|---|---|---|---|
| ... | ... | ... | ... |

## 四、单品诊断卡（衰退 / 近期恶化 / 问题商品）

### {ASIN}
- 分类：{投放分层}；生命阶段 {stage}；近期状态 {稳定/销售额下降N%/广告转化下降N%}{；可能受大促后回落影响}
- 库存/资格状态：{...}
- Buy Box / 退货信号：{...}
- 关联操作记录（非 ASIN 专属，campaign/adGroup 层面）：{...，标注为关联而非确定因果}

## 五、优化建议

1. **{保/优/撤}** {ASIN}
   - 依据：{data}
2. ...

---
_生成时间：{timestamp} · 数据源：SparkX AI MCP · Skill: sparkx-product-diagnosis v{version}_
```

### structured_report mode

```json
{
  "dimension": "asin",
  "period": {"start": "...", "end": "..."},
  "dataFreshnessWarning": null,
  "ranking": [{"entityId": "...", "entityType": "asin|parentAsin", "profileId": null, "profileName": null, "spend": ..., "sales": ..., "acos": null, "totalSalesAmount": ..., "tacos": null, "orderCount": ..., "conversions": ..., "portfolioTier": "star|core|longTail|noAdSpend", "lifecycleStage": "new|growth|mature|declining|insufficientData", "lifecycleEvidence": {"normalizedSlope": null, "peakDrawdown": null, "decliningPath": "drift|cliff|null", "validWeeks": null, "spOpenDateEarliest": null, "spOpenDateIsReproducible": true, "newlyAdvertisedNotNew": false, "stockout": false, "dayAvailability30": null, "yoyChecked": false, "seasonalDownswing": false}, "recentStatus": {"businessSalesDecline": false, "businessSalesChangeRate": null, "adConversionDecline": false, "adConversionChangeRate": null, "comparable": true, "possiblyPostPromotion": false}, "flagged": false, "flaggedBy": []}],
  "portfolioTierSummary": {"star": {"count": ..., "spendShare": ...}, "core": {...}, "longTail": {...}, "noAdSpend": {"count": ..., "spendShare": 0, "totalSalesAmount": ...}},
  "lifecycleStageSummary": {"new": {"count": ...}, "growth": {...}, "mature": {...}, "declining": {...}, "insufficientData": {...}},
  "lifecycleWindow": {"start": "...", "end": "...", "weeks": 12},
  "classificationRules": {"portfolioTier": {"starSpendPrefix": 0.5, "coreSpendPrefix": 0.8, "starAcosRule": "<= target ACOS", "targetAcosSource": "customer|none"}, "lifecycleStage": {"newSpAgeDays": 90, "minValidWeeks": 6, "decliningSlopeMax": -0.10, "decliningDrawdownMin": 0.25, "cliffDrawdownMin": 0.50, "growthSlopeMin": 0.10, "stockoutDaysMax": 7}, "recentDeterioration": {"recentSalesDeclineMin": 0.20, "recentSalesBaselineOrders": 5, "recentSalesBaselineAmount": 42.5, "recentSalesBaselineAmountSource": "derivedFromT|customer", "recentAdOrderDeclineMin": 0.30, "recentAdOrderBaselineMin": 3}},
  "variantComparison": null,
  "diagnosticCards": [{"entityId": "...", "entityType": "asin|parentAsin", "inventoryStatus": "...", "eligibilityIssue": null, "buyBoxSignal": null, "correlatedChanges": [...]}],
  "recommendations": [{"verdict": "keep|optimize|cut", "entityId": "...", "entityType": "asin|parentAsin", "action": "...", "evidence": "..."}]
}
```
`entityId`/`entityType` replace a bare `"asin"` key precisely so each entry is self-describing — a consumer reading one `ranking`/`diagnosticCards`/`recommendations` entry in isolation (not alongside the top-level `dimension`) can still tell whether `entityId` is a child or parent ASIN without cross-referencing back to the top of the payload. `profileId`/`profileName` are `null` when `profileIds` is a single store (nothing to disambiguate); populate them per "Multi-Store and Currency" whenever `profileIds` spans more than one — don't pull the per-store `select` fields upstream and then drop them here.

## Data Boundaries

- **No SKU-level margin/profitability** — this needs the customer's own cost data, out of scope for this skill (a candidate for the "combine with your own business data" pattern used elsewhere in this product, not something this skill computes on its own).
- **Both classifications are default rules, not certified business definitions** — always show the underlying numbers (spend share and ACOS for the portfolio tier; normalized slope, peak drawdown, which Declining path fired, and SP advertising age for the lifecycle stage) next to the labels, state the cutoffs you used, and say plainly that the customer can define their own. Neither label is a verdict beyond dispute.
- **The lifecycle stage has no seasonal or promotional adjustment beyond the year-over-year check** — no series decomposition and no event calendar. A Declining stage the YoY check could not confirm is a flag to investigate, not a conclusion.
- **Out-of-stock weeks are not excluded from the trend or the peak** — there is no inventory *history* to exclude on, only the current `asinDayAvailability30` / `asinInventoryStatus`. That is enough to tell a stockout apart from a life stage *today* (Axis B's stockout check), but not enough to rebuild what the series would have looked like in stock. A `stockout`-flagged series understates the product.
- **`asinOpenDate` is the SP go-live date (`sp_open_date`), not the listing date** — the New stage therefore means *newly advertised on SP*, and the parent-level column is non-deterministic. See Step 2c.
- **No weekly sales target and no review rating exist in this product's data**, so the growth/mature split rests on the trend slope alone. If a customer works to weekly sales targets, their own numbers beat this split and should replace it.
- **`get_entity_metadata` has no historical-snapshot capability** — inventory/eligibility status in Step 5's diagnostic card reflects the *current* state, not necessarily the state at the time of the decline. Say so if the timing matters and can't be confirmed.
- **`variant` granularity requires an anchor** (a named parent or child ASIN) — there is no "compare all variants across the whole catalog at once" mode; see "Granularity" above.
- **`TotalSalesAmount`/`TACOS` are unified Seller/Vendor metrics** — Vendor rows use the shipped basis, so these fields can be used directly across mixed Seller and Vendor profiles. Use `OrderedRevenue`/`OrderedTACOS` or `ShippedRevenue`/`ShippedTACOS` only when the user explicitly needs that Vendor-specific breakdown.

## Example Call

**User input**:
> 看下 Demo US 最近 30 天有哪些 ASIN 表现不好

**Skill flow**:
1. Resolve the profile: `get_user_authorized_context` → find Demo US's `profileId`
2. `scope = underperformingOnly`, window = trailing 30 days ending yesterday
3. Run Steps 2-6
4. Output the markdown report — in Chinese, since the user asked in Chinese

## Error Handling

Follows the shared error envelope used by both underlying tools (`isError`/`errorType`, see [`references/platform-notes.md`](references/platform-notes.md)).

| Situation | Handling |
|---|---|
| `profileIds` is empty | Follow "Resolving `profileIds`" above — ask only when those rules require it |
| Any call returns `isError: true` | Handle per `errorType` — `invalid_params` usually means a construction bug in this skill's own call; `rate_limited` → wait `retryAfterSeconds` |
| `effectiveProfileIds` doesn't match requested `profileIds` | Explain the scope mismatch before concluding "no data" |
| An ASIN has `Sales = 0` | `ACOS` is undefined — report "no ad-attributed sales this period," don't compute it against a zero denominator |
| An ASIN has `TotalSalesAmount = 0` | `TACOS` is undefined — report "no total sales this period," independently of whether `Sales` is also zero |
| `get_operation_log` returns `truncated: true` | Split into sub-windows per its "Getting a Complete Count" procedure |
| A degraded/sampled section | Disclose what was covered; don't fail the whole diagnosis over one segment's pagination trouble |

## Not Covered by This Skill

- Account-wide structural share analysis → `sparkx-ads-structure-analysis`
- Periodic WoW/MoM cadence recaps → `sparkx-weekly-ads-report` / `sparkx-monthly-ads-report`
- Search-term/keyword-level diagnosis → `sparkx-search-term-diagnosis` (if installed)
- SKU-level margin/profitability (needs the customer's own cost data)
