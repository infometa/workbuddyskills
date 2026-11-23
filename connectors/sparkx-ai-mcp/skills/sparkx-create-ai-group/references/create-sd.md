# Create SD managed group - `create_sd_ai_managed_group`

Creates a new **Sponsored Display** AI managed group. SD-only - for SP/SB use
`save_sp_sb_ai_managed_group` (see `create-sp-sb.md`).

## Parameters

| Field | Type | Required | Notes |
|---|---|---|---|
| `profileId` | long | **Yes** | Shop ID, from `get_user_authorized_context` |
| `smartCreationName` | string | **Yes** | Group name. Unique per profile; leading/trailing spaces are trimmed |
| `campaignIds` | int[] | **Yes** | SD campaigns (max 1000). Use each campaign's internal `campaignId` (int) - **not** `amazonCampaignId` (the long Amazon string). Archived campaigns are dropped downstream |
| `budget` | number | No | Total budget. Only applied when `budgetChange=true` |
| `budgetChange` | boolean | No | `true` = apply `budget`, `false`/omit = ignore budget |
| `acos` | number | No | Target ACOS on the **x100 scale** - user's `25%` -> send `25` (not `0.25`) |
| `optimizeType` | int | No | `1`=drive growth, `2`=maintain stability |
| `status` | int | No | AI status at creation: **`0`=off, `1`=on only** (`2`=cancelled is a lifecycle state, not a valid create input). Defaults to `1` when omitted |
| `budgetDynamicStatus` | int | No | **Not supported on SD — send `0` or omit it.** A non-zero value is rejected outright (`budgetDynamicStatus is not supported for SD (Sponsored Display)`). Historical values: `0`=off, `1`=on |
| `numType` | int | No | **Do not send for SD creation.** It is only meaningful with the unsupported dynamic-budget switch |
| `num` | number | No | **Do not send for SD creation.** It is only meaningful with the unsupported dynamic-budget switch |
| `campaignNameSign` | int | No | Campaign-name label: `0`=off, `1`=on |
| `targetHarvestStatus` | int | No | `0`=off, `1`=on, `2`=on with exact negation in the source ad group |
| `budgetRedistributeStatus` | int | No | Budget redistribute: `0`=off, `1`=on |
| `aiPersonality` | int | No | AI personality, `1`-`5` |

Only `profileId`, `smartCreationName`, `campaignIds` are required. Everything else
takes a platform default if omitted - only send the optional fields the user
actually wants to set.

**`status` defaults to `1` (on) when omitted** - same as SP/SB's `aiStatus`, with or
without a template. It is never inherited from the template (template `status` means
active/paused/archived, not AI on/off). Omit it (or send `1`) to start the group; send `0`
when the user asked for it not to start.

## Coupled fields (send together or not at all)

- **Budget**: `budget` does nothing unless `budgetChange=true`. If the user gives a
  budget, send both.
- **Dynamic budget is unavailable for SD creation**: omit `budgetDynamicStatus`, `numType`,
  and `num`. A non-zero `budgetDynamicStatus` is rejected; sending its companion values
  cannot enable the feature.

## Example - create an SD group the user asked not to start yet

(`status: 0`. For the normal case omit `status` or send `1`, and say in the preview that the
group starts optimizing immediately.)

```json
{
  "profileId": 3721212165742,
  "smartCreationName": "SD-Retargeting-US",
  "campaignIds": [45444534, 45444533],
  "acos": 30,
  "optimizeType": 1,
  "status": 0,
  "budget": 50,
  "budgetChange": true
}
```

Then verify with the full-signature read
`get_entity_metadata(profileIds=[3721212165742], entity='aiGroup',
filters={"aiGroupName": {"like": "%SD-Retargeting-US%"}}, userContext='verify created group')`,
exact-match the name in the results (the `aiGroupName` filter is a substring `like`),
and re-read `entity='campaign'` to confirm each campaign's `aiGroupId` now points at
the new group.
