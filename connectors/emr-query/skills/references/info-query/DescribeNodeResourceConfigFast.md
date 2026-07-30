# DescribeNodeResourceConfigFast

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

快速获取节点规格配置

## 统一调用格式

```bash
tccli emr DescribeNodeResourceConfigFast --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ResourceType | String | host(物理机)/pod |

## tccli 调用示例

```bash
cat > /tmp/DescribeNodeResourceConfigFast.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "ResourceType": "ALL",
  "PayMode": 0
}
EOF
tccli emr DescribeNodeResourceConfigFast --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeNodeResourceConfigFast.json
```

## 最新实测返回

```json
{
  "Data": [],
  "RequestId": "37c84a97-ccfd-4a26-b030-5fbd790ab254"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
