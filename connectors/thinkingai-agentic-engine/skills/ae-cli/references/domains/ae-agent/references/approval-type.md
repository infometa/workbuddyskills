# agent approval-type (Discover Approval Types)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Generic Approval / read**

## Commands

```bash
ae-cli agent approval-type list
ae-cli agent approval-type get --approval-type-id skill.publish@1
```

## Mandatory Rules

- Use `list` to discover registered versioned type IDs. Never guess a type version.
- Use `get` before `approval-request submit`; its `input_schema` defines the type-specific snake_case payload.
- `--approval-type-id` is a versioned type identity such as `skill.publish@1`, not a request or task ID.
- V1 definitions describe one `ANY_ONE` step. Do not infer future multi-step or conditional behavior from local CLI output.

## Output

The response keeps the te-agent public snake_case contract, including `input_schema`, `snapshot_schema`, `principal_selector`, `flow`, and `effect` metadata.

## Transition Metadata

- Transition status: transitional
- Owning module: te-agent approval domain
- Current transport: CLI-token-only versioned REST at `/agent/api/cli/approval/v1`
- Gateway target: `approval.type.list` and `approval.type.get`
- Review after: 2026-11-17
- Exit condition: Migrate these commands to equivalent Capability Gateway schemas once discovery, authorization, output, and versioning contracts are stable, or remove the curated commands if L3 provides the same typed safety.
