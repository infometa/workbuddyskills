# Field reference - managed-group create (exact write field names + enums)

All coded fields are **closed enums**; an unlisted value fails the call with a generic
error and no field-level hint, so validate here before sending. Field **names** also
matter: the tools set `additionalProperties: false`, so a wrong or extra field name is
rejected outright.

> **⚠️ No action-space switch has an `Action` suffix.** Earlier versions of this file
> claimed SP/SB writes needed `budgetDaypartActionStatus`, `budgetDynamicActionStatus`,
> `budgetRedistributeActionStatus`, `targetHarvestActionStatus` or `negativeTargetActionStatus`.
> **Those names do not exist** — not in the tool inputSchema, not in the payload sent
> downstream, not on the read side. The real names are `budgetDaypartStatus`,
> `budgetDynamicStatus`, `budgetRedistributeStatus`, `targetHarvestStatus`,
> `negativeTargetStatus` — the same names the read side returns.
>
> **Why this mattered:** an unknown field is dropped, not rejected, so a write built on the
> old names answered `success` while the switch never moved. If you have call templates
> saved from an earlier version of this file, check them.
>
> What **does** differ is **SD-create fields vs SP/SB fields** — those are genuinely
> different field sets. When building a write call, use the exact names in this file and
> check the ad type's column.

## Shared enums

| Field | Values |
|---|---|
| `aiPersonality` | `1`=非常保守, `2`=保守, `3`=平衡, `4`=激进, `5`=非常激进. **>=3 required when `targetType=3` (volume/冲量)** - front-end rule, not backend-enforced. ⚠️ **Group-level only, and rejected outright on accounts that set personality per action space** - check [`ai-personality.md`](ai-personality.md) before sending it |
| `campaignNameSign` | `0`=off, `1`=on |
| `budgetNumType` | `1`=percentage, `2`=fixed value |
| `bidRangeType` | `2`=fixed value. `1` = **unit unconfirmed** — documented here as "percentage" historically, but the platform UI looks coefficient-like (`0.5`-`1.13`). Do not validate, convert or restate the unit; see [`coupling-rules.md`](coupling-rules.md) |
| `*MatchType` (branded/competitor/harvest/negative) | `1`=exact(等于/精确), `2`=phrase(包含/词组) |
| `*ListType` (harvest/negative) | `1`=include/whitelist, `2`=exclude/blacklist |

## SD - `create_sd_ai_managed_group` fields

Flat fields (no nested objects):

| Field | Values / type |
|---|---|
| `status` | **create: `0`=off, `1`=on only** (`2`=cancelled is a lifecycle state, **not** a valid create input) |
| `optimizeType` | `1`=drive growth, `2`=maintain stability |
| `acos` | number, ACOS on the x100 scale (see create-sd.md) |
| `budget` / `budgetChange` | number / boolean (budget applies only when `budgetChange=true`) |
| `budgetDynamicStatus` | **Unsupported for SD creation** - omit or send `0`; non-zero is rejected |
| `numType` / `num` | **Do not send for SD creation**; companions of the unsupported dynamic-budget switch |
| `targetHarvestStatus` | `0`=off, `1`=on, `2`=on with exact negation in source ad group |
| `budgetRedistributeStatus` | `0`/`1` |
| `campaignNameSign` | `0`/`1` |
| `aiPersonality` | `1`-`5` |

## SP/SB - `save_sp_sb_ai_managed_group` `request` fields

Top-level: `aiStatus` (`0`=off, `1`=on - create input is `0`/`1`; a group reads back
as `2`=paused once off), `targetType` (`1`=drive growth, `2`=maintain stability,
`3`=volume, `4`=legacy growth), `campaignType` (`sponsoredProducts`/`sponsoredBrands`),
`acos`, `campaignIds`, `campaignNameSign`, `aiPersonality`, `preAddCampaignNums`.

### `aiActionSettings` (nested) - EXACT names

Each action-space `xxxStatus` is an on/off switch: `0` = off, `1` = on. It does not
identify AI versus Rule/RBA; use the corresponding `aiAutomation` mode field for that.

Bid: `bidDaypartStatus`, `bidPerformanceStatus`, `bidPerformanceStrictAcosStatus`,
`bidAmazonBusinessStatus`, `bidAdPlaceStatus`, `bidAdPlaceRangeStatus`,
`bidRangeStatus`, `bidRangeType`, `bidRange` (`[min,max]`, null=no limit),
`btbRangeStatus`, `btbMin`, `btbMax`, `tosMin`/`tosMax`, `pdpMin`/`pdpMax`,
`rosMin`/`rosMax`.

Struct (**SP only**): `structPauseProductStatus`, `structPauseCampaignStatus`.

Budget: **`budgetDaypartStatus`**, **`budgetDynamicStatus`**,
**`budgetRedistributeStatus`**, `budgetNum`, `budgetNumType`.

Target (**NOT writable via MCP - read-only / platform UI only**):
`targetHarvestStatus`, `targetHarvestBlackListStatus`,
`targetHarvestBlackList` (IDs), `targetHarvestListType`, `targetHarvestMatchType`,
`negativeTargetStatus`, `negativeTargetBlackListStatus`,
`negativeTargetBlackList` (IDs), `negativeTargetListType`, `negativeTargetMatchType`,
`targetPausedAddStatus` (`0`=off, `1`=on, `2`=on with supplement). The SP/SB tool
**hard-rejects** this entire `targetOptimization` module (target harvest / negative
target / target pause); create defaults it closed. These names may still appear in some
schemas, but they are read-only - inspect them via `get_entity_metadata`, change them in
the platform UI, and never send them as write inputs.

The whole `targetOptimization` module (all fields listed above) and the
`brandOptimization` module - including `brandedStatus`, `brandedList`, `competitorStatus`,
`competitorList`, and any `*BlackList*` status/list field - are **currently unsupported**
(removed from the write path; read-only, platform UI only). Do not send any of these
status, list ID, match-type, or list-type fields; the tool hard-rejects them.

### `aiAutomation` (flattened mode fields) - EXACT names

`aiActionSettings.xxxStatus` controls whether an action space is enabled. When it is
enabled, the corresponding `aiAutomation` field selects the mode.

**⚠️ The mode value reads backwards from intuition: `0` = AI mode (the system decides on its
own), `1` = Rule mode (RBA).** `1` is **not** "enabled" - and Rule mode cannot be configured
through these tools, because a rule needs conditions and actions that this schema doesn't
carry. So: send `0`, or omit the field. Never send `1`.

If the user wants a rule-driven setup, say it has to be built in the platform UI. (You *can*
read an existing rule's full configuration - see `sparkx-query-entity-metadata`. A
rule-based group can be switched to AI, but not the reverse.)

`aiAutomation` is a **flat object** (not nested per rule) on the write side. Each field maps
to one automation rule number:

| `aiAutomation` field | Rule | Paired `aiActionSettings` switch |
|---|---|---|
| `bidDaypartStatus` | 2 - bid dayparting | `bidDaypartStatus` |
| `targetHarvestRuleStatus` | 4 - target harvest (**read-only context; not settable at create**) | `targetHarvestStatus` |
| `negativeTargetRuleStatus` | 5 - negative target (**read-only context; not settable at create**) | `negativeTargetStatus` |
| `budgetDaypartRuleStatus` | 13 - budget dayparting | `budgetDaypartStatus` |
| `budgetPerformanceRuleStatus` | 17 - budget by performance | `budgetDynamicStatus` |
| `placementAdjustmentRuleStatus` | 19 - placement adjustment | `bidAdPlaceStatus` |
| `pauseCampaignRuleStatus` | 20 - pause campaign | `structPauseCampaignStatus` |
| `bidPerformanceRuleStatus` | 181 - bid by performance | `bidPerformanceStatus` |
| `targetPauseSupplementRuleStatus` | 182 - target pause / supplement (**read-only context; not settable at create**) | `targetPausedAddStatus` |

One extra field, only meaningful with rule 13:

| Field | Type | Notes |
|---|---|---|
| `budgetDaypartExcuteDays` | string | Comma-separated days for budget dayparting. **`1`-`6` = Mon-Sat, `0` = Sunday.** Default `"1,2,3,4,5,6,0"` (every day). Note the spelling - `Excute`, not `Execute` |

`budgetRedistributeStatus` and `bidAmazonBusinessStatus` have no Rule mode; only
their `aiActionSettings` on/off switch applies.

**On read**, `aiAutomation` comes back keyed by rule number (`"2"`, `"4"`, `"181"`, …) rather
than by these field names, and rules running in AI mode are omitted entirely. An empty
`aiAutomation` is ambiguous by itself: read the paired `aiActionSettings` switches to distinguish
off action spaces from enabled action spaces in AI mode. Details are in
`sparkx-query-entity-metadata`.

> Coupling rules (open a switch -> must also send its companion fields) are in
> [`coupling-rules.md`](coupling-rules.md).

## Known value-range caveat

- **Avoid `budgetType=3`** where it appears in edit/action paths - a known P0 that can
  hang the downstream service. Not needed for a basic create.
