# DescribeClusterFlowStatusDetail

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询异步流程状态（最重要的轮询接口）

## 统一调用格式

```bash
tccli emr DescribeClusterFlowStatusDetail --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| FlowParam | Object | {"FKey":"FlowId","FValue":"<flow_id>"} |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| NeedExtraDetail | Boolean | 是否返回额外详情 |

## tccli 调用示例

```bash
cat > /tmp/DescribeClusterFlowStatusDetail.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "FlowParam": {
    "FKey": "FlowId",
    "FValue": "1"
  }
}
EOF
tccli emr DescribeClusterFlowStatusDetail --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeClusterFlowStatusDetail.json
```

## 最新实测返回

```json
{
  "StageDetails": null,
  "FlowDesc": null,
  "FlowName": "",
  "FlowTotalProgress": 0,
  "FlowTotalStatus": 0,
  "FlowExtraDetail": null,
  "FlowInfo": "等待计费处理资源申请中",
  "RequestId": "e9ca33ef-bd6a-446b-9414-7cd8da338f3c"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
