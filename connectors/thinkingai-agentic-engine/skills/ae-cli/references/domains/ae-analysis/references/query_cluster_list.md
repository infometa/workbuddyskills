# analysis query-cluster list

List physical query-routing clusters accessible to the current account in one project.

## Terminology boundary

Both product concepts contain the English word `cluster`, but they are different:

- 查询集群 / 数据集群 / 部署集群: physical data-routing locations used by `GLOBAL` and `SLAVE`. This command lists these.
- 用户分群 / 人群包: saved user-membership assets. Use `analysis user-cluster list` for these.

Never use a 用户分群 ID as `--slave-cluster-id`, and never answer a user-segment inventory question with this command.

## Purpose

Use this capability before routing a report, dashboard, or ad-hoc query when the request mentions all clusters, a country/region, a game server, shard, site, market, or deployment. Do not call it for ordinary queries with no physical routing intent; omission preserves the query surface's documented default.

## Command

```bash
ae-cli analysis query-cluster list --project-id <project_id>
```

The snake_case output contains `current_cluster`, accessible `slave_clusters`, and `permissions.allowed_cluster_query_params`. `permissions.can_query_global` is authoritative for `GLOBAL`; only returned `slave_clusters[].cluster_id` values may be used for `SLAVE`.

## Typical workflow

1. Resolve the project and call `analysis query-cluster list`.
2. Match an explicit region/server request only against returned cluster ID, name, and description.
3. Use `--cluster-query-scope GLOBAL` only for explicit cross-cluster aggregation, or use `--cluster-query-scope SLAVE --slave-cluster-id <id>` for one matched physical slave cluster.
4. Run/export through `report-data`, `dashboard-report-data`, or `adhoc`.
5. For synchronous runs, verify `actual_cluster_query_scope`, `actual_slave_cluster_id`, and `cluster_query_scope_source` in the result. For exports, verify the submitted route and successful run before consuming the artifact; report-data artifacts contain report rows rather than route metadata. If permissions reject the route, report `allowed_cluster_query_params`; do not fall back silently.

Surface defaults differ: report-data and ad-hoc omit scope to query the current self cluster; dashboard-report-data omits scope to follow the saved dashboard configuration.
