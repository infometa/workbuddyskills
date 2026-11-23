# SparkX AI MCP Campaign Creation — Platform Notes

## The tools

`create_sp_sb_campaign` batch-creates Sponsored Products campaigns and their children.
`create_sp_ad_group` adds ad groups to existing SP campaigns; it is non-atomic and has its
own recovery contract in `create-sp-ad-group.md`. `create_sd_campaign` exists in the codebase
but is **not registered on this server**, so it will not appear in your tool list.

## Auth & scope

- Authenticate via bearer token. Always call `get_user_authorized_context` first and pass
  only a `profileId` it returned.
- `tenantId` / `userId` / `userName` are injected server-side from the token — never pass or
  fabricate them.
- Creating campaigns requires **`amazon_sa_campaign_create:write`**. This is a *different*
  scope from `amazon_sa_campaign_edit:write` (used by `batch_update_ads`) and from
  `amazon_sa_managed_group:write`. A token that can edit campaigns may still be unable to
  create them — if the tool is missing or refused, that is a scope question, not a syntax one.
- A `profileId` outside the token's grant is rejected outright; nothing partial is applied.

## One profile per call

`profileId` is a single top-level value, not a list. Campaigns for two stores are two calls,
and each is its own atomic unit.

## Campaign-creation batches are all-or-nothing

If any campaign, ad group or child object fails — tool-side validation or the downstream
write — **nothing is created**. There is no partial batch to reconcile and no "retry the
rest": fix the input and resend the whole thing.

This applies to `create_sp_sb_campaign`, not `create_sp_ad_group`.

## Response envelope

Success:
```json
{ "isError": false, "toolName": "create_sp_sb_campaign", "requestId": "a1b2c3d4e5f6",
  "data": { "status": "success", "result": [ 41398, 41399 ] } }
```

`result` is the list of **internal** campaign ids, in the order you sent the campaigns. There
is no per-object detail beyond that — no ad group ids, no child ids, no Amazon ids.

Failure comes back in one of two shapes, depending on whether the tool or the surrounding
pipeline rejected it:
```json
{ "isError": true, "errorType": "invalid_params", "message": "<message>",
  "recoveryHint": "<hint, if any>" }
```
```json
{ "isError": true, "errorType": "business_error", "service": "Amazon_SA_Service",
  "message": "<downstream message>" }
```

⚠️ **The downstream reports business failures as HTTP 200 with a non-zero code**, so a failure
is not an exception — it is a message. Read it; do not assume success from the absence of an
error status.

## Rate limits

The configured write budget is **20 calls/min**, per tenant+tool and per user+tool (reads
get 120). Whether limiting is enabled is an environment setting, so treat it as a ceiling to
plan against rather than something you can count on being off.

A confirmation flow costs **two** calls, and a write/read-back loop adds a read each time. A
serial pass over many entities will hit the ceiling - batch instead of looping, and honour
`retryAfterSeconds` on `rate_limited`.

## Non-idempotent

Every call creates new objects. A repeat creates duplicates, and campaign names must be
unique per profile, so a blind retry typically produces "Duplicate name" rather than silent
duplication — but do not rely on that as a safety net. **On a timeout or an ambiguous result,
read back with `get_entity_metadata(entity='campaign')` before resending.**

## Verify — the envelope is not proof

Success means the objects were created **locally**. It does not mean they are on Amazon, and
it does not mean delivery has started. Read back with
`get_entity_metadata(profileIds=[...], entity='campaign', userContext='...')` and confirm the
settings that matter — budget, state, targeting type, bidding strategy — before reporting
success in those terms.

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
