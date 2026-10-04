# Platform Support

NoxInfluencer skills support three platforms. Each has some data availability differences.

## Supported Platforms

| Platform | `--platform` value | Creator ID prefix byte |
|----------|-------------------|----------------------|
| YouTube | `youtube` | `0x01` |
| TikTok | `tiktok` | `0x02` |
| Instagram | `instagram` | `0x03` |

## Data Availability by Platform

| Data Dimension | YouTube | TikTok | Instagram |
|----------------|---------|--------|-----------|
| Search | Full | Full | Full |
| Profile overview | Full | Full | Full |
| NoxScore | Full | Full | Full |
| Audience demographics | Full | Full | Partial |
| Audience authenticity | Full | Full | Limited |
| Content tags | Full | Full | Full |
| Recent content | Full | Full | Full (posts, reels, pics) |
| Cooperation detail | Full | Partial | Partial |
| Brand partnerships | Full | Partial | Limited |
| Pricing data | Full | Partial | Limited |
| Contact/email | Available | Available | Available |
| Video monitoring | Full | Full | Full |
| Brand monitor product signals | YouTube only | Not supported | Not supported |

## Content Type Splits

Different platforms have different content types that affect performance metrics:

- **YouTube**: `normal` (long-form) vs. `shorts`
- **TikTok**: All content treated as short-form
- **Instagram**: `posts`, `reels`, `pics` — metrics may be split by type

## Platform-Specific Notes

- **Null fields**: Some fields may return `null` on certain platforms. This is expected behavior, not a data error. Skills should explain that the value may be unavailable for that platform rather than treating it as a failure.
- **Creator identity fields**: All creator read responses include `creator_id`, `creator_name`, `channel_handle`, `channel_url`, and `social_media`. `channel_url` and `social_media` are enhancement data and may still be empty on some creators or platforms.
- **Audience data**: Instagram audience data may be less granular than YouTube or TikTok.
- **Cooperation data**: Pricing and communication metrics are most complete on YouTube. TikTok and Instagram may have partial or no pricing data.
- **Creator IDs**: Creator search returns the encrypted token as `data.items[].id`; creator read responses return it as `data.creator_id`. Both are stable opaque identifiers generated from the platform and platform-side channel ID, not database record IDs. The same creator always produces the same token. Reuse it directly without decryption or reconstruction.
- **Direct selectors**: The first creator read call may use `--url` or `--platform --channel-id`. Once a response returns `data.creator_id`, switch to that token for follow-up calls.
- **Monitor task identity**: `monitor add-task` and `monitor tasks` may also expose `creator_id`, `creator_name`, `channel_handle`, and `channel_url`. Treat these as best-effort task metadata; nullable fields are not a hard failure.
- **Brand monitor product signals**: Product publication, category, SOV, TAE, PP, promotion matrix, and promotion distinction commands currently support YouTube only. For TikTok or Instagram brand questions, use non-product brand monitor reads or asset lists when schema permits.
