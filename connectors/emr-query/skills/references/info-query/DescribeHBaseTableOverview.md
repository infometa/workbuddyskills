# DescribeHBaseTableOverview

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取HBase表级监控数据概览

## 统一调用格式

```bash
tccli emr DescribeHBaseTableOverview --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |
| Offset | Integer | 分页偏移 |
| Limit | Integer | 分页大小 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 | - | 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeHBaseTableOverview.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "Offset": 0,
  "Limit": 10
}
EOF
tccli emr DescribeHBaseTableOverview --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeHBaseTableOverview.json
```

## 最新实测返回

```json
{
  "TableMonitorList": [
    {
      "Table": "hbase_meta",
      "ReadRequestCount": 0.02,
      "WriteRequestCount": 0,
      "MemstoreSize": 768,
      "StoreFileSize": 13802,
      "Operation": "Regions,RegionServers",
      "StoreFileNum": 2
    }
  ],
  "TotalCount": 3,
  "RequestId": "e162abad-a00c-4b8a-9d35-eb8fc9a39970"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
