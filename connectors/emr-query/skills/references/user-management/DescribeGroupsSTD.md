# DescribeGroupsSTD

> 分类：user-management | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询用户组

## 统一调用格式

```bash
tccli emr DescribeGroupsSTD --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
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
cat > /tmp/DescribeGroupsSTD.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeGroupsSTD --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeGroupsSTD.json
```

## 最新实测返回

```json
{
  "Data": [],
  "RequestId": "07d4fc75-d3d7-434b-9d1b-5e9a12ed340a"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
