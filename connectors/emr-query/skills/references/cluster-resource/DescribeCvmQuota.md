# DescribeCvmQuota

> 分类：cluster-resource | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询账户CVM配额

## 统一调用格式

```bash
tccli emr DescribeCvmQuota --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ClusterId | String | 集群ID |
| ZoneId | Integer | 可用区ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeCvmQuota.json <<'EOF'
{
  "ClusterId": "emr-oem5vw80",
  "ZoneId": 100007
}
EOF
tccli emr DescribeCvmQuota --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeCvmQuota.json
```

## 最新实测返回

```json
{
  "PostPaidQuotaSet": [],
  "RequestId": "761fb9b3-bb8a-44be-aa1a-051b33b3a40b"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
