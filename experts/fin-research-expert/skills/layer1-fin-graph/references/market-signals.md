# Market Signals Reference

Read this for industry index discovery, generated viewpoints, crowding, anomalies, anomaly details, and macro graph panels.

For empty-result and source-boundary wording, also read `references/limitations.md`.

## Industry Indices And Views

### `list_industry_indices`

Use to discover industry index names/codes and current change.
- `limit`: 1-500

### `get_industry_views`

Use for generated industry viewpoints.
- `index_codes`: values returned by `list_industry_indices`, `list_supported_subjects`, or resolver target fields

必要时再用 `list_industry_indices` 找到精确 `index_code`. Do not把行业名称直接塞进 `index_codes`; 不要把行业名当成指数代码.

If it returns "当前未返回已生成观点", only say this `index_code` has no generated viewpoint in this call; 不要扩写成该行业没有观点、没有研报或没有新闻.

## Crowding

### `get_industry_crowding`

Use for industry crowding analysis.
- `industry_name`: returned industry name
- `industry_level`: `industry01`, `industry02`, `industry03`

If using a parent-industry fallback, state the fallback口径.

## Anomalies

### `list_industry_anomalies`

Use for existing anomaly records.
- `date`
- `index_names`
- `page`
- `page_size`: max 100

### `get_anomaly_detail`

Use only after `list_industry_anomalies` returns `anomaly_id`.
- `anomaly_id`
- `output_format`: `json` or `markdown`

必须先从 `list_industry_anomalies` 的结果中拿到 `anomaly_id`; do not create IDs from titles, names, or page numbers.

## Macro Panels

### `get_macro_data`

Use for China/global macro graph panels.
- `scope`: `all`, `china_macro`, `global_macro`, or Chinese aliases
- `indicators`
- `max_points_per_series`: 1-60

Default China macro coverage includes northbound funds, margin balance, social financing, M1/M2, PMI, GDP, confidence, unemployment, industrial production, LPR, DR007/CD, USD/CNY central parity, RRR, MLF, OMO, deficit ratio, and local special bonds.

`USDCNY_mid`, `美元兑人民币中间价`, and `人民币中间价` resolve to the central-parity series. Do not describe that series as onshore spot CNY, a closing price, or offshore `USDCNH`.

`get_macro_data` is a compact graph panel with at most 60 recent points per series. Use Fin Data `search_macro_indicators` plus paginated `query_macro_series` when the user requests longer dated history.

Default global macro coverage includes VIX, global major indices, Fed funds, US Treasury yields, dollar index, nonfarm payrolls, unemployment, wages, core CPI/PCE, ISM PMI, Michigan confidence, US GDP, and Chicago FCI.

## Few-Shot

- "半导体设备今天有没有观点" -> resolve identity, find `market_index_code` or run `list_industry_indices`, then `get_industry_views`.
- "最近有什么行业异动" -> `list_industry_anomalies(page=1, page_size=10)`, then detail only with returned `anomaly_id`.
- "中国宏观面板" -> `get_macro_data(scope="china_macro")`.
