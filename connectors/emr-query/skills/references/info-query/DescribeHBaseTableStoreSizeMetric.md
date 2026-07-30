# DescribeHBaseTableStoreSizeMetric

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取 HBase 表级监控 StoreSize 大小指标。

## 统一调用格式

```bash
tccli emr DescribeHBaseTableStoreSizeMetric --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <InstanceId> --TableName <TableName> --StartTime <StartTime> --EndTime <EndTime>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |
| TableName | String | HBase 表名（可通过 DescribeHBaseTableOverview 获取，如 `hbase_meta`） |
| StartTime | Integer | 查询起始时间戳 |
| EndTime | Integer | 查询结束时间戳（必须大于 StartTime） |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| RegionServer | String | HBase RegionServer 服务 |
| Downsample | String | 监控数据粒度 |

## tccli 调用示例

```bash
tccli emr DescribeHBaseTableStoreSizeMetric --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80 --TableName hbase_meta --StartTime 1751277600 --EndTime 1751364000
```

## 最新实测返回

```json
{
  "MetricDataList": [],
  "RequestId": "c4eac841-8b96-42b9-9104-839c55c22fbd"
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter | EndTime 必须大于 StartTime |
| MissingParameter | 缺少必传参数 `TableName` |
