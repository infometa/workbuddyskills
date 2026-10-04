# `/sync_json` upload

The command sends a JSON array of receiver envelopes:

```json
[
  { "appid": "<appid>", "debug": 0, "data": { "#type": "track", "#time": "2026-08-10 10:00:00.000", "#account_id": "u-1", "#event_name": "open", "properties": { "channel": "web" } } }
]
```

The CLI assembles each envelope around the original UE JSONL text, preserving JSON number serialization from the generated file. System fields (`#type`, `#time`, `#account_id`/`#distinct_id`, `#event_name`) sit at the top level; all properties are nested under `properties`.

## Transport guarantees

- Explicit HTTP(S) endpoint ending in `/sync_json`.
- No AE access token, CLI token, Authorization header, or redirect following.
- Each request is retried 3 times with 2000ms backoff for network failures and HTTP 5xx. HTTP 4xx, non-zero receiver codes, redirects, and invalid responses are never retried.
- No compression unless the user enables it (see below).
- Sequential batches; default 500, maximum 1000 records.
- Fixed 30-second timeout.
- `code=0` means receiver accepted the batch, not durable storage.

## Optional uncertain-batch salvage and compression

Compression is opt-in and only changes transport, never the receiver contract.

- `--retry` — after the 3 transport retries, split a still-uncertain batch into single-record retries and report the offsets that keep failing, instead of stopping the whole upload. Data-level errors (HTTP 4xx, `code != 0`) are never retried. A final result still reports `persistence_verified=false`.
- `--compress gzip` — gzip the request body with `Content-Encoding: gzip`. The request still carries no auth header and does not follow redirects.
- `--debug` — mark every record `debug=1` so AE returns per-record validation details for the batch. Testing only; never use for production uploads. Default `debug=0`.

## Confirmation gate

Before execution, show:

- Resolved project ID/name.
- Masked receiver target and APPID.
- UE file SHA-256.
- Record count, quarantined count, resume offset, batch size/count, and bytes.
- Mapping mode/confidence and timezone.
- `persistence_verified=false`.

Wait for a clear confirmation. If the manifest is blocked, separately confirm clean-subset upload before using `--allow-clean-subset`.

## Interrupted delivery

Timeout or network failure makes the current batch `delivery_state=unknown`. The error's `meta` reports `completed_records`/`completed_batches`, `uncertain_batch_start`/`uncertain_batch_size`, and a candidate offset `resume_from_after_verification` — the zero-based record position in `valid.ue.jsonl` where the uncertain batch starts. Do not use that offset until the user verifies what receiver/AE accepted. Never retry or resume automatically.

To continue after verification, re-run the same upload with that offset; records before it are not re-sent:

```bash
ae-cli data-integration upload \
  --ue-file '<run-dir>/valid.ue.jsonl' \
  --manifest '<run-dir>/manifest.json' \
  --endpoint '<https://.../sync_json>' \
  --appid '<appid>' \
  --batch-size 500 \
  --resume-from <verified-offset>
```

The resumed run keeps the same confirmation gate as a normal upload.
