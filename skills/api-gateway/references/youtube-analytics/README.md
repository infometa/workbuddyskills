# YouTube Analytics Routing Reference

**App name:** `youtube-analytics`
**Base URL proxied:** `youtubeanalytics.googleapis.com`

## API Path Pattern

```
/youtube-analytics/v2/{resource}
```

## Common Endpoints

### Query Reports
```bash
GET /youtube-analytics/v2/reports?ids=channel==MINE&startDate=2025-01-01&endDate=2025-01-31&metrics=views,likes,comments
```

With dimensions and sorting:
```bash
GET /youtube-analytics/v2/reports?ids=channel==MINE&startDate=2025-01-01&endDate=2025-03-31&metrics=views,estimatedMinutesWatched&dimensions=day&sort=-views&maxResults=10
```

Monthly aggregation (endDate must align to 1st of month):
```bash
GET /youtube-analytics/v2/reports?ids=channel==MINE&startDate=2024-01-01&endDate=2024-12-01&metrics=views,subscribersGained&dimensions=month
```

### List Groups
```bash
GET /youtube-analytics/v2/groups?mine=true
```

### Get Groups by ID
```bash
GET /youtube-analytics/v2/groups?id={group_id}
```

### Create Group
```bash
POST /youtube-analytics/v2/groups
Content-Type: application/json

{
  "snippet": {"title": "My Group"},
  "contentDetails": {"itemType": "youtube#video"}
}
```

### Update Group
```bash
PUT /youtube-analytics/v2/groups
Content-Type: application/json

{
  "id": "{group_id}",
  "snippet": {"title": "Updated Title"},
  "contentDetails": {"itemType": "youtube#video"}
}
```

### Delete Group
```bash
DELETE /youtube-analytics/v2/groups?id={group_id}
```

### List Group Items
```bash
GET /youtube-analytics/v2/groupItems?groupId={group_id}
```

### Add Item to Group
```bash
POST /youtube-analytics/v2/groupItems
Content-Type: application/json

{
  "groupId": "{group_id}",
  "resource": {"kind": "youtube#video", "id": "{video_id}"}
}
```

### Remove Item from Group
```bash
DELETE /youtube-analytics/v2/groupItems?id={group_item_id}
```

## Report Parameters

**Required:** `ids`, `startDate`, `endDate`, `metrics`

**Optional:** `dimensions`, `filters`, `sort`, `maxResults`, `startIndex`, `currency`

**Common Metrics:** `views`, `likes`, `comments`, `shares`, `estimatedMinutesWatched`, `averageViewDuration`, `subscribersGained`, `subscribersLost`

**Common Dimensions:** `day`, `month`, `country`, `video`, `deviceType`, `operatingSystem`

## Notes

- Dates use `YYYY-MM-DD` format
- `month` dimension requires `endDate` aligned to 1st of month
- `ids=channel==MINE` targets authenticated user's channel
- Groups support up to 500 items of a single type: `youtube#video`, `youtube#playlist`, `youtube#channel`, `youtubePartner#asset`
- Only group title can be updated; use groupItems methods for membership
- Groups pagination uses `pageToken`; reports use `startIndex` + `maxResults`

## Resources

- [YouTube Analytics API Reference](https://developers.google.com/youtube/analytics/reference)
- [Channel Reports](https://developers.google.com/youtube/analytics/channel_reports)
- [Metrics Reference](https://developers.google.com/youtube/analytics/metrics)
