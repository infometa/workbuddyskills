# DescribeUsersForUserManager

> 分类：user-management | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询用户列表

## 统一调用格式

```bash
tccli emr DescribeUsersForUserManager --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| PageNo | Integer | 页码 |
| PageSize | Integer | 每页数量 |

## tccli 调用示例

```bash
cat > /tmp/DescribeUsersForUserManager.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "PageNo": 1,
  "PageSize": 10
}
EOF
tccli emr DescribeUsersForUserManager --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeUsersForUserManager.json
```

## 最新实测返回

```json
{
  "TotalCnt": 3,
  "UserManagerUserList": null,
  "RequestId": "92839c6d-75e0-4a3c-8b9e-51d009ace249"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
