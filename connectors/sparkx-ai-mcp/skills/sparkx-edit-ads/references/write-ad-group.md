# Ad group state

`adGroup + updateStatus` changes SP/SB/SD ad groups and executes directly, including
`state: "archived"`. The platform does not issue a confirm token for this route, so obtain
the user's approval before an irreversible archive.

Use `request.data` with 1-200 items. Every item requires:

| Field | Rule |
|---|---|
| `id` | internal `adGroupId` from metadata, not `amazonAdGroupId` |
| `profileId` | authorized profile owning the row |
| `campaignType` | exact metadata value: `sponsoredProducts` / `sponsoredBrands` / `sponsoredDisplay` |
| `state` | exact lowercase `enabled` / `paused` / `archived` |

Before writing, the server verifies the ad group and parent campaign, rejects configured
`archived` rows and `processStatus: Archived/Ended`, and refreshes `adGroupName` and
`defaultBid` because the downstream status endpoint requires them. A real zero bid is valid;
a missing or unparsable bid is not replaced with zero. An empty `processStatus` may be valid,
but a failed or incomplete metadata lookup rejects the whole batch.

Several states can be mixed in one call. If any target is already archived, the whole batch is
rejected before writing. The read and write are not one transaction; read the ad groups back
and report actual resulting states.
