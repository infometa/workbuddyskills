# YouTube Reporting Routing Reference

**App name:** `youtube-reporting`
**Base URL proxied:** `youtubereporting.googleapis.com`

## API Path Pattern

```
/youtube-reporting/v1/{resource}
```

## Common Endpoints

### List Report Types
```bash
GET /youtube-reporting/v1/reportTypes
```

With pagination:
```bash
GET /youtube-reporting/v1/reportTypes?pageSize=10&pageToken={nextPageToken}
```

### List Jobs
```bash
GET /youtube-reporting/v1/jobs
```

Include system-managed:
```bash
GET /youtube-reporting/v1/jobs?includeSystemManaged=true
```

### Get Job
```bash
GET /youtube-reporting/v1/jobs/{jobId}
```

### Create Job
```bash
POST /youtube-reporting/v1/jobs
Content-Type: application/json

{
  "reportTypeId": "channel_basic_a3",
  "name": "Daily User Activity"
}
```

### Delete Job
```bash
DELETE /youtube-reporting/v1/jobs/{jobId}
```

### List Reports for a Job
```bash
GET /youtube-reporting/v1/jobs/{jobId}/reports
```

With date filters:
```bash
GET /youtube-reporting/v1/jobs/{jobId}/reports?startTimeAtOrAfter=2025-04-01T00:00:00Z&startTimeBefore=2025-05-01T00:00:00Z
```

### Get Report
```bash
GET /youtube-reporting/v1/jobs/{jobId}/reports/{reportId}
```

## Notes

- Reports are generated daily as CSV files; first report available ~24 hours after job creation
- Each report covers a single day (startTime to endTime = 24 hours)
- Use `downloadUrl` from report metadata to download the CSV file
- Only one job per `reportTypeId` allowed (409 on duplicate)
- System-managed jobs cannot be created or deleted (403)
- Pagination uses `pageSize` + `pageToken`/`nextPageToken`
- Common report types: `channel_basic_a3` (user activity), `channel_demographics_a1`, `channel_traffic_source_a3`, `channel_device_os_a3`

## Resources

- [YouTube Reporting API Reference](https://developers.google.com/youtube/reporting/v1/reference/rest)
- [Bulk Reports Documentation](https://developers.google.com/youtube/reporting/v1/reports)
- [Report Types](https://developers.google.com/youtube/reporting/v1/report_types)
