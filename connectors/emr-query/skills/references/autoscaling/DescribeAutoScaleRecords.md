# DescribeAutoScaleRecords

> 分类：autoscaling | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取自动扩缩容记录

## 统一调用格式

```bash
tccli emr DescribeAutoScaleRecords --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Filters | Array | 过滤条件 |
| Offset | Integer | 分页 |
| Limit | Integer | 分页大小 |

## tccli 调用示例

```bash
cat > /tmp/DescribeAutoScaleRecords.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "Filters": [],
  "Offset": 0,
  "Limit": 10
}
EOF
tccli emr DescribeAutoScaleRecords --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeAutoScaleRecords.json
```

## 最新实测返回

```json
{
  "TotalCount": 0,
  "RecordList": [],
  "RequestId": "03a05233-d7e9-46ae-a785-0207d9a42f1c"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
