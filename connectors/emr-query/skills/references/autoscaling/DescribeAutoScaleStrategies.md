# DescribeAutoScaleStrategies

> 分类：autoscaling | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取自动扩缩容规则

## 统一调用格式

```bash
tccli emr DescribeAutoScaleStrategies --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| GroupId | Integer | 组ID |

## tccli 调用示例

```bash
cat > /tmp/DescribeAutoScaleStrategies.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeAutoScaleStrategies --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeAutoScaleStrategies.json
```

## 最新实测返回

```json
{
  "LoadAutoScaleStrategies": [],
  "TimeBasedAutoScaleStrategies": [],
  "RequestId": "c8a46dff-836f-4eb7-8abe-e070dfd52de9"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
