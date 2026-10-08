# engage-scene.report.config-item-analysis

Query config item analysis results through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-scene.report.config-item-analysis --input '<json>'`

Required input: `project_id`, `config_id`, `start_time`, `end_time`. Optional input: `request_id`,
`template_id_list`, `strategy_id_list`, `show_time_zone`. `template_id_list` and `strategy_id_list`
are mutually exclusive.

## Input contract

| Field | JSON type | Required | Rules |
| --- | --- | --- | --- |
| `project_id` | integer | Yes | Positive project ID. |
| `config_id` | string | Yes | Config item ID. |
| `start_time` | string | Yes | Date in `yyyy-MM-dd` format. |
| `end_time` | string | Yes | Date in `yyyy-MM-dd` format; must not be earlier than `start_time`. |
| `request_id` | string | No | Request identifier for continuation or cancellation. |
| `template_id_list` | array of strings | No | Cannot be used together with `strategy_id_list`. |
| `strategy_id_list` | array of strings | No | Cannot be used together with `template_id_list`. |
| `show_time_zone` | number | No | Hour offset from `-12.0` through `14.0`; use `8`, not the string `"8"`. |

```bash
ae-cli capability run engage-scene.report.config-item-analysis \
  --input '{"project_id":1,"config_id":"cfg_123","start_time":"2026-04-01","end_time":"2026-04-07","show_time_zone":8}'
```
