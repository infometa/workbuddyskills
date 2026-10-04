# engage-setting channel-touch-limits toggle

> Capability id: `engage-setting.channel-touch-limits.toggle` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting channel-touch-limits toggle \
  --project-id <project_id> --rule-id <rule_id> --enable <true|false>
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--rule-id` | Yes | Touch-limit rule ID to enable/disable. |
| `--enable` | Yes | Whether the touch-limit rule is enabled. |

## Output

- `data.success`: whether the toggle succeeded.

## Decision Rules

- Use this command when the user asks to enable or disable a single touch-limit (fatigue-control) rule.
- Discover the real rule ID with `ae-cli engage-setting channel-touch-limits list --project-id <project_id>` first.
- Risk is `write`; ordinary update, no confirmation gate.
