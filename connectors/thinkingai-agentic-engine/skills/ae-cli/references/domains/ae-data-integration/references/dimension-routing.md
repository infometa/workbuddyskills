# Dimension routing

Use this reference after [ue-routing.md](ue-routing.md) has classified the file as dimension data — a stable-entity lookup with no row-level identity or event time. It covers the handoff to ae-metadata; this skill does not ingest dimension data itself.

## What dimension data is

Judge by content, never by file extension — CSV / TSV / TXT / JSON / JSONL / XLS / XLSX can all be dimension data. The classification signals live in [ue-routing.md](ue-routing.md): no row-level identity, no row-level event time, finite entity enumeration, and a join key shared with event data.

Dimension data is not the only file that fails UE prerequisites. Aggregates, pivot tables, and cumulative snapshots also lack identity/time, but those are local-analysis material, not dictionaries. The tell is the entity shape and the join key: a dimension table maps one entity code to its attributes (`city_code` → name / level), while an aggregate summarizes many rows into one measure.

Low confidence is a proposal, never a silent decision — ask the user instead of routing automatically.

## Handoff to ae-metadata

Extract the dimension sheet / file to CSV, then hand the following commands to ae-metadata. The sequence lists entry points only; full flags live in ae-metadata's references.

Bind prerequisite (confirm before creating the table):

- The table binds to an existing property (`property_name` + `property_scope` = user or event). That property usually appears once event/user data is uploaded first (e.g. events carrying `city_code`), so dimension binding is a second-phase action after data lands.
- If the target property does not exist yet, create it first via ae-analysis metadata or a tracking plan. Never invent a property name.

Entry command sequence:

```bash
# 1. Extract the dimension sheet/file to CSV (metadata upload accepts CSV only,
#    purpose data_table.csv)
ae-cli analysis input-file upload --project-id <id> --purpose data_table.csv --file <dim.csv>
# 2. Create + bind in one step (or split into csv-write + bind-existing)
ae-cli metadata property create-and-bind-csv-dimension-table --project-id <id> \
  --property-name <p> --property-scope user|event --input-file-id ifile_xxx
# 3. Later dictionary changes (add/update/delete):
ae-cli metadata data-table csv-write --operation incremental_update|replace_update \
  --data-table-id <id> --input-file-id ifile_xxx
```

Binding model: AE attaches a dimension table to a user/event property, turning it into a dict property whose values join through the table's key column to expand `--dict-columns`. See ae-metadata's dimension-table reference for the full flags.
