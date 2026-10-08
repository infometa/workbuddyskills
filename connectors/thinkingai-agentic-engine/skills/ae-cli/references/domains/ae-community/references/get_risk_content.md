# ae-community +get_risk_content


Query content marked as risk/audit and support filtering by risk type and time. Optional return trend aggregation.

Mapping command: `ae-cli community +get_risk_content`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--space-id` | number | yes | community space ID |
| `--game-id` | number | yes | game/space ID |
| `--start-time` | string | Yes | Lower limit of release time for risky content, format yyyy-MM-dd |
| `--end-time` | string | yes | upper limit of release time for risky content, format yyyy-MM-dd |
| `--risk-codes` | string | No | List of risk type codes, comma separated |
| `--search-word` | string | No | Keyword search, text fuzzy matching |
| `--include-trends` | boolean | No | Whether to return trend aggregation |
| `--order-by` | number | no | sort: 0 release time desc |
| `--page-num` | number | No | Page number, starting from 1 |
| `--page-size` | number | No | Number of items per page |

## Example

```bash
# Query risk content
ae-cli community +get_risk_content \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07

# Filter by risk type
ae-cli community +get_risk_content \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07 \
  --risk-codes 1,2

# Keyword search
ae-cli community +get_risk_content \
  --space-id 1 --game-id 1 \
  --start-time 2024-01-01 --end-time 2024-01-07 \
--search-word "violating keywords"
```
