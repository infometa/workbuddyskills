# DescribeInstanceRenewNodes

> 分类：cluster-resource | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询待续费节点

## 统一调用格式

```bash
tccli emr DescribeInstanceRenewNodes --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群实例ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeInstanceRenewNodes.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeInstanceRenewNodes --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeInstanceRenewNodes.json
```

## 最新实测返回

```json
{
  "TotalCnt": 0,
  "NodeList": [],
  "MetaInfo": [],
  "RedisInfo": [],
  "RequestId": "6aa6797b-2b97-451a-81bf-6325bd6377e3"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
