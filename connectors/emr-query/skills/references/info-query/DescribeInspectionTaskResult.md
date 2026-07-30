# DescribeInspectionTaskResult

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取巡检任务结果列表

## 统一调用格式

```bash
tccli emr DescribeInspectionTaskResult --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
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
cat > /tmp/DescribeInspectionTaskResult.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeInspectionTaskResult --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeInspectionTaskResult.json
```

## 最新实测返回

```json
{
  "InspectionResultInfo": "W10=",
  "Total": 0,
  "TypeInfo": "eyJGaXhlZFRpbWUiOiLlrprml7YiLCJSZWFsVGltZSI6IuWNs+aXtiJ9",
  "RequestId": "ffd37474-af71-4219-916a-4a7e41b8c364"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
