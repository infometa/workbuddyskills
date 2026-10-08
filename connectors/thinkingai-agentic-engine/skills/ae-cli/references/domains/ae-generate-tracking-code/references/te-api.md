# AE Plan Query Capability API

This reference is for `ae-cli` maintainers. Skill users should call CLI commands, not backend APIs.

The code-generation skill reads the current tracking plan through the capability gateway. The CLI
must not call the legacy common-service tracking-program URL directly.

## Authentication

- Header: `cli-token: <token>`
- Do not send `authorization: bearer ...`.
- Do not read `ACCESS_TOKEN` from browser localStorage.

## Query Capability

- Capability: `track.program.query`
- Method: `POST`
- URL: `/api/cli/analysis/v1/capabilities/track.program.query/execute`
- Input:

```json
{ "project_id": 1603 }
```

## Response Shape

The gateway response keeps the standard AE envelope:

```json
{
  "return_code": 0,
  "return_message": "success",
  "showStackMessage": null,
  "data": {
    "projectId": 1603,
    "events": [],
    "eventProps": [],
    "commonEventProps": [],
    "userProps": []
  }
}
```

The CLI normalizes the capability output before converting it to the tracking draft shape.

## Field Mapping to Draft

| AE response field | Draft field |
|---|---|
| `data.events[].eventName` | `events[].event_name` |
| `data.events[].displayName` | `events[].display_name` |
| `data.events[].eventDesc` | `events[].event_desc` |
| `data.events[].eventTag` | `events[].event_tag` |
| `data.events[].props[]` | `events[].properties[]` |
| `data.events[].propInfosOnEvent[]` | `events[].property_infos[]` |
| `data.eventProps[].name` | `event_properties[].name` |
| `data.eventProps[].displayName` | `event_properties[].display_name` |
| `data.eventProps[].desc` | `event_properties[].description` |
| `data.commonEventProps[].name` | `common_event_properties[].name` |
| `data.userProps[].name` | `user_properties[].name` |
| `data.userProps[].updateType` | `user_properties[].update_type` |
| `data.userProps[].propTag` | `user_properties[].prop_tag` |

Empty projects may return a success envelope without `data`; treat that as an empty plan.
