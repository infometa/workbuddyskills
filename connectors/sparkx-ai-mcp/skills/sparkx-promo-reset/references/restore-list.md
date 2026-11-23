# Building the restore list

How to turn the operation log into "what a person changed for the promo, and what it was
before". Read the operation-log skill's SKILL.md first - pagination modes, the 90-day span,
truncation handling and the `createdDate` timezone rules all apply here and are not repeated.

## 1. One store, one window, several queries

- **One `profileId` per run.** Ad-entity timestamps are store-local only for a single
  profile; with several they turn UTC and the window boundaries shift.
- **Query from the window start to today**, not to the window end - you need the rows after
  the window to find items a person changed again later (they become "you decide").
- **One entity per query**, so each runs in real-pagination mode (`entities` = one non-`aiGroup`
  value -> loop `page` while `meta.hasNextPage`). A single multi-entity query is limit-only,
  and managed-group rows are not narrowed by `actionType`, so they crowd out everything else
  and the result truncates.
- **No `changeBy` filter.** Classify sources yourself (section 2).

| What | `entities` | Filter | Keep rows whose `changeField` is |
|---|---|---|---|
| Campaign budgets | `["campaign"]` | `actionType`: `Budget Increased`, `Budget Decreased` | `dailyBudget` |
| Placement multipliers | `["placement"]` | `actionType`: `Placement Increased`, `Placement Decreased` | the placement field the row reports |
| Keyword / target bids | `["target"]` | `actionType`: `Bid Increased`, `Bid Decreased` | the bid field the row reports |
| Ad group default bids | `["adGroup"]` | `operationType`: `AdGroup Bid Increased`, `AdGroup Bid Decreased` | the bid field the row reports |
| Managed-group settings | `["aiGroup"]` | none (limit-only, `pageSize` up to 10,000; split the window if `truncated`) | `optimizeType`, `acos`, `aiPersonality`, `bidRangeMin`, `bidRangeMax`, any action-space switch, and any budget field |
| Lowered budgets: is the new budget binding? | `["campaign"]` | `operationType`: `Campaign Out of Budget`, post-promo days only | - (count events per campaign) |
| Created during the promo | `["campaign"]`, `["target"]` | `actionType`: `Added` | - |

**An empty managed-group result is not proof of no changes.** That query returns an empty list
when it fails internally, instead of an error. Cross-check with
`get_entity_metadata(entity='aiGroup')`: groups still on `targetType: 3` with no history means
the history is unreadable -> "you decide".

**Managed-group rows are special.** They are always UTC (convert the window with the store's
`timezone` from `get_user_authorized_context`); they can come back with `profileId` and
`campaignName` null, so identify the group by `entityId` (= `aiGroupId`) against
`get_entity_metadata(entity='aiGroup')` for this store. Their `operationType` strings in
production (2026-10) were not the ones in the operation-log skill's enum table - e.g. "The
objective of managed group AI has been adjusted", "The target value of managed group AI has
been adjusted", "The min bid has been adjusted", "Set max bid" - so **do not filter managed
groups by `operationType`**; pull them unfiltered and select by `changeField`.

## 2. Which rows are a person's

| `changedBy` | Counts by default |
|---|---|
| an email address | yes - a user acting in the platform |
| `Manual` | yes - also a platform user |
| `Amazon Console` | **no by default - a source, not an operator.** Came from Amazon's side, author unknown. List separately as source-unknown with `suggestion: customerDecides`; restore only per-item on the user's say-so |
| `AI`, `Automation`, `AI-Custom Rule`, `Budget Management`, `Lock Ranking`, `API`, `Labels`, `System` | no - unless the user asks to include them; then name the added sources in the list header |

Why not `changeBy: manual` on the query: **the server rejects it** (case-insensitive, in `IN`,
`NOT_IN` or mixed). It used to match only the literal value `Manual` (plus a platform-source
restriction), so changes attributed to a user's email disappeared — in a production test
(2026-10) every human promo change in one store was email-attributed and `manual` returned none
of them. Omit `changeBy` and classify client-side.

Classify on `changeField` as well as `changedBy`: `Amazon Console` also appears on status events
such as `Campaign Out of Budget`, which are not settings anyone changed.

**AI's hourly budget rows are not promo changes.** In a managed group, AI rewrites the day's
spendable budget every hour - `changeField: currentBudget`, ramping from a few dollars at
midnight up to the cap. A few days produce hundreds of rows. Only `dailyBudget` (the cap a
person sets) is restored.

## 3. Pre-promo value, current value, and the buckets

Group rows by object + field: (`entity`, `entityId`, `changeField`; for placements also the
placement). Sort ascending by `createdDate` (the log is newest first).

- **Pre-promo value** = `previousValue` of the **first human row inside the window**. Everything
  after it inside the window is promo-time churn, including a blanket "set everything to $100"
  on the last day.
- **Creation rows are not pre-promo values.** An empty / null `previousValue` means the object
  or setting was created then. For budgets, bids, target ACOS and objective a `0` means the
  same thing (e.g. target ACOS `0 -> 31.15` when a group is created). **For placement
  multipliers `0` is a real value** (no uplift) - keep it.
- **Current value**: read it with `get_entity_metadata` (campaign `dailyBudget`, keyword/target
  bid, campaign placement rows, `aiGroup` `targetType` / `targetAcos` / `aiPersonality` /
  `aiActionSettings`). The log's last `newValue` is a cross-check, not the source of truth.

| Situation | Bucket |
|---|---|
| A human changed it again **after** the window | You decide - do not overwrite a newer decision |
| AI changed the same field after the last human change (bids in a running group) | You decide - AI is managing it and may move it again |
| The object was created inside the window | You decide - pause or keep; there is no "before" |
| Current value != the log's last value | You decide - something changed it outside what the log shows |
| Current = pre-promo | Skip (count it) |
| Current > pre-promo (numeric fields) | Raised -> pace it ([`pacing-rules.md`](pacing-rules.md)) |
| Current < pre-promo | Lowered -> you decide, with the "is it binding" note |
| Objective / switch differs from pre-promo | Restore with the group settings |

Groups that used a **dated schedule** for the promo show schedule rows, not setting changes,
and revert on their own when the schedule ends - list them as "已由排期自动失效".

## 4. From a log row to a write

Every write goes through its owning skill, with internal ids and discriminator fields from
`get_entity_metadata` - the log's `entityId` is a hint, never the write id without checking.

| Log row | Write | Notes |
|---|---|---|
| `campaign` / `dailyBudget` | `sparkx-edit-ads`: `campaign` + `updateBudget`, `budget.type: setTo` | One `campaignType` per batch. For a campaign inside a managed group this is the campaign's own daily budget - do **not** edit the group total, which rescales every enabled campaign |
| `placement` | `sparkx-edit-ads`: `campaign` + `updatePlacementBid` | The log's placement names are not the write fields: `topSearchAdjustment` is SP `topAdjustment` / SB `topOfSearchAdjustment`; SB uses `homeAdjustment`, `detailPageAdjustment`, `otherAdjustment`; SP uses `productPageAdjustment`, `restOfSearchAdjustment`. Values are absolute percentages 0-900 (SB integers only); send only the placements you restore. **On SB the write also sets `bidOptimization=false`** (custom bidding) - tell the user first. The Amazon Business adjustment is logged on the campaign entity, not under `["placement"]`, and has no write route here - out of scope |
| `target` bid | `sparkx-edit-ads`: `keyword` + `updateBid` or `target` + `updateBid` | Resolve the row (keyword vs target, `matchType`, `campaignType`) from metadata first |
| `adGroup` default bid | none | No MCP write route for ad group default bids - list it with its pre-promo value for the user to change in the platform |
| `aiGroup` / `optimizeType` | `sparkx-edit-ai-group`: SP/SB `targetType`; SD `optimizeType` | `1` 推动增长, `2` 保持订单稳定, `3` 活动冲量, `4` legacy (SP/SB). SD groups use the SD tool and shape - e.g. its `acos` needs `acosType` - follow that skill |
| `aiGroup` / `acos` | `acos` | Same percent scale on both sides (`248.115` in the log = 248.115%) |
| `aiGroup` / `aiPersonality` | `aiPersonality` | `targetType 3` requires `aiPersonality >= 3`: when restoring both, send them in the same request |
| `aiGroup` / `bidRangeMin`, `bidRangeMax` | `aiActionSettings` bid range | Written as one `[min, max]` pair (both required, min <= max). A log row usually changes one bound: rebuild the pair from the current value plus the restored bound. Keep the group's current `bidRangeType`. If a pre-promo bound was unset (`0` or empty, shown as "Set max bid"), do not guess how to clear it - show it and let the user decide or change it in the platform |
| `aiGroup` total budget | `sparkx-edit-ai-group` group budget | Editing the total rescales every enabled campaign's daily budget proportionally. If the promo change was to the group total (an aiGroup budget row, or all of a group's campaign budgets moving together at one timestamp by one person), restore the **total** and do **not** also restore those campaign rows one by one. If unclear which the user changed, ask |
| `aiGroup` / other action-space switches | `sparkx-edit-ai-group` | Follow that skill's action-space and coupling rules; when unsure, list it as "you decide" |

SP/SB group edits merge onto the current configuration: send only the restored fields. SD
groups use the other tool and shape - follow `sparkx-edit-ai-group`.
