---
name: nexa-knowledge
description: 用 Nexa Knowledge 连接器查询用户的数据：找表、查数、检索业务知识。用户问业务数据、表结构、指标口径或业务规则时使用。
---

# Nexa Knowledge

每次调用独立，工具看不到对话历史。

## 查数流程

1. `list_worlds` 拿 `world_id`。之后所有 `world_id` 只能用它返回的值；报
   "is not an available world" 就重新调 `list_worlds`。
2. 业务问题先 `link_schema(world_id, question)`，不要先遍历全部目录。多轮追问时把
   `question` 改写成自包含的一句话。
3. 问题里有具体名称、编码等字面量时，先 `lookup_value_index(values)` 定位，再把命中
   的字面量放进 `link_schema` 的 `values`。
4. 用 `link_schema` 返回的模型名和列名写语义 SQL，调
   `semantic_sql_query(world_id, semantic_sql)`。
5. 只有结果里 `fallback_suggested=true` 时才调
   `execute_fallback_sql(world_id, physical_sql, failed_semantic_sql)`，
   `failed_semantic_sql` 填刚才失败的语义 SQL。
6. 分页用工具自己的 `offset` / `limit`。

不要猜表名和列名。查出 0 行时先核对
过滤条件和数据范围（例如先按年份分组看数据从哪年开始），再下结论。

## 其他工具

| 场景 | 工具 |
| --- | --- |
| 盘点一个世界有哪些表、哪些业务域 | `inventory_world_catalog(world_id)` |
| 按业务域分页浏览模型 | `list_world_domains`，再 `list_world_manifests(world_id, domain_id)` |
| 展开模型的完整列、物理表和关联 | `get_world_manifests(world_id, names)`，一次 1–10 个 |
| 看某一列有哪些取值 | `probe_column_values(world_id, model, column)`，可带 `contains` |
| 某个客户 / 公司 / 品牌在哪些表出现 | `expand_entity_footprint(world_id, entity_names, concepts)` |
| 业务定义、规则、流程等表结构里没有的知识 | `search_knowledge(question)`，再 `read_knowledge` / `expand_knowledge` |
| 一个世界有哪些知识文档 | `list_knowledge_assets(world_id)` |

## 大结果

结果过大时返回 `result_ref` 和 JSON 预览。先看预览，证据不够才调
`read_result(result_ref)`，带回 `next_cursor` 继续读，读够就停。`result_ref` 只在本机
保留 24 小时。

## 错误与恢复

| 现象 | 处理 |
| --- | --- |
| 签名失败、SecretId 不存在 | 密钥错误，请用户在连接器里重新填写 SecretId / SecretKey |
| 未授权（CAM） | 请用户给该密钥授权 `DescribeDataAgentTools`、`CallDataAgentTool` |
| "is not an available world" | `world_id` 不对，重新调 `list_worlds` |
| `list_worlds` 返回空 | 该账号下还没有可查询的世界，如实告诉用户 |
| 超时 | 缩小问题范围或加过滤条件后重试一次 |
