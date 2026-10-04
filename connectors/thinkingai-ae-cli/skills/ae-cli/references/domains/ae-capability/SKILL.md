---
name: ae-capability
version: 1.3.1
description: "AE/TE capability gateway discovery and generic invocation with ae-cli. Use when the user needs to list or search available capabilities, inspect an unknown capability schema/risk/auth contract, optionally validate complex input or dry-run before execute, or invoke a long-tail capability that has no curated ae-cli command. Always discover and inspect before composing input; never guess capability IDs or input fields. Prefer on-demand validate OR dry-run — do not stack both by default."
---

# ae-capability

Use this skill for progressive capability discovery and generic gateway invocation. Prefer a domain-specific curated command when one exists; use `ae-cli capability ...` for discovery and long-tail capabilities.

## Decision Order

1. Use a domain skill and its curated command when it directly covers the task.
2. Otherwise search the capability catalog.
3. Inspect the selected capability before constructing input.
4. **Optionally** pre-check — pick **at most one** path from the table below (do not stack validate + dry-run by default).
5. Execute (`capability run` / curated command). Chat confirmation only for delete (`high-risk-write`).

Never guess a capability ID, input field, enum value, resource ID, or project ID.

**CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.

### On-demand pre-check (pick one)

Motto: **validate = fix params; dry-run = confirm ready to run.**
Hard rule: **for the same final input, do not run both validate and dry-run by default.** `dry-run` already includes parameter validation.

| Situation | What to call | Then |
| --- | --- | --- |
| Simple / familiar input (typical `read`, few scalar fields) | **Neither** — skip pre-check | `run` directly |
| Complex `qp` / nested `payload` / share maps; still iterating shape | **`--validate` / `capability validate` only** (may repeat while fixing) | After `valid=true`, **`run` directly** — skip dry-run unless below applies |
| Need risk / `output_mode` / `supports_cancel`, or `high-risk-write` delete gate | **`--dry-run` / `capability dry-run` only** (once on final input) | Then confirm (delete) / `run`. Do **not** validate first on the same final payload |
| Rare exception: many validate iterations, then still need delete confirmation | validate while drafting → **one** dry-run on the **final** input | Then chat confirm → `run --yes` |

Do **not** treat `validate → dry-run → run` as the normal path. That stack is the rare exception in the last row only.

## Skill references

Default: **do not** create a standalone skill reference for every new capability. Use `search` → `inspect` → (**optional** validate *or* dry-run) → `run`; catalog `description`, `risk`, and `inspect` `input_schema` are the contract.

Create or keep a standalone reference only when at least one applies: L2 hard bar, easily confused with neighbors, `high-risk-write` delete workflow, or multi-step orchestration. Domain skills may inline one-line summaries in overview matrices (e.g. `analysis_gateway_assets.md`). See [`capability-command-admission` §10](../../docs/capability-command-admission.md).

## Commands

```bash
# List company-level summaries, or the capabilities available in one project.
ae-cli capability list --domain <domain> [--project-id <id>]

# Search capability IDs and descriptions. All terms must match.
ae-cli capability search "<terms>" --domain <domain> [--project-id <id>]

# Read input_schema, risk, auth, output, and dry-run support.
ae-cli capability inspect <capability-id> [--project-id <id>]

# Optional — fix params only (gateway /validate). Curated: global --validate.
ae-cli capability validate <capability-id> --input '<json-object>'
ae-cli metadata data-table sql-write --project-id 1 ... --validate

# Optional — confirm ready to run (gateway /dry-run). Curated: global --dry-run.
ae-cli capability dry-run <capability-id> --input '<json-object>'
ae-cli metadata data-table sql-write --project-id 1 ... --dry-run

# Execute (after inspect; add at most one pre-check when needed).
ae-cli capability run <capability-id> --input '<json-object>'
```

`--input` accepts:

- An inline JSON object.
- A JSON file path.
- `@<path>`.
- `-` to read JSON from stdin.

The capability namespace is inferred from `<capability-id>` for `inspect`, `validate`, `dry-run`, and `run`. Use `--domain <domain>` only to override routing. For `list`, `search`, and `inspect`, omit `--project-id` for company License/Feature visibility; pass it to include project membership, project Feature, and user permission filtering.

## validate vs dry-run

| | `validate` / `--validate` | `dry-run` / `--dry-run` |
| --- | --- | --- |
| Purpose | Check **input shape** while composing complex payloads | **Pre-execution confirmation** (params + risk/output/cancel) |
| Does it mutate business data? | No | No |
| Primary success fields | `valid`, `capability_id`, `normalized_input` | `dry_run`, `capability_id`, `risk`, `output_mode`, `supports_cancel`, `normalized_input` |
| When to prefer | Iterating nested `payload` / `qp` / multi-field JSON | Final input; need risk/output contract or delete gate |
| Typical failure focus | Missing/invalid fields, type mismatches, bad `qp` structure | Same param errors, plus readiness signals for actual run |
| Curated commands | Global `--validate` on gateway-backed curated commands | Global `--dry-run` |

Server may still authenticate the caller for both endpoints. Neither executes the capability business handler. Do not combine `--validate` and `--dry-run` on one invocation.

**Complex input:** prefer **`--validate` only** while assembling `qp` / nested payload; after `valid=true`, go to `run`. Use dry-run instead of validate when you need the risk/output preview or a delete confirmation gate — not both.

Example (param risk only — no stacked dry-run):

```bash
ae-cli metadata data-table sql-write ... --validate   # iterate until valid
ae-cli metadata data-table sql-write ...              # execute ordinary write
```

Example (delete gate — dry-run only on final input):

```bash
ae-cli capability dry-run analysis.folder.delete --input '...'
# stop, ask user, then:
ae-cli capability run analysis.folder.delete --input '...' --yes
```

## Risk Levels (aligned with lark-cli)

| `risk` | Meaning | Chat confirmation before `run`? | CLI `[y/N]` without `--yes`? |
| --- | --- | --- | --- |
| `read` | Query / list / inspect | No | No |
| `write` | Create, update, share, and other ordinary writes | No | No |
| `high-risk-write` | Delete or remove resources | **Yes** | **Yes** |

Legacy values such as `create`, `update`, or `delete` are normalized to this three-tier model (`delete` → `high-risk-write`; `create`/`update` → `write`).

## Safety

- `list`, `search`, `inspect`, `validate`, and `dry-run` never execute business mutations.
- Curated gateway commands: `--validate` → `/validate`; `--dry-run` → `/dry-run`; do not combine them.
- Do not stack validate + dry-run on the same final input by default (efficiency).
- `capability run` inspects metadata before execution when `--yes` is absent.
- Only `high-risk-write` requires chat confirmation before `capability run ... --yes`.
- `read` and ordinary `write` may run after inspect; add validate **or** dry-run only when the on-demand table says so.
- Use `--yes` on delete runs only after the user explicitly authorizes execution in chat.
- Global `--dry-run` on `capability run` / curated commands calls the gateway dry-run endpoint instead of execute.
- Global `--validate` on `capability run` / curated commands calls the gateway validate endpoint instead of execute.

## High-Risk Confirmation Workflow (Agent)

Applies only when `inspect` shows `risk=high-risk-write`.

User intent (for example "delete this space") is **not** execution authorization. Do not pass `--yes` just because the user stated the desired action.

1. `capability inspect`. For complex delete input only, you may iterate with `validate` while drafting; for the **final** payload use **`dry-run` once** (skip a redundant validate on that same final JSON — dry-run already validates params).
2. **Stop in the same turn.** Do not call `capability run` in the same turn as dry-run.
3. Summarize in chat: capability ID, `project_id`, key input fields, and `risk=high-risk-write`.
4. Ask the user to confirm execution. Prefer `AskUserQuestion` when that tool is available; otherwise ask in plain text and wait for the user's **next message**.
5. Only after the user replies with explicit authorization (for example `confirm`, `execute`, or `yes`) run `capability run ... --yes` with the same input as dry-run.

For `risk=write`: no chat confirmation gate. Prefer direct `run` after inspect; use `--validate` alone when the payload is complex and you are fixing shape; use `--dry-run` alone only if you need the risk/output preview — **not** validate then dry-run as a habit.

Never pass `--yes` on the first delete attempt. CLI terminal `[y/N]` prompts do not work in Agent Bash; chat confirmation is the real gate for `high-risk-write`.

## Output

- `list` returns `{ domain, count, capabilities }`.
- `search` returns `{ domain, query, count, capabilities }`.
- `inspect`, `validate`, `dry-run`, and `run` return gateway data in the standard ae-cli envelope.

## Examples

```bash
ae-cli capability search "dashboard list" --domain analysis
ae-cli capability inspect analysis.dashboard.list
ae-cli capability validate metadata.data_table.sql_write --input input.json
ae-cli capability dry-run analysis.folder.delete --input '{"project_id":1,"folder_ids":[1001]}'
ae-cli capability run analysis.dashboard.list --input input.json
```
