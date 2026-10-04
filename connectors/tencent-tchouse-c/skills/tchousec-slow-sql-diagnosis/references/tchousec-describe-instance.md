
# tchousec-describe-instance

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeInstance` 云 API，根据实例 ID 查询集群的详细信息。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeInstance`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称   | 必选 | 类型   | 描述                                   |
| ---------- | ---- | ------ | -------------------------------------- |
| InstanceId | 是   | String | 集群实例 ID，格式如 `cdwch-xxxxxxxx`   |
| Region     | 是   | String | 地域，如 `ap-guangzhou`、`ap-shanghai` |

## 输出参数

| 参数名称                            | 类型   | 描述                                                               |
| ----------------------------------- | ------ | ------------------------------------------------------------------ |
| InstanceInfo.InstanceId             | String | 集群实例 ID                                                        |
| InstanceInfo.InstanceName           | String | 集群名称                                                           |
| InstanceInfo.Status                 | String | 状态：Init/Serving/Deleted/Deleting/Modify                         |
| InstanceInfo.StatusDesc             | String | 状态中文描述，如"运行中"                                           |
| InstanceInfo.Version                | String | ClickHouse 版本号                                                  |
| InstanceInfo.Region                 | String | 地域                                                               |
| InstanceInfo.Zone                   | String | 可用区                                                             |
| InstanceInfo.VpcId                  | String | 私有网络 ID                                                        |
| InstanceInfo.SubnetId               | String | 子网 ID                                                            |
| InstanceInfo.PayMode                | String | 付费类型：PREPAID（包年包月）/ POSTPAID_BY_HOUR（按量计费）        |
| InstanceInfo.CreateTime             | String | 集群创建时间                                                       |
| InstanceInfo.ExpireTime             | String | 集群到期时间（包年包月）                                           |
| InstanceInfo.AccessInfo             | String | 访问地址 JSON 数组，包含 tcp/mysql_tcp 协议的连接地址              |
| InstanceInfo.MasterSummary          | Object | 数据节点规格信息                                                   |
| InstanceInfo.MasterSummary.Spec     | String | 规格标识，如 `S_2_4_H`                                             |
| InstanceInfo.MasterSummary.NodeSize | Int    | 数据节点数量                                                       |
| InstanceInfo.MasterSummary.Core     | Int    | CPU 核数                                                           |
| InstanceInfo.MasterSummary.Memory   | Int    | 内存大小（GB）                                                     |
| InstanceInfo.MasterSummary.Disk     | Int    | 磁盘大小（GB）                                                     |
| InstanceInfo.MasterSummary.DiskType | String | 磁盘类型，如 `CLOUD_HSSD`（增强型 SSD）                            |
| InstanceInfo.MasterSummary.DiskDesc | String | 磁盘类型描述                                                       |
| InstanceInfo.CommonSummary          | Object | ZooKeeper 节点规格信息（结构同 MasterSummary）                     |
| InstanceInfo.HA                     | String | 是否高可用（`"true"` / `"false"`，注意为字符串类型）               |
| InstanceInfo.Components             | Array  | 组件列表，每项含 Name 和 Version（如 CLICKHOUSE、ZOOKEEPER）       |
| InstanceInfo.IsElastic              | Bool   | 是否弹性集群                                                       |
| InstanceInfo.EnableConfigKeyValue   | String | 是否启用 KV 配置（`"true"` / `"false"`），决定能否使用配置查询接口 |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeInstance",
  "Version": "2020-09-15",
  "Region": "ap-guangzhou",
  "InstanceId": "cdwch-xxxxxxxx"
}
```

### 响应示例

```json
{
  "Response": {
    "InstanceInfo": {
      "InstanceId": "cdwch-xxxxxxxx",
      "InstanceName": "测试集群",
      "Status": "Serving",
      "StatusDesc": "运行中",
      "Version": "25.8.11.0",
      "Region": "ap-chongqing",
      "Zone": "ap-chongqing-1",
      "VpcId": "vpc-xxxxxxxx",
      "SubnetId": "subnet-xxxxxxxx",
      "PayMode": "PREPAID",
      "CreateTime": "2026-05-28 19:16:50",
      "ExpireTime": "2026-06-28 19:16:50",
      "AccessInfo": "[{\"address\":\"172.x.x.x:9000\",\"protocol\":\"tcp\"},{\"address\":\"172.x.x.x:9004\",\"protocol\":\"mysql_tcp\"}]",
      "MasterSummary": {
        "Spec": "S_2_4_H",
        "NodeSize": 1,
        "Core": 2,
        "Memory": 4,
        "Disk": 200,
        "DiskType": "CLOUD_HSSD",
        "DiskDesc": "增强型SSD云硬盘"
      },
      "CommonSummary": {
        "Spec": "",
        "NodeSize": 0,
        "Core": 0,
        "Memory": 0,
        "Disk": 0
      },
      "HA": "false",
      "Components": [
        { "Name": "CLICKHOUSE", "Version": "25.8.11.0" },
        { "Name": "ZOOKEEPER", "Version": "3.6.1" }
      ],
      "IsElastic": false,
      "EnableConfigKeyValue": "false"
    },
    "RequestId": "xxx-xxx-xxx"
  }
}
```

## 典型使用场景

- **验证集群可用性**：确认集群状态为 `Serving` 才能继续后续操作
- **获取版本信息**：ClickHouse 20.6+ 才支持 EXPLAIN，需通过 `Components` 确认精确版本
- **获取连接地址**：后续 `TCHouseCDescribeCkSqlApis` 和 `TCHouseCDescribeTableSchema` 需要连接集群
- **了解集群规格**：节点数量（NodeSize）、CPU/内存/磁盘配置影响查询并发能力和资源瓶颈判断
- **磁盘类型判断**：`DiskType` 为 `CLOUD_HSSD`（增强型 SSD）或 `CLOUD_PREMIUM`（高性能云盘）直接影响 IO 密集型查询的性能预期
- **高可用判断**：`HA` 字段决定是否存在副本，影响分布式查询和容灾建议
- **配置查询前置检查**：`EnableConfigKeyValue` 为 `"false"` 时，KV 模式配置接口不可用；但 `TCHouseCDescribeClusterConfigs` 不受此限制，可直接获取配置文件内容
