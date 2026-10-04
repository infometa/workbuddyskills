# engage-setting push-language

> Capability ids: `engage-setting.push-language.{get,set}` · Domain: `engage`.

## Commands

```bash
# Query the project push-language property field
ae-cli engage-setting push-language get --project-id <project_id>

# Set the project push-language property field
ae-cli engage-setting push-language set --project-id <project_id> --push-language-column <prop_code>
```

## Parameters

### get

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

### set

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--push-language-column` | Yes | User property code used as the push language field. |

## Output

- `get`: `data.push_language_column` — configured push-language property code, or `null` if unset.
- `set`: `data.success` — whether the field was updated.

## Decision Rules

- Use these commands when the user asks to query or configure the project push-language (localization) property field.
- `--push-language-column` must be a real user property code; discover available properties via the analysis metadata commands first.
- `set` is `write`; ordinary update, no confirmation gate.
