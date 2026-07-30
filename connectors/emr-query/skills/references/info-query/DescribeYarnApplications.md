# DescribeYarnApplications

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取YARN任务信息

## 统一调用格式

```bash
tccli emr DescribeYarnApplications --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| StartTime | Integer | 起始时间戳(<30天前) |
| EndTime | Integer | 结束时间戳 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 分页 |
| Limit | Integer | 分页大小 |

## tccli 调用示例

```bash
cat > /tmp/DescribeYarnApplications.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "Offset": 0,
  "Limit": 10
}
EOF
tccli emr DescribeYarnApplications --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeYarnApplications.json
```

## 最新实测返回

```json
{
  "Total": 0,
  "Results": [],
  "RequestId": "a36f715e-6ef5-4ace-b6b7-d4ee2a9fffaf"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
