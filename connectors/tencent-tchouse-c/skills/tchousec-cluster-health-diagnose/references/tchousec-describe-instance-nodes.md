# tchousec-describe-instance-nodes

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeInstanceNodes` 云 API，获取指定集群的节点信息列表，包括数据节点和 ZooKeeper 节点。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeInstanceNodes`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称      | 必选 | 类型    | 描述                                                                 |
| ------------- | ---- | ------- | -------------------------------------------------------------------- |
| InstanceId    | 是   | String  | 集群实例 ID，格式如 `cdwch-xxxxxxxx`                                 |
| Region        | 是   | String  | 地域，如 `ap-guangzhou`、`ap-shanghai`                               |
| NodeRole      | 否   | String  | 节点角色类型：`DATA`（数据节点）、`COMMON`（ZooKeeper 节点），默认 `DATA` |
| Offset        | 否   | Integer | 分页偏移量，第一页为 0，第二页为 10                                  |
| Limit         | 否   | Integer | 分页步长，默认为 10                                                  |
| DisplayPolicy | 否   | String  | 展现策略，`All` 时显示所有                                           |
| ForceAll      | 否   | Boolean | 为 `true` 时返回所有节点（忽略分页）                                 |

## 输出参数

| 参数名称                          | 类型    | 描述                                       |
| --------------------------------- | ------- | ------------------------------------------ |
| TotalCount                        | Integer | 节点总数                                   |
| InstanceNodesList                 | Array   | 节点信息列表                               |
| InstanceNodesList[].Ip            | String  | 节点内网 IP                                |
| InstanceNodesList[].Spec          | String  | 规格标识，如 `S_2_4_H`                     |
| InstanceNodesList[].Core          | Integer | CPU 核数                                   |
| InstanceNodesList[].Memory        | Integer | 内存大小（GB）                             |
| InstanceNodesList[].DiskSize      | Integer | 磁盘大小（GB）                             |
| InstanceNodesList[].DiskType      | String  | 磁盘类型，如 `CLOUD_HSSD`                  |
| InstanceNodesList[].Cluster       | String  | 所属集群名称                               |
| InstanceNodesList[].Status        | String  | 节点状态：`Running`/`Stopped`/`Unknown`    |
| InstanceNodesList[].Zone          | String  | 可用区                                     |
| InstanceNodesList[].ZoneDesc      | String  | 可用区描述                                 |
| InstanceNodesList[].IsCHProxy     | Boolean | 是否为 CHProxy 节点                        |
| InstanceNodesList[].RealResourceId| String  | 底层 CVM 实例 ID                           |
| InstanceNodesList[].UUID          | String  | 节点唯一标识                               |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeInstanceNodes",
  "Version": "2020-09-15",
  "Region": "ap-chongqing",
  "InstanceId": "cdwch-xxxxxxxx",
  "NodeRole": "DATA",
  "ForceAll": true
}
```

### 响应示例

```json
{
  "Response": {
    "TotalCount": 2,
    "InstanceNodesList": [
      {
        "Cluster": "default_cluster",
        "Core": 2,
        "DiskSize": 200,
        "DiskType": "CLOUD_HSSD",
        "Ip": "10.0.0.1",
        "IsCHProxy": false,
        "Memory": 4,
        "RealResourceId": "ins-xxxxxxxx",
        "Spec": "S_2_4_H",
        "Status": "Running",
        "UUID": "939cd0af-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "Zone": "ap-chongqing-1",
        "ZoneDesc": "重庆一区"
      },
      {
        "Cluster": "default_cluster",
        "Core": 2,
        "DiskSize": 200,
        "DiskType": "CLOUD_HSSD",
        "Ip": "10.0.0.2",
        "IsCHProxy": false,
        "Memory": 4,
        "RealResourceId": "ins-yyyyyyyy",
        "Spec": "S_2_4_H",
        "Status": "Running",
        "UUID": "a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "Zone": "ap-chongqing-1",
        "ZoneDesc": "重庆一区"
      }
    ],
    "RequestId": "xxx-xxx-xxx"
  }
}
```

## 典型使用场景

- **节点健康检查**：遍历所有节点，确认 Status 是否全部为 `Running`，发现异常节点
- **资源瓶颈判断**：通过 Core/Memory/DiskSize 了解节点规格，结合监控指标判断资源是否充足
- **拓扑确认**：确认数据节点和 ZK 节点的数量和分布，用于 HA 和副本分析
- **故障定位**：当监控指标异常时，通过节点 IP 定位具体是哪个节点出问题
