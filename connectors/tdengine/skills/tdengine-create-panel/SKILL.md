---
name: tdengine-create-panel
description: Use when creating a persisted TDengine panel from known or publicly discoverable element, attribute, query, template, and presentation data.
version: "0.6.0"
author: "TDengine"
---

# TDengine Create Panel

## Tool Routing

When this skill is loaded, `create_panel` is the required creation route.
Use this skill to discover the public inputs, build the complete structured
request, and call `create_panel` directly. Do not call `add_panel` first, use
it to draft parameters, or retry with it after a structured validation error.
`add_panel` is only for callers that do not have this skill loaded and
therefore need the server-side AI to interpret an unstructured request.

Use the deterministic public `create_panel` tool when the request can be built
from user input and public MCP discovery. Read the live tool schema first. It
is authoritative when deployed behavior differs from these references.

## Workflow

```text
discover -> choose direct or template route -> choose type -> load reference
-> build -> validate -> call create_panel once -> confirm persisted result
```

1. Reuse supplied IDs and names. Discover missing elements, PanelTemplates,
   attributes, dashboards, events, and analyses with public MCP resources and
   read tools. Never invent an ID or attribute expression.
2. Choose a route before building the request:
   - Direct: supply the positive owner `element_id` and omit `template_id`.
   - Template: keep the same owner `element_id`, supply a positive
     PanelTemplate-valued `template_id`, and send the complete effective panel
     definition. A template ID does not replace `name`, `panel_type`, bindings,
     or type validation.
3. Choose exactly one of the 14 supported types and load
   [panel-types.md](references/panel-types.md).
4. Build bindings and windows with
   [panel-attributes.md](references/panel-attributes.md).
5. Start from a complete request in [examples.md](references/examples.md),
   then change only values established by discovery or the user.

## Route Guarantees

For the template route, a search result is only a candidate when its public
type is `PANEL_TEMPLATE`. The tool's element-scoped membership check is
authoritative. The ordinary element-panel create operation stores differences
from the selected baseline; public read-back merges the PanelTemplate and the
request, with request values taking precedence. The tool verifies that
relationship after creation and rolls back a newly created panel if it cannot
be confirmed.

Never substitute an ElementTemplate ID, `other_element_template_id`, or a
panel instance's `templateId` for `template_id`.

## Success

Progress notifications are advisory. Report success only when the final tool
result contains `persisted: true`, a positive `panel_id`, the requested
`panel_type`, and the owner `element_id`.

Return the exact `panel_url` from the final tool result as the clickable panel
link. Do not reconstruct its host, port, path, or hierarchy query parameters.
Copy the URL verbatim from its scheme through its final character,
including the complete query string. Hierarchy parameters such as
`?ids=/1/...` are required routing data: never omit, shorten, decode,
summarize, or move them outside the clickable URL. A path-only URL is invalid
when the returned URL contains query parameters.
Treat `content[type=resource_link].uri` as an indivisible URL and return it
without editing. Its value must exactly equal `panel_url`; report a tool
contract error instead of choosing between two different values.

- Direct success has `creation_route=direct` and no returned template field.
- Template success has `creation_route=template` and the exact string-safe
  `template_id` that was requested.

Surface validation, permission, conflict, cancellation, and upstream errors.
Do not retry with a different creation tool or call a private endpoint.
