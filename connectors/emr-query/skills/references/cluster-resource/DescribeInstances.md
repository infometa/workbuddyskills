# DescribeInstances

> 分类：cluster-resource | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询集群实例信息

## 统一调用格式

```bash
tccli emr DescribeInstances --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| DisplayStrategy | String | clusterList/monitorManage |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceIds | String[] | 如["emr-xxx"] |
| Offset | Integer | 页编号,默认0 |
| Limit | Integer | 每页数量,默认100 |
| ProjectId | Integer | 建议填-1拉取所有项目 |
| OrderField | String | 排序字段 |
| Asc | Integer | 0降序/1升序 |

## tccli 调用示例

```bash
cat > /tmp/DescribeInstances.json <<'EOF'
{
  "DisplayStrategy": "clusterList",
  "InstanceIds": [
    "emr-oem5vw80"
  ],
  "ProjectId": 0
}
EOF
tccli emr DescribeInstances --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeInstances.json
```

## 最新实测返回

```json
{
  "TotalCnt": 0,
  "RequestId": "bcb8c900-0cc7-41d8-902e-e30733d892c0"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
