# agent +list-sandbox-tools (List Sandbox Tools)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Sandbox tools / read**

## Use Cases

- List tools activated in the current sandbox by scanning `/home/ta/.local/bin` for managed shims.
- Each managed shim carries a `managed-by: te-agent-sandbox-tools` marker plus tool, version, command, target, and runtime fields. The command verifies the real target path, share-root containment, file type, and runtime-specific permissions.
- This is a **local filesystem scan** — it does NOT call any remote API and does not require `--host` or a token.

## Mandatory Rules (MUST)

- Only entries with the `managed-by: te-agent-sandbox-tools` marker are reported; non-managed files in `/home/ta/.local/bin` are ignored (deactivate on the admin side only removes managed entries).
- The command runs inside the sandbox; ensure `/home/ta/.local/bin` is readable.
- Managed shim symlinks, oversized shims, malformed or duplicate marker fields, and targets outside `${SANDBOX_SYSTEM_SHARE_ROOT:-/data/app/te_agent_ta/share}/tools` are never treated as active.

## Command

```bash
ae-cli agent +list-sandbox-tools

# Filter to only broken entries
ae-cli agent +list-sandbox-tools --status broken

# Dry-run to inspect the scan target (no disk read)
ae-cli agent +list-sandbox-tools --dry-run
```

## Parameters

| Parameter  | Required | Description                            |
| ---------- | -------- | -------------------------------------- |
| `--status` | No       | Filter by status: `active` \| `broken` |

## Decision Rules

- Use this to inspect which managed sandbox tools are currently usable in this sandbox.
- `active` = the real target stays inside the configured tools root, is a regular file, and is readable for `node` or executable for `native`.
- `broken` = the managed shim or target fails marker, containment, file-type, or permission checks. Re-activate via the admin console to repair.
- Legacy shims without version/runtime remain readable: both fields are reported as `unknown`, and the target must at least be readable.
- `summary` counts reflect the full scan (before `--status` filtering); `tools` respects the `--status` filter.

## Response Shape

```json
{
  "tools": [
    {
      "tool": "ae-cli",
      "version": "1.0.32",
      "command": "ae-cli",
      "runtime": "node",
      "target": "/data/app/te_agent_ta/share/tools/ae-cli/1.0.32/bin/ae-cli.js",
      "status": "active"
    },
    {
      "tool": "gstack",
      "version": "0.1.0",
      "command": "gstack",
      "runtime": "native",
      "target": "/data/app/te_agent_ta/share/tools/gstack/0.1.0/bin/gstack",
      "status": "broken",
      "reason": "target missing"
    }
  ],
  "summary": { "total": 2, "active": 1, "broken": 1 }
}
```

## Next Steps on Failure

- Empty `tools` with `summary.total=0`: no managed shims in this sandbox; activate tools from the admin console (system management → sandbox management → sandbox tools) first.
- `broken` entries: the shared tool package may have been removed or the version path changed; re-activate the tool from the admin console.

## Recommended Chaining

- `+list-sandbox-tools` → spot `broken` → ask the admin to re-activate via the sandbox tools admin page.
