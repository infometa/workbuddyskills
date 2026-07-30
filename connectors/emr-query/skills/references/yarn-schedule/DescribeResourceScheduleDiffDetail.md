# DescribeResourceScheduleDiffDetail

> 分类：yarn-schedule | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

YARN资源调度变更详情

## 统一调用格式

```bash
tccli emr DescribeResourceScheduleDiffDetail --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| Scheduler | String | 调度器类型:capacity |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeResourceScheduleDiffDetail.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "Scheduler": "capacity"
}
EOF
tccli emr DescribeResourceScheduleDiffDetail --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeResourceScheduleDiffDetail.json
```

## 最新实测返回

```json
{
  "Details": [],
  "RequestId": "e5e527b4-4c02-4328-9d70-b52c2e4cdac2"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
