# engage-scene template

> Trigger keywords: config center, scene config, template · Capability ids: `engage-scene.template.{list,get,copy,create,update,update-status,delete}` · Domain: `engage`.

Scene management / config center — config item template management. `create`/`update` pass backend DTOs via `--payload` (native camelCase structure); `project_id` is injected into the payload.

## Commands

```bash
# List templates of a config item
ae-cli engage-scene template list --project-id <project_id> --config-id <config_id>

# Get a template's detail
ae-cli engage-scene template get --project-id <project_id> --config-id <config_id> --template-id <template_id>

# Copy a template to a target config item
ae-cli engage-scene template copy \
  --source-project-id <source_project_id> --source-config-id <source_config_id> \
  --source-template-id <source_template_id> --project-id <target_project_id> --config-id <target_config_id>

# Create a template
ae-cli engage-scene template create --project-id <project_id> \
  --payload '{"configId":"cfg-1","templateId":"tpl-1","templateName":"t1","remark":""}'

# Update a template (bind config-item params into template.config — required before enable)
ae-cli engage-scene template update --project-id <project_id> \
  --payload '{
    "configId":"cfg-1",
    "templateId":"tpl-1",
    "templateName":"t1",
    "config":[{
      "paramId":48,
      "paramName":"title",
      "paramDisplayName":"Title",
      "paramType":"STRING",
      "paramSubType":"SHORT_TEXT",
      "isRequired":1,
      "defaultValue":"hello"
    }]
  }'

# Enable / disable a template (only after config[] is non-empty)
ae-cli engage-scene template update-status \
  --project-id <project_id> --config-id <config_id> --template-id <template_id> --status <1|0>

# Delete a template (high-risk)
ae-cli engage-scene template delete --project-id <project_id> --config-id <config_id> --template-id <template_id> --yes
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| list | `--project-id`, `--config-id` | read. |
| get | `--project-id`, `--config-id`, `--template-id` | read. |
| copy | `--source-project-id`, `--source-config-id`, `--source-template-id`, `--project-id`, `--config-id` | write. |
| create | `--project-id`, `--payload` | payload = `ConfigTemplateAddDTO`. |
| update | `--project-id`, `--payload` | payload = `ConfigTemplateModifyDTO`. |
| update-status | `--project-id`, `--config-id`, `--template-id`, `--status` | status 1 enable / 0 disable. |
| delete | `--project-id`, `--config-id`, `--template-id` | high-risk. |

`template update-status --validate` and `--dry-run` perform the same read-only business preflight as execution. They reject incomplete template fields, missing dependency configuration, unsupported status transitions, and status values other than `0` or `1` before any template state is changed.

## Output

- `list`: `data.items` + `data.total`.
- `get`: `data.template`.
- `copy` / `create` / `update` / `update-status` / `delete`: `data.success`.

## Decision Rules

- `delete` is `high-risk-write`; requires `--yes` and does not support dry-run.
- Discover real template IDs with `list`/`get` first; never invent IDs.
- **`create` requires `templateId` in payload** (unique within config item, <=80 chars), not only `templateName`.
- **Enable workflow:** (1) `config-param batch-add` on the config item → (2) `template create` → (3) **`template update` with non-empty `config[]`** referencing real `paramId` values from `config-param list` → (4) `template update-status --status 1`. Skipping step 3 returns `TEMPLATE_FIELDS_INCOMPLETE`.
- Enabling a template is a prerequisite for `strategy create` on the same config (`TEMPLATE_ENABLE` if template disabled).
- Template test-send is not exposed via `engage-scene` CLI; use the product UI.
