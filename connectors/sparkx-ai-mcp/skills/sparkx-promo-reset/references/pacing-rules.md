# Pacing rules: how fast to restore each item

Two kinds of numbers drive the suggestions, and the reasons must show both:

- **Ranges and targets come from the store's own data** - each item's normal ACOS / CVR range,
  the store's range, the target ACOS (sections 2-3).
- **A few cut-offs are default rules of thumb**, set from two backtests (2026-10). They are
  not derived from the store; state them when they decide an item, and let the customer
  change them:

| Default | Value | Used in |
|---|---|---|
| Minimum clicks per 3-day window | 10 | normal range (2), "barely spent" (5) |
| "Barely spent" spend ceiling | 10 x the store's average CPC over the normal period | 5 |
| Step-down cut-offs | raised < 1.5x -> at once; >= 2x with high CVR -> 3 days | 5 |
| Usable windows needed for an own range | 5 | 2 |
| Low stock | promoted ASINs' days of cover under about 2 weeks | 5 |
| Binding budget | out of budget on 2 of the 3 post-promo days | 7 |

The spend ceiling is expressed in CPC so it works in any currency without an exchange rate.

## 1. Data to pull

`get_ads_perf`, one store, daily (`select` includes `date`):

| Period | Range | Used for |
|---|---|---|
| Normal | the 21 days before the window starts | normal range per item, and for the store |
| Post-promo | the last 3 full days after the window ends | the item's post-promo performance |

- Budgets and placements are judged on the **campaign** (`factEntity: campaign`, select
  `campaign.campaignId_` + `campaign.campaignName_`); bids on the **keyword / target**
  (`factEntity: target`). The perf ids are Amazon ids - join them to the log's
  `amazonCampaignId` / Amazon entity id, not to internal ids.
- Metrics: `Spend`, `Sales`, `Clicks`, `Conversions` (compute ACOS and CVR yourself from the
  sums - never average daily ratios).
- Store totals for the same days (`select: ["date"]`): the store normal range and the
  one-line store context.
- Reporting delay: if the post-promo days include yesterday or today, say the data may still
  be filling in. Fewer than ~3 complete days -> restore at once if raised < 1.5x, otherwise
  step down over 2 days, and say the data was too thin to judge.
- None of this file applies when the user chose "all at once" in Step 1: every raised item
  is restored at once.

## 2. Normal range

1. **Fill the calendar first.** `get_ads_perf` returns no row for a day with no activity. Build
   all 21 calendar days for the item and fill missing days with zeros, so every window below
   really is 3 consecutive days.
2. Slide a 3-day window over the 21 days: 19 windows.
3. **Usable windows**: at least 10 clicks, and at least one sale. A window that spent but sold
   nothing has no finite ACOS - leave it out of both percentiles (ACOS and CVR come from the
   same set of windows), but count it and say so when it matters ("21 天里有 6 段 3 天没出单").
4. With **5 or more** usable windows: normal ACOS = 10th-90th percentile of the usable
   windows' ACOS; normal CVR = 10th-90th percentile of their CVR.
5. With fewer (new or small items, or items that often sell nothing): use the **store's**
   range and say "店铺整体平时范围" in the reason. The store range is computed the same way on
   the store's daily totals - calendar filled, 3-day windows - with no click minimum (a whole
   store clears it anyway); a store window with no sales is left out like an item's.

## 3. Target ACOS

First that exists:

1. The item's managed group's **pre-promo** target ACOS - the `previousValue` of the group's
   first `acos` change in the window, or the current value if the group's target was not
   changed.
2. A target the user gave.
3. The upper end of the store's normal ACOS range.

The store range can be very narrow when branded campaigns dominate spend (29-32% in one
production store) - too tight to judge a category-keyword campaign by. That is why the
group's own target comes first.

## 4. Post-promo values

Over the 3 post-promo days: spend, sales, clicks, conversions; ACOS = spend / sales (spend
with no sales counts as worse than any range); CVR = conversions / clicks. Ratio = current
value / pre-promo value (for a placement whose pre-promo value is `0` there is no ratio - use
the uplift in percentage points instead: under 50 points counts as "< 1.5x", 100 or more as
">= 2x").

## 5. Decision, in this order

| # | Condition | Suggestion | Reason should say |
|---|---|---|---|
| 1 | Fewer than 10 clicks **and** spend below 10 x the store's average CPC (normal period) | Restore at once | "大促后 3 天只花了 $2.1，影响很小" |
| 2 | ACOS above its normal range **and** above target | Restore now | ACOS, the range, the target |
| 3 | ACOS above target, but **not** above its own normal range (own range, not store fallback) | Normal pace (rule 5) + note | "高于目标，但和它平时差不多——不是大促造成的" |
| 4 | CVR above its normal range | Step down: 3 days if ratio >= 2, else 2 days | CVR, the range, the ratio |
| 5 | Otherwise | Restore at once if ratio < 1.5, else 2 days | ACOS / CVR within range, the ratio |

Then overrides:

- **Product low on stock** (the promoted ASINs' `asinDayAvailability` under ~2 weeks, Seller
  profiles with SP-API only) -> restore now: "库存只够 9 天，不要把剩余库存花在高价流量上".
- **A deal still running** (from Step 1) -> hold until it ends.
- **Changed again after the window**, **created in the window**, **lowered** -> you decide
  (see [`restore-list.md`](restore-list.md)).

## 6. Step values

For `n` days from current value `c` to pre-promo value `b`, day `k` writes
`c - (c - b) * k / n`; the last day writes exactly `b`. Round to the currency's precision
(whole units for JPY), placements to whole percent on SB.

Example: 100 -> 35 over 3 days: 78.33 -> 56.67 -> 35 (shown as $78 -> $57 -> $35).

## 7. Lowered budgets: is the cut binding?

Count the **distinct days** with a `Campaign Out of Budget` event per campaign in the
post-promo days (several events can land on one day).

- **2 or more of the 3 days** -> binding: "大促后每天都花光 $100，大促前是 $250，可以考虑加回".
- **Fewer** -> not binding: adding budget back changes nothing. If the campaign's sales also
  fell sharply, say budget is not the cause and suggest checking stock, buy box and listing
  status.

## Backtest notes (2026-10, two production stores, read-only)

- A manual-bidding store, 88 campaigns with promo budget changes: 16 restore now (3-day
  post-promo spend of 1,533), 13 step down, 7 at once, 4 changed again later, 45 lowered,
  3 unchanged.
- A managed-group store: all 43 groups still on 活动冲量 five days after the promo; of 41
  campaign budgets, 7 restore now, 5 step down, 6 at once, 12 lowered (4 binding), 11
  unchanged. Switching the target from the store range to each group's pre-promo target did
  not change any "restore now" verdict. (Those counts used a fixed 20 USD "barely spent"
  ceiling; with the CPC-based ceiling one campaign - 3 clicks, 26 spent - moves from "restore
  now" to "at once". Both write the pre-promo value in one step. The first store's verdicts
  are unchanged.)
- Still to validate on more promos: the 1.5x / 2x step-down cut-offs, and whether the store
  fallback range is too strict for small campaigns.
