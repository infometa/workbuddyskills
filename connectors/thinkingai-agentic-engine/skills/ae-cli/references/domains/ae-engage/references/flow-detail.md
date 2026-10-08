# ae-cli engage-flow flow get


Query flow details.

Mapped command: `ae-cli engage-flow flow get`

## Response shape

The flow detail is under `data.flow`. Every response key is snake_case, for example
`data.flow.mapping_status`, `data.flow.version_type`, and `data.flow.node_list[].type`.

For custom-audience nodes, `node_list[].config` remains a JSON string. Parse it and read
`targetDefinitionRequest`, `definitionStatus`, and optional
`definitionUnavailableReason`. Branch audiences use the same fields inside
`branchList[]`. Stored execution QP is hidden. Reuse `targetDefinitionRequest` when
building the next flow save request.

Top-level `completion_indicators` and `current_flow_completion_indicators` are exposed
as arrays. Each indicator uses semantic `event_definition`; stored `event` execution
QP is removed. Check `completion_indicators_definition_status` and
`current_flow_completion_indicators_definition_status` before reusing them. A
non-`AVAILABLE` status may also include the corresponding
`*_definition_unavailable_reason`.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--flow-uuid` | string | Yes | Flow UUID |

## Common enums in the response

### `data.flow.status`

- `0`: `DRAFT`
- `1`: `WAITING`
- `2`: `RUNNING`
- `3`: `PENDING`
- `4`: `COMPLETE`

### `data.flow.mapping_status`

- `0`: `DRAFT`
- `1`: `APPROVE`
- `2`: `DENY`
- `3`: `REGISTERING`
- `4`: `REGISTER_FAIL`
- `5`: `WAITING`
- `6`: `RUNNING`
- `7`: `PENDING`
- `8`: `COMPLETE`

### `data.flow.version_type`

- `0`: history version
- `1`: current version
- `2`: update-content version
- `3`: new version
- `4`: test version

### `data.flow.entry_trigger_type`

- `0`: scheduled single trigger
- `1`: scheduled recurring trigger
- `2`: event trigger

### `data.flow.node_list[].type`

Common node types include:

- `single_trigger`
- `repeat_trigger`
- `event_trigger`
- `feature_judge`
- `event_judge`
- `message_push`
- `wechat_push`
- `webhook_push`
- `config_push`
- `tag`
- `time_control`
- `feature_split_flow`
- `event_split_flow`
- `trigger_prop_split_flow`
- `percent_split_flow`
- `ab_split_flow`
- `race_split_flow`
- `exit_flow`

## Examples

```bash
ae-cli engage-flow flow get --project-id 1 --flow-uuid flow_uuid_123
```
