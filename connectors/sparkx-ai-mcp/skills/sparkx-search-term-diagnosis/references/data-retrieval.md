# Data retrieval

One store, one period. Everything below was run against two production stores (2026-10,
read-only): a manual SP store with about 2,300 ordering search terms, and an AI-managed SP +
SB store. Call counts are from those runs.

## Three behaviours that decide how you query

1. **A metric used in `filters` must also be in `metrics`.** Filtering on `Conversions`
   without requesting it fails with `unknown field 'Conversions'`.
2. **Metric filters apply after grouping.** They filter the aggregated row of whatever you
   `select`. With `select: ["query_"]`, `{"Conversions": {"=": 0}}` means "search terms with
   no orders in total" - what you want. With `select: ["matchType_"]` it means "match types
   with no orders at all" and returns nothing. Choose `select` for the level you want to
   filter at.
3. **Normalise response keys before using them.** In live calls (2026-10) and in the server's
   column cleaner, rows come back without the entity prefix and the `_` suffix: `query_` ->
   `query`, `campaign.campaignId_` -> `campaignId`, `target.targetText_` -> `targetText`
   (plus `...Text` companions). Some base-skill examples show the requested form instead.
   Don't rely on either: map every key with "drop everything up to the last `.`, then drop a
   trailing `_`" once, right after each call, and use only the normalised names afterwards
   (the reference script expects them).
   `matchType` values seen: `LOOSE-MATCH`, `CLOSE-MATCH`, `SUBSTITUTES`, `COMPLEMENTS`
   (auto), `broad`, `phrase`, `exact` (keywords), `ASIN`, `CATEGORY` (product targeting -
   upper case).

Do not pass `queryType` on `factEntity: searchTerm`: omitting it is the only way to include
auto-targeting search terms.

## Narrowing the scope

Whole store by default. When the user names:

- **campaigns**: resolve them with `get_entity_metadata(entity='campaign')` (internal
  `campaignId` and `amazonCampaignId`). Add `{"campaign.campaignId_": {"in": [<Amazon ids>]}}`
  to every `get_ads_perf` call, including call 8, and `{"campaignId": {"in": [<internal
  ids>]}}` to call 7;
- **a product (ASIN or parent ASIN)**: there is no product dimension on search terms. Follow
  the base skill's three steps - `get_entity_metadata(entity='productAd')` filtered to the
  ASINs (expand a parent first via `entity='asin'`, `filters: {"parentAsin": ...}`) gives
  internal `adGroupId`s; `entity='adGroup'` maps them to `amazonAdGroupId`. Then filter
  **every** `get_ads_perf` call - the search-term calls and call 8 - on
  `{"p.adGroupId_": {"in": [<Amazon ad group ids>]}}`, and call 7 on
  `{"adGroupId": {"in": [<internal ad group ids>]}}`. Skipping the mapping step returns zero
  rows with no error; leaving call 7 or 8 unfiltered mixes the whole store's exact keywords
  into V3a, V3c, V4 and V5. Report the result as **search terms in the ad
  groups that contain this product**, not traffic attributed to the ASIN - an ad group usually
  holds several products.

Scoped totals (call 1) use the same filter, so AOV and shares are within the scope. Every
business-analysis call below takes the scope filter, not only the search-term ones. The sole
exception is call 1a: an additional unfiltered whole-store total used only when the customer
did not provide a target ACOS. Do not use call 1a for scoped shares or scoped AOV.

## Call plan

All `get_ads_perf` calls: `factEntity: "searchTerm"` unless noted, the same `dateStart` /
`dateEnd`, `pageSize: 500`, and **loop `page` while `meta.hasNextPage`**.

| # | Purpose | `select` | `metrics` | `filters` |
|---|---|---|---|---|
| 1 | Totals (and the average order value) | `["campaign.campaignType_"]` - one row per ad type; **sum the rows** into one total | `Spend, Sales, Clicks, Conversions` | - |
| 1a | Whole-store target-ACOS fallback, only when the customer supplied no target and call 1 is scoped | same as call 1 | same | **no product/campaign scope filter**; still the same profile and period |
| 2 | Totals by source | `["matchType_"]` | same | - |
| 3 | Search terms with orders | `["query_"]` | same | `{"Conversions": {">": 0}}` |
| 4 | Zero-order terms above the threshold `T` | `["query_"]` | same | `{"Conversions": {"=": 0}, "Spend": {">=": T}}` |
| 5 | Source match types of ordering terms (harvest source, small-term split) | `["query_", "matchType_"]` | same | `{"Conversions": {">": 0}}` |
| 6 | Zero-order search-term x match-type rows at or above `T` (small-spend source split) | `["query_", "matchType_"]` | same | `{"Conversions": {"=": 0}, "Spend": {">=": T}}` |

`T` = one order's target spend = (`Sales` / `Conversions` from scoped call 1) x target ACOS
(as a fraction - see classification.md -> Units). When the user supplied no target, the target
ACOS is `Spend / Sales` from call 1a (or call 1 itself when the run is already whole-store).
Calls 1, 1a when needed, 3 and 9 run in Step 1; calls 4, 6 and 8's V3a cut-off need `T`, so
they run after the target ACOS is confirmed.

Order calls 3 and 4 by `Spend` descending so a partial run still holds the important rows,
but classify only on complete page sets.

Metadata (`get_entity_metadata`, page through `hasNextPage`):

| # | Purpose | Call |
|---|---|---|
| 7 | Exact keywords in use (harvest de-dup, V3a / V3c, V5) | `entity: "keyword"`, `filters: {"matchType": {"in": ["exact"]}, "keywordState": {"in": ["enabled"]}}`, `select: ["keywordId", "amazonKeywordId", "keywordText", "matchType", "campaignId", "adGroupId", "campaignType", "profileId"]` - names come from call 11 |
| 8 | Exact keyword performance (V3a, V5) | `get_ads_perf`, `factEntity: "target"`, `queryType: "keyword"`, `select: ["target.targetId_", "target.targetText_", "target.targetMatchType_", "target.targetState_", "target.campaignId_"]`, `metrics: ["Spend", "Sales", "Clicks", "Conversions"]`, `filters: {"target.targetMatchType_": "exact"}`. `targetId` is the Amazon keyword id - join to call 7 on `amazonKeywordId` to get the internal `keywordId` a pause needs |
| 9 | Brand pre-fill | `entity: "asin"`, `select: ["asin", "asinBrand", "asinTitle"]` |

Managed-group labels, only for the terms that end up in the V3 / V4 lists:

| # | Purpose | Call |
|---|---|---|
| 10 | Where each listed term's spend came from | `get_ads_perf`, `select: ["query_", "campaign.campaignId_", "campaign.campaignName_", "campaign.campaignType_", "adGroupId_"]`, `metrics: ["Spend", "Clicks", "Conversions"]`, `filters: {"query_": {"in": [...]}}` in batches of about 100 terms. If the `in` filter on `query_` is refused, pull the same `select` for the whole period instead (one AI-managed test store: 10 pages) |
| 11 | Campaign / ad group -> internal ids, names and managed group | `get_entity_metadata(entity='campaign')`, `select: ["campaignId", "amazonCampaignId", "campaignName", "campaignType", "profileId", "aiGroupId"]`; `get_entity_metadata(entity='adGroup')`, `select: ["adGroupId", "amazonAdGroupId", "adGroupName", "campaignId"]`. Search-term rows carry **Amazon** ids; join on the `amazon*Id` fields, comparing as strings (one side may be numeric). Whether an ad group can take a negative product target is checked by `sparkx-edit-ads` at write time - metadata has no targeting-type field to pre-check it |
| 12 | Group switches | `get_entity_metadata(entity='aiGroup')`: `aiActionSettings.targetOptimization.negativeTargetStatus` (`1` = automatic negative targeting on) and `targetHarvestStatus` (`1` or `2` = harvesting on) |

Candidate safeguards and current-state coverage, run only for the V3/V5 candidate set rather
than for every term in the account:

| # | Purpose | Call |
|---|---|---|
| 13 | Immediately preceding equal-length exact-keyword performance (V3a history guard) | Same shape and scope as call 8, with `dateStart`/`dateEnd` shifted to the immediately preceding non-overlapping period. Join by Amazon keyword id, not text. A prior `Conversions > 0` changes the action from pause to investigate |
| 14 | Current keyword-negative coverage (V3b keyword entries) | `get_entity_metadata(entity='negativeKeyword')`, enabled rows only, selecting `keywordText`, `matchType`, `businessType`, `campaignId`, `adGroupId`, `campaignType`, `profileId`. Normalize text with Unicode case-folding, trim and collapse whitespace. Only an enabled `matchType=negativeExact` row proves the proposed exact-negative action is already covered; `negativePhrase` is different coverage. A campaign-level row covers every source ad group in that campaign; an ad-group row covers only that ad group |
| 15 | Current ASIN-negative coverage (V3b ASIN entries) | `get_entity_metadata(entity='negativeTarget')`, enabled rows only, selecting `negativeTargetText`, `negativeTargetType`, `campaignId`, `adGroupId`, `campaignType`, `profileId`. Negative targets are ad-group scoped; match the normalized ASIN and source ad group. Do not infer coverage from managed-group switches or old operation logs |
| 16 | Keyword age and relevant recent changes (V3a/V5) | First query `get_operation_log` for the candidate keyword/target additions and bid/status changes, using the correct Amazon ids and a single entity per call so real pagination is available. If no creation event is retained, pull daily exact-keyword performance over the available lookback and use its first observed row as a **lower bound**, not an exact creation date. Campaign start date is context only and must never be reported as keyword age. For historically proven V3a rows, also inspect campaign/ad-group/keyword changes spanning the prior and current windows |

For each V3b candidate, build the set of source destinations from call 10 and evaluate coverage
destination by destination. Report one of three states:

- **already handled**: every source destination is covered now; remove it from the actionable list;
- **partially covered**: show covered and uncovered destinations separately; only uncovered ones
  are actionable;
- **not covered**: no current matching negative covers its source destinations.

Current coverage says what is protected now. It does not prove when the negative began taking
effect, and historical spend must not be described as leakage after that date without dated evidence.

A term is labelled "托管组已开自动否定" only when **every** campaign it spent in belongs to a
group with that switch on; the same rule for harvesting.

## The zero-order small terms, and where small unconverted spend comes from

Two different measures - keep them apart, and name them differently to the customer:

- **Zero-order small terms (零单小词)** - search terms with no orders in total and spend below
  `T`. Amount = call 1 spend - call 3 spend - call 4 spend. This is the V1 line. Never
  listed.
- **Small unconverted spend by source (未出单的小额流量)** - measured one level finer, at
  search term x match type: the rows with no orders and spend below `T`. Per match type it is
  exactly (call 2) - (call 5) - (call 6); calls 5 and 6 work at that same level, so nothing
  is double-counted. It includes the zero-order slices of terms that did convert under another
  match type, so it is **not** "the source of the zero-order small terms": present it as its
  own line - "没出单的小额流量（按搜索词 × 匹配方式计）里，X% 来自 …" - with shares.

Use the source line to say **where to look**, not to prescribe a cut: harvest the good terms
from that match type, check its negatives, or split it into its own campaign to watch it. Do
not suggest pausing a match type on this number alone - it mixes in traffic from terms that
convert.

- **By campaign**: the same row-level measure needs search-term x campaign detail. Only give
  it when that detail was pulled anyway (e.g. as the fallback of call 10).

## Sanity checks

- Search-term spend (call 1) should be close to the spend of the same scope one level up:
  whole store -> `factEntity: campaign` with `{"campaign.campaignType_": {"in":
  ["sponsoredProducts", "sponsoredBrands"]}}` (search terms exist for SP and SB only, so SD
  must be left out); product scope -> `factEntity: adGroup` with the same `p.adGroupId_`
  filter. The test stores were at 99.5% and 99.8%. A large gap means a scope mismatch - say
  so.
- Call 3 must reproduce the total orders and sales of call 1 exactly (all orders sit on
  ordering terms).
- Volumes seen: 2,332 ordering terms (5 pages), 218 zero-order terms above `T`, 2,909
  search-term x match-type rows with orders (6 pages), 810 and 3,891 enabled exact keywords
  (2 and 8 pages). The manual store's full diagnosis took about 15 calls.
