# Channel Management

Use this workflow for channel configuration, group routing, WhatsApp Web linking, and Feishu user bindings. All channel endpoints require an authenticated `root` or `agent_admin` and enforce company isolation.

## Scope

Channel configuration supports `feishu`, `lark`, `slack`, `discord`, `dingtalk`, `wecom`, `mattermost`, `google_chat`, and `whatsapp`. Administrator-driven user binding is available only for `feishu`.

The default Feishu binding is group-routing ready. It requires a verified `endpoint_id` for the channel and a `union_id` for every user. Use `--private-only` only after the user explicitly accepts private-chat-only behavior; never downgrade silently when either value is unavailable.

## Two Confirmation Phases

Treat channel configuration and personnel binding as separate writes:

1. **Channel configuration phase**: discover current state, prepare channel configuration and routing, run every applicable `ae-cli ... --dry-run`, show the redacted target/effect, and obtain one explicit confirmation before executing this phase.
2. **Personnel binding phase**: resolve the final roster and IDs, inspect each person's sandbox readiness, validate the complete binding batch and every required sandbox write with `--dry-run`, show counts, endpoint, private-only state, Agent assignments, sandbox creates, and sandbox enables, then obtain explicit confirmation before each planned write set. A roster containing only existing Agent members needs one final binding-and-sandbox confirmation.

A confirmation for phase 1 does not authorize phase 2. A confirmation for one roster does not authorize a changed roster.

## Phase 1: Configure a Channel

Start from current state:

```bash
ae-cli system +list-channels
ae-cli system channel get --id <channel-id>
```

Create JSON uses snake_case. The original `+create-channel` and `+update-channel` commands also accept legacy camelCase fields, but new files should not use them.

```json
{
  "name": "Support Bot",
  "type": "feishu",
  "config": {
    "app_id": "<app-id>",
    "app_secret": "<app-secret>"
  },
  "model": "<optional-model-id>",
  "system_prompt": "<optional-system-prompt>",
  "enabled": false
}
```

Run the dry-run before the phase-1 confirmation. Credential values are replaced with `***`:

```bash
ae-cli --dry-run system +create-channel --channel @channel.json
ae-cli system +create-channel --channel @channel.json
```

Type-specific configuration:

| Type | Required config | Conditional config |
| --- | --- | --- |
| `feishu`, `lark` | `app_id`, `app_secret` | — |
| `slack` | `bot_token`, `app_token` | `client_id`, `client_secret` when used by the deployment |
| `discord` | `bot_token` | `client_id`, `client_secret` when used by the deployment |
| `dingtalk` | `client_id`, `client_secret`, `corp_id` | `interaction_card_template_id` |
| `wecom` | `bot_id`, `bot_secret` | If `oauth_enabled=true`: `corp_id`, `corp_secret`, `agent_id` |
| `mattermost` | `server_url`, `bot_token` | If `oauth_enabled=true`: `client_id`, `client_secret` |
| `google_chat` | `service_account_json` | `workspace_addon_service_account_email`; if `oauth_enabled=true`: `client_id`, `client_secret` |
| `whatsapp` | no manual config | Credentials are created by the QR lifecycle |

Update accepts a partial object containing `name`, `type`, `config`, `model`, `system_prompt`, `enabled`, or `unbind_users`. If `type` is present it must equal the channel's existing type. Omitting a secret or passing an empty string preserves the stored value; it does not clear the secret.

For every non-WhatsApp channel, verify credentials before depending on endpoints:

```bash
ae-cli --dry-run system channel verify --id <channel-id>
ae-cli system channel verify --id <channel-id>
ae-cli system channel get --id <channel-id>
```

Treat configuration persistence and runtime startup as separate outcomes. An HTTP 200 may still contain `runtime_status="error"`; report that the configuration was saved without claiming the bot is online. When Google Chat creation returns its one-time `webhook_url`, ask the operator to save it immediately in an approved secret store and never copy it into logs or repository files.

For WhatsApp, create the channel without config, enable it with `+update-channel`, then start linking. Poll only until the returned `expires_at` (and never longer than two minutes) for `linked`, `needs_relink`, `failed`, or `expired`:

```bash
ae-cli --dry-run system +update-channel --id <channel-id> --channel '{"enabled":true}'
ae-cli system +update-channel --id <channel-id> --channel '{"enabled":true}'
ae-cli --dry-run system channel whatsapp-web start --id <channel-id>
ae-cli system channel whatsapp-web start --id <channel-id>
ae-cli system channel whatsapp-web status --id <channel-id>
```

Show `qr_data_url` to the user for scanning. Do not call `channel verify` for WhatsApp. Before unlinking, disable the channel with `+update-channel`, then call `channel whatsapp-web unlink`; the unlink command requires its own high-risk CLI confirmation and still stays inside phase 1.

```bash
ae-cli --dry-run system +update-channel --id <channel-id> --channel '{"enabled":false}'
ae-cli system +update-channel --id <channel-id> --channel '{"enabled":false}'
ae-cli --dry-run system channel whatsapp-web unlink --id <channel-id>
ae-cli system channel whatsapp-web unlink --id <channel-id>
```

## Group Routing

Use a verified endpoint ID from `channel verify` or `channel get`:

```bash
ae-cli system channel routing get --endpoint-id <endpoint-id>
ae-cli --dry-run system channel routing set \
  --endpoint-id <endpoint-id> \
  --routing @routing.json
```

`routing.json` replaces the full routing configuration:

```json
{
  "status": "enabled",
  "default_handler": { "kind": "agent", "id": "<agent-id>" },
  "targets": [
    {
      "handler_kind": "team",
      "handler_id": "<team-id>",
      "slug": "billing",
      "keywords": ["invoice", "refund"],
      "sort_order": 10,
      "enabled": true
    }
  ]
}
```

`status` is `enabled | disabled`, `default_handler` is an Agent/Team handler or `null`, and `targets` contains at most 19 entries. The server validates handler ownership, duplicate handlers/slugs, and keyword conflicts.

## Phase 2: Resolve and Bind Feishu Users

### Feishu binding transport contract

Both the single-user and batch CLI flows use the same binding endpoint:

| Operation | Method and path | CLI mapping |
| --- | --- | --- |
| Bind one Feishu identity to one channel | PUT `/api/cli/channel/v1/bindings/feishu` | `channel binding bind-feishu` sends one request. |
| Bind 1-100 Feishu identities to one channel | PUT `/api/cli/channel/v1/bindings/feishu` | `+bind-feishu-users` validates the full roster, then sends one binding PUT per person. |
| Set the private-chat default Agent after binding | PUT `/api/cli/channel/v1/bindings/{binding_id}/agent` | `channel binding set-agent`; the batch command calls it after each successful binding when an Agent is selected. |

The Feishu binding request body is a strict, flat JSON object:

| Field | Required | Binding meaning |
| --- | --- | --- |
| `channel_id` | yes | `channel_id` identifies the one target Feishu channel for the request. The channel must belong to the current company and be enabled. |
| `te_user_id` | yes | The selected AE Agent member's `openId`; this is the member being associated with the channel identity. |
| `open_id` | yes | The person's Feishu `open_id` under the same Feishu application configured by the target channel. |
| `union_id` | group-ready only | The person's stable Feishu identity for group routing. Supply it together with `endpoint_id`; omit both only for explicitly approved private-chat-only binding. |
| `endpoint_id` | group-ready only | `endpoint_id` must identify a verified endpoint that belongs to the same `channel_id`. Supply it together with `union_id`. |

```json
{
  "channel_id": "channel-sales",
  "te_user_id": "agent-member-open-id-alice",
  "open_id": "ou_alice",
  "union_id": "on_alice",
  "endpoint_id": "endpoint-sales-verified"
}
```

The binding response returns:

| Field | Meaning |
| --- | --- |
| `binding_id` | The channel-user binding ID used for later Agent assignment or maintenance. |
| `channel_id` | The target channel confirmed by the server. |
| `te_user_id` | The AE Agent member associated with the channel identity. |
| `open_id` | The Feishu application-scoped identity stored on the binding. |
| `group_routing_ready` | Whether this binding is ready for group routing. |
| `agent_id` | The current private-chat default Agent, or no value when system-default resolution applies. |
| `endpoint_id` | The associated endpoint when the binding is group-routing ready. |

`agent_id` is not part of this request body. After the binding response returns `binding_id`, set or clear the private-chat default Agent through `PUT /api/cli/channel/v1/bindings/{binding_id}/agent`. `default_agent_id` and `private_only` are also CLI orchestration fields, not fields accepted by the Feishu binding endpoint.

One `+bind-feishu-users` invocation has one top-level `--channel-id` and one shared `--endpoint-id`; every entry in `bindings.json` is bound to that channel. Run separate confirmed batches for different channels. Do not put `channel_id` or `endpoint_id` inside individual roster entries.

Common contract mistakes:

| Mistake | Required correction |
| --- | --- |
| Reusing an `open_id` resolved under another Feishu application | Resolve the person again with the application configured by the target channel. |
| Pairing the target channel with an endpoint from another channel | Select a verified endpoint returned by `channel get` or `channel verify` for the same `channel_id`. |
| Sending `agent_id`, `default_agent_id`, or `private_only` to the Feishu binding endpoint | Keep them in CLI orchestration; assign the Agent through the binding-specific Agent endpoint. |
| Mixing users for multiple channels in one batch roster | Split the work by channel, dry-run every final roster, and confirm each batch separately. |

1. The current session must have the Feishu OpenAPI MCP mounted. Before resolving identities, verify all of these prerequisites:

- The MCP and the target channel use the same App ID and App Secret. Read the channel's `config.app_id` with `ae-cli system channel get --id <channel-id>` and compare it with the MCP application configuration. When the App Secret or MCP configuration is masked, obtain explicit confirmation from the configuration owner instead of assuming a match. Feishu `open_id` is application-scoped.
- The Feishu application has the `contact:user.id:readonly` permission.
- The MCP exposes the `contact.v3.users.batchGetId` tool.

Stop when any prerequisite is missing or cannot be verified. Resolve people by exact corporate email address or mobile number; `contact.v3.users.batchGetId` does not resolve names, so ask for an email address or mobile number when only a name is provided.

2. Call `contact.v3.users.batchGetId` with `user_id_type=open_id`. Put exact emails in `data.emails` or exact mobile numbers in `data.mobiles`:

```json
{
  "params": { "user_id_type": "open_id" },
  "data": { "emails": ["alice@example.com", "bob@example.com"] }
}
```

Map each returned `user_list[].user_id` to the matching returned email or mobile number as that person's Feishu `open_id`. A zero-result lookup, missing input, duplicate input, or response that cannot be mapped one-to-one is unresolved. Stop, show the unresolved inputs, and obtain corrected exact identifiers; never choose the first result or infer a person from ordering.

3. Repeat `contact.v3.users.batchGetId` for the same exact emails or mobile numbers with `user_id_type=union_id`; reuse the corresponding `data.emails` or `data.mobiles` roster from step 2 unchanged.

Map each returned `user_list[].user_id` to the same person as that person's Feishu `union_id`. Require the `open_id` and `union_id` lookup results to cover the same uniquely identified roster. If the Feishu OpenAPI MCP cannot return a `union_id`, stop. Ask whether the user explicitly accepts `--private-only`; do not infer that choice.

4. Fetch Agent members and match each selected person to exactly one Agent member by confirmed login/display identity. Use that member's `openId` as `te_user_id`; do not use its database `userId`, and do not assume the app-scoped Feishu `open_id` equals the AE member `openId`:

```bash
ae-cli system +list-members --status enabled --all true
```

If a selected person is not yet an Agent member, use `+list-member-candidates` to resolve the exact candidate. When member addition is required, phase 2 has a prerequisite member-add confirmation and a final binding-and-sandbox confirmation. Dry-run and confirm `+add-members`, execute it, then refetch members before preparing the final binding and sandbox plan. Keep `--create-sandbox` false or omit it in this workflow; sandbox creation and verification happen explicitly after a successful channel binding. The member-add confirmation does not authorize the later binding or sandbox writes.
5. Build `bindings.json` using only snake_case:

```json
[
  {
    "te_user_id": "<agent-member-open-id>",
    "open_id": "<feishu-open-id>",
    "union_id": "<feishu-union-id>",
    "agent_id": "<optional-per-user-agent-id>"
  }
]
```

`--default-agent-id` applies when an item omits `agent_id`; an item's `agent_id` overrides the default. Omit both to leave the private-chat default Agent unchanged.

6. Inspect sandbox capacity and current ownership before building the phase-2 plan:

```bash
ae-cli system +get-sandbox-config
ae-cli system +list-sandboxes
```

For sandbox operations, map each selected Agent member's database `userId` to `items[].boundUsers[].userId`; never use the member's `openId`, Feishu `open_id`, or Feishu `union_id`. A channel-bound person's sandbox is ready when exactly one returned sandbox contains that `userId` and has `enabled === true`. Container `runningState` is a separate lifecycle state and does not trigger `+start-sandbox` in this workflow.

- For members with no sandbox, prepare one dry-run containing their database user IDs:

```bash
ae-cli --dry-run system +batch-create-sandboxes \
  --user-ids '["<member-database-user-id>"]'
```

- For each existing sandbox with `enabled === false`, prepare its enable dry-run:

```bash
ae-cli --dry-run system +set-sandbox-enabled \
  --id <sandbox-id> \
  --enabled true
```

Calculate the planned quota use from `+get-sandbox-config`: required create seats equal the number of members with no sandbox, and required active seats equal that number plus the number of existing disabled sandboxes to enable. Require `sandboxQuota.cluster.remaining` to cover required create seats and `sandboxQuota.active.remaining` to cover required active seats. Treat a missing or non-numeric quota value as unverified rather than assuming capacity; `sandboxActiveSeatsLimit` is the limit, not the remaining count.

Sandbox preflight protects sandbox writes without becoming a gate on channel binding. When sandbox management is disabled, verified capacity cannot cover the plan, quota values are unverified, a person maps to multiple sandboxes, or ownership cannot be matched exactly, mark the affected person as `sandbox_readiness_blocked` and show the reason in the phase-2 plan. Require confirmation that the channel binding may succeed while the sandbox remains not ready, and do not issue an unsafe sandbox write. A sandbox preflight failure does not cancel a confirmed channel binding.

The phase-2 confirmation also authorizes the listed sandbox readiness writes. If the roster, target user IDs, sandbox IDs, required actions, or limits change, regenerate every affected dry-run and obtain a new confirmation.

7. Validate the whole 1-100 item binding batch and show the complete phase-2 plan before asking for confirmation:

```bash
ae-cli --dry-run system +bind-feishu-users \
  --channel-id <channel-id> \
  --endpoint-id <verified-endpoint-id> \
  --bindings @bindings.json \
  --default-agent-id <optional-agent-id>
```

For an explicitly approved private-chat-only batch, omit every `union_id` and `--endpoint-id`, then add `--private-only true`.

8. After phase-2 confirmation, execute the same binding command without `--dry-run`. The command validates the whole batch before the first request, then processes users sequentially. An item-level validation or conflict failure does not stop later users and no automatic rollback is attempted; a final 401 or any 403 stops the batch because authentication or authorization is no longer valid. Inspect `succeeded`, `failed`, and every result's `stage` (`binding` or `agent_assignment`). Retry only failed items with a new file; the Feishu binding PUT is idempotent.

9. Only users whose channel binding succeeded proceed to sandbox readiness. A result with `binding_id` and `stage: "agent_assignment"` still proceeds to sandbox readiness. The channel binding exists, so report the Agent-assignment failure separately. Refetch `+list-sandboxes` after binding, then apply the confirmed plan against the refreshed state:

- If preflight marked the person as `sandbox_readiness_blocked`, preserve the successful binding, report `channel_bound_sandbox_not_ready`, and wait for a new safe dry-run and confirmation before any later sandbox write.
- If the exact user's sandbox is already `enabled === true`, make no write.
- If the confirmed existing sandbox is still present with `enabled === false`, execute its prepared `+set-sandbox-enabled --enabled true` command.
- If the confirmed user still has no sandbox, execute the prepared `+batch-create-sandboxes` command. The create call must return a successful result and a `sandboxId` for that database `userId`.
- Refetch after creation. The batch-create contract creates an enabled personal sandbox and binds it to the requested database `userId`. If the new sandbox instead has `enabled === false`, run a fresh `+set-sandbox-enabled` dry-run and obtain supplemental explicit confirmation for the returned `sandboxId` before enabling it.
- If the refreshed ownership or sandbox ID conflicts with the confirmed plan, stop that person's sandbox action and request a new dry-run and confirmation.

Inspect every create or enable result. A final 401 or any 403 stops remaining sandbox writes. A quota, validation, conflict, or other item failure does not undo earlier bindings or prevent independent confirmed users from being processed. Record and report that person as `channel_bound_sandbox_not_ready`. Do not roll back a successful channel binding when sandbox preparation fails.

10. Read back the final channel and sandbox state:

```bash
ae-cli system channel binding list --channel-id <channel-id>
ae-cli system +list-sandboxes
```

For every successful channel binding, verify that exactly one sandbox contains the Agent member's database `userId` in `boundUsers[].userId` and returns `enabled === true`. Report separate counts and identities for `channel_bound_sandbox_ready`, `channel_bound_sandbox_not_ready`, and `channel_binding_failed`; do not collapse partial readiness into overall success.

For one-off maintenance, use `channel binding bind-feishu`, `channel binding set-agent`, and `channel binding unbind` with the same dry-run, confirmation, and read-back rules. Clear a binding's private-chat Agent and restore system-default resolution with `channel binding set-agent --binding-id <binding-id> --clear`.

## Transport Status

Transition status: transitional
Owning module: te-agent channel management
Current transport: signed REST at `/api/cli/channel/v1/**`
Gateway target: channel Capability Gateway
Review after: 2026-10-24
Exit condition: migrate when equivalent schemas, authorization, risk, dry-run, batch orchestration, and output contracts are stable.
