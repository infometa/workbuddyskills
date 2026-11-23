# `create_sp_ad_group` - existing SP campaigns

Use this tool only to add ad groups to existing Sponsored Products campaigns. It shares the
`amazon_sa_campaign_create:write` scope with campaign creation, but its execution and recovery
semantics are different.

## Request and limits

The request has one positive `profileId` and `adGroups` with 1-10 items. Every item requires:

- `campaignId`: the campaign's **internal** id from `get_entity_metadata(entity='campaign')`;
  never use `amazonCampaignId`.
- `name`: non-blank, at most 255 characters, unique case-sensitively within the campaign.
- `defaultBid`: positive, at most two decimals, at or above the marketplace SP minimum; JP
  requires an integer. When the campaign budget is available, the bid cannot exceed it.
- `productAds`: 1-500 items. Seller profiles require the store-owned `(asin, sku)` pair;
  Vendor profiles must omit `sku`. Both reject explicitly ineligible ASINs.
- targeting content matching the campaign: all four `targetBid` groups for automatic
  campaigns; exactly one of `keywords` or `targets` for manual campaigns. If `targetingType`
  is omitted for a manual campaign, the tool infers it from that single populated list.

For automatic campaigns, `targetBid` must contain each of `closeMatch`, `looseMatch`,
`substitutes`, and `complements` exactly once; `keywords` and `targets` must be empty. For
manual campaigns:

- keyword mode accepts only `keywords` and `negativeKeywords`; target mode accepts only
  `targets` and `negativeTargets`;
- keyword text is trimmed, must be at most 80 characters, and cannot contain `/`;
  `matchType` is `exact`, `phrase`, `broad`, or `group` (`theme` is rejected), and `group`
  requires `keywordGroupText`;
- product/category targets reject `categoryName`. Category expressions start with one
  `asinCategorySameAs`; each expression type can occur only once, each target can contain
  at most one `asinBrandSameAs`, and `resolvedExpression` must use the same type sequence;
- duplicate keywords, targets, product ads, and negatives inside an ad group are rejected,
  not silently deduplicated.

Use `state: "paused"` when the user does not want the new ad group to spend immediately.
`archived` is rejected.

Child limits are 1,000 per keywords/targets/negatives list, 500 product ads, and 5,000 child
objects across the call. Keyword and target bids must be positive; automatic `targetBid.bid`
may be negative to close a group but cannot be zero. Category targets use category/brand ids
from `sdCategory` and `categoryBrand`; never invent those ids.

## Preflight and confirmation

Before writing, read the campaign and verify it belongs to the selected profile, is SP, is not
archived, and has the expected automatic/manual targeting mode. Read product metadata for SKU
ownership and eligibility. Show the names, campaign, state, products and targeting to the user
and get approval before the call. The platform tool itself does not issue a confirm token.

## Non-atomic result and recovery

All validation, authorization, campaign and duplicate-name checks finish before the first
write. The actual creates then run sequentially and are **not atomic**:

- `success`: every item was created.
- `partial_success`: at least one item was created and at least one was explicitly rejected.
  Report each result and retry only the failed entries after correcting them.
- `ambiguous_write`: a timeout, 5xx, empty response, or success without an id stopped later
  entries. Do not blindly retry. Query `adGroup` by campaign and name, reconcile created,
  rejected and unattempted indexes, then retry only entries proven absent.

`success: true` means the local platform created the ad group and returned its internal id.
Amazon synchronization is asynchronous. Say "created", not "live on Amazon" or "delivering",
and read the ad groups back before reporting their configuration as verified.
