---
name: datahub-data-apps
description: Discover, inspect, run, monitor, cancel, and retrieve results from DataHub Data Apps while preserving billing and retry safety.
description_zh: 发现、检查和运行 DataHub Data App，安全地跟踪、取消运行并获取结构化结果，避免重复计费。
description_en: Discover, inspect, run, monitor, cancel, and retrieve results from DataHub Data Apps while preserving billing and retry safety.
version: "1.0.0"
author: DataHub
---

# DataHub Data Apps

Use this Skill when the user wants to discover a Data App, understand its inputs or price, execute it, inspect current or historical runs, cancel a run, or retrieve structured results.

Reply in the user's language. Keep Data App IDs/slugs, run IDs, field names, enum values, prices, currencies, timestamps, and platform error messages exact.

## Available Base Tools

| Tool | Use it for |
| --- | --- |
| `search_data_apps` | Discover visible Data Apps by intent, type, or scope |
| `get_data_app_details` | Inspect input/output schemas, execution behavior, pricing, knowledge, and examples |
| `run_data_app` | Create a potentially billable run |
| `get_run_status` | Read or long-poll one run's status and cost |
| `get_run_result` | Page and project structured results |
| `cancel_run` | Request cancellation of an active run |
| `list_runs` | Find recent runs, recover a run ID, or summarize run history |

Treat the live tool schemas as authoritative. The root endpoint exposes the seven tools above; do not assume the retired `?tools=` routing behavior.

## Discovery and Selection

1. If the user did not provide an exact app ID or slug, call `search_data_apps` with a short intent-oriented query.
2. Use `type=data` for collection/extraction and `type=transform` for processing existing data when the intent makes the distinction clear. Otherwise omit the type.
3. Default to `scope=all`. Use a narrower scope only when the user asks for public, private, or shared apps.
4. Use the smallest useful page; `limit` cannot exceed 20.
5. If several apps match, compare relevance, description, availability, and pricing information. Ask the user to choose only when the choice materially changes inputs, cost, or output.
6. Never launch a card whose `accepting_runs` value is false.

## Inspect Before Running

Call `get_data_app_details` before the first run in the conversation unless all of these are already known from fresh tool output:

- exact app ID or slug;
- `accepting_runs` state;
- required input fields and their types;
- output schema;
- execution behavior;
- price/currency and any record or run limits.

Map the user's words to the declared input schema. Never guess a required value. Preserve explicit zero, false, empty arrays, and enum spelling. Explain only missing or invalid fields that block the call.

If pricing is nonzero and the user has not already authorized this exact app, input, and quantity bound, show the known price/billing basis and request confirmation before calling `run_data_app`.

## Starting Runs

`run_data_app` accepts `app`, `input`, optional `max_records`, and optional `wait_seconds`. The live tool schema is authoritative; `wait_seconds` is currently bounded to 0-60 seconds.

- Keep `max_records` within the tool schema and the user's requested bound. Do not silently increase it.
- Use `wait_seconds=0` when the caller needs the `run_id` immediately. A positive value may wait for completion within the declared bound; if the Run is still active, retain the returned `run_id` and poll separately.
- For multiple async runs, submit the bounded set first with a short or zero wait, retain every returned `run_id`, and poll separately.
- A sync App may return inline records according to its declared execution profile and the requested wait bound.
- Never launch an unbounded set. When the user does not set a smaller limit, allow at most five concurrent runs and batch the rest only after capacity is released. Respect lower tenant/platform quotas.
- Report the returned `run_id`, status, and cost fields exactly. Do not exceed the live `wait_seconds` bound.

`run_data_app` has no exposed idempotency key. Never automatically retry it after a timeout, disconnect, `5xx`, or any response where acceptance is uncertain.

### Ambiguous Run Recovery

1. Call `list_runs` for the same `app`, `triggered_by=mcp`, and a narrow creation-time window around the attempted call.
2. Compare timestamps, app identity, status, run kind, and any returned metadata.
3. If exactly one run is an unambiguous match, continue with that `run_id` and tell the user it was recovered.
4. If zero or multiple runs could match, explain the ambiguity and ask before creating another potentially billable run.

This lookup reduces duplicate risk but is not atomic idempotency. Never claim otherwise.

## Monitoring and Results

Use `get_run_status(run_id, wait_seconds=0)` for an immediate check. Use up to 60 seconds only when the user is waiting for completion. Do not create many simultaneous long polls for one run.

Recognize the live status enum. Treat `SUCCEEDED`, `PARTIALLY_SUCCEEDED`, `FAILED`, and `CANCELLED` as terminal when the schema reports them. For terminal runs, report the final status, counts, timestamps, and platform-reported cost when present.

Use `get_run_result` only when results are available:

- `offset` starts at 0;
- `limit` cannot exceed 50;
- use `fields` when the user requested a subset;
- fetch only enough pages to satisfy the request;
- summarize the page boundary and remaining availability when the result is larger;
- do not loop through an unknown or unlimited result set.

Use `list_runs` to answer history questions, recover lost IDs, and compare recent costs. Apply the narrowest known filters. Its `limit` cannot exceed 50.

## Cancellation

Cancellation is a side effect. If the user did not explicitly request cancellation, confirm the exact `run_id` first. Call `cancel_run` once. If completion races with cancellation, report the platform's returned/current terminal state and do not repeatedly cancel.

## Error Handling

- Authentication error: tell the user DataHub authorization must be completed or renewed; allow WorkBuddy to reconnect through OAuth. Never ask them to paste a bearer token into chat.
- Validation error: read fresh app details, identify the exact invalid field, and correct only with user-provided or unambiguous values.
- `accepting_runs=false`: do not call `run_data_app`; search for an alternative or report unavailability.
- Rate limit or transient error on a read: retry only a small bounded number of times with backoff when useful.
- Ambiguous write error: follow Ambiguous Run Recovery and do not retry automatically.
- Failed run: show the platform's useful error and suggest a concrete input/app change; do not expose credentials, stack traces, or unrelated internal details.

## Response Shape

For a completed workflow, return a compact summary containing:

- selected Data App name and ID/slug;
- run ID and final/current status;
- requested/returned record count and pagination position;
- cost and currency when reported;
- the requested fields or a concise preview of results;
- the next useful action only when the run is still active or more pages remain.
