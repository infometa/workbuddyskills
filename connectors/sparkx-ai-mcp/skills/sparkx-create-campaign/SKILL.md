---
name: sparkx-create-campaign
description: >-
  Create new Amazon Sponsored Products campaigns in bulk through `create_sp_sb_campaign`, or add
  ad groups to an existing SP campaign through `create_sp_ad_group` -
  promoted products, negatives, and either auto targeting, keywords, or product targets.
  New-campaign creation also supports placement adjustments and an optional audience. Use when the
  user wants to build / launch / set up a new campaign - 新建广告活动 / 建一个自动广告 /
  开个手动词的活动 / 按这批 ASIN 建活动 - or add ad groups under an existing SP campaign.
  It is not for editing existing objects (use sparkx-edit-ads), for AI managed groups (use sparkx-create-ai-group), or
  for reading data (use sparkx-query-ads-performance / sparkx-query-entity-metadata).
metadata:
  version: 1.0.5
---

# Create Sponsored Products campaigns and ad groups

Two tools: `create_sp_sb_campaign` and `create_sp_ad_group`. Both use scope
`amazon_sa_campaign_create:write`, separate from the
edit scope - a token that can edit campaigns cannot necessarily create them.

## Sponsored Products only, right now

The tool is named `create_sp_sb_campaign`, but this server currently enables **SP only**.

- **Sponsored Brands is refused at the entry**, with an error naming the types that are
  enabled. **Do not retry the same type.** Tell the user SB creation is not available here
  and point them at the web console.
- **Sponsored Display has no tool at all.** `create_sd_campaign` is not registered, so it
  will not appear in your tool list. Do not go looking for it.
- The enabled set is server configuration and can widen later without a code change. **Trust
  the error over this document**: if a type is refused, it is off; if it succeeds, it is on.

Everything below describes the SP path. Sections that apply only to
`create_sp_sb_campaign` or only to `create_sp_ad_group` say so explicitly.

## These writes create live configuration

A created campaign or ad group is live configuration. There is no "draft" state and no undo
through these tools - a mistake has to be cleaned up in `sparkx-edit-ads` or the console, one
object at a time.

**Use `state: "paused"` while testing.** A paused campaign or ad group can be enabled in one
edit afterwards. Creating enabled and fixing later can spend during the gap.
**A `create_sp_sb_campaign` batch is atomic.** If any campaign, ad group or child object fails validation or
the downstream write, **nothing is created** - not even the campaigns that were fine. So a
failure is safe, and the fix is to correct and resend the whole batch, never to "retry the
rest".

## Before you build anything

1. `get_user_authorized_context` -> the `profileId`. **One profile per call**; campaigns for
   two stores are two calls.
2. `get_entity_metadata(entity='asin')` -> the ASINs you will promote, and **their SKUs on a
   Seller profile**. Do not invent SKUs; see "Seller vs Vendor" below.
   **An ASIN that returns nothing may be a parent** - see "A parent ASIN cannot be advertised"
   below before telling the user it doesn't exist.
3. If the user asked for keyword or product-target suggestions, the suggestion entities live
   in `sparkx-query-entity-metadata`. All of them need exactly one `profileId`, but **their
   mandatory filters differ - they are not interchangeable**:

   | Entity | Mandatory filter |
   |---|---|
   | `suggestedKeyword`, `keywordGroup`, `suggestedTarget` | `filters.asin` |
   | `suggestedBid` | `filters.asin`, plus one of two mutually exclusive modes |
   | `amcAudience` | **`filters.campaignType`** (`sponsoredProducts` / `sponsoredBrands`; SD is rejected). It takes **no `asin`** |

4. **For new campaign creation, picking an audience is its own step, not part of the
   suggestion sweep.** `create_sp_ad_group` has no audience fields.
   `amcAudience` also takes `filters.audienceSegmentType`, and **that filter chooses which of
   the two pools you see**. Omitting it does not widen the search - it silently narrows it to
   `SPONSORED_ADS_AMC`, so every Amazon-built audience is invisible and the user never learns
   it existed. **The filter takes one value only** - a two-value array is rejected outright
   (`accepts a single value only, got 2`), so there is no single call that returns both
   pools. When the user names the type, query that pool. When they do not, either ask, or
   **make two separate calls - one with `SPONSORED_ADS_AMC`, one with `BEHAVIOR_DYNAMIC` -
   and merge the two results into one list for them to choose from**, saying which pool each
   came from. Never let the default pick the audience.
5. Decide the targeting type **before** writing anything - the campaign's and the ad group's
   together. They decide which child lists are legal, and sending the wrong ones fails the
   batch.

## Pick the targeting type first - campaign and ad group together

The console shows one 投放类型 / Targeting radio on the campaign, but the request carries a
second `targetingType` on each ad group, and the two must agree.

A campaign is `targetingType: "auto"` or `"manual"`, and an ad group is
`targetingType: "keyword"` or `"target"` (omitted on a manual campaign: inferred from content - only keywords -> keyword, only targets -> target, both or neither rejected). Only three combinations exist:

| What the user wants | campaign | ad group | Child lists you may send |
|---|---|---|---|
| let Amazon match automatically | `auto` | `target` (required) | `targetBid` **and** `productAds`; negatives of **both** kinds allowed |
| bid on search terms | `manual` | `keyword` | `keywords` + `productAds`; **`negativeKeywords` only** |
| target ASINs or categories | `manual` | `target` | `targets` + `productAds`; **`negativeTargets` only** |

Two things fall out of this table that are easy to get wrong:

- **An auto campaign's ad group must be `target`**, not `auto`. Sending
  `targetingType: "auto"` on the ad group is rejected.
- **Under manual targeting the ad group's dimension also constrains the negatives.** A
  `keyword` ad group must not carry `negativeTargets`, and a `target` ad group must not carry
  `negativeKeywords`. Auto campaigns accept both kinds. This mirrors the console, where the
  two panels are mutually exclusive.

The non-selected lists must be **empty**, not omitted-and-hoped-for: sending `keywords` on an
auto campaign fails the batch.

## The seven rules that will bite you

**1. On `create_sp_sb_campaign`, `biddingStrategy` is required and has no default.** SP accepts `legacyForSales`,
`autoForSales` or `manual`. Omitting it stores an empty strategy, so pick one explicitly and
say which one you picked.

**2. An auto campaign must cover all four target groups.** `targetBid` needs `closeMatch`,
`looseMatch`, `substitutes` **and** `complements`, each at most once. **To disable one, send a
negative bid - do not omit it.** An omitted group is a validation failure, not a default.

**3. Keywords are unique per (`keywordText`, `matchType`) inside an ad group.** A repeat is
**rejected**, not silently de-duplicated - the downstream would otherwise create two rows with
different bids. Deduplicate before sending.

**4. On a Seller profile every promoted product needs `sku`, and the pair is verified; on a
Vendor profile `sku` must be omitted.** See "Seller vs Vendor".

**5. Budget-vs-bid validation differs by tool.** `create_sp_sb_campaign` checks every
`defaultBid` / `targetBid` / keyword bid / target bid against the campaign budget; a negative
auto-targeting bid is exempt. `create_sp_ad_group` checks `defaultBid` against the existing
campaign budget when that budget can be read; do not claim that its child bids received the
same budget-cap check.

**6. On `create_sp_sb_campaign`, `siteRestrictions` makes several other fields illegal.** Its only value is
`AMAZON_BUSINESS`, it exists only on US/CA/MX/UK/DE/FR/IT/ES/IN/JP, and when you set it you
must omit `siteAmazonBusinessAdjustment`, **every `audience*` field**, and
`offAmazonBudgetControlStrategy`. Amazon rejects those combinations and the downstream would
drop them silently. Note the tool does **not** fill in the usual
`offAmazonBudgetControlStrategy` default when `siteRestrictions` is set, precisely so the
request matches what actually takes effect.

**7. On JP profiles every bid and budget must be a whole number.** No decimals anywhere.

## Seller vs Vendor

| | Seller | Vendor |
|---|---|---|
| Product ad identity | **ASIN + SKU** | ASIN alone |
| `sku` on `productAds` | **required** | **must be omitted** - a non-blank `sku` rejects the whole call |
| Verification | each `(asin, sku)` pair is checked against the shop's catalog, plus SP eligibility | SP eligibility only |

On a Seller profile a pair that is not found is **rejected**. Read SKUs from
`get_entity_metadata(entity='asin')` - never construct one.

On a Vendor profile send `asin` only. A non-blank `sku` rejects the whole call (nothing is
created): the downstream would send that SKU to Amazon instead of the ASIN, and Amazon
identifies vendor products by ASIN. A blank `sku` is treated as omitted.

On both profile types a product whose `asinSpEligibilityStatus` is `INELIGIBLE` rejects the
whole call (nothing is created); check it via `get_entity_metadata(entity='asin')` first.

⚠️ **If the catalog lookup itself fails, the call is rejected too** (nothing is created). That
error means *retry*, not *change the ASIN*. Resending a different ASIN because a lookup
failed is how you end up advertising the wrong product.

## A parent ASIN cannot be advertised - expand it to its children

`get_entity_metadata(entity='asin')` lists **advertisable products**, and a parent ASIN is not
one of them: Amazon advertises the child (variation) ASINs, never the parent. So a user who
hands you a parent gets an empty lookup, which reads as "this product doesn't exist" when it
actually means "this one can't be advertised, but its children can".

**When `{"asin": "<value>"}` returns no rows, re-query by parent before concluding anything:**

```
get_entity_metadata(entity='asin', filters={"parentAsin": "<the same value>"})
```

- **Rows come back** -> it is a parent. **Deduplicate the rows** (the same child can appear more
  than once), then show the children - ASIN and title - and ask which ones to advertise.
- **Still nothing** -> it genuinely isn't in this profile's catalog. Say so; don't guess at a
  different ASIN.

⚠️ **Do not substitute silently.** "Couldn't find it, so I advertised all its children" is a
different campaign from the one the user asked for, and a parent can have many children. Expand,
show, and let them choose - the preview is where they see what will actually be promoted.

⚠️ **Do not decide parentage from the field alone.** A standalone product with no variations
comes back with `parentAsin` equal to its own `asin`. The only reliable test is the pair of
queries above: not found as `asin`, found as `parentAsin`.

This is a lookup detail, not a reason to change the product. The "lookup failure means retry,
not a different ASIN" rule above still applies.

## Audience targeting is optional, and verified

**Three fields, one atomic group.** Configuring an audience means sending `audienceId`,
`audienceSegmentType` **and** `audienceBidPercentage` together, or none of them.
`audienceBidPercentage` is an integer 0-900 **sent as a string**; `audienceSegmentType` is
`SPONSORED_ADS_AMC` or `BEHAVIOR_DYNAMIC`.

**All three are enforced.** An `audienceId` without an `audienceBidPercentage` is rejected,
and **`audienceSegmentType` is required whenever `audienceId` is set** - there is no default
to fall back on.

**The server checks that the id really belongs to the pool you named.** Before any campaign is
created it looks the `audienceId` up in the audience list for that `profileId`,
`campaignType` and `audienceSegmentType`. An id from the other pool, or one that no longer
appears in the list, is **rejected**; so is a lookup that fails or comes back empty. The check
covers the whole request, so **one bad binding stops every campaign in the batch**.

A wrong pool therefore fails loudly now rather than silently - but that does not make guessing
cheap, because the rejection costs the entire batch. Copy **`audienceId` and
`audienceSegmentType` from one and the same** `get_entity_metadata(entity='amcAudience')`
row - that entity echoes the type on every row exactly so the pair travels together.
**Never substitute that query's default type for the campaign's real one**:
`SPONSORED_ADS_AMC` is the default *of the lookup*, not a fact about the audience you picked.

**There is no "audience off" flag here.** To create without an audience, omit all three
fields. (`audienceBidAdjustmentEnabled` exists only on the edit path, for clearing a binding
that already exists.)

⚠️ **A successful write still does not prove Amazon applied the binding.** Validation
confirms the id belongs to the pool, not that the targeting went live. Don't report it as
confirmed on Amazon's side from the write response alone.

### ⚠️ `portfolioId` wants the **Amazon** portfolio id, and it is verified

This is the one field where the usual rule inverts. Everywhere else a write takes the
internal id; here the tool checks the value against the shop's portfolios and requires
**`amazonPortfolioId`** - the long one from `get_entity_metadata(entity='portfolio')`, not the
much shorter same-named `portfolioId` in that response.

Sending the internal id fails with `portfolioId must be an Amazon portfolio ID belonging to
profile ...`, which is a good error but an easy one to earn: the two fields differ only by
prefix. A portfolio belonging to another shop is rejected the same way.

**Convert the type as you copy it.** `amazonPortfolioId` comes back from
`get_entity_metadata` as a **string**; this request field is a **number**. Parse the digits
and send `"portfolioId": 123456789012345`, not `"123456789012345"`.

## The console can do three things this tool cannot

The user may be looking at the creation page while talking to you. These parts of it have no
equivalent here - say so and point at the console rather than approximating:

1. **从词库添加 / Add from keyword list.** The negatives panels have an "Enter list" tab and
   an "Add from keyword list" tab. Only the first has an equivalent: send the words in
   `negativeKeywords`. **Keyword lists (词库) are not supported by MCP at all** - you cannot
   reference one, and you cannot enumerate its contents to paste them in.
2. **自动定向 → 设置默认出价 / Automatic targeting → Set default bid.** The console lets an
   auto campaign run on one default bid instead of per-group bids. This tool always requires
   all four groups in `targetBid`; there is no "just use the default" mode. If the user wants
   a single bid, send the same value four times and tell them that is what you did.
3. **Adding ad groups to an existing non-SP campaign.** `create_sp_ad_group` supports existing
   Sponsored Products campaigns only. Use the console for SB or SD.

Terminology for everything the tool *does* support is mapped to the console's own labels in
[`references/sp-fields.md`](references/sp-fields.md) - use those labels when you talk to the
user.

## Batch limits

| Limit | Value |
|---|---|
| campaigns per call | **20** |
| ad groups per campaign | **50** |
| items in any one child list | **1000** |
| child items across the whole call | **5000** |

Split larger campaign-creation workloads into several calls. Each
`create_sp_sb_campaign` call is its own atomic unit, so report per call which ones landed.

For `create_sp_ad_group`, the limit is **10 ad groups per call**. That tool is deliberately
**non-atomic**: it creates rows sequentially and may return `partial_success`. Read
[`references/create-sp-ad-group.md`](references/create-sp-ad-group.md) before building or
recovering that request.

## Workflow

```
1. get_user_authorized_context           -> profileId (one per call)
2. get_entity_metadata(entity='asin')    -> ASINs, and SKUs on a Seller profile
3. (optional) suggestion entities        -> keywords / targets / bids / audiences
4. Route the request: new campaign -> `create_sp_sb_campaign`; new ad groups under an
   existing SP campaign -> `create_sp_ad_group`.
5. Decide the required targeting type(s). Ambiguous -> ASK, do not pick.
6. Build the request and check that tool's limits.
7. Show the user what will be created and get a yes.
8. Call the selected create tool.
9. Read back the created campaign/ad groups. On an ambiguous ad-group result, read back
   before retrying and retry only entries proven missing.
```

Step 7 is not optional. This is a write that can start spending.

Step 9 matters more than usual here: success means the objects were created **locally**.
`create_sp_sb_campaign` returns only campaign ids; `create_sp_ad_group` returns per-item
results, but neither response proves Amazon synchronization or delivery.

## Confirm before creating

Show, in the user's own terms: whether this creates a campaign or adds ad groups to an
existing one; the campaign and ad-group names; budget/start/bidding settings when creating a
campaign; targeting, ASINs, and enabled/paused state. Then get a yes.

If the user has explicitly waived confirmation, announce the same summary and proceed without
waiting - see the waiver rules in `sparkx-edit-ads`. A waiver for editing does not authorize
creating: it has to cover creation.

## After the write

**The response gives internal ids, not Amazon ids.** Creation completes locally first and the
Amazon id appears later, after sync. So:

- Report campaigns and ad groups **by name**.
- If the user asks for an id, give the internal one and say plainly that the Amazon id is not
  available until the campaign syncs. **Do not poll for it and do not invent one.**
- Do not claim a campaign or ad group is live on Amazon. It exists in the platform; delivery
  starts only after synchronization and, when created paused, after it is enabled.

Full convention: [`references/platform-notes.md`](references/platform-notes.md) -> "Naming
things in your answer".

## Do not guess - ask

- **"建个自动广告"** - auto targeting, or a manual campaign they will manage themselves? These
  are different `targetingType`s and cannot be converted afterwards through this tool.
- **budget** - daily budget. If the user names a monthly figure, ask rather than dividing.
- **"用这些词"** - as keywords (they bid on search terms) or as product targets? Different
  child list, different ad group dimension.
- **"先别花钱"** - create `paused`. Say that you did.
- Anything the registered tools cannot do - SB, SD (including SD
  creatives) - say so and point at the console. Do not approximate it with something else.

## Reference files

| File | Read it when |
|---|---|
| [`references/sp-fields.md`](references/sp-fields.md) | Creating a new campaign with `create_sp_sb_campaign`; campaign fields and shared SP labels |
| [`references/create-sp-ad-group.md`](references/create-sp-ad-group.md) | Adding ad groups to an existing SP campaign; non-atomic results and recovery |
| [`references/platform-notes.md`](references/platform-notes.md) | Auth, envelope, errors, and how to name things in your answer |

Sibling skills you will need installed: `sparkx-query-entity-metadata` (ASINs, SKUs,
portfolios, suggestions), `sparkx-edit-ads` (anything after creation).
