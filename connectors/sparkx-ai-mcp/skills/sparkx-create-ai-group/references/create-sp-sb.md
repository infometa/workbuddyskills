# Create SP/SB managed group - `save_sp_sb_ai_managed_group` (create mode)

Creates a **Sponsored Products** or **Sponsored Brands** AI managed group. All
arguments go inside a single `request` object. **Create mode is triggered by leaving
`aiGroupId` empty (omit it or set `0`)** - a positive `aiGroupId` means edit, which
belongs to the `sparkx-edit-ai-group` skill.

The `aiAutomation` **you pass is AI mode only**. Use `aiActionSettings.xxxStatus` for the
action-space on/off switch. When that action space has a corresponding `aiAutomation` mode
field, set it to `0` (AI); never set it to `1` (Rule/RBA) - a `1` is rejected. Rule
condition/action configs cannot be written through your parameters (they *can* be read -
see `sparkx-query-entity-metadata`).

**Template-based creation is supported**: pass `templateId` (>0) and the template's config
becomes the baseline, with any field you send explicitly overriding it. Read templates first
with `get_ai_group_template`; for a system preset also pass `isSystemTemplate=1`. Archived
templates (`status=2`) are rejected. **The one exception to "AI mode only"**: if you don't
pass `aiAutomation`, the template's automation rules are carried over as-is, including
Rule-mode rules (`status=1`) with their condition/action - tell the user in the preview.
One hard restriction: a template whose rule 4 / rule 5 is bound to specific campaigns and
ad groups (`isSelf=2`, rule enabled) is rejected. See the main SKILL.md section "Creating
from a template", and [`template-guide.md`](template-guide.md) for recommending one by
campaign purpose.

**If you send no `aiActionSettings` at all, the server fills in ad-type-appropriate
defaults** (an SB-specific default set for `sponsoredBrands`, otherwise the SP set). That's
usually what you want for a basic create - don't hand-build a full object just to look
thorough. It also means "I didn't send it" is not the same as "it's off": read the group back
if the user needs to know what's active.

## Required for create

| Field | Type | Notes |
|---|---|---|
| `profileId` | long | Shop ID |
| `aiGroupName` | string | Unique per profile |
| `acos` | number | Target ACOS on the **x100 scale** - the user's `25%` is sent as **`25`** (not `0.25`). Must be `> 0` |
| `targetType` | int | `1`=drive growth, `2`=maintain stability, `3`=volume, `4`=legacy growth |
| `campaignType` | string | `"sponsoredProducts"` or `"sponsoredBrands"` |

## Common optional fields

| Field | Type | Notes |
|---|---|---|
| `aiStatus` | int | `0`=off, `1`=on. **Omit it** - the server fills in `1` and the group starts optimizing. Send `0` only when the user asked for it not to start. A template never sets it |
| `campaignIds` | int[] | Campaigns to include (auto-increment IDs). Omit to create an empty group |
| `campaignNameSign` | int | Campaign-name label: `0`=off, `1`=on |
| `aiPersonality` | int | `1`-`5`; **must be >=3 when `targetType=3` (volume/冲量)** (front-end rule - MCP won't enforce it). ⚠️ **Rejected on accounts that set personality per action space** - send the `*AiPersonality` fields inside `aiActionSettings` instead; see [`ai-personality.md`](ai-personality.md) |
| `preAddCampaignNums` | int | Pre-add campaign count |
| `aiAutomation` | object | AI/Rule mode fields: create may use only `0`=AI; never `1`=Rule/RBA. See field-reference |
| `aiActionSettings` | object | Supported action-space config (bid / struct / budget / target optimization). See field-reference |

Only send `aiAutomation` / `aiActionSettings` fields the user wants to change from
platform defaults - both are large flattened objects and you rarely need most of it
for a basic create. Exact field names are in `field-reference.md`.

## Action-space coupling rules

Enabling an action-space switch usually requires sending its companion fields (dynamic
budget -> numType+num; ranges -> min/max with min <= max). Word-list settings are not
supported and must not be sent. The supported coupling rules are in the shared
[`coupling-rules.md`](coupling-rules.md) - read it before enabling any `aiActionSettings`
switch.

## SP vs SB differences (SB is not SP)

Some capabilities exist only for SP. On an SB group these are now **rejected outright**, not
silently ignored - the call fails with `X is not supported for sponsoredBrands; remove it or
set to 0` (or `set to null` for numeric range fields), and **every** offending field is
listed at once. Nothing is applied.

SP-only `aiActionSettings` fields (complete list as enforced):

| Group | Fields |
|---|---|
| B2B bidding | `bidAmazonBusinessStatus`, `btbRangeStatus`, `btbMin`, `btbMax` |
| Bid dayparting | `bidDaypartStatus` |
| Strict ACOS | `bidPerformanceStrictAcosStatus` |
| Placement bidding | `bidAdPlaceStatus`, `bidAdPlaceRangeStatus`, `tosMin`, `tosMax`, `pdpMin`, `pdpMax`, `rosMin`, `rosMax` |
| Struct optimization | `structPauseProductStatus`, `structPauseCampaignStatus` |

Sending `0` (or `null` for the numeric ones) is accepted - only an *enabled* value trips the
check. Best practice is to omit them entirely on SB.

**Templates are not rejected on create**: creating an SB group from a template that has
any of these SP-only switches on succeeds - the server turns them off, and the response
summary lists the switches that were turned off; tell the user which parts of the template
won't take effect. (If
you send `aiActionSettings` with `templateId` on create, the template's action-space config is
skipped and your values go through the check above.)

When the user is on SB and asks for one of these, tell them it isn't available for
Sponsored Brands rather than sending it and letting the whole call fail. The full "which capability is
supported (AI / Rule / none) per SP / SB / SD" matrix is in
[`action-space-matrix.md`](action-space-matrix.md) - check it before enabling any
action-space switch (notably: **SB's BidDaypart has no AI mode**, and
`budgetRedistribute` / `bidAmazonBusiness` are `noRule` - never attach Rule configs).

## Example - create a basic SP group

`aiStatus` is omitted, so the group is created with AI on and starts optimizing
immediately. Say that in the preview before calling this.

```json
{
  "request": {
    "profileId": 3721212165742,
    "aiGroupName": "SP-Core-Keywords-US",
    "campaignType": "sponsoredProducts",
    "acos": 25,
    "targetType": 1,
    "campaignIds": [45444534]
  }
}
```

**Same group, but the user asked not to start it yet** - add `aiStatus: 0`:

```json
{
  "request": {
    "profileId": 3721212165742,
    "aiGroupName": "SP-Core-Keywords-US",
    "campaignType": "sponsoredProducts",
    "acos": 25,
    "targetType": 1,
    "aiStatus": 0,
    "campaignIds": [45444534]
  }
}
```

`campaignIds` uses each campaign's internal `campaignId` (int) - **not**
`amazonCampaignId` (the long Amazon string).

Success returns `data.result.aiGroupId`. Then verify with the full-signature read
`get_entity_metadata(profileIds=[3721212165742], entity='aiGroup',
filters={"aiGroupName": {"like": "%SP-Core-Keywords-US%"}}, userContext='verify created group')`
and exact-match the name in the results (the filter is a substring `like`).

> Reminder: a group created with `aiStatus=0` **reads back as `0`** ("never turned on"),
> not as `2`. Both mean AI is not running; the distinction only matters because of the
> two notes below.
>
> ⚠️ **`2` is a read-side value only. Never send it back into a write.** The write
> side takes `0` (off) and `1` (on); `2` is what the read side uses to distinguish
> "was turned off" from "never turned on" (`0`). Echoing a group you just read into an
> edit therefore carries a value the write contract does not define, and nothing in the
> tool layer validates it. Build the write payload from what you intend - `0` or `1` -
> not from the row you read. Same trap as `isActive` on schedules.
>
> ⚠️ **A group that was never turned on does not stay at `0`.** Known downstream
> behaviour: a group reading `aiStatus=0` is stored as `aiStatus=2` after **any** edit,
> even one that never mentions `aiStatus`. So a later read showing `2` does not prove
> someone turned AI off - it may only mean the group was edited once. Both values mean
> AI is not running; don't narrate `0` -> `2` to the user as a change they made.
