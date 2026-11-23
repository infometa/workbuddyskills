# Route matrix

25 registered `entity` + `action` routes. An unregistered pair throws
`Batch update route is not implemented` (the message lists what is registered).

`entity` values that have routes here: `campaign`, `keyword`, `target`, `productAd`,
`negativeKeyword`, `negativeTarget`, `portfolio`, `adGroup`.
`action` values: `create`, `updateStatus`, `updateBudget`, `updateBiddingStrategy`,
`updateAudienceBid`, `updatePlacementBid`, `updateBid`, `addPortfolio`,
`removePortfolio`, `updateDates`, `archive`, `copy`.

## The payload array name differs per route

This is the most common build error. A correctly-spelled but wrong-route field is
**silently discarded**, and the route then fails with "required array missing" - an error
that points at the field you thought you sent.

| # | entity + action | Payload lives in | Ad types | Confirm |
|---|---|---|---|---|
| 1 | `campaign` + `updateBudget` | `request.data` | SP / SB / SD | always |
| 2 | `campaign` + `updateStatus` | `request.data` | SP / SB / SD | if `archived` |
| 3 | `campaign` + `updateBiddingStrategy` | `request.data` | **SP only** | - |
| 4 | `negativeKeyword` + `create` | `request.data` | **SP only** | - |
| 5 | `negativeKeyword` + `updateStatus` | `request.updates` | SP / SB / SD — **SB rejects `paused`** | if `archived` |
| 6 | `negativeKeyword` + `copy` | `request.businessType` + `request.target` | SP / SB / SD | - |
| 7 | `keyword` + `create` | `request.data` | SP / SB | - |
| 8 | `keyword` + `updateStatus` | `request.data` | any | if `archived` |
| 9 | `keyword` + `updateBid` | `request.data` | any | always |
| 10 | `target` + `create` | `request.data` | SP / SB | - |
| 11 | `target` + `updateStatus` | `request.data` + `request.targetType` | product: SP/SB/SD; auto: **SP only** | if `archived` |
| 12 | `target` + `updateBid` | `request.data` + `request.targetType` | product: SP/SB/SD; auto: **SP only** | always |
| 13 | `productAd` + `create` | `request.campaigns` + `request.asins` + `request.profileType` | SP / SD | - |
| 14 | `productAd` + `updateStatus` | `request.updates` | SP / SD | - |
| 15 | `productAd` + `archive` | `request.updates` | SP / SD | always |
| 16 | `negativeTarget` + `create` | `request.businessType` + `request.target` | SP / SB | - |
| 17 | `negativeTarget` + `updateStatus` | `request.data` | SP / SB | if `archived` |
| 18 | `negativeTarget` + `copy` | `request.businessType` + `request.target` | SP / SB | - |
| 19 | `campaign` + `updateAudienceBid` | `request.data` | SP / SB, one profile and campaignType | always |
| 20 | `campaign` + `updatePlacementBid` | `request.data` | SP / SB, one campaignType and one verified marketplace | always |
| 21 | `campaign` + `addPortfolio` | `request.data` | SP / SB / SD | - |
| 22 | `campaign` + `removePortfolio` | `request.data` | SP / SB / SD | - |
| 23 | `portfolio` + `updateBudget` | `request.data` | portfolio | always |
| 24 | `portfolio` + `updateDates` | `request.data` | portfolio | - |
| 25 | `adGroup` + `updateStatus` | `request.data` | SP / SB / SD | - |

`request.profileIds` is required on **every** route.

## Two easy-to-confuse pairs

- **`businessType` placement.** `negativeKeyword + updateStatus` takes it **per item**
  (`updates[].businessType`). `negativeKeyword + copy` and both `negativeTarget`
  create/copy routes take it **top-level** (`request.businessType`).
- **`negativeTarget` `create` and `copy` are the same operation.** Same implementation,
  same downstream endpoint, identical request body. Use either; `action` makes no
  difference. Both **create new rows at the destination**, so both are non-idempotent.

`negativeKeyword + copy` is also a create downstream - it adds new negative keywords at
the destination rather than moving anything.

## Two families, one difference that matters

Routes 1-2, 4, 7, 10 are "internal" routes; the rest are "page" routes. For a Skill the
only observable differences are:

| | Internal (1-2, 4, 7, 10) | Page (the other 20) |
|---|---|---|
| Invalid item | whole batch refused, **message lists every bad item** ("N of M items are invalid") | whole batch refused, **message names only the first** |
| Success payload | `{total, successCount, failCount, results[{id, success, message}]}` — `results[].id` is the **outer item's** key (`campaignId` at campaign level, `adGroupId` at ad-group level), not a created child id; `message` is `success` or the failure reason | `{code, message, data}` on success only |
| Non-success from downstream | three shapes: a failed envelope is raised as a tool error, a missing/mismatched `results` list becomes `ambiguous_write`, and otherwise per-item `results[].success=false` | raised as a tool error - **never** appears as `data.code != 0` |

Neither family does per-item partial acceptance at validation time. Checking `data.code`
for failure on a page route will never find one.

## Field trimming is silent, at two levels

Both the top-level request and each item are trimmed to a per-route whitelist. Extra
fields are dropped with no warning and no error. Consequences:

- `productAd + archive`: a supplied `state` is **overwritten** with `archived`, not
  rejected. Sending `state: "enabled"` still archives.
- `campaign + updateBiddingStrategy`: `businessType` is injected server-side; do not set it.
- `target + updateStatus` / `updateBid`: `matchType` is dropped (unlike keyword routes,
  which keep it).
- `target` routes: `request.targetType` selects the downstream endpoint and is then removed
  from the payload - it is a router switch, not data.
