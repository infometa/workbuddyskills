# LinkedIn Community Management Routing Reference

> **Private Beta:** This integration is currently in private beta. Contact [support@maton.ai](mailto:support@maton.ai) to get added to the allowlist.

**App name:** `linkedin-community-management`
**Base URL proxied:** `api.linkedin.com`

## API Path Pattern

```
/linkedin-community-management/rest/{resource}
```

## Required Headers

All requests require these headers in addition to the Authorization header:

| Header | Value |
|--------|-------|
| `Linkedin-Version` | `YYYYMM` (e.g., `202605`) |
| `X-Restli-Protocol-Version` | `2.0.0` |

## Common Endpoints

### Get Current Member Profile
```bash
GET /linkedin-community-management/rest/me
```

### Get Person by ID
```bash
GET /linkedin-community-management/rest/people/(id:{personId})
```

Returns profile fields: `id`, `firstName`, `lastName`, `vanityName`, `localizedFirstName`, `localizedLastName`, `localizedHeadline`, `headline`, `profilePicture`.

Non-connected members may return `{"id": "private"}`.

Use `fields` query param to request a single field:
```bash
GET /linkedin-community-management/rest/people/(id:{personId})?fields=localizedHeadline
```

### Find Organization by Vanity Name
```bash
GET /linkedin-community-management/rest/organizations?q=vanityName&vanityName={name}
```

### Get Organization by ID
```bash
GET /linkedin-community-management/rest/organizations/{orgId}
```

### Get Organization Follower Count
```bash
GET /linkedin-community-management/rest/networkSizes/urn%3Ali%3Aorganization%3A{orgId}?edgeType=COMPANY_FOLLOWED_BY_MEMBER
```

### Find Administered Organizations
```bash
GET /linkedin-community-management/rest/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED
```

### Create a Post
```bash
POST /linkedin-community-management/rest/posts
Content-Type: application/json

{
  "author": "urn:li:organization:{orgId}",
  "commentary": "Post text",
  "visibility": "PUBLIC",
  "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```

### Get Post by URN
```bash
GET /linkedin-community-management/rest/posts/{encoded_postUrn}
```

### Find Posts by Author
```bash
GET /linkedin-community-management/rest/posts?author={encoded_orgUrn}&q=author&count=10&sortBy=LAST_MODIFIED
X-RestLi-Method: FINDER
```

### Update a Post
```bash
POST /linkedin-community-management/rest/posts/{encoded_postUrn}
X-RestLi-Method: PARTIAL_UPDATE
Content-Type: application/json

{"patch": {"$set": {"commentary": "Updated text"}}}
```

### Delete a Post
```bash
DELETE /linkedin-community-management/rest/posts/{encoded_postUrn}
X-RestLi-Method: DELETE
```

### Get Comments on a Post
```bash
GET /linkedin-community-management/rest/socialActions/{encoded_postUrn}/comments
```

### Create a Comment
```bash
POST /linkedin-community-management/rest/socialActions/{encoded_postUrn}/comments
Content-Type: application/json

{
  "actor": "urn:li:organization:{orgId}",
  "object": "urn:li:activity:{activityId}",
  "message": {"text": "Comment text"}
}
```

### Delete a Comment
```bash
DELETE /linkedin-community-management/rest/socialActions/{encoded_postUrn}/comments/{commentId}?actor={encoded_actorUrn}
```

### Create a Reaction
```bash
POST /linkedin-community-management/rest/reactions?actor={encoded_actorUrn}
Content-Type: application/json

{"root": "urn:li:activity:{activityId}", "reactionType": "LIKE"}
```

### Delete a Reaction
```bash
DELETE /linkedin-community-management/rest/reactions/(actor:{encoded_actorUrn},entity:{encoded_entityUrn})
```

### Follower Statistics (Lifetime)
```bash
GET /linkedin-community-management/rest/organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity={encoded_orgUrn}
```

### Page Statistics
```bash
GET /linkedin-community-management/rest/organizationPageStatistics?q=organization&organization={encoded_orgUrn}
```

### Share Statistics
```bash
GET /linkedin-community-management/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={encoded_orgUrn}
```

## Notes

- All URNs in URL paths and query parameters must be URL-encoded (`:` -> `%3A`)
- `Linkedin-Version` header is mandatory (format: `YYYYMM`, e.g., `202605`). LinkedIn keeps roughly the last ~12 monthly versions active and returns HTTP 426 `NONEXISTENT_VERSION` for retired or future-dated versions — pin to a recent month and bump periodically
- Organization endpoints require admin role for full data; non-admins get limited fields
- Statistics endpoints require `ADMINISTRATOR` role on the organization
- Post content types: text, image, video, document, article, carousel (sponsored only)
- Reaction types: `LIKE`, `PRAISE`, `EMPATHY`, `INTEREST`, `APPRECIATION`, `ENTERTAINMENT`
- Pagination uses `start` + `count` parameters
- The `X-RestLi-Method` header is required for FINDER, PARTIAL_UPDATE, BATCH_GET, and DELETE operations

## Resources

- [LinkedIn Community Management API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview)
- [Posts API Reference](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Organization Lookup](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations/organization-lookup-api)
