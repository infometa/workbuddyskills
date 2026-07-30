# DescribeTrinoQueryInfo

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询Trino(PrestoSQL)查询信息

## 统一调用格式

```bash
tccli emr DescribeTrinoQueryInfo --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
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
| Offset | Integer | 分页 |
| Limit | Integer | 分页大小 |

## tccli 调用示例

```bash
cat > /tmp/DescribeTrinoQueryInfo.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "PageSize": 10,
  "Page": 1
}
EOF
tccli emr DescribeTrinoQueryInfo --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeTrinoQueryInfo.json
```

## 最新实测返回

```json
{
  "TotalCount": 0,
  "QueryInfoList": null,
  "RequestId": "511ff049-04a9-4c90-86af-51814886f16c"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
