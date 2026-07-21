# Google Tag Manager Routing Reference

**App name:** `google-tag-manager`
**Base URL proxied:** `tagmanager.googleapis.com`

## API Path Pattern

```
/google-tag-manager/tagmanager/v2/{resource-path}
```

Resources follow a hierarchical pattern:
```
accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/{resource}/{resourceId}
```

## Common Endpoints

### List Accounts
```bash
GET /google-tag-manager/tagmanager/v2/accounts
```

### Get Account
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}
```

### List Containers
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers
```

### List Workspaces
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces
```

### List Tags
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/tags
```

### Create Tag
```bash
POST /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/tags
Content-Type: application/json

{
  "name": "My Tag",
  "type": "html",
  "parameter": [{"type": "template", "key": "html", "value": "<script>...</script>"}],
  "firingTriggerId": ["{triggerId}"]
}
```

### Update Tag
```bash
PUT /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/tags/{tagId}
Content-Type: application/json

{...full resource body with fingerprint...}
```

### Delete Tag
```bash
DELETE /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/tags/{tagId}
```

### List Triggers
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/triggers
```

### Create Trigger
```bash
POST /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/triggers
Content-Type: application/json

{"name": "Page View", "type": "pageview"}
```

### List Variables
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/{workspaceId}/variables
```

### List Environments
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/environments
```

### List Version Headers
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/version_headers
```

### Publish Version
```bash
POST /google-tag-manager/tagmanager/v2/accounts/{accountId}/containers/{containerId}/versions/{versionId}:publish
```

### List User Permissions
```bash
GET /google-tag-manager/tagmanager/v2/accounts/{accountId}/user_permissions
```

## Notes

- All paths include the `tagmanager/v2` prefix after the app name
- Updates (PUT) require the full resource body including `fingerprint` for concurrency control
- Common tag types: `html`, `gaawc` (GA4 Config), `gaawe` (GA4 Event)
- Common trigger types: `pageview`, `domReady`, `customEvent`, `click`, `formSubmit`
- Common variable types: `v` (Data Layer), `j` (JS Variable), `c` (Constant), `k` (Cookie)
- Special actions use colon syntax: `:publish`, `:create_version`, `:revert`, `:sync`
- Built-in trigger ID `2147479553` = "All Pages"

## Resources

- [Google Tag Manager API Reference](https://developers.google.com/tag-platform/tag-manager/api/reference/rest)
- [GTM API v2 Guide](https://developers.google.com/tag-platform/tag-manager/api/v2)
