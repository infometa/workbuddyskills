# Reuse (match a historical handoff package)

Before walking the full pipeline for a new file, check whether a **handoff package** already exists for the same table shape. A match lets the file skip Source re-identification and Transform — the frozen transform is run directly, then Sink proceeds with its own confirmation. It does **not** skip the Tracking plan step unconditionally: skip it only when the matched package's `plan.json` already covers every event and property the new file will produce, including flattened object sub-properties. New properties the plan does not cover still go through the Tracking plan gate and merge into the existing project plan before Sink.

## When

Run reuse right after `inspect`, only when the profile is `ue_eligible` and a `.ae-cli/data-integration/index.json` exists. It is read-only and makes no writes.

## CLI

```
ae-cli data-integration reuse --mapping <recommended_mapping> [--out-dir .ae-cli/data-integration]
```

- `--mapping` — the candidate mapping, typically `inspect`'s `recommended_mapping` (the new file's structure, inferred exactly as Source would infer it).
- `--out-dir` — handoff root. Optional. Without it, `reuse` searches in order: the current directory's `.ae-cli/data-integration/`, then each parent directory upward, then `~/.ae-cli/data-integration/` as a global fallback — so a package written in another directory or another session is still reachable.
- `--dry-run` previews the fingerprint and match verdict without reading frozen packages.

## Search paths

When `--out-dir` is omitted, the result carries `searched_paths` — the exact `index.json` paths probed, in order. A `matched: false` result with a non-empty `searched_paths` means all of them were checked; a missing global fallback (no `$HOME`) simply omits it from the list.

## Matching

The command computes the same **structure fingerprint** the handoff index is keyed on — the raw source columns (by name, reconstructed so flatten, exclude, and account-vs-distinct decisions don't move it), the format, and the event model — and looks it up in `index.json`. Business logic (the frozen event name, `value_mapping`, transforms, `time_format`, `flatten_rules`, `exclude_columns`, and the system-field assignments) is not part of the key, so a same-shape file with different content or a different file name still matches.

## Result

- **No match** (`matched: false`): continue the full pipeline from Tracking plan.
- **Match** (`matched: true`): the result carries the matched package — `mapping_file`, optional `plan_file`, the frozen `default_event_name` (so the user sees which event name will be reused), and a `run` command:

```
node .ae-cli/data-integration/<fingerprint[:16]>/transform.mjs <new-input-file> [<output-dir>]
```

## Confirmation gate

Do **not** run the returned command on your own. Show the user the proposed package — the frozen event name, the property mapping it implies, and the fact that the confirmed business logic (event name, `value_mapping`, flatten rules) is reused unchanged — and wait for one explicit confirmation. Before confirming, diff the new file's flattened properties against the package's `plan.json`: if the package has no `plan_file`, or the new file produces properties the plan does not cover, run the Tracking plan step to add them (merge into the existing project plan) first. Only then run `transform.mjs` on the new file and continue to Sink.

## Safety rules

- Reuse only for a file of the **same shape** (same header/schema and format). The `transform.mjs` wrapper re-binds the content fingerprint to the new file, so the content guard still applies per run.
- A match does not authorize an upload. Sink still requires its own explicit, confirmed `upload` call.
- A mismatch is not an error — it means the new file's shape differs and needs the full pipeline.
- Never invent or edit the frozen mapping to force a match; if the shape genuinely differs, walk the pipeline again.
