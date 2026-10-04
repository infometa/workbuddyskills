# Community chat analysis

Use this workflow for customer-service conversations, customer after-sales groups, in-game chat,
or an unspecified chat dataset. Chat capabilities are dynamic L3 capabilities. Do not invent
capability IDs, intent codes, server IDs, participant IDs, input fields, or enum values. Participant
roles are call-scoped inputs; do not assume a persistent customer/staff identity mapping exists.

## Workflow

1. Search the live catalog, inspect every capability that will be called, and use the inspected
   schema as the contract.
2. Discover tenant-specific intent definitions with `community.chat.list_intent_rules`.
3. Discover servers with `community.chat.list_servers` when the user mentions a server or the
   dataset may be in-game chat.
4. If the user did not supply dates, analyze the last seven complete calendar days (ending
   yesterday) and compare with the immediately preceding seven complete days. The concrete dates
   depend on today; compute them from the current date in Asia/Shanghai.
5. For "this month vs last month", use month-to-date for the current month (the 1st through today)
   and the full previous calendar month. The windows differ in length, so compare rate metrics
   (`responseRate`, SLA, median, and P90) directly, but normalize volume metrics such as turns and
   messages to per-day values before drawing volume conclusions. Do not compare raw volume totals
   without this normalization, and state both window lengths in the report.
   For service metrics, also record the query as-of time and compare `pendingTurns`: the final date
   may still contain turns whose response window has not matured. If the user requires fully matured
   results, move the end date back until the entire response window has elapsed and use an equal-length
   comparison period. Never treat pending turns as unanswered merely to complete the comparison.
6. Prefer the scenario explicitly declared by the user. Otherwise infer it with the rules below
   and label the source as `inferred`. Never hide ambiguity.
7. Apply the identity gate before service metrics. Use the scenario-specific flow below; a
   no-roster discovery response is not a service-performance result.
8. Run aggregate capabilities for both periods. Drill into no more than the three most important
   anomalies with intent, room, session, or raw-message capabilities.
9. Report the period, comparison period, filters, scenario source, identity source, classification
   coverage, evidence, limitations, and recommended actions. Respond in the user's language.

Start with:

```bash
ae-cli capability search "chat" --domain community
ae-cli capability inspect community.chat.list_intent_rules
ae-cli capability inspect community.chat.overview
```

Use `capability dry-run` when composing non-trivial filters, then execute with `capability run`.
All chat capabilities are read-only; medium risk means the response can contain identities or raw
conversation evidence, not that the capability mutates data.

## Capability map

| Task | Capability |
|---|---|
| Tenant intent discovery | `community.chat.list_intent_rules` |
| Server discovery and scale | `community.chat.list_servers` |
| Volume, room types, daily trend, intent, sentiment, alerts | `community.chat.overview` |
| Participant discovery and roster-driven response efficiency | `community.chat.service_metrics` |
| Rank or filter rooms | `community.chat.search_rooms` |
| List daily room sessions | `community.chat.list_sessions` |
| Read a bounded message page | `community.chat.list_messages` |
| Find individual intent detections | `community.chat.search_intents` |
| Aggregate intent topics | `community.chat.intent_instances` |
| Explain one intent topic | `community.chat.intent_detail` |
| Read evidence attached to one intent | `community.chat.intent_messages` |
| Find concentrated negative topics | `community.chat.negative_alerts` |
| Compare daily positive, neutral, and negative intent counts | `community.chat.sentiment_trend` |

`room_types` can contain `dm`, `group`, `public`, or `other`. Use `channel_ids` and
`chat_server_ids` only after discovering or receiving real IDs.

## Scenario selection

Prefer the user's declaration. If it is absent, use `overview.roomTypeDistribution` and server
discovery; participant roles are not available until a scenario-specific identity flow runs:

- Infer `customer_service` when DM messages are the clear majority.
- Infer `after_sales_group` when group messages are the clear majority and the rooms behave like
  support groups rather than public game channels.
- Infer `in_game_chat` when public/other messages are the clear majority or server dimensions are
  prominent.
- Use `generic_chat` when signals conflict or no type is a clear majority. State that the scenario
  cannot be inferred reliably and avoid service-performance conclusions.

Do not create a service identity roster for an in-game or generic scenario unless the user
explicitly requests service analysis. Do not call the metric phase without a complete verified or
inferred staff roster for the selected scope and at least one customer ID or the documented DM
customer fallback.

## Identity gate

**Single-agent questions still require the full staff roster.** In the documented DM fallback where
`customer_user_ids` is omitted, `service_metrics` classifies every message whose author is not in
`staff_user_ids` or `excluded_user_ids` as customer traffic. When an explicit customer list is
supplied, users outside all supplied identity lists remain unclassified and are filtered instead.
A roster containing only the target agent can therefore misattribute other agents as customers in
the fallback, or filter their work from an explicit-list analysis; either case invalidates the
roster-wide result. Always pass the complete staff roster, then read the target agent from its
`staffMetrics[]` entry -- never from the aggregate `response` block. When the inspected schema
exposes `focus_staff_user_id`, pass the target ID in that field in addition to the complete roster;
it is a drill-down selector, not a replacement for the roster.

Inspect the live `community.chat.service_metrics` schema before using these fields. The expected
call-scoped inputs are `staff_user_ids`, `customer_user_ids`, `excluded_user_ids`, and
`identity_source`; `focus_staff_user_id` is an optional evidence selector when exposed by the live
schema.

Use the same roster for the current and comparison periods. Discover candidates over the union of
both periods so a user who is inactive in one period is not silently reclassified. If that union
exceeds the maximum date range in the inspected schema, run discovery separately for each valid
window, paginate each result, then merge and deduplicate candidates before resolving the roster.
Never send an over-limit union range. Keep all identity lists disjoint.

### Discovery phase

Without staff or customer lists, call `community.chat.service_metrics` over the combined date range
only when that union fits the maximum range in the inspected live schema. Otherwise, do not attempt
the over-limit union: call each valid period separately, paginate both, then merge and deduplicate
their candidates. Reuse the intended room/channel/server filters for every discovery call. Set
`breakdown_limit` to the largest value allowed by the inspected live schema (currently 100) to
reduce accidental candidate truncation. Discovery deliberately returns
`availability:"unavailable"` plus `participantCandidates`. Use candidates only to resolve real
user IDs and choose bounded evidence.

**Detect likely automated / broadcast accounts from `participantCandidates`.** Signals include
`roomCount` approaching `messageCount`, `messagesPerRoom` approaching 1 (approximately one message
per room), coverage of hundreds or thousands of rooms, or uniform single-line posts. A high
`messageCount` or a low `messagesPerRoom` alone is not evidence of automation or staff activity.
Never place a suspected automated account in `staff_user_ids`; once bounded raw-message evidence
confirms automation, place it in `excluded_user_ids`.

Follow the inspected live schema for candidate pagination. When it exposes `page_num` and
`page_size`, fetch pages until `participantCandidatesPage.hasMore` is false, merging every page and
deduplicating by participant ID. Offset pagination is best-effort while late chat data is arriving,
so keep the filters and date window fixed, fetch pages consecutively, and disclose possible
duplicates or omissions if the source changes during the scan. If pagination is unavailable,
`participantCandidatesTruncated` remains true, or a paged result is still incomplete, run discovery
separately per `room_type`, or per server/channel filter when those dimensions apply, to surface
more candidates; merge and deduplicate the results. A roster that remains partial is not sufficient
for service KPIs: ask the user to complete it or use the non-service fallback, and disclose that
additional low-activity staff may remain uncovered. Do not claim exhaustive identity coverage or
quote response rates, response times, workload, or any other KPI from a discovery response.

If the response has no candidates, or roles cannot be established under the scenario rules below,
stop the service-metric workflow. Fall back to overview, intent, sentiment, activity, and bounded
evidence analysis. Explicitly state that service performance is unavailable because no usable
identity roster was supplied or inferred.

### After-sales group inference

For a declared or reliably inferred after-sales group scenario:

1. Start from `participantCandidates`. Prioritize candidates with enough activity to affect the
   result, including accounts active across multiple group rooms.
2. Read only a small evidence sample with `list_sessions` and `list_messages`: at most three
   representative group rooms and only enough messages to observe conversational role. Do not
   retrieve a full history merely to classify every participant.
3. Infer staff only from conversational behavior supported by evidence, such as repeatedly
   answering customer requests, coordinating follow-up, or serving several support groups. Infer
   customers from supported request or after-sales behavior. Never classify a role solely from a
   display name, message volume, sentiment, response speed, or demographic clues.
4. **User-ID format is a structural signal (distinct from a display name).** WeCom external-contact
   IDs (`wmnLKgCwAA…`, `wonLKgCwAA…`, `wrnLKgCwAA…`) are almost always customers; short internal
   handles (pinyin logins, `TD#####`) are staff. Use ID shape to prioritize candidates, then confirm
   staff by conversational behavior in evidence before adding anyone to `staff_user_ids`.
5. Leave ambiguous users unclassified. Omit them from both role lists. Put only confirmed bots,
   automated notifications, or system accounts in `excluded_user_ids`.
6. Resolve every plausible staff candidate into the complete inferred staff roster for the selected
   scope, and require at least one inferred customer ID. If discovery is incomplete or any plausible
   staff account remains unresolved, ask the user to complete the roster or use the non-service
   fallback; do not calculate service KPIs from a partial inferred roster.
7. Call `service_metrics` for each period with the same complete lists and
   `identity_source:"llm_inferred"`.

Example input fragment after inference:

```json
{
  "room_types": ["group"],
  "staff_user_ids": ["staff-user-id"],
  "customer_user_ids": ["customer-user-id"],
  "excluded_user_ids": ["system-user-id"],
  "identity_source": "llm_inferred"
}
```

Treat every LLM-inferred result as low confidence, regardless of classification coverage. Coverage
measures how much message traffic the supplied lists classify; it does not validate that inferred
roles are correct. Describe staff breakdowns as estimated operational workload, never as personnel
evaluation. The chat source does not provide staff departments: treat `department:null` as
unavailable and never infer or report a department. Include the inference basis and the material
unknown population in the report.

### Customer-service DM declaration

For customer-service DMs, do not infer employee identities from message text. Resolve the discovery
candidates, then require the user to declare the complete staff roster for the selected service
scope, even when the question targets one agent. Accept IDs directly; if the user supplies names,
map only unambiguous names to candidate IDs and ask for IDs when names collide.

Pass `staff_user_ids` with `identity_source:"user_declared"`. The customer list is optional:

- When the user supplies `customer_user_ids`, classify only those explicit customers.
- When the user omits it, the service treats every participant not in `staff_user_ids` or
  `excluded_user_ids` as a customer. Use this fallback only for DMs and disclose it prominently.
- Put known bot and system accounts in `excluded_user_ids`; never silently count them as customers.

Example input fragment with the DM fallback:

```json
{
  "room_types": ["dm"],
  "staff_user_ids": ["declared-staff-user-id-1", "declared-staff-user-id-2"],
  "excluded_user_ids": ["known-bot-user-id"],
  "identity_source": "user_declared"
}
```

If the user does not provide the complete staff roster after candidate discovery, do not output
customer-service performance. Continue with non-service chat analysis and state the missing
prerequisite.

## Customer-service DMs

Default to `room_types:["dm"]` unless the user specifies shared service channels.

1. Compare `overview` for current and previous periods.
2. Run the DM declaration flow above. Only after the user supplies the complete staff roster, compare
   `service_metrics` for both periods. The default response window is 1440 minutes. Pass
   `sla_minutes` only when the user supplies an SLA.
3. Use `search_intents` with `chat_type:"dm"` for room-type-scoped detections and
   `negative_alerts` with `room_types:["dm"]` for escalation. `intent_instances` does not support
   `room_types`; use it only when channel/server scope is sufficient, and disclose the broader
   room-type scope.
4. Drill into the largest unanswered, slowest, or most negative rooms and retrieve bounded evidence.

Report:

- Service health: customer/staff volume, service rooms, response rate, unanswered and pending turns,
  median and P90 response time, and period-over-period movement.
- Demand map: leading configured intents and emerging topics.
- Escalations: negative topics and rooms with supporting evidence.
- Workload: employee response turns, reply messages, rooms, customers, and response time.
- Actions: staffing, routing, knowledge-base, and follow-up recommendations tied to evidence.

Never claim resolution rate, transfer rate, customer satisfaction, or ticket closure. Those fields
are not present in the chat contract.

## Customer after-sales groups

Default to `room_types:["group"]`.

1. Compare group overview across the two periods, then run the bounded group identity inference.
   Compare `service_metrics` only if a complete inferred roster for the selected scope is produced;
   otherwise ask the user to complete it or use the non-service fallback.
2. Use room metrics to identify groups with many unanswered turns or slow P90 response.
3. Use `search_intents` with `chat_type:"group"` and group-filtered negative alerts to find issues
   recurring across groups. `intent_instances` cannot filter by room type; use it only with a valid
   channel/server scope and disclose that it may include other room types.
4. Drill into up to three group/topic combinations for short evidence excerpts.

Report:

- Group service coverage and response efficiency.
- A group risk matrix: room, request turns, unanswered/pending turns, response rate, P50/P90, and
  dominant negative or recurring topics.
- Cross-group issue clusters and the number of affected rooms.
- Estimated employee workload and suggested owners, labeled low confidence when roles were inferred.
- Prioritized containment, communication, and product-fix actions.

Treat group messages as conversation volume, not ticket volume. Do not infer that an issue is
resolved merely because an employee replied.

## In-game chat

Use all relevant room types; focus on `public`, `group`, and `other` rather than forcing a service
filter.

1. Compare overview volume, active rooms/users, room-type distribution, and daily trend.
2. Run `list_servers` for both periods and union the server IDs, then compare the selected servers
   with server-filtered overview calls using one consistent room-type scope. `list_servers` covers
   all room types and omits messages with an empty server ID, so disclose server-ID message coverage
   against an unfiltered overview before ranking servers.
3. Analyze intent topics, sentiment trend, concentrated negative alerts, and high-activity rooms.
4. Drill into up to three emerging or high-risk topics for evidence.

`intent_instances` supports server IDs but not room types; `search_intents` supports one chat type
but not server IDs. Do not claim a server-by-room-type intent comparison that the live contract
cannot express. Choose one verified dimension and disclose the limitation.

Report:

- Ecosystem health and period-over-period activity.
- Server/channel differences without ranking servers that lack comparable data.
- Emerging topics, intent changes, and negative concentration.
- High-risk rooms and short evidence excerpts.
- Community-operation, moderation, incident-response, or game-product actions.

Do not present customer-service KPIs when identity mapping is unavailable or irrelevant.

## Service metric semantics

- The response envelope has two levels. The top-level `response` and `volume` blocks are
  **roster-wide aggregates** and are only valid when the roster is complete. `staffMetrics[]` is
  **per-agent**. Answer single-agent questions from the matching `staffMetrics[]` entry, not the
  aggregate block.
- `staffMetrics[]` exposes per-agent workload and responded-turn timing, such as reply messages,
  responded turns, service rooms/customers, and average/P50/P90 response time. It does not expose
  a per-agent request-turn denominator, unanswered turns, `responseRate`, or `slaMetRate`. Never
  attribute roster-wide response/SLA rates or an unanswered turn to one employee, and do not derive
  a personal rate from fields that lack a valid denominator.
- When `focus_staff_user_id` is available, keep the complete `staff_user_ids` roster and use
  `focusedStaffTurns` for bounded evidence drill-down into that employee's slowest responded turns.
  A turn belongs to the focused employee only when that employee owns the first staff response.
  Never attribute an unanswered turn to an individual employee. Use the returned room, timestamps,
  and trigger/response message IDs to fetch only the evidence needed for the finding. When
  `focusedStaffTurnsTruncated` is true, disclose that only the slowest `breakdown_limit` turns were
  returned; do not present the bounded list as the employee's complete turn history.
- A request turn starts with a customer message. Consecutive customer messages remain one turn
  until the first employee response or an inactivity gap longer than `response_window_minutes`.
- The response deadline and response duration are measured from the turn's first customer message;
  customer follow-ups inside the same turn do not restart that clock.
- The first employee response closes and owns the turn. Later employee messages do not create
  additional responded turns.
- A response after the analysis end still counts when it falls inside the response window.
- A turn with no response is `pending` until its full response window has elapsed. Pending turns are
  excluded from the response-rate denominator. SLA uses its own observation threshold: a turn enters
  the SLA denominator once it has a response or has waited at least `sla_minutes`, even when it is
  still pending under a longer response window. For example, with a 24-hour response window and a
  30-minute SLA, an unanswered turn waiting one hour is pending but already SLA-eligible and missed.
- Average, median, and P90 response time use responded turns only.
- `identity_source:"llm_inferred"` is always low confidence. Never upgrade it based on coverage.
- A no-roster response is candidate discovery only. When metrics are unavailable, fall back to
  volume, intent, sentiment, and evidence analysis and state the reason.
- Classification coverage describes messages assigned by the supplied call-scoped roster. It is
  not evidence that the role assignments are correct.

## Evidence and privacy

- Use aggregate results first. Fetch raw messages only for a selected anomaly or explicit request.
- Do not paste full message pages. Quote the minimum excerpt that supports a finding.
- Mask or omit user IDs, phone numbers, order numbers, and other unnecessary identifiers.
- Separate measured facts from scenario inference and recommendations.
- If live data does not cover a scenario, say so; do not present fixture or inferred evidence as live.
