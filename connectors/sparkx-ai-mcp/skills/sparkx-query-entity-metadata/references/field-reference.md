# Field Reference — `get_entity_metadata`

## `entity` Enum Values (and backing provider)

| entity | Backing provider | Notes |
|---|---|---|
| `profile` | AdsListMetadataProvider | Store/profile list. **Can be queried standalone** — it is a first-class entity here, not a required-join-only dimension |
| `campaign` | AdsListMetadataProvider | Campaign list |
| `adGroup` | AdsListMetadataProvider | Ad group list |
| `target` | AdsListMetadataProvider | Targeting list |
| `productAd` | AdsListMetadataProvider | Product ad list |
| `keyword` | AdsListMetadataProvider | Keyword list - includes keyword groups and SB themes; see `matchType` |
| `negativeKeyword` | AdsListMetadataProvider | Negative keyword list, campaign-level and ad-group-level (see `businessType`) |
| `negativeTarget` | AdsListMetadataProvider | Negative product-target list (negative ASIN / negative brand) |
| `portfolio` | AdsListMetadataProvider | Portfolio list |
| `placement` | AdsListMetadataProvider | Placement list |
| `aiGroup` | AiGroupMetadataProvider | AI managed group list. Response is a **projection of the currently effective config** — see SKILL.md |
| `aiGroup_schedule` | AiGroupScheduleMetadataProvider | Schedules of **one** managed group — **requires exactly one `profileId` and `filters.aiGroupId` only**, ignores pagination/sorting |
| `asin` | AsinMetadataProvider | ASIN product info (child ASIN + parent ASIN + product line, nested) |
| `automationRule` | AutomationRuleMetadataProvider | Enabled rule-type codes/names for given campaign(s) — **requires `amazonCampaignId` in filters; does not return template configuration** |
| `amcAudience` | AmcAudienceMetadataProvider | Targetable audiences bindable to a campaign — **requires `filters.campaignType`; one profileId; not paginated. One call returns ONE audience pool** - `filters.audienceSegmentType` takes a single value and defaults to `SPONSORED_ADS_AMC`, so query once per type to see both |
| `keywordGroup` | KeywordGroupMetadataProvider | Keyword-group suggestions — **requires `filters.asin`; one profileId; not paginated** |
| `suggestedKeyword` | SuggestedKeywordMetadataProvider | Keyword suggestions — **requires `filters.asin`; one profileId; not paginated** |
| `suggestedTarget` | SuggestedTargetMetadataProvider | Product **and** category targeting suggestions — **requires `filters.asin`; one profileId; not paginated** |
| `suggestedBid` | SuggestedBidMetadataProvider | Suggested bid for a keyword or for auto targeting — **requires `filters.asin` plus one of the two modes; one profileId; not paginated** |
| `sdCategory` | SdCategoryMetadataProvider | Marketplace category tree flattened into rows — **one profileId; requires keyword, parentCategoryId or level; not paginated; capped at 500** |
| `categoryBrand` | CategoryBrandMetadataProvider | Brands available to refine one category — **one profileId; requires one categoryId; not paginated** |

### `currency` - a per-row field, plus an envelope fallback

A row's **`currency`** field holds that row's store currency. **It is emitted whenever the
underlying row carries one - it is not conditional on profile count**, so a single-profile
read can return it too (verified in the `asin` provider, whose row mapping adds it
unconditionally; the value is *omitted* rather than set to null when absent).

The envelope's `meta.currency` is the fallback, and **what it does varies by entity** - the
table below is the authority. Do not generalise from one entity to another.

**So: always prefer the row's own `currency`; fall back to `meta.currency` only when the row
has none, and treat a `USD` there as a claim to check rather than a fact.**

It is not listed in the per-entity tables below because it is not an entity field.
**`select` does not strip it**: the server re-adds `currency` after applying your projection,
so you never have to list it.

### Where the currency lives, per entity

| Entities | Single profile | Multiple profiles |
|---|---|---|
| AdsList entities | row `currency` **and** `meta.currency` when the currency resolves; if it does not, the row's `currency` is `null`, `meta.currency` is **dropped**, and a `meta.hint` says so | row `currency` only — `meta.currency` is omitted |
| `asin` | row `currency` when the downstream supplied one, plus `meta.currency` from the resolver — which **falls back to `USD`** if the lookup fails | row `currency` only — `meta.currency` is omitted |
| `aiGroup` | `meta.currency` only | `meta.currency` is **`"USD"`**, and amounts are **not** converted — see below |
| `aiGroup_schedule` | `meta.currency` only | n/a — **it requires exactly one `profileId`**; asking for several is an error, not a fallback |
| `keywordGroup`, `suggestedKeyword`, `suggestedBid` | `meta.currency` only | n/a — these accept exactly one profile |
| `automationRule`, `amcAudience`, `suggestedTarget`, `sdCategory`, `categoryBrand` | none | none — they return no amounts |

⚠️ **The two read-failure modes are opposite, so trust them differently.** When AdsList
cannot resolve a currency it **removes** `meta.currency` and flags it in `meta.hint` - absence
is the signal. `asin` instead goes through the resolver, which **substitutes `USD`** - so a
`USD` on an `asin` read may be a real answer or a failed lookup, and nothing in the response
distinguishes them.

⚠️ **`meta.currency: "USD"` can mean "we could not tell".** The resolver returns `USD` as a
fallback in three situations: more than one profile is in scope, the profile lookup failed, or
it came back without a currency code. In none of those has anything been converted - the
amounts are still each store's local currency.

So a `USD` label is only trustworthy when you asked for **one** profile and that store really
is a USD marketplace. In particular:

- **Never label a multi-store `aiGroup` figure as USD**, and never sum managed-group budgets
  across stores on the strength of that code. Query one profile at a time when the currency
  matters. (`aiGroup_schedule` cannot get into this state - it refuses a multi-profile request
  outright rather than returning a fallback.)
- On the bid-carrying suggestion entities the single-profile shape removes the multi-store
  ambiguity, but not the lookup-failure one - a suggested bid is in the store's own currency
  either way, so treat `USD` there as a label to verify, not a conversion.

When a customer needs the currency behind an `aiGroup` budget and you only have a fallback
`USD`, say the currency is not established rather than guessing.

### Money value types (string vs number - not uniform)

**Money types are not uniform across entities - check the per-entity table.**

- **Decimal strings** such as `"100.00"`: `dailyBudget`, `currentBudget`, `defaultBid`,
  `targetBid`, `portfolioBudget`, `profileDailyBudgetCap`, and `placement.multiplier` (which
  is a **percentage, not an amount**: `"50.00"` = +50%).
- **Numbers**: the `keyword` entity's `keywordBid` and `keywordCurrentBid`. These are the
  exception - do not assume the string form just because every other money field uses it.
  ⚠️ **`keywordCurrentBid` can be `0` for an entire store.** Observed in production:
  76,257 keywords in one profile all reading `0.00` while `keywordBid` was populated
  normally, and a second profile where the two fields matched row for row. Treat `0` as
  "no value", never as a bid, and never filter on it (`keywordCurrentBid >= 0.01` silently
  empties such a store and looks exactly like "no keywords matched").

MCP does not coerce either way. Parse the string form before doing arithmetic, and never
compare those as strings (`"9.00" > "10.00"` is true as text).

Internal ids are numbers (`campaignId`, `adGroupId`, `targetId`, `keywordId`, `portfolioId`,
`aiGroupId`, `productAdId`); Amazon-side ids and `profileId` are strings - except on the
`profile` entity itself, where `profileId` comes back as a number.

Dates are inconsistent: campaign dates are strings and may be `YYYYMMDD` or `YYYY-MM-DD` or
empty; portfolio dates are numbers (`YYYYMMDD`, `0` when unset). Build a date filter in the
shape a read of that same entity actually returned. `profileUseBudgetCap` can be `null` -
**null is not `false`**.

### The field to answer with, per entity

Answers go out by name (see `platform-notes.md` -> "Naming things in your answer"), so every
read that will be shown to a user needs its label field - and `select`, being a strict
projection, will not add it for you.

| Entity | Label field | Amazon-side id |
|---|---|---|
| `campaign` | `campaignName` | `amazonCampaignId` |
| `adGroup` | `adGroupName` | `amazonAdGroupId` (parent campaign: none - see below) |
| `keyword` / `negativeKeyword` | `keywordText` | `amazonKeywordId` |
| `target` / `negativeTarget` | **none** - see below | `amazonTargetId` |
| `productAd` | **none** - use `asin` + `sku` | `amazonAdId` |
| `asin` / `parentAsin` | `asinTitle` / `parentAsinTitle` | the ASIN itself is Amazon-side |
| `portfolio` | `portfolioName` | `amazonPortfolioId` |
| `profile` | `profileName` | `profileId` is already Amazon-side |
| `aiGroup` | `aiGroupName` | **none** - platform-only object, report `aiGroupId` |
| `placement` | the placement label itself | n/a - an enum, not an object |

`automationRule` returns `enabledRuleNames`, already human-readable and already localized.

**Three entities have no name to report**, so "answer with the name" needs a different shape
for them - say *what the thing is*, not a bare identifier:

| Entity | What identifies it | How to say it |
|---|---|---|
| `productAd` | `asin` + `sku` | "推广商品 B0XXXXXXXX (SKU: ...)" |
| `target` | `targetText` — an ASIN, a category, or an expression, depending on `targetType` | "商品定向 B0XXXXXXXX" / "类目定向 Headphones" — name the kind, then the value |
| `negativeTarget` | `negativeTargetText` — **the ASIN, or the brand id** | "否定商品 B0XXXXXXXX" / "否定品牌 <id>" — and say it is a brand id when that is what it is |

⚠️ `targetText` / `negativeTargetText` are **not** display names, so do not present them as
one. A brand id in particular is a number the user has no way to recognise: label it rather
than dropping it into a sentence where a brand name belongs.

The suggestion entities are recommendations rather than objects in the account, so they carry
no id/name split: report `audienceName` (with `audienceId` when binding one), `keywordText`,
`keywordGroupText`, `categoryName` / `categoryPath`.

## Fields by Entity

### profile

**Return fields**: `profileId`, `profileName`, `countryCode` (enum: `US`/`CA`/`MX`/`UK`/`DE`/`FR`/`IT`/`ES`/`JP`/`NL`/`AU`/`SG`/`BR`/`SE`/`AE`/`PL`/`IN`/`TR`/`SA`/`BE`/`EG`/`ZA`), `profileDailyBudgetCap`, `profileUseBudgetCap`

**Filterable**: `profileName` (`like` only) — e.g. `{"profileName": {"like": "%star%"}}`

### campaign

**Every campaign return field except `processStatus` is filterable** - per the underlying ads API, for the campaign
entity the filterable set otherwise follows the return fields (so `aiGroupId`,
`portfolioId` and `campaignStartDate`/`campaignEndDate` can all be used in `filters`, not
just the core fields below; the `campaignAi*Date` fields are placeholders and not worth
filtering on). The two tables are split for
readability only.

**Core fields:**

| Field | Type | Enum |
|---|---|---|
| campaignId | number | Internal auto-increment campaign ID; use this value for managed-group write-tool `campaignIds` and for every write route |
| profileId | string | Store profile ID. Required alongside the internal ID on every write |
| amazonCampaignId | string | Amazon campaign ID; use this value to link performance/log data, not as a managed-group write ID |
| campaignName | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| campaignState | string | `enabled` / `paused` / `archived` |
| processStatus | string/null | Enriched delivery status. Selectable but **not filterable or sortable**; empty is unknown, not enabled/delivering |
| biddingStrategy | string | `legacyForSales` / `autoForSales` / `manual` / `ruleBased` |
| targetingType | string | `auto` / `manual` |
| costType | string | `cpc` / `vcpm` |
| isAiCreate | int | `1` / `0` |
| dailyBudget | string | Local-currency **decimal string**, e.g. `"100.00"` |
| currentBudget | string | Decimal string. **Not the same field the write path adjusts** — budget writes and their previews are based on `dailyBudget`. **`0` is not a budget of zero**: it means no AI-adjusted value is recorded for the day. Never report "this campaign's budget is 0" from this field — read `dailyBudget` |

**Campaign ID contract:** `campaignId` and `amazonCampaignId` are different identifiers.
Managed-group create/edit tools accept the internal integer `campaignId`. When starting
from an Amazon campaign ID returned by `get_ads_perf` or `get_operation_log`, filter this
entity by `amazonCampaignId`, then use the matched row's internal `campaignId`. Never
coerce a long Amazon ID into the write field or infer one identifier from the other.

**Which one to report back.** The internal `campaignId` is this platform's own primary key -
never present it to a user as "the campaign ID". Answer with `campaignName`; when an id is
actually asked for, give `amazonCampaignId`. The same split applies to every entity below
(`amazonAdGroupId`, `amazonKeywordId`, `amazonTargetId`, `amazonAdId`, `amazonPortfolioId`).
Full convention, including the three exceptions, in
[`platform-notes.md`](platform-notes.md) -> "Naming things in your answer".

**⚠️ "How much budget is left today?" cannot be reliably answered from `dailyBudget`/`currentBudget` alone.** These are configuration values, not a live spend ledger, and can change intraday. Combining them with `get_ads_perf`'s today's-`Spend` doesn't produce a reliable real-time remaining-budget figure either, since that metric is subject to the T+2 processing delay (see PLATFORM_NOTES.md). Tell the user this can't be computed reliably rather than presenting a subtraction as if it were precise.

**More campaign fields (also filterable):**

| Field | Type | Enum |
|---|---|---|
| campaignStartDate | **string — see date note below** | `"20260101"` *or* `"2026-01-01"`; may be `""` |
| campaignEndDate | **string — see date note below** | same; `""` when there is no end date |
| portfolioId | number | **This is the AMAZON portfolio ID, not the internal one** — see "Joining campaigns to portfolios" below |
| aiGroupId | number | — |
| campaignAiFirstOnDate | string | — |
| campaignAiLastOnDate | string | — |
| campaignAiLastOffDate | string | — |

**Audience fields — returned, filterable and sortable:**

| Field | Type | Notes |
|---|---|---|
| audienceId | string | The audience bound to this campaign - either pool, custom AMC or Amazon-built. **`""` means no audience is bound** - the key is always present, never omitted. SP / SB only; on SD it is permanently `""` because SD supports neither audience pool |
| audienceBidPercentage | number | Bid uplift for that audience, `10` = +10%. **`0` does not mean "unbound"** - it is a legitimate value meaning "bound, no uplift". Unbound rows also carry `0`, so this field cannot tell the two apart |

Both can be filtered and sorted on, and **the empty string is a real filter value, not "no
condition"**: `{"audienceId": ""}` selects the campaigns with no audience bound. The
empty-string meaning is stated in the interface contract; that the field is **filterable** is
confirmed against the implementation and not yet written there - so reading the contract alone
would lead you to think it is sort-only.

⚠️ **`{"audienceId": ""}` alone is wrong** - it sweeps in every Sponsored Display campaign,
whose `audienceId` is permanently `""` because SD supports neither audience pool. Always pair
it with a `campaignType` filter.

The **enriched** audience fields - `audienceName`, `audienceType`, `proximityLevel`,
`updateFrequence`, `autoUpdate`, `audienceCount` - are neither filterable nor sortable: MCP
adds them after the list call, so the downstream has never seen them.

**Is this campaign using an audience?** Test `audienceId != ""`. This covers both pools; the row does not say which one (see SKILL.md). Do not test for the key's
presence (it is always there) and do not test `audienceBidPercentage` (0 is ambiguous). When a
row does have an audience, the server also merges that audience's configuration into the same
row - see "`entity: campaign` - audience configuration arrives on its own" in SKILL.md.


**⚠️ Date fields: the JSON *type* is certain, the *format* is not.** **campaign** dates come back as **strings** and a live sample contained **both** `"20260101"` and `"2026-01-01"` - the format is not settled, and an empty string also occurs. **portfolio** dates come back as **numbers** in `YYYYMMDD` (`0` when unset). So the type is predictable per entity and the campaign format is not. **Never normalise by stripping the dashes**, and never assume one campaign row's format applies to the next. If you need to filter on a date field **for one known campaign**, read that campaign's row first and build the filter value in **the same JSON type and shape the response actually gave you** - and pin the filter to that campaign's id so it cannot be reused across a mixed set. **Across campaigns there is no safe server-side date filter on these fields**: page to the end and compare client-side. If you cannot read first, say the filter may not match rather than presenting an empty result as "none found". (`campaignAiFirstOnDate` / `campaignAiLastOnDate` / `campaignAiLastOffDate` are placeholder fields with no settled type at all - do not filter on them.) This is different from the `dateStart`/`dateEnd` request parameters on the other two tools, which use `YYYY-MM-DD`. This tool has no `dateStart`/`dateEnd` params of its own — these are just two ordinary campaign config fields that happen to hold dates — in whatever shape the downstream stored them, and **the shapes can be mixed within one result set**. Because a filter can only be written in one shape, **do not filter a date range on these fields across campaigns**: narrow with other filters, page to the end, then parse both shapes client-side.

**Filter examples** (each is a standalone example of a `filters` value — not one combined call):
```json
{"campaignState": {"in": ["enabled", "paused"]}}
```
```json
{"campaignType": {"in": ["sponsoredProducts"]}}
```
```json
{"dailyBudget": {">=": 10, "<=": 100}}
```
```json
{"campaignName": {"like": "%brand%"}}
```
```json
{"amazonCampaignId": {"in": ["298539385213868"]}}
```
```json
{"amazonCampaignId": {"in": ["298539385213868"]}, "campaignStartDate": {">=": "20260101", "<=": "20260131"}}
```
⚠️ **Note the campaign id in that example - it is not decoration.** Filtering these date
fields is only safe for a campaign whose stored shape you have already seen. Across campaigns
the shapes can be mixed, and a filter written one way silently drops every row stored the
other, so there is no correct cross-campaign form of this filter - page to the end and compare
client-side instead. See the date note below.
```json
{"biddingStrategy": "autoForSales"}
```

### adGroup

| Field | Type | Enum |
|---|---|---|
| adGroupId | number | — (internal ID) |
| amazonAdGroupId | string | Amazon ad group ID — the bridge from `get_ads_perf` / `get_operation_log` back to the internal `adGroupId` |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` — required on writes |
| campaignId | number | **Internal** parent-campaign id. ⚠️ This entity returns **no `amazonCampaignId`** — to report the parent campaign (by name, or by its Amazon id) read the `campaign` entity keyed on this value. Never pass this number off as the Amazon campaign id |
| adGroupName | string | — |
| adGroupState | string | `enabled` / `paused` / `archived` |
| processStatus | string/null | This ad group's enriched delivery status, not its parent's. Selectable but **not filterable or sortable**; empty is unknown |
| defaultBid | string | Local-currency **decimal string**, e.g. `"0.50"` |
| sdBidOptimization | string | `clicks` / `conversions` / `reach` (SD only) |

### target

| Field | Type | Enum |
|---|---|---|
| targetId | number | — (internal ID) |
| amazonTargetId | string | Amazon target ID — the bridge from `get_ads_perf` / `get_operation_log` back to the internal `targetId` |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| adGroupId | number | — |
| campaignId | number | — |
| targetText | string | — |
| targetMatchType | string | Product: `asinSameAs` / `asinExpandedFrom` / `asinCategorySameAs`. Automatic: `queryHighRelMatches` / `queryBroadRelMatches` / `asinSubstituteRelated` / `asinAccessoryRelated`. Audience / SD expressions: `similarProduct` / `exactProduct` / `relatedProduct` / `audienceSameAs`. **Keyword match types (`exact`/`phrase`/`broad`) are NOT values of this entity** - see the note below |
| targetState | string | `enabled` / `paused` / `archived` |
| **targetBid** | string | Current bid, **decimal string** e.g. `"1.20"` — the field to filter on for bid ranges. `>` / `<` are rejected; use `>=` / `<=` |

**Keywords and negatives are separate entities - do not look for them here.** None of `targetMatchType`'s enum values represent a keyword or a negative-targeting variant. Use `entity: "keyword"`, `entity: "negativeKeyword"` or `entity: "negativeTarget"` instead (documented below). Querying `target` with `targetMatchType in ["exact","phrase","broad"]` returns **zero rows** - keywords are not in this entity.

`get_operation_log` still only tells you *when* a negative was added or removed; the three entities below are the queryable current snapshot.

**Careful with `similarProduct` and its siblings.** `EnumTranslator` gives them display labels like *"Auto-Similar Product" / "自动-相似商品"*, but the data layer classifies `similarProduct` / `exactProduct` / `relatedProduct` / `audienceSameAs` as **audience** expressions (Sponsored Display), not automatic targeting. **A display label containing "Auto-" does not mean the write tool's `targetType=auto`** - `targetType=auto` accepts Sponsored Products only, so these values go to `targetType=product`. Only `queryHighRelMatches`, `queryBroadRelMatches`, `asinAccessoryRelated` and `asinSubstituteRelated` map to `auto`.

### productAd

| Field | Type | Enum |
|---|---|---|
| **productAdId** | number | — (internal id — this is the one write tools need) |
| amazonAdId | string | — (Amazon-side id, 15-19 digits — not usable for writes) |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| adGroupId | number | — |
| campaignId | number | — |
| asin | string | — |
| sku | string | — |
| productAdState | string | `enabled` / `paused` / `archived` |

### keyword

| Field | Type | Enum |
|---|---|---|
| **keywordId** | number | — (internal id) |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| amazonKeywordId | string | — (Amazon-side id) |
| adGroupId | number | — |
| campaignId | number | — |
| keywordText | string | — (see the `group` note below) |
| matchType | string | `exact` / `phrase` / `broad` / `group` / `theme` |
| keywordState | string | `enabled` / `paused` / `archived` |
| keywordBid | number | Configured bid — a **number** here, unlike most money fields |
| **keywordCurrentBid** | number | The AI-adjusted current bid (a **number**, unlike most money fields). **`0` is not a bid** — it means no AI override is recorded, and on some stores every keyword reads `0`. **Never use it as the basis for a bid change without checking for `0` first**; fall back to `keywordBid` |

- When `matchType = "group"`, `keywordText` is **not plain text**: it is a JSON string of the
  form `[{"type":"keywordGroupSameAs","value":"..."}]`. Don't show it raw to a customer and
  don't substring-match it as a keyword.
- When `matchType = "theme"` (SB only), `keywordText` is an enum-like value such as
  `KEYWORDS_RELATED_TO_YOUR_LANDING_PAGES`.

### negativeKeyword

| Field | Type | Enum |
|---|---|---|
| **negativeKeywordId** | number | — (internal id) |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| **businessType** | string | `campaign` / `adgroup` — note the lowercase `g`, unlike the `adGroup` entity name |
| tableType | string | `campaign_negative_keyword` / `negative_keyword` — the raw source column `businessType` is derived from |
| amazonKeywordId | string | — |
| adGroupId | number | — (meaningless on campaign-level rows) |
| campaignId | number | — |
| keywordText | string | — |
| matchType | string | `negativeExact` / `negativePhrase` |
| negativeKeywordState | string | `enabled` / `paused` / `archived`. ⚠️ **A value you read is not necessarily one you can write back**: on `sponsoredBrands` rows `paused` can be read but **cannot be set** - that write is rejected for the whole batch. See `edit-ads` |

Campaign-level and ad-group-level negatives live in two different tables, so `businessType`
is part of the row's identity, not decoration.

### negativeTarget

| Field | Type | Enum |
|---|---|---|
| **negativeTargetId** | number | — (internal id) |
| profileId | string | — |
| campaignType | string | `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| amazonTargetId | string | — |
| adGroupId | number | — |
| campaignId | number | — |
| negativeTargetText | string | — (the ASIN, or the brand id) |
| negativeTargetType | string | `asinSameAs` / `asinExpandedFrom` / `asinBrandSameAs` |
| negativeTargetState | string | `enabled` / `paused` / `archived` |

There is no `matchType` and no `businessType` on this entity. `negativeTargetState` (this
entity's status) is unrelated to `negativeTargetStatus`, which is a managed-group on/off
setting.

### Filtering and id types on these three entities

- **Every returned field is filterable** on `keyword`, `negativeKeyword` and `negativeTarget`.
- Internal ids (`keywordId`, `adGroupId`, `campaignId`, ...) come back as **numbers**;
  `profileId` and the Amazon-side ids (`amazonKeywordId`, `amazonTargetId`) are **strings**.
  Write tools want the numeric ids as numbers and `profileId` quoted.
- When reading rows for a write, filter on **that entity's own state field** -
  `keywordState`, `negativeKeywordState`, `negativeTargetState` (there is no generic `state`,
  and an unknown filter field is a hard error) - e.g.
  `{"keywordState": {"in": ["enabled", "paused"]}}`. This surfaces archived rows up front;
  the write side refuses the whole batch for an archived object, and refuses it again if it
  cannot verify the state.

### Joining campaigns to portfolios

`portfolioId` means **different things on different entities**, and joining them naively
matches an unrelated row or nothing at all, with no error:

- `campaign.portfolioId` = the **Amazon** portfolio ID
- `portfolio.portfolioId` = the **internal** ID; its Amazon ID is `portfolio.amazonPortfolioId`

**Correct join:** `campaign.portfolioId` -> `portfolio.amazonPortfolioId`, **and constrain both
queries to the same `profileId`** (Amazon IDs are only unique within a store).

**The two sides also have different JSON types.** `campaign.portfolioId` comes back as a
**number** while `portfolio.amazonPortfolioId` comes back as a **string**, even though they
hold the same id. Convert before comparing - matching `123` against `"123"` fails silently.
(The "Amazon ids are returned as strings" rule is applied by field *name*, and this field is
not named `amazon*`, so it escapes it.)

### Field-name traps across these entities

- The match column is `matchType` on `keyword` / `negativeKeyword`, but **`targetMatchType`**
  on `target`. `negativeTarget` uses `negativeTargetType`. A wrong name fails the downstream
  field whitelist, so it errors rather than silently returning nothing — but it does fail.
- Each of these entities has its own state column name (`keywordState`,
  `negativeKeywordState`, `negativeTargetState`) — there is no generic `state`.

### Performance data lives under a different entity

These three entities are **metadata only**. `get_ads_perf` does not accept `keyword`,
`negativeKeyword` or `negativeTarget` as a `factEntity`:

- **Keyword performance** -> `get_ads_perf(factEntity="target", queryType="keyword")`. In the
  performance tool keywords sit under `target`; in *this* tool they do not (`target` returns
  zero rows for `exact`/`phrase`/`broad`). The two tools split the same objects differently -
  do not carry one tool's entity layout into the other.
- **Keyword x placement, hourly** -> `factEntity="keywordPlacement"` (AMS, SP only, max 7-day
  span).
- **Negative keywords and negative targets have no performance data at all**, and that is
  inherent rather than a gap: a negative blocks traffic, it never serves. What you *can* do is
  list the current negatives here and compare them against wasteful search terms from
  `get_ads_perf(factEntity="searchTerm")`.

### If these ids are headed for a write

An internal id **does not uniquely identify a row on its own.** Several of these entities are
stored across multiple physical tables with independent id spaces, and the write path also
needs the store and the ad type for routing and authorization. So carry the whole set:

| Entity | Fields a write needs alongside the id |
|---|---|
| `campaign` | internal `campaignId` + `profileId` + `campaignType` |
| `adGroup` | internal `adGroupId` + `profileId` + `campaignType` |
| `keyword` | `keywordId` + `profileId` + `campaignType` + **`matchType`** |
| `negativeKeyword` | `negativeKeywordId` + `profileId` + `campaignType` + **`businessType`** |
| `negativeTarget` | `negativeTargetId` + `profileId` + `campaignType` |
| `target`, `productAd` | internal id + `profileId` + `campaignType` |

The bold fields select the physical table; the rest route the call and scope authorization.

So when you read rows that a write will act on, **return the discriminator fields together
with the id, and pass them through verbatim** — don't normalise the case and don't infer
them. See the `sparkx-edit-ads` skill.

### portfolio

| Field | Type | Enum |
|---|---|---|
| portfolioId | number | — **internal** portfolio ID |
| amazonPortfolioId | string | Amazon portfolio ID — this is what `campaign.portfolioId` holds |
| portfolioName | string | — |
| portfolioState | string | `enabled` / `paused` / `archived` |
| portfolioServingStatus | string | `IN_BUDGET` / `OUT_OF_BUDGET` / `PORTFOLIO_ENDED` |
| portfolioStartDate | **see date note below** | Ymd |
| portfolioEndDate | **see date note below** | Ymd |
| **portfolioBudget** | string | Budget amount as a decimal string, e.g. `"20.00"`. **`{">": 0}` is rejected** — strict comparison is not supported. To find "has a budget set", filter `{">=": 0}` and drop the rows equal to 0 yourself |
| portfolioBudgetType | string | `dateRange` / `monthlyRecurring` |

### placement

One row per campaign × placement combination.

| Field | Type | Enum |
|---|---|---|
| campaignId | number | — internal campaign ID |
| amazonCampaignId | string | Amazon campaign ID |
| profileId | string | returned, but **not filterable** |
| campaignType | string | returned, but **not filterable** |
| placement | string | SP: `topOfSearch` / `productPage` / `restOfSearch` / `siteAmazonBusiness`. SB: `topOfSearch` / `home` / `detailPage` / `other` — **four each**, and `topOfSearch` means a different placement on the two |
| placementText | string | Localized label — **only the SP values are translated**; SB rows echo the raw value (`home`, `detailPage`, `other`). Use `enum-i18n.md` for SB |
| multiplier | string | Bid-adjustment **percentage** as a decimal string: `"50.00"` = +50%, `"0.00"` = no adjustment — **not a money amount**. Range 0–900; a stored value outside it (historically `-99`) comes back `null` - report that adjustment as unavailable, never as 0% |
| writeField | string | The `batch_update_ads` field for this placement (`topAdjustment`, `homeAdjustment`, …) — use it rather than mapping the label yourself. Comes back **empty** on SB `topOfSearch`; fall back to the placement-field table in `sparkx-edit-ads`'s `references/write-campaign.md` |

**This and the placement performance entity agree on SB now.** Both return SB's four
placements with their own values (the performance entity used to return three and put the
Home value on its top-of-search row). This entity is still the one to use before a write,
because it carries `writeField`.

### aiGroup (AI Managed Group)

Sourced from a separate backend (`td-api getSaAiGroupList`), aggregated from the SA perspective — richer field set than the ads DB.

**Return fields** (partial — full list is long):
`aiGroupId`, `aiGroupName`, `aiStatus` (`0`=AI never turned on, `1`=AI currently running, `2`=AI turned off), `campaignType`, `targetType` (`1`=Drive growth/推动增长, `2`=Optimize ROAS/保持订单稳定, `3`=Promotion sales boost/活动冲量), `targetAcos`, `aiPersonality` (1-5), `aiPersonalityUpdatedAt`, `profileId`, `profileName`, `countryCode`, `numCampaign`, `numProduct`, `campaignNameSign`, `createTime`, `createBy`, `createUid`, `hasEditAuth`, `isAutoPacing`, `statusOnDate`, `lastStatusOnDate`, `lastStatusOffDate`, `lastOnDays`, `lastOnDaysBegin`, `lastOnDaysEnd`, `totalBudget`, `totalDailyBudget`, `sbStyleNum`, `aiActionSettings`, `aiAutomation`

**`hasAdvice`** (intensity-enabled accounts only) says whether an AI personality recommendation is
waiting for this group — it is the cheap way to find the groups worth calling
`get_sp_sb_ai_personality_recommendation` on, instead of asking group by group.

| Value | Meaning |
|---|---|
| `true` | a recommendation exists **and can be applied directly**: it was computed against the group's current campaigns / ASINs / targetType |
| `false` | none available |
| `null` | the recommendation service was temporarily unavailable — **unknown, not "no"**; say so rather than reporting "no recommendation" |

- **Always `false` for `sponsoredDisplay` groups and for any group whose AI is not running** (`aiStatus != 1`). A `false` on those tells you nothing about whether advice could exist — it is structural.
- **Not a filter.** There is no `hasAdvice` filter; pull the rows and group them client-side.
- **An absent field is "unknown", not `false`, and not proof of a legacy account.** The field is omitted on legacy (non-intensity) accounts **and** whenever the capability check itself fails (`CapabilityDecision.QUERY_FAILED` falls back to the legacy output path). Those two look identical in the response, so read absence as "not enabled, or could not be determined" — never as "this account has no per-action-space intensities".
- `true` is not an authorisation to write. It only says advice exists; applying it is still the separate user-approved step described in the create / edit skills.

Display `aiPersonality` as its numeric value `1`-`5` in customer-facing group and schedule
configuration output. Do not replace it with `aiPersonalityText` or append a personality label.

- **`sbStyleNum`** (int/null): the **count** of SB ad styles in use — e.g. "3" means 3 different SB ad style/formats are running. This can answer "how many SB ad styles is this group using," but **not** "which specific style(s)" (product collection / store spotlight / video, etc) — that breakdown is not exposed by this field and is not otherwise documented in the platform spec. Don't infer or invent a style name from the count.
- **`totalBudget` / `totalDailyBudget`** (number): the **sum of the group's enabled
  campaigns' daily budgets** (i.e. 托管组总预算 / group total budget). These are **read-only
  rollups** here. On the write side, editing the group total **proportionally rescales
  every enabled campaign's daily budget** to the new total (see the create/edit skills) —
  don't treat them as independent editable fields.
- **`aiActionSettings`** (object): transport container for action-space switches and their
  parameters, plus `brandOptimization`. A relevant `xxxStatus` value of `0` means off and `1`
  means on. The container's nesting is not the customer-facing UI taxonomy:
  `brandOptimization` must be presented separately as brand/non-brand/competitor mode, not as an
  action space. Use [`managed-group-display.md`](managed-group-display.md).
- **`aiAutomation`** (object): keyed by rule type (`2`, `4`, `5`, `13`, `17`, `19`, `20`,
  `181`, `182`). Each entry's `status` is the mode: `0` = AI, `1` = Rule/RBA. Pair an
  action-space switch with its mode entry rather than deciding the mode from
  `aiActionSettings` alone. Conversely, do not decide from `aiAutomation` alone either:
  an empty object can mean the paired action spaces are off, that enabled action spaces are
  AI-driven, or both. Read the paired switch first.
- **⚠️ Both objects are returned as a projection of what's *currently effective*, not the
  raw stored record.** Fields belonging to a switch that is off are omitted; rules running
  in AI mode are omitted from `aiAutomation` entirely; rules in Rule mode drop their
  AI-only parameters; and the whole set is first trimmed to what the `campaignType`
  supports. **An absent field means "not in effect", not "unset" and not "write failed".**
  Full rules and the per-ad-type trim table are in SKILL.md — read them before reporting a
  config or verifying a write.
- **RBA rule configuration is readable.** For a rule in Rule mode, `aiAutomation.{ruleType}`
  carries its real conditions, actions, condition items, time periods, and (for dayparting)
  the hour matrix. Confirmed leaves carry a `...Text` companion; unconfirmed leaves are
  passed through raw with no Text — relay those verbatim rather than labelling them. The
  same raw value can mean different things under different rule types, so never carry a
  label across rules. Reading is supported; **writing RBA config is not available through
  any MCP tool**.
- For legacy rules `4`/`5`, `isSelf` is a confirmed three-value scope: `1` = current campaign,
  all ad groups; `3` = current campaign, current ad group only; `2` = the specified
  campaign/ad-group bindings in `campaignAd`. Their `condition[].day` lookback excludes today;
  `condition[].exceptDay` removes the latest dates from inside that lookback. See
  [`automation-rule-reading.md`](automation-rule-reading.md) for the exact date formula and
  reporting shape.
- For rule `13` (budget dayparting), percentage operations and the effective budget ratio are
  different representations. Decrease by `X%` leaves `100%-X%` of the current daily budget;
  increase by `X%` produces `100%+X%`. An unconfigured hour restores 100%. Label a derived matrix
  as a calculated effective budget ratio, not an actual delivery/spend percentage. Fixed-budget
  and amount operations remain currency values. See the rule-specific guide for examples.
- For rule `17` (adjust budget by performance), an action's boundary belongs to that strategy:
  combine its direction/value with `action.switch` and `action.bounds` instead of emitting a
  second standalone budget-boundary section. `autoModifySwitch` and `autoModifySetting` form the
  separate Custom settings group; when enabled, they set the budget to the configured value at
  the next store-local 00:00. They are not part of the execution-time group and do not mean an
  additional amount applied on every evaluation.

For the paired-switch table, standalone-vs-managed capability boundary, condition priority,
and rule-specific business semantics, read [`automation-rule-reading.md`](automation-rule-reading.md)
before explaining the configuration to a user.

**Automation rule <-> action-space mapping** (when a managed-group action space is in
Rule/RBA mode, its readable config appears under `aiAutomation.{ruleType}`):

| action space | ruleType | automation rule template | Notes |
|---|---:|---|---|
| `bidDaypart` / 分时调价 | `2` | Bid dayparting / 分时调价 | Standalone automation supports SP/SB/SD; managed-group action-space support follows the action-space matrix. |
| `targetHarvest` / 定向收割 | `4` | Harvest Keywords / 添加搜索词 | `targetHarvestStatus` special source-exact-negative modes are represented on the action-space switch, not by a different ruleType. |
| `negativeTarget` / 添加否定定向 | `5` | Add Negative Keywords / 添加否定词 | SP/SB standalone automation; SP/SB managed-group word-list settings are read-only through MCP. |
| `budgetDaypart` / 分时预算 | `13` | Budget dayparting / 分时预算 | SP/SB standalone automation. |
| `budgetPerformance` / 按表现调预算 | `17` | Budget rules / 预算规则 | Help Center calls this Budget Rules; action-space docs also call it budget by performance / boost budget. |
| `bidAdPlace` / 广告位调价 | `19` | Placement Rules / 广告位规则 | Help Center says standalone Placement Rules support SP/SB; managed-group action-space use may still be SP-only per the action-space matrix and PRD template filtering. |
| `structPauseCampaign` / 暂停广告活动、广告组 | `20` | Campaign activation/pausing (New) / 开启/暂停广告活动（新版） | Replaces the old pause/enable campaign rules for new setup. |
| `bidPerformance` / 按表现调价 | `181` | Bid by performance / 按表现调价 | Managed-group action-space RBA rule type. |
| `targetPausedAdd` / 定向暂停/补充 | `182` | Target pause/supplement / 定向暂停/补充 | Managed-group action-space RBA rule type. |

`budgetRedistribute` (预算重新分配), `bidAmazonBusiness` (B2B 调价), and
`structPauseProduct` (暂停商品) are action spaces without an `aiAutomation` ruleType in
the current MCP projection.

**Filterable fields — this is a closed whitelist.** Unlike `campaign` (where every returned
field is filterable), `aiGroup` accepts only the fields below. Anything else fails with
`Invalid aiGroup filter 'x': is not supported for aiGroup`, and an out-of-domain enum value
fails too (e.g. `campaignType` must be one of `sponsoredProducts` / `sponsoredBrands` /
`sponsoredDisplay`; `targetType` must be `1`/`2`/`3`). Don't assume a field is filterable
just because it appears in the response.

| Field | Type | Format | Example |
|---|---|---|---|
| aiStatus | int/array | value or `in` | `{"aiStatus": 1}` or `{"aiStatus": {"in": [0, 1, 2]}}` |
| campaignType | array | `in` | `{"campaignType": {"in": ["sponsoredProducts"]}}` |
| aiGroupId | array | `in` | `{"aiGroupId": {"in": [123, 456]}}` |
| aiGroupName | string | `like` | `{"aiGroupName": {"like": "%keyword%"}}` |
| targetType | string/array | `in` or comma | `{"targetType": {"in": ["1", "2"]}}` |
| targetAcos | number | range | `{"targetAcos": {">=": 10, "<=": 50}}` |
| portfolioId | array | `in` | `{"portfolioId": {"in": [123, 456]}}` |

**`targetAcos` uses the same confirmed ×100/percentage scale as performance `ACOS` in `get_ads_perf`** (documented as "Target ACOS (percentage)") — a value of `35` means a 35% target. Don't re-scale the number, but **append `%`** when presenting it: "target ACOS is 35%".

**orderBy supported fields**: `aiGroupName`, `createTime` (default), `createBy`

### aiGroup_schedule (managed-group schedules)

Schedules ("flights") of **one** managed group. Special calling contract — see SKILL.md and [`example-ai-group-schedule.md`](example-ai-group-schedule.md).

**Request contract** (all enforced, all fail-closed):

| Requirement | Error when violated |
|---|---|
| Exactly one authorized `profileId` | `aiGroup_schedule query requires exactly one authorized profileId` |
| `filters` contains `aiGroupId` | `aiGroup_schedule query requires filters.aiGroupId` |
| `filters` contains **nothing else** | `aiGroup_schedule query only supports filters.aiGroupId` |
| `aiGroupId` is a single positive integer (`29123`, `[29123]`, or `{"in": [29123]}`) | invalid-filter error |

Pagination and `orderBy` are ignored; all schedules for the group come back in one response, and the top-level `page`/`pageSize`/`hasNextPage` fields are omitted.

**Return fields** (per schedule row):

| Field | Type | Notes |
|---|---|---|
| `id` | long | Schedule ID (used as the update/delete key by the write tool) |
| `isActive` | boolean | Whether the schedule is **currently inside its effective window** - a not-yet-started or already-ended fixed-date schedule reads `false` while still existing. ⚠️ **Do not echo this into `save_sp_sb_ai_group_schedule`**: there `isActive: false` means *delete*. See the `edit-ai-group` Skill |
| `timeType` | int | `1` = fixed date window, `2` = weekly repeat |
| `startDate` / `endDate` | string | `timeType=1` only |
| `weekDays` | array[int] | `timeType=2` only. `1`=Monday … `7`=Sunday - **the same encoding `save_sp_sb_ai_group_schedule` takes**, so these values can be written back unchanged |
| `optimizeType` | int | `1`=Drive growth/推动增长, `2`=Optimize ROAS/保持订单稳定, `3`=Promotion sales boost/活动冲量, `4`=Drive growth · Budget-utilization priority. **`timeType=2`: inherited from the parent group, read it from the group row instead. For customer output use the selected option in the user's language, not the English enum or category heading.** |
| `acos` | number | Target ACOS. Same inheritance note as `optimizeType` |
| `aiPersonality` | int | 1–5. Same inheritance note as `optimizeType` |
| `aiActionSettings` | object | Per-schedule action-space settings, same shape and same effective-config projection as on the group |
| `aiAutomation` | object | Per-schedule automation rules, keyed by rule type, same projection rules |

**Reporting rule**: for a `timeType=2` (weekly) schedule, do **not** report `optimizeType`/`acos`/`aiPersonality` from the schedule row — they're inherited. Read them from the parent group (`entity: aiGroup`) and say so.

**⚠️ `weekDays` read vs write encodings differ.** The values above (`1`=Monday … `7`=Sunday) are what the **read** side (`get_entity_metadata`) returns. The **write** tool `save_sp_sb_ai_group_schedule` expects a **different** encoding — `0`=Sunday … `6`=Saturday. Do **not** echo a `weekDays` value read here straight into a save-schedule call; translate between the two encodings first.

### sdCategory

Returns a flattened marketplace category tree. Exactly one authorized profile is required.
At least one of `keyword` (case-insensitive name substring), `parentCategoryId` (direct
children only), or `level` (integer >=1) must be supplied. `targetableOnly` is optional but
does not count as narrowing on its own. All filters are single-valued and combine with AND.

| Field | Type | Notes |
|---|---|---|
| categoryId | string | Copy unchanged into `asinCategorySameAs.value` |
| categoryName | string | Display name; use in the matching resolved expression |
| targetable | number | 0 or missing means Amazon will not accept it as a target |
| level | number | 1 is top level |
| parentCategoryId | string | omitted for top-level rows |
| childCount | number | direct children; 0 means leaf |

Pagination and sorting are ignored. More than 500 matches returns the first 500 in tree order
with `meta.truncated=true` and `meta.total`. Narrow the query; never infer unseen ids.

### categoryBrand

Requires exactly one authorized profile and one `filters.categoryId` from `sdCategory`.
Optional `keyword` filters brand names case-insensitively. It returns:

| Field | Type | Notes |
|---|---|---|
| brandId | string | Copy unchanged into `asinBrandSameAs.value` |
| brandName | string | May be absent |
| targetExpression | object | Copyable brand fragment; resolved value falls back to the id when name is absent |

For category + brand targeting, prepend the matching category expression to each brand
target. Multiple brands require multiple targets. A td-api credential error is
`service_unavailable` with `service: td-api`; do not retry or invent ids.

### asin (ASIN product info)

Single query returns **child ASIN + parent ASIN + product line info nested together**. By default only returns non-deleted ASINs (`asinIsDelete=0`).

**Child ASIN fields**: `profileId`, `asin`, `sku`, `parentAsin` (aka virtual_parent_asin), `asinTitle`, `asinBrand`, `asinOpenDate` (SP go-live date), `asinCategoryInfo` (JSON), `asinBsr`, `asinPrice`, `asinInventoryStatus`, `asinSpEligibilityStatus`, `asinSbEligibilityStatus`, `asinSdEligibilityStatus`

**Parent ASIN fields**: `parentAsinTitle`, `parentAsinBrand`, `parentAsinPrice`, `parentAsinBsr`, `parentAsinInventoryStatus`, `parentAsinOpenDate`, `parentAsinCategoryInfo`, `parentAsinSpEligibilityStatus`, `parentAsinSbEligibilityStatus`, `parentAsinSdEligibilityStatus`

**Inventory & available-days fields**: `asinFbaQuantity` (fulfillable), `asinFbmQuantity` (merchant-fulfilled), `asinInventoryDetail` (breakdown object), `asinDayAvailability7` / `14` / `30` / `60` / `90`

The parent dimension mirrors all of these: `parentAsinFbaQuantity`, `parentAsinFbmQuantity`, `parentAsinInventoryDetail`, `parentAsinDayAvailability7` / `14` / `30` / `60` / `90`. Every parent figure is **summed from its child ASINs** — the parent row itself carries no inventory.

⚠️ **Parent available-days is NOT the average of its children's.** The numerator is the summed stock of all child ASINs; the denominator is the **sum of each child's daily sales rate** (`Σ if(daysᵢ > 0, unitsᵢ / daysᵢ, 0)`), not "summed units ÷ a shared day count" — each child has its own number of selling days, so summing first and dividing once would be wrong. Parent therefore computes `floor(summedStock / summedDailyRate)` while a child computes `floor(stock × days / units)`. This matches the report-side `availableDaysAgg` exactly. Example: a parent with 4 children holding 100/100/100/117 units, each selling 3/day, yields `floor(417 / 12) = 34`, while the children individually read 33/33/33/39.

⚠️ Only returned for **Seller profiles with SP-API authorization** — the same rule the product list page applies. Vendor profiles and unauthorized profiles omit this whole group, and `meta.hint` names those profileIds.

⚠️ **A missing field is not zero stock.** Key absent = the profile cannot provide SP-API inventory data. Key present with value `0` = the stock really is zero. Never report a missing field as out-of-stock.

`asinInventoryDetail` shape (each node with children carries its own `total`; the outermost `total` is the overall figure):

```json
{
  "inbound":       { "inboundQuantity": 50, "inboundWorkingQuantity": 10,
                     "inboundShippedQuantity": 30, "inboundReceivingQuantity": 10 },
  "reserved":      { "reservedQuantity": 15, "pendingCustomerOrderQuantity": 8,
                     "pendingTransshipmentQuantity": 5, "fcProcessingQuantity": 2 },
  "totalResearchingQuantity": 3,
  "unfulfillable": { "totalUnfulfillableQuantity": 4, "customerDamagedQuantity": 1,
                     "warehouseDamagedQuantity": 1, "distributorDamagedQuantity": 0,
                     "carrierDamagedQuantity": 0, "defectiveQuantity": 1, "expiredQuantity": 1 },
  "total": 189
}
```

Field names follow the `InventoryDetailField` enum and map one-to-one onto the front-end `FBA_INVENTORY_TREE`, so MCP output can be cross-checked against list-page exports and reports. The product's own labels for each node - use these when you show the breakdown to a user:

| Node | English | 中文 | 日本語 |
|---|---|---|---|
| (top-level `asinFbaQuantity`) | Available | 可售 | 販売可能 |
| `inbound.inboundQuantity` | Inbound | 入库 | 入庫中 |
| `inbound.inboundWorkingQuantity` | Working | 处理中 | 処理中 |
| `inbound.inboundShippedQuantity` | Shipped | 已发货 | 出荷済み |
| `inbound.inboundReceivingQuantity` | Receiving | 正在接收 | 受領中 |
| `reserved.reservedQuantity` | Reserved | 预留 | 引当済み |
| `reserved.pendingCustomerOrderQuantity` | Customer orders | 买家订单 | 顧客注文 |
| `reserved.pendingTransshipmentQuantity` | FC transfer | 运营中心转运 | FC間移動 |
| `reserved.fcProcessingQuantity` | FC processing | 运营中心处理 | FC処理中 |
| `totalResearchingQuantity` | Researching | 调查中 | 調査中 |
| `unfulfillable.totalUnfulfillableQuantity` | Unfulfillable | 不可售 | 販売不可 |
| `unfulfillable.customerDamagedQuantity` | Customer damaged | 因买家导致的残损 | 顧客による破損 |
| `unfulfillable.warehouseDamagedQuantity` | Warehouse damaged | 在库房出现残损 | 倉庫による破損 |
| `unfulfillable.distributorDamagedQuantity` | Distributor damaged | 因分销商导致的残损 | 販売者・ベンダー・ディストリビューターによる破損 |
| `unfulfillable.carrierDamagedQuantity` | Carrier damaged | 因承运人导致的残损 | 配送業者による破損 |
| `unfulfillable.defectiveQuantity` | Defective | 存在瑕疵 | 不良品 |
| `unfulfillable.expiredQuantity` | Expired | 已过期 | 期限切れ |

`inboundQuantity` is a **computed** subtotal (working + shipped + receiving), not a field Amazon returns. `Researching` never lasts more than 60 days, by Amazon's own rule - a non-zero value there is temporary, not stuck. Within each node the **first key is that node's subtotal** (e.g. `inbound.inboundQuantity`) and the rest are its constituents. Fulfillable stock is not repeated here — see the top-level `asinFbaQuantity`.

The outer `total` = fulfillable + inbound + reserved + unfulfillable, **excluding `totalResearchingQuantity`** (per SP-API, `totalQuantity` excludes `researchingQuantity`), matching the product list page. Only first-level nodes are summed — children are the constituents of their subtotal, so adding them again would double-count.

`asinDayAvailability*` = `floor(inventory(fba + reserved) × selling-days-in-window / units-sold-in-window)`, same implementation as the product list page. Its product name is **Product available days (Based on units over the past N days)** / **商品可售天数(基于过去 N 天销量)** / **商品販売可能日数(過去N日間の販売数に基づく)** - the stock in the numerator is deliberately fulfillable **plus** reserved, matching the rule-based-automation definition of "inventory". The look-back window is `[today-N, today-1]` (**excludes today**, since the current day's report is incomplete and marketplaces differ by timezone) and does not follow any date filter in the request. **N is the number of days that actually counted, not the nominal window.** A day drops out of the denominator whether it had no sales or no report at all - so a 7-day window with sales on 3 days divides by 3, and a 7-day window missing two days of reports divides by 5. Zero-sales days therefore never dilute the daily average, and the figure can look healthier than a naive stock/7-day-rate calculation would suggest. Say which window you used when you report it.

- **`null` when there were no sales in the window** (cannot be projected) — this differs from `0` (stock really is zero).
- It is an **ASIN-level** metric (the sales data has no SKU dimension), so SKU rows of the same ASIN repeat the same value, whereas the inventory fields are per SKU.

**Product line fields** (nested array `productLines`, one ASIN may belong to multiple product lines): `productLineParentId`, `productLineParentName`, `productLineChildId` (null = directly attached to parent line, no sub-tag), `productLineChildName`, `productLineCreator`

**Currency**: `asinPrice`/`parentAsinPrice` behave differently for single vs multi-profile queries:

| Scenario | Outer `currency` | Per-row `currency` field | Notes |
|---|---|---|---|
| Single profile | the store's code, **or `USD` if the resolver's lookup failed** | **may also be present** | `asinPrice`/`parentAsinPrice` in local currency either way — a `USD` label here is not a conversion |
| Multi profile | **not present** | present **only when the row has one** (key omitted, not `null`) | Product pricing is not FX-converted. Same rule as the AdsList entities, except those always emit the key and may set it to `null` |

Multi-profile example:
```json
{
  "isError": false,
  "toolName": "get_entity_metadata",
  "data": {
    "rows": [
      {"asin": "B0XX", "asinPrice": 29.99, "currency": "USD", "profileId": 111},
      {"asin": "B0YY", "asinPrice": 2980, "currency": "JPY", "profileId": 222}
    ],
    "rowCount": 2
  },
  "meta": {"effectiveProfileIds": [111, 222], "hint": "Limit conclusions to this query's scope. Missing fields are not zero, and empty results do not prove that no matching business data exists. Do not present partial or paginated results as complete. Distinguish returned facts from analytical inferences; state limitations or query further when evidence is insufficient."}
}
```
Multi-profile does not mean USD here — check each row's `currency` field individually. `asin` was the first entity to behave this way; every AdsList entity now does.

**Filterable fields**:

| Field | Type | Op | Example |
|---|---|---|---|
| asin | string/array | `in` | `{"asin": {"in": ["B0XX", "B0YY"]}}` |
| parentAsin | string/array | `in` | `{"parentAsin": {"in": ["B0PARENT1"]}}` |
| sku | string/array | `in` | `{"sku": {"in": ["SKU001", "SKU002"]}}` |
| asinBrand | string | `like` / `=` | `{"asinBrand": {"like": "%Samsung%"}}` |
| asinTitle | string | `like` | `{"asinTitle": {"like": "%wireless%"}}` |
| asinBsr | number | `>=`, `<=` | `{"asinBsr": {">=": 1, "<=": 1000}}` |
| asinPrice | number | `>=`, `<=` | `{"asinPrice": {">=": 10.0, "<=": 50.0}}`. **`0` means unpopulated, not free** — treat it as null, never report it as the product's price, and remember a `>=` filter silently drops every such row |
| asinInventoryStatus | string/array | `in` | `{"asinInventoryStatus": {"in": ["IN_STOCK"]}}` |
| asinSpEligibilityStatus / asinSbEligibilityStatus / asinSdEligibilityStatus | string | `=` | `{"asinSpEligibilityStatus": "ELIGIBLE"}` |
| asinIsDelete | number | `=` | `{"asinIsDelete": 1}` (to see deleted ones) |
| asinFbaQuantity | number | `>=`, `<=` | `{"asinFbaQuantity": {">=": 10, "<=": 500}}` |
| asinFbmQuantity | number | `>=`, `<=` | `{"asinFbmQuantity": {">=": 10, "<=": 500}}` |
| asinDayAvailability7 / 14 / 30 / 60 / 90 | number | `>=`, `<=` | `{"asinDayAvailability30": {"<=": 14}}` — 14 days of cover or less (restock risk) |
| productLineParentId / productLineChildId | number/array | `in` | `{"productLineParentId": {"in": [101, 102]}}` |
| productLineParentName | string | `like` / `=` | — |

⚠️ Available-days filtering takes **one window per call**: the five windows share the same downstream parameter, so if several are given only the smallest window (most sensitive to sales pace) is applied and the rest are ignored.

⚠️ Inventory-based filters need inventory data. If every profile in the request is a Vendor or unauthorized profile, such a filter returns an empty result rather than silently dropping the condition and returning a page of seemingly-matching rows.

⚠️ Numeric range fields (`asinBsr`, `asinPrice`, `asinFbaQuantity`, `asinFbmQuantity`, `asinDayAvailability*`) accept only `>=`, `<=`, `>` and `<`, where `>` behaves as `>=` and `<` as `<=` (the downstream SQL has closed bounds only) — so `{"<": 14}` matches 14 as well, and the strict-operator **rejection** described in SKILL.md is AdsList-only and does not reach this entity. Write the inclusive operator you actually mean and drop the boundary rows yourself. Any other operator — `=`, `eq`, `in`, `between`, `like` — is **rejected** rather than ignored: silently dropping the condition would return unfiltered rows while you believe the filter applied.

⚠️ A range whose lower bound exceeds its upper bound, e.g. `{"asinDayAvailability30": {">=": 100, "<=": 10}}`, is **rejected**. Such a condition compiles to an always-false predicate and returns zero rows, which is easy to report as a genuine "no products match this criteria" finding. Equal bounds (`{">=": 100, "<=": 100}`) are a valid single-point range and are accepted.

⚠️ Two bounds on the same side, e.g. `{"asinPrice": {">": 5, ">=": 10}}`, are also **rejected**. `>` and `>=` collapse to the same closed bound downstream, so which value survived would depend on map ordering. Keep at most one lower bound and one upper bound.

**orderBy supported fields**: `asin`, `asinTitle`, `asinBrand`, `asinBsr`, `asinPrice`, `parentAsin`, `asinFbaQuantity`, `asinFbmQuantity`, `asinDayAvailability7` / `14` / `30` / `60` / `90`, `parentAsinFbaQuantity`, `parentAsinFbmQuantity`, `parentAsinDayAvailability7` / `14` / `30` / `60` / `90`

⚠️ The inventory-based sort fields are ignored (falling back to no sorting) when no profile in the request can provide inventory data — otherwise the query would reference a column that does not exist.

### automationRule

Queries which automation rule types are enabled for given campaign(s). **Must pass `amazonCampaignId` in filters — this is not optional for this entity.**

This entity is deliberately narrow: it returns an enabled-type summary, not the account's
automation-template library. It does not expose template ID/name, applicable objects,
conditions, actions, frequency, date windows, or campaign-template associations. To read a
managed group's embedded Rule-mode configuration, query `entity: aiGroup` and inspect
`aiAutomation`; that still does not expose standalone template details.

Product inventory rules are SKU/product-scoped and have no rule type in this campaign lookup.
Their absence from `enabledRuleTypes` does not prove that no product inventory rule exists.

**Return fields**: `amazonCampaignId` (long), `enabledRuleTypes` (array[int] — enabled rule type codes), `enabledRuleNames` (array[string] — human-readable rule names, already localized; there is no separate `Text` companion field for this one since the values are already human-readable)

**ruleType enum** (meaning of the ints in `enabledRuleTypes`):

| ruleType | Name | Description |
|---|---|---|
| 2 | Dayparting | Bid dayparting |
| 3 | Budget rules (legacy) | Deprecated legacy budget rule; may still appear on historical campaigns |
| 4 | Harvest Keywords | Auto-harvest search terms into keywords |
| 5 | Harvest Negative Targeting | Auto-add negative targets |
| 6 | Pause Campaign | Auto-pause campaign |
| 7 | Enable Campaign | Auto-enable campaign |
| 8 | Campaign (pause/enable) | Combined pause/enable rule |
| 13 | Budget Day Parting | Budget dayparting |
| 15 | Target | Targeting rule |
| 17 | Budget Performance | Performance-based budget rule |
| 18 | Target (new) | Targeting rule v1 |
| 19 | Placement Rule | Placement adjustment rule |
| 20 | Campaign V2 (pause/enable) | Combined pause/enable rule V2 |
| 181 | Bid Performance | Managed-group bid-by-performance action-space rule |
| 182 | Target Pause/Supplement | Managed-group target pause/supplement action-space rule |

**Filter**: only `amazonCampaignId` (required)
```json
{"amazonCampaignId": {"in": [123456789, 987654321]}}
```
Shorthand also accepted:
```json
{"amazonCampaignId": [123456789, 987654321]}
```

**Note**: `automationRule` does **not** support sort or pagination — results are returned in the **same order as the `amazonCampaignId` list you passed in `filters`** (not sorted by ID value, and unrelated to `orderBy`/`page`, which have no effect here). It also has no outer `currency` field (rule configuration is not a monetary value).

**Full example**:
```json
{
  "profileIds": [4404871489220462],
  "entity": "automationRule",
  "filters": {"amazonCampaignId": {"in": [123456789, 987654321, 555555555]}},
  "userContext": "Which automation rules are enabled on these campaigns"
}
```
Response:
```json
{
  "isError": false,
  "toolName": "get_entity_metadata",
  "data": {
    "rows": [
      {"amazonCampaignId": 123456789, "enabledRuleTypes": [2, 4], "enabledRuleNames": ["Dayparting", "Harvest Keywords"]},
      {"amazonCampaignId": 987654321, "enabledRuleTypes": [], "enabledRuleNames": []},
      {"amazonCampaignId": 555555555, "enabledRuleTypes": [17, 19], "enabledRuleNames": ["Budget Performance", "Placement Rule"]}
    ],
    "rowCount": 3
  },
  "meta": {"effectiveProfileIds": [4404871489220462], "hint": "Limit conclusions to this query's scope. Missing fields are not zero, and empty results do not prove that no matching business data exists. Do not present partial or paginated results as complete. Distinguish returned facts from analytical inferences; state limitations or query further when evidence is insufficient."}
}
```

---

**Enum i18n**: When presenting enum values to the user or translating between API values and display labels, consult [`enum-i18n.md`](enum-i18n.md) for the complete ZH/EN/JA mapping of all enum fields documented above.
