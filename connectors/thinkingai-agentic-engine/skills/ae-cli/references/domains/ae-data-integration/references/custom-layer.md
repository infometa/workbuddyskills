# Project custom layer (verify + salvage overlays)

The handoff package is deliberately **standard flow only**: it ships the generic
stage executors and never embeds environment-specific workarounds such as SQL
direct queries or multi-round salvage loops. Some projects need those — a hard
per-event persistence judge, or a repeated salvage loop for a dirty source. Add
them as a **custom layer next to the package**, never by editing the generic
package itself.

## When to add a layer

- **Hard persistence judge.** `bin/verify.py` is a soft check: it computes the
  submit window and expected counts from the local UE output, then shows the
  `tracking ingest summary` payload before and after for comparison. It does not
  parse that payload into per-event counts — the capability's `data` shape is
  server-defined, and a shared project's window delta cannot be attributed to one
  import. When the project requires an automated per-event ✓/✗ verdict, overlay a
  SQL layer that reads the project's event/user tables directly.
- **Multi-round salvage.** `bin/run.sh` already prints a single-round salvage
  hint when `invalid.rows.jsonl` is non-empty. For sources that fail in layers,
  wrap that command in a loop that re-feeds each round's quarantine into the next
  `--salvage-from` until nothing fails or the user stops.

## Rules

1. Put overlays in a sibling directory (e.g. `custom/`) under the package root,
   and reference `../pipeline.json` / `../index.json` — never modify the frozen
   mappings, `bin/`, or the generated docs.
2. Keep every existing confirmation gate. A custom layer may add gates; it must
   not remove the `--confirm` upload gate or the plan/shape gates.
3. Keep secrets in `.local/target.env`. Never write APPID, endpoints, tokens, or
   raw data values into an overlay file.
4. An overlay is project-specific. Do not copy it into another project's package
   without re-confirming the environment assumptions (table names, APPID, host).

## Skeleton 1 — SQL verify (hard per-event judge)

The reference deployment queries the ingested tables directly. **Table and
column names vary by deployment** (`v_event_1` / `v_user_1` and `$part_date` /
`$part_event` are examples only) — confirm them against the project's receiver
schema before use, and keep the query read-only.

```bash
# custom/verify.sh — hard judge; requires the SQL capability to be available.
# usage: custom/verify.sh <run-dir> [--baseline|--check]
# Reuses bin/verify.py's window/count computation idea, but answers the question
# "did exactly these events land?" with a direct count over the event table.
```

The query shape (adapt table/column names):

```text
select <event_column>, count(*)
from <event_table>
where <date_partition_column> between '<window-start>' and '<window-end>'
group by 1
```

Compare the per-event delta (after upload minus before upload) against the
expected counts from `valid.ue.jsonl`. User-profile rows are overwrite-writes,
so a zero user-table delta is normal; compare event rows per event, not totals.

Keep this layer read-only and non-blocking: report the verdict, never retransmit
automatically on a mismatch — first check `tracking ingest-error list` for the
silent-drop reason.

## Skeleton 2 — multi-round salvage loop

`bin/run.sh` prints the one-round hint. Wrap it into a loop that re-processes each
round's quarantine against the fixed mapping until clean or the user stops:

```bash
# custom/salvage.sh <run-dir> — re-process quarantined rows round by round.
# Each round's valid.ue.jsonl is disjoint from earlier rounds', so upload each
# round independently (same --confirm and --allow-clean-subset gates).
round=1
while [ -s "<run-dir>/invalid.rows.jsonl" ]; do
  ae-cli data-integration convert \
    --input-file '<same-source>' \
    --mapping '<fixed-mapping.json>' \
    --salvage-from "<run-dir>/invalid.rows.jsonl" \
    --output-dir "<run-dir>-salvage-$round"
  round=$((round + 1))
  # stop condition is the user's: a row that still fails after a fix is a real
  # data defect, not a code bug.
done
```

See [transform.md](transform.md) for the `--salvage-from` semantics (single-file
only; the source must be the same file that produced the quarantine) and
[handoff.md](handoff.md) for the package the overlay attaches to. Persistence
verification always follows [sink-upload.md](sink-upload.md): `receiver_accepted`
is not durability.
