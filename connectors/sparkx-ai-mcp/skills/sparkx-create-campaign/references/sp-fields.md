# `create_sp_sb_campaign` - SP field reference

Request shape:

```
{
  "profileId": 4404871489220462,
  "campaigns": [ { ...campaign..., "adGroups": [ { ...adGroup..., <child lists> } ] } ]
}
```

`profileId` is top-level and applies to every campaign in the call. One profile per call.

## The console this maps to

The user is describing the "新建广告活动 / Create Campaign" page. Speak in its labels, not in
field names, and read requests through this table - several field names do **not** mean what
they sound like.

| Console (ZH) | Console (EN) | Field |
|---|---|---|
| 广告活动名称 | Campaign name | `name` |
| 广告组合 | Portfolios | `portfolioId` |
| 站点 | Sites | `siteRestrictions` — see below |
| 开始日期 / 结束日期 | Start date / End date | `startDate` / `endDate` |
| 每日预算 | Daily budget | `budget` |
| 投放类型 | Targeting | `targetingType` (`auto` = 自动, `manual` = 手动) |
| 竞价策略 | Campaign bidding strategy | `biddingStrategy` — see below |
| 按展示位置调整出价 | Adjust bids by placement | `topAdjustment` / `productPageAdjustment` / `restOfSearchAdjustment` |
| 进一步提高亚马逊企业购各展示位置的出价 → 出价调整比例 | Further increase bids across placements on Amazon Business → Bid adjustment percentage | `siteAmazonBusinessAdjustment` |
| 按受众调整出价 → 选择受众类型 | Adjust bids by audience → Select audience type | `audienceSegmentType` — see below |
| 按受众调整出价 → 选择受众 | Select the audience | `audienceId` |
| 按受众调整出价 → 出价调整比例 | Bid adjustment percentage | `audienceBidPercentage` |
| 站外广告策略 | Off-site Ads Strategy | `offAmazonBudgetControlStrategy` — see below |
| 广告组名称 | Ad group name | ad group `name` |
| 商品 | Products | `productAds` |
| 自动定向 → 按目标组设置出价 | Automatic targeting → Set bids by targets group | `targetBid` |
| 否定词 | Negative Keyword Targets | `negativeKeywords` |
| 否定商品 | Negative Product Targets | `negativeTargets` |

### ⚠️ `biddingStrategy`: `manual` means **Fixed bids**, not "manual targeting"

| Value | Console (EN) | Console (ZH) |
|---|---|---|
| `legacyForSales` | Dynamic bids - **down only** | 动态竞价-仅降低 |
| `autoForSales` | Dynamic bids - **up and down** | 动态竞价-提高和降低 |
| `manual` | **Fixed bids** | 固定竞价 |

`manual` here is the *bidding* strategy and has nothing to do with `targetingType: "manual"`.
A user asking for 手动投放 wants `targetingType`, and may well want dynamic bidding with it.
Asking for 固定竞价 is what selects `biddingStrategy: "manual"`. Confusing the two silently
sets the wrong thing and the call still succeeds.

`ruleBased` exists on the **edit** tool but is **not accepted at creation** - create with one
of the three above and switch afterwards if the user wants rule-based bidding.

### `siteRestrictions` is the 站点 / Sites radio

| Console choice | Send |
|---|---|
| 亚马逊及其他网站 / Amazon and beyond | omit `siteRestrictions` |
| 亚马逊企业购 / Amazon Business | `siteRestrictions: "AMAZON_BUSINESS"` |

Choosing Amazon Business is what makes `siteAmazonBusinessAdjustment`, every `audience*`
field and `offAmazonBudgetControlStrategy` illegal — in the console those controls belong to
the "Amazon and beyond" branch and disappear.

### `offAmazonBudgetControlStrategy` is 站外广告策略 / Off-site Ads Strategy

| Value | Console (EN) | Console (ZH) |
|---|---|---|
| `MINIMIZE_SPEND` (default) | Limit off-Amazon spend | 限制在亚马逊站外的花费 |
| `MAXIMIZE_REACH` | Increase reach | 扩大受众触达 |

The console marks this **required** and pre-selects 限制在亚马逊站外的花费, which is why the
tool defaults to `MINIMIZE_SPEND`.

### `audienceSegmentType` is 选择受众类型 / Select audience type

| Value | Console (EN) | Console (ZH) |
|---|---|---|
| `SPONSORED_ADS_AMC` (default) | Increase bids on a custom audience created in AMC | 提高针对自定义 AMC 人群的竞价 |
| `BEHAVIOR_DYNAMIC` | Increase bids for audiences built by Amazon | 提高针对亚马逊人群的竞价 |

`BEHAVIOR_DYNAMIC` reads like a behavioural setting; it is simply Amazon-built audiences.

## Campaign

| Field | Type | Required | Notes |
|---|---|---|---|
| `campaignType` | string | yes | `sponsoredProducts`. `sponsoredBrands` is refused on this server; `sponsoredDisplay` has its own (unregistered) tool |
| `name` | string | yes | max **128** characters. Must be unique for the profile - a clash returns "Duplicate name" |
| `budget` | number | yes | daily budget, local currency. **Whole numbers only on JP** |
| `startDate` | string | yes | `yyyyMMdd`. Must not be earlier than the shop's current date, evaluated in **the shop's own timezone** - not yours |
| `endDate` | string | no | `yyyyMMdd`, on or after `startDate` |
| `targetingType` | enum | yes | `auto` / `manual` - decides which child lists are legal |
| `biddingStrategy` | enum | **yes** | `legacyForSales` / `autoForSales` / `manual`. **No default** - omitting it stores an empty strategy |
| `state` | enum | no | `enabled` / `paused`. Use `paused` while testing |
| `portfolioId` | long | no | **the `amazonPortfolioId`** from `get_entity_metadata(entity='portfolio')` — **not** that response's own `portfolioId`, which is the platform-internal one. That field arrives as a **string**; send it here as a **number**. Verified against this shop's portfolios; a wrong or foreign id is rejected |
| `aiGroupId` | long | no | an existing managed group. A bad value returns "get aiGroupName failed" |
| `adGroups` | array | yes | non-empty, at most **50** |

### SP placement adjustments

| Field | Console label | Notes |
|---|---|---|
| `topAdjustment` | Top of search (first page) | integer percentage **0-900** |
| `productPageAdjustment` | Product pages | integer percentage 0-900 |
| `restOfSearchAdjustment` | Rest of search | integer percentage 0-900 |
| `siteAmazonBusinessAdjustment` | — | integer percentage 0-900; SP-only; **illegal together with `siteRestrictions`** |

> ⚠️ The **edit** tool (`batch_update_ads` + `updatePlacementBid`) uses the same three SP
> names, so placement fields carry over between creating and editing an SP campaign. They do
> **not** carry over for SB, which is one more reason not to reuse an SP request shape for a
> Brands campaign.

### Off-Amazon and site restrictions

| Field | Notes |
|---|---|
| `offAmazonBudgetControlStrategy` | `MINIMIZE_SPEND` (default, matching the console) or `MAXIMIZE_REACH`. **Not defaulted when `siteRestrictions` is set** |
| `siteRestrictions` | only `AMAZON_BUSINESS`; only on **US / CA / MX / UK / DE / FR / IT / ES / IN / JP** |

Setting `siteRestrictions` makes `siteAmazonBusinessAdjustment`, **all `audience*` fields**
and `offAmazonBudgetControlStrategy` illegal - omit them all.

### Audience

| Field | Type | Notes |
|---|---|---|
| `audienceId` | string | **verified** - the server checks it belongs to this `profileId` + `campaignType` + `audienceSegmentType` before creating anything |
| `audienceBidPercentage` | string | an integer 0-900 **sent as a string** |
| `audienceSegmentType` | enum | `SPONSORED_ADS_AMC` / `BEHAVIOR_DYNAMIC`. **Required whenever `audienceId` is set**, and must come from the **same** `amcAudience` row as the `audienceId` |

**All three together, or none** - and all three are enforced. A mismatched pool, an id missing
from the list, or a failed lookup **rejects the whole request**, not just that campaign. Omit
all three to create without an audience; there is no separate off switch here. See SKILL.md.

## Ad group

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | max **255** characters |
| `defaultBid` | number | yes | must not exceed the campaign budget |
| `targetingType` | enum | no | `keyword` / `target`. Must be `target` on an auto campaign. On a manual campaign, if omitted it is inferred: only keywords -> keyword, only targets -> target; both or neither is rejected |
| `state` | enum | no | `enabled` / `paused` |
| `productAds` | array | **yes for SP** | non-empty |
| `targetBid` | array | auto only | all four groups - see below |
| `keywords` | array | manual `keyword` only | |
| `targets` | array | manual `target` only | |
| `negativeKeywords` | array | auto, or manual `keyword` | |
| `negativeTargets` | array | auto, or manual `target` | |

Every child list is capped at **1000** items, and all child items across the whole call at
**5000**.

## `productAds`

| Field | Type | Required | Notes |
|---|---|---|---|
| `asin` | string | yes | real ASIN format: `B` + 9 alphanumerics, or 9 digits + X/digit. Placeholders are rejected |
| `sku` | string | Seller: **yes**; Vendor: **must be omitted** | Seller: verified as the SKU actually bound to that ASIN in this shop. Vendor: a non-blank sku rejects the whole call; a blank one is treated as omitted |

## `targetBid` (auto campaigns)

| Field | Type | Required | Notes |
|---|---|---|---|
| `targetGroup` | enum | yes | `closeMatch` / `looseMatch` / `substitutes` / `complements` |
| `bid` | number | yes | **negative = disable this group** |
| `state` | enum | no | |

**All four groups must be present**, each at most once. Omitting a group is a validation
error; disabling one is a negative bid.

## `keywords`

| Field | Type | Required | Notes |
|---|---|---|---|
| `keywordText` | string | yes | max **80** characters, must not contain `/` |
| `matchType` | enum | yes | includes `group`; see below |
| `bid` | number | yes | must not exceed the campaign budget |
| `keywordGroupText` | string | when `matchType` is `group` | **required in that case** - a missing value fails the batch |
| `state` | enum | no | |

Unique per (`keywordText`, `matchType`) within an ad group. A duplicate is **rejected**, not
de-duplicated.

## `targets`

| Field | Type | Required | Notes |
|---|---|---|---|
| `expression` | array | one-of | with `resolvedExpression`, **same number of elements**; starts with `asinCategorySameAs`, each type at most once |
| `resolvedExpression` | array | with `expression` | required whenever `expression` is used; same type sequence as `expression` |
| `asin` | string | one-of | real ASIN format |
| `categoryName` | string | - | **rejected for sponsoredProducts**; use `expression` + `resolvedExpression` instead |
| `type` | string | **yes with `asin`** | `asinSameAs` / `asinExpandedFrom`; missing is rejected. Not used with `expression` |
| `bid` | number | yes | |

**Exactly one** of `expression` / `asin` - the tool checks this and **rejects** an entry
carrying more than one. `categoryName` is **NOT supported for sponsoredProducts** (the
downstream would store the category NAME instead of the category ID); use `expression` with
`resolvedExpression`.

For category targeting, `expression` must start with the category item `asinCategorySameAs`;
brand / price / rating / prime refinements follow it and each type may appear at most once per
target. `asinCategorySameAs` / `asinBrandSameAs` values must be strings (ID in `expression`,
display name in `resolvedExpression`), and `resolvedExpression` must list the same types in
the same order. A target holds at most ONE brand: for several brands create several targets,
each starting with the same category item. Category IDs come from
`get_entity_metadata(entity='sdCategory', filters.keyword=<name>, filters.targetableOnly=true)`
and brand IDs from `get_entity_metadata(entity='categoryBrand', filters.categoryId=<categoryId>)`;
never invent IDs.

## `negativeKeywords`

| Field | Type | Required |
|---|---|---|
| `keywordText` | string | yes |
| `matchType` | enum | yes |
| `state` | enum | no |

## `negativeTargets`

| Field | Type | Required | Notes |
|---|---|---|---|
| `asin` | string | one-of | |
| `brand` | string | one-of | |
| `expression` | array | one-of | with `resolvedExpression` |
| `name` | string | no | |
| `state` | enum | no | |

**Exactly one** of `asin` / `brand` / `expression`.

## Errors worth recognising

| Message | Means |
|---|---|
| `Duplicate name` | a campaign or ad group name already exists for this profile |
| `get aiGroupName failed` | `aiGroupId` does not reference an existing managed group |
| catalog lookup failed | **retry** - do not substitute a different ASIN |
| campaign type not enabled | that type is off on this server; do **not** retry it |
