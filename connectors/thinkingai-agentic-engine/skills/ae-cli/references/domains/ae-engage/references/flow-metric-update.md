# Flow metric update

Use this reference when the user asks to configure, replace, or save effect metric settings for a flow canvas.

Mapped CLI command:

- `ae-cli engage-flow metric update`

Mapped capability:

- `engage-flow.metric.update`

## Safety

This is a write command. Only run it when the user explicitly asks to change a flow's metric configuration. Use `--dry-run` first when the final `metric_map` was assembled by an agent.

The backend uses a clean-and-insert update model: omitted existing metric settings may be deleted. Treat `metric_map` as the complete desired metric configuration for the flow, not a partial patch.

## Required input

- `--project-id`
- `--flow-id`
- `--metric-map '<metric_map_json>'`

## Parameter guidance

- `flow_id` is the logical flow ID used by the flow canvas APIs.
- `metric_map` is a JSON object keyed by metric target-user group. Valid first-level keys are exactly:
  - `trigger`
  - `view`
  - `click`
  - `ab_test`
- Preserve first-level group keys exactly. Do not convert `ab_test` to `abTest`.
- Each group value is an array of Hermes metric DTO objects.
- Use DTO field names from `HermesMetricReqDTO`: `metricSettingId`, `metricType`, `metricName`, `metricQp`, `metricWindowNum`, `metricWindowTimeUnit`, `displayName`, `orderId`, `note`, and `metricParams`.
- The CLI boundary accepts snake_case nested DTO fields too, but prefer the native camelCase names above in examples and generated payloads.
- For existing bindings, include `metricSettingId` so Hermes updates that binding instead of treating it as a new binding.
- For preset metrics, use `metricType: 1` and a real `metricName` discovered from `engage-setting common-metric list/get`.
- For custom metrics, use `metricType: 2` plus a complete `metricQp`, `metricWindowNum`, `metricWindowTimeUnit`, and `displayName`; Hermes creates the custom metric name.
- Do not invent metric names, event names, property names, QP structures, or metric-setting IDs. Read the existing flow detail and available metric definitions first, then update the complete desired metric map.

## Examples

Dry-run updating an existing binding:

```bash
ae-cli --dry-run engage-flow metric update \
  --project-id 1 \
  --flow-id flow_id_123 \
  --metric-map '{"trigger":[{"metricSettingId":"setting_1","metricType":1,"metricName":"purchase_count","displayName":"Purchase count","orderId":1}]}'
```

Apply the same update:

```bash
ae-cli engage-flow metric update \
  --project-id 1 \
  --flow-id flow_id_123 \
  --metric-map '{"trigger":[{"metricSettingId":"setting_1","metricType":1,"metricName":"purchase_count","displayName":"Purchase count","orderId":1}]}'
```

Add a custom metric to the `view` group:

```bash
ae-cli engage-flow metric update \
  --project-id 1 \
  --flow-id flow_id_123 \
  --metric-map '{"view":[{"metricType":2,"metricQp":"{\"type\":0,\"eventName\":\"purchase\",\"analysis\":\"A100\",\"filts\":[]}","metricWindowNum":1,"metricWindowTimeUnit":"day","displayName":"Purchase after view","orderId":1}]}'
```

## Common mistakes

- Do not pass `flow_uuid`; this command requires `flow_id`.
- Do not pass `metricId`; `HermesMetricReqDTO` has no `metricId` field. Use `metricSettingId` for an existing binding or `metricName` for a preset metric.
- Do not use arbitrary first-level keys such as `custom`, `ACTION`, or `channel`; use only `trigger`, `view`, `click`, or `ab_test`.
- Do not submit only the group you want to change unless deleting omitted groups is intended.
- Do not use this command to query report data. For report metric details, use `references/flow-metric-detail-report.md`.
