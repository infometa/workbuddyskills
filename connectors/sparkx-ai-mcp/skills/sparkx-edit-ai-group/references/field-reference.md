# Field reference - managed-group create/edit (exact write field names + enums)

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
| `numType` / `budgetNumType` | `1`=percentage, `2`=fixed value |
| `bidRangeType` | `2`=fixed value. `1` = **unit unconfirmed** — documented here as "percentage" historically, but the platform UI looks coefficient-like (`0.5`-`1.13`). Do not validate, convert or restate the unit; see [`coupling-rules.md`](coupling-rules.md) |
| `*MatchType` (branded/competitor/harvest/negative) | `1`=exact(等于/精确), `2`=phrase(包含/词组) |
| `*ListType` (harvest/negative) | `1`=include/whitelist, `2`=exclude/blacklist |

## SD - `create_sd_ai_managed_group` fields

Flat fields (no nested objects):

| Field | Values / type |
|---|---|
| `status` | **create: `0`=off, `1`=on only** (`2`=cancelled is a lifecycle state, **not** a valid create input) |
| `optimizeType` | `1`=drive growth, `2`=maintain stability, **`3`=boost volume** (SD edit accepts 1-3; anything else is rejected) |
| `acos` | number, ACOS on the x100 scale (see create-sd.md) |
| `budget` / `budgetChange` | number / boolean (budget applies only when `budgetChange=true`) |
| `budgetDynamicStatus` | `0`/`1` |
| `numType` / `num` | value type / value for dynamic budget |
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

Target (**read-only via MCP - not settable at edit; configure in the platform UI**):
`targetHarvestStatus`, `targetHarvestBlackListStatus`,
`targetHarvestBlackList` (IDs), `targetHarvestListType`, `targetHarvestMatchType`,
`negativeTargetStatus`, `negativeTargetBlackListStatus`,
`negativeTargetBlackList` (IDs), `negativeTargetListType`, `negativeTargetMatchType`,
`targetPausedAddStatus` (`0`=off, `1`=on, `2`=on with supplement). These read back
from `get_entity_metadata` but the SP/SB write tool does not apply them - don't send
them at edit.

Word-list fields may appear in some schemas, including `brandedStatus`, `brandedList`,
`competitorStatus`, `competitorList`, `negativeTargetBlackListStatus`, and
`targetHarvestBlackListStatus`. They are **currently unsupported**. Do not send any
word-list status, list ID, match-type, or list-type field.

### `aiAutomation` (flattened mode fields) - EXACT names

`aiActionSettings.xxxStatus` controls whether an action space is enabled. When it is
enabled, the corresponding `aiAutomation` field selects the mode.

**⚠️ The value reads backwards from intuition: `0` = AI mode (system decides), `1` = Rule
mode (RBA).** `1` is **not** "enabled". Edit may set a field to `0` to switch **RBA -> AI**;
it must never set `1` to switch **AI -> RBA**, and it cannot write RBA conditions/actions.

`aiAutomation` is a **flat object** on the write side. Each field maps to one rule number:

| `aiAutomation` field | Rule | Paired `aiActionSettings` switch |
|---|---|---|
| `bidDaypartStatus` | 2 - bid dayparting | `bidDaypartStatus` |
| `targetHarvestRuleStatus` | 4 - target harvest (read-only, not settable at edit) | `targetHarvestStatus` |
| `negativeTargetRuleStatus` | 5 - negative target (read-only, not settable at edit) | `negativeTargetStatus` |
| `budgetDaypartRuleStatus` | 13 - budget dayparting | `budgetDaypartStatus` |
| `budgetPerformanceRuleStatus` | 17 - budget by performance | `budgetDynamicStatus` |
| `placementAdjustmentRuleStatus` | 19 - placement adjustment | `bidAdPlaceStatus` |
| `pauseCampaignRuleStatus` | 20 - pause campaign | `structPauseCampaignStatus` |
| `bidPerformanceRuleStatus` | 181 - bid by performance | `bidPerformanceStatus` |
| `targetPauseSupplementRuleStatus` | 182 - target pause / supplement (read-only, not settable at edit) | `targetPausedAddStatus` |

| Field | Type | Notes |
|---|---|---|
| `budgetDaypartExcuteDays` | string | Only meaningful with rule 13. Comma-separated: **`1`-`6` = Mon-Sat, `0` = Sunday**. Default `"1,2,3,4,5,6,0"`. Note the spelling - `Excute` |

`budgetRedistributeStatus` and `bidAmazonBusinessStatus` have no Rule mode; only
their `aiActionSettings` on/off switch applies.

**Partial edits merge with current config**, so you can send just the mode field you're
changing. But when you send `aiActionSettings`, mind the SB restrictions in
[`action-space-matrix.md`](action-space-matrix.md) - an SP-only field enabled on an SB group
now fails the whole call.

**On read**, `aiAutomation` is keyed by rule number (`"2"`, `"4"`, `"181"`, …), AI-mode rules
are omitted entirely, and Rule-mode rules come back with their full condition/action
configuration (readable, not writable). An empty `aiAutomation` is ambiguous by itself: read the
paired `aiActionSettings` switches to distinguish off action spaces from enabled action spaces in
AI mode.

> Coupling rules (open a switch -> must also send its companion fields) are in
> [`coupling-rules.md`](coupling-rules.md).

## Edit-only fields - SD `edit_sd_ai_managed_group`

These exist on the SD edit tool (not on create). `*Type` selects a mode that dictates
which value field is valid - see `edit-sd.md` for the full mutual-exclusion table.

| Field | Values |
|---|---|
| `acosType` | `1`=value (-> `acos`), `2`=recommended (-> `acosStatus=1`), `3`=ratio (-> `acosRatio`) |
| `acosStatus` | `1`=apply recommended ACOS |
| `roasType` | `1`=value (-> `roas`), `2`=recommended, `3`=ratio (-> `roasRatio`) |
| `budgetType` | `1`=total (-> `budget`), `2`=daily (-> `budget`), `3`=ratio (-> `budgetRatio`) |
| `campaignNameRecoveryType` | when turning the name label off: `1`=keep current, `2`=restore original |
| `remark` | free text, max 200 chars |
| `ids` | array of aiGroupIds to update, **max 20** |

## SP/SB batch-only fields - inside `request`

When `operation` is non-null, the tool uses `ids` as the target set and ignores
`aiGroupId`. Operation values are **UPPER_SNAKE_CASE** - verified live against the tool
enum (lowercase is rejected with `does not have a value in the enumeration [...]`):

`BUDGET`, `STATUS`, `TARGET_TYPE`, `ACOS`, `ROAS`, `TARGET_HARVEST`, `DYNAMIC_BUDGET`,
`CAMPAIGN_NAME_SIGN`, `AI_PERSONALITY`, `BID_OPTIMIZATION`,
`STRUCT_OPTIMIZATION`, `BUDGET_DAYPART`, `BUDGET_DYNAMIC_ACTION`, `BUDGET_REDISTRIBUTE`,
`TARGET_HARVEST_ACTION`, `NEGATIVE_TARGET`, `BRAND_TARGET`, `TARGET_PAUSED_ADD`.

Flat operations read these fields from `batchParams`: `budgetType`, `budget`,
`budgetRatio`, `status`, `optimizeType`, `acosStatus`, `acosType`, `acos`,
`acosRatio`, `roasType`, `roas`, `roasRatio`, `targetHarvestStatus`,
`budgetDynamicStatus`, `numType`, `num`, `campaignNameSign`,
`campaignNameRecoveryType`, and `aiPersonality`. See `batch.md` for the operation to
parameter mapping and mutual-exclusion rules.

## Known value-range caveat

- **`budgetType=3`** (ratio) is a known-risky value - it can hang the downstream
  service. Avoid unless ratio mode is specifically needed; if used, send `budgetRatio`
  and no `budget`.
