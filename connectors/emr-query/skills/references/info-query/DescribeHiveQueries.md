# DescribeHiveQueries

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取Hive查询信息

## 统一调用格式

```bash
tccli emr DescribeHiveQueries --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| StartTime | Integer | 起始时间戳 |
| EndTime | Integer | 结束时间戳 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 分页偏移 |
| Limit | Integer | 分页大小 |
| Status | String[] | 状态过滤:[RUNNING,COMPLETED,FAILED] |

## tccli 调用示例

```bash
cat > /tmp/DescribeHiveQueries.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "Offset": 0,
  "Limit": 10
}
EOF
tccli emr DescribeHiveQueries --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeHiveQueries.json
```

## 最新实测返回

```json
{
  "Total": 0,
  "Results": [],
  "RequestId": "b4e84cfe-efe2-4325-bf6f-25e26a928928"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
