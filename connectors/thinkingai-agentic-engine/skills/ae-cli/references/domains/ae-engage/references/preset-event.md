# Preset event semantic definitions

Project preset add/active/recharge events use the same semantic event model as trigger events.

```bash
ae-cli engage-setting preset-event list --project-id <project_id>

ae-cli engage-setting preset-event update --project-id <project_id> \
  --add-event-definition '{"type":"event","event":"register","aggregation":"count","operator":"gte","value":1}' \
  --active-event-definition '{"type":"event","event":"login","aggregation":"count","operator":"gte","value":1}' \
  --recharge-event-definition '{"type":"event","event":"purchase","aggregation":"sum","property":"amount","operator":"gt","value":0}'
```

At least one definition is required for update. Event filters use semantic `field`, `operator`, `values`, and `and`/`or`; Hermes resolves project metadata and compiles the stored event object.
`field` accepts a technical-name string or `{"name":"...","type":"event_property"}`. Unknown
semantic fields, unsupported relations/operators, and invalid time ranges are rejected.

List hides the stored event QP and returns each semantic field plus its conversion status:

- `add_event_definition`
- `active_event_definition`
- `recharge_event_definition`

UI-saved preset events are often incomplete event selections. List fills write-path defaults (`operator=eq`, `value=1`) so these stay `AVAILABLE`. If conversion still fails for other reasons, status is `UNAVAILABLE` with an unavailable-reason field. Do not reconstruct definitions from raw internal QP codes.
