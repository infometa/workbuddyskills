---
name: ae-analysis-global
version: 1.0.0
description: "Use when AE/TE analysis requests mention query/current/service/deployment clusters, current cluster (当前集群), cluster info (集群信息/有哪些集群), global or multi-cluster data, all clusters/all servers, GLOBAL/SLAVE, query-cluster, cluster_query_scope, slave_cluster_id, country/region/server/shard/site/market routing, or when cluster may mean query cluster rather than audience/user segment."
---

# ae-analysis-global


This is a terminology and routing overlay for `ae-analysis`. Read the base command reference [`../ae-analysis/references/query_cluster_list.md`](../ae-analysis/references/query_cluster_list.md) before composing the inventory command. Server output, not a local CLI feature switch, is authoritative for whether global query is enabled and which routes the account may use.

Every command accepts `--host <url>` to override the active AE host. Host selection is independent of `--cluster-query-scope`: `--host` chooses the AE instance, while `--cluster-query-scope` / `--slave-cluster-id` choose a physical query route inside that instance.

**CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice. (Also covered by `ae-analysis` Global Rules when both skills are loaded.)

## Routing Rules

- In this overlay, **查询集群 / 数据集群 / 部署集群** means physical multi-cluster routing for analysis queries. **用户分群 / 人群包** means user-membership assets under `analysis user-cluster`.
- If the user asks for query-cluster inventory or cluster info, call `ae-cli analysis query-cluster list --project-id <project_id>`. Localized examples include "查询集群信息" and "有哪些数据集群".
- Do not answer query-cluster inventory questions with `ae-cli analysis user-cluster list` unless the user explicitly asks for audience clusters, cohorts, segments, user membership, or cluster definitions.
- If the user mentions country, region, server, shard, site, market, or deployment area semantics, call `analysis query-cluster list` before choosing query scope.
- Match slave intent only against returned `slave_clusters[].cluster_id`, `cluster_name`, and `cluster_desc`.
- Report-data, dashboard-report-data, and ad-hoc run/export expose `--cluster-query-scope GLOBAL|SLAVE`; `SLAVE` requires `--slave-cluster-id`.
- Use `GLOBAL` only when the user clearly asks for all clusters/servers or cross-cluster aggregation and `permissions.can_query_global=true`.
- If the user does not express global or slave-cluster intent, omit the flag. Report/ad-hoc then use current self; dashboard follows its saved configuration.
- If a requested route is not allowed, explain `permissions.allowed_cluster_query_params` instead of silently falling back.
- SQL and attribution ad-hoc analysis do not support `GLOBAL`; SQL report/dashboard data also reject effective `GLOBAL`. Use an allowed `SLAVE` or current-self route.

## Response Wording

- For `analysis query-cluster list`, call the result "查询集群" or "query clusters" and summarize `current_cluster`, `slave_clusters`, and `permissions.allowed_cluster_query_params`.
- For `analysis user-cluster list`, call the result "audience clusters" or "user segments"; do not call those results query clusters.

## Query-cluster command

- `ae-cli analysis query-cluster list --project-id <project_id>`
