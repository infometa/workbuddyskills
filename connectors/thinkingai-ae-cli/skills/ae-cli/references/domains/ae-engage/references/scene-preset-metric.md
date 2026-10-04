# Scene preset metric semantic events

Config-item impression, click, and attend metrics are stored as event QP but exposed to the CLI as semantic event definitions.

```bash
ae-cli engage-scene preset-metric get --project-id <project_id> --config-id <config_id>

ae-cli engage-scene preset-metric set --project-id <project_id> --config-id <config_id> \
  --impression-event-definition '{"type":"event","event":"impression","aggregation":"count","operator":"gte","value":1}' \
  --click-event-definition '{"type":"event","event":"click","aggregation":"count","operator":"gte","value":1}' \
  --attend-event-definition '{"type":"event","event":"attend","aggregation":"count","operator":"gte","value":1}'
```

All three event flags are optional; an omitted definition clears that stored preset event, preserving existing set semantics. Resolve real event/property metadata before writing.

Get returns the three semantic definitions with per-field conversion status and never returns raw event QP.
