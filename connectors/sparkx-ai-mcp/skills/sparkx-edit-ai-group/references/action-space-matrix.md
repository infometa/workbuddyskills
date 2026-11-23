# Action-space support matrix (SP / SB / SD)

Not every action-space capability is available for every ad type, and some support a
different **mode** (AI auto-decision vs Rule-based). The platform UI hides the
unsupported ones; **MCP does not** - so before enabling any action-space switch, check
it's actually supported for this group's `campaignType`. If it isn't, tell the user
it's not supported for that ad type and don't send it.

**Two different failure modes, depending on the field:**

- **SP-only fields on an SB group are now rejected outright.** The call fails with
  `X is not supported for sponsoredBrands; remove it or set to 0` (`set to null` for numeric
  ranges), listing **every** offending field at once, and **nothing is applied** - including
  the valid parts of your call. Enforced fields: `bidAmazonBusinessStatus`, `btbRangeStatus`,
  `btbMin`, `btbMax`, `bidDaypartStatus`, `bidPerformanceStrictAcosStatus`,
  `bidAdPlaceStatus`, `bidAdPlaceRangeStatus`, `tosMin`, `tosMax`, `pdpMin`, `pdpMax`,
  `rosMin`, `rosMax`, `structPauseProductStatus`, `structPauseCampaignStatus`. Sending `0` /
  `null` is fine; only an enabled value trips it.
- **One exception: a template applied cross-type is sanitized, not rejected.** When you apply
  an SP template to an existing SB group, the server zeroes the template's SP-only fields and
  the call succeeds; the response summary lists the switches that were turned off. If you also send `aiActionSettings`, the template's values are still
  merged in (current config <- template <- yours) and still sanitized; only SP-only switches
  **you** turn on go through the check above. (Creating an SB group from such a template
  turns them off the same way and lists them in the summary - see `sparkx-create-ai-group`.)
- **Everything else unsupported may still be silently ignored** - looks like success, changes
  nothing.

Either way the instruction is the same: don't send an unsupported field. But know that on SB
a single stray switch now costs you the whole write, so check before you send rather than
letting the error teach you.

> Create mode is **AI mode only** for your `aiAutomation` parameter (a `1` is rejected). So
> at create time, only enable capabilities that support **AI** for the group's ad type.
> Rule-only or unsupported ones don't belong in a create call. The one exception is SP/SB
> template create without `aiAutomation`: the template's rules, Rule mode included, are
> carried over as-is.

## Platform support != what the write tool exposes

The table below is **platform-level** capability support. It does **not** mean the MCP
write tool for that ad type actually has a field for it. Two layers must both hold to
make a valid call: **platform supports it** AND **the tool exposes a field for it**.

The gap that matters most: **the SD tools (`create_sd_ai_managed_group` /
`edit_sd_ai_managed_group`) expose only a small set** - `status`, `optimizeType`, `acos`
(edit adds `acosType`/`roasType`/`budgetType` + values), `budgetDynamicStatus`/
`numType`/`num`, `budgetRedistributeStatus`, `targetHarvestStatus`, `aiPersonality`,
`campaignNameSign` (edit: `campaignNameRecoveryType`, `remark`). They do **not** expose
the full `aiActionSettings`/`aiAutomation` action space (bid daypart / placement /
struct pause / etc.). Those fields exist **only
on the SP/SB tool** (`save_sp_sb_ai_managed_group`). **Exception - the SP/SB word-list modules are not writable via MCP:** on `save_sp_sb_ai_managed_group`, the `targetOptimization` module (negative target, target-harvest details, target pause) and `brandOptimization` module (branded / competitor) are removed from the write path - the SP/SB tool hard-rejects them; create defaults them closed and they are managed in the platform UI (read-only via MCP). **This does not affect SD:** the SD tools' own `targetHarvestStatus` (`0`/`1`/`2`) remains writable.

**SD supports only two of these action spaces** - `预算重新分配` (budgetRedistribute)
and `定向收割` (targetHarvest). Everything else in the table below is SD N. And even for
those two, confirm the SD write tool actually exposes a field before using them.

Source of truth: the per-ad-type **"AI 行动空间设置" UI** - what each ad type actually
renders. If an action space isn't in that ad type's UI, it's unsupported for that type;
the UI hides it and **MCP silently ignores the field** if you send it.

Do not confuse this with the standalone **Rule-based Automation** Help Center article.
Standalone automation templates can have broader support than the managed-group action
space exposed by MCP. Example: Help Center lists **Placement Rules / 广告位规则** as
SP/SB automation, while managed-group **广告位调价** remains SP-only here and SB templates
must be filtered out when pairing a rule with this action space.

**Per-ad-type support - UI/platform level, NOT MCP write support** (for SP/SB the word-list rows below - 添加否定定向 / 定向收割 / branded / competitor - are read-only via MCP per the exception above; SD's 定向收割 `targetHarvestStatus` and 预算重新分配 are writable):
- **SP - all 12 (AI):** every row below.
- **SB - 7:** 分时调价 *(Rule only)*, 按表现调价, 分时预算, 按表现调预算, 预算重新分配,
  添加否定定向, 定向收割.
- **SD - 2:** 预算重新分配, 定向收割.

| 行动空间 (UI) | field family (rule#) | SP | SB | SD |
|---|---|---|---|---|
| 广告位调价 (placement bids) | `bidAdPlace` / placementAdjustment (19) | Y | N | N |
| 分时调价 (bid dayparting) | `bidDaypart` (2) | Y | Y *(SB: Rule only, no AI)* | N |
| 按表现调竞价 (bid by performance) | `bidPerformance` (181) | Y | Y | N |
| B2B调价 | `bidAmazonBusiness` (noRule) | Y | N | N |
| 分时预算 (budget dayparting) | `budgetDaypart` (13) | Y | Y | N |
| 按表现调预算 (budget by performance) | `budgetPerformance` / `budgetDynamicAction` (17) | Y | Y | N |
| 预算重新分配 (budget reallocation) | `budgetRedistribute` (noRule) | Y | Y | Y |
| 添加否定定向 (add negative target) | `negativeTarget` (5) | Y | Y | N |
| 定向收割 (target harvest) | `targetHarvest` (4) | Y | Y | Y |
| 定向暂停 (target pause) | `targetPausedAdd` / targetPauseSupplement (182) | Y | N | N |
| 暂停商品 (pause products) | `structPauseProduct` | Y | N | N |
| 暂停广告活动 (pause campaigns) | `structPauseCampaign` / pauseCampaign (20) | Y | N | N |

## The things that trip agents up

- **The group switch is not the negative itself.** `negativeTargetStatus` here is the
  managed group's "自动添加否定定向" switch and is **read-only through MCP** (so are the
  word-list settings `targetOptimization` / `brandOptimization`). That does **not** mean
  negatives are unmanageable: adding, pausing, archiving and copying individual negative
  keywords and negative product targets all work through `batch_update_ads`
  (`negativeKeyword` / `negativeTarget` routes) - see the `edit-ads` Skill. Read the two
  apart before telling a user something cannot be done:
  `negativeTargetStatus` = "let the AI add negatives" (platform UI only);
  `negativeTargetState` = the state of one specific negative (writable).
- **SD supports only two** - `budgetRedistribute` + `targetHarvest`. Nothing else on SD.
- **广告位调价 (placement bids) = SP only.** Enable it via
  `aiActionSettings.bidAdPlaceStatus = 1`. **For SD and SB: skip it - do not send
  `bidAdPlaceStatus`.** On SB it is rejected outright (the whole call fails); on SD it is
  simply not supported.
- **Not available for SB (SP-only)**: 广告位调价, B2B调价, 定向暂停, 暂停商品, 暂停广告活动.
  If the user asks for any of these on an SB group, say it's SP-only and don't send it -
  enabling one now fails the entire request, not just that field.
- **SB 分时调价 is Rule-only (no AI).** In AI-mode create/edit, don't enable it as an AI
  switch on SB - tell the user it's Rule-only.
- **`noRule` capabilities** (`budgetRedistribute`, `bidAmazonBusiness`) do **not** accept
  Rule-mode parameters - only their on/off switch. Never attach Rule configs.

## What you get back when you read the group

`get_entity_metadata(entity='aiGroup')` does not echo your write - it returns the
**currently effective** config, after two reductions. Both remove fields, so plan your
verification around them.

**1. Trimmed to what the ad type supports.** The response omits action spaces that don't
apply, matching the matrix above:

| campaignType | Absent from the response |
|---|---|
| `sponsoredProducts` | nothing (full set) |
| `sponsoredBrands` | `structOptimization`; in `bidOptimization`: `bidAdPlaceStatus`, `bidAdPlaceRangeStatus`, `tos*`/`pdp*`/`ros*`, `bidAmazonBusinessStatus`, `btb*`; plus `targetPausedAddStatus` |
| `sponsoredDisplay` | `bidOptimization`, `structOptimization`, `brandOptimization`; in `budgetOptimization`: `budgetDaypartStatus`, `budgetDynamicStatus`, `numType`, `num`; the `negativeTarget*` family and `targetPausedAddStatus`; **all** automation rules |

(If `campaignType` is missing or unrecognized, nothing is trimmed.)

**2. Reduced to what's actually in effect.** A switch that's **off** drops its dependent
fields; a rule in **AI mode** is dropped from `aiAutomation` entirely; a rule in **Rule
mode** keeps its config minus AI-only parameters.

So when verifying a write: check the **switch** first, then its dependents, and treat a
missing dependent under an off switch as expected. A field's absence never proves the write
failed. Full rules in the shared [`platform-notes.md`](platform-notes.md) and in
`sparkx-query-entity-metadata`.

**Rule-mode configuration is readable.** If a group runs a rule (Rule/RBA mode), its actual
conditions, actions, condition items, time periods and hour matrices come back under
`aiAutomation.{ruleType}`. You can show and explain that setup to a user; you **cannot write
it** through any MCP tool.

## Unsupported switches for the ad type - don't send them

If the user asks for an action space that isn't supported for their ad type (per the
table), say it isn't available and **don't send it**. Per the 2026-08-14 backend spec a
cross-type field should be **rejected with an error**; but that validation isn't fully
implemented yet, so today it may instead be **silently ignored** (call looks successful,
nothing changes). Either way the result is wrong - don't send it.
