# engage-scene.report.strategy-comparison

Compare config strategy results through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-scene.report.strategy-comparison --input '<json>'`

Required input: `project_id`, `config_id`, `strategy_id_list` with at least two IDs. Optional input:
`request_id`, `show_time_zone`.

## Input contract

| Field | JSON type | Required | Rules |
| --- | --- | --- | --- |
| `project_id` | integer | Yes | Positive project ID. |
| `config_id` | string | Yes | Config item ID. |
| `strategy_id_list` | array of strings | Yes | Must contain at least two strategy IDs. |
| `request_id` | string | No | Request identifier for continuation or cancellation. |
| `show_time_zone` | number | No | Hour offset from `-12.0` through `14.0`; use `8`, not the string `"8"`. |

```bash
ae-cli capability run engage-scene.report.strategy-comparison \
  --input '{"project_id":1,"config_id":"cfg_123","strategy_id_list":["strategy_a","strategy_b"],"show_time_zone":8}'
```
