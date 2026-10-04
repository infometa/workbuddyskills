# analysis user-tag export

Export every matching accessible user tag without pagination.

```bash
ae-cli analysis user-tag export \
  --project-id <project_id> \
  --output <temporary_path>/tags.jsonl
```

Capability id: `analysis.user_tag.export`.

Optional filters are `--queries`, `--fields`, and `--authenticated-only`. `--limit`, `--offset`, and `--all` are not accepted. The CLI requires a `.jsonl` output path and writes an adjacent `.meta.json` completeness and identity sidecar. Search the file locally; do not load the full snapshot into model context.
