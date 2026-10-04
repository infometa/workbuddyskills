# Complete Requests

Each block is a complete public MCP request. Replace discovered IDs and
attribute expressions with values from the target environment. The examples
are ordered by the public enum.

Every `attr_id` below is a write target returned by `create_attribute` (or an
explicitly selected compatible derived attribute), never the ID of the raw
attribute referenced in its expression. For a new calculated result, complete
this two-step workflow after validating the rest of the analysis request:

```json
{"element_id":10,"name":"Current 5m Maximum","value_type":"Double","reuse_if_exists":false}
```

Use the returned `attribute_id` in the analysis output:

```json
{"element_id":10,"name":"Previous-hour current maximum every 5 minutes","root_element_id":99,"trigger_type":"Interval","trigger":{"sliding":"5m"},"output":{"attributes":[{"attr_id":101,"attr_name":"Current 1h Maximum","expression":"MAX(${attributes['Current']})"}],"rollup_window":{"enabled":true,"interval":"1h"}}}
```

If the analysis call fails, retry with target `101`; do not create another
attribute. Event-only analyses may keep `output.attributes` empty.

<!-- complete-example: period -->
```json
{"element_id": 10, "name": "period sample", "root_element_id": 99, "trigger_type": "Period", "trigger": {"periodTime": "1m", "offsetTime": "0s"}, "output": {"attributes": [{"attr_id": 101, "attr_name": "scheduled latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: anomaly-detection -->
```json
{"element_id": 10, "name": "anomaly sample", "root_element_id": 99, "trigger_type": "AnomalyDetection", "trigger": {"sliding": "1m", "anomalyDetectionConfig": {"algorithm": "iqr", "whiteNoiseDataCheck": true, "algorithmParameters": "k=1.5", "targetAttributeExpressions": ["${attributes['value']}"]}}, "output": {"attributes": [{"attr_id": 102, "attr_name": "anomaly latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: count -->
```json
{"element_id": 10, "name": "count sample", "root_element_id": 99, "trigger_type": "Count", "trigger": {"count": 2, "slidingCount": 0, "expressions": ["${attributes['value']}"]}, "output": {"attributes": [{"attr_id": 103, "attr_name": "count-window latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: interval -->
```json
{"element_id": 10, "name": "interval sample", "root_element_id": 99, "trigger_type": "Interval", "trigger": {"sliding": "1m"}, "output": {"attributes": [{"attr_id": 104, "attr_name": "interval latest value", "expression": "LAST(${attributes['value']})"}], "rollup_window": {"enabled": false}}}
```

<!-- complete-example: state -->
```json
{"element_id": 10, "name": "state sample", "root_element_id": 99, "trigger_type": "State", "trigger": {"states": ["${attributes['status']}"], "trueForMode": "DURATION", "duration": "1m"}, "output": {"attributes": [{"attr_id": 105, "attr_name": "state-window latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: session -->
```json
{"element_id": 10, "name": "session sample", "root_element_id": 99, "trigger_type": "Session", "trigger": {"interval": "1m"}, "output": {"attributes": [{"attr_id": 106, "attr_name": "session latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: event -->
```json
{"element_id": 10, "name": "event sample", "root_element_id": 99, "trigger_type": "Event", "trigger": {"eventTrigger": {"starts": [{"name": "high", "expression": "${attributes['value']} > 10", "parameters": [{"label": "A", "type": "variable", "detail": "attributes['value']", "apply": "${attributes['value']}"}], "duration": "1m", "trueForMode": "DURATION", "allowAck": true, "severityLevel": "Information"}], "end": {"expression": "${attributes['value']} <= 10", "parameters": []}}}, "event": {"template_id": 77, "severity_level": "Major"}, "output": {"apply_on_self": true, "attributes": []}}
```

<!-- complete-example: data-input -->
```json
{"element_id": 10, "name": "data input sample", "root_element_id": 99, "trigger_type": "DataInput", "trigger": {"slidingCount": 0, "expressions": ["${attributes['value']}"]}, "output": {"attributes": [{"attr_id": 107, "attr_name": "per-row latest value", "expression": "LAST(${attributes['value']})"}]}}
```

<!-- complete-example: spc -->
```json
{"element_id": 10, "name": "spc sample", "root_element_id": 99, "trigger_type": "SPC", "trigger": {"spcConfig": {"targetAttributeExpression": "${attributes['value']}", "rules": [1, 2]}}, "event_template_id": 77, "output": {"apply_on_self": true, "attributes": []}}
```

The child-output form below is a partial fragment, not a complete example. It
shows the normalized tag input and is valid only after public tag discovery.

<!-- partial-example: child-output -->
```json
{"apply_on_self":false,"element_template":{"id":20},"partition_by_tags":["region","${attributes['site']}"] ,"attributes":[{"attr_id":108,"attr_name":"child latest value","expression":"LAST(${attributes['value']})"}]}
```

## Complete Cross-Field Requests

These requests cover paths which are conditional rather than separate trigger
types. Replace every ID, expression, tag, and template with publicly discovered
values before calling the tool.

<!-- complete-example: child-output -->
```json
{"element_id":10,"name":"child output sample","root_element_id":99,"trigger_type":"Period","trigger":{"periodTime":"1m"},"output":{"apply_on_self":false,"element_template":{"id":20},"partition_by_tags":["region"],"attributes":[{"attr_id":108,"attr_name":"child latest value","expression":"LAST(${attributes['value']})"}]}}
```

<!-- complete-example: enabled-rollup -->
```json
{"element_id":10,"name":"rollup sample","root_element_id":99,"trigger_type":"Count","trigger":{"count":2,"slidingCount":0,"expressions":["${attributes['value']}"]},"output":{"attributes":[{"attr_id":109,"attr_name":"rollup latest value","expression":"LAST(${attributes['value']})"}],"rollup_window":{"enabled":true,"interval":"1m","start_time":"_wstart","end_time":"_wend","start_time_offset":"0s","end_time_offset":"0s"}}}
```

<!-- complete-example: event-multi-start -->
```json
{"element_id":10,"name":"multi start event sample","root_element_id":99,"trigger_type":"Event","trigger":{"eventTrigger":{"starts":[{"name":"high","expression":"${attributes['value']} > 10","trueForMode":"DURATION","duration":"1m"},{"name":"critical","expression":"${attributes['value']} > 20","trueForMode":"DURATION","duration":"1m"}],"end":{"expression":"${attributes['value']} <= 10"}}},"event_template_id":77,"severity":"Major","output":{"apply_on_self":true,"attributes":[]}}
```

<!-- complete-example: event-outside-normal-range -->
```json
{"element_id":10,"name":"outside normal range sample","root_element_id":99,"trigger_type":"Event","trigger":{"eventTrigger":{"starts":[{"name":"below normal","expression":"${attributes['value']} < 2","trueForMode":"DURATION","duration":"1m","allowAck":true,"severityLevel":"Major"},{"name":"above normal","expression":"${attributes['value']} > 10","trueForMode":"DURATION","duration":"1m","allowAck":true,"severityLevel":"Major"}],"end":{"expression":"${attributes['value']} >= 2 AND ${attributes['value']} <= 10"}}},"event":{"template_id":77,"severity_level":"Major"},"output":{"apply_on_self":true,"attributes":[]},"start_after_created":true}
```

<!-- complete-example: spc-all-rules -->
```json
{"element_id":10,"name":"extended spc sample","root_element_id":99,"trigger_type":"SPC","trigger":{"spcConfig":{"targetAttributeExpression":"${attributes['value']}","rules":[1,2,3,4,5,6,7,8]}},"event_template_id":77,"output":{"apply_on_self":true,"attributes":[]}}
```

<!-- complete-example: action-rule -->
```json
{"element_id":10,"name":"action sample","root_element_id":99,"trigger_type":"Period","trigger":{"periodTime":"1m"},"output":{"attributes":[{"attr_id":110,"attr_name":"action latest value","expression":"LAST(${attributes['value']})"}]},"actions":[{"condition_expression":"${attributes['value']} > 10","action_template_id":88}]}
```

<!-- complete-example: event-output-only -->
```json
{"element_id":10,"name":"event output without generated event","root_element_id":99,"trigger_type":"Event","trigger":{"eventTrigger":{"starts":[{"name":"high","expression":"${attributes['value']} > 10","duration":"1m","trueForMode":"DURATION","allowAck":true,"severityLevel":"Information"}],"end":{"expression":"${attributes['value']} <= 10"}}},"output":{"attributes":[{"attr_id":111,"attr_name":"event latest value","expression":"LAST(${attributes['value']})"}]}}
```
