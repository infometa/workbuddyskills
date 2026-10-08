# analysis entity id-import-options

Discover how imported values must map to one analysis entity before creating or updating an imported-value cluster or tag.

```bash
ae-cli analysis entity id-import-options --project-id <project_id> --entity-id <entity_id>
```

If the entity ID is not already known, discover it first instead of guessing:

```bash
ae-cli project entity list --project-id <project_id> --fields '["entity_id","entity_name","column_name","select_type"]'
```

- `match_mode=user_property`: `--association-property` is required and must be copied from `association_properties`; `#user_id` is forbidden.
- `match_mode=entity_id`: omit `--association-property`; the first CSV column contains that entity's own IDs.

Output includes the resolved `entity_column`, matching mode, whether an association property is required, explicitly excluded properties, and the allowed property names/types.

Do not guess `entity_id`, property names, or CSV shape.
