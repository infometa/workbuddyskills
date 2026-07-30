# DescribeEmrOverviewMetrics

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询监控概览页指标数据

## 统一调用格式

```bash
tccli emr DescribeEmrOverviewMetrics --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeEmrOverviewMetrics.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "End": 1782804465,
  "Downsample": "5m",
  "Metric": "cpu_used_percent"
}
EOF
tccli emr DescribeEmrOverviewMetrics --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeEmrOverviewMetrics.json
```

## 最新实测返回

```json
{
  "Result": null,
  "RequestId": "37cff4e3-c616-453b-b4f5-5b8e9b7f8883"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
