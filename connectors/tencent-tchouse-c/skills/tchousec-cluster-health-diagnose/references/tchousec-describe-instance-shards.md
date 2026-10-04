# tchousec-describe-instance-shards

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeInstanceShards` 云 API，获取指定集群的分片（Shard）拓扑信息，包括分片数量、副本配置和 ZooKeeper 连接信息。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeInstanceShards`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称   | 必选 | 类型   | 描述                                   |
| ---------- | ---- | ------ | -------------------------------------- |
| InstanceId | 是   | String | 集群实例 ID，格式如 `cdwch-xxxxxxxx`   |
| Region     | 是   | String | 地域，如 `ap-guangzhou`、`ap-shanghai` |

## 输出参数

| 参数名称           | 类型   | 描述                                                                 |
| ------------------ | ------ | -------------------------------------------------------------------- |
| InstanceShardsList | String | 分片信息 JSON 字符串，包含 HA 状态和 ZK 地址等（需 JSON 解析）       |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeInstanceShards",
  "Version": "2020-09-15",
  "Region": "ap-chongqing",
  "InstanceId": "cdwch-xxxxxxxx"
}
```

### 响应示例

```json
{
  "Response": {
    "InstanceShardsList": "[{\"HA\": 1, \"ZKHost\": \"10.0.4.199\"}]",
    "RequestId": "f510b0e8-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

### InstanceShardsList 解析后结构

```json
[
  {
    "HA": 1,
    "ZKHost": "10.0.4.199"
  }
]
```

| 字段   | 类型    | 描述                                   |
| ------ | ------- | -------------------------------------- |
| HA     | Integer | 是否为 HA 模式：1-是，0-否             |
| ZKHost | String  | ZooKeeper 节点地址                     |

## 典型使用场景

- **HA 状态确认**：确认集群是否为高可用模式，影响副本延迟诊断和故障恢复策略
- **ZooKeeper 连接检查**：获取 ZK 地址，用于判断 ZK 连接是否正常（副本延迟的常见原因）
- **分片拓扑分析**：了解集群的分片数量和分布，用于数据均衡分析
- **故障影响评估**：HA 集群单节点故障影响较小，非 HA 集群单节点故障可能导致数据不可用

## 注意事项

- `InstanceShardsList` 返回的是 JSON 字符串，需要额外解析
- HA=1 表示集群有副本，副本延迟诊断才有意义
- HA=0 的集群没有副本，单节点故障可能导致数据丢失，诊断时需特别提醒用户
