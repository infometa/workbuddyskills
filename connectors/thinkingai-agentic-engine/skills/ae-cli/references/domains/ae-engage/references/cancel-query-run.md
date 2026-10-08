# Cancel a running Engage query or export

Cancel asynchronous Engage work by the Capability Gateway run ID.

Mapped command:

```bash
ae-cli engage-query query cancel --run-id <run_id>
```

Mapped capability: `engage-query.query.cancel`

## Input

| Field | Type | Required | Description |
|------|------|------|------|
| `run_id` | string | Yes | Run ID returned by an asynchronous query or export capability |
| `reason` | string | No | Optional cancellation reason |

## Safety Constraints

This command is a **write operation**. Use only the `run_id` returned by the asynchronous
query/export lifecycle; a report `request_id` is not accepted.

## Example

```bash
ae-cli engage-query query cancel \
  --run-id run_123 \
  --reason "No longer needed"
```
