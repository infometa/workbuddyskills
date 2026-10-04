# 慢日志解读与优化指南

> 本文档为 [SKILL.md](../SKILL.md) 的详细参考。适用于 `DescribeInstanceLogs` 的慢日志分析。
>
> **LogType 语义**：`2` = 搜索慢日志（查询慢），`3` = 索引慢日志（写入慢）。二者是独立类型，需分别调用；
> `4` 是 GC 日志。完整取值见 [api/DescribeInstanceLogs.md](api/DescribeInstanceLogs.md#logtype-取值本表是-logtype-语义的唯一权威来源)。

---

## 慢日志关键字段解读

| 字段 | 含义 | 判断标准 |
|------|------|---------|
| `took` | 查询/写入耗时（ms） | 搜索 > 1000ms、写入 > 500ms 需关注 |
| `source` | 查询 DSL 原文 | 重点看 `wildcard`/`script`/深度聚合 |
| `total_shards` | 参与分片数 | 过多分片会放大延迟 |
| `types` | 查询类型 | `query_then_fetch` 为正常全文搜索 |

---

## 常见慢查询模式及优化建议

| 慢查询模式 | 识别特征 | 优化建议 |
|-----------|---------|---------|
| 前缀通配符 | `source` 中含 `"wildcard": {"field": "*keyword"}` | 改用 `edge_ngram` 或 `prefix` 查询 |
| Script 字段计算 | `source` 中含 `"script"` | 改用 `runtime_fields` 或预计算存储 |
| 深度聚合 | `source` 中含 `"size": >1000` 的 terms 聚合 | 改用 `composite` 聚合分页 |
| 无 filter 全量扫描 | `source` 中无时间范围 `filter` | 加时间范围 `filter` 缩小扫描范围 |
| 高基数 terms 聚合 | `source` 中 terms 聚合字段为 text 类型 | 改用 `.keyword` 字段或 `fielddata` |

---

> ⚠️ 慢日志优化建议属于 ES 通用知识，本 Skill 提供轻量指引。复杂 DSL 优化可参考 [ES 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)。
