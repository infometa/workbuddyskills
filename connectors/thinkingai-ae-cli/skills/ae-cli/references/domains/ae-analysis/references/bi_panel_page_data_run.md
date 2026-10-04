# analysis bi-panel-page-data run

Use for inline BI panel page chart or summary data with the same result cap as the UI.

Routing: read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing this `run` command instead of `bi-panel-page-data export`.

Do not use this command when completeness matters, the result size is unknown, or the query is long-running; use `bi-panel-page-data export`.

Command:

```bash
ae-cli analysis bi-panel-page-data run --project-id <project_id> --panel-id <panel_id> --page-key <page_key> --result-type charts [--chart-ids '["chart1"]'] [--timeout-seconds 120]
```

Input sends `project_id`, `panel_id`, `page_key`, `result_type`, and optional control, cache, request, and timeout fields. `--timeout-seconds` defaults to 120 and is capped at 180. There are no row/block paging flags. Chart results use the configured top-N when enabled, otherwise the BI UI default cap of 20,000 rows, and return `has_more`. The routing rule lives in [`analysis_data_retrieval.md`](analysis_data_retrieval.md).

Output is the gateway envelope. `data` contains bounded inline page data.

BI page/chart sources are SQL and do not support analysis drilldown or result-cluster creation. Do not call model drilldown commands from this result.
