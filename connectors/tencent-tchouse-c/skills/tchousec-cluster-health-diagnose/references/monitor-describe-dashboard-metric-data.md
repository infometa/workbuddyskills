# monitor-describe-dashboard-metric-data

## 功能说明

通过 Monitor 产品的 DescribeDashboardMetricData 接口查询 TCHouse-C（QCE/CDWCH）集群的监控指标数据。支持集群级和节点级指标查询，可批量查询多个指标。

## 工具类型

- **实现方式**：MCP tool（由 TCHouseC MCP Server 封装）
- **协议**：SSE / Streamable HTTP
- **产品**：monitor（非 cdwch）

## MCP Tool 输入参数

> ⚠️ **重要**：Agent 调用此工具时使用以下**扁平化参数**，MCP Server 会自动将其转换为底层 API 所需的嵌套结构（包括自动注入 Module、Namespace、Datasource 等固定字段）。

| 参数名 | 必选 | 类型 | 描述 |
|--------|------|------|------|
| Region | 是 | String | 地域字符串，如 `ap-guangzhou`、`ap-shanghai`、`ap-beijing` |
| RegionId | 是 | Number | 地域数字ID（ap-guangzhou=1, ap-shanghai=4, ap-beijing=8, ap-nanjing=33, ap-chengdu=16, ap-chongqing=19, ap-singapore=9, ap-hongkong=5） |
| InstanceId | 是 | String | 集群实例ID，格式如 `cdwch-xxxxxxxx` |
| MetricNames | 是 | String | 要查询的指标名称列表，**用英文逗号分隔**，使用**驼峰格式**（如 `SumCpuUsage,SumMemUsage,SumDiskUsage`） |
| NodeCount | 否 | Number | CK节点数量。**查询集群聚合指标（Sum/Ck开头）时必填**，用于构造 Dimension 数组。通过 `TCHouseCDescribeInstanceNodes` 获取 |
| NodeIps | 否 | String | 节点IP列表，**用英文逗号分隔**。**查询节点级指标时必填**（通过 `TCHouseCDescribeInstanceNodes` 获取）。集群聚合指标不需要传此参数 |
| StartTime | 是 | String | 起始时间，**ISO 8601 格式**，如 `2026-06-11T18:00:00+08:00` |
| EndTime | 是 | String | 结束时间，**ISO 8601 格式**，如 `2026-06-11T19:00:00+08:00` |
| Period | 否 | Number | 数据粒度（秒），可选 60/300/3600。默认 60 |

### 参数使用规则

**规则 1：查询集群聚合指标**（MetricName 以 Sum/Ck/Cluster 开头）：
- 必须传 `NodeCount`（CK 节点数），不传 `NodeIps`
- MCP Server 会自动构造 N 个相同的 `{"InstanceId":"xxx"}` Dimension

**规则 2：查询 CK 节点级指标**（如 CpuUsage、MemUsage、DiskUsage 等）：
- 必须传 `NodeIps`（CK 节点 IP，通过 NodeRole=DATA 获取），不传 `NodeCount`
- MCP Server 会自动构造 `{"ip":"xxx","InstanceId":"xxx"}` Dimension（ip 在前）

**规则 3：查询 Keeper/ZK 节点指标**（如 KeeperUp、ZkUp 等）：
- 必须传 `NodeIps`（Keeper/ZK 节点 IP，通过 NodeRole=COMMON 获取），不传 `NodeCount`
- MCP Server 会自动构造 `{"ip":"xxx","InstanceId":"xxx"}` Dimension（ip 在前）

### Period（数据粒度）选择建议

| 查询时间跨度 | 建议 Period | 说明 |
|-------------|------------|------|
| ≤ 1 小时 | 60（1分钟） | 最细粒度，排障场景 |
| 1-6 小时 | 300（5分钟） | 平衡精度与数据量 |
| 6-24 小时 | 300（5分钟） | 日常巡检 |
| 1-7 天 | 3600（1小时） | 趋势分析 |

## 调用示例

### 示例 1：查询集群聚合 CPU/内存/磁盘使用率（集群有 4 个 CK 节点）

```json
{
  "Region": "ap-beijing",
  "RegionId": 8,
  "InstanceId": "cdwch-t54licyq",
  "MetricNames": "SumCpuUsage,SumMemUsage,SumDiskUsage",
  "NodeCount": 4,
  "StartTime": "2026-06-11T18:00:00+08:00",
  "EndTime": "2026-06-11T19:00:00+08:00",
  "Period": 60
}
```

### 示例 2：查询 CK 节点级 CPU 和磁盘 IO

```json
{
  "Region": "ap-beijing",
  "RegionId": 8,
  "InstanceId": "cdwch-t54licyq",
  "MetricNames": "CpuUsage,NodeDiskIoUtil",
  "NodeIps": "10.0.0.14,10.0.0.12,10.0.0.3",
  "StartTime": "2026-06-11T18:00:00+08:00",
  "EndTime": "2026-06-11T19:00:00+08:00",
  "Period": 60
}
```

### 示例 3：查询 Keeper 节点存活和 Leader 状态

```json
{
  "Region": "ap-beijing",
  "RegionId": 8,
  "InstanceId": "cdwch-t54licyq",
  "MetricNames": "KeeperUp,KeeperIsLeader",
  "NodeIps": "10.0.1.1,10.0.1.2,10.0.1.3",
  "StartTime": "2026-06-11T18:00:00+08:00",
  "EndTime": "2026-06-11T19:00:00+08:00",
  "Period": 60
}
```

## 输出参数

### 响应结构

```json
{
  "Response": {
    "Data": [
      {
        "MetricName": "CpuUsage",
        "Namespace": "QCE/CDWCH",
        "Dimensions": [
          { "Name": "region", "Value": "ap-beijing" },
          { "Name": "InstanceId", "Value": "cdwch-xxxxxxxx" },
          { "Name": "ip", "Value": "10.0.0.1" }
        ],
        "StartTime": "2026-06-11T18:00:00+08:00",
        "EndTime": "2026-06-11T19:00:00+08:00",
        "Period": 60,
        "Value": "[45.2,47.8,43.1,50.5,...]",
        "Timestamps": [],
        "GroupBy": [
          { "Name": "InstanceId", "Value": "" }
        ]
      }
    ],
    "RequestId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

### 响应字段说明

| 字段路径 | 类型 | 描述 |
|---------|------|------|
| Response.Data | Array | 指标数据列表，每个元素对应一个维度组合 |
| Data[].MetricName | String | 指标名称 |
| Data[].Dimensions | Array | 维度信息，包含 region、InstanceId、ip 等 |
| Data[].Value | String | **JSON 字符串格式的数值数组**，需 JSON.parse 解析 |
| Data[].StartTime | String | 实际数据起始时间 |
| Data[].EndTime | String | 实际数据结束时间 |
| Data[].Period | Integer | 数据粒度（秒） |
| Data[].Timestamps | Array | 时间戳数组（可能为空，此时按 StartTime + Period 递推） |

### ⚠️ Value 字段解析

`Value` 是一个 **JSON 字符串**（不是数组），需要 `JSON.parse()` 解析：

```javascript
const values = JSON.parse(dataItem.Value); // "[5.806,5.786,...]" → [5.806, 5.786, ...]
```

- 数组中的 `null` 表示该时间点无数据
- 数组长度 = (EndTime - StartTime) / Period
- 每个值对应一个时间点：`StartTime + index * Period`

## MetricName 转换规则

告警配置中的 `metricName` 使用下划线格式（如 `cpu_usage`），调用本工具时需转换为**首字母大写的驼峰格式**：

**转换规则**：将下划线 `_` 去掉，每个单词首字母大写。

| 原始 metricName（下划线格式） | 接口 MetricName（驼峰格式） |
|-------------------------------|----------------------------|
| `ck_up` | `CkUp` |
| `cpu_usage` | `CpuUsage` |
| `mem_usage` | `MemUsage` |
| `disk_usage` | `DiskUsage` |
| `node_load1` | `NodeLoad1` |
| `node_load5` | `NodeLoad5` |
| `node_load15` | `NodeLoad15` |
| `node_disk_io_util` | `NodeDiskIoUtil` |
| `node_disk_io_wait` | `NodeDiskIoWait` |
| `node_disk_read_iops` | `NodeDiskReadIops` |
| `node_disk_write_iops` | `NodeDiskWriteIops` |
| `node_disk_read_throughout` | `NodeDiskReadThroughout` |
| `node_disk_write_throughout` | `NodeDiskWriteThroughout` |
| `node_network_receive_bytes_total` | `NodeNetworkReceiveBytesTotal` |
| `node_network_transmit_bytes_total` | `NodeNetworkTransmitBytesTotal` |
| `sum_cpu_usage` | `SumCpuUsage` |
| `sum_mem_usage` | `SumMemUsage` |
| `sum_disk_usage` | `SumDiskUsage` |
| `ck_mem_usage` | `CkMemUsage` |
| `ck_cpu_usage` | `CkCpuUsage` |
| `ck_disk_usage` | `CkDiskUsage` |

## 指标分类

### 集群聚合指标（sum_alarm）— 传 NodeCount 参数

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| SumCkUp | 集群节点数 | — |
| SumCpuUsage | CPU使用率（集群聚合） | % |
| SumMemUsage | 内存使用率（集群聚合） | % |
| SumDiskUsage | 数据盘使用率（集群聚合） | % |
| SumQuery | 总查询数 | 个/s |
| SumInsertquery | 插入数 | 个/s |
| SumFailedinsertquery | 插入失败数 | 个/s |
| SumFailedselectquery | 查询失败数 | 个/s |
| SumNodeNetworkReceiveBytesTotal | 节点接收流量 | MBytes/s |
| SumNodeNetworkTransmitBytesTotal | 节点发送流量 | MBytes/s |
| CkCpuUsage | CK节点CPU使用率 | % |
| CkMemUsage | CK节点内存使用率 | % |
| CkDiskUsage | CK节点磁盘使用率 | % |
| ClusterZkGlobalSessions | ZK全局session个数 | 个 |

### CK 节点指标（ck_process）— 传 NodeIps 参数（CK 节点 IP）

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| CkUp | 节点存活（1=存活，0=失活） | — |
| CpuUsage | CPU峰值使用率 | % |
| MemUsage | 内存使用率 | % |
| DiskUsage | 数据盘使用率 | % |
| NodeLoad1 | 节点1分钟负载 | — |
| NodeLoad5 | 节点5分钟负载 | — |
| NodeLoad15 | 节点15分钟负载 | — |
| Httpconnection | HTTP连接数 | 个 |
| Mysqlconnection | MySQL方式连接数 | 个 |
| Tcpconnection | TCP连接数 | 个 |
| Query | 包含增删改查的query个数 | 个/s |
| Insertquery | 单位时间insert执行次数 | 个/s |
| Failedinsertquery | 插入失败数 | 个/s |
| Failedselectquery | 查询失败数 | 个/s |
| Querythread | 查询线程数 | 个 |
| Merge | 合并数 | 个 |
| Mergestimemilliseconds | Merge消耗时间（速率） | ms |
| Replicatedpartmerges | 副本块合并个数 | 个/s |
| Replicatedpartmutations | 副本块修改数 | 个/s |
| Zookeeperrequest | ZK请求数 | 个 |
| Zookeepersession | ZK session个数 | 个 |
| Zookeeperwatch | ZK watch个数 | 个 |
| NodeDiskIoUtil | 节点硬盘IO使用率 | % |
| NodeDiskIoWait | 节点硬盘IO等待时间 | ms |
| NodeDiskReadIops | 节点硬盘读IOPS | 个/s |
| NodeDiskWriteIops | 节点硬盘写IOPS | 个/s |
| NodeDiskReadThroughout | 节点硬盘读流量 | MBytes/s |
| NodeDiskWriteThroughout | 节点硬盘写流量 | MBytes/s |
| NodeNetworkReceiveBytesTotal | 节点接收流量 | MBytes/s |
| NodeNetworkTransmitBytesTotal | 节点流出流量 | MBytes/s |
| Contextlockwait | 上下文锁等待 | 个 |
| CpuLoadRate | CPU负载比率 | % |
| CpuUsageAvg | CPU平均使用率 | % |
| ReadonlyReplica | readonlyReplica数量 | 个 |
| PartMutation | mutation数量 | 个 |
| Distributedfilestoinsert | 分布式表等待写入的数据文件数 | 个 |
| DiskUsageWithExtendDisk | 数据盘使用率（含挂载） | % |
| NodeIoQueueSize | 节点IO队列长度 | 个 |
| Fileopen | 文件打开数 | 个 |
| Uptime | 启动时间 | — |

### Keeper 节点指标（keeper_process_alarm）— 传 NodeIps 参数（Keeper 节点 IP，NodeRole=COMMON）

> ⚠️ Keeper 节点也有通用系统指标（CPU、内存、磁盘、网络等），查询时需使用 **Keeper 节点的 IP**（NodeRole=COMMON），而非 CK 节点 IP。

**Keeper 专有指标**：

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| KeeperUp | Keeper进程存活 | — |
| KeeperPacketsSent | 发包个数 | 个/s |
| KeeperPacketsReceived | 收包个数 | 个/s |
| KeeperWatchCount | Keeper watch数量 | 个 |
| KeeperRequestCommitQueued | 请求提交队列个数 | 个/s |
| KeeperActiveDistributedDdl | 正在运行的分布式DDL | 个 |
| KeeperIsLeader | Keeper节点Leader | — |
| KeeperZnodeCount | Keeper Znode个数 | 个 |
| KeeperZxid | Keeper事务版本 | — |
| KeeperGlobalSessions | 全局session个数 | 个 |

**Keeper 节点系统资源指标**（与 CK 节点同名，但采集的是 Keeper 节点的资源，需用 Keeper 节点 IP 查询）：

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| CpuUsage | CPU使用率 | % |
| MemUsage | 内存使用率 | % |
| DiskUsage | 数据盘使用率 | % |
| NodeLoad1 / NodeLoad5 / NodeLoad15 | 节点负载 | — |
| NodeDiskIoUtil | 硬盘IO使用率 | % |
| NodeDiskIoWait | 硬盘IO等待时间 | ms |
| NodeDiskReadIops / NodeDiskWriteIops | 硬盘读写IOPS | 个/s |
| NodeDiskReadThroughout / NodeDiskWriteThroughout | 硬盘读写流量 | MBytes/s |
| NodeNetworkReceiveBytesTotal / NodeNetworkTransmitBytesTotal | 网络流量 | MBytes/s |
| NodeIoQueueSize | IO队列长度 | 个 |

### ZooKeeper 节点指标（zk_process_alarm）— 传 NodeIps 参数（ZK 节点 IP，NodeRole=COMMON）

> ⚠️ ZK 节点也有通用系统指标（CPU、内存、磁盘、网络等），查询时需使用 **ZK 节点的 IP**（NodeRole=COMMON），而非 CK 节点 IP。

**ZK 专有指标**：

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| ZkUp | ZK进程存活 | — |
| PacketsSent | 发包个数 | 个 |
| PacketsReceived | 收包个数 | 个 |
| PrepProcessorQueueTimeMs | 预处理队列等待时间 | ms |
| PrepProcessTime | 预处理时间 | ms |
| GlobalSessions | 全局session个数 | 个 |
| WatchCount | ZK watch个数 | 个 |
| JvmMemoryPoolBytesUsed | JVM内存池使用 | MBytes |
| ConnectionRejected | 拒绝连接个数 | 个 |
| RequestCommitQueued | 请求提交队列个数 | 个 |
| Zxid | ZooKeeper事务版本 | — |
| ZkIsLeader | ZooKeeper节点Leader | — |
| ActiveDistributedDdl | 正在运行的分布式DDL | 个 |
| ZnodeCount | Znode个数 | 个 |
| LeaderServes | LeaderServes配置 | — |

**ZK 节点系统资源指标**（与 CK 节点同名，但采集的是 ZK 节点的资源，需用 ZK 节点 IP 查询）：

| MetricName（驼峰） | 含义 | 单位 |
|-------------------|------|------|
| CpuUsage | CPU使用率 | % |
| MemUsage | 内存使用率 | % |
| DiskUsage | 数据盘使用率 | % |
| NodeLoad1 / NodeLoad5 / NodeLoad15 | 节点负载 | — |
| NodeDiskIoUtil | 硬盘IO使用率 | % |
| NodeDiskIoWait | 硬盘IO等待时间 | ms |
| NodeDiskReadIops / NodeDiskWriteIops | 硬盘读写IOPS | 个/s |
| NodeDiskReadThroughout / NodeDiskWriteThroughout | 硬盘读写流量 | MBytes/s |
| NodeNetworkReceiveBytesTotal / NodeNetworkTransmitBytesTotal | 网络流量 | MBytes/s |
| NodeIoQueueSize | IO队列长度 | 个 |

## 典型使用场景

- **健康巡检**：先查集群聚合指标（SumCpuUsage/SumMemUsage/SumDiskUsage），发现异常再下钻到节点级
- **告警排查**：收到磁盘告警后，查询 DiskUsage 趋势，判断是突增还是持续增长
- **节点对比**：同时查询多个节点的同一指标，发现热点节点
- **ZK/Keeper 健康**：查询 KeeperUp/ZkUp 确认进程存活，查询 KeeperZxid/Zxid 确认事务版本一致性
- **写入压力评估**：查询 Insertquery 和 Merge，判断写入是否过于频繁

## 注意事项

1. **MetricName 必须使用驼峰格式**，不能使用下划线格式
2. **节点级指标必须传 NodeIps 参数**，IP 通过 `TCHouseCDescribeInstanceNodes` 接口获取
3. **集群聚合指标必须传 NodeCount 参数**（CK 节点数），通过 `TCHouseCDescribeInstanceNodes` 获取节点数
4. **MetricNames 可批量查询多个指标**（逗号分隔），建议一次不超过 5 个，避免响应过大
5. **时间范围不宜过大**：Period=60 时建议不超过 6 小时，Period=300 时不超过 24 小时，Period=3600 时不超过 7 天
6. **Value 是 JSON 字符串**，需要 JSON.parse 解析，其中 null 表示该时间点无数据
7. **时间格式为 ISO 8601**（如 `2026-06-11T18:00:00+08:00`），注意与 `TCHouseCDescribeEventTasks` 的 `YYYY-MM-DD HH:MM:SS` 格式不同

---

## 附录：底层 API 原始请求结构（MCP Server 实现参考）

> 以下内容为 MCP Server 内部实现参考，Agent 无需关心。MCP Server 会自动将上述 flat 参数转换为以下嵌套结构。

```json
{
  "Module": "monitor",
  "Query": [
    {
      "Datasource": "DS_QCEMetric",
      "Namespace": "QCE/CDWCH",
      "MetricName": "<指标名称，驼峰格式>",
      "Conditions": [
        {
          "Region": "<地域，如 ap-beijing>",
          "Dimension": [
            "{\"InstanceId\":\"<集群ID>\"}",
            "{\"ip\":\"<节点IP>\",\"InstanceId\":\"<集群ID>\"}"
          ]
        }
      ],
      "GroupBy": ["InstanceId"],
      "StartTime": "<ISO 8601 格式>",
      "EndTime": "<ISO 8601 格式>",
      "Period": 60
    }
  ],
  "SpaceUUID": "space_default",
  "Language": "zh-CN"
}
```

### MCP Server 自动注入的固定字段

| 字段 | 值 | 说明 |
|------|-----|------|
| Module | `monitor` | 顶层必选参数 |
| Query[].Datasource | `DS_QCEMetric` | 数据源标识 |
| Query[].Namespace | `QCE/CDWCH` | 命名空间 |
| SpaceUUID | `space_default` | 空间标识 |
