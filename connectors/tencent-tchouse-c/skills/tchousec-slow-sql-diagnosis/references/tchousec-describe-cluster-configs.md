
# tchousec-describe-cluster-configs

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeClusterConfigs` 云 API，获取指定集群的所有配置文件内容（包括 config.xml、users.xml、metrika.xml 等）。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeClusterConfigs`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称   | 必选 | 类型   | 描述                                 |
| ---------- | ---- | ------ | ------------------------------------ |
| InstanceId | 是   | String | 集群实例 ID，格式如 `cdwch-xxxxxxxx` |
| Region     | 是   | String | 地域，如 `ap-guangzhou`              |

## 输出参数

| 参数名称                      | 类型   | 描述                                                      |
| ----------------------------- | ------ | --------------------------------------------------------- |
| ClusterConfList               | Array  | 集群配置文件列表                                          |
| ClusterConfList[].FileName    | String | 配置文件名称，如 `config.xml`、`users.xml`、`metrika.xml` |
| ClusterConfList[].FilePath    | String | 配置文件路径，如 `/etc/clickhouse-server`                 |
| ClusterConfList[].FileConf    | String | 配置文件的明文内容（XML 格式或纯文本）                    |
| ClusterConfList[].KeyConf     | String | KV 格式的配置内容（通常为空字符串）                       |
| ClusterConfList[].NeedRestart | Int    | 修改后是否需要重启（0: 不需要，1: 需要）                  |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeClusterConfigs",
  "Version": "2020-09-15",
  "Region": "ap-chongqing",
  "InstanceId": "cdwch-xxxxxxxx"
}
```

### 响应示例

```json
{
  "Response": {
    "ClusterConfList": [
      {
        "FileName": "config.xml",
        "FilePath": "/etc/clickhouse-server",
        "FileConf": "<?xml version=\"1.0\"?>\n<yandex>\n    <max_connections>4096</max_connections>\n    <keep_alive_timeout>120</keep_alive_timeout>\n    <max_concurrent_queries>100</max_concurrent_queries>\n    <max_thread_pool_size>20000</max_thread_pool_size>\n    <uncompressed_cache_size>8589934592</uncompressed_cache_size>\n    <mark_cache_size>10737418240</mark_cache_size>\n    <merge_tree>\n        <parts_to_throw_insert>4096</parts_to_throw_insert>\n        <parts_to_delay_insert>2048</parts_to_delay_insert>\n    </merge_tree>\n    ...\n</yandex>",
        "KeyConf": "",
        "NeedRestart": 0
      },
      {
        "FileName": "metrika.xml",
        "FilePath": "/etc/clickhouse-server",
        "FileConf": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<yandex>\n    <clickhouse_remote_servers>\n        <default_cluster>\n            <shard>\n                <internal_replication>true</internal_replication>\n                <replica>\n                    <host>10.0.4.75</host>\n                    <port>9000</port>\n                </replica>\n            </shard>\n        </default_cluster>\n    </clickhouse_remote_servers>\n    <zookeeper-servers>\n        <node><host>10.0.4.199</host><port>2181</port></node>\n    </zookeeper-servers>\n</yandex>",
        "KeyConf": "",
        "NeedRestart": 0
      },
      {
        "FileName": "users.xml",
        "FilePath": "/etc/clickhouse-server",
        "FileConf": "<yandex>\n    <profiles>\n        <default>\n            <max_threads>2</max_threads>\n            <max_insert_threads>2</max_insert_threads>\n            <max_memory_usage>3200000000</max_memory_usage>\n            <max_query_size>524288</max_query_size>\n            <load_balancing>random</load_balancing>\n        </default>\n    </profiles>\n    ...\n</yandex>",
        "KeyConf": "",
        "NeedRestart": 0
      },
      {
        "FileName": "hosts",
        "FilePath": "/etc",
        "FileConf": "127.0.0.1 VM-16-16-centos VM-16-16-centos\n127.0.0.1 localhost.localdomain localhost",
        "KeyConf": "",
        "NeedRestart": 0
      }
    ],
    "RequestId": "a54778bd-6423-4cf7-a455-62efd294595f"
  }
}
```

## 配置文件说明

| 文件名      | 用途                                                              |
| ----------- | ----------------------------------------------------------------- |
| config.xml  | ClickHouse 服务端主配置，包含端口、连接数、缓存、MergeTree 参数等 |
| users.xml   | 用户配置，包含 profile 级别的查询限制（内存、超时、并发线程等）   |
| metrika.xml | 集群拓扑配置，包含 remote_servers、ZooKeeper 地址、macros 等      |
| hosts       | 主机名解析配置                                                    |

## 慢 SQL 诊断相关的关键配置项

### config.xml 中的关键配置

| 配置项（XML 路径）                 | 说明                     | 对慢 SQL 的影响              |
| ---------------------------------- | ------------------------ | ---------------------------- |
| `max_concurrent_queries`           | 最大并发查询数           | 过低导致查询排队等待         |
| `max_connections`                  | 最大连接数               | 连接数耗尽导致新查询无法执行 |
| `max_thread_pool_size`             | 线程池大小               | 影响查询并行执行能力         |
| `uncompressed_cache_size`          | 未压缩数据缓存大小       | 影响热数据查询性能           |
| `mark_cache_size`                  | Mark 缓存大小            | 影响 MergeTree 索引查找性能  |
| `merge_tree.parts_to_throw_insert` | 触发 insert 拒绝的分区数 | 过多 parts 导致查询变慢      |
| `merge_tree.parts_to_delay_insert` | 触发 insert 延迟的分区数 | parts 过多时写入被限速       |
| `keep_alive_timeout`               | 连接保活超时             | 影响连接复用效率             |

### users.xml 中的关键配置

| 配置项                               | 说明                 | 对慢 SQL 的影响                |
| ------------------------------------ | -------------------- | ------------------------------ |
| `max_threads`                        | 查询并发线程数       | 影响单查询并行度               |
| `max_insert_threads`                 | INSERT 并发线程数    | 影响写入性能                   |
| `max_memory_usage`                   | 单次查询最大内存     | 过低会导致查询 OOM 失败        |
| `max_query_size`                     | 最大查询文本长度     | 过低导致复杂 SQL 被拒绝        |
| `background_pool_size`               | 后台合并线程池大小   | 影响 MergeTree 合并速度        |
| `max_distributed_connections`        | 分布式查询最大连接数 | 影响分布式查询并发能力         |
| `max_memory_usage_for_all_queries`   | 所有查询总内存上限   | 0 表示不限制                   |
| `max_bytes_before_external_sort`     | 外部排序阈值         | 超过此值使用磁盘排序，性能下降 |
| `max_bytes_before_external_group_by` | 外部 GROUP BY 阈值   | 超过此值使用磁盘聚合           |
| `max_execution_time`                 | 查询超时时间（秒）   | 超时自动终止                   |
| `join_algorithm`                     | JOIN 算法            | hash/partial_merge/auto 等     |
| `max_bytes_in_join`                  | JOIN 哈希表最大内存  | 超过会失败或降级               |
| `max_rows_to_read`                   | 最大读取行数         | 限制全表扫描                   |
| `max_bytes_to_read`                  | 最大读取字节数       | 限制大查询                     |
| `load_balancing`                     | 副本负载均衡策略     | random/nearest_hostname 等     |

## 典型使用场景

- **配置瓶颈排查**：解析 config.xml 和 users.xml，判断是否因 `max_memory_usage` 过低导致查询失败或降级
- **并发能力评估**：通过 `max_concurrent_queries` 和 `max_thread_pool_size` 评估集群并发处理能力
- **缓存配置评估**：通过 `uncompressed_cache_size` 和 `mark_cache_size` 判断缓存是否充足
- **MergeTree 健康度**：通过 `parts_to_throw_insert`/`parts_to_delay_insert` 判断是否存在 parts 过多问题
- **JOIN 策略确认**：从 users.xml 中确认当前 `join_algorithm` 是否最优
- **优化建议生成**：基于当前配置和查询特征，建议调整特定配置项
- **超时分析**：确认 `max_execution_time` 是否合理，是否有查询因超时被终止
- **集群拓扑确认**：通过 metrika.xml 确认分片和副本拓扑，辅助分布式查询分析

## 配置优化建议策略

| 问题现象   | 可能的配置原因                          | 建议调整                          |
| ---------- | --------------------------------------- | --------------------------------- |
| 查询 OOM   | max_memory_usage 过低                   | 适当调高，或优化 SQL 减少内存使用 |
| 查询超时   | max_execution_time 过短                 | 调高超时或优化 SQL                |
| 排序慢     | max_bytes_before_external_sort 过低     | 调高阈值避免磁盘排序              |
| JOIN 慢    | join_algorithm 不合适                   | 根据数据量选择合适算法            |
| 并发低     | max_concurrent_queries/max_threads 过低 | 适当调高并发配置                  |
| 查询排队   | max_concurrent_queries 过低             | 调高并发查询数上限                |
| 索引查找慢 | mark_cache_size 过小                    | 增大 Mark 缓存                    |

## 注意事项

- `FileConf` 字段返回的是完整的配置文件内容（XML 或纯文本），需要解析提取具体配置项
- 配置文件可能很长（尤其是 config.xml），分析时应聚焦于慢 SQL 诊断相关的配置项
- 不同集群版本的配置项可能有差异，需结合 `DescribeInstance` 返回的版本号判断
- 此接口不依赖 `EnableConfigKeyValue` 开关，任何集群都可调用
- `metrika.xml` 中包含集群拓扑（分片/副本）和 ZooKeeper 信息，对分布式查询分析至关重要
- `users.xml` 中 `<profiles><default>` 下的配置是所有用户的默认查询限制
