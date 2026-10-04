# ae-cli engage-flow flow manage


Batch manage flow status or review actions.

Mapped command: `ae-cli engage-flow flow manage`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--action` | string | Yes | action type |
| `--flow-list` | json | No | Review list JSON array |
| `--pause-flow-list` | json | No | pause list JSON array |
| `--flow-id-list` | json | No | Flow ID JSON array |
| `--reason` | string | No | review reason |

## Enum Notes

### `--action`

- `approve`: review approved, requires `--flow-list`
- `deny`: review denied, requires `--flow-list`
- `cancel`: cancel review, requires `--flow-list`
- `pause`: pause flow, requires `--pause-flow-list`
- `recover`: resume flow, requires `--flow-id-list`
- `end`: end flow, requires `--flow-id-list`

## JSON Parameter Notes

### `--flow-list`

Used for review actions such as `approve`, `deny`, and `cancel`. Each array item is an object:

| Field | Type | Required | Description |
|------|------|------|------|
| `flowUuid` | string | Yes | Flow UUID |
| `reason` | string | No | per-item review reason |

Examples: 

```json
[
  { "flowUuid": "flow_uuid_1", "reason": "approve by ops" }
]
```

### `--pause-flow-list`

Used for the `pause` action. Each array item is an object:

| Field | Type | Required | Description |
|------|------|------|------|
| `flowId` | string | Yes | Flow ID |
| `flowInstanceProcessType` | number | No | flow instance processing mode |

`flowInstanceProcessType` enum:

- `1`: normal, normal pause
- `2`: force exit, force-exit the instance

Examples: 

```json
[
  { "flowId": "flow_id_1", "flowInstanceProcessType": 1 }
]
```

### `--flow-id-list`

Used for batch operations by ID such as `recover` and `end`:

```json
["flow_id_1", "flow_id_2"]
```

## Safety Constraints

This command is a **write operation** and changes the flow status.

Different `action` values require different parameters:

- `approve` / `deny` / `cancel`: must include `--flow-list`
- `pause`: must include `--pause-flow-list`
- `recover` / `end`: must include `--flow-id-list`

## Examples

```bash
ae-cli engage-flow flow manage --project-id 1 --action end --flow-id-list '["flow_id_1"]'
```
