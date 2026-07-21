# Quick Reference — AI Cheat Sheet

When user says something like  "给 X 配表 / 迁移硬编码 / 新增 Y 类型"，do this 3 steps:

## Step 1. Draft spec (interactive, 1 turn)

Tell the user the list of fields you will extract (pulled from their `.gd`)
and ask once for corrections. Produce a JSON file under the user's workspace
at `specs/<name>_spec.json` following the schema.

Minimal valid spec:
```json
{
  "name": "weapon",
  "fields": [
    {"key": "id", "type": "StringName", "default": "&\"\"", "group": "Identity"},
    {"key": "damage", "type": "int", "default": 10, "range": [0, 9999, 1]}
  ],
  "validators": ["damage >= 0"]
}
```

## Step 2. Scaffold

```bash
python3 ~/.codebuddy/skills/godot-data-driven-config/scripts/scaffold.py \
  --project-root $WORKSPACE \
  --spec $WORKSPACE/specs/<name>_spec.json
```

Run it for **each** category.

## Step 3. Migrate consumer .gd

For each original file that used hardcoded numbers:

1. Add at top:
   ```gdscript
   @export var <name>_data: <Name>Data
   ```
2. In `_ready()` add:
   ```gdscript
   if <name>_data == null:
       <name>_data = DataManager.get_<name>()
   ```
3. Replace literals: `JUMP_SPEED` → `<name>_data.jump_speed` etc.
4. Keep purely technical `const` (collision masks, shader paths) unchanged.

## Step 4. Validate

```bash
godot --headless --script res://tools/validate_data.gd
```

Exit 0 = green. Show user the stdout.

## Step 5. Document

Append to `PROJECT_OVERVIEW.md` or `README.md`:
- A mapping table (source → new field)
- Designer how-to (where to edit, how to run validator)

## Type → @export attribute cheat sheet

| field.type | decorator |
| --- | --- |
| `int`/`float` + `range` | `@export_range(min, max, step)` |
| `String` + `multiline: true` | `@export_multiline` |
| everything else | bare `@export` |

## Common pitfalls (AI must avoid)

- Don't edit large `.tscn` unless asked — `DataManager` fallback is enough for default binding.
- Don't use `FileAccess + JSON.parse` — use `.tres` + `load()`.
- Don't put everything in one god-Resource — one `<Name>Data` per category.
- Don't mutate `Resource` at runtime — `duplicate()` first.
- When there are NEW categories, **always re-run scaffold.py**; don't hand-edit `data_manager.gd` — the `# region *_AUTOGEN` blocks get regenerated.
