# DescribeClusterNodes

> 分类：cluster-resource | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询集群节点信息

## 统一调用格式

```bash
tccli emr DescribeClusterNodes --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID,如emr-xxx |
| NodeFlag | String | all/master/core/task/common/router/db/recyle(回收站)/renew(待续费) |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 页编号,默认0 |
| Limit | Integer | 每页数量,默认100 |
| HardwareResourceType | String | all/host/pod |
| OrderField | String | 排序字段 |
| Asc | Integer | 0降序/1升序 |

## tccli 调用示例

```bash
cat > /tmp/DescribeClusterNodes.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "NodeFlag": "all"
}
EOF
tccli emr DescribeClusterNodes --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeClusterNodes.json
```

## 最新实测返回

```json
{
  "TotalCnt": 0,
  "RequestId": "f74d9fd6-7078-48cd-846a-b06d55aacd5d"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
