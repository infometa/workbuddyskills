# ae-cli engage-flow node-config validate


Validate and normalize a single node configuration before placing it into a `save_flow` request.

Mapped command: `ae-cli engage-flow node-config validate`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--node-type` | string | Yes | Flow node type |
| `--config` | string | Yes | Node config JSON object encoded as a string |
| `--operation-mode` | string | Yes | Validation mode |

## When To Use

Use this after `engage-flow node-config schema` and before passing a config into `engage-flow flow save`.

The command validates one node config only; it does not validate the full canvas topology. It returns:

- `valid`: whether the candidate config passed validation
- `normalizedConfigObject`: backend-normalized config with defaulted fields
- `errors`: hard validation failures to fix before calling `engage-flow flow save`
- `warnings`: issues that depend on live channel/template/config data

Use `--operation-mode save_flow` for the current exposed MCP protocol. Use `save_submit_flow` only when you intentionally want stricter submit-time checks.

Important current rules:

- `event_trigger` / `event_judge` A segment: use `periodStart`, `periodEnd`, `periodTimeSymbol`; do not use branch-style `delayTime`.
- `event_split_flow` branch segment: use `delayTime`, `delayTimeSymbol`, `targetClusterType`; omit `triggerDefinition` on default branches.
- `event_trigger targetUserType=2` is invalid.
- Push `OBJ_ARRAY.value` must be a JSON array, not a stringified array.
- Push `contentList[].content` should be a JSON array, but a JSON-stringified array is accepted for compatibility.
- Compatible inputs are normalized before validation: apostrophe-prefixed field aliases, case-insensitive property aliases, `enableChannelTouchLimits` booleans, string `"0"`/`"1"` QP relations inside `targetClusterQp`, and `clusterPredictCount: null`.
- Missing defaults such as `clusterPredictCount`, `clusterPredictTime`, `processType`, and `zoneoffset` may be filled in `normalizedConfigObject`.

## Enum Notes

### `--node-type`

Schema-backed node types include:

- `single_trigger`
- `repeat_trigger`
- `event_trigger`
- `feature_judge`
- `event_judge`
- `message_push`
- `wechat_push`
- `webhook_push`
- `time_control`
- `feature_split_flow`
- `event_split_flow`
- `ab_split_flow`
- `exit_flow`

### `--operation-mode`

- `save_flow`
- `save_submit_flow`

## Examples

```bash
ae-cli engage-flow node-config validate \
  --project-id 1 --node-type message_push --operation-mode save_flow --config '{}'
```
