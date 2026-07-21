# Google Apps Script Routing Reference

**App name:** `google-apps-script`
**Base URL proxied:** `script.googleapis.com`

## API Path Pattern

```
/google-apps-script/v1/{resource}
```

## Common Endpoints

### Create Project
```bash
POST /google-apps-script/v1/projects
Content-Type: application/json

{"title": "My Script", "parentId": "{optional_drive_file_id}"}
```

### Get Project
```bash
GET /google-apps-script/v1/projects/{scriptId}
```

### Get Project Content
```bash
GET /google-apps-script/v1/projects/{scriptId}/content
```

With specific version:
```bash
GET /google-apps-script/v1/projects/{scriptId}/content?versionNumber=1
```

### Update Project Content
```bash
PUT /google-apps-script/v1/projects/{scriptId}/content
Content-Type: application/json

{
  "files": [
    {"name": "appsscript", "type": "JSON", "source": "{...manifest...}"},
    {"name": "Code", "type": "SERVER_JS", "source": "function main() {}"}
  ]
}
```

### Get Project Metrics
```bash
GET /google-apps-script/v1/projects/{scriptId}/metrics?metricsGranularity=DAILY
```

### Create Version
```bash
POST /google-apps-script/v1/projects/{scriptId}/versions
Content-Type: application/json

{"description": "v1.0"}
```

### List Versions
```bash
GET /google-apps-script/v1/projects/{scriptId}/versions
```

### Get Version
```bash
GET /google-apps-script/v1/projects/{scriptId}/versions/{versionNumber}
```

### Create Deployment
```bash
POST /google-apps-script/v1/projects/{scriptId}/deployments
Content-Type: application/json

{"versionNumber": 1, "description": "Production"}
```

### List Deployments
```bash
GET /google-apps-script/v1/projects/{scriptId}/deployments
```

### Get Deployment
```bash
GET /google-apps-script/v1/projects/{scriptId}/deployments/{deploymentId}
```

### Update Deployment
```bash
PUT /google-apps-script/v1/projects/{scriptId}/deployments/{deploymentId}
Content-Type: application/json

{"deploymentConfig": {"scriptId": "...", "versionNumber": 2, "description": "Updated"}}
```

### Delete Deployment
```bash
DELETE /google-apps-script/v1/projects/{scriptId}/deployments/{deploymentId}
```

### List Processes
```bash
GET /google-apps-script/v1/processes
GET /google-apps-script/v1/processes?pageSize=10
```

### List Script Processes
```bash
GET /google-apps-script/v1/processes:listScriptProcesses?scriptId={scriptId}
```

### Run Function
```bash
POST /google-apps-script/v1/scripts/{scriptId}:run
Content-Type: application/json

{"function": "myFunction", "parameters": ["arg1"], "devMode": false}
```

## Notes

- `scriptId` is the Google Drive file ID of the Apps Script project
- `updateContent` replaces ALL files; always include the `appsscript` manifest
- File types: `SERVER_JS` (code), `HTML` (HTML files), `JSON` (manifest only)
- Versions are immutable; deploy a specific version number
- `scripts.run` requires an "API Executable" deployment
- Metrics require `metricsGranularity` parameter: `DAILY` or `WEEKLY`
- Pagination uses `pageSize` + `pageToken`/`nextPageToken`

## Resources

- [Apps Script API Reference](https://developers.google.com/apps-script/api/reference/rest)
- [Managing Deployments](https://developers.google.com/apps-script/api/how-tos/manage-deployments)
- [Executing Functions](https://developers.google.com/apps-script/api/how-tos/execute)
