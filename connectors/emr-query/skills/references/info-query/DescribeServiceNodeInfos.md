# DescribeServiceNodeInfos

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询服务进程信息。

## 统一调用格式

```bash
tccli emr DescribeServiceNodeInfos --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <InstanceId> --ServiceName <ServiceName> --Offset <Offset> --Limit <Limit>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |
| ServiceName | String | 服务名，如 `HDFS` / `YARN` / `HIVE` / `HBASE`（注意：API 文档未标注必选，但实际调用需要此参数） |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 页码偏移，默认0 |
| Limit | Integer | 页大小 |
| SearchText | String | 搜索字段 |
| ConfStatus | Integer | 配置状态：-2 失败 / -1 过期 / 1 已同步 / -99 全部 |
| MaintainStateId | Integer | 维护状态：0 全部 / 1 正常 / 2 维护 |
| OperatorStateId | Integer | 操作状态 |

## tccli 调用示例

```bash
tccli emr DescribeServiceNodeInfos --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80 --ServiceName HDFS --Offset 0 --Limit 5
```

## 最新实测返回

```json
{
  "TotalCnt": 11,
  "ServiceNodeList": [
    {
      "Ip": "172.16.48.17",
      "NodeType": 1,
      "NodeName": "NameNode",
      "ServiceStatus": 1,
      "MonitorStatus": 1,
      "Status": 1,
      "ConfGroupId": 448255,
      "ConfGroupName": "hdfs-master-defaultGroup",
      "ConfStatus": 1,
      "NodeFlagFilter": "master",
      "HealthStatus": {"Code": 1, "Text": "良好", "Desc": "端口探测在5s内响应"},
      "HAState": "Active"
    }
  ],
  "AliasInfo": "eyJjb21tb24iOiJjb21tb24i...",
  "SupportNodeFlagFilterList": ["master", "core", "task", "common", "router"],
  "RequestId": "d6c8dcb0-3f78-43f5-aeb4-1c1a26e1a32d"
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter | 缺少必传参数 `ServiceName`（API 文档未标注但实际需要） |
