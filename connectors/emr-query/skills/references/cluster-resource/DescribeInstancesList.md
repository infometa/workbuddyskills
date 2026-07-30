# DescribeInstancesList

> 分类：cluster-resource | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询集群列表

## 统一调用格式

```bash
tccli emr DescribeInstancesList --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| DisplayStrategy | String | clusterList(除已销毁)/monitorManage(除已销毁+创建中+失败) |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 页编号,默认0 |
| Limit | Integer | 每页数量,默认100,最大100 |
| OrderField | String | 排序字段:clusterId/addTime/status |
| Asc | Integer | 排序:0升序/1降序 |
| Filters | Array | [{"Name":"ClusterId","Values":["emr-xxx"]}] |
| ClusterType | Integer | 0普通集群/2TKE集群 |

## tccli 调用示例

```bash
cat > /tmp/DescribeInstancesList.json <<'EOF'
{
  "DisplayStrategy": "clusterList",
  "Limit": 10
}
EOF
tccli emr DescribeInstancesList --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeInstancesList.json
```

## 最新实测返回

```json
{
  "TotalCnt": 0,
  "RequestId": "316eb5e5-d0a7-4966-ac15-0f564abdaa8c"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
