# Field Reference — `get_operation_log`

## Parameter Details

### entities

Entity types (use carefully):
- `campaign` - campaign
- `adGroup` - ad group
- `target` - targeting/keyword
- `placement` - ad placement
- `portfolio` - portfolio
- `profile` - store
- `aiGroup` - AI managed group
- `productAd` - product ad
- `audience` - audience targeting. ⚠️ **Currently returns 0 rows for every query** (verified in production). Until that is fixed, do not read an empty `audience` result as "no audience changes" — it carries no information at all. Say the audience history could not be read. Also excluded from the default "all entities" scan — must be requested explicitly.

**Important**: entities strictly filters only direct operations on that entity type.
- User says "what operations on this campaign" -> **do NOT** set entities
- User says "only campaign-level operations themselves" -> set `entities: ["campaign"]`
- Default (omitted) queries all entity types **except `audience`**

### resourceIds

Array, each item has `idEntity` (resource type) and `ids` (list of IDs):
```json
[
  {"idEntity": "campaign", "ids": [123456, 789012]},
  {"idEntity": "adGroup", "ids": [111222]}
]
```

**`idEntity` enum values**:
- `campaign` - campaign
- `adGroup` - ad group
- `keyword` - keyword
- `target` - targeting
- `placement` - placement
- `aiGroup` - AI managed group
- `portfolio` - portfolio
- `productLine` - product line

**`idType` rule** (optional, auto-inferred if omitted):
- `amazon` (default): applies to campaign, adGroup, keyword, target, placement, portfolio — these use Amazon's own entity IDs
- `increment`: applies to aiGroup, productLine — these use SparkX AI's internal auto-increment IDs

```json
[{"idEntity": "aiGroup", "idType": "increment", "ids": [501, 502]}]
```

⚠️ **For `campaign` and `adGroup` the ids are Amazon's `amazonCampaignId` / `amazonAdGroupId`, never the internal `campaignId` / `adGroupId`.** Both exist side by side on `get_entity_metadata`'s `campaign` entity, and passing the internal one is **not** an error — the filter simply matches nothing, so the call succeeds and returns rows that were never scoped to your campaigns (or none at all). Resolve the Amazon id first, and **decide which space a value belongs to by the field name it came out of, not by its length** — a single log row carries both at once (`entityId` internal, `amazonCampaignId` Amazon), and id lengths are not a contract. `aiGroup` and `productLine` are the opposite — those take the internal auto-increment id.

**Locating a resource by name first**: this tool takes IDs, not names. If the user describes an object by name (e.g. "campaign SP-T1 MAX-KW-Brands-solder", "keyword 'wireless earbuds' exact match"), first resolve it to an ID via `get_entity_metadata`:
- campaign name -> `entity: "campaign", filters: {"campaignName": {"like": "%...%"}}` -> take **`amazonCampaignId`**
- ad group -> `entity: "adGroup"` -> take **`amazonAdGroupId`**
- keyword text + match type -> `entity: "target", filters: {"targetText": {"like": "%...%"}, "targetMatchType": "exact"}` -> `targetId`
- ASIN -> `entity: "productAd", filters: {"asin": "..."}` -> this returns **internal** `campaignId` / `adGroupId` and an `amazonAdId`. **None of the three is usable in `resourceIds`.** `amazonAdId` has no `idEntity`, and the other two are internal ids, so you need a second hop: feed the internal `campaignId` / `adGroupId` into `entity: "campaign"` / `entity: "adGroup"` and read `amazonCampaignId` / `amazonAdGroupId` off those rows.

Then pass the **Amazon** ID into `resourceIds` — for `aiGroup` and `productLine`, the internal auto-increment id instead (see the warning above).

### campaignTypes

Campaign types:
- `sponsoredProducts` - SP ads
- `sponsoredBrands` - SB ads
- `sponsoredDisplay` - SD ads

### changeBy

Operator filter. Always pass an object with explicit `operator` and `values`:
```json
{"operator": "IN", "values": ["ai", "automation"]}
```
Use `"operator": "NOT_IN"` to exclude values instead.

Valid values:
| User says | Value |
|-----------|-------|
| AI | ai |
| Manual / user | ⚠️ **not a filter value** — `manual` is **rejected** (see below). Pass the person's email, or omit `changeBy` and classify `changedBy` client-side |
| Automation rule | automation |
| AI custom rule | aiCustomRule |
| Budget management | budgetManagement |
| Lock ranking | lockRanking |
| Amazon console | amazonConsole |
| API | api |
| Labels | labels |
| System | system |
| Specific user | user email address (pass as one of the `values`) |

⚠️ **`manual` is rejected outright — it is not a value you can pass.** The server
validates `changeBy.values` up front and throws on `manual` (case-insensitive), **including inside
`IN`, inside `NOT_IN`, and mixed with other values**:

```
Parameter 'changeBy.values' does not support 'manual' (case-insensitive), including IN, NOT_IN,
or mixed values. Specify a concrete operator email or name; to query all operators, omit the
changeBy filter.
```

The reason it was removed: `manual` is a UI-level category, not a real operator. It only ever
matched rows whose `changedBy` was literally `Manual`, while changes made by a named platform
user are recorded under that user's **email** (production, 2026-10: every human budget change in
one store was email-attributed, and `manual` returned none of them). Silently returning that
wrong answer was worse than refusing, so now it refuses.

**To get all human changes**: omit `changeBy` and classify `changedBy` client-side — an email
or `Manual` is a person — or pass the specific user's email as a value.

⚠️ **`Amazon Console` says where, not who.** It means the change came from Amazon's side.
Do not count it as a human change. Two consequences:

- In attribution (weekly / monthly reports), keep it as its own bucket, not inside "a person did
  this".
- Before anything **reverts** such a change, say where it came from, so the user decides
  whether it should be rolled back at all.

### actionType

Action type filter (coarse-grained, 14 categories). Always pass an object with explicit `operator` and `values`:
```json
{"operator": "IN", "values": ["Bid Increased", "Bid Decreased"]}
```

Valid values:
| User says | Value |
|-----------|-------|
| Added / created | Added |
| Archived | Archived |
| Paused | Paused |
| Enabled | Enabled |
| Bid increased | Bid Increased |
| Bid decreased | Bid Decreased |
| Budget increased | Budget Increased |
| Budget decreased | Budget Decreased |
| Placement increased | Placement Increased |
| Placement decreased | Placement Decreased |
| Other field changes | Other Fields Changed |
| Bidding strategy | Bidding Strategy Setting |
| Abnormal status | Abnormal Status Changed |
| Bid adjustment setting | Bid Adjustment Setting |
| AI group setting changed | AI Group Setting changed |

### operationType

Operation type filter (fine-grained). More precise than `actionType`. Always pass an object with explicit `operator` and `values`:
```json
{"operator": "IN", "values": ["Campaign Paused", "DailyBudget Increased"]}
```

⚠️ **Only use the exact string values listed below.** Do not invent or guess values outside this table.

#### Complete operationType values by entity

| Entity | operationType |
|--------|---------------|
| `profile` | `Update Profile DailyBudget` |
| `campaign` | `Campaign Added` |
| `campaign` | `Campaign Archived` |
| `campaign` | `Campaign Enabled` |
| `campaign` | `Campaign Paused` |
| `campaign` | `Campaign Name Changed` |
| `campaign` | `Campaign Out of Budget` |
| `campaign` | `Campaign Ended` |
| `campaign` | `StartDate Changed` |
| `campaign` | `EndDate Changed` |
| `campaign` | `DailyBudget Decreased` |
| `campaign` | `DailyBudget Increased` |
| `campaign` | `offAmazonBudgetControlStrategy Changed` |
| `campaign` | `AudienceSegmentType Changed` |
| `campaign` | `SiteAmazonBusinessAdjustment Decreased` |
| `campaign` | `Bidding Strategy Down Only` |
| `campaign` | `Bidding Strategy Fixed Bids` |
| `campaign` | `Bidding Strategy Up And Down` |
| `campaign` | `Bidding Strategy Rule-based Bidding` |
| `campaign` | `Bid Adjustment None` |
| `campaign` | `Bid Adjustment Automated` |
| `campaign` | `Bid Adjustment Decreased` |
| `campaign` | `Bid Adjustment Increased` |
| `campaign` | `Campaign Label Changed` |
| `adGroup` | `AdGroup Added` |
| `adGroup` | `AdGroup Archived` |
| `adGroup` | `AdGroup Enabled` |
| `adGroup` | `AdGroup Paused` |
| `adGroup` | `AdGroup Name Changed` |
| `adGroup` | `AdGroup Bid Decreased` |
| `adGroup` | `AdGroup Bid Increased` |
| `adGroup` | `Bid Optimization For Conversions` |
| `adGroup` | `Bid Optimization For Page Visits` |
| `adGroup` | `Bid Optimization For Viewable Impressions` |
| `adGroup` | `AdGroup Label Changed` |
| `productAd` | `ASIN Added` |
| `productAd` | `ASIN Archived` |
| `productAd` | `ASIN Enabled` |
| `productAd` | `ASIN Paused` |
| `productAd` | `Asin Ineligible` |
| `productAd` | `Asin Not Buyable` |
| `productAd` | `Asin Out ot Stock` |
| `productAd` | `Asin Not in Buybox` |
| `productAd` | `Asin Missing Decoration` |
| `productAd` | `Asin No Inventory` |
| `productAd` | `Ad Added` |
| `productAd` | `Ad Name Changed` |
| `productAd` | `Ad Enabled` |
| `productAd` | `Ad Paused` |
| `productAd` | `Ad Archived` |
| `target` | `Keyword Group Enabled` |
| `target` | `Keyword Group Paused` |
| `target` | `Keyword Group Added` |
| `target` | `Keyword Group Bid Decreased` |
| `target` | `Keyword Group Bid Increased` |
| `target` | `Keyword Group Archived` |
| `target` | `Theme Targeting Enabled` |
| `target` | `Theme Targeting Paused` |
| `target` | `Theme Targeting Bid Increased` |
| `target` | `Theme Targeting Bid Decreased` |
| `target` | `Theme Targeting Archived` |
| `target` | `Theme Targeting Added` |
| `target` | `Keyword Targeting Added` |
| `target` | `Keyword Targeting Paused` |
| `target` | `Keyword Targeting Enabled` |
| `target` | `Keyword Targeting Archived` |
| `target` | `Keyword Targeting Bid Increased` |
| `target` | `Keyword Targeting Bid Decreased` |
| `target` | `Product Targeting Added` |
| `target` | `Product Targeting Paused` |
| `target` | `Product Targeting Enabled` |
| `target` | `Product Targeting Archived` |
| `target` | `Product Targeting Bid Increased` |
| `target` | `Product Targeting Bid Decreased` |
| `target` | `Category Targeting Added` |
| `target` | `Category Targeting Paused` |
| `target` | `Category Targeting Enabled` |
| `target` | `Category Targeting Archived` |
| `target` | `Category Targeting Bid Increased` |
| `target` | `Category Targeting Bid Decreased` |
| `target` | `Automatic Targeting Added` |
| `target` | `Automatic Targeting Paused` |
| `target` | `Automatic Targeting Enabled` |
| `target` | `Automatic Targeting Archived` |
| `target` | `Automatic Targeting Bid Increased` |
| `target` | `Automatic Targeting Bid Decreased` |
| `target` | `Audience Targeting Added` |
| `target` | `Audience Targeting Paused` |
| `target` | `Audience Targeting Enabled` |
| `target` | `Audience Targeting Archived` |
| `target` | `Audience Targeting Bid Increased` |
| `target` | `Audience Targeting Bid Decreased` |
| `target` | `Negative Keyword Added` |
| `target` | `Negative Keyword Paused` |
| `target` | `Negative Keyword Enabled` |
| `target` | `Negative Keyword Archived` |
| `target` | `Negative Asin Added` |
| `target` | `Negative Asin Enabled` |
| `target` | `Negative Asin Paused` |
| `target` | `Negative Asin Archived` |
| `target` | `Negative Brand Added` |
| `target` | `Negative Brand Enabled` |
| `target` | `Negative Brand Paused` |
| `target` | `Negative Brand Archived` |
| `target` | `Negative Product Added` |
| `target` | `AudienceId Changed` |
| `target` | `AudienceBidPercentage Changed` |
| `placement` | `OTHERADJUSTMENT Decreased` |
| `placement` | `OTHERADJUSTMENT Increased` |
| `placement` | `DETAILPAGEADJUSTMENT Increased` |
| `placement` | `DETAILPAGEADJUSTMENT Decreased` |
| `placement` | `HOMEADJUSTMENT Increased` |
| `placement` | `HOMEADJUSTMENT Decreased` |
| `placement` | `TopSearchAdjustment Decreased` |
| `placement` | `TopSearchAdjustment Increased` |
| `placement` | `ProductPageAdjustment Decreased` |
| `placement` | `ProductPageAdjustment Increased` |
| `placement` | `RestOfSearchAdjustment Decreased` |
| `placement` | `RestOfSearchAdjustment Increased` |
| `portfolio` | `Portfolio Changed` |
| `portfolio` | `Portfolio Name Changed` |
| `portfolio` | `Portfolio EndDate Changed` |
| `portfolio` | `Portfolio StartDate Changed` |
| `portfolio` | `Budget Cap Decreased` |
| `portfolio` | `Budget Cap Increased` |
| `portfolio` | `Budget Type Changed` |
| `portfolio` | `Portfolio Ended` |
| `portfolio` | `Portfolio Out of Budget` |
| `portfolio` | `Portfolio Added` |

| `aiGroup` | `Turn on Managed group AI` |
| `aiGroup` | `Turn off Managed group AI` |
| `aiGroup` | `Set managed group name` |
| `aiGroup` | `Change managed group name` |
| `aiGroup` | `Set the objective of managed group AI` |
| `aiGroup` | `Set the target value of managed group AI` |
| `aiGroup` | `Set the AI personality` |
| `aiGroup` | `Enable campaign name tag` |
| `aiGroup` | `Added campaigns to the managed group` |
| `aiGroup` | `Merged the current managed group into another managed group` |
| `aiGroup` | `Enable budget dayparting (optimization method: AI)` |
| `aiGroup` | `Enable budget dayparting (optimization method: rule)` |
| `aiGroup` | `Disable budget dayparting` |
| `aiGroup` | `Enable placement multiplier (optimization method: AI)` |
| `aiGroup` | `Disable placement multiplier` |
| `aiGroup` | `Enable bid dayparting (optimization method: AI)` |
| `aiGroup` | `Disable bid dayparting` |
| `aiGroup` | `Enable adjustment base bids base on performance (optimization method: AI)` |
| `aiGroup` | `Disable adjustment base bids base on performance` |
| `aiGroup` | `Enable target harvesting (optimization method: AI)` |
| `aiGroup` | `Disable target harvesting` |
| `aiGroup` | `Enable adding negative targets (optimization method: AI)` |
| `aiGroup` | `Disable adding negative targets` |
| `aiGroup` | `Enable pause targets (optimization method: AI)` |
| `aiGroup` | `Disable pause targets` |
| `aiGroup` | `Enabled budget reallocation` |
| `aiGroup` | `Disabled budget reallocation` |
| `aiGroup` | `Enabled bidding range` |
| `aiGroup` | `Disabled bidding range` |
| `aiGroup` | `Set the coefficient` |

> **Rule variants:** only the budget-dayparting Rule string above is confirmed in a
> production log (2026-08-18). Do not construct or submit inferred Rule strings for
> other action spaces. Query with the broader `actionType` (or without an
> `operationType` filter), inspect the exact returned value, and only then reuse that
> observed string in a narrower follow-up query. `budgetRedistribute` and
> `bidAmazonBusiness` are `noRule` capabilities and have no Rule variant.

> **aiGroup action-space changeField values**: the `changeField` is the action-space
> switch name (e.g. `budgetDaypartStatus`, `bidAdPlaceStatus`). The `newValue`/
> `previousValue` encode the state:
>
> | Value | Meaning | operationType suffix |
> |---|---|---|
> | `0` | Off / disabled | "Disable ..." |
> | `1` | On, AI mode | "Enable ... (optimization method: AI)" |
> | `3` | On, Rule mode | Confirmed for budget dayparting; do not infer an exact `operationType` for other action spaces |
>
> Value `3` has been observed for budget dayparting. Treat it as a returned display
> value, not a direct write value, and do not generalize it to an unobserved action
> space without evidence from that action space's returned rows.

Use `actionType` for broad filtering; use `operationType` when you need precise control over specific entity+action combinations.

### targetTypes

Targeting type filter. Narrows target entity operations to specific targeting types.

Valid values:
- `product` - product targeting
- `keyword` - keyword targeting
- `automatic` - automatic targeting
- `category` - category targeting
- `theme` - theme targeting
- `keywordGroup` - keyword group
- `negativeKeyword` - negative keyword
- `negativeAsin` - negative ASIN
- `negativeBrand` - negative brand

### placementTypes

Placement type filter. Narrows placement operations to specific placement types.

**Complete enum — these 7 values**: `detailPageAdjustment`, `homeAdjustment`, `otherAdjustment`, `productPageAdjustment`, `restOfSearchAdjustment`, `siteAmazonBusinessAdjustment`, `topSearchAdjustment`. Do not guess at additional values or try to infer more from `changeField`.

⚠️ **These are the change log's own names and they do not all line up with the write tool's.** The log has `topSearchAdjustment`, which matches neither SP's `topAdjustment` nor SB's `topOfSearchAdjustment`. Use this list when filtering the log, and the placement-field table in `sparkx-edit-ads`'s `references/write-campaign.md` when writing — do not map a name from one onto the other.

### ChangeLogVO Field Reference

| Field | Type | Description |
|---|---|---|
| entity | string | Entity type: `campaign`/`adGroup`/`target`/`aiGroup`/`portfolio`/`placement`/`profile`/`productAd` |
| entityName | string | Entity display name |
| amazonEntityId | long | Amazon-side entity ID |
| entityId | long | SparkX AI-side entity ID |
| operationType | string | Fine-grained operation type (e.g. `DailyBudget Increased`) |
| profileId | long | Profile ID |
| aiGroupName | string | AI managed group name (present on aiGroup-related logs) |
| amazonCampaignId | long | Amazon campaign ID — **this is the id to report** when the user asks for one; it is not the internal `campaignId` the write tools take |
| campaignName | string | Campaign name — **answer with this** unless an id was explicitly asked for (see `platform-notes.md` -> "Naming things in your answer") |
| campaignType | string | Campaign type |
| amazonAdGroupId | long | Amazon ad group ID (null if not applicable) |
| adGroupName | string | Ad group name (null if not applicable) |
| changeField | string | Which field changed |
| previousValue | string | Value before the change |
| newValue | string | Value after the change |
| countryCode | string | Country code |
| **currencyCode** | string | **Currency of this row's monetary change** (e.g. `"USD"`/`"JPY"`), mapped from `countryCode`. Always local currency — there is no cross-profile USD conversion for logs |
| createdDate | string | Operation timestamp, `yyyy-MM-dd HH:mm:ss`. **⚠️ Timezone is not fixed** — SP/SB `aiGroup` rows are UTC, SD `aiGroup` rows use the downstream DB's timezone (undocumented, so they cannot be labelled at all); `campaign`/`adGroup`/`target`/`placement` rows are **store-local when you pass one `profileId`** and **UTC when you pass several**. Verified 2026-08 on a US (`America/Los_Angeles`) profile: the same pause record returned `2026-08-24 00:01:06` for one profileId and `2026-08-24 07:01:06` for two. Always label the zone, never merge single- and multi-profile results, and remember a mixed-entity response can contain both clocks in one time-sorted list (so it is not reliably chronological). See SKILL.md → "createdDate Timezone" |
| changedBy | string | Who made the change, as a **display value** - `AI`, `Manual`, `Automation`, `AI-Custom Rule`, `Budget Management`, `Lock Ranking`, `Amazon Console`, `API`, `Labels`, `System` - or a platform user's **email**. These are not the lowercase `changeBy` filter values; see the `changeBy` note above |
| aiGroupScheduleId | long | Schedule ID (present on aiGroup-related logs) |
| operationSource | string | Which surface the change was made from (`MCP`, `PAGE`, `FEISHU`, and older values such as `platform` / `automation`). **Read-only and not filterable**; `null` means not recorded, not "manual" - see the section below |

---

### `operationSource` - where the change was made from

This field says which surface an operation came from: the web console, MCP, Feishu, and so on.
It is useful, but it has three properties that make a naive reading wrong.

**1. It is read-only. There is no filter for it.** `get_operation_log` takes no source
parameter, so "show me only the changes made through MCP" cannot be pushed down - pull the rows
and group them client-side, and say that is what you did.

**2. MCP's own writes are tagged, including managed groups.** Every write path this server
offers stamps the source on the request, so a change you made through MCP comes back as `MCP` -
advertising entities and AI managed groups alike, on create, edit, batch, **delete** (the campaign
release / migration rows) and **schedule save** (add, update and delete). Verified end to end
against the operation log.

> The delete and schedule paths were the last two to be covered; rows written by those paths
> before that carry the downstream default `PAGE`, not `MCP`. So a historical `PAGE` on a
> managed-group delete or schedule row is not proof a person did it in the console.

**But `null` still means "not recorded", not "done by a human".** Rows written before the field
existed carry `null`, and so does anything whose upstream did not supply a source. Treat `null`
as no information: don't read it as manual, as console, or as "not MCP". If the answer depends
on who made a change, use `changedBy` - that field is populated far more consistently - and use
`operationSource` to say *where from* once you already know *what* happened.

**3. The values are not a closed set.** The field carries whatever the downstream stored, and
two vocabularies share it: the older `platform` / `amazon` / `automation` / `recommendations`
(*where* the change originated) and the newer `MCP` / `PAGE` / `FEISHU` (*which surface inside
the platform*). A row reading `automation` tells you a rule made the change but not which
surface configured it. Report the value you got; don't map it onto a list of your own, and
don't assume a value you haven't seen is impossible.

**What it is good for**, within those limits: saying which surface a change came from once
you have the row, and separating rule-driven rows from human ones alongside `changedBy`.
**What it is not good for**: filtering (there is no parameter), counting usage across a
period (older rows carry no source, so any total is a floor), or any claim that rests on
`null` meaning something.

**Enum i18n**: When presenting enum values to the user or translating between API values and display labels, consult [`enum-i18n.md`](enum-i18n.md) for the complete ZH/EN/JA mapping of all enum fields documented above.
