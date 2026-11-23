# Action-space & budget coupling rules (SP / SB / SD)

The first bullets cover SP/SB `aiActionSettings`; sections further down also cover SD and
the group-total-budget behavior. `aiActionSettings` is not just on/off switches - several switches are meaningless (or
fail / fall back to unintended defaults) unless you also send their companion fields.
When enabling one, include the whole set. These are front-end-enforced linkages; MCP
won't enforce them, so you must. (Exact field names: `field-reference.md`.)

- **Dynamic budget** (`budgetDynamicStatus=1`) -> also `budgetNumType`
  (`1`=percentage / `2`=fixed) and `budgetNum` (the value). Value bounds (the batch path
  uses `budgetDynamicStatus`/`numType`/`num`): `num > 0`; `numType=1` (percentage)
  `num <= 1000`; `numType=2` (fixed) `num <= 100000`.
  **Use percentage mode (`1`) whenever the operation spans stores in different currencies** -
  a fixed amount has no single meaning across currencies, and nothing on the backend stops
  you from applying one uniformly. If the user asks for a fixed increase across a
  mixed-currency set, either convert per store and write per store, or switch them to a
  percentage and say why.
- **Bid range** (`bidRangeStatus=1`) -> also `bidRangeType` and `bidRange` `[min,max]`
  (array length exactly 2, **min <= max**). `bidRangeType=2` (fixed): `min >=` the site's
  minimum bid.

  ⚠️ **`bidRangeType=1` - treat the meaning as unconfirmed.** This file used to call it
  "percentage" and bound it to `0.01 <= min`, `max <= 100`. The platform UI appears to take a
  **bid coefficient** instead (values like `0.5` - `1.13`), which the old bound would reject as
  illegal while accepting a percentage-shaped number that means something else entirely. Until
  the backend confirms the enum: **do not reject a `bidRangeType=1` value for falling outside
  `0.01`-`100`**, do not convert between percent and coefficient, pass what the user gave,
  and tell them the unit is unconfirmed so they can check the value in the UI after the write.
  Note:
  **BidDaypart and BidAdjustment share this one `bidRange`** - if both are on it applies
  to both.
- **B2B range** (`btbRangeStatus=1`) -> `btbMin`/`btbMax`: `btbMin >= 0`, `btbMax <= 900`,
  min <= max, at least one end non-null.
- **Placement ranges** (`bidAdPlaceRangeStatus=1`) -> **at least one** of the `tos*`/
  `pdp*`/`ros*` min/max pairs non-null (don't enable the switch with all null); each pair
  `min >= 0`, `max <= 900`, min <= max.

## Performance budget (按表现调预算) and budget reallocation (预算重新分配) are linked

**按表现调预算** (`DYNAMIC_BUDGET`) - the value is an **increase cap on top of the current
budget, NOT a target**. Mode `1`=percentage (`+num%`), `2`=fixed (`+$num`). **Fields by
path:** SP/SB create uses `budgetDynamicStatus`+`budgetNumType`+`budgetNum`; SD
**creation does not support this feature**. The SD edit/batch path is documented separately
in the edit Skill; do not carry its `budgetDynamicStatus`+`numType`+`num` fields into create.

**预算重新分配** (`BUDGET_REDISTRIBUTE`) - a switch that **changes the scope of 按表现调预算**.
**Fields by path:** SP/SB action space `budgetRedistributeStatus`; SD
`budgetRedistributeStatus`; batch = per the `BUDGET_REDISTRIBUTE` schema.

**Scope - worked example.** A group with two enabled campaigns at **$100** and **$200**
(group total **$300**), 按表现调预算 value = **20**:

| 预算重新分配 | mode | how it applies | group max |
|---|---|---|---|
| OFF | fixed 20 | each campaign +$20 ($100->$120, $200->$220) | **$340** |
| OFF | percent 20% | each campaign +20% ($100->$120, $200->$240) | **$360** |
| ON | fixed 20 | whole group ($300 + $20) | **$320** |
| ON | percent 20% | whole group ($300 + 20%) | **$360** |

- **OFF = per enabled campaign** (each campaign's own daily budget may rise by the cap).
- **ON = whole group** - you can only determine the **group-level** cap; you **cannot**
  infer how much each individual campaign will end up with.
- **Fixed vs percentage give different results** once campaign budgets differ - the
  single-campaign "$100 -> $120" case hides this, so always distinguish the two modes.
- **Whether to ask:** at **create**, the user must specify the mode (fixed/percent) and
  预算重新分配 on/off. At **edit**, read the current 预算重新分配 first and **keep it unless
  the user asked to change it** (state it in the preview). **Only ask** when the mode, the
  scope, or the user's intent is still ambiguous. Either way, always make clear the number
  is an *increase* (not a target) and show the full impact before executing.

## Group total budget (托管组总预算) rescales campaigns proportionally

托管组总预算 / group total budget = the **sum of the group's enabled campaigns' daily
budgets** (`totalBudget` / `totalDailyBudget` on read reflect this).

> **It is a sum, not a separate cap.** `totalDailyBudget` reads like an extra group-level
> ceiling sitting above the campaigns, and there is no such thing here: nothing enforces it
> independently, and the group spends whatever its members spend.
>
> **But it is writable, and writing it is a real lever** — editing the group total
> **proportionally rescales every enabled campaign's daily budget** to the new total. So
> "lower the group budget to contain spend" does work; what it is not is a cap you can set
> and forget. Before writing it, state the blast radius in the preview: **which campaigns
> change and to what**, because every enabled member moves, not just the ones the customer
> had in mind. It is not an isolated field.

## Strict ACOS / ACOS priority mode (`bidPerformanceStrictAcosStatus`)

Page name **"ACOS 优先模式 / ACOS priority mode"** (a.k.a. Strict ACOS / strict ROAS). It's
a **checkbox under 按表现调价 (bid-by-performance)** that makes the AI cut bids harder and
faster when ACOS is badly off target. Field: `bidPerformanceStrictAcosStatus` (`0`/`1`).

- **SP only** - SB and SD do not support it; don't send it for them.
- **Requires ALL of these together, or it will NOT trigger** (don't claim it's active
  otherwise): `targetType=2` (Maintain Stability / 保持订单稳定) **and** `bidPerformanceStatus=1`
  (performance bidding on, AI mode) **and** an AI personality of at least `3` on performance
  bidding. Enabling it means setting/confirming all three; a personality of 1-2 never
  triggers it. **Which field carries that personality depends on the account.**
  - **Legacy accounts**: the group-level `aiPersonality`.
  - **Accounts that set personality per action space**: `bidPerformanceAiPersonality`.
    The group-level `aiPersonality` is still returned by a read on these accounts, but it
    is read-only and **no longer drives this rule** - don't evaluate the condition from it.
  - **When you can't tell**: a missing `*AiPersonality` field does **not** prove the
    account is legacy - a failed capability lookup returns the legacy shape too. Treat the
    rule as **not satisfied** unless one of the two readings clearly meets `>= 3`, and say
    which reading you used. See [`ai-personality.md`](ai-personality.md).
- **Auto Pacing wins:** if the group's `isAutoPacing` is on, Strict ACOS is **paused** until
  Auto Pacing is turned off. Read `isAutoPacing` and tell the user if it will be suppressed.
- **Scope:** affects **base bid only** (not targeting / budget / negatives); no weekday
  scheduling (date-range only).
- **Early Access / permission-gated:** the account/group may not have it enabled. If the
  switch doesn't stick on read-back, tell the user it's Early Access (access-controlled) -
  don't report it as a silent failure of your call.
- **It's a tradeoff** - it can **underspend budget and reduce orders** in exchange for
  hitting ACOS. **Confirm this tradeoff with the user before enabling**, and don't turn it
  on by default for every stability-target group.

## Word-list fields are not supported

All word-list settings are currently unsupported, including branded, non-branded,
competitor, negative-target blacklist, and target-harvest blacklist settings. **Do not
send their status, list ID, match-type, or list-type fields for SP, SB, or SD**, even if
the routed schema exposes them. Tell the user to configure word lists in the platform.

## Disabling an action space doesn't clear its follow-up fields

Turning an action space off (its `*Status=0`) only updates that status - the backend does
**not** zero out the range/companion values you set before (confirmed 2026-08-14). To
change a follow-up value you must re-send it.
