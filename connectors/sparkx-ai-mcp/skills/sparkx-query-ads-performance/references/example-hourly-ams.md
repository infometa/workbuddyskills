# Hourly / AMS Queries (intraday and keyword × placement)

Hour-level data comes from Amazon Marketing Stream (AMS). Two entry points, both capped at a **7-day span** (not 90).

## 1. Campaign metrics by hour

```json
{
  "profileIds": [4404871489220462],
  "factEntity": "campaign",
  "timeGranularity": "hourly",
  "dateStart": "2026-08-17",
  "dateEnd": "2026-08-23",
  "select": ["campaign.campaignId_", "campaign.campaignName_", "date", "hour"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "Conversions"],
  "orderBy": [{"field": "Spend", "direction": "DESC"}],
  "pageSize": 500,
  "userContext": "Which hours of day drive spend and conversions last week"
}
```

Notes:
- `timeGranularity: "hourly"` is valid **only** with `factEntity: "campaign"`. On any other entity the call fails with `Parameter 'timeGranularity=hourly' is only supported for factEntity=campaign`.
- Span must be ≤ 7 days. `2026-08-17`→`2026-08-23` is exactly 7 inclusive days.
- **No AI metrics by hour.** `AISpend`/`AISales` return `0` and `AIACOS`/`AIROAS` return `null` here too - placeholders, not real zeros. For AI attribution use a daily `factEntity: campaign` query.
- `hour` must be present in `select`; `timeGranularity: "hourly"` does not add it automatically. **This is the #1 cause of "I asked for hourly but only got a date field" reports** — if `hour` is missing from `select`, the response silently groups by day only. Always double-check `select` before concluding the API doesn't support hourly.
- **Timezone (confirmed by SparkX, 2026-08)**: AMS/hourly data is in the **profile's local IANA timezone** (the same `timezone` string returned by `get_user_authorized_context`, e.g. `America/Los_Angeles`) — not UTC. This covers the `date`/`hour` values in each row. DST-transition-day hour encoding (23-hour spring-forward day, repeated-hour fall-back day) is still not documented; treat results on the DST transition date itself as ambiguous until confirmed.
- **Latency (confirmed by SparkX, 2026-08)**: hourly AMS data is typically available roughly **~2 hours** after the hour ends — much faster than the daily pipeline's T+2. **These two numbers measure different things and neither contradicts the other: ~2 hours is when a row first appears; T+2 is the daily pipeline's own figure, and nothing here establishes it as the point where hourly attribution completes.** The ~2 hours is approximate, not a hard SLA, and the backfill/revision window for late-arriving conversions is still undocumented - so the supportable statement is "first data in about two hours, backfilled afterwards, final window unknown". Treat the most recent few hours as provisional - readable, but subject to upward revision - and re-pull before treating them as final.
- **`productAd.asin_`/`productAd.sku_` cannot be added to `select` on `factEntity: campaign` + `timeGranularity: hourly`** — confirmed by testing, fails with `business_error`: `查询执行失败: 无法连接CTE: [campaign_perf, productAd_meta, campaign_meta]`. Only this exact combination (hourly campaign query + `productAd.*` fields) was tested; whether the same join fails on a *daily* campaign query, or whether `asin.*` (the general product dimension, distinct from `productAd`) behaves differently, was not tested — don't extrapolate either way. What's confirmed either way: `factEntity: productAd` itself rejects `timeGranularity: hourly` outright (`Parameter 'timeGranularity=hourly' is only supported for factEntity=campaign`), so **there is no tested path to ASIN/SKU/product-ad identity at hourly granularity**. If the user needs hourly-by-product, say plainly this isn't supported today rather than trying filter workarounds.
- The 15-month earliest-lookback limit (see `platform-notes.md`'s Date Range Limits) is **confirmed to apply identically to hourly queries**, and the boundary is **inclusive** (`dateStart` exactly 15 months before today is allowed; the check is `dateStart` strictly earlier than the cutoff that fails). Verified 2026-08: a window with `dateStart` exactly at the 15-month-ago cutoff date succeeded with real data; the same window shifted one day earlier failed with `invalid_params`: `dateStart cannot be earlier than 15 months ago (<cutoff date>)`. A window 10 months back also succeeded. It is not a daily-only limit copy-pasted by mistake, and it is not an exclusive boundary — don't tell the user the cutoff date itself is unqueryable.

## 2. Keyword × placement (SP only)

```json
{
  "profileIds": [4404871489220462],
  "factEntity": "keywordPlacement",
  "dateStart": "2026-08-17",
  "dateEnd": "2026-08-23",
  "select": ["keywordText", "matchType", "placement", "campaignId", "adGroupId"],
  "metrics": ["Impressions", "Clicks", "Spend", "Sales", "ACOS"],
  "orderBy": [{"field": "Spend", "direction": "DESC"}],
  "pageSize": 500,
  "userContext": "Top of search vs product page performance by keyword"
}
```

A returned row looks like this — note the keys are **not** the names you sent:

```json
{
  "keywordText_": "wireless earbuds",
  "matchType_": "EXACT",
  "placement": "Top of Search on-Amazon",
  "campaignId_": 12345,
  "adGroupId_": 67890,
  "hour": 20,
  "date": "20260823",
  "Spend": 18.4,
  "ACOS": 22.13
}
```

Notes:
- **Do not pass `timeGranularity`** here — this entity is hourly by nature, and it has no daily rollup either.
- **Naming is asymmetric**: send the bare names (`keywordId`, `keywordText`, `matchType`, `placement`, `campaignId`, `adGroupId`), read `_`-suffixed keys back (`keywordText_`, `matchType_`, …, plus `placement`, `hour`, `date`, `profileId_`). Don't feed a response key back into a request — `keywordPlacement.keywordText_` happens to resolve, but `keywordPlacement.placement_` fails because that column has no underscore.
- **Enum values are this entity's own.** `matchType_` is upper case (`EXACT`/`PHRASE`/`BROAD`), and `placement` is an **unprefixed** display string (`Top of Search on-Amazon` / `Detail Page on-Amazon` / `Other on-Amazon`). Three different value spaces share the name "placement": this one, `factEntity: "placement"` (same strings but `SP-`/`SB-` **prefixed**), and `get_entity_metadata(entity='placement')` (`topOfSearch` / `productPage` / …). A value from the wrong space is accepted and returns zero rows — see `field-reference.md` → Placement.
- **SP only**, span ≤ 7 days. A `campaignType` filter is dropped here (SP-only source), so filtering for SB/SD returns an empty set that means "wrong entity", not "no data".
- **Metric set is restricted**: base metrics, Same/Other-SKU variants, and `CTR`/`CVR`/`CPC`/`CPA`/`ACOS`/`ROAS`. Requesting an NTB / DPV / video / viewability / impression-share / ASIN-business metric **fails the call** — that column doesn't exist here.
- **AI metrics are placeholders on this entity**: `AISpend`/`AISales` return `0`, `AIACOS`/`AIROAS` return `null` (accepted, but meaningless). Never report them as real values and never use them as a denominator — switch to `factEntity: campaign` for AI attribution.

## When the user wants a longer hourly window

"Show me the hourly pattern for last month" cannot be one call. Options, in order of preference:

1. Aggregate hour-of-day across several ≤7-day calls and **tell the user you sampled** (e.g. "based on the last 4 weeks, one week per call").
2. Fall back to daily granularity and state that hourly data is limited to a 7-day window.

Don't silently truncate the range to 7 days and present it as the month.
