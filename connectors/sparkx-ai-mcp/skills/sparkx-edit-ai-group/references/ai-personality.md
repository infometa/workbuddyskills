# AI personality: per-action-space, and the legacy group-level field

> **This file is duplicated across the create and edit managed-group skills (and both
> brands). Any change here must be applied to every copy** - a rule that disagrees between
> them produces different model behaviour depending on which skill answered.

Two kinds of account exist. The write tools decide which one you are on **at call time**, you
cannot switch an account through them, and the schema and descriptions are identical for
both - only the server's response differs.

**A read can tell you, in one direction.** `get_entity_metadata(entity='aiGroup')` on an
account that sets personality per action space returns the 12 `*AiPersonality` fields inside
`aiActionSettings`, plus
`actionSpaceIntensitySummary` at the top of the row - `{"allSame": true, "intensity": N}` when
every space is on the same level, `{"allSame": false}` otherwise. Legacy accounts carry none of
these.

The companions are conditional, so do not expect them on every field: a `*Text` is derived
only when that field's value is an integer `1`-`5`, and a `*UpdatedAt` appears only when the
downstream supplied one. A missing companion says nothing about the personality itself.

- **Seeing them is proof**: that account sets personality per action space.
- **Not seeing them proves nothing.** The summary is only emitted when the row has at least
  one valid personality value, so a group whose personalities are all unset looks the same as a
  legacy one; a failed capability lookup also falls back to the legacy shape.

So on an **edit** - where you are reading the group first anyway - use that read. On a
**create** there is no group yet: read any existing `aiGroup` in the same profile (the
setting is per account, not per group), or simply send the form you intend and let an
`invalid_params` rejection tell you - it happens before anything is written.

⚠️ On these accounts the group-level `aiPersonality` **is still returned by a read, but it is
read-only**. Seeing a number there is not permission to send it back.

| | Per-action-space accounts | Legacy accounts |
|---|---|---|
| How personality is set | 12 `*AiPersonality` fields inside `aiActionSettings` | one group-level `aiPersonality` |
| Group-level `aiPersonality` | **rejected** (any non-null value) | the supported group-level field - optional, omit it to leave the value unchanged |
| `operation: "aiPersonality"` (batch) | **rejected** | the way to do it |
| `operation: "actionSpaceIntensity"` (batch) | the way to do it | **rejected** |

Rejections happen **before any downstream call** and come back as `invalid_params`, which is
**not retryable** - fix the request rather than trying again. Omitting `aiPersonality` on an
edit is always fine: it is read as "no change", not as a value.

> **Naming.** The product calls this **AI personality** (AI 人格) everywhere, and so should you
> when talking to the user. The batch operation's literal value is nevertheless
> `actionSpaceIntensity` and the fields end in `AiPersonality` - send the literal strings
> exactly as written here; they are API values, not product terms.

## The 12 fields

They sit **flat inside `aiActionSettings`**, not nested under the optimization node they belong
to. The node column only tells you which switch they modify.

| Field | Node | SB |
|---|---|---|
| `bidPerformanceAiPersonality` | `bidOptimization` | supported |
| `bidDaypartAiPersonality` | `bidOptimization` | **not supported** |
| `bidAdPlaceAiPersonality` | `bidOptimization` | **not supported** |
| `bidAmazonBusinessAiPersonality` | `bidOptimization` | **not supported** |
| `structPauseProductAiPersonality` | `structOptimization` | **not supported** |
| `structPauseCampaignAiPersonality` | `structOptimization` | **not supported** |
| `budgetDaypartAiPersonality` | `budgetOptimization` | supported |
| `budgetDynamicAiPersonality` | `budgetOptimization` | supported |
| `budgetRedistributeAiPersonality` | `budgetOptimization` | supported |
| `targetHarvestAiPersonality` | `targetOptimization` | supported |
| `negativeTargetAiPersonality` | `targetOptimization` | supported |
| `targetPausedAddAiPersonality` | `targetOptimization` | **not supported** |

**Value: an integer `1`-`5`** (`1` = very conservative … `5` = very aggressive). **`null` is
rejected** (`invalid_params`), and **clearing a single action space is not supported at all** -
to leave one alone, omit the field. Anything else is rejected too, and the error lists **every**
invalid field at once, so read the whole list rather than fixing one and resending.

**Omit = keep unchanged** on a normal edit, and **omit = take the template's value** in template
mode. There is no payload that resets one action space to the group default.

⚠️ **On create, at least one intensity must be set.** An intensity-enabled account creating a
group (template create included) must end up with **at least one applicable field holding a
non-null `1`-`5` after the template is merged in**, or the request is rejected and the error
lists the fields applicable to that `campaignType`. Switch fields such as
`bidPerformanceStatus` do not count, and neither do nulls. So "the user didn't mention
personality" is not a reason to send none of them on a create - ask, or take the
recommendation (below), or use a template that carries them.

**Personality applies to `sponsoredProducts` and `sponsoredBrands` only.**

(SB's list is shorter because personality steers an **AI** decision: an action space SB runs
in Rule mode only - 分时调价 / `bidDaypart`, per `action-space-matrix.md` - has no AI decision
to steer, even though the switch exists. Capability and personality are separate questions.)

⚠️ **For an SB group, sending any of the six unsupported fields is rejected - whatever the
value.** Build the SB payload from the six supported ones and leave the rest out entirely.

**Omitted fields keep their current value on a normal edit.** (Template mode is different - see
below.)

## Setting one group

Put the fields you want in `aiActionSettings` of `save_sp_sb_ai_managed_group`, alongside the
switches:

```json
{
  "request": {
    "profileId": 1234567890123,
    "aiGroupId": 4567,
    "aiActionSettings": {
      "bidPerformanceAiPersonality": 4,
      "targetHarvestAiPersonality": 2
    }
  }
}
```

Do **not** add `aiPersonality` to that object on a per-action-space account - it is rejected
even when the rest of the request is valid.

## Setting many groups, or every action space at once

Batch is a different route: **inside a batch, personality fields in `aiActionSettings` are
rejected**. Use the operation instead.

```json
{
  "request": {
    "profileId": 1234567890123,
    "operation": "actionSpaceIntensity",
    "ids": [4567, 4568],
    "batchParams": { "actionSpaces": ["bidPerformance", "targetHarvest"], "intensity": 3 }
  }
}
```

- `actionSpaces` takes the action-space names **without** the `AiPersonality` suffix:
  `bidDaypart`, `bidPerformance`, `bidAdPlace`, `bidAmazonBusiness`, `structPauseProduct`,
  `structPauseCampaign`, `budgetDaypart`, `budgetDynamic`, `budgetRedistribute`,
  `targetHarvest`, `negativeTarget`, `targetPausedAdd` - or `["all"]` for all 12. Duplicates are
  ignored.
- `intensity` is an integer `1`-`5` and is **required**; `null` is rejected here as it is
  everywhere else. Nothing clears a personality - leaving an action space out of
  `actionSpaces` is how you leave it alone.
- Only the named action spaces are written; the rest of each group is untouched.
- Every id must be an SP/SB group of that profile.

⚠️ **`["all"]` plus any SB group in `ids` fails the whole batch**, because "all" includes the
six action spaces SB does not support. To set everything on a mixed selection, split it: `all`
for the SP ids, and the six supported names for the SB ids.

**To set every action space to the same level, this operation is the only way** - there is no
group-level shortcut on a per-action-space account.

## Template mode

Template mode (`templateId > 0`) works on both account types, with these differences on a
per-action-space account:

- Personality is written **field by field, user value over template value**. `null` is rejected
  here too: **omit a field to take the template's value**. There is no way to send a field
  that overrides the template with "nothing".
- **Template create does not write a group-level `aiPersonality`;** template edit keeps the
  group's current one. The template's own `aiPersonality` and the group-level defaults apply to
  legacy accounts only.
- Passing only personality fields in `aiActionSettings` **still applies the template's
  switches**. An empty `aiActionSettings` object behaves exactly like omitting it.
- For an SB group, the six SB-unsupported personalities in the template are **dropped
  automatically** - you do not have to clean the template first.
- **If a template personality that would be written is not an integer `1`-`5`, the request is
  rejected before anything is written.** Fix the template; re-sending will not help.
- Passing `aiPersonality` in template mode is rejected the same way as outside it.

## When the account check itself is unavailable

Any request carrying `aiPersonality`, any personality field, `operation: "aiPersonality"`,
`operation: "actionSpaceIntensity"`, or `templateId > 0` can fail with
**`capability_unavailable`**. That one **is** retryable: nothing was written, so resend the same
call later unchanged. Do not fall back to the other account type's syntax to "make it work" -
you would be guessing at which account you are on.

## Schedules take a different shape - do not copy the group payload

`save_sp_sb_ai_group_schedule` also carries personality, but **its `aiActionSettings` is not the
group's**. Four differences, each of which silently or loudly breaks a copied payload:

**1. Nested, not flat.** On the group the 12 fields sit directly in `aiActionSettings`. On a
schedule each one goes **inside the node it belongs to** - `bidOptimization`, `structOptimization`,
`budgetOptimization` or `targetOptimization` (the node column in the table above):

```json
"aiActionSettings": {
  "bidOptimization":    { "bidPerformanceAiPersonality": 4 },
  "budgetOptimization": { "budgetDaypartAiPersonality": 3 }
}
```

**2. Weekly schedules reject personality outright.** A `timeType: 2` item carrying any
`*AiPersonality` field fails the whole call:
`Weekly schedules (timeType=2) do not store action space intensity; remove <paths>`. Weekly
schedules inherit personality from the parent group - the same rule that already forbids
`aiPersonality` on them. (Items marked `operation: "delete"` are skipped by this check.)

**3. On a fixed-date schedule, omitting a field is not "keep what it had".** `timeType: 1`
**requires** `aiPersonality`, and that value is the fallback for every action space you do not
give an explicit `*AiPersonality`. So a personality you leave out **falls back to the
schedule's `aiPersonality`** rather than keeping its previous value - the opposite of the
group's edit semantics. Send the full set you want on that schedule, or read it back first and
re-send what should stay.

**4. Some nodes are stripped.** `targetOptimization` and `brandOptimization` (word-list
settings) are not configurable here and are dropped if sent - **except** the
`targetOptimization` personality fields, which are kept.

## Asking the platform what to set: `get_sp_sb_ai_personality_recommendation`

Read-only; it writes nothing. Available on **per-action-space accounts only** - a legacy account
is rejected with `invalid_params`, because it has no per-action-space values to recommend.

It covers **4 of the 12 action spaces**: `bidPerformance`, `bidAdPlace`, `targetHarvest`,
`negativeTarget`. The other eight are not recommended and are left alone.

**Two modes, and the parameters are mutually exclusive:**

**`profileId` is required in both modes**, and `language` is optional in both
(`zh` / `en` / `ja`, default `en`) - it sets the language of `summary`, so pass the language the
user is writing in rather than letting it default.

| Mode | Pass | Returns |
|---|---|---|
| Edit (`aiGroupId > 0`) | `profileId`, `aiGroupId`, optionally `language` - **any other parameter is rejected** | the group's latest stored recommendation (last 7 days) |
| Create (`aiGroupId` omitted or `0`) | `profileId`, plus `campaignIds`, `amazonCampaignIds`, `optimizeType`, `campaignType`; `targetAcos` and `language` optional | a recommendation computed in real time (takes a few seconds) |

In create mode, `campaignIds` and `amazonCampaignIds` must describe the **same** campaigns - get
both from `get_entity_metadata(entity='campaign')` - and `optimizeType` / `targetAcos` should be
the values you are about to pass to `save_sp_sb_ai_managed_group`, or the advice describes a
group you are not creating.

**Read `adviceStatus` before using anything:**

| `adviceStatus` | What it means | What to do |
|---|---|---|
| `VALID` | personalised recommendation | present it and let the user decide |
| `INVALID` | no personalised signal; every value is the default `3` | say it is the default, not a recommendation |
| `NO_ADVICE` | no data; every value is `null` | say there is no recommendation; change nothing |
| `ARCHIVED` | computed from a campaign / ASIN / targetType set the group no longer has | **tell the user it may be out of date before applying it** |

`recommendedIntensities` is keyed by the same field names as `aiActionSettings`, so values can
be copied across unchanged; each is `1`-`5` or `null` (no recommendation for that space). For an
SB group `bidAdPlaceAiPersonality` is simply absent. `summary` is the explanation to show the
user and is `null` for `INVALID` and `NO_ADVICE`. `evidence` says where each number came from:
`I1` this group's own manual operations, `I2` manual operations on campaigns sharing its ASINs,
`I3` / `I4` / `ACCOUNT` peer benchmarks, `P3` the default `3`. It has one item per action space,
keyed by `service`: `bid` -> `bidPerformanceAiPersonality`, `placement` ->
`bidAdPlaceAiPersonality`, `harvest` -> `targetHarvestAiPersonality`, `negation` ->
`negativeTargetAiPersonality`. Keep the items as they are: they are passed back unchanged when
applying.

**Applying it is a separate, user-approved step.** Show the recommendation, get an explicit yes,
then copy the **non-null** values into `aiActionSettings` on `save_sp_sb_ai_managed_group` - the
same `aiGroupId` on edit, the same campaigns and `targetType` on create. Fields you do not
include keep their current values. A recommendation is not an authorisation to write.

In that same save call, put the matching `evidence` items unchanged into `evidence` and set
`isApplyP=true`. If the user applies only some action spaces, pass only the items for those
spaces (each item's `personality` must equal the value you write). Do not set `isApplyP` unless
the user confirmed. `evidence` / `isApplyP` only work on a normal create or edit: not with
`templateId` and not with a batch `operation`, and not on a legacy account. Do not pass
`isPreview`; it is rejected by the schema.

The gateway validates `evidence` before anything is written, so these are hard rules, not advice:

- **At most 4 items, and each `service` at most once** — one per action space (`bid`, `placement`,
  `harvest`, `negation`).
- **`personality` must be an integer `1`-`5`** in every item.
- **An SB group cannot pass `service=placement`** — that action space does not exist for SB, which is
  also why `bidAdPlaceAiPersonality` is absent from an SB recommendation.
- **On edit, an item's `aiGroupId` must be `0` or equal the group's `aiGroupId`.** The recommendation
  always returns `0`, and `0` is treated as "not supplied" — so **leave it alone**. "Correcting" it to
  something else is the one way to get the unchanged evidence rejected.
- **The gateway rebuilds each item from a field whitelist, so three keys never survive as you sent
  them.** `tenantId` and `profileId` are **replaced** with the caller's own — a deliberate guard against
  writing evidence rows under another tenant. `status` is **dropped entirely**: it is not on the whitelist,
  so it is not forwarded at all, and the downstream sets it. Don't try to set any of the three, and
  don't report them back as if they took effect.
