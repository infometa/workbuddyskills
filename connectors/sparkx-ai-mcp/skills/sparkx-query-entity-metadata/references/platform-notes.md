# SparkX AI MCP Read Tools — Shared Platform Notes

This file holds behavior that is **common to all 3 read tools** (`get_ads_perf`, `get_entity_metadata`, `get_operation_log`). It ships as `references/platform-notes.md` **inside each skill's own folder** — so this copy travels with the skill you're reading even if a Skill Hub installs/updates/downloads one skill folder at a time, since the reference file is nested under the same folder, not a sibling directory. Every skill that reads platform data (the three read skills plus the report/analysis skills built on them) carries a byte-identical copy for the same reason — this is intentional duplication for delivery robustness, not a mistake. Read this once per session before making tool-selection decisions.

## Auth Flow

All 3 tools authenticate via Bearer Token, handled by a shared pipeline (pre-ratelimit → auth → business ratelimit → error mapping). Each tool method itself only does param validation + business logic.

**Before calling any of the 3 read tools, you must first call `get_user_authorized_context`** to obtain the current token's authorized `profileIds`, `tenantId`, `userId`.

`get_user_authorized_context` response:
```json
{
  "isError": false,
  "toolName": "get_user_authorized_context",
  "userId": "12345",
  "tenantId": "2064",
  "profiles": [
    {"profileId": 4404871489220462, "profileName": "Star-Store-US", "countryCode": "US"},
    {"profileId": 9283746501928374, "profileName": "Star-Store-JP", "countryCode": "JP"}
  ]
}
```

How to use this:
- `profiles[].profileId` → the `profileIds` param for all 3 tools
- `profiles[].countryCode` → resolve "US store" style user references to a profileId
- `profiles[].profileName` → resolve store-name references
- **User didn't specify a store** → default to passing **all** authorized `profileIds` (cross-store aggregate; monetary metrics come back in USD — see Currency below)

**Always source `profileIds` from this call's response verbatim.** Never hand-type an ID, reuse one from an earlier session, or carry one over from a user message without confirming it appears in `profiles[]` — unauthorized IDs now fail the whole request (see below).

## Permission Scopes

Each tool requires a specific OAuth scope on the token. If a call fails with an auth/permission error, this is the likely cause — tell the user their token/role is missing the corresponding scope rather than guessing at a query bug.

| Tool | Required scope |
|---|---|
| `get_ads_perf` | `amazon_sa_performance_data:read` |
| `get_entity_metadata` | `amazon_sa_ads_configuration:read` |
| `get_operation_log` | `amazon_sa_ads_logs:read` |

## profileIds Authorization: All-or-Nothing

**All 3 tools require every requested `profileId` to be authorized. There is no silent intersection — one unauthorized ID fails the entire request.**

- every value in `profileIds` must appear in `get_user_authorized_context`'s `profiles[]`, and must be a positive integer
- if any requested ID is outside the authorized set, the call fails with `isError:true`, `errorType: invalid_params`, message `Requested profileIds contain unauthorized values` — **no partial results, no empty success**
- non-positive or non-numeric values fail with `Parameter 'profileIds' must contain only positive integers`
- `effectiveProfileIds` in the response echoes back the scope that was actually queried; since the request now fails outright on any mismatch, treat this field as a confirmation echo rather than a "did anything get dropped?" check

Practical consequences:
- For "swap store X for all my current stores" style requests, re-call `get_user_authorized_context` and use its list as-is. Don't append or splice IDs from memory.
- A permission change mid-session (store removed from the user's access) turns previously-working calls into hard failures. On `Requested profileIds contain unauthorized values`, re-fetch the authorized context and tell the user which store is no longer in scope — don't retry the same ID list.
- `entity='aiGroup_schedule'` on `get_entity_metadata` is stricter still: it needs **exactly one** authorized `profileId` (see that tool's skill).

## Diagnosing Zero/Empty Results

Any of the 3 tools can legitimately return zero rows for reasons that have nothing to do with "no data exists." Before telling the user "there's no data for that," work through this sequence — don't jump straight to that conclusion from the first empty response:

1. **Check `isError`.** If `true`, this isn't an empty-data situation at all — it's an error (see the error-handling section above). Handle it as an error, not as "no results."
2. **Check `effectiveProfileIds`.** An unauthorized profile can no longer cause a silent empty result — that fails as `invalid_params` with `Requested profileIds contain unauthorized values` (see profileIds Authorization above), so it shows up in step 1, not here. What this field is still good for: confirming you queried the store the user actually meant. If the user asked about "the JP store" and `effectiveProfileIds` holds the US profile, the empty result is a targeting mistake on your side — fix the profile and retry before concluding anything about the data.
3. **Check the date range for T+2 delay effects (`get_ads_perf` only) — but note this is different from a range violation.** If `dateStart`/`dateEnd` genuinely exceed the 90-day span or 15-month lookback, that's a request-construction mistake that should surface as `isError:true` (`errorType: invalid_params`) per the error-handling rules above — it should not come back as a silent empty success. If you're instead seeing `isError:false` with empty/incomplete rows for a *valid* range that includes "today" or very recent days, that's the T+2 delay: recent data genuinely hasn't finished processing yet, which is a legitimate (if unhelpful) empty-but-correct result — not a bug and not "no data exists," just "not processed yet."
4. **Confirm the requested fields/metrics are actually valid for the `factEntity`/`entity` in use** (see the Metrics × Entity Support Matrix). Requesting an unsupported combination is documented as a common source of `invalid_params` errors — so this should also come back as `isError:true`, not a silent empty result. If you're getting empty-but-non-error rows, an invalid metric/entity combination is an unlikely explanation; look at filters and data existence instead (steps 5-6).
   ⚠️ **This does not apply to `select` on `get_entity_metadata`.** An unknown name there is **dropped, not rejected**: the call succeeds, the field is simply missing from every row, and the only trace is `meta.hint` (`Unknown select fields ignored: [...]`). So a field that reads as empty everywhere is a spelling mistake until you have checked `meta.hint`, and "the call returned 200" proves nothing about the names you asked for. The `invalid_params` behaviour above is about **filters and metrics**, not about `select`.
5. **If you filtered by an id, check that the field and the value belong to the same id space.** Both spaces are filterable: `campaignId` / `adGroupId` / `targetId` / `keywordId` / `productAdId` take the internal id, `amazonCampaignId` / `amazonAdGroupId` / `amazonKeywordId` / `amazonTargetId` take the Amazon one. The mistake is the **mismatch** - e.g. passing an `amazonCampaignId` taken off a performance or log row as `campaignId`. That is a valid filter whose value matches nothing, so it returns zero rows **without an error**. **Judge by the field name the value came out of**, not by its length and not by which tool returned it: a `get_operation_log` row carries `entityId` (internal) and `amazonEntityId` / `amazonCampaignId` (Amazon) at the same time, and `portfolioId` is Amazon-side on `campaign` but internal on `portfolio`. The entity field tables are the source of truth.
6. **Remove your business filters (`filters`) and retry.** If removing filters (state=enabled, spend thresholds, etc.) suddenly returns rows, the entity/data exists but didn't match your filter conditions — the honest answer to the user is "nothing matches your filter criteria," not "you have no data at all." These are different statements — don't conflate them.
7. **If you still get zero rows after 1-6, confirm the entity itself exists** via `get_entity_metadata` (e.g. does this campaign ID actually exist for this profile?). A nonexistent entity and an existing-but-inactive-in-this-window entity warrant different answers to the user.

**Only after working through this sequence** can you responsibly tell the user "there's genuinely no data/activity in that range" — and even then, be specific about what you checked (e.g. "no spend recorded for campaign X between these dates, and the campaign does exist and is enabled") rather than a bare "no data found."

## Diagnosing inflated or non-reconciling numbers

> **Before diagnosing anything: are the two numbers even from the same source?** "Cross-source"
> does not only mean different MCP tools. It includes any of these:
>
> - the same period queried through different `get_ads_perf` fact entities or aggregation
>   levels, such as a campaign row versus summed ad-group, target, search-term, product-ad or ASIN
>   rows;
> - performance facts from `get_ads_perf` compared with current configuration from
>   `get_entity_metadata`, or with historical events from `get_operation_log`;
> - the same logical report run at different times while late-attributed orders, report rows or
>   operation-log backfill are still arriving.
>
> **Common cases.** Use campaign facts for a campaign total; do not force that total to equal the
> sum of ASIN, product-ad, target or search-term detail. A campaign containing one requested ASIN
> still reports the whole campaign's spend, including its other products. Use ASIN/product-ad
> facts for product attribution instead. A metadata `dailyBudget`, a logged `currentBudget`
> change and performance `Spend` are three different concepts, not three readings of one
> number. Likewise, today's metadata describes what can act now; it does not prove what was
> configured when an older log event occurred.
>
> Different sources can refresh on different schedules and continue accepting late data, so two
> figures for the same dates can differ slightly. A few cents, a click or two, or a fraction of a
> percent is normally timing, not a defect. Record the tool, fact entity, aggregation level and
> run time before comparing results.
>
> **The rule: one judgement, one source.** Pick the source and entity level that answer the
> question, and compute every number for that judgement from it. When two sources must be shown,
> label both and explain whether the gap is expected semantics or refresh timing. Escalate only
> when like-for-like results from the same source, scope, dates and snapshot still differ by an
> amount material to the conclusion.

The opposite failure of the one above: the call succeeds, the rows look reasonable, and the
totals are several times the truth. It happens when a dimension from another entity doesn't
match one-to-one, so every fact row is repeated once per match, each copy carrying the full
value. Nothing errors.

**The known high-risk shape** is splitting a non-product entity by a product dimension
(`productAd.*`, `asin.*`, `sku.*`, `productLine.*`, `parentAsin.*` on a `campaign` / `adGroup` /
`target` / `searchTerm` / `keywordPlacement` query) - always check that one. The server rejects
some of these outright, but **rejection covers only the combinations already known to be
unsafe**; it is not evidence that everything it lets through is one-to-one. So also check any
cross-entity join whose cardinality you cannot confirm.

> **The check.** Re-run the same query **without** the extra dimension. `SUM(Spend)` across the
> split rows must equal the unsplit total. If it is larger, the rows are duplicated - do not
> report them.

**Recovering without changing the question.** Which fix is right depends on what was asked, and
they are not interchangeable:

| The user asked for | Do this |
|---|---|
| Ad performance per product ("spend / ACOS by ASIN") | Re-query with `factEntity: "productAd"` - its rows are one per advertised product |
| Targets or search terms **within** a product scope ("keywords that ran for this ASIN") | **Keep the original `factEntity`** and narrow it by ad group - three steps, see below |
| A real target x product or search-term x product cross-split | **Not available** - spend is not attributed per product at that level. Say so; do not substitute either row above |

Switching to `productAd` answers "how did this product do", not "which search terms ran for this
product". Silently swapping one for the other is a wrong answer, not a workaround.

**Narrowing target / search-term performance to a product takes three steps, not two**, because
the metadata and performance tools use different id spaces:

1. `get_entity_metadata(entity='productAd')` filtered to the ASIN or SKU -> gives the
   **internal** `adGroupId` (that row carries no `amazonAdGroupId`).
2. `get_entity_metadata(entity='adGroup')` filtered by those internal ids -> gives
   `amazonAdGroupId`.
3. Filter the performance query on `p.adGroupId_` with those distinct **Amazon** ids.
   `p.` is the fact table itself, so this filters it directly rather than joining ad-group metadata to do the same thing; it is also the form the backend's own split-query
   test uses. `adGroup.adGroupId_` returns the same rows, just less directly.

> ⚠️ **Skipping step 2 returns zero rows and no error.** Both `p.adGroupId_` and the
> dimension form `adGroup.adGroupId_` hold Amazon's id on the performance side, so an
> internal id is a valid filter that matches nothing. The
> `UNSUPPORTED_PERFORMANCE_JOIN` error message describes only steps 1 and 3 - following it
> literally produces an empty result that reads as "this product had no search terms", which is
> a wrong answer, not an empty one. This is case 5 of the zero-results checklist above.

Report the outcome for what it is: **search terms or targets in the ad groups that contain this
product**. An ad group usually holds several products, so this is a scope, not an attribution -
never state or imply that the spend or traffic belongs to that ASIN.

Two giveaways in the rows themselves: **identical values repeated across products** (the same
spend and orders on every ASIN is one value copied, not a coincidence), and **a filtered total
larger than the unfiltered one**, which is never possible.

## Error Response Format

**Every error uses a single `errorType` key.** Check `isError:true` first, then read `errorType`; depending on the error, extra fields accompany it (`requestId`, `recoveryHint`, `service`, `dimension`, `retryAfterSeconds`).

**Tool-execution errors** (parameter validation, query failures) — `errorType`:
```json
{
  "isError": true,
  "toolName": "get_ads_perf",
  "requestId": "a1b2c3d4e5f6",
  "errorType": "invalid_params",
  "message": "Parameter 'profileIds' is required and cannot be empty",
  "recoveryHint": "..."
}
```

**Pipeline errors** (auth, rate limit, downstream service) — same `errorType` key, plus error-specific fields:
```json
{
  "isError": true,
  "errorType": "rate_limited",
  "dimension": "tenant",
  "retryAfterSeconds": 30,
  "message": "Rate limit exceeded on dimension [tenant]. Retry after 30 seconds."
}
```

`requestId` is present on responses (success and error) and is the support handle. **When you report a tool failure to the user, include `requestId`** — it's what lets the platform team trace the call. It may be absent in local/dev environments.

**`errorType` enum** (every value uses the `errorType` key):

| identifier | Meaning | Common cause |
|---|---|---|
| `invalid_params` | Bad parameters | Missing required param, bad date format, date span over limit, unauthorized `profileIds`, `pageSize` out of range, illegal `timeGranularity`, null filter value |
| `serialization_error` | Serialization failure | Rare fallback case |
| `rate_limited` | Rate-limited | Token bucket exhausted on one dimension — retry after `retryAfterSeconds` |
| `rate_limit_service_unavailable` | Rate limiter down | The limiter fails **closed**: when it can't check, the request is rejected (429), not let through |
| `token_invalid` | Auth failure (401) | Token expired/invalid |
| `permission_denied` / `scope_missing` / `api_not_authorized` | Auth failure (403) | Token lacks the tool's scope, or the user's role lacks the underlying permission |
| `profile_out_of_range` | Auth failure (403) | Requested profile outside the token's grant |
| `business_error` | Backend / query-execution error (most common) | Read the semantic `message` and branch (unknown field, filter value type mismatch, result set too large, execution timeout, server busy); downstream service errors carry a `service` field (e.g. `Amazon_SA_Service`) |
| `timeout` | Query timeout | Narrow the range and retry |
| `service_unavailable` | Backend data source unavailable | ClickHouse connection pool exhausted — transient, retry shortly. With `service: td-api` (sdCategory / categoryBrand) the platform credential for the category service was rejected — a server-side configuration issue; retrying will not help |
| `auth_service_unavailable` | Auth service unavailable | Auth check failed closed (503) — transient, retry shortly. **An invalid or expired token is not this**: the auth service answers 4xx and the gateway now returns **401 / 403**, which is permanent — re-authenticate instead of retrying |
| `capability_unavailable` | Capability check unavailable | A dependent capability lookup failed; the request was **not executed** — retry the same call unchanged later (`service: Auth_Service`, message `能力查询暂不可用，请稍后重试`) |
| `query_shape_unsupported` | The entity combination cannot be joined | **Not retryable — change the query, not the timing.** The requested `factEntity` and dimensions cannot be connected: either a granularity rule blocked the path or the entities are unrelated. Messages read `Cannot connect CTEs: [...]` or `Cannot connect all terminal nodes, remaining: [...]`. Drop the dimension that doesn't belong to the fact entity's own hierarchy, or query it separately and join the results yourself. Previously this came back as `business_error`, so older advice to "retry" does not apply |

**The configured rate-limit policy** (token-bucket, per 60s window). Whether limiting is switched on is an environment setting, so you may never hit these — but plan against them rather than assuming they're off:

| Layer | Dimension | Budget |
|---|---|---|
| Pre-auth | client IP | 60 / min |
| Pre-auth | token prefix | 300 / min |
| Business | tenant + tool name | read **120 / min**, write 20 / min |
| Business | user + tool name | read **120 / min**, write 20 / min |

The `dimension` field on a `rate_limited` error tells you which bucket you hit: `ip`, `token_prefix`, `tenant`, or `user`. All 3 read tools count as reads (120/min per tool, per tenant and per user). A "loop pages until `hasNextPage=false`" plan over a large account can realistically hit this — pace the loop and raise `pageSize` toward the cap instead of firing many small pages.

**How to handle each error when talking to the user:**
- `invalid_params` → almost always a query-construction bug on the agent's side (bad field name, missing required param, date range too wide, unauthorized profile, out-of-range `pageSize`). Fix the call and retry — don't tell the user "the tool doesn't support this" until you've checked field names/param names against this skill's reference tables.
- `rate_limited` → wait `retryAfterSeconds` before retrying the *same* call. Don't retry in a loop. If it recurs, tell the user the query is being throttled and narrow scope (smaller date range, fewer profiles, fewer pages).
- `rate_limit_service_unavailable` → not your query's fault and not retryable immediately; the platform is failing closed. Tell the user the service is temporarily rejecting requests.
- `token_invalid` / `permission_denied` / `scope_missing` / `profile_out_of_range` → an auth/permission problem, not a query bug. Name the scope the tool needs (see Permission Scopes) and tell the user to have their token/role updated. Retrying the same call won't help.
- `business_error` → **read the `message` and branch — it is semantically translated, do NOT blindly retry**: `unknown field 'X'` → fix the field name against field_reference and retry; `filter value type mismatch` → fix the filter value's type and retry; `result set too large` → narrow the date range / add filters; `execution timeout` → narrow and retry; `server is busy` → wait a few seconds and retry; any other internal error → report as a transient failure and quote `requestId`.
- `timeout` / `service_unavailable` / `auth_service_unavailable` → backend/dependency temporarily unavailable, not a param problem. (**A bad or expired token is not in this group** — it comes back as **401 / 403** and retrying never fixes it.) Retry once; if it persists, tell the user the data source is temporarily unavailable (quote `requestId`). Exception: `service_unavailable` with `service: td-api` (sdCategory / categoryBrand) means the platform credential was rejected — do not retry and never invent category or brand IDs; tell the user category lookup is currently unavailable.
- `serialization_error` → rare edge case; report as a transient tool error, retry once.

Messages are sanitized server-side: SQL, tokens, signed URLs, internal hostnames, stack traces, and raw table names are redacted (you may see `[SQL_REDACTED]`, `[redacted_token]`, `[internal]`, `[table]`). Don't treat a redaction marker as corruption, and don't try to reconstruct what was removed.

Always check `isError` before reading `rows` — do not assume a response without `isError:false` explicitly checked is safe to parse as data.

## Null Filter Values Are Rejected

**Do not put null in `filters`.** All 3 read tools reject a null filter value (`invalid_params`, naming the field). This is intentional: a null used to be silently dropped, turning the query unconditional and returning **unfiltered full data** — indistinguishable from "the condition matched every row". The classic trigger: you look up an ID, the lookup returns empty, and you splice that empty result straight in as a filter value. **Abort on the empty result** instead.

### Query for genuinely-empty rows (`get_ads_perf` only)

```json
{"filters": {"campaign.campaignName_": {"isNull": true}}}
{"filters": {"campaign.campaignName_": {"isNotNull": true}}}
```

The boolean says whether the test holds, so `{"isNull": false}` equals `{"isNotNull": true}`. `isNull` rows + `isNotNull` rows = the unfiltered whole.

**`get_entity_metadata` has no null-test operator** (its downstream vocab is only eq/ne/in/notin/like/between) — to drop a constraint, just omit the field.

## Pagination Rules

| Tool | Pagination style | Default pageSize | Max pageSize | Out-of-range value |
|---|---|---|---|---|
| `get_ads_perf` | `page` + `pageSize` | 100 | 500 | **Error** |
| `get_entity_metadata` | `page` + `pageSize` | 100 | 500 | **Error** |
| `get_operation_log` | single non-`aiGroup` entity: `page` + `pageSize`; multi-entity or `aiGroup`-only: limit-only | 100 | 1,000 (`aiGroup`-only 10,000) | Clamped silently |

**The two behaviors are different — this bites when you compute `pageSize` instead of hard-coding it.** On `get_ads_perf` and `get_entity_metadata`, a `pageSize` of `0`, a negative number, or anything over `500` fails the call with `invalid_params` (`Parameter 'pageSize' must be between 1 and 500`); `page` ≤ 0 fails with `Parameter 'page' must be greater than 0`. Nothing is clamped for you. So a derived value like `pageSize = min(topN, 500)` must also be floored at 1 — `topN=0` is now an error, not an empty page. `get_operation_log` still clamps (it takes `min(pageSize, max)` and doesn't complain), so don't port either assumption to the other tools.

`get_entity_metadata` with `entity='aiGroup_schedule'` ignores pagination entirely and returns every schedule for the group in one call; its response omits `page`/`pageSize`/`hasNextPage`.

`get_operation_log` has **two modes decided by `entities`**. When `entities` is exactly one non-`aiGroup` entity: **real pagination**; loop `page` while `hasNextPage=true` to retrieve the complete set (raise `pageSize` toward 1,000 to cut round trips). When `entities` is empty/multiple or only `aiGroup`: **limit-only**; a single call caps at `pageSize` (max 1,000, or 10,000 for `aiGroup`-only), always time-descending; check `truncated`. On `truncated=true` you cannot page; first prefer steering the user to a single entity (real pagination), otherwise split the date range into non-overlapping sub-windows and recurse (see `sparkx-query-operation-log`'s "Getting a Complete Count"); adding `resourceIds`/`operationType`/`changeBy` filters is a last resort (changes *what* you're searching for; flag the result as partial).

## Date Range Limits

**⚠️ Illustrative dates**: any concrete date shown in this skill's own example files (e.g. `2026-06-01`) is for format illustration only — it will eventually fall outside the 15-month lookback window as time passes. Always substitute real dates that satisfy the constraints below at call time; never copy an example's literal date value into a live call without checking it's still within range.

| Tool | Max date span | Earliest lookback | Format |
|---|---|---|---|
| `get_ads_perf` (daily) | 90 days | 15 months | `YYYY-MM-DD` |
| `get_ads_perf` (hourly — `timeGranularity: hourly`, or `factEntity: keywordPlacement`) | **7 days** | 15 months | `YYYY-MM-DD` |
| `get_operation_log` | 90 days | 15 months | `YYYY-MM-DD` |
| `get_entity_metadata` | No date limit (no date params at all) | — | — |

**Hourly (AMS) queries are capped at 7 days, not 90.** This applies to `timeGranularity: hourly` (campaign only, SP+SB+SD) and to `factEntity: keywordPlacement` (SP only, hourly by nature). Exceeding it is an error, not a truncation. `hourly` on any entity other than `campaign` is also an error — it is not ignored and does not fall back to daily. `keywordPlacement` additionally uses asymmetric field naming (bare names in the request, `_`-suffixed keys in the response) and a restricted metric set. See `sparkx-query-ads-performance` for the full hourly rules.

These are two **separate** hard constraints on the `dateStart`/`dateEnd` request parameters, not "auto-truncate":
1. **Max span is 90 days, counting both endpoints (inclusive).** Precisely: `dateEnd - dateStart` (as a plain date subtraction) must be **≤ 89**, not ≤ 90 — since both `dateStart` and `dateEnd` count as covered days, a subtraction of 90 actually spans 91 inclusive calendar days, one more than the limit. Think of it as "≤ 90 inclusive calendar days," and derive the subtraction bound (89) from that, not the other way around. **Weekly/monthly aggregation (`select: [..., "toMonday(...) as week"]`) does NOT let you bypass the span limit either way** — it only reduces the number of *rows* a single already-compliant call returns. If the user wants a window longer than 90 days (e.g. "performance over the last 12 months by month"), you **must first split into multiple calls, each spanning ≤90 inclusive days** (a full year typically needs **5** such calls, not 4 — calendar quarters are 91-92 days and don't reliably fit under the 90-day cap, so don't split by quarter; see sparkx-query-ads-performance's aggregation-over-time example for a worked, verified split), and *then*, within each call, optionally use week/month aggregation in `select` to reduce that call's row count. Splitting is mandatory; aggregation is optional and orthogonal.
2. `dateStart` cannot be more than 15 months before today — going further back returns an error, it does not silently clamp the range for you.

If a user's requested range exceeds 90 days, **proactively split it** into sequential ≤90-day calls rather than sending one oversized request and waiting for it to fail.

**Data delay**: ad performance data has a T+2 delay. "Today"'s data is usually incomplete. When the user doesn't specify an end date, default `dateEnd` to **yesterday**, not today.

### Date Format: Query Params vs. Data Fields

**These are two different formats — do not use one where the other is expected.**

| Where | Format | Example |
|---|---|---|
| `dateStart`/`dateEnd` request params (`get_ads_perf`, `get_operation_log`) | `YYYY-MM-DD` | `"2026-06-01"` |
| `date` dimension field returned in `get_ads_perf` rows (daily grouping) | `YYYYMMDD` (no dashes) | `"20240601"` |
| `campaignStartDate`/`campaignEndDate` fields in `get_entity_metadata` | **string, format varies** — `"20260101"` *or* `"2026-01-01"`, sometimes `""` | one known campaign: use its returned value as-is. Across campaigns: **do not filter server-side** — page to the end and compare client-side |
| `createdDate` field in `get_operation_log` rows | Full timestamp, **timezone varies by entity + `profileIds` count** — see the next section | `"2026-08-24 07:01:06"` |

Concretely: when you *request* a date range, always use `YYYY-MM-DD`. The `date` dimension **returned by `get_ads_perf`** is `YYYYMMDD` with no separators. But **`campaignStartDate`/`campaignEndDate` on `get_entity_metadata` have no fixed format** — a live sample contained both `"20260101"` and `"2026-01-01"`, plus empty strings, and **the two shapes can coexist in one result set**. So:

- **Reading one known campaign's dates**: use the value as returned, parsing whichever shape it is.
- **Filtering a date range across campaigns**: **do not filter server-side on these fields at all.** A filter can only be written in one shape, so it silently drops every row stored in the other. Narrow with other filters (`campaignState`, `campaignType`, `portfolioId`…), page to the end, then parse both shapes and compare client-side.
- **If you did not page to the end**, say the result is partial rather than presenting it as the full set.

**Never strip the dashes just to build a server-side filter on these fields** — that turns a
non-match into a wrong match. Client-side is the opposite: **do** parse both shapes into real
date values and compare those, rather than comparing the strings.

### ⚠️ `get_operation_log`'s `createdDate` timezone depends on your request shape

**Confirmed by testing (2026-08): the timezone of `createdDate` is not fixed — it varies with the entity type and with how many `profileIds` you passed.**

| Entity in `entities` | profileIds count | `createdDate` timezone | Example |
|---|---|---|---|
| `aiGroup` (SP/SB) | one or many | **UTC** | `2026-08-24 05:58:50` |
| `aiGroup` (SD) | one or many | **downstream DB timezone — undocumented** | `2026-08-24 05:58:50` |
| `campaign` / `adGroup` / `target` / `placement` | **one** | **Store-local time** | `2026-08-24 00:01:06` (LA time) |
| `campaign` / `adGroup` / `target` / `placement` | **many** | **UTC** | `2026-08-24 07:01:06` (UTC) |

Verified against a single pause record on a US (`America/Los_Angeles`, UTC-7) profile: requesting one `profileId` returned `00:01:06`, requesting two returned `07:01:06` — exactly the 7-hour LA daylight-saving offset for the *same event*.

**What this means in practice:**

- **The same log entry can carry two different timestamps** depending on how many stores you queried. Adding a second store to a query silently shifts every ad-entity timestamp in the result by that store's UTC offset.
- **Never compare or merge timestamps across a single-profile result and a multi-profile result.** They're in different clocks. If you already pulled single-store data and then widen to all stores, re-pull rather than stitching.
- **Never present `createdDate` as "the store's time" without knowing which branch you're in.** In a multi-profile call, a `2026-08-24 07:01:06` on a US store is 00:01 local — reporting it as "7am" is wrong by a business day's worth of interpretation near midnight.
- **Mixed `entities` mean mixed clocks in one response.** A query with `entities: ["campaign", "aiGroup"]` returns UTC for **SP/SB** aiGroup rows (and the downstream DB's timezone for **SD** aiGroup rows) alongside (if single-profile) store-local campaign rows, in one time-sorted list. The sort itself is done on the raw string, so a mixed-clock result is not reliably chronological.
- **There are three clocks, not two.** Ad-entity rows are store-local for a single profile and **UTC for multiple profiles**; **SP/SB** managed-group rows are UTC; **SD** managed-group rows follow the **downstream database's** timezone, which is not stated anywhere. So an SP/SB-only managed-group query is safe to call UTC, while a query that can return SD managed-group rows cannot be given a single zone label at all — say which rows you could not place.
- **Choose deliberately:**
  - Want store-local times the user can match against their own console? Query **one profile at a time** and restrict `entities` to ad entities.
  - Want a comparable cross-store timeline? Query **multiple profiles**, which puts **ad-entity rows** in UTC, or convert client-side using each row's `countryCode`, and label the output as UTC. **This does not normalise managed-group rows** — SP/SB aiGroup is UTC either way, and SD aiGroup stays on the downstream DB's clock no matter how many profiles you query.
- **When you show a timestamp, label the zone** ("2026-08-24 07:01 UTC" / "2026-08-24 00:01 store time"). An unlabeled timestamp from this tool is ambiguous by construction.

Note this is a property of the log data itself; the MCP layer passes `createdDate` through unchanged and does no conversion.

### Unconfirmed: which timezone the `dateStart`/`dateEnd` *filter* boundary uses

Separate from the above: the platform spec still doesn't state which timezone `dateStart`/`dateEnd` are interpreted in when resolving a day boundary. Given the `createdDate` behavior just described, don't infer it — a request-level boundary in one zone and a returned value in another are entirely possible.

This matters most for boundary-sensitive windows ("yesterday") on non-UTC stores in multi-country queries: you can be off by up to a full day at the edges.

- When precision matters, say you're not certain which zone the boundary uses and treat results near day boundaries as approximate.
- Prefer an explicit reference point ("results for 2026-07-19") over a bare relative date ("yesterday"), so any boundary ambiguity is visible rather than baked into an unlabeled range.

## Currency Rules

Amount fields carry a `currency` indicator, but the exact mechanism differs by tool/entity — read carefully, this is a common source of dollar-amount misinterpretation with multi-store customers.

### get_ads_perf

| Scenario | Outer `currency` | Behavior |
|---|---|---|
| Single profile | That profile's local currency code (e.g. `"JPY"`) | All monetary metrics (Spend/Sales/CPC/etc) in local currency |
| Multiple profiles | `"USD"` | All monetary metrics auto-converted to USD |

**Exception**: the `asin.asinPrice_` dimension field (product list price) is **always local currency** and is NOT affected by the USD conversion above, even in a multi-profile query. If `select` includes `asin.asinPrice_` on a multi-profile call, that one field's value does not match the outer `currency=USD` — cross-reference `profile.countryCode_` to determine its actual currency.

### get_entity_metadata

**One rule, one place.** Which entities carry a per-row `currency`, which carry only
`meta.currency`, which carry neither, and when a `USD` label is a real answer versus a failed
lookup - all of that lives in **`query-entity-metadata`'s field reference**, under "Where the
currency lives, per entity". It is not repeated here, because a table copied into 24 files
drifts the moment the behaviour changes.

The two things worth knowing without opening it:

- **Amounts are never FX-converted.** Every figure is in its own store's currency, whatever
  label the envelope carries.
- **A `USD` in `meta.currency` may mean "could not resolve".** Do not sum across stores, and
  do not label a multi-store figure as USD, on the strength of that code alone.

### get_operation_log

Amount-bearing fields (e.g. `previousValue`/`newValue` for a `dailyBudget` change) are always **local currency** — there is no cross-profile USD conversion for logs. Each row carries a `currencyCode` field (e.g. `"USD"`/`"JPY"`) mapped from that row's `countryCode`.

This tool *may* also emit an outer `currency`, inferred from the rows: if every row shares one currency you get that code, if the result mixes currencies you get the literal string **`"mixed"`**, and if no row carries a currency the field is absent. **`"mixed"` is not a currency** — never render an amount as "123 mixed" or sum across rows when you see it; fall back to each row's own `currencyCode` and either report per-store or state that amounts aren't directly comparable.

## Ratio Metric Display Rule

**Use the confirmed field list below rather than generalizing from a metric's name.** The server explicitly calculates these percentage metrics on a ×100 scale.

### Confirmed ×100 percentage metrics

Checked one by one against the SQL the server builds: `ACOS`, `CTR`, `CVR`, `AdsCVR`, `TACOS`,
`ShippedTACOS`, `OrderedTACOS`, `AIACOS`, `DPVR`, `NTBOrdersRate`, `NTBUnitsRate`, `NTBSalesRate`,
`ViewableImpressionsRate`, `AdsSalesRate`, `AdsOrdersRate`, `AdsUnitsRate`,
`AdsSalesSameSKURate`, `AdsOrdersSameSKURate`, `Video5SecondViewRate`,
`UnitSessionPercentage` and `UnavailabilityRate` all end in `* 100`. `BuyBoxPercentage` comes
out on the same scale: its source column is already 0–100, and the expression divides by 100
only to weight by page views, then multiplies back (prod source median 96.4). `aiGroup.targetAcos_` on
`get_entity_metadata` is on the same scale.

For the fields listed above:

- **The number is already ×100 — never multiply or divide by 100 again.**
- **Append `%` when you show it.** `"ACOS": 17.61` is 17.61%, and `"TACOS": 17.61` is 17.61%
  too. Relaying the bare number reads as a ratio and understates it a hundredfold.
- **Filters take the same ×100 number, with no `%` in the JSON**: `{"ACOS": {"<": 20}}` means
  "under 20%". `{"ACOS": {"<": 0.2}}` means "under 0.2%", which is almost never intended.

**`UnavailabilityRate` changed scale.** It used to come back as a 0–1 ratio rounded to two
decimals (`0.99`); it is now on the same ×100 scale as the fields above (`99.29` = 99.29%), and
its filters take the ×100 number too (`{"UnavailabilityRate": {">": 20}}` = over 20%). A figure
pulled before the change is a hundredth of today's - convert it before comparing.

### Passed through from the source, already 0–100

`VTR` and `TopOfSearchIS` get no `* 100` here, but their source columns are themselves on a
0–100 scale (prod samples: `VTR` median 22.5; `TopOfSearchIS` 5.09 / 44.82 / 69.98, max 100).
Show them with `%` and don't rescale them, exactly like the list above.

- **`VTR` is summed across rows**, not averaged. One entity on one day stays within 0–100;
  a query that rolls several days or entities into one row can return more than 100, which is
  no longer a rate. Break it down by day and entity, and don't present a rolled-up value above
  100 as a percentage.

### `vCTR` - don't use it as a percentage

`vCTR` is also passed through, but its source values are out of range for any rate (prod raw
rows: 99th percentile around 4696, max 80000). That is an upstream calculation problem, not a
scale this service applies. Don't show it as a percentage, don't apply thresholds to it, and
don't rescale or clip it to make it look plausible. If the user asks for it, give the raw number
and say the field's calculation is under review.

### Everything else

Do not infer a field's scale from its name. A field not covered above has no confirmed scale -
follow its field-specific contract, and do not rescale it merely because its name implies a
rate or percentage.

`ROAS`, `AIROAS`, `CPC`, `CPA`, `CPO` are **not percentages** — plain ratios or currency-per-unit (e.g.
`ROAS: 5.68`). Neither is `vCPM`: its expression multiplies by 1000, because it is a cost per
thousand viewable impressions - never append `%` to it.

## Multi-Profile Row Attribution

When a call spans **more than one** `profileId`, make sure the response can actually be attributed back to a specific store before presenting results — rows with the same campaign/entity name across different stores are otherwise indistinguishable to the user.

- **`get_ads_perf`**: add `"profile.profileId_"` (and usually `"profile.profileName_"`) to `select` whenever `profileIds` has more than one entry, so each row carries its store identity.
- **`get_entity_metadata`**: check whether the entity's returned rows include a `profileId` field (e.g. the `asin` entity does — see its Currency example). If the entity type you're querying doesn't surface `profileId` on its own, either issue one call per `profileId` or cross-reference by combining with a `get_ads_perf`/`asin` call that does carry `profileId`, before presenting a merged answer across stores.
- **`get_operation_log`**: every row already carries `profileId` (see ChangeLogVO fields) — map it to the store's `profileName` using the `profiles` list from `get_user_authorized_context` before describing a change to the user, especially when `entities`/`resourceIds` span multiple stores with same-named campaigns.

## Tool Selection Decision Tree

```
User intent:
├── Has a time range + wants metric data (spend/sales/ACOS/clicks/...)
│   ├── by hour / "which hours convert" / intraday pattern
│   │   └── → get_ads_perf (timeGranularity=hourly, campaign only, ≤7 days)
│   ├── keyword × placement breakdown
│   │   └── → get_ads_perf (factEntity=keywordPlacement, hourly by nature, ≤7 days)
│   └── → get_ads_perf (daily, default)
├── Asking about config/list/status (no metrics, no date range)
│   ├── "what campaigns exist" → get_entity_metadata (entity=campaign)
│   ├── "AI managed group config" → get_entity_metadata (entity=aiGroup)
│   ├── "the managed group's schedule / flights / seasonal plan"
│   │   └── → get_entity_metadata (entity=aiGroup_schedule; one profileId, filters.aiGroupId only)
│   ├── "this group runs on a rule — show me the rule's actual conditions/actions"
│   │   └── → get_entity_metadata (entity=aiGroup) and read aiAutomation.{ruleType}
│   │       (rule-mode config is readable; it is NOT writable through MCP)
│   ├── "product info / ASIN" → get_entity_metadata (entity=asin)
│   ├── "portfolio list" → get_entity_metadata (entity=portfolio)
│   └── "which automation rules are enabled on this campaign" → get_entity_metadata (entity=automationRule)
├── "Who did what" / "what did AI change" / "change history"
│   └── → get_operation_log  (mind the createdDate timezone rules)
└── Needs both metrics AND config
    └── get_ads_perf first for the data → get_entity_metadata to enrich with names/config
```

**Common combined-call patterns**:
- "What's the bidding strategy of the highest-spend campaign?" → `get_ads_perf` (find the top campaign) → `get_entity_metadata` (look up its config)
- "How did the AI managed group perform last week?" → `get_ads_perf` with `select` including `aiGroup.aiGroupName_`
- "What bids did AI change yesterday?" → `get_operation_log` with `changeBy=ai`, `actionType=Bid Increased/Bid Decreased`
- "Why did my ACOS go up?" (root-cause investigation, all 3 tools) → `get_ads_perf` twice to quantify the change and identify the affected campaign(s) → `get_operation_log` on that campaign over the same window to find candidate changes → `get_entity_metadata` for current config context. Report findings as correlation, not proven causation — see the dedicated ACOS root-cause example.

## Implicit Inference Rules

These are semantic mappings the agent should apply automatically when translating natural language into tool params.

### Metric name mapping (get_ads_perf)

| User says | Maps to metric | Note |
|---|---|---|
| Orders / conversions | `Conversions` | **Not** `Orders` — there is no metric literally named `Orders` |
| Spend / ad cost | `Spend` | — |
| Sales / revenue | `Sales` | — |
| Total sales | `TotalSalesAmount` | `asin` entity only |
| TACOS | `TACOS` | `asin` entity only |
| New-to-brand | `NTBOrders` + `NTBSales` | Pick based on what's asked |

### Status/filter inference (get_ads_perf, dimension fields use `entity.field_`; get_entity_metadata, plain camelCase — see each tool's own SKILL.md for the exact field format)

| User says | Inferred filter (ads_perf form) |
|---|---|
| AI-managed / AI ads | `{"aiGroup.aiStatus_": 1}` |
| Ads without AI enabled | `{"OR": [{"aiGroup.aiStatus_": 0}, {"aiGroup.aiStatus_": 2}]}` — **`OR` works on `get_ads_perf` only**; `get_entity_metadata` has no logical nodes, use `{"aiStatus": [0, 2]}` there |
| Active / running ads | `{"campaign.campaignState_": "enabled"}` |
| Paused keywords | `{"target.targetState_": "paused"}` |
| "By portfolio" analysis | add `{"portfolio.portfolioId_": {">": 0}}` (exclude campaigns with no portfolio) |
| "By product line" analysis | add `{"productLine.productLineParentId_": {">": 0}}` |
| SP ads | `{"campaign.campaignType_": "sponsoredProducts"}` |
| SB ads | `{"campaign.campaignType_": "sponsoredBrands"}` |
| SD ads | `{"campaign.campaignType_": "sponsoredDisplay"}` |

### Time inference

**`get_ads_perf` is subject to the T+2 data delay** (see above) — default `dateEnd` to **yesterday** whenever the user doesn't give an explicit end date, since "today"'s ad performance data is usually incomplete.

| User says (get_ads_perf) | Inferred range |
|---|---|
| Last week | `dateStart` = last Monday, `dateEnd` = last Sunday |
| This month | `dateStart` = 1st of this month, `dateEnd` = yesterday |
| Last 30 days | `dateStart` = 30 days ago, `dateEnd` = yesterday |
| Quarter-to-date (QTD) | `dateStart` = 1st day of the current calendar quarter (Jan/Apr/Jul/Oct 1st), `dateEnd` = yesterday |
| Year-to-date (YTD) | `dateStart` = January 1st of the current year, `dateEnd` = yesterday |
| "Since this campaign launched" / "since we started" | **Not a fixed offset — look it up, then convert it.** Query `get_entity_metadata` (`entity: "campaign"`) for that campaign's `campaignStartDate`, parse it (it may come back as `"20260101"` **or** `"2026-01-01"`, and `""` means no start date is recorded), and **reformat it to `YYYY-MM-DD` before passing it as `dateStart`** — `get_ads_perf` rejects the compact form. **Constrained by the 15-month lookback**: if the launch date is more than 15 months ago, you cannot query the full lifecycle in one range — say so explicitly ("I can only go back 15 months; this campaign launched earlier than that, so this covers the most recent 15 months, not the full history") rather than silently truncating and presenting it as the complete picture |

**⚠️ Check for a reversed range before sending it — this month/QTD/YTD can produce `dateEnd < dateStart` on the first day of the period.** These rules all use "yesterday" as `dateEnd` (per the T+2 rule) but "1st of the period" as `dateStart`. If today is the 1st of the month/quarter/year, `dateStart` = today's date but `dateEnd` = yesterday — which is *before* `dateStart`, an invalid, reversed range. Concretely: querying "this month" on July 1st gives `dateStart=2026-07-01`, `dateEnd=2026-06-30` (reversed). The same happens for QTD on Jan/Apr/Jul/Oct 1st, and for YTD on January 1st. **Always compute `dateEnd` and compare it to `dateStart` before issuing the call.** If `dateEnd < dateStart`, do not send the request — the period genuinely has no completed days to report yet (e.g. "this month" on July 1st has zero elapsed complete days). Tell the user that directly ("this month just started, so there's no completed-day data yet") rather than sending a reversed range and letting it error, or worse, silently swapping the two dates and reporting the wrong period.

**⚠️ QTD/YTD/"since launch" frequently exceed the 90-day single-call cap — check the actual span before issuing one call.** A full quarter is 91-92 days on its own (already over the limit), so QTD past the first ~2 months of a quarter, any YTD beyond Q1, and "since launch" beyond ~3 months **all require the same split-then-merge procedure** as the aggregation-over-time example: split into contiguous ≤90-day windows first, then merge results by re-grouping on whatever time key you aggregated on and recomputing derived ratio metrics (`ACOS`/`CTR`/`CVR`/etc) from the summed base metrics — never average pre-computed ratios across windows. Don't assume "QTD" or "YTD" is safe to send as a single `dateStart`/`dateEnd` pair just because the phrasing sounds like one range — compute the actual day count first.
| Period-over-period / week-over-week (unspecified) | take an equal-length prior period, issue two `get_ads_perf` calls |
| Month-over-month (full calendar months, e.g. "July vs June") | compare the two full calendar months **as-is — do not force equal length** (months are 28-31 days); note the day-count difference to the user, and add each month's daily average if the user cares about rate rather than raw totals |
| Month-to-date-over-month-to-date (e.g. "this month so far vs last month so far") | align to the **same number of elapsed days** in each month (equal length is correct here, unlike full-calendar-month above) |

See the dedicated Period-over-Period and Top Movers example for the full procedure in all cases (join by ID, matching granularity/filters, full pagination before comparing, handling new/disappeared entities, zero-denominator deltas).

**`get_operation_log` has no documented processing delay** — operation logs record changes as they happen, not as a batch-aggregated report. Do **not** apply the same "default to yesterday" rule here.

| User says (get_operation_log) | Inferred range |
|---|---|
| Today's changes / what changed today | `dateStart` = `dateEnd` = **today** (not yesterday) |
| Last week | `dateStart` = last Monday, `dateEnd` = last Sunday |
| This month | `dateStart` = 1st of this month, `dateEnd` = **today** |
| Last 7 days | `dateStart` = 6 days ago, `dateEnd` = **today** |

## Common Pitfalls

- **`like` wildcard handling**: any `%` you include in a `like` pattern is stripped and replaced with an automatic leading+trailing `%` (case-insensitive substring match). Writing `{"like": "%test%"}` and `{"like": "test"}` behave the same — always effectively "contains", not prefix/suffix match.
- **Multi-profile `get_ads_perf` metrics are USD** (except `asin.asinPrice_`, which stays local). **`get_entity_metadata` is the opposite** — its config amounts stay in each store's currency and every row carries its own `currency`; see Currency Rules. When reporting a multi-profile **`get_ads_perf`** figure, say "in USD" explicitly so the user doesn't assume local currency. When reporting **`get_entity_metadata`** amounts, present each row with its own `currency` and **never label the combined result as USD** — group by currency, or convert explicitly and say so.
- **Multi-profile rows need store attribution** — see Multi-Profile Row Attribution above; don't merge same-named campaigns across stores without labeling which store each row belongs to.
- **`get_operation_log` pagination depends on `entities`**: a single non-`aiGroup` entity paginates for real (loop `page` until `hasNextPage=false`); multi-entity or `aiGroup`-only is limit-only. In limit-only mode with `truncated=true`, first prefer steering the user to a single entity (real pagination), otherwise split into non-overlapping date sub-windows until each returns `truncated=false`; if a single day alone is still truncated, say so rather than reporting a partial count as complete.
- **Query-param dates (`dateStart`/`dateEnd`) are `YYYY-MM-DD`; `get_ads_perf`'s `date` dimension is `YYYYMMDD`; `campaignStartDate`/`campaignEndDate` are strings of *no guaranteed format* — sample them before filtering** — see Date Format above. These are NOT interchangeable.
- **`get_ads_perf` max span is 90 days on the request itself** — week/month aggregation reduces row count within a call, it does NOT let one call's `dateStart`/`dateEnd` exceed 90 days. Split first, aggregate second.
- **Confirmed percentage metrics are pre-scaled ×100** — use the explicit field list in Ratio Metric Display Rule rather than assuming every `*Rate`/`*Percentage` name has the same implementation. For confirmed fields such as `ACOS`, `CTR`, `CVR`, `TACOS`, `AdsCVR`, `targetAcos`, and `UnitSessionPercentage`, don't re-scale, but **do append `%`** when presenting (`"17.61%"`); filters stay on the raw ×100 scale (`{"ACOS": {"<": 20}}`). `ROAS`/`CPC`/`CPA` are not percentages.
- **Metric/field names are case-sensitive** — `Spend` ✓, `spend` ✗, `SPEND` ✗.
- **Field-naming convention differs by tool** — see the "Field Naming Rules" section in each tool's own SKILL.md before constructing `select`/`filters`. Do not assume the two tools share one convention.
- **One unauthorized `profileId` fails the whole call** — no silent dropping any more. Always take IDs verbatim from `get_user_authorized_context`.
- **`pageSize` out of range is an error on `get_ads_perf`/`get_entity_metadata`** (clamped only on `get_operation_log`) — floor any computed `pageSize` at 1 and cap it at the tool's max yourself.
- **Hourly/AMS queries cap at 7 days, not 90** — applies to `timeGranularity: hourly` (campaign only) and `factEntity: keywordPlacement` (SP only). `hourly` on any other entity errors rather than falling back to daily, and `keywordPlacement` requests use bare field names while its responses come back `_`-suffixed.
- **`get_operation_log`'s `createdDate` timezone shifts with the request** (SP/SB `aiGroup` = UTC, SD `aiGroup` = downstream DB timezone / unknown; ad entities = store-local for one profile, UTC for many) — always label the zone, never merge single- and multi-profile results. See the timezone section above.
- **`currency: "mixed"` on `get_operation_log` is not a currency** — read each row's `currencyCode` instead of formatting or summing.
- **`get_entity_metadata`'s `aiGroup` response is a projection of what's *currently effective*** — fields belonging to a disabled switch, and rules running in AI mode, are omitted rather than returned with stale values. A missing field means "not in effect", not "not configured" and not "write failed". See that skill for the full rules.

## Naming things in your answer: names first, Amazon ids when asked

Users think in names, not numbers. An internal id is this platform's own primary key - it
means nothing on Amazon and nothing to the person reading your answer.

**Default to names.** Unless the user asked for an identifier, report `campaignName` /
`adGroupName` / `portfolioName` / `aiGroupName` / `asinTitle` and leave ids out entirely -
"Summer Tent SP - Exact spent $1,200 last week", not "campaign 41398 spent $1,200".

**If an id is shown, the name goes with it**: `Summer Tent SP - Exact (ID: 298539385213868)`.
Never a bare number.

**When the user asks for an id, give the Amazon one.** The same object has two different
numbers, and which one you get depends on the tool:

| Source | What its `campaignId` holds |
|---|---|
| `get_ads_perf` | the **Amazon** campaign id |
| `get_operation_log` | the **Amazon** campaign id |
| `get_entity_metadata` | the **internal** id - the Amazon one is the separate `amazonCampaignId` field |

Amazon-side fields per entity: `amazonCampaignId`, `amazonAdGroupId`, `amazonKeywordId`
(keywords and negative keywords), `amazonTargetId` (targets and negative targets),
`amazonAdId` (product ads), `amazonPortfolioId`. **Never present an internal id as "the
campaign ID", and never derive one identifier from the other** - they are unrelated numbers.

**Exports and tables carry both.** For a CSV, a spreadsheet, or any table the user will
reconcile against another system, give a name column **and** an Amazon-id column.

**Previews and confirmations.** A write preview echoes back the **internal** ids you sent.
Translate them to names before showing the user - nobody can meaningfully approve a change
to objects they cannot identify.

### Three exceptions

1. **Managed groups have no Amazon id.** A managed group is this platform's own construct,
   not an Amazon object, so no Amazon-side identifier exists. Report its name, and its
   internal `aiGroupId` when an id is asked for. The **campaigns inside** a managed group are
   ordinary Amazon objects and follow the rule above.
2. **Product ads have no name.** Identify one by **ASIN + SKU**; do not invent a label.
   (`placement` is an enum rather than an object - report the placement label itself.)
3. **A just-created object has only an internal id.** Creation returns local ids; the Amazon
   id appears later, once the object syncs. Report the name, and if an id is asked for give
   the internal one and say plainly that the Amazon id is not available yet. Do not poll for
   it, and do not invent one.

### Getting the name in the first place

`select` is a **strict projection**: ask for ids only and no name comes back. Whenever a
result will be shown to a user, put the name field in `select` as well - or omit `select`
entirely and take the full row.
