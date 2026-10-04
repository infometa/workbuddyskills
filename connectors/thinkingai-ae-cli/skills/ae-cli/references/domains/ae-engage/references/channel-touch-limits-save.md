# engage-setting channel-touch-limits save

> Capability id: `engage-setting.channel-touch-limits.save` · Domain: `engage`.

## Command

```bash
# Create a new touch-limit rule (omit --rule-id)
ae-cli engage-setting channel-touch-limits save \
  --project-id <project_id> --channel-biz-type <biz_type> \
  --rule-def '<rule_def_json>' --enable true

# Update an existing touch-limit rule (provide --rule-id)
ae-cli engage-setting channel-touch-limits save \
  --project-id <project_id> --channel-biz-type <biz_type> \
  --rule-def '<rule_def_json>' --enable false --rule-id <rule_id>
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--channel-biz-type` | Yes | Channel business type the rule belongs to. |
| `--rule-def` | Yes | Touch-limit rule definition (JSON string, see ChannelTouchLimitRuleDTO). |
| `--enable` | Yes | Whether the touch-limit rule is enabled. |
| `--rule-id` | No | Existing rule ID. When omitted a new rule is created. |

## Output

- `data.success`: whether the save succeeded.

## Decision Rules

- Use this command when the user asks to create or update a single touch-limit (fatigue-control) rule.
- For updates, discover the real rule ID with `ae-cli engage-setting channel-touch-limits list --project-id <project_id>` first.
- Risk is `write`; ordinary write, no confirmation gate.
