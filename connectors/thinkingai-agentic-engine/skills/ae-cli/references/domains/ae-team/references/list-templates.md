# team +list-templates (List Team Templates)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team management / discovery**

## Use Cases
- Browse built-in team templates provided by the platform.
- Each template includes a ready-to-use `config` that can be passed directly to `+create --config`.
- Supports locale-specific template names and descriptions.

## Mandatory Rules (MUST)
- Do not fabricate template names or configs. Always call this command first and present the real list to the user.
- `--locale` must be one of `zh`, `en`, `ja`, `ko` if provided.

## Command
```bash
ae-cli team +list-templates
ae-cli team +list-templates --locale en
ae-cli team +list-templates --locale zh --format table
ae-cli team +list-templates --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--locale` | No | `zh` (default) \| `en` \| `ja` \| `ko` |

## Decision Rules
- When the user says "show me team templates" or "I want to create a team from a template", call this command first.
- Extract the `config` field from the chosen template and pass it to `+create --config`.
- If the user asks for templates in a specific language, pass the corresponding `--locale`.

## Next Steps on Failure
- Empty list: the platform may not have templates configured for the current environment.

## Recommended Chaining
- `+list-templates` → user picks template → `+create --name "..." --config '<template.config>'`
