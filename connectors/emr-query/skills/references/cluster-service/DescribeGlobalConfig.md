# DescribeGlobalConfig

> 分类：cluster-service | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询YARN资源调度全局配置

## 统一调用格式

```bash
tccli emr DescribeGlobalConfig --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
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
cat > /tmp/DescribeGlobalConfig.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeGlobalConfig --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeGlobalConfig.json
```

## 最新实测返回

```json
{
  "EnableResourceSchedule": true,
  "RequestId": "c8c0be0f-3919-4963-a160-fa3c02c9fafa"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
